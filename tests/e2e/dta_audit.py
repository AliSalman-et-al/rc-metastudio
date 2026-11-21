"""DTA method availability through real Qt controls and the installed R backend."""

from PyQt6.QtCore import QCoreApplication, QDeadlineTimer, QEvent, Qt
from PyQt6.QtWidgets import QComboBox, QLabel, QDialogButtonBox
from PyQt6.QtTest import QTest
from typing import Callable, cast
from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
from rc_metastudio.analysis.diagnostic_metrics_dialog import DiagnosticMetricsDialog


def check_fixed_workflow(app, window, workflow, record):
    import json
    import math
    from analysis_matrix import set_parameter
    from rc_metastudio import r_bridge
    from rc_metastudio.results.window import ResultsWindow
    from tests.e2e.report_retention import assert_report

    raw = window.model.get_current_raw_data()
    group_column = next((cov for cov in window.model.current_sheet.covariates if cov['name'] == 'Group'), None)
    groups = [str(study.covariate_values[group_column['id']])
              for study in window.model.get_studies()] if group_column else []
    for selected, method in ((('dor',), 'diagnostic.fixed.mh'),
                             (('dor',), 'diagnostic.fixed.peto'),
                             (('lr',), 'diagnostic.fixed.mh')):
        dialog = AnalysisSetupDialog(window.model, parent=window, analysis_type=workflow,
                                     external_params={'cov_name': 'Group'} if workflow == 'subgroup' else None,
                                     diagnostic_metrics=selected, on_result=window.analysis,
                                     confidence_level=window.model.get_confidence_level())
        dialog.method_cbo_box.setCurrentIndex(dialog.method_cbo_box.findData(method))
        set_parameter(app, dialog, 'digits', 6)
        dialog.show()
        app.processEvents()
        record('dta-fixed-workflow-setup', dialog, workflow=workflow, method=method, metrics=selected,
               raw_counts=raw, groups=groups)
        button = dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        assert button is not None
        button.click()
        app.processEvents()
        view = next(w for w in app.topLevelWidgets() if isinstance(w, ResultsWindow) and w.isVisible())
        title = {'cumulative': 'Cumulative results', 'leave-one-out': 'Leave-one-out results',
                 'subgroup': 'Model Results'}[workflow]
        tables = [(section, table) for section in view.results.sections for table in section.tables if table.title == title]
        metrics = ('DOR',) if selected == ('dor',) else ('PLR', 'NLR')
        assert len(tables) == len(metrics), tables
        record('dta-fixed-workflow-result', view, workflow=workflow, method=method,
               sections=[(section.title, table.rows) for section, table in tables])
        for metric in metrics:
            title = {'DOR': 'diagnostic odds ratio', 'PLR': 'positive likelihood ratio', 'NLR': 'negative likelihood ratio'}[metric]
            table = next(table for section, table in tables if section.title.casefold().startswith(title))
            group_order = [row[0].removeprefix('Subgroup ') for row in table.rows[:-1]] if workflow == 'subgroup' else []
            if workflow == 'subgroup':
                assert table.rows[-1][0] == 'Overall' and set(group_order) == set(groups), table.rows
            columns = '; '.join(f'{name} <- c({",".join(str(row[i]) for row in raw)})'
                                for i, name in enumerate(('TP', 'FN', 'FP', 'TN')))
            subsets = {'cumulative': 'lapply(seq_along(TP), seq_len)',
                       'leave-one-out': 'c(list(seq_along(TP)), lapply(seq_along(TP), function(i) setdiff(seq_along(TP), i)))',
                       'subgroup': 'c(lapply(group.order, function(g) which(groups == g)), list(seq_along(TP)))'}[workflow]
            arguments = 'ai=FN[i], bi=TP[i], ci=TN[i], di=FP[i]' if metric == 'NLR' else 'ai=TP[i], bi=FN[i], ci=FP[i], di=TN[i]'
            call = f'metafor::rma.peto({arguments})' if method.endswith('peto') else f'metafor::rma.mh({arguments}, measure="{"OR" if metric == "DOR" else "RR"}")'
            reference_code = f'''jsonlite::toJSON(local({{
                {columns}; groups <- unlist(jsonlite::fromJSON('{json.dumps(groups)}'))
                group.order <- unlist(jsonlite::fromJSON('{json.dumps(group_order)}'))
                subsets <- {subsets}
                lapply(subsets, function(i) {{ fit <- {call}
                    c(estimate=exp(fit$b[1]),ci_lower=exp(fit$ci.lb),ci_upper=exp(fit$ci.ub),se=fit$se,p=fit$pval)
                }})
            }}), digits=16)'''
            references = json.loads(str(r_bridge.execute_r_string(reference_code)[0]))
            assert len(table.rows) == len(references), (table.rows, references)
            for row, reference in zip(table.quantities, references, strict=True):
                quantities = {quantity.role: quantity.value for cell in row for quantity in cell}
                for role, expected in zip(('estimate', 'ci_lower', 'ci_upper', 'se', 'p'), reference, strict=True):
                    value = quantities[role]
                    assert value is not None and math.isclose(value, expected, rel_tol=1e-8, abs_tol=1e-8), (workflow, method, metric, role, value, expected)
            record('dta-fixed-workflow-package-reference', view, workflow=workflow, method=method,
                   metric=metric, reference_command=reference_code, expected=references, displayed_rows=table.rows)
        assert_report(view)
        view.close()
        app.processEvents()


