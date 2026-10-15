# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Drive application controls with the production R backend."""

import json
import os
import shutil
import sys
import traceback
from typing import Callable, cast
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtTest import QTest

from tests.python.gui.test_types import key_click, mouse_click, required

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(sys.argv[2])

# Keep preferences and working artifacts out of the user's normal workspace.
QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
QtCore.QSettings.setPath(
    QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope, str(WORK)
)
QtCore.QStandardPaths.setTestModeEnabled(True)

from rc_metastudio import r_backend

r_backend.install_r_backend()

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()

from rc_metastudio import analysis_setup_dialog, automation, results_window, settings
from tests.analysis_regression.golden.support.golden_analysis import (
    parsed_numeric_sections,
)

EVIDENCE = (
    Path(os.environ["RCMS_E2E_EVIDENCE_DIR"])
    if os.environ.get("RCMS_E2E_EVIDENCE_DIR")
    else None
)
STEP = 0


def record_step(action, *widgets, **observations):
    """Capture the action and its observed state while the relevant UI still exists."""
    global STEP
    if EVIDENCE is None:
        return
    STEP += 1
    captures = []
    for index, widget in enumerate(widgets):
        path = EVIDENCE / f"{STEP:02d}-{index}-{action}.png"
        if app.platformName() in {"windows", "xcb", "cocoa"}:
            widget.raise_()
            widget.activateWindow()
            app.processEvents()
            cast(Callable[[int], None], QTest.qWait)(100)
            if observations.get("capture_surface") == "desktop-composite":
                capture = widget.screen().grabWindow(0)
                ratio = capture.devicePixelRatio()
                geometry = widget.frameGeometry()
                origin = widget.screen().geometry().topLeft()
                capture = capture.copy(round((geometry.x() - origin.x()) * ratio),
                                       round((geometry.y() - origin.y()) * ratio),
                                       round(geometry.width() * ratio), round(geometry.height() * ratio))
            else:
                capture = widget.screen().grabWindow(int(widget.winId()))
        else:
            capture = widget.grab()
        assert capture.save(str(path), "PNG"), path
        captures.append(path.name)
        if app.platformName() in {"windows", "xcb", "cocoa"} and action in {"analysis-results", "matrix-results", "small-study-results", "family-plot-cancelled"}:
            report_checked = widget.report_action.isChecked()
            original_nav_item = widget.nav_tree.currentItem()
            widget.report_action.setChecked(True)
            app.processEvents()
            cast(Callable[[int], None], QTest.qWait)(100)
            report_path = EVIDENCE / f"{STEP:02d}-{index}-{action}-report.png"
            assert widget.screen().grabWindow(int(widget.winId())).save(str(report_path), "PNG")
            captures.append(report_path.name)
            (EVIDENCE / f"{STEP:02d}-report.txt").write_text(widget.report_text.toPlainText(), encoding="utf-8")
            if widget.tables_action.isEnabled():
                widget.tables_action.trigger()
                app.processEvents()
                cast(Callable[[int], None], QTest.qWait)(100)
                table_path = EVIDENCE / f"{STEP:02d}-{index}-{action}-table.png"
                assert widget.screen().grabWindow(int(widget.winId())).save(str(table_path), "PNG")
                captures.append(table_path.name)
                for table_index, table in enumerate(widget._report_tables):
                    if table.title == "Test of subgroup differences":
                        widget.table_selector.setCurrentIndex(table_index)
                        app.processEvents()
                        cast(Callable[[int], None], QTest.qWait)(100)
                        subgroup_path = EVIDENCE / f"{STEP:02d}-{index}-{action}-subgroup-test.png"
                        assert widget.screen().grabWindow(int(widget.winId())).save(str(subgroup_path), "PNG")
                        captures.append(subgroup_path.name)
                        widget.table_selector.setCurrentIndex(0)
            widget.report_action.setChecked(report_checked)
            widget._show_report(report_checked)
            app.processEvents()
            widget.nav_tree.setCurrentItem(getattr(widget, "_last_plot_item", original_nav_item))
            widget.report_action.setChecked(False)
            widget._show_report(False)
            scroll = widget.graphics_view.verticalScrollBar()
            position = scroll.value()
            widget._scroll_to_section(widget.nav_tree.currentItem())
            app.processEvents()
            cast(Callable[[int], None], QTest.qWait)(100)
            figure_path = EVIDENCE / f"{STEP:02d}-{index}-{action}-figure.png"
            assert widget.screen().grabWindow(int(widget.winId())).save(str(figure_path), "PNG")
            captures.append(figure_path.name)
            selected_plot = widget._selected_plot()
            if selected_plot is not None:
                bottom = selected_plot[1].sceneBoundingRect().bottom() * widget.graphics_view.transform().m22()
                scroll.setValue(round(bottom - widget.graphics_view.viewport().height() + 30))
            app.processEvents()
            cast(Callable[[int], None], QTest.qWait)(100)
            bottom_path = EVIDENCE / f"{STEP:02d}-{index}-{action}-bottom.png"
            assert widget.screen().grabWindow(int(widget.winId())).save(str(bottom_path), "PNG")
            captures.append(bottom_path.name)
            scroll.setValue(position)
            widget.nav_tree.setCurrentItem(original_nav_item)
            widget.report_action.setChecked(report_checked)
            widget._show_report(report_checked)
            app.processEvents()
    artifacts = {}
    for index, (title, source) in enumerate(observations.get("plots", {}).items()):
        source = Path(source)
        destination = EVIDENCE / f"{STEP:02d}-{index}-{source.name}"
        shutil.copy2(source, destination)
        artifacts[title] = destination.name
    event = {
        "step": STEP,
        "action": action,
        "utc": datetime.now(UTC).isoformat(),
        "captures": captures,
        "artifacts": artifacts,
        **observations,
    }
    with (EVIDENCE / "steps.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")


