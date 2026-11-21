"""Drive result properties and presentation-only ordering with real Qt and R."""

import hashlib
from pathlib import Path

from PyQt6 import QtCore, QtWidgets, sip
from collections.abc import Iterable
from typing import cast
from xml.etree import ElementTree as ET
from tests.python.gui.qt_test_support import key_clicks, mouse_click, required
from tests.e2e.plot_observations import load_saved_analysis, load_serialized_object


def run(app, window, root, record, analyze):
    from advanced_workflows import modal, click
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog
    from rc_metastudio import r_bridge
    from rc_metastudio.results import window as results_window
    from rc_metastudio.results.plot_editor import EditPlotDialog
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

    def plot_hashes(result_view):
        paths = [*result_view.results.images.values(), *result_view.results.display_images.values()]
        assert len(paths) == 2, paths
        return {str(path): hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths}

    assert window.open(str(root / "sample_projects/amino.rcms"), raise_on_error=True)
    view = analyze(app, window, "binary.random")
    first_plot = plot_hashes(view)
    first_numbers = parsed_numeric_sections(view.results)
    assert window.open(str(root / "sample_projects/continuous.rcms"), raise_on_error=True)
    window.action_go.trigger()
    app.processEvents()
    fresh_dialog = setup()
    fresh_dialog.specs_tab.setCurrentWidget(fresh_dialog.plot_tab)
    fresh_dialog.x_lbl_le.selectAll()
    key_clicks(fresh_dialog.x_lbl_le, "Second analysis axis")
    fresh_view = submit(fresh_dialog)
    fresh_plot = plot_hashes(fresh_view)
    record("review-fresh-fit-plots", fresh_view, original=first_plot, fresh=fresh_plot,
           original_after=plot_hashes(view))
    assert not first_plot.keys() & fresh_plot.keys(), (first_plot, fresh_plot)
    assert plot_hashes(view) == first_plot
    assert parsed_numeric_sections(view.results) == first_numbers
    fresh_svg = next(iter(fresh_view.results.display_images.values()))
    assert "Second analysis axis" in {
        "".join(node.itertext()) for node in ET.parse(fresh_svg).iter("{http://www.w3.org/2000/svg}text")
    }
    fresh_view.close()
    assert window.open(str(root / "sample_projects/amino.rcms"), raise_on_error=True)
    assert view.result_identity.isVisible()
    assert view.windowTitle().startswith("Meta-analysis — clinical failure · Binary · Odds ratio")
    assert "Random-effects" in view.windowTitle() and "95% CI" in view.windowTitle()
    report = view.manuscript_text.toPlainText()
    from tests.e2e.report_retention import assert_report
    assert_report(view)
    assert report.index("Pooled effect") < report.index("Model fit") < report.index("Study results") < report.index("Model configuration\n")
    assert view.results.identity not in report
    assert view.change_settings_action.isEnabled()
    view.change_settings_action.trigger()
    app.processEvents()
    dialog = setup()
    assert dialog.current_method == "binary.random"
    assert dialog.current_param_vals["digits"] == 3
    assert dialog.style_cbo.currentText() == "Default"
    assert dialog.study_order.currentData() == "table"
    record("review-properties-prefilled", dialog, parameters=dialog.current_param_vals)
    dialog.specs_tab.setCurrentWidget(dialog.plot_tab)
    dialog.x_lbl_le.selectAll()
    key_clicks(dialog.x_lbl_le, "[default]")
    literal_view = submit(dialog)
    assert not first_plot.keys() & plot_hashes(literal_view).keys()
    assert sip.isdeleted(view) or not view.isVisible()
    assert {str(path): hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in first_plot} == first_plot
    literal_svg = next(iter(literal_view.results.display_images.values()))
    captions = {"".join(node.itertext()): node for node in ET.parse(literal_svg).iter("{http://www.w3.org/2000/svg}text")}
    assert "[default]" in captions, captions.keys()
    literal_view.change_settings_action.trigger()
    app.processEvents()
    dialog = setup()
    assert dialog.x_lbl_le.text() == "[default]", "Change Settings lost the literal axis label"
    record("review-literal-axis-label", dialog, caption=dialog.x_lbl_le.text(),
           svg_caption=ET.tostring(captions["[default]"], encoding="unicode"))
    dialog.reject()
    assert literal_view.isVisible()
    view = literal_view
    baseline = parsed_numeric_sections(view.results)
    params_path = next(iter(view.params_paths.values()))
    load_saved_analysis(params_path)
    load_serialized_object(str(params_path) + ".plotdata")
    original_labels = list(cast(Iterable[str], r_bridge.ro.r("plot.data$slab[plot.data$display_order]")))
    import json
    inputs = json.loads(str(r_bridge.execute_r_string('jsonlite::toJSON(list(year=plot.data$years, effect=as.numeric(plot.data$res$yi), weight=as.numeric(plot.data$weights)), na="null", digits=16)')[0]))
    expected_orders = {'table': list(range(len(original_labels)))}
    for key, values in inputs.items():
        assert len(values) == len(original_labels), (key, values)
        # Python's stable sort retains fixture/table order for ties; missing years go last.
        indexes = sorted(range(len(values)), key=lambda i: (values[i] is None or (key == 'year' and values[i] == 0),
                         0 if values[i] is None else -values[i] if key == 'weight' else values[i]))
        expected_orders[key] = indexes
    view.report_action.setChecked(True)
    report = view.manuscript_text.toPlainText()
    assert "Q(df=" not in report and "Het. p-value" not in report
    assert_report(view)
    assert report.index("Pooled effect") < report.index("Model fit") < report.index("Study results")
    record("review-report-top", view, text=report)

    # A result belongs to its original input even after the main window opens another project.
    assert window.open(str(root / "sample_projects/continuous.rcms"), raise_on_error=True)
    for style, order in (("Default", "year"), ("RevMan", "year"), ("RevMan", "effect"), ("RevMan", "weight"), ("RevMan", "table")):
        view.change_settings_action.trigger()
        app.processEvents()
        dialog = setup()
        assert dialog.data_type == "binary" and dialog.model.current_outcome_name == "clinical failure"
        dialog.specs_tab.setCurrentWidget(dialog.plot_tab)
        dialog.style_cbo.setCurrentText(style)
        dialog.study_order.setCurrentIndex(dialog.study_order.findData(order))
        dialog.content_scroll_area.ensureWidgetVisible(dialog.study_order)
        app.processEvents()
        record("review-study-order-" + style.lower() + '-' + order, dialog, order=order, style=style)
        if order == "year":
            dialog.study_order.showPopup()
            app.processEvents()
            record("review-study-order-options", dialog, dialog.study_order.view().window())
            dialog.study_order.hidePopup()
        changed = submit(dialog)
        assert parsed_numeric_sections(changed.results) == baseline
        load_saved_analysis(next(iter(changed.params_paths.values())))
        load_serialized_object(str(next(iter(changed.params_paths.values()))) + ".plotdata")
        labels = list(cast(Iterable[str], r_bridge.ro.r("plot.data$slab[plot.data$display_order]")))
        display_order = [int(index) - 1 for index in r_bridge.ro.r("plot.data$display_order")]
        assert display_order == expected_orders[order], ('study order', order, display_order, expected_orders[order])
        last_column = list(cast(Iterable[str], r_bridge.ro.r("plot.data$ilab$columns[[length(plot.data$ilab$columns)]]$key")))
        assert last_column == ["weight"], (style, last_column)
        record("review-ordered-result-" + order, changed, labels=labels, numbers=baseline,
               plots=dict(changed.results.display_images))
        svg = ET.parse(next(iter(changed.results.display_images.values())))
        nodes = list(svg.iter("{http://www.w3.org/2000/svg}text"))
        captions = ["".join(node.itertext()) for node in nodes]
        tick_baseline = max(float(node.attrib["y"]) for node in nodes
                            if "".join(node.itertext()) in {"0.01", "0.1", "1", "10", "100"})
        axis_titles = ["".join(node.itertext()) for node in nodes
                       if float(node.attrib["y"]) > tick_baseline and "".join(node.itertext()) == "Odds ratio"]
        assert len(axis_titles) == 1 and "Odds ratio (log scale)" not in captions, captions
        assert sip.isdeleted(view) or not view.isVisible()
        view = changed
        app.processEvents()
    view.change_settings_action.trigger()
    app.processEvents()
    dialog = setup()
    label = next(w for w in dialog.findChildren(QtWidgets.QLabel) if w.buddy() is not None and isinstance(w.buddy(), QtWidgets.QComboBox) and w.buddy().findData("REML") >= 0)
    label.buddy().setCurrentIndex(label.buddy().findData("REML"))
    assert dialog.current_param_vals["rm.method"] == "REML"
    changed = submit(dialog)
    assert "REML" in changed.manuscript_text.toPlainText() or "Restricted" in changed.manuscript_text.toPlainText()
    record("review-settings-rerun", changed, plots=dict(changed.results.display_images), text=changed.manuscript_text.toPlainText())
    project_path = window.workspace.path
    old_labels = window.model.current_sheet.settings.get("favours_labels")

    def edit_replaced_project_plot(editor):
        editor.favours_left.setText("Earlier project left")
        editor.favours_right.setText("Earlier project right")
        click(app, editor.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))

    changed.report_action.setChecked(False)
    app.processEvents()
    modal(app, EditPlotDialog, edit_replaced_project_plot, changed.edit_plot_action.trigger)
    edited_svg = next(iter(changed.results.display_images.values()))
    edited_caption = " ".join(ET.parse(edited_svg).getroot().itertext())
    assert "Earlier project left" in edited_caption
    assert "Earlier project right" in edited_caption
    assert window.workspace.path == project_path
    assert window.model.current_sheet.settings.get("favours_labels") == old_labels
    assert not window.workspace.is_dirty
    record("review-replaced-project-edit-stays-local", changed, project=str(project_path),
           favours_labels=old_labels, plots={"Edited forest plot": edited_svg})
    changed.close()

    assert window.open(str(root / "sample_projects/amino.rcms"), raise_on_error=True)
    view = analyze(app, window, "binary.random")
    for confidence in (90, 99):
        view.change_settings_action.trigger()
        app.processEvents()
        dialog = setup()
        for key, value in (("conf.level", confidence), ("inference.method", "knha")):
            label = next(w for w in dialog.findChildren(QtWidgets.QLabel)
                         if w.buddy() is not None and w.text().rstrip(":").casefold() ==
                         ("confidence level" if key == "conf.level" else "inference method"))
            control = label.buddy()
            if key == "conf.level":
                control.setValue(value)
            else:
                control.setCurrentIndex(control.findData(value))
        assert dialog.current_param_vals["conf.level"] == confidence
        assert dialog.current_param_vals["inference.method"] == "knha"
        changed = submit(dialog)
        assert f"Confidence intervals ({confidence:g}%)" in changed.manuscript.methods
        path = next(iter(changed.params_paths.values()))
        load_saved_analysis(path)
        df = int(r_bridge.ro.r("res$dfs")[0])
        assert df == len(window.model.get_studies()) - 1
        assert f"{df} degrees of freedom" in changed.manuscript.methods
        assert f"df = {df}" in changed.manuscript.results
        assert any("df" in table.headers and table.rows[0][table.headers.index("df")] == str(df)
                   for section in changed.results.sections for table in section.tables
                   if table.rows)
        svg_text = Path(next(iter(changed.results.display_images.values()))).read_text()
        assert f"t (df = {df})" in svg_text
        record(f"review-confidence-{confidence}-kh", changed,
               methods=changed.manuscript.methods, df=df,
               plots=dict(changed.results.display_images))
        view.close()
        view = changed
    view.close()

    window.action_cum_ma.trigger()
    app.processEvents()
    dialog = setup()
    assert dialog.study_order.isEnabled()
    assert [dialog.study_order.itemData(i) for i in range(dialog.study_order.count())] == ['table', 'year', 'effect']
    assert dialog.study_order_label.text() == 'Add studies in'
    assert dialog.show_i2.isChecked()
    # The amino effect-ordered REML prefixes can fail to converge in metafor.
    # Use an explicit FE fit to prove successful sequence/rerun preservation;
    # the independent prefix oracle separately exercises REML sequences.
    dialog.method_cbo_box.setCurrentIndex(dialog.method_cbo_box.findData('binary.fixed.inv.var'))
    app.processEvents()
    record("review-cumulative-order", dialog, explanation=dialog.study_order.toolTip())
    dialog.study_order.setCurrentIndex(dialog.study_order.findData('year'))
    view = submit(dialog)
    assert_report(view)
    assert view.manuscript.results.count('the pooled odds ratio was') == 1
    assert 'publication-year order' in view.manuscript.methods
    assert ('studies without a year' in view.manuscript.methods) == any(not study.year for study in window.model.get_studies())
    sequential = [t for s in view.manuscript.sections for t in s.tables if t.title == 'Cumulative results']
    assert len(sequential) == 1 and len(sequential[0].rows) == len(window.model.get_studies())
    assert {'Step', 'Study added', 'k', 'I²'} <= set(sequential[0].headers)
    record('review-cumulative-forest', view, plots=dict(view.results.display_images))
    view.report_action.setChecked(True)
    record('review-cumulative-summary', view, text=view.manuscript.results, plots=dict(view.results.display_images))
    original_plot = Path(next(iter(view.results.display_images.values())))
    original_bytes = original_plot.read_bytes()
    original_last = sequential[0].rows[-1]
    def change_sequence(editor):
        assert not editor.study_order.isEnabled() and editor.study_order.currentData() == 'year'
        editor.style_cbo.setCurrentText('BMJ')
        editor.show_i2.setChecked(False)
        record('review-sequence-rerun-draft', editor)
        click(app, editor.sequence_rerun)
    view.report_action.trigger()
    modal(app, EditPlotDialog, change_sequence, view.edit_plot_action.trigger)
    dialog = setup()
    assert dialog.style_cbo.currentText() == 'BMJ' and not dialog.show_i2.isChecked()
    assert dialog.study_order.currentData() == 'year'
    dialog.reject()
    assert original_plot.read_bytes() == original_bytes
    modal(app, EditPlotDialog, change_sequence, view.edit_plot_action.trigger)
    dialog = setup()
    dialog.study_order.setCurrentIndex(dialog.study_order.findData('effect'))
    changed = submit(dialog)
    assert_report(changed)
    changed_table = next(t for s in changed.manuscript.sections for t in s.tables if t.title == 'Cumulative results')
    assert changed_table.rows[0] != sequential[0].rows[0]
    for header in ('Estimate', '95% CI', 'I²'):
        index = changed_table.headers.index(header)
        assert changed_table.rows[-1][index] == original_last[index]
    assert original_plot.read_bytes() == original_bytes
    record('review-effect-sequence-rerun', changed, plots=dict(changed.results.display_images))
    changed_bytes = Path(next(iter(changed.results.display_images.values()))).read_bytes()
    existing = {id(w) for w in app.topLevelWidgets() if isinstance(w, results_window.ResultsWindow)}
    changed.change_settings_action.trigger()
    app.processEvents()
    failed = setup()
    failed.method_cbo_box.setCurrentIndex(failed.method_cbo_box.findData('binary.random'))
    app.processEvents()
    from analysis_matrix import set_parameter
    set_parameter(app, failed, 'rm.method', 'REML')
    mouse_click(required(failed.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)), QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()
    assert failed.isVisible() and failed.analysis_error_panel.isVisible()
    assert 'did not converge' in failed.analysis_error_details.toPlainText()
    assert {id(w) for w in app.topLevelWidgets() if isinstance(w, results_window.ResultsWindow)} == existing
    assert Path(next(iter(changed.results.display_images.values()))).read_bytes() == changed_bytes
    record('review-package-convergence-error', failed, details=failed.analysis_error_details.toPlainText())
    failed.reject()
    changed.close()
    view.close()

    window.action_loo_ma.trigger()
    app.processEvents()
    dialog = setup()
    assert [dialog.study_order.itemData(i) for i in range(dialog.study_order.count())] == ['table', 'year', 'effect', 'i2']
    assert dialog.study_order_label.text() == 'Row order'
    dialog.study_order.setCurrentIndex(dialog.study_order.findData('i2'))
    view = submit(dialog)
    assert_report(view)
    assert view.manuscript.results.count('The pooled odds ratio was') <= 1
    assert 'omission fits' in view.manuscript.results
    sequential = [t for s in view.manuscript.sections for t in s.tables if t.title == 'Leave-one-out results']
    assert len(sequential) == 1 and len(sequential[0].rows) == len(window.model.get_studies()) + 1
    assert {'Study omitted', 'k', 'I²'} <= set(sequential[0].headers)
    assert not any(t.title == 'Study weights' for s in view.results.sections for t in s.tables)
    record('review-leave-one-out-forest', view, plots=dict(view.results.display_images))
    view.report_action.setChecked(True)
    record('review-leave-one-out-summary', view, text=view.manuscript.results, plots=dict(view.results.display_images))
    path = next(iter(view.params_paths.values()))
    def saved_plot():
        load_serialized_object(str(path) + '.plotdata')
        return json.loads(str(r_bridge.execute_r_string('jsonlite::toJSON(list(order=plot.data$display_order, i2=vapply(plot.data$res,function(f)f$I2,numeric(1)), effect=plot.data$effect$yi, headers=plot.data$ilab$headers),digits=16)')[0]))
    before = saved_plot()
    assert before['order'] == [1, *[i + 2 for i in sorted(range(len(before['i2']) - 1), key=lambda i: (before['i2'][i + 1], i))]]
    view.report_action.trigger()
    def edit_omissions(editor):
        assert editor.study_order.currentData() == 'i2'
        editor.study_order.setCurrentIndex(editor.study_order.findData('effect'))
        editor.show_i2.setChecked(False)
        click(app, editor.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Apply))
        assert editor._commit_error.isHidden(), editor._commit_error.text()
        record('review-omission-display-only-edit', editor)
        editor.reject()
    modal(app, EditPlotDialog, edit_omissions, view.edit_plot_action.trigger)
    after = saved_plot()
    assert after['headers'] == ['k']
    assert after['effect'] == before['effect'] and after['i2'] == before['i2']
    assert after['order'] == [1, *[i + 2 for i in sorted(range(len(after['effect']) - 1), key=lambda i: (after['effect'][i + 1], i))]]
    record('review-omission-effect-sorted', view, plots=dict(view.results.display_images), fit_values=after)
    view.close()
