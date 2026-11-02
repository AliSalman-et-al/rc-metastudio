"""Exercise nondefault controls against real R results and durable artifacts."""

import json
import math
import sys
import traceback
from pathlib import Path
from unittest.mock import patch

from analysis_matrix import run as matrix
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtTest import QTest

SCENARIOS = (
    *(
        "analysis-sequential-" + family + "-" + workflow
        for family in ("fixed", "diagnostic")
        for workflow in ("cumulative", "leave-one-out", "subgroup")
    ),
    *("options-" + family for family in ("binary", "continuous", "diagnostic")),
    "options-confidence-inclusion",
    "options-zero-cells",
    "project-structure",
    "project-table-covariates",
    "project-shell",
    "project-display-labels",
    "project-round6-polish",
    "project-release-coefficients",
    "project-reviewer-predictions",
    "project-reviewer-groups",
    "project-reviewer-colours",
    "project-axis-proportions",
    "project-axis-others",
    "project-axis-sequential",
    "calculator-grid-precision",
    "calculator-ratio-precision",
    *(
        "plot-workflow-" + family
        for family in (
            "forest",
            "cumulative",
            "leave-one-out",
            "subgroup",
            "regression",
            "sroc",
            "coefficient",
            "funnel",
            "contour",
            "trimfill",
            "deeks",
        )
    ),
    *(
        "calculator-mode-" + mode
        for mode in (
            "binary-metrics",
            "continuous-metrics",
            "diagnostic-metrics",
            "onearm-proportion",
            "onearm-mean",
            "entered-binary",
            "entered-continuous",
            "entered-diagnostic",
            "pre-post",
            "back-binary",
            "back-continuous",
            "back-diagnostic",
        )
    ),
)

ROOT = Path(__file__).resolve().parents[4]