def doctor(app, window):
    from importlib import metadata

    from rc_metastudio import r_bridge
    from scripts.r_dependency_policy import load_policy

    policy = load_policy(ROOT / "config/r-dependencies.json")
    r_version = r_bridge.get_r_version_string()
    assert r_version.startswith("R version " + policy["r_version"] + " "), r_version
    assert (
        metadata.version("rpy2")
        == json.loads((ROOT / "config/r-dependencies.json").read_text())[
            "target_runtime"
        ]["rpy2"]
    )
    # packageVersion canonicalizes hyphens to dots; the manifest uses DCF spellings.
    versions = {
        name: str(
            r_bridge.execute_r_function("packageDescription", name).rx2("Version")[0]
        )
        for name in policy["pinned_authorities"]
    }
    assert versions == policy["pinned_authorities"], versions
    description = (ROOT / "r/RCMetaR/DESCRIPTION").read_text()
    rcmetar_version = next(
        line.split(":", 1)[1].strip()
        for line in description.splitlines()
        if line.startswith("Version:")
    )
    assert r_bridge.get_r_package_version("RCMetaR") == rcmetar_version
    assert window.isVisible()
    assert Path(settings.get_base_path()).resolve() == WORK.resolve()
    identity = {
        "r": r_version,
        "r_libraries": r_bridge.get_r_library_paths(),
        "r_home": os.environ.get("R_HOME"),
        "authorities": versions,
        "rcmetar": rcmetar_version,
        "rpy2": metadata.version("rpy2"),
        "qt": QtCore.qVersion(),
        "pyqt": QtCore.PYQT_VERSION_STR,
        "platform_plugin": app.platformName(),
        "application": app.applicationName(),
        "qt_build_root": os.environ.get("RCMS_QT6_BUILD_ROOT"),
        "application_base_path": settings.get_base_path(),
    }
    if EVIDENCE is not None:
        (EVIDENCE / "runtime.json").write_text(
            json.dumps(identity, indent=2) + "\n", encoding="utf-8"
        )
    record_step("ready", window, runtime=identity)