def check_small_study_threshold(app, window, record, *, system_clipboard=True):
    from rc_metastudio.analysis.small_study_effects_dialog import SmallStudyEffectsDialog
    from rc_metastudio.results.window import ResultsWindow
    model = window.model
    original = [model.data(model.index(row, model.INCLUDE_STUDY), Qt.ItemDataRole.CheckStateRole)
                for row in range(len(model.get_studies(only_if_included=False)))]
    try:
        for row in range(len(original)):
            assert model.setData(model.index(row, model.INCLUDE_STUDY),
                                 Qt.CheckState.Checked if row < 7 else Qt.CheckState.Unchecked,
                                 Qt.ItemDataRole.CheckStateRole)
        assert window.action_go.isEnabled()
        dialog = SmallStudyEffectsDialog(model, parent=window, on_result=window.analysis)
        dialog.show()
        app.processEvents()
        assert dialog.use_package_minimum_check.isChecked()
        assert not dialog.minimum_studies_spin.isEnabled()
        assert dialog.minimum_studies_spin.minimum() == 3
        assert dialog._eligibility_report is not None
        assert not any(item.available for item in dialog._eligibility_report.methods)
        record('small-study-package-default-threshold', dialog)
        dialog.use_package_minimum_check.setChecked(False)
        dialog.minimum_studies_spin.setValue(7)
        app.processEvents()
        assert dialog._eligibility_report is not None
        assert any(item.method == 'peters' and item.available for item in dialog._eligibility_report.methods)
        assert dialog._request().to_mapping()['k.min'] == 7
        record('small-study-explicit-threshold', dialog)
        run_button = dialog.button_box.button(QDialogButtonBox.StandardButton.Ok)
        assert run_button is not None
        run_button.click()
        app.processEvents()
        assert not dialog.failure_label.isVisible(), dialog.failure_label.text()
        view = next(w for w in app.topLevelWidgets() if isinstance(w, ResultsWindow) and w.isVisible())
        assert 'Peters' in view.manuscript.plain_text()
        assert 'failed' not in view.manuscript.plain_text().lower(), view.manuscript.plain_text()
        seven_study_results = view.results
        record('small-study-seven-study-results', view, report=view.manuscript.plain_text())
        navigation_width = view.results_nav_splitter.sizes()[0]
        assert navigation_width <= max(20 * view.fontMetrics().height(), .22 * view.width()), (navigation_width, view.width())
        from tests.e2e.report_retention import assert_report
        assert_report(view, system_clipboard=system_clipboard)
        view.close()
        from PyQt6.QtCore import QSettings
        from rc_metastudio.settings import RESULTS_WORKSPACE_GROUP
        assert not QSettings().contains(RESULTS_WORKSPACE_GROUP + '/splitter_proportions')
        dialog.deleteLater()
        for row in range(len(original)):
            assert model.setData(model.index(row, model.INCLUDE_STUDY),
                                 Qt.CheckState.Checked if row == 0 else Qt.CheckState.Unchecked,
                                 Qt.ItemDataRole.CheckStateRole)
        assert window.action_go.isEnabled() and window.action_cum_ma.isEnabled()
        assert not window.action_loo_ma.isEnabled()
        record('singleton-analysis-actions', window)
        window.action_go.trigger()
        app.processEvents()
        setup = next(w for w in app.topLevelWidgets() if isinstance(w, AnalysisSetupDialog) and w.isVisible())
        from analysis_matrix import set_parameter
        set_parameter(app, setup, 'inference.method', 'knha')
        button = setup.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        assert button is not None
        button.click()
        app.processEvents()
        view = next(w for w in app.topLevelWidgets() if isinstance(w, ResultsWindow) and w.isVisible())
        assert 'Analysis warnings' in view.manuscript.plain_text()
        assert 'test="z"' in view.manuscript.plain_text().replace(' ', '')
        assert view.results.software.startswith('metafor ')
        assert ', ' not in view.results.software, view.results.software
        assert 'normal approximation' in view.manuscript.methods
        assert 'Knapp' not in view.manuscript.methods
        assert view.results.details.count('Inference:') == 1
        assert 'Inference: Normal approximation' in view.results.details
        assert view.results_nav_splitter.sizes()[0] <= max(20 * view.fontMetrics().height(), .22 * view.width())
        record('singleton-package-warning-result', view, report=view.manuscript.plain_text())
        assert_report(view, system_clipboard=system_clipboard)
        view.close()
        reopened = ResultsWindow(seven_study_results, parent=window)
        reopened.show()
        deadline = QDeadlineTimer(2000)
        while abs(reopened.results_nav_splitter.sizes()[0] - navigation_width) > 2 and not deadline.hasExpired():
            cast(Callable[[int], None], QTest.qWait)(10)
        assert abs(reopened.results_nav_splitter.sizes()[0] - navigation_width) <= 2
        assert not QSettings().contains(RESULTS_WORKSPACE_GROUP + '/splitter_proportions')
        record('results-sidebar-repeated-open', reopened)
        reopened.results_nav_splitter.moveSplitter(round(reopened.width() * .3), 1)
        app.processEvents()
        chosen_sizes = reopened.results_nav_splitter.sizes()
        chosen_ratio = chosen_sizes[0] / sum(chosen_sizes)
        reopened.close()
        restored = ResultsWindow(seven_study_results, parent=window)
        restored.show()
        deadline = QDeadlineTimer(2000)
        while not deadline.hasExpired():
            sizes = restored.results_nav_splitter.sizes()
            if sum(sizes) and abs(sizes[0] / sum(sizes) - chosen_ratio) <= .02:
                break
            cast(Callable[[int], None], QTest.qWait)(10)
        record('results-sidebar-user-size-restored', restored)
        restored_sizes = restored.results_nav_splitter.sizes()
        assert abs(restored_sizes[0] / sum(restored_sizes) - chosen_ratio) <= .02, (restored_sizes, chosen_sizes, restored.width())
        restored.close()
    finally:
        for row, value in enumerate(original):
            assert model.setData(model.index(row, model.INCLUDE_STUDY), value,
                                 Qt.ItemDataRole.CheckStateRole)