def click(app, widget):
    assert widget.isEnabled(), widget.objectName()
    QTest.mouseClick(widget, QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()


def modal(app, kind, drive, launch):
    errors = []
    completed = []

    def ready():
        dialog = app.activeModalWidget()
        if not isinstance(dialog, kind):
            QtCore.QTimer.singleShot(10, ready)
            return
        if isinstance(dialog, QtWidgets.QMessageBox):
            dialog.setProperty("verificationExpectedMessage", True)
        try:
            drive(dialog)
        except Exception as error:  # noqa: BLE001 - propagate Qt callback failures after the modal loop.
            traceback.print_exc()
            errors.append(error)
            dialog.reject()
        finally:
            completed.append(True)

    QtCore.QTimer.singleShot(0, ready)
    launch()
    deadline = QtCore.QDeadlineTimer(5000)
    while not completed and not deadline.hasExpired():
        QTest.qWait(10)
    assert completed, ("modal did not open", kind)
    assert not errors, errors


def raw_rows(window):
    # Canonical study order, independent of the table's current sort.
    return [list(row) for row in window.model.get_current_raw_data()]


def authority(
    window,
    family,
    estimator,
    inference,
    confidence,
    correction="only0",
    entered=None,
    metric=None,
):
    """Public metafor reconstruction uses observed input, never RCMS preparation."""
    from rc_metastudio import r_bridge

    rows = raw_rows(window)
    vector = lambda i: (
        "c("
        + ",".join("NA_real_" if row[i] in (None, "") else str(row[i]) for row in rows)
        + ")"
    )
    metric = metric or window.model.current_effect
    if family == "binary":
        expression = (
            f'metafor::escalc("PR", xi={vector(0)}, ni={vector(1)})'
            if metric == "PR"
            else f'metafor::escalc("{metric}", ai={vector(0)}, n1i={vector(1)}, ci={vector(2)}, n2i={vector(3)}, add=.5, to="{correction}", drop00=FALSE)'
        )
    elif family == "continuous":
        expression = (
            f'metafor::escalc("MN", ni={vector(0)}, mi={vector(1)}, sdi={vector(2)})'
            if metric == "TX Mean"
            else f'metafor::escalc("{metric}", n1i={vector(0)}, m1i={vector(1)}, sd1i={vector(2)}, n2i={vector(3)}, m2i={vector(4)}, sd2i={vector(5)})'
        )
    elif metric == "Sens":
        # Diagnostic correction applies to all four cells if any is zero,
        # including zeros in the specificity arm of a Sens analysis.
        correction_mask = f"({vector(0)}*{vector(1)}*{vector(2)}*{vector(3)} == 0)"
        expression = f'metafor::escalc("PLO", xi={vector(0)}+.5*{correction_mask}, ni={vector(0)}+{vector(1)}+{correction_mask}, add=0)'
    else:
        expression = f'metafor::escalc("OR", ai={vector(0)}, bi={vector(1)}, ci={vector(2)}, di={vector(3)}, add=.5, to="only0", drop00=FALSE)'
    override = (
        ""
        if entered is None
        else f"e$yi[1] <- {entered[0]}; e$vi[1] <- {entered[1] ** 2}; "
    )
    result = r_bridge.execute_r_string(
        "{ e <- "
        + expression
        + "; "
        + override
        + 'f <- metafor::rma.uni(e$yi, vi=e$vi, method="'
        + estimator
        + '", test="'
        + inference
        + '", level='
        + str(confidence)
        + "); jsonlite::toJSON(list(estimate=as.numeric(f$b), lower_bound=f$ci.lb, upper_bound=f$ci.ub, standard_error=f$se, p_value=f$pval, q=f$QE, heterogeneity_p_value=f$QEp, tau_squared=f$tau2), auto_unbox=TRUE, digits=16) }"
    )
    return json.loads(str(result[0]))


def compare_authority(view, expected, family, record, metric=None):
    from tests.analysis_regression.golden.support.golden_analysis import (
        parsed_numeric_sections,
    )

    sections = parsed_numeric_sections(view.results)
    actual = sections[
        ("Sensitivity Summary" if metric == "Sens" else "Odds Ratio Summary")
        if family == "diagnostic"
        else "Summary"
    ]
    for key, value in expected.items():
        observed_key = (
            "calculation_scale." + key
            if (family == "diagnostic" or (family == "binary" and metric != "PR"))
            and key in ("estimate", "lower_bound", "upper_bound", "standard_error")
            else key
        )
        assert observed_key in actual, (observed_key, actual)
        assert abs(actual[observed_key] - value) <= 1e-6 + 1e-12, (
            key,
            actual[observed_key],
            value,
        )
    record(
        "nondefault-public-authority",
        view,
        actual=actual,
        expected=expected,
        oracle="metafor::escalc + rma.uni",
        tolerance=1e-6,
    )


def options(app, window, family, record):
    # Independent inference and variance choices must survive the dialog boundary.
    for estimator, inference in (("REML", "knha"), ("PM", "t"), ("ML", "adhoc")):
        scenario = {
            "binary": "analysis-amino-binary-cumulative",
            "continuous": "analysis-continuous-cumulative",
            "diagnostic": "analysis-diagnostic-cumulative",
        }[family]
        view = matrix(
            app,
            window,
            scenario,
            record,
            keep_results=True,
            workflow_override="standard",
            parameters={
                "rm.method": estimator,
                "inference.method": inference,
                "conf.level": 90,
                "digits": 6,
            },
        )
        compare_authority(
            view, authority(window, family, estimator, inference, 90), family, record
        )
        view.close()


def confidence_inclusion(app, window, record):
    from rc_metastudio import analysis_setup_dialog, results_window
    from rc_metastudio.confidence_level_dialog import ConfidenceLevelDialog

    assert window.open(str(ROOT / "sample_projects/amino.rcms"), raise_on_error=True)

    def set_ci(dialog):
        dialog.confidence_level_spinbox.setValue(90)
        click(
            app, dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        )

    modal(
        app,
        ConfidenceLevelDialog,
        set_ci,
        window.action_change_confidence_level.trigger,
    )
    assert window.model.get_confidence_level() == 90
    window.action_undo.trigger()
    assert window.model.get_confidence_level() == 95
    window.action_redo.trigger()
    model = window.model
    index = model.index(0, model.INCLUDE_STUDY)
    window.tableView.setCurrentIndex(index)
    QTest.keyClick(window.tableView, QtCore.Qt.Key.Key_Space)
    app.processEvents()
    assert not model.get_studies(False)[0].include
    assert sum(s.include for s in model.get_studies(False)) == 18
    window.out_path = str(Path(sys.argv[2]) / "confidence-subset.rcms")
    assert window.save() and window.open(window.out_path, raise_on_error=True)
    assert window.model.get_confidence_level() == 90
    assert not window.model.get_studies(False)[0].include
    window.action_go.trigger()
    app.processEvents()
    dialog = next(
        w
        for w in app.topLevelWidgets()
        if isinstance(w, analysis_setup_dialog.AnalysisSetupDialog) and w.isVisible()
    )
    from analysis_matrix import set_parameter

    set_parameter(app, dialog, "digits", 6)
    set_parameter(app, dialog, "rm.method", "DL")
    assert dialog.current_param_vals["conf.level"] == 90
    click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    view = next(
        w
        for w in app.topLevelWidgets()
        if isinstance(w, results_window.ResultsWindow) and w.isVisible()
    )
    compare_authority(
        view, authority(window, "binary", "DL", "z", 90), "binary", record
    )
    assert "Gonzalez" not in view.texts["Weights"]
    record(
        "confidence-subset-reopened",
        window,
        confidence=window.model.get_confidence_level(),
        included=[s.label for s in window.model.get_studies(only_if_included=True)],
    )
    view.close()


def zero_cells(app, window, record):
    def prepare(window):
        model = window.model
        columns = list(model.RAW_DATA)
        for row, column in ((0, columns[0]), (1, columns[0]), (1, columns[2])):
            assert model.setData(model.index(row, column), "0")
        assert sum(s.include for s in model.get_studies(False)) == 19
        record("zero-cell-fixture", window, rows=raw_rows(window))

    for policy in ("only0", "all"):
        view = matrix(
            app,
            window,
            "analysis-amino-binary-cumulative",
            record,
            keep_results=True,
            workflow_override="standard",
            prepare=prepare,
            parameters={"to": policy, "digits": 6, "rm.method": "DL"},
        )
        compare_authority(
            view, authority(window, "binary", "DL", "z", 95, policy), "binary", record
        )
        assert len(view.texts["Weights"].strip().splitlines()) == 20
        view.close()
        window.workspace.mark_saved()

    # One participant per group leaves no residual degrees of freedom for SMD.
    assert window.open(str(ROOT / "sample_projects/continuous.rcms"), raise_on_error=True)
    window.tableView.set_metric_in_ui("SMD")
    model = window.model
    for column in (model.RAW_DATA[0], model.RAW_DATA[3]):
        assert model.setData(model.index(0, column), "1"), model.last_data_error
    assert [model.data(model.index(0, column)) for column in model.OUTCOMES] == [
        "Not estimable", "\u2014", "\u2014"
    ]
    assert "complete raw data" in model.data(model.index(0, model.OUTCOMES[0]), QtCore.Qt.ItemDataRole.ToolTipRole)
    record("smd-not-estimable", window, raw=raw_rows(window)[0])
    # The same means still define an ordinary mean difference.
    window.tableView.set_metric_in_ui("MD")
    assert math.isfinite(float(model.data(model.index(0, model.OUTCOMES[0]))))
    record("md-estimable-with-supplied-sd", window)
    window.tableView.set_metric_in_ui("SMD")
    path = Path(sys.argv[2]) / "not-estimable.rcms"
    window.out_path = str(path)
    assert window.save() and window.open(str(path), raise_on_error=True)
    model = window.model
    assert model.data(model.index(0, model.OUTCOMES[0])) == "Not estimable"
    assert model.setData(model.index(0, model.RAW_DATA[0]), "20")
    assert math.isfinite(float(model.data(model.index(0, model.OUTCOMES[0]))))
    assert model.setData(model.index(0, model.RAW_DATA[0]), "")
    assert [model.data(model.index(0, column)) for column in model.OUTCOMES] == ["", "", ""]
    record("smd-estimable-recovery-and-incomplete", window)


def plots(app, window, family, record, *, view=None):
    producer = {
        "forest": "analysis-binary.fixed.inv.var",
        "cumulative": "analysis-amino-binary-cumulative",
        "leave-one-out": "analysis-amino-binary-leave-one-out",
        "subgroup": "analysis-amino-binary-subgroup",
        "regression": "analysis-amino-binary-meta-regression",
        "sroc": "analysis-diagnostic-joint",
        "coefficient": "analysis-diagnostic-regression-continuous",
        "funnel": "small-study-binary-extended",
        "contour": "small-study-binary-extended",
        "trimfill": "small-study-binary-extended",
        "deeks": "small-study-diagnostic",
    }[family]
    if view is None:
        view = matrix(app, window, producer, record, keep_results=True)
    kind = {
        "coefficient": "forest",
        "contour": "contour_funnel",
        "trimfill": "trimfill_funnel",
        "deeks": "deeks_funnel",
        "cumulative": "cumulative_forest",
        "leave-one-out": "leave_one_out_forest",
        "subgroup": "subgroup_forest",
    }.get(family, family)
    artifacts = [
        view.create_plot_artifact(
            title, path, params_path=view.results.image_params_paths.get(title)
        )
        for title, path in view.results.images.items()
    ]
    artifact = next(
        a
        for a in artifacts
        if a.plot_kind == kind
        and a.params_path
        and (
            family != "coefficient"
            or view.plot_service.load_params(a.params_path).get(
                "reitsma.coefficient.scale"
            )
        )
    )
    item = None
    # Results attaches its artifact to the context callback closure.
    for candidate in (*view._svg_plot_items, *view._raster_plot_items):
        callback = candidate.contextMenuEvent
        cells = [
            c.cell_contents for c in (getattr(callback, "__closure__", None) or ())
        ]
        if any(getattr(c, "title", None) == artifact.title for c in cells):
            item = candidate
            break
    assert item is not None, artifact.title
    texts = dict(view.texts)
    path = Path(artifact.display_path())
    before = path.read_bytes()
    from tests.e2e.audit_round3 import check_caption
    from rc_metastudio.analysis_identity import dataset_identity, metric_label
    initial_svg = path
    if path.suffix != ".svg":
        initial_svg = Path(sys.argv[2]) / (family + "-initial.svg")
        view.plot_service.export(regenerator=artifact.capability.regenerator, params_path=artifact.params_path, output_path=str(initial_svg))
    check_caption(initial_svg, dataset_identity(window.model))
    if artifact.capability.regenerator == "forest":
        from tests.e2e.header_geometry import check_forest_footer
        check_forest_footer(initial_svg)
    if family in {"funnel", "contour", "trimfill"}:
        from xml.etree import ElementTree as ET
        labels = {"".join(node.itertext()) for node in ET.parse(initial_svg).iter("{http://www.w3.org/2000/svg}text")}
        assert "Standard error (log scale)" in labels, labels
        assert metric_label(window.model).casefold() in {label.casefold() for label in labels}, labels

    section = next(section for section in view.results.sections if section.source_key == artifact.title)
    navigation = view.nav_tree.findItems(section.title, QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)
    assert len(navigation) == 1, (family, section.title)
    view.nav_tree.setCurrentItem(navigation[0])
    view.report_action.setChecked(False)
    view._show_report(False)
    app.processEvents()
    assert view._selected_plot()[0].title == artifact.title
    record("review1-caption-initial", view, family=family, plots={artifact.title: str(path)}, exports={"svg": str(initial_svg)})
    from rc_metastudio.funnel_plot_editor_dialog import FunnelPlotEditorDialog
    from rc_metastudio.plot_editor_dialog import EditPlotDialog

    funnel = artifact.capability.regenerator == "funnel"
    key = (
        "funnel.xlab"
        if funnel
        else "bp_xlabel"
        if family == "regression"
        else "fp_xlabel"
    )
    label = "Verified " + family + " axis"
    accepted = {}

    def snapshot():
        if artifact.capability.regenerator == "forest":
            check_forest_footer(path)
        base = Path(artifact.params_path)
        paths = [path, *(base.parent.glob(base.name + ".*"))]
        return {str(file): file.read_bytes() for file in paths if file.is_file()}

    def selected_controls(dialog):
        values = {
            "point_size": (
                dialog.point_size_spin if funnel else dialog.point_size_multiplier
            ).value()
        }
        values["caption"] = dialog.figure_caption.text()
        if family == "contour":
            values["contour_levels"] = dialog.contour_levels_edit.text()
        elif family == "deeks":
            values["regression_visible"] = dialog.regression_visible_check.isChecked()
        elif family == "regression":
            values["confidence_band"] = dialog.show_confidence_band.isChecked()
            values["style"] = dialog.style_cbo.currentText()
        elif family == "sroc":
            values["prediction"] = dialog.sroc_show_prediction.isChecked()
        elif not funnel:
            values["style"] = dialog.style_cbo.currentText()
        if family == "forest":
            values["bounds"] = (dialog.plot_lb_le.text(), dialog.plot_ub_le.text())
            values["directions"] = (dialog.favours_left.text(), dialog.favours_right.text())
            values["order"] = dialog.study_order.currentData()
        return values

    def edit(dialog):
        if family in {"forest", "cumulative", "leave-one-out", "subgroup"}:
            original_style = dialog.style_cbo.currentText()
            original_directions = (dialog.favours_left.text(), dialog.favours_right.text())
            for names in (("Intervention", "Control"), (
                "Intensive individualized cognitive behavioural therapy plus structured clinical follow-up",
                "Intensive individualized cognitive behavioural therapy plus structured clinical follow-through",
            )):
                dialog.favours_left.setText("Favours " + names[0])
                dialog.favours_right.setText("Favours " + names[1])
                for style in ("Default (metafor)", "RevMan", "BMJ"):
                    dialog.style_cbo.setCurrentText(style)
                    click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Apply))
                    measurements = check_forest_footer(path)
                    retained = Path(sys.argv[2]) / f"{family}-{style.split()[0]}-arms-{len(names[0])}.svg"
                    retained.write_bytes(path.read_bytes())
                    record("forest-footer-geometry", dialog, family=family, style=style,
                           names=names, measurements=measurements, artifacts={"SVG": str(retained)})
            dialog.style_cbo.setCurrentText(original_style)
            dialog.favours_left.setText(original_directions[0])
            dialog.favours_right.setText(original_directions[1])
        field = dialog.x_label_edit if funnel else dialog.x_lbl_le
        for heading in ("figure_caption", "col1_str_edit", "col2_str_edit", "col3_str_edit", "col4_str_edit", "x_lbl_le", "x_label_edit", "y_label_edit"):
            control = getattr(dialog, heading, None)
            if control is not None and control.isVisible():
                text = control.text() or control.placeholderText()
                assert control.contentsRect().width() - 8 >= control.fontMetrics().horizontalAdvance(text), (heading, text, control.width())
        field.setText(label)
        assert dialog.figure_caption.isVisible(), "figure caption cannot be edited"
        assert dialog.figure_caption.text(), "standalone figure lacks context"
        assert " · None" not in dialog.figure_caption.text(), dialog.figure_caption.text()
        assert " · Comparison:" in dialog.figure_caption.text() or " · Group:" in dialog.figure_caption.text(), dialog.figure_caption.text()
        dialog.figure_caption.setText("Edited outcome / comparison / follow-up")
        if funnel:
            dialog.point_size_spin.setValue(1.8)
            if family == "contour":
                dialog.contour_levels_edit.setText("85,95,99")
            if family == "deeks":
                dialog.regression_visible_check.setChecked(False)
        else:
            dialog.point_size_multiplier.setValue(1.8)
            if family == "regression":
                dialog.show_confidence_band.setChecked(False)
                dialog.style_cbo.setCurrentText("BMJ")
            elif family == "sroc":
                dialog.sroc_show_prediction.setChecked(False)
            else:
                dialog.style_cbo.setCurrentText("RevMan")
            if family == "forest":
                dialog.plot_lb_le.setText("10")
                dialog.plot_ub_le.setText("11")
                assert [dialog.favours_left.text(), dialog.favours_right.text()] == ["Favours " + name for name in window.model.arm_names]
                dialog.favours_left.setText("Favours treatment")
                dialog.favours_right.setText("Favours control")
                dialog.study_order.setCurrentIndex(dialog.study_order.findData("year"))
        box = dialog.button_box if funnel else dialog.buttonBox
        if family == "forest":
            dialog.content_scroll.ensureWidgetVisible(dialog.favours_right)
            app.processEvents()
        dialog.content_scroll.ensureWidgetVisible(dialog.figure_caption)
        dialog.repaint()
        QTest.qWait(250)
        record("family-editor-controls", dialog, family=family, capture_surface="desktop-composite")
        click(app, box.button(QtWidgets.QDialogButtonBox.StandardButton.Apply))
        assert path.read_bytes() != before
        if funnel:
            from PIL import Image

            with Image.open(path) as image:
                image.load()
                assert image.width > 100 and image.height > 100
        else:
            assert QSvgRenderer(str(path)).isValid()
        params = view.plot_service.load_params(artifact.params_path)
        expected_params = {
            key: label,
            "funnel.point.size"
            if funnel
            else "bp_point_size_multiplier"
            if family == "regression"
            else "fp_point_size_multiplier": 1.8,
        }
        expected_params["plot_caption"] = "Edited outcome / comparison / follow-up"
        if not funnel:
            assert "Edited outcome / comparison / follow-up" in path.read_text()
        if family == "contour":
            expected_params["funnel.contour.levels"] = "85,95,99"
        elif family == "deeks":
            expected_params["funnel.regression.visible"] = False
        elif family == "regression":
            expected_params["bp_show_confidence_band"] = False
            expected_params["bp_style"] = "bmj"
        elif family == "sroc":
            expected_params["fp_show_prediction"] = False
        elif not funnel:
            expected_params["fp_style"] = "revman"
        if family == "forest":
            expected_params.update(fp_plot_lb="10", fp_plot_ub="11")
            expected_params.update(fp_favours_left="Favours treatment", fp_favours_right="Favours control", fp_study_order="year")
            from rc_metastudio import r_bridge

            r_bridge.ro.globalenv["verified_plot_path"] = (
                str(artifact.params_path) + ".plotdata"
            )
            bounds = list(
                r_bridge.ro.r(
                    "local({ state <- new.env(); load(verified_plot_path, envir=state); "
                    "RCMetaR:::rcmetar.forest.layout.preflight(state$plot.data)$x$alim })"
                )
            )
            assert all(
                math.isclose(actual, math.log(wanted), abs_tol=1e-10)
                for actual, wanted in zip(bounds, (10, 11), strict=True)
            ), bounds
        for name, value in expected_params.items():
            actual = params[name]
            if funnel and isinstance(actual, (list, tuple)):
                actual = actual[dialog._funnel_index - 1]
            assert actual == value, (name, params[name], value)
        if family == "regression":
            from xml.etree import ElementTree as ET
            for style in ("Default (metafor)", "RevMan", "BMJ"):
                dialog.style_cbo.setCurrentText(style)
                dialog.show_legend.setChecked(True)
                for line, confidence, prediction in ((True, False, False), (False, True, False), (True, True, True), (False, False, False)):
                    dialog.show_regression_line.setChecked(line)
                    dialog.show_confidence_band.setChecked(confidence)
                    dialog.show_prediction_interval.setChecked(prediction)
                    click(app, box.button(QtWidgets.QDialogButtonBox.StandardButton.Apply))
                    labels = {"".join(node.itertext()) for node in ET.parse(path).iter("{http://www.w3.org/2000/svg}text")}
                    assert ("Regression line" in labels) == line, labels
                    assert ("95% CI" in labels) == confidence, labels
                    assert ("95% PI" in labels) == prediction, labels
                    dialog.hide()
                    app.processEvents()
                    record("bubble-visible-legend", view, style=style, line=line,
                           confidence=confidence, prediction=prediction, labels=sorted(labels), plots={artifact.title: str(path)})
                    dialog.show()
            dialog.show_regression_line.setChecked(True)
            dialog.show_confidence_band.setChecked(False)
            dialog.show_prediction_interval.setChecked(False)
            click(app, box.button(QtWidgets.QDialogButtonBox.StandardButton.Apply))
        accepted["files"] = snapshot()
        accepted["controls"] = selected_controls(dialog)
        record(
            "family-plot-applied",
            dialog,
            family=family,
            parameters=expected_params,
            plots={artifact.title: str(path)},
        )
        field.setText("Uncommitted draft")
        QTest.mouseClick(
            box.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel),
            QtCore.Qt.MouseButton.LeftButton,
        )

    def context(action_text):
        view.graphics_view.ensureVisible(item)
        app.processEvents()
        point = view.graphics_view.mapFromScene(item.sceneBoundingRect().center())
        chosen = []
        errors = []
        deadline = QtCore.QDeadlineTimer(5000)

        def choose():
            menu = app.activePopupWidget()
            if not isinstance(menu, QtWidgets.QMenu):
                if deadline.hasExpired():
                    errors.append("plot context menu did not open")
                    return
                QtCore.QTimer.singleShot(10, choose)
                return
            try:
                action = next(a for a in menu.actions() if a.text() == action_text)
                QTest.mouseClick(
                    menu,
                    QtCore.Qt.MouseButton.LeftButton,
                    pos=menu.actionGeometry(action).center(),
                )
                chosen.append(action_text)
            except Exception as error:  # noqa: BLE001 - propagate Qt callback failures.
                traceback.print_exc()
                errors.append(error)
                menu.close()

        QtCore.QTimer.singleShot(0, choose)
        # One context event follows the real viewport/scene hit-test route.
        # A right-click plus this event can open two menus on some Qt platforms.
        viewport = view.graphics_view.viewport()
        event = QtGui.QContextMenuEvent(
            QtGui.QContextMenuEvent.Reason.Mouse, point, viewport.mapToGlobal(point)
        )
        QtWidgets.QApplication.sendEvent(viewport, event)
        while not chosen and not errors and not deadline.hasExpired():
            QTest.qWait(10)
        assert chosen and not errors, (action_text, errors)

    modal(
        app,
        FunnelPlotEditorDialog if funnel else EditPlotDialog,
        edit,
        lambda: context("Edit plot…"),
    )
    assert snapshot() == accepted["files"]
    applied = path.read_bytes()
    assert view.texts == texts
    record("family-plot-cancelled", view, family=family)

    def cancel(dialog):
        assert selected_controls(dialog) == accepted["controls"]
        assert (dialog.x_label_edit if funnel else dialog.x_lbl_le).text() == label
        (dialog.x_label_edit if funnel else dialog.x_lbl_le).setText("Second draft")
        dialog.figure_caption.clear()
        QTest.mouseClick(
            (dialog.button_box if funnel else dialog.buttonBox).button(
                QtWidgets.QDialogButtonBox.StandardButton.Cancel
            ),
            QtCore.Qt.MouseButton.LeftButton,
        )

    modal(
        app,
        FunnelPlotEditorDialog if funnel else EditPlotDialog,
        cancel,
        lambda: context("Edit plot…"),
    )
    assert path.read_bytes() == applied
    assert snapshot() == accepted["files"]
    view.fit_width_action.trigger()
    view.graphics_view.verticalScrollBar().setValue(0)
    app.processEvents()
    record("family-plot-reopened", view, family=family)
    files = export_formats(app, view, Path(sys.argv[2]), family, record,
                           lambda extension, action_label: context("Export " + action_label + "…"))
    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=("", "")):
        context("Export SVG…")
    assert path.read_bytes() == applied
    assert snapshot() == accepted["files"]
    assert view.texts == texts
    record(
        "family-exports-cancelled",
        view,
        family=family,
        exports=files,
        plots={artifact.title: str(path)},
        text_unchanged=True,
    )
    assert "Edited outcome / comparison / follow-up" in Path(files["svg"]).read_text()
    def remove_caption(dialog):
        assert dialog.figure_caption.isVisible()
        dialog.figure_caption.clear()
        box = dialog.button_box if funnel else dialog.buttonBox
        click(app, box.button(QtWidgets.QDialogButtonBox.StandardButton.Apply))
        assert view.plot_service.load_params(artifact.params_path)["plot_caption"] == ""
        without = Path(sys.argv[2]) / (family + "-without-caption.svg")
        view.plot_service.export(regenerator=artifact.capability.regenerator, params_path=artifact.params_path, output_path=str(without))
        assert "Edited outcome / comparison / follow-up" not in without.read_text()
        record("round5-caption-removed", dialog, family=family, exports={"svg":str(without)}, capture_surface="desktop-composite")
        dialog.reject()
    modal(app, FunnelPlotEditorDialog if funnel else EditPlotDialog, remove_caption, lambda: context("Edit plot…"))
    def reopen_without_caption(dialog):
        assert dialog.figure_caption.text() == ""
        dialog.reject()
    modal(app, FunnelPlotEditorDialog if funnel else EditPlotDialog, reopen_without_caption, lambda: context("Edit plot…"))
    view.close()