def analyze(app, window, method):
    from rc_metastudio.diagnostic_metrics_dialog import DiagnosticMetricsDialog

    assert window.action_go.isEnabled()
    record_step("analysis-action", window, method=method)
    window.action_go.trigger()
    app.processEvents()
    if window.model.get_current_outcome_type() == "diagnostic":
        metrics = next(
            w
            for w in app.topLevelWidgets()
            if isinstance(w, DiagnosticMetricsDialog) and w.isVisible()
        )
        for metric in metrics.SELECTABLE_METRICS:
            checkbox = metrics._metric_checkbox(metric)
            if checkbox.isChecked() != (metric == "dor"):
                mouse_click(checkbox, QtCore.Qt.MouseButton.LeftButton)
        mouse_click(metrics.btn_ok, QtCore.Qt.MouseButton.LeftButton)
        app.processEvents()
    dialog = next(
        w
        for w in app.topLevelWidgets()
        if isinstance(w, analysis_setup_dialog.AnalysisSetupDialog) and w.isVisible()
    )
    label = next(
        label for label, key in dialog.available_method_d.items() if key == method
    )
    dialog.method_cbo_box.setCurrentText(label)
    app.processEvents()
    precision_label = next(
        label
        for label in dialog.findChildren(QtWidgets.QLabel)
        if label.text().casefold() == "decimal places"
    )
    precision = precision_label.buddy()
    assert isinstance(precision, QtWidgets.QSpinBox)
    precision.setValue(3)
    record_step("analysis-configured", dialog, method=method, digits=3)
    button = dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
    assert button.isEnabled()
    mouse_click(required(button), QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()
    views = [
        w
        for w in app.topLevelWidgets()
        if isinstance(w, results_window.ResultsWindow) and w.isVisible()
    ]
    assert len(views) == 1, "analysis did not display results"
    view = views[0]
    assert view.scene.items(), "results scene is empty"
    assert any(
        isinstance(item, QtWidgets.QGraphicsTextItem) and item.toPlainText().strip()
        for item in view.scene.items()
    )
    for path in view.results.display_images.values():
        assert QSvgRenderer(str(path)).isValid(), path
    record_step(
        "analysis-results",
        view,
        texts=dict(view.texts),
        plots=dict(view.results.display_images),
    )
    return view


def sample_analysis(app, window, sample):
    assert window.open(
        str(ROOT / f"sample_projects/{sample}.rcms"), raise_on_error=True
    )
    first_study, study_count = {
        "amino": ("Gonzalez", 19),
        "continuous": ("Carroll", 6),
        "lymph": ("Kinderman", 17),
    }[sample]
    assert (
        str(window.model.data(window.model.index(0, window.model.NAME))) == first_study
    )
    assert sum(study.include for study in window.model.dataset.studies) == study_count
    method, case = {
        "amino": ("binary.random", "amino-binary-random"),
        "continuous": ("continuous.random", "continuous-random"),
        "lymph": ("diagnostic.random", "lymph-diagnostic-random-dor"),
    }[sample]
    view = analyze(app, window, method)
    contract = json.loads(
        (ROOT / "tests/analysis_regression/baseline/numeric-contract.json").read_text()
    )
    section = "Odds Ratio Summary" if sample == "lymph" else "Summary"
    expected_sections = next(c for c in contract["cases"] if c["id"] == case)[
        "sections"
    ]
    actual_sections = parsed_numeric_sections(view.results)
    expected = expected_sections[section]
    actual = actual_sections[section]
    rendered_text = "\n".join(
        item.toPlainText()
        for item in view.scene.items()
        if isinstance(item, QtWidgets.QGraphicsTextItem)
    )
    source_key = next(
        item.source_key for item in view.results.sections if item.title == section
    )
    assert view.texts[source_key].strip() in rendered_text, "summary was not displayed"
    policy = contract["tolerance_policy"]
    for title, values in expected_sections.items():
        assert title in actual_sections, (title, actual_sections)
        for key, value in values.items():
            tolerance = max(policy["absolute"], policy["relative"] * abs(value))
            assert key in actual_sections[title], (title, key)
            assert abs(actual_sections[title][key] - value) <= tolerance + 1e-12, (
                title,
                key,
                actual_sections[title][key],
                value,
            )
    record_step(
        "numerical-oracle",
        view,
        case=case,
        actual=actual,
        expected=expected,
        tolerance=0.001,
        actual_sections=actual_sections,
        expected_sections=expected_sections,
        tolerance_policy=policy,
    )
    assert view.results.display_images, "analysis produced no plot"
    title = next(iter(view.results.display_images))
    artifact = view.create_plot_artifact(
        title,
        view.results.display_images[title],
        params_path=view.results.image_params_paths[title],
    )
    exported = WORK / "forest.pdf"
    with patch.object(
        QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(exported), "")
    ):
        view.save_image_as(artifact, format="pdf")
    assert exported.read_bytes().startswith(b"%PDF-"), "plot export is not a PDF"
    record_step("pdf-exported", view, file=str(exported))
    view.close()


