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
                    target.model.add_covariate('Region','factor',
                        {s.label:'A' if i%2 else 'B' for i,s in enumerate(target.model.get_studies(False))})
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
        window.model.add_covariate('Dose','continuous',
            {s.label:float(i+1) for i,s in enumerate(window.model.get_studies(only_if_included=True))})
        window.model.reset_model()
        window.enable_menu_options_that_require_dataset()
        def regress(dialog):
            for cov, checkbox in dialog.covs_and_check_boxes:
                checkbox.setChecked(cov['name'] == 'Dose')
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


def run_small_screen(app, window, work, record):
    from unittest.mock import patch
    from advanced_workflows import modal, click
    from rc_metastudio.about_legal_dialog import AboutLegalDialog
    from rc_metastudio.binary_data_dialog import BinaryBackCalculationDialog
    from rc_metastudio.continuous_data_dialog import ContinuousBackCalculationDialog
    available = QtCore.QRect(50,50,360,240)
    factories = [
        (AboutLegalDialog, lambda: AboutLegalDialog(window)),
        (ContinuousBackCalculationDialog, lambda: ContinuousBackCalculationDialog(
            'Back-calculation depends on the relationship between the two population standard deviations.\nShould RC MetaStudio assume they are equal?',
            'Yes (default)', 'No', parent=window)),
        (BinaryBackCalculationDialog, lambda: BinaryBackCalculationDialog(
            {'op1':dict(a=55,b=100,c=90,d=100),'op2':dict(a=10,b=100,c=5,d=100)},parent=window)),
    ]
    from rc_metastudio import adaptive_window
    register = adaptive_window.register_adaptive_window
    def bounded_register(dialog, role):
        return register(dialog, role, available_geometry_provider=lambda _window: available)
    with patch('rc_metastudio.adaptive_window.register_adaptive_window',side_effect=bounded_register):
        for kind, factory in factories:
            def probe(dialog):
                app.processEvents()
                frame = dialog.frameGeometry()
                assert available.contains(frame), (kind.__name__,frame,available)
                scroll = dialog.content_scroll_area if isinstance(dialog,AboutLegalDialog) else dialog.content_scroll
                bar = scroll.verticalScrollBar()
                if isinstance(dialog,AboutLegalDialog):
                    assert bar.maximum() > 0, (kind.__name__,frame,bar.maximum())
                elif bar.maximum() == 0:
                    assert scroll.widget().height() <= scroll.viewport().height(), (kind.__name__,frame)
                    assert dialog.choice1_btn.isVisible() and dialog.choice2_btn.isVisible()
                record('release-small-screen-top',dialog,kind=kind.__name__,available=str(available),frame=str(frame),scroll_max=bar.maximum(),scope='synthetic available geometry on native xcb')
                bar.setValue(bar.maximum())
                app.processEvents()
                record('release-small-screen-bottom',dialog,kind=kind.__name__)
                dialog.reject()
            modal(app,kind,probe,lambda: factory().exec())