def export_formats(app, view, directory, family, record, invoke=None):
    directory.mkdir(parents=True, exist_ok=True)
    if invoke is None:
        def invoke(extension, _label):
            view.export_format_control.setCurrentIndex(view.export_format_control.findData(extension))
            view.export_plot_action.trigger()
            app.processEvents()
    files = {}
    for extension, action_label in (
        ("pdf", "PDF"),
        ("png", "PNG"),
        ("tiff", "TIFF"),
        ("svg", "SVG"),
    ):
        destination = directory / (family + "." + extension)
        with patch.object(
            QtWidgets.QFileDialog,
            "getSaveFileName",
            return_value=(str(destination), ""),
        ):
            invoke(extension, action_label)
        assert destination.is_file(), destination
        if extension == "svg":
            renderer = QSvgRenderer(str(destination))
            assert renderer.isValid()
            rendered = QtGui.QImage(400, 400, QtGui.QImage.Format.Format_RGB32)
            rendered.fill(QtCore.Qt.GlobalColor.white)
            painter = QtGui.QPainter(rendered)
            renderer.render(painter)
            painter.end()
        elif extension == "pdf":
            from PyQt6.QtPdf import QPdfDocument

            document = QPdfDocument(view)
            assert document.load(str(destination)) == QPdfDocument.Error.None_
            assert document.pageCount() == 1
            rendered = document.render(0, QtCore.QSize(400, 400))
            assert not rendered.isNull()
            document.close()
        else:
            from PIL import Image

            with Image.open(destination) as image:
                assert image.width > 100 and image.height > 100
                assert image.crop((0, 0, 1, 1)).convert("RGB").getpixel((0, 0)) == (255, 255, 255)
                image.load()
                assert (
                    min(
                        channel[0]
                        for channel in image.resize((256, 256))
                        .convert("RGB")
                        .getextrema()
                    )
                    < 200
                )
        if extension in ("svg", "pdf"):
            assert any(
                rendered.pixelColor(x, y).lightness() < 200
                for x in range(0, 400, 4)
                for y in range(0, 400, 4)
            ), "Export contains no visible plot content"
        files[extension] = str(destination)
        record(
            "family-export-decoded",
            view,
            family=family,
            format=extension,
            exports={extension: str(destination)},
        )
    return files


