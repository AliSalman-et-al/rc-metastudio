"""Drive result properties and presentation-only ordering with real Qt and R."""

from PyQt6 import QtCore, QtWidgets
from collections.abc import Iterable
from typing import cast
from xml.etree import ElementTree as ET
from tests.python.gui.test_types import mouse_click, required


def run(app, window, root, record, analyze):
    from rc_metastudio import analysis_setup_dialog, r_bridge, results_window
    from tests.analysis_regression.golden.support.golden_analysis import parsed_numeric_sections

    def setup():
        return next(w for w in app.topLevelWidgets()
                    if isinstance(w, analysis_setup_dialog.AnalysisSetupDialog) and w.isVisible())

    def submit(dialog):
        before = {id(w) for w in app.topLevelWidgets() if isinstance(w, results_window.ResultsWindow)}
        mouse_click(required(dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)),
                    QtCore.Qt.MouseButton.LeftButton)
        app.processEvents()
        return next(w for w in app.topLevelWidgets()
                    if isinstance(w, results_window.ResultsWindow) and w.isVisible() and id(w) not in before)

    assert window.open(str(root / "sample_projects/amino.rcms"), raise_on_error=True)
    view = analyze(app, window, "binary.random")
    assert view.identity_label.text() == view.results.identity
    assert len(view.identity_label.text().splitlines()) == 2
    report = view.report_text.toPlainText()
    assert report.index("Pooled ") < report.index("Model configuration\n")
    assert view.results.identity not in report
    assert view.change_settings_action.isEnabled()
    view.change_settings_action.trigger()
    app.processEvents()
    dialog = setup()
    assert dialog.current_method == "binary.random"
    assert dialog.current_param_vals["digits"] == 3
    assert dialog.style_cbo.currentText() == "RevMan"
    assert dialog.study_order.currentData() == "table"
    record("review-properties-prefilled", dialog, parameters=dialog.current_param_vals)
    dialog.reject()
    app.processEvents()
    baseline = parsed_numeric_sections(view.results)
    params_path = next(iter(view.params_paths.values()))
    r_bridge.load_vars_for_plot(params_path)
    r_bridge.load_in_r(str(params_path) + ".plotdata")
    original_labels = list(cast(Iterable[str], r_bridge.ro.r("plot.data$slab[plot.data$display_order]")))
    view.report_action.setChecked(True)
    report = view.report_text.toPlainText()
    assert "Q(df=" not in report and "Het. p-value" not in report
    assert "95% CI" in report and "[0.485, 1.222]" in report
    assert report.index("Model Results") < report.index("Heterogeneity") < report.index("Test for overall effect") < report.index("Prediction interval")
    record("review-report-top", view, text=report)

    # A result belongs to its original input even after the main window opens another project.
    assert window.open(str(root / "sample_projects/continuous.rcms"), raise_on_error=True)
    for order in ("year", "effect", "weight", "table"):
        view.change_settings_action.trigger()
        app.processEvents()
        dialog = setup()
        assert dialog.data_type == "binary" and dialog.model.current_outcome_name == "clinical failure"
        dialog.specs_tab.setCurrentWidget(dialog.plot_tab)
        dialog.study_order.setCurrentIndex(dialog.study_order.findData(order))
        dialog.content_scroll_area.ensureWidgetVisible(dialog.study_order)
        app.processEvents()
        record("review-study-order-" + order, dialog, order=order)
        if order == "year":
            dialog.study_order.showPopup()
            app.processEvents()
            record("review-study-order-options", dialog, dialog.study_order.view().window())
            dialog.study_order.hidePopup()
        changed = submit(dialog)
        assert parsed_numeric_sections(changed.results) == baseline
        r_bridge.load_vars_for_plot(next(iter(changed.params_paths.values())))
        r_bridge.load_in_r(str(next(iter(changed.params_paths.values()))) + ".plotdata")
        labels = list(cast(Iterable[str], r_bridge.ro.r("plot.data$slab[plot.data$display_order]")))
        assert sorted(labels) == sorted(original_labels)
        if order == "table":
            assert labels == original_labels
        else:
            assert labels != original_labels
        assert list(cast(Iterable[str], r_bridge.ro.r("plot.data$ilab$columns[[length(plot.data$ilab$columns)]]$key"))) == ["weight"]
        record("review-ordered-result-" + order, changed, labels=labels, numbers=baseline,
               plots=dict(changed.results.display_images))
        svg = ET.parse(next(iter(changed.results.display_images.values())))
        captions = ["".join(node.itertext()) for node in svg.iter("{http://www.w3.org/2000/svg}text")]
        assert "Odds ratio (log scale)" in captions, captions
        changed.close()
        app.processEvents()
    view.change_settings_action.trigger()
    app.processEvents()
    dialog = setup()
    label = next(w for w in dialog.findChildren(QtWidgets.QLabel) if w.buddy() is not None and isinstance(w.buddy(), QtWidgets.QComboBox) and w.buddy().findData("REML") >= 0)
    label.buddy().setCurrentIndex(label.buddy().findData("REML"))
    assert dialog.current_param_vals["rm.method"] == "REML"
    changed = submit(dialog)
    assert "REML" in changed.report_text.toPlainText() or "Restricted" in changed.report_text.toPlainText()
    record("review-settings-rerun", changed, plots=dict(changed.results.display_images), text=changed.report_text.toPlainText())
    changed.close()
    view.close()

    window.cum_ma()
    app.processEvents()
    dialog = setup()
    assert not dialog.study_order.isEnabled()
    assert "current study order" in dialog.context_label.text()
    record("review-cumulative-order", dialog, explanation=dialog.context_label.text())
    dialog.reject()