def editing(app, window):
    assert window.open(str(ROOT / "sample_projects/amino.rcms"), raise_on_error=True)
    table = window.tableView
    original = str(window.model.data(window.model.index(0, window.model.NAME)))
    record_step("table-before-edit", window, name=original)
    table.setCurrentIndex(window.model.index(0, window.model.NAME))
    table.edit(table.currentIndex())
    app.processEvents()
    editor = table.findChild(QtWidgets.QLineEdit)
    assert editor is not None
    editor.setText("München – edited")
    key_click(editor, QtCore.Qt.Key.Key_Return)
    app.processEvents()
    assert (
        str(window.model.data(window.model.index(0, window.model.NAME)))
        == "München – edited"
    )
    assert table.currentIndex().row() == 1
    assert window.workspace.is_dirty
    window.action_undo.trigger()
    assert str(window.model.data(window.model.index(0, window.model.NAME))) == original
    assert not window.workspace.is_dirty
    window.action_redo.trigger()
    destination = WORK / "edited.rcms"
    with patch.object(
        QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(destination), "")
    ):
        assert window.save_as()
    assert not window.workspace.is_dirty
    assert window.open(str(destination), raise_on_error=True)
    assert (
        str(window.model.data(window.model.index(0, window.model.NAME)))
        == "München – edited"
    )
    # A malformed project must leave the current document and save path intact.
    broken = WORK / "broken.rcms"
    broken.write_bytes(b"not a project")
    with patch.object(
        QtWidgets.QMessageBox,
        "critical",
        return_value=QtWidgets.QMessageBox.StandardButton.Ok,
    ) as error:
        assert not window.open(str(broken))
    assert error.called
    assert (
        str(window.model.data(window.model.index(0, window.model.NAME)))
        == "München – edited"
    )
    assert window.out_path == str(destination)
    record_step(
        "edit-reopened",
        window,
        name="München – edited",
        project=str(destination),
        corrupt_open_preserved=True,
    )
    analyze(app, window, "binary.random").close()


