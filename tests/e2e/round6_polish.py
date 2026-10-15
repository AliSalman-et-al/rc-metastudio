"""Selected diagnostic precision and recoverable small-study configuration."""
import json
from pathlib import Path

from PyQt6 import QtWidgets


def run(app, window, work, record):
    from analysis_matrix import run as matrix
    from advanced_workflows import modal, click
    from rc_metastudio import r_bridge, results_window
    from rc_metastudio.publication_bias_dialog import PublicationBiasDialog
    from tests.e2e.audit_round3 import check_report

    for shape in ('continuous', 'factor', 'multiple'):
        for digits in (2, 6):
            window.workspace.mark_saved()
            view = matrix(app, window, 'analysis-diagnostic-regression-' + shape, record,
                          keep_results=True, parameters={'digits': digits})
            raw = json.loads(str(r_bridge.execute_r_string('jsonlite::toJSON(lapply(result$Summary[c("Sensitivity coefficients", "Specificity coefficients")], function(x) unname(as.matrix(x))), digits=16, na="null")')[0]))
            tables = {table.title: table for section in view.results.sections for table in section.tables}
            for name, rows in raw.items():
                table = tables[name]
                assert 'Estimate (logit)' in table.headers, table.headers
                assert '95% CI lower (logit)' in table.headers and '95% CI upper (logit)' in table.headers, table.headers
                assert 'Odds ratio' in table.headers and '95% CI lower (OR)' in table.headers and '95% CI upper (OR)' in table.headers, table.headers
                for displayed, numeric in zip(table.rows, rows, strict=True):
                    for column, (text, value) in enumerate(zip(displayed[1:], numeric, strict=True), 1):
                        if value is None:
                            continue
                        precision = max(3, digits) if table.headers[column] == 'p-value' else digits
                        if table.headers[column] == 'p-value' and value < 10**(-precision):
                            assert text.startswith('< '), (name, text, value)
                        elif value and float(f'{value:.{precision}f}') == 0:
                            assert float(text) != 0, (name, text, value)
                        else:
                            assert text == f'{value:.{precision}f}', (name, table.headers[column], text, value, precision)
            check_report(app, view, work, record)
            record('diagnostic-selected-precision', view, shape=shape, digits=digits,
                   raw_coefficients=raw, tables={name: dict(headers=tables[name].headers, rows=tables[name].rows) for name in raw})
            from tests.e2e.reviewer_fixes import check_table_surface
            for name in raw:
                check_table_surface(app,view,work,record,name,f'diagnostic-{shape}-{digits}-{name.split()[0]}')
            view.close()

    for workflow in ('cumulative', 'subgroup'):
        window.workspace.mark_saved()
        view = matrix(app, window, 'analysis-diagnostic-' + workflow, record,
                      keep_results=True, parameters={'digits':2})
        found = []
        for section in view.results.sections:
            for table in section.tables:
                for column, header in enumerate(table.headers):
                    if not header.startswith('SE ('):
                        continue
                    found.append(table.title)
                    for row in table.rows:
                        value = float(row[column])
                        if value and float(f'{value:.2f}') == 0:
                            assert 'e' in row[column].lower(), row
                        else:
                            assert row[column] == f'{value:.2f}', (workflow, header, row)
        assert found, (workflow, [table.headers for section in view.results.sections for table in section.tables])
        check_report(app, view, work, record)
        record('diagnostic-sequential-selected-precision', view, workflow=workflow, digits=2)
        view.close()

    root = Path(__file__).resolve().parents[2]
    window.workspace.mark_saved()
    assert window.open(str(root / 'sample_projects/NielWeise2008-IRR.rcms'), raise_on_error=True)
    def small_study(dialog):
        explanation = dialog.automatic_test_label.text()
        assert '10' in explanation and '9' in explanation, explanation
        dialog.contour_funnel_check.setChecked(True)
        for invalid in ('abc', '90,,95', '0,101', ''):
            dialog.contour_levels_edit.setText(invalid)
            click(app, dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
            assert dialog.isVisible() and dialog.failure_label.isVisible()
            assert not dialog.progress_bar.isVisible()
            assert 'Contour' in dialog.failure_label.text()
            assert dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).isEnabled()
            record('contour-inline-validation', dialog, input=invalid,
                   failure=dialog.failure_label.text(), eligibility=explanation)
        dialog.contour_levels_edit.setText('90,95,99')
        click(app, dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    modal(app, PublicationBiasDialog, small_study, window.action_publication_bias.trigger)
    view = next(widget for widget in app.topLevelWidgets() if isinstance(widget, results_window.ResultsWindow) and widget.isVisible())
    assert any('contour' in title.lower() for title in view.results.images)
    record('contour-validation-recovered', view, texts=dict(view.texts), plots=dict(view.results.display_images))
    view.close()

    run_headers(app, window, work, record)


def run_headers(app, window, work, record):
    from analysis_matrix import run as matrix
    from tests.e2e.audit_round3 import check_report
    from tests.e2e.header_geometry import check_headers
    from xml.etree import ElementTree as ET
    import re
    pairs = (
        ("Drug", "Control"),
        ("Cognitive behavioural therapy plus usual care", "Usual care only"),
        ("Intensive individualized cognitive behavioural therapy plus structured clinical follow-up", "Standard clinical care"),
    )
    for names in pairs:
        for style in ('default', 'revman', 'bmj'):
            window.workspace.mark_saved()
            view = matrix(app, window, 'analysis-data-twoarm-proportion', record,
                          keep_results=True, parameters={'digits': 6, 'fp_style': style}, group_names=names)
            check_report(app, view, work, record)
            title, path = next(iter(view.results.display_images.items()))
            export = work / ('headers-' + style + '-' + str(len(names[0])) + '.svg')
            view.plot_service.export(regenerator='forest', params_path=view.params_paths[title], output_path=str(export))
            record('wrapped-arm-header-before-assertion', view, style=style, names=names,
                   plots={title:path}, export=str(export))
            measurements = [measurement for source in (path, str(export))
                            for measurement in check_headers(source, names)]
            view.report_action.setChecked(False)
            view._show_report(False)
            app.processEvents()
            record('measured-wrapped-arm-headers', view, style=style, names=names,
                   header_blocks=measurements, plots={title:path}, export=str(export))
            view.close()