def calculators(app, window, mode, record):
    from rc_metastudio import r_bridge
    from rc_metastudio.binary_data_dialog import BinaryDataDialog
    from rc_metastudio.continuous_data_dialog import ContinuousDataDialog
    from rc_metastudio.diagnostic_data_dialog import DiagnosticDataDialog

    family = (
        "continuous"
        if mode in ("onearm-mean", "pre-post") or "continuous" in mode
        else "diagnostic"
        if "diagnostic" in mode
        else "binary"
    )
    if mode.startswith("onearm-"):
        matrix(app, window, "analysis-data-" + mode, record)
    else:
        sample = {"binary": "amino", "continuous": "continuous", "diagnostic": "lymph"}[
            family
        ]
        assert window.open(
            str(ROOT / f"sample_projects/{sample}.rcms"), raise_on_error=True
        )
    kind = {
        "binary": BinaryDataDialog,
        "continuous": ContinuousDataDialog,
        "diagnostic": DiagnosticDataDialog,
    }[family]
    before = list(
        window.model.get_current_analysis_unit_for_study(0).get_raw_data_for_arms(
            window.model.arm_names
        )
    )
    entered = mode.startswith("entered-")
    included_before = sum(study.include for study in window.model.get_studies(False))
    observed = {}

    def entered_values():
        unit = window.model.get_current_analysis_unit_for_study(0)
        return unit.get_entered_effect_and_ci(
            "Sens" if family == "diagnostic" else window.model.current_effect,
            window.model.get_current_arm_key(),
        )

    before_entered = entered_values()

    def cell(table, row, column, value):
        table.setCurrentCell(row, column)
        table.setFocus()
        table.editItem(table.item(row, column))
        app.processEvents()
        editor = next((field for field in table.findChildren(QtWidgets.QLineEdit) if field.isVisible()), None)
        assert editor is not None, (mode, row, column)
        QTest.keyClick(editor, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier)
        QTest.keyClicks(editor, str(value))
        QTest.keyClick(editor, QtCore.Qt.Key.Key_Tab)
        app.processEvents()

    def text(field, value):
        field.window().activateWindow()
        field.setFocus()
        deadline = QtCore.QDeadlineTimer(5000)
        while not field.hasFocus() and not deadline.hasExpired():
            QTest.qWait(10)
        assert field.hasFocus(), ("keyboard editor did not gain focus", mode, field.objectName())
        QTest.keyClick(field, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier)
        QTest.keyClicks(field, str(value))
        QTest.keyClick(field, QtCore.Qt.Key.Key_Tab)
        app.processEvents()

    def preview(dialog, metric):
        value = float(dialog.effect_text_box.text().replace(",", "."))
        raw = dialog.analysis_unit.get_raw_data_for_arms(dialog.arm_names)
        if family == "binary":
            a, n, c, m = raw
            expected = {
                "OR": lambda: (a / (n - a)) / (c / (m - c)),
                "RR": lambda: (a / n) / (c / m),
                "RD": lambda: a / n - c / m,
                "PR": lambda: a / n,
            }[metric]()
        elif family == "continuous":
            n, m, sd, n2, m2, sd2 = raw
            if metric == "TX Mean":
                expected = m
            elif metric == "MD":
                expected = m - m2
            else:
                # Exact small-sample Hedges correction used by metafor.
                df = n + n2 - 2
                correction = math.exp(
                    math.lgamma(df / 2)
                    - 0.5 * math.log(df / 2)
                    - math.lgamma((df - 1) / 2)
                )
                expected = (
                    correction
                    * (m - m2)
                    / math.sqrt(((n - 1) * sd**2 + (n2 - 1) * sd2**2) / df)
                )
        else:
            tp, fn, fp, tn = raw
            expected = tp / (tp + fn) if metric == "Sens" else tn / (tn + fp)
        assert abs(value - expected) <= 0.0001, (metric, value, expected)
        observed[metric] = {"actual": value, "expected": expected}

    def drive(dialog):
        if mode.startswith("back-"):
            click(app, dialog.clear_button)
            if family == "binary":
                for row in (0, 1):
                    cell(dialog.raw_data_table, row, 2, 100)
                effect = (10 / 90) / (5 / 95)
                se = math.sqrt(1 / 10 + 1 / 90 + 1 / 5 + 1 / 95)
                z = r_bridge.get_confidence_multiplier_from_r(95)
                values = (
                    effect,
                    math.exp(math.log(effect) - z * se),
                    math.exp(math.log(effect) + z * se),
                )
            elif family == "continuous":
                dialog.effect_combo_box.setCurrentIndex(
                    dialog.effect_combo_box.findData("MD")
                )
                for row, fields in enumerate(((20, 10, 2), (20, "", 2))):
                    for column, value in enumerate(fields):
                        cell(dialog.simple_table, row, column, value)
                z = r_bridge.get_confidence_multiplier_from_r(95)
                values = (2, 2 - z * math.sqrt(0.4), 2 + z * math.sqrt(0.4))
            else:
                z = r_bridge.get_confidence_multiplier_from_r(95)

                def diagnostic_interval(successes, failures):
                    logit = math.log(successes / failures)
                    se = math.sqrt(1 / successes + 1 / failures)
                    return (
                        successes / (successes + failures),
                        1 / (1 + math.exp(-(logit - z * se))),
                        1 / (1 + math.exp(-(logit + z * se))),
                    )

                values = diagnostic_interval(80, 20)
            for field, value in zip(
                (dialog.effect_text_box, dialog.lower_text_box, dialog.upper_text_box),
                values,
            ):
                text(field, value)
            if family == "diagnostic":
                dialog.effect_combo_box.setCurrentIndex(dialog.effect_combo_box.findData("Spec"))
                for field, value in zip(
                    (
                        dialog.effect_text_box,
                        dialog.lower_text_box,
                        dialog.upper_text_box,
                    ),
                    diagnostic_interval(90, 10),
                ):
                    text(field, value)
                text(dialog.prevalence_text_box, 0.5)
                assert dialog.back_calculate_button.isEnabled()
                click(app, dialog.back_calculate_button)
                assert dialog.analysis_unit.get_raw_data_for_arms(
                    dialog.arm_names
                ) == [80, 20, 10, 90]
            else:
                from rc_metastudio.binary_data_dialog import BinaryBackCalculationDialog
                from rc_metastudio.continuous_data_dialog import (
                    ContinuousBackCalculationDialog,
                )

                nested = (
                    BinaryBackCalculationDialog
                    if family == "binary"
                    else ContinuousBackCalculationDialog
                )
                raw_before = list(
                    dialog.analysis_unit.get_raw_data_for_arms(dialog.arm_names)
                )

                def dialog_state():
                    tables = dialog.findChildren(QtWidgets.QTableWidget)
                    return (
                        [
                            [
                                table.item(r, c).text() if table.item(r, c) else None
                                for r in range(table.rowCount())
                                for c in range(table.columnCount())
                            ]
                            for table in tables
                        ],
                        [
                            field.text()
                            for field in (
                                dialog.effect_text_box,
                                dialog.lower_text_box,
                                dialog.upper_text_box,
                            )
                        ],
                        getattr(dialog, "metric_parameter", None),
                        dialog.back_calculate_button.isEnabled(),
                    )

                state_before = dialog_state()

                def cancel_choice(choice):
                    app.processEvents()
                    if choice.screen().availableGeometry().height() >= 700:
                        assert choice.content_scroll.verticalScrollBar().maximum() == 0, ('reconstruction content hidden', mode, choice.size())
                    record("back-calculation-nested-cancel", choice, mode=mode)
                    click(
                        app,
                        choice.buttonBox.button(
                            QtWidgets.QDialogButtonBox.StandardButton.Cancel
                        ),
                    )

                assert dialog.back_calculate_button.isEnabled()
                modal(
                    app,
                    nested,
                    cancel_choice,
                    lambda: click(app, dialog.back_calculate_button),
                )
                assert (
                    dialog.analysis_unit.get_raw_data_for_arms(dialog.arm_names)
                    == raw_before
                )
                assert dialog_state() == state_before

                def accept_choice(choice):
                    click(app, choice.choice1_btn)
                    click(
                        app,
                        choice.buttonBox.button(
                            QtWidgets.QDialogButtonBox.StandardButton.Ok
                        ),
                    )

                modal(
                    app,
                    nested,
                    accept_choice,
                    lambda: click(app, dialog.back_calculate_button),
                )
                actual = dialog.analysis_unit.get_raw_data_for_arms(
                    dialog.arm_names
                )
                if family == "binary":
                    assert actual in ([10, 100, 5, 100], [95, 100, 90, 100]), actual
                    preview(dialog, "OR")
                else:
                    assert all(
                        math.isclose(a, b, abs_tol=0.0001)
                        for a, b in zip(actual, [20, 10, 2, 20, 8, 2])
                    ), actual
                    preview(dialog, "MD")
        elif entered:
            if family in {"binary", "continuous"}:
                dialog.input_mode_combo.setCurrentIndex(dialog.input_mode_combo.findData("estimate"))
            click(app, dialog.clear_button)
            assert all(
                v is None
                for v in dialog.analysis_unit.get_raw_data_for_arms(
                    dialog.arm_names
                )
            )
            values = (
                (0.12345678901234566, 1.2345678901234567e-8, 1e12)
                if family == "binary"
                else (0.12345678901234566, 1.2345678901234567e-8, 0.999999999999999)
                if family == "diagnostic"
                else (0.12345678901234566, -1.2345678901234567e-8, 1e12)
            )
            for field, value in zip(
                (dialog.effect_text_box, dialog.lower_text_box, dialog.upper_text_box),
                values,
            ):
                text(field, value)
            for field, value in zip(
                (dialog.effect_text_box, dialog.lower_text_box, dialog.upper_text_box),
                values,
            ):
                assert math.isclose(float(field.text()), value, abs_tol=0.0001)
            observed["entered"] = list(values)
            transform = (
                math.log
                if family == "binary"
                else (lambda value: math.log(value / (1 - value)))
                if family == "diagnostic"
                else float
            )
            point, lower, upper = [transform(value) for value in values]
            z = r_bridge.get_confidence_multiplier_from_r(95)
            observed["authority_entered"] = [point, (upper - point) / z]
            actual_entered = dialog.analysis_unit.get_entered_effect_and_ci(
                dialog.current_effect, dialog.arm_key
            )
            assert all(
                math.isclose(a, b, abs_tol=1e-10)
                for a, b in zip(actual_entered, (point, lower, upper))
            ), actual_entered
        elif mode == "pre-post":
            dialog.input_mode_combo.setCurrentIndex(dialog.input_mode_combo.findData("pre-post"))
            click(app, dialog.clear_button)
            combo = dialog.effect_combo_box
            combo.setCurrentIndex(combo.findData("MD"))
            for table, values in (
                (dialog.g1_pre_post_table, ((20, 10, 2), (20, 14, 3))),
                (dialog.g2_pre_post_table, ((20, 9, 2), (20, 10, 2))),
            ):
                for row, fields in enumerate(values):
                    for column, value in enumerate(fields):
                        cell(table, row, column, value)
            raw_zero = dialog.analysis_unit.get_raw_data_for_arms(
                dialog.arm_names
            )
            assert math.isclose(raw_zero[2], math.sqrt(13), abs_tol=0.0001), raw_zero
            text(dialog.correlation_pre_post, 0.5)
            expected = [20, 4, math.sqrt(7), 20, 1, 2]
            actual = dialog.analysis_unit.get_raw_data_for_arms(dialog.arm_names)
            assert all(
                math.isclose(a, b, abs_tol=0.0001) for a, b in zip(actual, expected)
            ), (actual, expected)
            preview(dialog, "MD")
            observed["raw"] = expected
        else:
            combo = dialog.effect_combo_box
            metrics = (
                ["PR"]
                if mode == "onearm-proportion"
                else ["TX Mean"]
                if mode == "onearm-mean"
                else {
                    "binary": ["OR", "RR", "RD"],
                    "continuous": ["MD", "SMD"],
                    "diagnostic": ["Sens", "Spec"],
                }[family]
            )
            for metric in metrics:
                index = (
                    combo.findData(metric)
                    if family != "diagnostic"
                    else combo.findData(metric)
                )
                assert index >= 0, metric
                combo.setCurrentIndex(index)
                app.processEvents()
                preview(dialog, metric)
            table = (
                dialog.raw_data_table
                if family == "binary"
                else dialog.simple_table
                if family == "continuous"
                else dialog.two_by_two_table
            )
            column = 1 if family == "continuous" else 0
            cell(table, 0, column, float(table.item(0, column).text()) + 1)
            preview(dialog, metrics[-1])
        if entered:
            before_invalid = list(dialog.analysis_unit.get_entered_effect_and_ci(dialog.current_effect, dialog.arm_key))
            modal(app, QtWidgets.QMessageBox,
                  lambda message: click(app, message.button(QtWidgets.QMessageBox.StandardButton.Ok)),
                  lambda: text(dialog.upper_text_box, "-1"))
            click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
            assert dialog.isVisible(), "invalid CI was accepted"
            assert list(dialog.analysis_unit.get_entered_effect_and_ci(dialog.current_effect, dialog.arm_key)) == before_invalid
            record("calculator-invalid-ci-blocked", dialog, mode=mode, entered=before_invalid)
            finished = []
            dialog.upper_text_box.editingFinished.connect(lambda: finished.append(True))
            text(dialog.upper_text_box, values[2])
            focus = app.focusWidget()
            record("calculator-ci-correction-state", dialog, mode=mode,
                   draft=dialog.upper_text_box.text(), expected_upper=values[2],
                   original_value=dialog.upper_text_box.property("calculatorValue"),
                   editing_finished=len(finished), has_focus=dialog.upper_text_box.hasFocus(),
                   focus=focus.objectName() if focus else None,
                   invalid=dialog._validation_failed,
                   stored=list(dialog.analysis_unit.get_entered_effect_and_ci(dialog.current_effect, dialog.arm_key)))
            assert finished, ("CI correction did not commit through editingFinished", mode)
            assert not dialog._validation_failed
        if family == "continuous" and not entered:
            if mode == "pre-post":
                dialog.input_mode_combo.setCurrentIndex(dialog.input_mode_combo.findData("summary"))
            # Each precision class is committed through the real delegate. The last
            # values persist through Cancel, undo/redo, save/reopen and a public fit.
            samples = ("0.00001", "1e12", "0,12345678901234566", "1.2345678901234567e-8")
            for value in samples:
                cell(dialog.simple_table, 0, 2, value)
                actual = dialog.analysis_unit.get_raw_data_for_arms(dialog.arm_names)[2]
                expected = float(value.replace(",", "."))
                record("calculator-precision-input", dialog, mode=mode, input=value,
                       stored=actual, expected=expected)
                assert actual == expected, ("raw precision lost", mode, value, actual)
            cell(dialog.simple_table, 0, 1, "0,12345678901234566")
            assert dialog.analysis_unit.get_raw_data_for_arms(dialog.arm_names)[1] == 0.12345678901234566
            cell(dialog.simple_table, 0, 0, "1e6")
            assert dialog.analysis_unit.get_raw_data_for_arms(dialog.arm_names)[0] == 1000000
            if mode not in {"onearm-mean", "pre-post"}:
                cell(dialog.simple_table, 1, 2, "1e12")
                assert dialog.analysis_unit.get_raw_data_for_arms(dialog.arm_names)[5] == 1e12
            # Generated group intervals must describe the edited mean and SD.
            from statistics import NormalDist
            n, mean, sd = dialog.analysis_unit.get_raw_data_for_arms(dialog.arm_names)[:3]
            headers = dialog.get_column_header_strs()
            z = NormalDist().inv_cdf(.975)
            for name, expected in (("Lower", mean-z*sd/math.sqrt(n)), ("Upper", mean+z*sd/math.sqrt(n))):
                column = headers.index(name)
                actual = float(dialog.simple_table.item(0, column).text())
                assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-15), (mode, name, actual, expected)
            if mode == "pre-post":
                dialog.input_mode_combo.setCurrentIndex(dialog.input_mode_combo.findData("pre-post"))
        observed["accepted_raw"] = list(
            dialog.analysis_unit.get_raw_data_for_arms(dialog.arm_names)
        )
        observed["metric"] = dialog.current_effect
        if entered:
            observed["accepted_entered"] = list(
                dialog.analysis_unit.get_effect_and_ci_for_source(
                    "entered",
                    dialog.current_effect,
                    dialog.arm_key,
                    dialog.confidence_multiplier,
                )
            )
        if family in {"binary", "continuous"}:
            if mode == "pre-post":
                assert dialog.pre_post_group_box.isVisible() and not dialog.simple_group.isVisible()
                dialog.input_mode_combo.setCurrentIndex(dialog.input_mode_combo.findData("summary"))
                assert dialog.simple_group.isVisible() and not dialog.pre_post_group_box.isVisible()
                dialog.input_mode_combo.setCurrentIndex(dialog.input_mode_combo.findData("pre-post"))
            app.processEvents()
            primary = (dialog.effect_text_box, dialog.clear_button,
                       dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
            if mode in {"onearm-proportion", "onearm-mean"}:
                assert not dialog.back_calculate_button.isVisible()
            else:
                primary += (dialog.back_calculate_button,)
            positions = [widget.mapTo(dialog, QtCore.QPoint()).y() for widget in primary]
            scrollbar = dialog.content_scroll.verticalScrollBar()
            for position in (0, scrollbar.maximum()):
                scrollbar.setValue(position)
                app.processEvents()
                assert [widget.mapTo(dialog, QtCore.QPoint()).y() for widget in primary] == positions
                assert all(widget.isVisible() and widget.visibleRegion().boundingRect().contains(widget.rect()) for widget in primary)
            record("calculator-mode-layout", dialog, mode=mode,
                   scroll_maximum=scrollbar.maximum(), positions=positions,
                   size=[dialog.width(), dialog.height()])
        from tests.e2e.review1_design import keyboard_traversal
        keyboard_traversal(app, dialog, [dialog.effect_combo_box, dialog.effect_text_box, dialog.lower_text_box, dialog.upper_text_box, dialog.buttonBox], record, "calculator-" + mode)
        record("calculator-mode-preview", dialog, mode=mode, observations=observed)
        click(
            app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        )

    def launch():
        header = window.tableView.verticalHeader()
        point = QtCore.QPoint(
            header.viewport().width() // 2,
            header.sectionViewportPosition(0) + header.sectionSize(0) // 2,
        )
        QTest.mouseClick(header.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=point)

    modal(app, kind, drive, launch)
    assert window.model.get_studies(False)[0].include
    assert (
        sum(study.include for study in window.model.get_studies(False)) == included_before
    )
    accepted_entered = entered_values()
    assert window.workspace.is_dirty
    assert (
        list(
            window.model.get_current_analysis_unit_for_study(0).get_raw_data_for_arms(
                window.model.arm_names
            )
        )
        == observed["accepted_raw"]
    )

    def cancel(dialog):
        click(app, dialog.clear_button)
        assert all(
            v is None
            for v in dialog.analysis_unit.get_raw_data_for_arms(dialog.arm_names)
        )
        click(
            app,
            dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel),
        )

    modal(app, kind, cancel, launch)
    assert entered_values() == accepted_entered
    # Compare actual raw/entered values rather than mutable state-object identity.
    assert (
        list(
            window.model.get_current_analysis_unit_for_study(0).get_raw_data_for_arms(
                window.model.arm_names
            )
        )
        == observed["accepted_raw"]
    )
    window.action_undo.trigger()
    assert entered_values() == before_entered
    assert (
        list(
            window.model.get_current_analysis_unit_for_study(0).get_raw_data_for_arms(
                window.model.arm_names
            )
        )
        == before
    )
    assert not window.workspace.is_dirty
    window.action_redo.trigger()
    assert entered_values() == accepted_entered
    assert (
        list(
            window.model.get_current_analysis_unit_for_study(0).get_raw_data_for_arms(
                window.model.arm_names
            )
        )
        == observed["accepted_raw"]
    )
    window.out_path = str(Path(sys.argv[2]) / "calculator-mode.rcms")
    assert window.save() and window.open(window.out_path, raise_on_error=True)
    assert window.model.get_studies(False)[0].include
    unit = window.model.get_current_analysis_unit_for_study(0)
    assert list(unit.get_raw_data_for_arms(window.model.arm_names)) == [
        "" if value is None else value for value in observed["accepted_raw"]
    ]
    if entered:
        comparison = window.model.get_current_arm_key()
        values = list(
            unit.get_effect_and_ci_for_source(
                "entered",
                observed["metric"],
                comparison,
                r_bridge.get_confidence_multiplier_from_r(95),
            )
        )
        assert values == observed["accepted_entered"], (values, observed)
    record(
        "calculator-mode-reopened",
        window,
        mode=mode,
        raw=unit.get_raw_data_for_arms(window.model.arm_names),
        entered=observed.get("accepted_entered"),
    )
    from rc_metastudio import analysis_setup_dialog, results_window
    from rc_metastudio.diagnostic_metrics_dialog import DiagnosticMetricsDialog

    window.action_go.trigger()
    app.processEvents()
    if family == "diagnostic":
        metrics_dialog = next(
            w
            for w in app.topLevelWidgets()
            if isinstance(w, DiagnosticMetricsDialog) and w.isVisible()
        )
        if entered:
            assert metrics_dialog._metric_checkbox("sens").isEnabled()
            assert all(
                not metrics_dialog._metric_checkbox(metric).isEnabled()
                for metric in ("spec", "dor", "lr")
            )
        for metric in metrics_dialog.SELECTABLE_METRICS:
            metrics_dialog._metric_checkbox(metric).setChecked(metric == "sens")
        click(app, metrics_dialog.btn_ok)
    setup = next(
        w
        for w in app.topLevelWidgets()
        if isinstance(w, analysis_setup_dialog.AnalysisSetupDialog) and w.isVisible()
    )
    from analysis_matrix import set_parameter

    method = family + ".random"
    setup.method_cbo_box.setCurrentText(
        next(label for label, key in setup.available_method_d.items() if key == method)
    )
    app.processEvents()
    set_parameter(app, setup, "digits", 6)
    set_parameter(app, setup, "rm.method", "DL")
    set_parameter(app, setup, "inference.method", "z")
    click(app, setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    view = next(
        w
        for w in app.topLevelWidgets()
        if isinstance(w, results_window.ResultsWindow) and w.isVisible()
    )
    metric = "Sens" if family == "diagnostic" else window.model.current_effect
    expected = authority(
        window,
        family,
        "DL",
        "z",
        95,
        entered=observed.get("authority_entered"),
        metric=metric,
    )
    compare_authority(view, expected, family, record, metric=metric)
    assert all(
        QSvgRenderer(str(p)).isValid() for p in view.results.display_images.values()
    )
    record(
        "calculator-mode-analysis",
        view,
        mode=mode,
        texts=dict(view.texts),
        plots=dict(view.results.display_images),
    )
    view.close()
    if entered and family in {"binary", "continuous"}:
        from tests.e2e.entered_ci import check
        check(app, window, kind, launch, text, family, record)
    if family == "diagnostic" and entered:
        saved_entered = entered_values()
        for invalid_input in ("empty", "partial"):

            def accept_invalid(dialog, invalid_input=invalid_input):
                if invalid_input == "empty":
                    click(app, dialog.clear_button)
                else:
                    # Keep the entered interval but introduce incomplete counts.
                    cell(dialog.two_by_two_table, 0, 0, 1)
                click(
                    app,
                    dialog.buttonBox.button(
                        QtWidgets.QDialogButtonBox.StandardButton.Ok
                    ),
                )

            modal(app, kind, accept_invalid, launch)
            assert not window.model.get_studies(False)[0].include
            if invalid_input == "partial":
                partial = window.model.get_current_analysis_unit_for_study(
                    0
                ).get_raw_data_for_arms(window.model.arm_names)
                assert partial[0] == 1 and all(
                    value in (None, "") for value in partial[1:]
                ), partial
            record("diagnostic-unusable-excluded", window, input=invalid_input)
            window.action_undo.trigger()
            assert window.model.get_studies(False)[0].include
            assert entered_values() == saved_entered
            assert all(
                value in (None, "")
                for value in window.model.get_current_analysis_unit_for_study(
                    0
                ).get_raw_data_for_arms(window.model.arm_names)
            )


def table_covariates(app, window, record):
    from rc_metastudio.add_new_dialogs import AddCovariateDialog

    assert window.open(str(ROOT / "sample_projects/amino.rcms"), raise_on_error=True)
    for name, kind in (("Dose", "continuous"), ("Region", "factor")):

        def add(dialog, name=name, kind=kind):
            dialog.covariate_name_le.setText(name)
            dialog.datatype_cbo_box.setCurrentIndex(dialog.datatype_cbo_box.findData(kind))
            click(
                app,
                dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok),
            )

        modal(app, AddCovariateDialog, add, window.action_add_covariate.trigger)
    table = window.tableView
    model = window.model
    columns = table.get_covariate_columns()
    dose_id, region_id = [c["id"] for c in model.current_sheet.covariates][-2:]
    first = model.index(0, columns[0])
    table.setCurrentIndex(first)
    values = "\n".join(f"{i + 1}\t{'North' if i % 2 else 'South'}" for i in range(19))
    app.clipboard().setText(values)
    window.action_paste.trigger()
    app.processEvents()
    assert model.current_sheet.rows[0].covariate_values == {dose_id: 1.0, region_id: "South"}
    assert model.current_sheet.rows[18].covariate_values == {
        dose_id: 19.0,
        region_id: "South",
    }
    window.action_undo.trigger()
    assert window.model.current_sheet.rows[0].covariate_values.get(dose_id) in (None, "")
    window.action_redo.trigger()
    model = window.model
    selection = QtCore.QItemSelection(
        model.index(0, columns[0]), model.index(18, columns[1])
    )
    table.selectionModel().select(
        selection, QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect
    )
    window.action_copy.trigger()
    assert [
        [float(row.split("\t")[0]), row.split("\t")[1]]
        for row in app.clipboard().text().strip().splitlines()
    ] == [[i + 1, "North" if i % 2 else "South"] for i in range(19)]
    identities = {
        s.id: (s.label, dict(s.covariate_values), s.include)
        for s in model.current_sheet.rows
    }
    table.scrollTo(window.model.index(0, window.model.NAME))
    app.processEvents()
    # A real header context event reaches sorting, including identity preservation.
    header = table.horizontalHeader()
    position = QtCore.QPoint(
        header.sectionViewportPosition(model.NAME)
        + header.sectionSize(model.NAME) // 2,
        header.height() // 2,
    )

    def choose_sort():
        menu = next(
            (
                w
                for w in app.topLevelWidgets()
                if isinstance(w, QtWidgets.QMenu) and w.isVisible()
            ),
            None,
        )
        if menu is None:
            QtCore.QTimer.singleShot(10, choose_sort)
            return
        action = next(
            a for a in menu.actions() if a.text() == "Sort studies by study name"
        )
        QTest.mouseClick(
            menu,
            QtCore.Qt.MouseButton.LeftButton,
            pos=menu.actionGeometry(action).center(),
        )

    QtCore.QTimer.singleShot(0, choose_sort)
    QtWidgets.QApplication.sendEvent(
        header.viewport(),
        QtGui.QContextMenuEvent(
            QtGui.QContextMenuEvent.Reason.Mouse,
            position,
            header.viewport().mapToGlobal(position),
        ),
    )
    app.processEvents()
    names = [
        window.model.data(window.model.index(row, window.model.NAME))
        for row in range(window.model.rowCount())
    ]
    names = [str(name) for name in names if name not in (None, "")]
    assert names == sorted(names, key=str.casefold), names
    assert {
        s.id: (s.label, dict(s.covariate_values), s.include)
        for s in window.model.current_sheet.rows
    } == identities
    window.out_path = str(Path(sys.argv[2]) / "covariates.rcms")
    assert window.save() and window.open(window.out_path, raise_on_error=True)
    assert {
        s.id: (s.label, dict(s.covariate_values), s.include)
        for s in window.model.current_sheet.rows
    } == identities
    record(
        "table-covariates-reopened",
        window,
        covariates=[(c["name"], c["data_type"]) for c in window.model.current_sheet.covariates],
        studies=list(identities.values()),
    )
    from analysis_matrix import set_parameter

    from rc_metastudio import analysis_setup_dialog, r_bridge, results_window
    from rc_metastudio.subgroup_analysis_dialog import SubgroupAnalysisDialog
    from tests.analysis_regression.golden.support.golden_analysis import (
        parsed_numeric_sections,
    )

    def visible(kind):
        return next(
            w for w in app.topLevelWidgets() if isinstance(w, kind) and w.isVisible()
        )

    rows = raw_rows(window)
    vector = lambda index: "c(" + ",".join(str(row[index]) for row in rows) + ")"
    effects = f'metafor::escalc("OR", ai={vector(0)}, n1i={vector(1)}, ci={vector(2)}, n2i={vector(3)}, add=.5, to="only0", drop00=FALSE)'
    included = [study for study in window.model.current_sheet.rows if study.include]
    dose = (
        "c(" + ",".join(str(study.covariate_values[dose_id]) for study in included) + ")"
    )
    for workflow in ("meta-regression", "subgroup"):
        (
            window.action_meta_regression
            if workflow == "meta-regression"
            else window.action_subgroup_ma
        ).trigger()
        app.processEvents()
        if workflow == "subgroup":
            choice = visible(SubgroupAnalysisDialog)
            choice.covariate_combo_box.setCurrentText("Region")
            click(
                app,
                choice.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok),
            )
        setup = visible(analysis_setup_dialog.AnalysisSetupDialog)
        if workflow == "meta-regression":
            for covariate, checkbox in setup.covs_and_check_boxes:
                checkbox.setChecked(covariate["name"] == "Dose")
            setup.fixed_effects_radio.setChecked(False)
        else:
            setup.method_cbo_box.setCurrentText(
                next(
                    label
                    for label, method in setup.available_method_d.items()
                    if method == "binary.random"
                )
            )
        app.processEvents()
        set_parameter(app, setup, "digits", 6)
        set_parameter(app, setup, "rm.method", "DL")
        click(app, setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
        view = visible(results_window.ResultsWindow)
        actual = parsed_numeric_sections(view.results)
        record(
            "covariates-analysis",
            view,
            workflow=workflow,
            texts=dict(view.texts),
            plots=dict(view.results.display_images),
            actual=actual,
        )
        if workflow == "meta-regression":
            expression = f'{{ e <- {effects}; f <- metafor::rma.uni(e$yi, vi=e$vi, mods=~{dose}, method="DL"); jsonlite::toJSON(list(coefficient=as.numeric(f$b[2]), standard_error=f$se[2], lower_bound=f$ci.lb[2], upper_bound=f$ci.ub[2], p_value=f$pval[2]), auto_unbox=TRUE, digits=16) }}'
            expected = json.loads(str(r_bridge.execute_r_string(expression)[0]))
            for key, value in expected.items():
                assert abs(actual["Summary"]["model.dose." + key] - value) <= 1e-6, (
                    actual,
                    expected,
                )
        else:
            for region in ("North", "South"):
                mask = (
                    "c("
                    + ",".join(
                        "TRUE"
                        if study.covariate_values[region_id] == region
                        else "FALSE"
                        for study in included
                    )
                    + ")"
                )
                expression = f'{{ e <- {effects}; f <- metafor::rma.uni(e$yi[{mask}], vi=e$vi[{mask}], method="DL"); as.numeric(exp(f$b)) }}'
                expected = float(r_bridge.execute_r_string(expression)[0])
                assert (
                    abs(
                        actual["Subgroup Summary"][
                            "model.subgroup_" + region.lower() + ".estimate"
                        ]
                        - expected
                    )
                    <= 1e-6
                ), (actual, region, expected)
        view.close()

    from rc_metastudio.covariate_type_dialog import CovariateTypeDialog
    sheet_id = window.model.current_sheet_id
    other_sheet = window.model.dataset.sheets[1]
    other_before = [(r.id, dict(r.covariate_values)) for r in other_sheet.rows], list(other_sheet.covariates)
    dose = next(c for c in window.model.current_sheet.covariates if c["id"] == dose_id)
    def convert(dialog):
        assert dialog.cov_model.rowCount() == 19
        assert dialog.cov_model.setData(dialog.cov_model.index(0, 2), "Low")
        dialog.accept()
    modal(app, CovariateTypeDialog, convert, lambda: window.change_covariate_type(dose))
    converted = window.model.current_sheet.covariates[-1]
    assert converted["name"] == "Dose (category)"
    assert window.model.current_sheet.rows[0].covariate_values[converted["id"]] == "Low"
    window._commit_model_operation(lambda: window.model.rename_covariate("Dose (category)", "Dose category"))
    window.delete_covariate(converted)
    assert converted["id"] not in [c["id"] for c in window.model.current_sheet.covariates]
    window.undo()
    assert converted["id"] in [c["id"] for c in window.model.current_sheet.covariates]
    assert ([(r.id, dict(r.covariate_values)) for r in window.model.dataset.sheets[1].rows], list(window.model.dataset.sheets[1].covariates)) == other_before
    assert window.model.current_sheet_id == sheet_id
    window.out_path = str(Path(sys.argv[2]) / "covariate-types.rcms")
    assert window.save() and window.open(window.out_path, raise_on_error=True)
    assert window.model.current_sheet.covariates[-1]["name"] == "Dose category"
    record("sheet-covariate-type-edit-delete-undo-reopened", window, covariates=window.model.current_sheet.covariates)


def shell(app, window, record):
    from rc_metastudio.about_legal_dialog import AboutLegalDialog
    from rc_metastudio.launch import _show_main_window
    from rc_metastudio.settings import save_main_window_placement

    def wait_for_state(predicate):
        deadline = QtCore.QDeadlineTimer(5000)
        stable = QtCore.QElapsedTimer()
        while not deadline.hasExpired():
            if predicate():
                if not stable.isValid():
                    stable.start()
                if stable.elapsed() >= 200:
                    return
            else:
                stable.invalidate()
            QTest.qWait(10)
        assert predicate(), "native window state did not settle within five seconds"

    def luminance(color):
        channels = [value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4
                    for value in (color.redF(), color.greenF(), color.blueF())]
        return sum(value*weight for value,weight in zip(channels, (.2126,.7152,.0722)))
    palette = window.palette()
    contrasts = []
    for foreground, background in ((QtGui.QPalette.ColorRole.WindowText, QtGui.QPalette.ColorRole.Window),
                                   (QtGui.QPalette.ColorRole.Text, QtGui.QPalette.ColorRole.Base),
                                   (QtGui.QPalette.ColorRole.ButtonText, QtGui.QPalette.ColorRole.Button)):
        a,b = palette.color(foreground), palette.color(background)
        low,high = sorted((luminance(a), luminance(b)))
        ratio = (high+.05)/(low+.05)
        assert ratio >= 4.5, (foreground.name, a.name(), b.name(), ratio)
        contrasts.append(dict(role=foreground.name, foreground=a.name(), background=b.name(), ratio=ratio))
    record("native-normal-text-contrast", window, measured_pairs=contrasts,
           scope="Qt active palette pairs on this host; excludes inactive controls and screen-reader qualification")

    # Startup must maximize even after a previous normal or full-screen session.
    window.showNormal()
    window.resize(700, 500)
    wait_for_state(lambda: not window.isMaximized() and not window.isFullScreen() and window.size() == QtCore.QSize(700, 500))
    save_main_window_placement(window, window.tableView.column_width_state())
    remembered_size = window.size()
    _show_main_window(window)
    wait_for_state(lambda: window.isMaximized() and not window.isFullScreen())
    assert window.isMaximized() and not window.isFullScreen()
    record("startup-maximized-after-normal", window)
    window.showNormal()
    deadline = QtCore.QDeadlineTimer(5000)
    while window.size() != remembered_size and not deadline.hasExpired():
        QTest.qWait(10)
    assert window.size() == remembered_size, (window.size(), remembered_size)
    record("startup-restored-normal-geometry", window, width=window.width(), height=window.height())
    window.showFullScreen()
    wait_for_state(window.isFullScreen)
    save_main_window_placement(window, window.tableView.column_width_state())
    _show_main_window(window)
    wait_for_state(lambda: window.isMaximized() and not window.isFullScreen())
    assert window.isMaximized() and not window.isFullScreen()
    record("startup-maximized-after-full-screen", window)

    sample = str(ROOT / "sample_projects/amino.rcms")
    with patch.object(
        QtWidgets.QFileDialog, "getOpenFileName", return_value=(sample, "")
    ):
        window.action_open.trigger()
    assert window.model.get_studies(False)[0].label == "Gonzalez"
    assert window.model.setData(
        window.model.index(0, window.model.NAME), "Unsaved study"
    )

    def cancel(message):
        record("dirty-open-prompt", message, message=message.text())
        click(app, message.button(QtWidgets.QMessageBox.StandardButton.Cancel))

    with patch.object(
        QtWidgets.QFileDialog,
        "getOpenFileName",
        return_value=(str(ROOT / "sample_projects/continuous.rcms"), ""),
    ):
        modal(app, QtWidgets.QMessageBox, cancel, window.action_open.trigger)
    assert window.model.get_studies(False)[0].label == "Unsaved study"
    assert window.workspace.is_dirty
    destination = Path(sys.argv[2]) / "shell.rcms"
    with patch.object(
        QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(destination), "")
    ):
        window.action_save_as.trigger()
    assert destination.is_file() and not window.workspace.is_dirty
    action = next(
        a
        for a in window.action_open_recent_2.actions()
        if str(a.data()) == str(destination)
    )
    action.trigger()
    assert window.model.get_studies(False)[0].label == "Unsaved study"

    def about(dialog):
        text = dialog.content_scroll_area.toPlainText()
        assert "RC MetaStudio" in text
        app.processEvents()
        if dialog.screen().availableGeometry().height() >= 700:
            assert dialog.content_scroll_area.verticalScrollBar().maximum() == 0, ('About content hidden', dialog.size())
        record("about-legal", dialog, text=text)
        dialog.reject()

    modal(app, AboutLegalDialog, about, window.action_about_legal.trigger)
    assert window.isVisible() and window.action_go.isEnabled()
    record(
        "shell-reopened",
        window,
        project=window.out_path,
        name=window.model.get_studies(False)[0].label,
    )


