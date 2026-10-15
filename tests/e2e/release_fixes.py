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


def run_presentation(app, window, work, record):
    from analysis_matrix import run as matrix, set_parameter
    from advanced_workflows import modal, click
    from rc_metastudio import analysis_dataset, analysis_setup_dialog, results_window
    from rc_metastudio.about_legal_dialog import AboutLegalDialog
    from tests.e2e.audit_round3 import check_report
    from tests.e2e.reviewer_fixes import labels, check_table_surface
    def about(dialog):
        app.processEvents()
        assert dialog.content_scroll_area.verticalScrollBar().maximum() == 0
        record('release-about-content-visible', dialog, size=[dialog.width(),dialog.height()], text=dialog.content_scroll_area.toPlainText())
        dialog.reject()
    modal(app, AboutLegalDialog, about, window.action_about_legal.trigger)
    for name in ('Group', 'Participants'):
        for workflow in ('standard','subgroup'):
            window.workspace.mark_saved()
            def prepare(target):
                if workflow == 'subgroup':
                    target.model.dataset.add_covariate(analysis_dataset.Covariate('Region','factor'),
                        {s.name:'A' if i%2 else 'B' for i,s in enumerate(target.model.dataset.studies)})
                    target.model.reset_model()
                    target.enable_menu_options_that_require_dataset()
            view = matrix(app, window, 'analysis-data-onearm-proportion', record, keep_results=True,
                          metric_override='PFT', workflow_override=workflow, group_names=(name,), prepare=prepare,
                          parameters={'fp_style':'bmj','digits':6})
            title, path = next(iter(view.results.display_images.items()))
            figure = labels(path)
            assert 'Events / Total' in figure, figure
            assert ('Group' not in figure) if name == 'Group' else ('Participants' in figure), figure
            assert '4 / 20' in figure and '39 / 135' in figure, figure
            target = work / ('bmj-'+workflow+'-'+name+'.svg')
            view.plot_service.export(regenerator='forest', params_path=view.params_paths[title], output_path=str(target))
            assert labels(target) == figure
            check_report(app, view, work, record)
            view.report_action.setChecked(False)
            view._show_report(False)
            record('release-bmj-single-arm', view, group=name, workflow=workflow, labels=figure,
                   plots={title:path}, export=str(target))
            view.close()
    root = Path(__file__).resolve().parents[2]
    for family, sample in (('hr','Pignon2000-HR'),('irr','NielWeise2008-IRR')):
        window.workspace.mark_saved()
        assert window.open(str(root / 'sample_projects' / (sample+'.rcms')),raise_on_error=True)
        window.model.dataset.add_covariate(analysis_dataset.Covariate('Dose','continuous'),
            {s.name:float(i+1) for i,s in enumerate(window.model.get_studies(only_if_included=True))})
        window.model.reset_model()
        window.enable_menu_options_that_require_dataset()
        def regress(dialog):
            for cov, checkbox in dialog.covs_and_check_boxes:
                checkbox.setChecked(cov.name == 'Dose')
            set_parameter(app, dialog, 'digits', 6)
            set_parameter(app, dialog, 'rm.method', 'REML')
            click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
        modal(app, analysis_setup_dialog.AnalysisSetupDialog, regress, window.action_meta_regression.trigger)
        view = next(w for w in app.topLevelWidgets() if isinstance(w,results_window.ResultsWindow) and w.isVisible())
        assert 'intrcpt' not in view._plain_text_report()
        check_report(app, view, work, record)
        table = next(t for s in view.results.sections for t in s.tables if t.title.startswith('Exponentiated coefficients'))
        assert table.rows[0][0] == 'Intercept', table
        check_table_surface(app, view, work, record, table.title, 'release-'+family+'-exponentiated')
        view.report_action.setChecked(True)
        view._show_report(True)
        cursor = view.report_text.document().find('Exponentiated coefficients')
        y = view.report_text.document().documentLayout().blockBoundingRect(cursor.block()).top()
        view.report_text.verticalScrollBar().setValue(round(y))
        record('release-readable-exponentiated', view, family=family, headers=table.headers, rows=table.rows)
        view.close()