def check_method_choices(app, window, record):
    for workflow in (None, 'cumulative', 'leave-one-out', 'subgroup'):
        for metrics in (('lr',), ('dor',)):
            dialog = AnalysisSetupDialog(window.model, parent=window,
                                         analysis_type=workflow, diagnostic_metrics=metrics,
                                         confidence_level=window.model.get_confidence_level())
            try:
                dialog.show()
                app.processEvents()
                choices = {dialog.method_cbo_box.itemData(i)
                           for i in range(dialog.method_cbo_box.count())}
                record('dta-method-availability', dialog, workflow=workflow,
                       metrics=metrics, choices=sorted(choices))
                assert ('diagnostic.fixed.peto' in choices) == (metrics == ('dor',)), choices
                assert 'diagnostic.fixed.mh' in choices, (workflow, metrics, choices)
            finally:
                dialog.hide()
                dialog.deleteLater()
                app.processEvents()


    for attempt in range(3):
        window.action_go.trigger()
        app.processEvents()
        selector = next(widget for widget in app.topLevelWidgets()
                        if isinstance(widget, DiagnosticMetricsDialog) and widget.isVisible())
        selector.btn_ok.click()
        app.processEvents()
        setup = next(widget for widget in app.topLevelWidgets()
                     if isinstance(widget, AnalysisSetupDialog) and widget.isVisible())
        setup.reject()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        assert not window.findChildren(DiagnosticMetricsDialog)
        record('dta-selector-cancel-cleanup', window, attempt=attempt)


def check_combined_controls(app, dialog, record):
    labels = [label.text() for label in dialog.parameter_grp_box.findChildren(QLabel)]
    assert 'Sensitivity, specificity' in labels, labels
    def estimators():
        return [control for control in dialog.current_widgets
                if isinstance(control, QComboBox) and control.count() == 2 and control.findData('ML') >= 0]
    assert not estimators(), 'Reitsma estimator is shown for separate univariate fits'
    previous = dialog.method_cbo_box.currentText()
    dialog.method_cbo_box.setCurrentText('Reitsma bivariate model')
    app.processEvents()
    assert estimators(), 'Joint model estimator is unavailable for Reitsma'
    record('dta-combined-joint-controls', dialog)
    dialog.method_cbo_box.setCurrentText(previous)
    app.processEvents()
    assert not estimators()
    record('dta-combined-univariate-controls', dialog)