def csv_import(app, window):
    from rc_metastudio import main_wizard

    csv = WORK / "studies.csv"
    csv.write_text(
        'Study Name,Year,Tx A #evts,Tx A #total,Tx B #evts,Tx B #total,OR,Lower,Upper,Dose,Region\n"Alpha, München",2020,1,10,2,12,,,,5.5,North\nBeta,2021,3,11,4,13,,,,7,South\nGamma,2022,2,20,5,20,,,,8,West\n',
        encoding="utf-8-sig",
    )
    wizard = main_wizard.MainWizard(path="csv_import")
    wizard.set_dataset_info(
        {
            "arms": "two",
            "data_type": "binary",
            "sub_type": "proportions",
            "effect": "OR",
            "metric_choices": [],
            "name": "Mortality",
        }
    )
    name_page = wizard.page(main_wizard.Page_OutcomeName)
    assert isinstance(name_page, main_wizard.OutcomeNamePage)
    name_page.outcome_name_LineEdit.setText("Mortality")
    wizard.setStartId(main_wizard.Page_CsvImport)
    wizard.restart()
    wizard.show()
    app.processEvents()
    page = wizard.currentPage()
    assert isinstance(page, main_wizard.CsvImportPage)
    with patch.object(
        QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(csv), "")
    ):
        mouse_click(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
    assert page.isComplete()
    assert page.preview_table.rowCount() == 3
    record_step("csv-preview", wizard, rows=3, file=str(csv))
    window._handle_wizard_results(wizard.get_results())
    wizard.close()
    assert (
        str(window.model.data(window.model.index(0, window.model.NAME)))
        == "Alpha, München"
    )
    assert window.model.dataset.studies[1].covariate_values["Dose"] == 7.0
    assert window.model.dataset.studies[1].covariate_values["Region"] == "South"
    assert all(study.include for study in window.model.dataset.studies)
    view = analyze(app, window, "binary.random")
    assert "Alpha" in view.texts.get("Weights", "")
    view.close()
    window.out_path = str(WORK / "imported.rcms")
    assert window.save()
    assert window.open(window.out_path, raise_on_error=True)
    assert window.model.dataset.studies[0].name == "Alpha, München"
    reopened = window.model.dataset.studies[1]
    assert reopened.covariate_values["Dose"] == 7.0
    assert reopened.covariate_values["Region"] == "South"
    assert window.model.current_effect == "OR"
    record_step(
        "csv-reopened",
        window,
        project=window.out_path,
        study="Alpha, München",
        dose=reopened.covariate_values["Dose"],
        region=reopened.covariate_values["Region"],
    )


def plot_edit(app, window):
    from rc_metastudio.plot_editor_dialog import EditPlotDialog

    assert window.open(str(ROOT / "sample_projects/amino.rcms"), raise_on_error=True)
    view = analyze(app, window, "binary.random")
    title = next(iter(view.results.display_images))
    path = Path(view.results.display_images[title])
    before = path.read_bytes()
    artifact = view.create_plot_artifact(
        title,
        view.results.images[title],
        params_path=view.results.image_params_paths[title],
    )
    callback_errors = []

    def edit():
        dialog = app.activeModalWidget()
        if not isinstance(dialog, EditPlotDialog):
            QtCore.QTimer.singleShot(10, edit)
            return
        try:
            dialog.x_lbl_le.setText("Edited effect axis")
            record_step("plot-edit-draft", dialog, axis="Edited effect axis")
            mouse_click(
                required(
                    dialog.buttonBox.button(
                        QtWidgets.QDialogButtonBox.StandardButton.Apply
                    )
                ),
                QtCore.Qt.MouseButton.LeftButton,
            )
            assert path.read_bytes() != before
            assert (
                view.plot_service.load_params(artifact.params_path)["fp_xlabel"]
                == "Edited effect axis"
            )
            dialog.x_lbl_le.setText("Discard this draft")
        except Exception as error:  # noqa: BLE001 - propagate Qt callback failures after the modal loop.
            callback_errors.append(error)
        finally:
            dialog.reject()

    QtCore.QTimer.singleShot(0, edit)
    view.edit_plot(artifact, view._svg_plot_items[0])
    assert not callback_errors, callback_errors
    assert (
        view.plot_service.load_params(artifact.params_path)["fp_xlabel"]
        == "Edited effect axis"
    )
    assert QSvgRenderer(str(path)).isValid()
    record_step(
        "plot-applied-cancelled",
        view,
        axis="Edited effect axis",
        plots={title: str(path)},
    )
    view.close()


def small_study_effects(app, window):
    from rc_metastudio.publication_bias_dialog import PublicationBiasDialog

    assert window.open(str(ROOT / "sample_projects/amino.rcms"), raise_on_error=True)
    callback_errors = []

    def run():
        dialog = app.activeModalWidget()
        if not isinstance(dialog, PublicationBiasDialog):
            QtCore.QTimer.singleShot(10, run)
            return
        try:
            button = dialog.button_box.button(
                QtWidgets.QDialogButtonBox.StandardButton.Ok
            )
            assert button.isEnabled()
            if not dialog.ordinary_funnel_check.isChecked():
                dialog.ordinary_funnel_check.setChecked(True)
            record_step("small-study-configured", dialog, ordinary_funnel=True)
            mouse_click(required(button), QtCore.Qt.MouseButton.LeftButton)
            assert not dialog.failure_label.isVisible(), dialog.failure_label.text()
        except Exception as error:  # noqa: BLE001 - propagate Qt callback failures after the modal loop.
            callback_errors.append(error)
        finally:
            dialog.reject()

    QtCore.QTimer.singleShot(0, run)
    window.action_publication_bias.trigger()
    assert not callback_errors, callback_errors
    view = next(
        w
        for w in app.topLevelWidgets()
        if isinstance(w, results_window.ResultsWindow) and w.isVisible()
    )
    assert view.results.images, dict(view.texts)
    assert any("Harbord" in text or "Rücker" in text for text in view.texts.values())
    for path in view.results.images.values():
        if Path(path).suffix == ".svg":
            assert QSvgRenderer(str(path)).isValid()
        else:
            assert not QtGui.QImage(str(path)).isNull()
    record_step(
        "small-study-results",
        view,
        texts=dict(view.texts),
        plots=dict(view.results.images),
    )
    view.close()


def calculator(app, window, family):
    from rc_metastudio import (
        binary_data_dialog,
        continuous_data_dialog,
        diagnostic_data_dialog,
    )

    sample, dialog_type, table_name, column = {
        "binary": ("amino", binary_data_dialog.BinaryDataDialog, "raw_data_table", 0),
        "continuous": (
            "continuous",
            continuous_data_dialog.ContinuousDataDialog,
            "simple_table",
            1,
        ),
        "diagnostic": (
            "lymph",
            diagnostic_data_dialog.DiagnosticDataDialog,
            "two_by_two_table",
            0,
        ),
    }[family]
    assert window.open(
        str(ROOT / f"sample_projects/{sample}.rcms"), raise_on_error=True
    )

    def raw():
        model = window.model
        return list(
            model.get_current_analysis_unit_for_study(0).get_raw_data_for_group(
                model.current_groups[0]
            )
        )

    before = raw()
    record_step("calculator-before", window, family=family, raw=before)
    expected = before.copy()
    expected[column] += 1.5 if family == "continuous" else 1
    if family == "binary":
        expected[1] += 1
    callback_errors = []

    def edit(accept):
        dialog = app.activeModalWidget()
        if not isinstance(dialog, dialog_type):
            QtCore.QTimer.singleShot(10, lambda: edit(accept))
            return
        try:
            table = getattr(dialog, table_name)
            for field in (dialog.effect_text_box, dialog.lower_text_box, dialog.upper_text_box):
                width = field.fontMetrics().horizontalAdvance(field.text())
                assert field.width() >= width + field.textMargins().left() + field.textMargins().right() + 12
            table.setCurrentCell(0, column)
            table.item(0, column).setText(
                str(expected[column] if accept else expected[column] + 1).replace(
                    ".", ","
                )
            )
            if accept:
                dialog.effect_text_box.setFocus()
                app.processEvents()
                record_step("calculator-effect-preview", dialog, family=family,
                            previews=[field.text() for field in
                                      (dialog.effect_text_box, dialog.lower_text_box, dialog.upper_text_box)])
                dialog.lower_text_box.setFocus()
                app.processEvents()
                record_step("calculator-ci-preview", dialog, family=family,
                            lower=dialog.lower_text_box.text(), upper=dialog.upper_text_box.text())
            button = dialog.buttonBox.button(
                QtWidgets.QDialogButtonBox.StandardButton.Ok
                if accept
                else QtWidgets.QDialogButtonBox.StandardButton.Cancel
            )
            assert button.isEnabled()
            record_step(
                "calculator-accept" if accept else "calculator-cancel",
                dialog,
                family=family,
            )
            mouse_click(required(button), QtCore.Qt.MouseButton.LeftButton)
        except Exception as error:  # noqa: BLE001 - propagate Qt callback failures after the modal loop.
            callback_errors.append(error)
            dialog.reject()

    QtCore.QTimer.singleShot(0, lambda: edit(True))
    header = window.tableView.verticalHeader()
    first_row = QtCore.QPoint(
        header.viewport().width() // 2,
        header.sectionViewportPosition(0) + header.sectionSize(0) // 2,
    )
    mouse_click(header.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=first_row)
    assert not callback_errors, callback_errors
    assert raw() == expected, (raw(), expected)
    assert window.workspace.is_dirty
    QtCore.QTimer.singleShot(0, lambda: edit(False))
    mouse_click(header.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=first_row)
    assert not callback_errors, callback_errors
    assert raw() == expected
    window.action_undo.trigger()
    assert raw() == before
    assert not window.workspace.is_dirty
    window.action_redo.trigger()
    assert raw() == expected
    window.out_path = str(WORK / "calculator.rcms")
    assert window.save()
    assert window.open(window.out_path, raise_on_error=True)
    assert raw() == expected
    method = {
        "binary": "binary.random",
        "continuous": "continuous.random",
        "diagnostic": "diagnostic.random",
    }[family]
    record_step(
        "calculator-reopened", window, family=family, raw=raw(), project=window.out_path
    )
    analyze(app, window, method).close()


base_path_patch = patch(
    "rc_metastudio.settings.get_base_path", return_value=WORK.as_posix()
)
base_path_patch.start()
try:
    app, window = automation.start_automation()
except BaseException:
    base_path_patch.stop()
    sys.excepthook = sys.__excepthook__
    raise
sys.excepthook = sys.__excepthook__
errors = []


def dismiss_unexpected_messages():
    for widget in app.topLevelWidgets():
        if isinstance(widget, QtWidgets.QMessageBox) and widget.isVisible() and not widget.property("verificationExpectedMessage"):
            errors.append(widget.text())
            widget.setProperty("verificationExpectedMessage", True)
            record_step("unexpected-dialog", widget, message=widget.text())
            print("UNEXPECTED DIALOG:", widget.text(), file=sys.stderr, flush=True)
            widget.reject()


watchdog = QtCore.QTimer()
watchdog.timeout.connect(dismiss_unexpected_messages)
watchdog.start(100)
try:
    scenario = sys.argv[1]
    if EVIDENCE is not None or scenario == "doctor":
        doctor(app, window)
    if scenario == "doctor":
        pass
    elif scenario.startswith("audit-round3-"):
        sys.path.insert(0, str(ROOT / ".agents/skills/verify-rcms/scripts"))
        from tests.e2e.audit_round3 import run

        run(app, window, WORK, record_step, scenario)
    elif scenario == "review1-design":
        sys.path.insert(0, str(ROOT / ".agents/skills/verify-rcms/scripts"))
        from tests.e2e.review1_design import run

        run(app, window, WORK, ROOT, record_step, analyze)
    elif scenario == "review-workflows":
        from tests.e2e.review_workflows import run

        run(app, window, ROOT, record_step, analyze)
    elif scenario == "ux-improvements":
        from tests.e2e.ux_workflows import run

        run(app, window, WORK, ROOT, record_step, analyze)
    elif scenario in ("amino", "continuous", "lymph"):
        sample_analysis(app, window, scenario)
    elif scenario == "editing":
        editing(app, window)
    elif scenario == "plot-edit":
        plot_edit(app, window)
    elif scenario == "small-study-effects":
        small_study_effects(app, window)
    elif scenario.startswith(
        (
            "options-",
            "plot-workflow-",
            "calculator-mode-",
            "project-",
            "analysis-sequential-",
        )
    ):
        sys.path.insert(0, str(ROOT / ".agents/skills/verify-rcms/scripts"))
        from advanced_workflows import run

        run(app, window, scenario, record_step)
    elif scenario.startswith("calculator-"):
        calculator(app, window, scenario.removeprefix("calculator-"))
    elif scenario == "csv":
        csv_import(app, window)
    elif scenario.startswith("ratios-"):
        sys.path.insert(0, str(ROOT / ".agents/skills/verify-rcms/scripts"))
        from ratio_workflows import run

        run(app, window, scenario, record_step)
    elif scenario.startswith(("analysis-", "small-study-")):
        sys.path.insert(0, str(ROOT / ".agents/skills/verify-rcms/scripts"))
        from analysis_matrix import run

        run(app, window, scenario, record_step)
    else:
        raise ValueError(f"Unknown desktop scenario: {scenario}")
    assert not errors, errors
    record_step("workflow-passed", window, scenario=scenario)
except BaseException:
    traceback.print_exc()
    raise
finally:
    window.workspace.mark_saved()
    watchdog.stop()
    for widget in app.topLevelWidgets():
        widget.close()
    automation.dispose_qobjects(app, app.topLevelWidgets())
    app.quit()
    base_path_patch.stop()
print("WORKFLOW PASSED")
