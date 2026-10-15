"""Final release paths that the broad matrix did not previously prove."""
import json
from pathlib import Path
from PyQt6 import QtCore, QtWidgets


def run_coefficients(app, window, work, record):
    from analysis_matrix import run as matrix
    from advanced_workflows import modal, click, export_formats
    from rc_metastudio import r_bridge
    from rc_metastudio.plot_editor_dialog import EditPlotDialog
    from tests.e2e.axis_conventions import check_axis
    view = matrix(app, window, 'analysis-diagnostic-regression-continuous', record,
                  keep_results=True, parameters={'digits':6})
    report = dict(view.texts)
    for title in view.results.images:
        if 'Moderator Coefficients' not in title:
            continue
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
        def edit(dialog):
            assert dialog.axis_scale.isVisible() and dialog.axis_scale.currentData() == 'transformed'
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
        export_formats(app, view, work / title.replace(' ', '-'), 'coefficient-linear', record)
    view.close()