def check_small_sample_ui(app, window, record):
    from rc_metastudio.results.window import ResultsWindow
    model = window.model
    count = len(model.get_studies(only_if_included=False))
    original = [model.data(model.index(row, model.INCLUDE_STUDY), Qt.ItemDataRole.CheckStateRole)
                for row in range(count)]
    try:
        for k in (3, 4, 5):
            for row in range(count):
                assert model.setData(model.index(row, model.INCLUDE_STUDY),
                                     Qt.CheckState.Checked if row < k else Qt.CheckState.Unchecked,
                                     Qt.ItemDataRole.CheckStateRole)
            dialog = AnalysisSetupDialog(model, parent=window, diagnostic_metrics=('sens', 'spec'),
                                         confidence_level=model.get_confidence_level(), on_result=window.analysis)
            dialog.show()
            app.processEvents()
            assert dialog.current_method == 'diagnostic.reitsma'
            record('dta-small-sample-setup', dialog, included=k, total=count)
            run_button = dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
            assert run_button is not None
            run_button.click()
            app.processEvents()
            views = [widget for widget in app.topLevelWidgets()
                     if isinstance(widget, ResultsWindow) and widget.isVisible()]
            if views:
                view = views[0]
                assert view.results.analysis_method == 'diagnostic.reitsma'
                plots = [section.plot_kind for section in view.results.sections if section.kind == 'image']
                if 'sroc' not in plots:
                    assert 'SROC' in view.manuscript.plain_text(), view.manuscript.plain_text()
                record('dta-small-sample-result', view, included=k, plot_kinds=plots,
                       report=view.manuscript.plain_text())
                view.close()
            else:
                assert dialog.analysis_error_panel.isVisible()
                assert 'Reitsma' in dialog.analysis_error_label.text()
                record('dta-small-sample-package-error', dialog, included=k,
                       error=dialog.analysis_error_details.toPlainText())
                dialog.reject()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    finally:
        for row, value in enumerate(original):
            assert model.setData(model.index(row, model.INCLUDE_STUDY), value,
                                 Qt.ItemDataRole.CheckStateRole)


def check_partial_count_previews(app, dialog, cell, record):
    table = dialog.two_by_two_table
    def select(metric):
        index = dialog.effect_combo_box.findData(metric)
        assert index >= 0, metric
        dialog.effect_combo_box.setCurrentIndex(index)
        app.processEvents()
        return dialog.effect_text_box.text()
    dialog.clear_button.click()
    for row, column, value in ((0, 0, 10), (1, 0, 5), (0, 1, 2), (1, 1, 8)):
        cell(table, row, column, value)
    cell(table, 1, 1, '')
    record('dta-incomplete-preview-after-delete', dialog, raw=dialog.get_raw_diagnostic_data())
    for metric in ('Spec', 'PLR', 'NLR', 'DOR'):
        preview = dialog.analysis_unit.get_effect_and_ci_for_source('derived_preview', metric, dialog.arm_key, dialog.confidence_multiplier)
        assert preview == (None, None, None), (metric, preview)
        if metric in ('Sens', 'Spec'):
            assert select(metric) == '', (metric, dialog.effect_text_box.text())
    assert select('Sens') != '', ('Sens', dialog.get_raw_diagnostic_data())
    dialog.clear_button.click()
    cell(table, 0, 0, '10')
    cell(table, 1, 0, '5')
    record('dta-incomplete-preview-half-table', dialog, raw=dialog.get_raw_diagnostic_data())
    for metric in ('Spec', 'PLR', 'NLR', 'DOR'):
        preview = dialog.analysis_unit.get_effect_and_ci_for_source('derived_preview', metric, dialog.arm_key, dialog.confidence_multiplier)
        assert preview == (None, None, None), (metric, preview)
        if metric in ('Sens', 'Spec'):
            assert select(metric) == '', (metric, dialog.effect_text_box.text())
    assert abs(float(select('Sens')) - 10 / 15) < .0001, ('Sens', dialog.effect_text_box.text())
    cell(table, 0, 1, '2')
    cell(table, 1, 1, '8')
    for metric in ('Sens', 'Spec', 'PLR', 'NLR', 'DOR'):
        values = dialog.analysis_unit.get_effect_and_ci_for_source('derived_preview', metric, dialog.arm_key, dialog.confidence_multiplier)
        assert values[0] is not None, metric
        if metric in ('Sens', 'Spec'):
            assert select(metric) != '', metric
    record('dta-complete-preview-recovered', dialog, raw=dialog.get_raw_diagnostic_data())
    dialog.reject()
