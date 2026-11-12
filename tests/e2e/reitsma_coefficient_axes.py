"""Reitsma coefficient-axis settings, persistence and exported intervals."""

import json
from pathlib import Path
from PyQt6 import QtCore, QtWidgets


def run_coefficients(app, window, work, record):
    from analysis_matrix import run as matrix
    from advanced_workflows import modal, click, export_formats
    from rc_metastudio import r_bridge
    from rc_metastudio.plot_editor_dialog import EditPlotDialog
    from tests.e2e.axis_conventions import check_axis
    def prepare(target):
        for row in range(6):
            assert target.model.setData(target.model.index(row, target.model.RAW_DATA[2]), '1')
        raw = [list(row) for row in target.model.get_current_raw_data()]
        assert raw == [[19+i,10+i,1,81+i] for i in range(6)], raw
        target.model.add_covariate('Dose','continuous',
            {study.label:float(i+1) for i,study in enumerate(target.model.get_studies(only_if_included=True))})
        target.model.reset_model()
        target.enable_menu_options_that_require_dataset()
        target.out_path = str(work / 'reitsma-six-dose.rcms')
        assert target.save() and target.open(target.out_path,raise_on_error=True)
        assert [list(row) for row in target.model.get_current_raw_data()] == raw
        record('release-reitsma-exact-input', target, raw=raw, dose=list(range(1,7)))
    view = matrix(app, window, 'analysis-data-diagnostic', record,
                  keep_results=True, workflow_override='meta-regression', prepare=prepare,
                  parameters={'digits':6})
    report = dict(view.texts)
    def record_bottom(action, **observations):
        _, item = view._selected_plot()
        bottom = item.sceneBoundingRect().bottom() * view.graphics_view.transform().m22()
        view.graphics_view.verticalScrollBar().setValue(round(bottom - view.graphics_view.viewport().height() + 30))
        app.processEvents()
        record(action, view, **observations)
    exercised = []
    for title in view.results.images:
        if title not in ('diagnostic.reitsma.sensitivity.coefficients', 'diagnostic.reitsma.specificity.coefficients'):
            continue
        exercised.append(title)
        section = next(s for s in view.results.sections if s.source_key == title)
        item = view.nav_tree.findItems(section.title, QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)[0]
        view.nav_tree.setCurrentItem(item)
        view.report_action.setChecked(False)
        view._show_report(False)
        app.processEvents()
        artifact, _ = view._selected_plot()
        r_bridge.load_vars_for_plot(artifact.params_path, return_params_dict=True)
        expression = 'jsonlite::toJSON(plot.data[c("estimate","ci.lb","ci.ub")],digits=16)'
        before = str(r_bridge.execute_r_string(expression)[0])
        observed = check_axis(artifact.display_path(), 'transformed', ratio=True)
        record('coefficient-log-default', view, title=title, ticks=observed, coefficients=json.loads(before), plots={title:artifact.display_path()})
        record_bottom('coefficient-log-default-bottom', title=title, ticks=observed, plots={title:artifact.display_path()})
        def edit(dialog):
            assert dialog.axis_scale.isVisible(), 'coefficient scale chooser hidden'
            assert dialog.axis_scale.currentData() == 'transformed', dialog.axis_scale.currentData()
            dialog.axis_scale.setCurrentIndex(dialog.axis_scale.findData('natural'))
            record('coefficient-linear-choice', dialog, title=title)
            click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
        modal(app, EditPlotDialog, edit, view.edit_plot_action.trigger)
        r_bridge.load_vars_for_plot(artifact.params_path, return_params_dict=True)
        assert str(r_bridge.execute_r_string(expression)[0]) == before
        assert dict(view.texts) == report
        linear = check_axis(artifact.display_path(), 'natural', ratio=True)
        def reopen(dialog):
            assert dialog.axis_scale.currentData() == 'natural'
            dialog.axis_scale.setCurrentIndex(dialog.axis_scale.findData('transformed'))
            click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel))
        current = Path(artifact.display_path()).read_bytes()
        modal(app, EditPlotDialog, reopen, view.edit_plot_action.trigger)
        assert Path(artifact.display_path()).read_bytes() == current
        record('coefficient-linear-reopened', view, title=title, ticks=linear, plots={title:artifact.display_path()})
        record_bottom('coefficient-linear-reopened-bottom', title=title, ticks=linear, plots={title:artifact.display_path()})
        export_formats(app, view, work / title.replace(' ', '-'), 'coefficient-linear', record)
    assert len(exercised) == 2, ('coefficient plots not exercised', exercised)
    view.close()