def run(app, window, scenario, record):
    if scenario == "project-axis-sequential":
        from tests.e2e.axis_conventions import run_sequential
        run_sequential(app, window, Path(sys.argv[2]), record)
        return
    if scenario.startswith("project-axis-"):
        from tests.e2e.axis_conventions import run as axes
        axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
        return
    if scenario == "calculator-ratio-precision":
        from tests.e2e.ratio_precision import run as ratio_precision
        ratio_precision(app, window, Path(sys.argv[2]), record)
        return
    if scenario.startswith("project-reviewer-"):
        from tests.e2e.reviewer_fixes import run_predictions, run_groups, run_colours
        driver = {"predictions":run_predictions, "groups":run_groups, "colours":run_colours}[scenario.rsplit("-",1)[-1]]
        driver(app, window, Path(sys.argv[2]), record)
        return
    if scenario == "project-release-coefficients":
        from tests.e2e.release_fixes import run_coefficients
        run_coefficients(app, window, Path(sys.argv[2]), record)
        return
    if scenario == "project-round6-polish":
        from tests.e2e.round6_polish import run as polish
        polish(app, window, Path(sys.argv[2]), record)
        return
    if scenario == "project-display-labels":
        from tests.e2e.display_labels import run as labels
        labels(app, window, record)
        return
    if scenario == "calculator-grid-precision":
        from tests.e2e.precision_inputs import run as precision
        precision(app, window, record)
        return
    if scenario.startswith("analysis-sequential-"):
        from sequential_workflows import run as sequential

        sequential(app, window, scenario, record)
    elif scenario == "options-confidence-inclusion":
        confidence_inclusion(app, window, record)
    elif scenario == "options-zero-cells":
        zero_cells(app, window, record)
    elif scenario == "project-table-covariates":
        table_covariates(app, window, record)
    elif scenario == "project-shell":
        shell(app, window, record)
    elif scenario.startswith("options-"):
        options(app, window, scenario.removeprefix("options-"), record)
    elif scenario.startswith("plot-workflow-"):
        plots(app, window, scenario.removeprefix("plot-workflow-"), record)
    else:
        calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
