"""Diagnostic coefficient display precision against the actual fitted result."""

import json


def run(app, window, work, record):
    from analysis_matrix import run as matrix
    from rc_metastudio import r_bridge
    from tests.e2e.analysis_result_checks import check_report
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
            from tests.e2e.plot_workflow_support import check_table_surface
            for name in raw:
                check_table_surface(app,view,work,record,name,f'diagnostic-{shape}-{digits}-{name.split()[0]}')
            view.close()
