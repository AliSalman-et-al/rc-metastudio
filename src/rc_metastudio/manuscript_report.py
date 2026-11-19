"""Manuscript content taken exclusively from an executed result."""
from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol
from rc_metastudio.qt_object_guard import required
from dataclasses import dataclass, replace
from decimal import Decimal
import re
import math
from rc_metastudio.analysis_results import ResultTable, ResultSection
from rc_metastudio.application_metadata import CITATION_DOI, citation_text
from rc_metastudio.svg_rendering import svg_bytes_for_qt
from rc_metastudio.result_formatting import numeric_cell, numeric_columns, report_numbers, table_html
from html import escape
import io
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QFont, QImage, QPainter, QPdfWriter, QTextDocument, QPageSize, QTextOption
from PyQt6.QtSvg import QSvgRenderer
from docx import Document
from docx.shared import Mm, RGBColor, Pt
from docx.oxml.ns import qn
from rc_metastudio import __version__

if TYPE_CHECKING:
    from rc_metastudio.analysis_dataset import Sheet
    from rc_metastudio.analysis_results import AnalysisResult
    from rc_metastudio.trial_sequential_analysis import TsaRequest, TsaRun


class AnalysisResultHandler(Protocol):
    def __call__(
        self, result: "AnalysisResult", /, *, source_sheet: "Sheet | None" = None,
        change_settings: Callable[[dict[str, object]], None] | None = None,
        manuscript: "ManuscriptReport | None" = None,
    ) -> object: ...


_PACKAGE_REFERENCES = {
    'meta': 'Balduzzi, S., Rücker, G., & Schwarzer, G. (2019). How to perform a meta-analysis with R: a practical tutorial. Evidence-Based Mental Health, 22(4), 153–160. doi:10.1136/ebmental-2019-300117.'
}


def binary_correction_prose(method, adjust, label, double_zero):
    if method in ("binary.fixed.mh", "binary.fixed.peto"):
        estimator = "Mantel–Haenszel" if method.endswith("mh") else "Peto"
        text = f"A continuity correction of {adjust} was applied to estimable individual study effects only; the pooled {estimator} estimate uses the original counts."
        if double_zero:
            text += f" The {double_zero} " + ("study with no events in either arm had" if double_zero == 1 else "studies with no events in either arm had") + " no individual effect estimate and did not contribute to pooling or heterogeneity estimation."
        return text
    text = f"A continuity correction of {adjust} was applied to {label}."
    if method in ("binary.random", "binary.fixed.inv.var") and double_zero:
        text += f" The {double_zero} " + ("study with no events in either arm was retained" if double_zero == 1 else "studies with no events in either arm were retained") + " with this correction."
    return text


def _inference_prose(parameters, confidence, applied_inference: tuple[str, ...]):
    codes = applied_inference or ((str(parameters['inference.method']),) if parameters.get('inference.method') else ())
    if not codes:
        return ''
    descriptions = {'z': 'the normal approximation', 'normal': 'the normal approximation',
                    't': 'the t distribution', 'knha': 'the Knapp–Hartung adjustment',
                    'adhoc': 'the modified Knapp–Hartung adjustment'}
    description = ' and '.join(descriptions[code] for code in codes)
    suffix = ' across the fitted models' if len(codes) > 1 else ''
    return f"Confidence intervals ({float(confidence):g}%) used {description}{suffix}."



def methods_prose(metric, model, parameters, confidence, workflow, details, fits, applied_inference: tuple[str, ...]=(), *, missing_years=False):
    plural = {"odds ratio": "Odds ratios", "risk ratio": "Risk ratios", "hazard ratio": "Hazard ratios",
              "mean difference": "Mean differences", "standardized mean difference": "Standardized mean differences"}.get(metric, (metric[:1].upper() + metric[1:]) + " estimates")
    sentence = f"{plural} were pooled using a {model} model"
    estimator = parameters.get('rm.method', parameters.get('estimator'))
    if estimator and model == 'random-effects':
        label = _estimator_prose(estimator)
        sentence += f" with the {label} estimator of between-study variance"
    parts = [sentence + '.']
    if any('reitsma' in method.lower() for _, method, _ in fits):
        parts = []
        for label, method, fit_parameters in fits:
            if 'reitsma' in method.lower():
                continue
            text = f'{label[:1].upper() + label[1:]} estimates were pooled using the {method} method'
            estimator = fit_parameters.get('rm.method')
            if estimator and 'random' in method.lower():
                name = _estimator_prose(estimator)
                text += f' with the {name} estimator of between-study variance'
            parts.append(text + '.')
    inference = _inference_prose(parameters, confidence, applied_inference)
    if inference:
        parts.append(inference)
    parts.extend(_workflow_prose(workflow, parameters, details, missing_years=missing_years))
    if workflow == 'meta-regression' and metric in ('odds ratio', 'risk ratio', 'hazard ratio', 'incidence rate ratio'):
        parts.append('Regression coefficients and their confidence intervals are on the log scale.')
    if any('reitsma' in method.lower() for _, method, _ in fits):
        parts.append('Sensitivity and specificity were jointly modeled using the Reitsma bivariate model.')
    return ' '.join(parts)


def p_value(value, quantities=()):
    """Keep producer text; apply the app's P floor only to an exact raw P."""
    if not value or value in ("NA", "—", "Not estimable"):
        return "—"
    if value.strip().startswith(("<", ">")):
        return value.strip()
    p = next((q.value for q in quantities if q.role == 'p'), None)
    return "< 0.001" if p is not None and p < .001 else value


def _estimator_prose(estimator):
    from rc_metastudio.analysis_method_labels import parameter_value_display_label
    label = parameter_value_display_label('rm.method', estimator)
    return label[:1].lower() + label[1:] if estimator in ('ML', 'REML', 'EB', 'PMM') else label

def _p_clause(value):
    return "P " + (value if value.startswith(("<", ">")) else "= " + value)


def _row(table, index):
    numbers = table.quantities[index] if table.quantities else ((),) * len(table.headers)
    values, quantities = dict(zip(table.headers, table.rows[index])), dict(zip(table.headers, numbers))
    _alias_quantity_fields(table, numbers, values, quantities)
    if table.label_column is not None:
        values[_row_context_label(table)] = table.rows[index][table.label_column]
    if table.role in ('subgroup_test', 'model_tests'):
        values['Test'] = table.rows[index][0]
    return values, quantities


def _alias_quantity_fields(table, numbers, values, quantities):
    labels = {'estimate': 'Estimate', 'q': 'Q', 'df': 'df', 'p': 'p-value', 'i2': 'I²', 'tau2': 'τ²', 'k': 'k',
              'se': 'SE', 'statistic': 't' if table.inference in ('t', 'knha', 'adhoc') else 'Z'}
    statistic_header = None
    for header, qs in zip(table.headers, numbers):
        for q in qs:
            label = labels.get(q.role)
            if label:
                values[label], quantities[label] = values[header], qs
            if q.role == 'statistic' and statistic_header is None:
                statistic_header = header
    if statistic_header is not None:
        values['Statistic'], quantities['Statistic'] = values[statistic_header], quantities[statistic_header]


def _row_context_label(table):
    if table.role == 'coefficients':
        return 'Term'
    if table.workflow == 'subgroup':
        return 'Subgroups'
    return {'cumulative': 'Study added', 'leave_one_out': 'Study omitted'}.get(table.role, 'Level')


def _cells(table, index):
    numbers = table.quantities[index] if table.quantities else ((),) * len(table.headers)
    return list(zip(table.rows[index], numbers))


def _table(title, headers, rows, *, role, **context):
    return ResultTable(title, tuple(headers), tuple(tuple(text for text, qs in row) for row in rows),
                       tuple(tuple(qs for text, qs in row) for row in rows) if any(qs for row in rows for text, qs in row) else (), role=role, **context)


def _interval_fields(table):
    fields = {q.role: (header, q) for row in table.quantities for header, qs in zip(table.headers, row) for q in qs}
    kind = 'pi' if 'pi_lower' in fields else 'ci'
    lower, upper = fields.get(kind+'_lower'), fields.get(kind+'_upper')
    if not lower or not upper:
        return None, None, ''
    return lower[0], upper[0], f'{lower[1].level:g}% {kind.upper()}'

def _heterogeneity_sentence(values, quantities, heading="Heterogeneity"):
    if values.get('Q') == '—' and values.get('df') == '—':
        return [heading + ': not estimable (k = 1).']
    parts = []
    if "Q" in values:
        test = f"Q = {values['Q']}"
        if "df" in values:
            test += f" (df = {values['df']}"
        if "p-value" in values:
            test += ("; " if "df" in values else " (") + _p_clause(p_value(values['p-value'], quantities.get('p-value', ())))
        if "df" in values or "p-value" in values:
            test += ")"
        parts.append(test)
    if values.get('I²') and values['I²'] not in ("NA", "NaN"):
        parts.append(f"I² = {values['I²']}")
    if 'τ²' in values:
        parts.append(f"τ² = {values['τ²']}")
    return [heading + ": " + "; ".join(parts) + "."] if parts else []

def _study_inputs(result):
    for section in result.sections:
        for table in section.tables:
            if table.role == 'study_results':
                yield section, table


def _study_result_rows(result):
    rows = []
    for section, table in _study_inputs(result):
        analysis = table.metric_label or section.title.removesuffix(' summary')
        if section.source_key == 'Weights':
            analysis = result.manuscript_metric or section.title
        for i, row in enumerate(table.rows):
            cells = _cells(table, i)
            values = (cells[0], cells[1], (row[2] + ' to ' + row[3], cells[2][1]+cells[3][1]), cells[4]) if len(row) == 5 else (cells[0], ('—', ()), ('—', ()), cells[1])
            rows.append(((analysis, ()), *values))
    return rows

def _study_results(result, template, level):
    rows = _study_result_rows(result)
    row_label = 'Fit' if any(t.role == 'leave_one_out' for s in result.sections for t in s.tables) else 'Study'
    headers = ('Analysis', row_label, 'Effect', level, 'Weight')
    if rows and all(row[2][0] == row[3][0] == '—' for row in rows):
        headers = ('Analysis', row_label, 'Weight')
        rows = [(row[0], row[1], row[4]) for row in rows]
    if len({row[0] for row in rows}) == 1:
        headers = headers[1:]
        rows = [row[1:] for row in rows]
    paragraphs = () if rows else ('No study-level estimates or weights are available for this analysis. See Supplementary details for the full output.',)
    return replace(template, title='Study results', paragraphs=paragraphs,
                   tables=(_table('Study results', headers, rows, role='study_results'),) if rows else ())


def _reference_lines(result):
    references = []
    for section in result.sections:
        if section.source_key in {'References', 'small-study.references'}:
            references.extend(re.sub(r'^\d+[.)]\s*', '', line.strip()) for line in section.value.splitlines() if line.strip())
    return references



def _references(result):
    references = _reference_lines(result)
    references = list(dict.fromkeys(line for line in references if CITATION_DOI not in line and 'RC MetaStudio: open-source desktop software' not in line))
    if re.search(r'(^|,\s*)meta ', result.software) and not any('10.1136/ebmental-2019-300117' in line for line in references):
        references.append('Implementation reference: ' + _PACKAGE_REFERENCES['meta'])
    packages = [line for line in references if line.startswith(('Implementation reference:', 'Statistical implementation:'))]
    methods = [line for line in references if line not in packages]
    return [(citation_text(), 'software')] + [(re.sub(r'^[A-Z][^:]{2,60}:\s+', '', line), 'package') for line in packages] + [(re.sub(r'^[A-Z][^:]{2,60}:\s+', '', line), 'method') for line in methods]


def _held_section_content(section):
    tables = tuple(replace(table, title=table.title if section.title == table.title else section.title + ' — ' + table.title) for table in section.tables)
    paragraphs = tuple(re.sub(r'\bPooled ([A-Z])(?=[a-z])', lambda match: 'Pooled ' + match[1].lower(), paragraph) for paragraph in section.paragraphs if paragraph not in section.prediction_notes)
    if not tables and section.value:
        paragraphs = (section.title + ':', *section.value.splitlines(), *paragraphs)
    return tables, paragraphs


def _held_sections(result):
    sections = []
    for section in result.sections:
        if section.kind != 'text' or section.source_key in {'References', 'small-study.references', 'small-study.warning'}:
            continue
        tables, paragraphs = _held_section_content(section)
        sections.append(replace(section, title='Supplementary details', value='',
                                paragraphs=paragraphs, tables=tables))
    references = tuple(f'{number}. {line}' for number, (line, _) in enumerate(_references(result), 1))
    sections.append(ResultSection('report.references', 'text', len(sections), 'Supplementary details', '', 'References', paragraphs=references))
    return sections


def _prediction_rows(table, lower, upper, ci_level, vertical, fit, summary, analysis_context=''):
    for index in range(len(table.rows)):
        values, quantities = _row(table, index)
        context = values.get('Subgroups', table.metric_label if vertical else analysis_context)
        interval = values[lower] + ' to ' + values[upper]
        fit.append(((ci_level.replace(' PI', '') + ' prediction interval' + (' (' + context + ')' if context else ''), ()),
                    (interval, quantities[lower]+quantities[upper])))
        lead = 'Overall, the' if context.casefold() == 'overall' else f'In {context}, the' if context else 'The'
        summary.append(f"{lead} {ci_level.replace(' PI', '')} prediction interval was {interval}.")

def _pooled_statistics(values, quantities, overall, calculation, metric):
    overall_values, overall_qs = overall
    calc_values, calc_qs = calculation
    combined, combined_qs = {**calc_values, **overall_values, **values}, {**calc_qs, **overall_qs, **quantities}
    stat = next((key for key in ('t', 'Z') if key in combined), None)
    statistic = 't' if stat == 't' else 'z'
    df, method = combined.get('df'), ''
    if statistic == 't' and df:
        statistic += f' (df = {df})'
        method = f'The overall effect was tested using t with {df} degrees of freedom.'
    se, se_scale = _pooled_standard_error(combined, combined_qs, metric)
    test = (combined.get(stat, '—'), combined_qs.get(stat, ())) if stat else ('—', ())
    p = (p_value(combined.get('p-value', ''), combined_qs.get('p-value', ())), combined_qs.get('p-value', ()))
    return statistic, se, se_scale, test, p, method

def _pooled_prose(result, values, effect, effect_metric, coefficient, statistic, test, p, level, lower, upper, summary):
    if coefficient and effect == 'Intercept':
        return
    lead = f"The pooled {effect_metric}"
    if result.analysis_method == 'diagnostic.reitsma':
        qualifier = "summary " if effect_metric in ("sensitivity", "specificity", "false-positive rate") else ""
        lead = f"The {qualifier}{effect_metric}"
    if coefficient:
        lead = f"For {effect}, the coefficient"
    elif values.keys() & {"Subgroups", "Term", "Level"}:
        lead = f"In {effect}, the pooled {effect_metric}"
        if effect.lower() == "overall":
            lead = f"Overall, the pooled {effect_metric}"
    within_subgroup = 'Subgroups' in values and values['Subgroups'].casefold() != 'overall'
    inference = '' if within_subgroup else (f"; {statistic} = {test}" if test != '—' else '') + ('; ' + _p_clause(p) if p != '—' else '')
    summary.append(f"{lead} was {values['Estimate']} ({level} {values[lower]} to {values[upper]}{inference}).")


def _effect_metric(metric, section, table, vertical, coefficient):
    if vertical:
        metric = table.title.lower()
    elif table.metric_label:
        metric = table.metric_label.lower()
    if not coefficient and metric.endswith('transformed proportion'):
        return 'proportion'
    return metric


def _pooled_rows(result, section, table, lower, upper, ci_level, vertical, overall, calculation, pooled, fit, summary, methods):
    metric = result.manuscript_metric or "effect"
    statistic, level = "z", ci_level
    coefficient = table.role == 'coefficients'
    for index in range(len(table.rows)):
        values, quantities = _row(table, index)
        if not values.get('Estimate'):
            continue
        if 'k' in values and 'Subgroups' in values and values['Subgroups'].casefold() != 'overall':
            fit.append((('Studies in ' + values['Subgroups'] + ' (k)', ()), (values['k'], quantities.get('k', ()))))
        effect_metric = _effect_metric(metric, section, table, vertical, coefficient)
        effect = _pooled_effect_label(values, table, vertical, effect_metric, coefficient, _multiple_metrics(result))
        statistic, se, se_scale, test, p, method = _pooled_statistics(values, quantities, overall, calculation, table.metric)
        if not coefficient and not vertical and values.get("Subgroups", "Overall").casefold() == "overall":
            methods.append(method)
        pooled.append(((effect[:1].upper() + effect[1:], ()), (values['Estimate'], quantities['Estimate']),
                       (values[lower] + ' to ' + values[upper], quantities[lower]+quantities[upper]), se, (se_scale, ()), test, p))
        _pooled_prose(result, values, effect, effect_metric, coefficient, statistic, test[0], p[0], level, lower, upper, summary)
    return level, statistic

def _heterogeneity_rows(table, fit, summary, residual=None):
    for index in range(len(table.rows)):
        values, quantities = _row(table, index)
        if table.role == 'residual_heterogeneity':
            summary.append(_residual_heterogeneity_sentence(values, quantities, residual))
        else:
            subgroup = values.get('Subgroups', '')
            heading = 'Overall heterogeneity' if subgroup.casefold() == 'overall' else 'Heterogeneity in ' + subgroup if subgroup else 'Heterogeneity'
            summary.extend(_heterogeneity_sentence(values, quantities, heading=heading))
        _heterogeneity_fit_rows(values, quantities, fit)


def _fit_table(table, fit, summary):
    if table.role == 'subgroup_test' and table.rows:
        values, numbers = _row(table, 0)
        test = 'F' if table.inference in ('t', 'knha', 'adhoc') else 'Q'
        summary.append(f"Test for subgroup differences: {test} = {values['Statistic']} (df = {values['df']}; {_p_clause(p_value(values['p-value'], numbers.get('p-value', ())))}).")
        fit.extend(((label, ()), (p_value(values[key], numbers.get(key, ())) if key == 'p-value' else values[key], numbers.get(key, ())))
                   for key, label in (("Test", "Between-group test"), ("Statistic", "Between-group statistic"), ("df", "Between-group degrees of freedom"), ("p-value", "Between-group P")))
        return True
    return _model_fit_table(table, fit, summary)

def _model_fit_table(table, fit, summary):
    if table.role == 'model_fit':
        fit.extend(_cells(table, index) for index in range(len(table.rows)))
        return True
    if table.role == 'model_tests':
        for index in range(len(table.rows)):
            values, numbers = _row(table, index)
            name = values['Test']
            fit.extend(((label + ' (' + name + ')', ()), (p_value(values[key], numbers.get(key, ())) if key == 'p-value' else values[key], numbers.get(key, ())))
                       for key, label in (('Statistic', 'Test statistic'), ('df', 'Test degrees of freedom'), ('p-value', 'Test P')))
        return True
    if table.role == 'model_specification':
        return True
    if table.role == 'overall_test':
        return True
    return False

def _horizontal_table(table):
    vertical = table.vertical and 'estimate' in _table_roles(table)
    if vertical:
        table = _table(table.title, [row[0] for row in table.rows], [[_cells(table, i)[1] for i in range(len(table.rows))]], role=table.role, metric=table.metric, metric_label=table.metric_label, workflow=table.workflow, inference=table.inference)
    return table, vertical

def _residual_statistics(section):
    return {label: source.rows[i][j] for source in section.tables if source.role == 'model_fit'
            for i, row in enumerate(source.quantities) for j, cell in enumerate(row)
            for q in cell if q.value is not None for role, label in (('df', 'df'), ('i2', 'I²')) if q.role == role}


def _report_heterogeneity(result, section, table, fit, summary):
    start = len(fit)
    _heterogeneity_rows(table, fit, summary, _residual_statistics(section))
    if _multiple_metrics(result):
        fit[start:] = [((label[0] + ' (' + section.title.removesuffix(' summary') + ')', label[1]), value) for label, value in fit[start:]]



def _report_table(result, section, table, summary, pooled, fit, level, statistic, overall, calculation, methods):
    table, vertical = _horizontal_table(table)
    if table.role == 'calculation':
        return level, statistic
    if table.role == 'study_results':
        return level, statistic
    lower, upper, ci_level = _interval_fields(table)
    if table.role in ('cumulative', 'leave_one_out'):
        _sequential_prose(result, section, table, lower, upper, ci_level, summary)
        return ci_level or level, statistic
    if table.role == 'prediction' and lower and upper:
        context = section.title.removesuffix(' summary') if _multiple_metrics(result) else ''
        _prediction_rows(table, lower, upper, ci_level, vertical, fit, summary, context)
        return level, statistic
    if table.role in ('pooled', 'coefficients') and lower and upper and 'estimate' in _table_roles(table):
        level, statistic = _pooled_rows(result, section, table, lower, upper, ci_level, vertical, overall, calculation, pooled, fit, summary, methods)
        return level, statistic
    if table.role in ('heterogeneity', 'residual_heterogeneity') and 'q' in _table_roles(table):
        _report_heterogeneity(result, section, table, fit, summary)
        return level, statistic
    _fit_table(table, fit, summary)
    return level, statistic


def _finite_sequential_quantity(quantities, role):
    return next((q.value for q in quantities
                 if q.role == role and q.value is not None and math.isfinite(q.value)), None)


def _has_sequential_estimate(record):
    return _finite_sequential_quantity(record[1].get('Estimate', ()), 'estimate') is not None


def _omission_endpoint(item, available, field):
    ties = sum(number == item[1] for _, number in available) - 1
    suffix = f'; tied with {ties} other omission' + ('s' if ties != 1 else '') if ties else ''
    return f"{item[0][field]} (omitting {item[0]['Study omitted']}{suffix})"


def _omission_endpoints(estimable, field, role):
    available = [(values, _finite_sequential_quantity(qs.get(field, ()), role))
                 for values, qs in estimable]
    available = [(values, number) for values, number in available if number is not None]
    if not available:
        return '', False, 0
    low = min(available, key=lambda pair: pair[1])
    high = max(available, key=lambda pair: pair[1])
    if low[1] == high[1]:
        return low[0][field], False, len(available)
    return (_omission_endpoint(low, available, field) + ' to ' +
            _omission_endpoint(high, available, field)), True, len(available)


def _omission_range_prose(estimable, total, summary):
    effect_range, varied, count = _omission_endpoints(estimable, 'Estimate', 'estimate')
    denominator = f'all {total} omission fits' if count == total else f'the {count} of {total} omission fits that could be estimated'
    if effect_range:
        summary.append(f"Across {denominator}, pooled estimates ranged from {effect_range}." if varied else
                       f"Every estimable omission fit ({count} of {total}) gave a pooled estimate of {effect_range}.")
    i2_range, varied, count = _omission_endpoints(estimable, 'I²', 'i2')
    if i2_range:
        if count != total:
            summary.append(f'I² was reported for {count} of {total} omission fits.')
        summary.append(f"I² after omission ranged from {i2_range}." if varied else
                       f"I² was {i2_range} in every omission fit" + ('.' if count == total else ' reporting it.'))


def _sequential_reference_prose(reference, cumulative, metric, lower, upper, level, summary):
    if reference is not None and _has_sequential_estimate(reference):
        values, _ = reference
        lead = 'After the final addition' if cumulative else 'With all studies'
        heterogeneity = f"; I² = {values['I²']}" if values.get('I²') not in (None, '', '—', 'NA') else ''
        summary.append(f"{lead}, the pooled {metric} was {values['Estimate']} ({level} {values[lower]} to {values[upper]}{heterogeneity}).")


def _sequential_table_number(result, section, table):
    sequential_tables = [(s, t) for s in result.sections for t in s.tables
                         if t.role in {'cumulative', 'leave_one_out'}]
    return next(i for i, (s, t) in enumerate(sequential_tables, 1) if s is section and t is table)



def _sequential_missing_prose(subsets, label, cumulative, summary):
    missing = [values[label] for values, quantities in subsets
               if not _has_sequential_estimate((values, quantities))]
    if missing:
        context = 'after adding' if cumulative else 'after omitting'
        summary.append(f"The model could not be estimated {context} " + '; '.join(missing) + '. See the detailed rows and analysis notes.')


def _sequential_prose(result, section, table, lower, upper, level, summary):
    if not table.rows or not lower or not upper:
        return
    cumulative = table.role == 'cumulative'
    label = 'Study added' if cumulative else 'Study omitted'
    records = [_row(table, i) for i in range(len(table.rows))]
    metric = _effect_metric(result.manuscript_metric or 'effect', section, table, False, False)
    reference = records[-1] if cumulative else records[0]
    _sequential_reference_prose(reference, cumulative, metric, lower, upper, level, summary)
    subsets = records if cumulative else records[1:]
    estimable = [row for row in subsets if _has_sequential_estimate(row)]
    if not cumulative:
        _omission_range_prose(estimable, len(subsets), summary)
    elif records[0][0].get('k') == '1':
        summary.append('Heterogeneity at the first step was not estimable (k = 1).')
    _sequential_missing_prose(subsets, label, cumulative, summary)
    number = _sequential_table_number(result, section, table)
    summary.append(f'Table {number} gives the estimate, {level} and I² after each addition.' if cumulative else f'Table {number} gives every omission fit.')


def _sequential_report_table(table, title):
    lower, upper, level = _interval_fields(table)
    headers = list(table.headers)
    start = headers.index(lower)
    headers[start] = level
    headers.remove(upper)
    p_header = next((header for header, cell in zip(table.headers, table.quantities[0]) if any(q.role == 'p' for q in cell)), None)
    headers = ['P' if header == p_header else header for header in headers]
    rows = []
    for index in range(len(table.rows)):
        values, quantities = _row(table, index)
        cells = []
        for header in headers:
            if header == level:
                cells.append((values[lower] + ' to ' + values[upper], quantities[lower] + quantities[upper]))
            else:
                key = 'p-value' if header == 'P' else header
                text = p_value(values[key], quantities.get(key, ())) if header == 'P' else values[key]
                cells.append((text, quantities.get(key, ())))
        rows.append(cells)
    return _table(title, headers, rows, role=table.role, metric=table.metric, metric_label=table.metric_label, workflow=table.workflow, inference=table.inference, label_column=table.label_column)


def _section_statistics(section):
    overall = next((_row(t, 0) for t in section.tables if t.role == 'overall_test' and len(t.rows) == 1 and
                    any(q.role == 'statistic' for row in t.quantities for cell in row for q in cell) and
                    not any(q.role == 'estimate' for row in t.quantities for cell in row for q in cell)), ({}, {}))
    calculation = next((_row(t, 0) for t in section.tables if t.role == 'calculation' and t.rows), ({}, {}))
    return overall, calculation

def _report_subgroup_tests(text_sections, fit, summary):
    for section in text_sections:
        for table in section.tables:
            if table.role == 'subgroup_test':
                _fit_table(table, fit, summary)


def _sequential_sections(result, text_sections):
    sequential = []
    for section in text_sections:
        for table in section.tables:
            if table.role not in ('cumulative', 'leave_one_out'):
                continue
            title = table.title + (' — ' + section.title.removesuffix(' summary') if _multiple_metrics(result) else '')
            note = 'Note: k is the number of studies in the fitted model; it can be smaller than the number entered when the package excludes non-estimable study effects.'
            sequential.append(replace(section, title=table.title, paragraphs=(note,),
                                      tables=(_sequential_report_table(table, title),)))
    return sequential


def _supplementary_sections(result, primary):
    represented = {q for section in primary for table in section.tables
                   for row in table.quantities for cell in row for q in cell}
    supplementary = []
    for section in _held_sections(result):
        tables = []
        for table in section.tables:
            quantities = {q for row in table.quantities for cell in row for q in cell}
            # Only these tables supply the primary summaries. Equal numbers in
            # another table can describe a different comparison or context.
            transferred = _primary_covers_source_context(table)
            if not (transferred and quantities and quantities <= represented):
                tables.append(table)
        supplementary.append(replace(section, tables=tuple(tables)))
    return supplementary



def _report_sections(result, summary, methods):
    text_sections = [section for section in result.sections if section.kind == 'text']
    summary.extend(section.value for section in text_sections if section.source_key == 'small-study.warning' and section.value.strip())
    if not text_sections:
        return [], []
    pooled, fit = [], [((label, ()), (value, ())) for label, value in result.manuscript_model_info]
    coefficients = []
    level, statistic = '95% CI', 'z'
    coefficient_level, coefficient_statistic = level, statistic
    _report_subgroup_tests(text_sections, fit, summary)
    for section in result.sections:
        if section.kind != 'text':
            continue
        overall, calculation = _section_statistics(section)
        for table in section.tables:
            if table.role == 'subgroup_test':
                continue
            if table.role == 'coefficients':
                coefficient_level, coefficient_statistic = _report_table(
                    result, section, table, summary, coefficients, fit, coefficient_level,
                    coefficient_statistic, overall, calculation, methods)
            else:
                level, statistic = _report_table(result, section, table, summary, pooled, fit, level, statistic, overall, calculation, methods)
    primary = _primary_sections(result, text_sections, pooled, fit, level, statistic)
    if coefficients and primary:
        primary[0] = _regression_section(result, primary[0], coefficients,
                                         coefficient_level, coefficient_statistic)
    sequential = _sequential_sections(result, text_sections)
    if sequential:
        primary = sequential + primary
    supplementary = _supplementary_sections(result, primary)
    return primary, supplementary


def _primary_covers_source_context(table):
    if table.role in {'study_results', 'residual_heterogeneity', 'overall_test', 'subgroup_test', 'cumulative', 'leave_one_out'}:
        return True
    if table.vertical or table.label_column is not None:
        return False
    return table.role == 'heterogeneity' or (table.role in {'pooled', 'prediction'} and table.workflow == 'standard')


def _primary_sections(result, text_sections, pooled, fit, level, statistic):
    template = text_sections[0]
    primary_title = 'Diagnostic summary' if result.analysis_method == 'diagnostic.reitsma' else 'Pooled effect'
    notes = _prediction_notes(text_sections)
    if any(t.role in {'cumulative', 'leave_one_out'} for s in text_sections for t in s.tables):
        return [replace(template, title='Model fit', paragraphs=notes,
                        tables=(_table('Model fit', ('Statistic', 'Value'), fit, role='model_fit'),))] if fit else []
    estimates = replace(template, title=primary_title, paragraphs=(() if pooled else
        ('No structured pooled estimates are available for this analysis. See Supplementary details for the full output.',)),
        tables=(_pooled_table(primary_title, pooled, level, statistic),))
    sections = [estimates, replace(template, title='Model fit', paragraphs=notes,
                        tables=(_table('Model fit', ('Statistic', 'Value'), fit, role='model_fit'),)),
                _study_results(result, template, level)]
    if not any(section.tables for section in text_sections):
        return []
    return [replace(section, tables=tuple(_available_columns(table) for table in section.tables if table.rows)) for section in sections]


def _regression_section(result, section, coefficients, level, statistic):
    metric = (result.manuscript_metric or 'effect').lower()
    if metric.endswith('transformed proportion'):
        metric = 'proportion'
    scale = _coefficient_scale(coefficients, metric)
    title = f'Model coefficients ({scale})'
    coefficient_table = _pooled_table(title, coefficients, level, statistic, scale=scale)
    fitted = [replace(table, title=f'Fitted subgroup effects ({metric})',
                      headers=tuple(f'{header} ({metric})' if header == 'Estimate' or header.endswith('% CI')
                                    else header for header in table.headers))
              for table in section.tables]
    return replace(section, title=title, paragraphs=(),
                   tables=(_available_columns(replace(coefficient_table, role='coefficients')), *fitted))


def _coefficient_scale(rows, metric):
    scales = {quantity.scale for row in rows for quantity in row[1][1] if quantity.role == 'estimate'}
    if scales == {'log'}:
        return f'log {metric} scale'
    if scales == {'logit'}:
        return 'logit scale'
    if scales == {'arcsine'}:
        return 'arcsine scale'
    if scales == {'freeman-tukey'}:
        return 'Freeman–Tukey scale'
    return f'{metric} scale'


def _pooled_table(title, rows, level, statistic, *, scale=''):
    estimate = f'Estimate ({scale})' if scale else 'Estimate'
    interval = f'{level} ({scale})' if scale else level
    scales = {row[4][0] for row in rows if row[3][0] not in ('', '—', 'NA')}
    if len(scales) == 1 and scales <= {'log', 'logit', 'outcome'}:
        se_scale = next(iter(scales))
        return _table(title, ('Effect', estimate, interval, f'SE ({se_scale} scale)', statistic, 'P'),
                      [(*row[:4], *row[5:]) for row in rows], role='pooled')
    return _table(title, ('Effect', estimate, interval, 'SE', 'SE scale', statistic, 'P'), rows, role='pooled')


def _available_columns(table):
    has_se = 'SE' in table.headers and any(row[table.headers.index('SE')] not in ('', '—', 'NA') for row in table.rows)
    indexes = [i for i, header in enumerate(table.headers) if (header == 'SE scale' and has_se) or any(row[i] not in ('', '—', 'NA') for row in table.rows)]
    return replace(table, headers=tuple(table.headers[i] for i in indexes),
                   rows=tuple(tuple(row[i] for i in indexes) for row in table.rows),
                   quantities=tuple(tuple(row[i] for i in indexes) for row in table.quantities))


def _subgroup_test_prose(result):
    subgroup_test = next((table for section in result.sections for table in section.tables if table.role == 'subgroup_test' and table.rows), None)
    if subgroup_test:
        wording = 'Subgroup differences were tested with an F test.' if subgroup_test.inference in ('t', 'knha', 'adhoc') else 'Subgroup differences were tested with Cochran’s Q across subgroup estimates (inverse-variance weighted).'
        return ' ' + wording
    return ""


def _package_reference_numbers(package, references):
    return [str(number) for number, (line, kind) in enumerate(references, 1)
                   if kind == 'package' and (line == _PACKAGE_REFERENCES.get(package) or re.search(r'\b' + re.escape(package) + r'(?:\s+package\b|:)', line, re.IGNORECASE))]


def _software_prose(result, references):
    software = f'Statistical analyses were performed using RC MetaStudio (version {__version__}; Research Consultancy) [1]'
    packages = [package.strip().rsplit(' ', 1) for package in result.software.split(',')
                if package.strip() and not package.strip().startswith('RCMetaR')]
    names = []
    for package in packages:
        if len(package) != 2:
            continue
        numbers = _package_reference_numbers(package[0], references)
        marker = ' [' + ', '.join(numbers) + ']' if numbers else ''
        names.append(f'{package[0]} (version {package[1]}){marker}')
    if names:
        joined = names[0] if len(names) == 1 else ' and '.join(names) if len(names) == 2 else ', '.join(names[:-1]) + ', and ' + names[-1]
        software += ' with the R package' + ('s ' if len(names) > 1 else ' ') + joined
    return software



def _report_methods(result, pooled_methods):
    methods = " ".join(filter(None, (result.manuscript_methods, *dict.fromkeys(pooled_methods))))
    methods += _subgroup_test_prose(result)
    if any(q.role == 'q' for s in result.sections for t in s.tables for row in t.quantities for cell in row for q in cell):
        methods += " Heterogeneity" + (" for the separate univariate fits" if 'Reitsma' in methods else '') + " was assessed with Cochran’s Q and I²."
    references = _references(result)
    method_numbers = [str(number) for number, (_, kind) in enumerate(references, 1) if kind == 'method']
    if method_numbers:
        methods = re.sub(r'\.(?=\s|$)', ' [' + ', '.join(method_numbers) + '].', methods, count=1)
    software = _software_prose(result, references)
    return software + '. ' + methods.strip()


def _methods_fragments(text):
    """Keep package emphasis identical in HTML and Word without marking up plain text."""
    start = 0
    for match in re.finditer(r'\b[A-Za-z][\w.]*\b(?= \(version [^);]+\))', text):
        yield text[start:match.start()], False
        yield match.group(), True
        start = match.end()
    yield text[start:], False


def _table_html(table, table_number):
    return f'<p style="page-break-after:avoid;"><b>Table {table_number}. {escape(table.title)}</b></p>' + table_html(table.headers, table.rows)


@dataclass(frozen=True)
class ManuscriptReport:
    title: str
    methods: str
    primary_sections: tuple[ResultSection, ...]
    supplementary_sections: tuple[ResultSection, ...]
    figures: tuple[ResultSection, ...]
    summary: tuple[str, ...]
    comparison: str = ''
    configuration: str = ''

    @property
    def results(self):
        return ' '.join(self.summary)

    @property
    def sections(self) -> tuple[ResultSection, ...]:
        return self.primary_sections + self.supplementary_sections

    @property
    def has_supplementary_details(self) -> bool:
        return any(section.source_key != "References" and (section.tables or section.paragraphs)
                   for section in self.supplementary_sections)

    @classmethod
    def from_result(cls, result):
        summary = [result.manuscript_context] if result.manuscript_context else []
        pooled_methods = []
        sections, supplementary = _report_sections(result, summary, pooled_methods)
        methods = _report_methods(result, pooled_methods)
        return cls(
            title=result.manuscript_title or 'Meta-analysis',
            methods=methods,
            primary_sections=tuple(sections),
            supplementary_sections=tuple(supplementary),
            figures=tuple(s for s in result.sections if s.kind == 'image'),
            summary=tuple(summary),
            comparison=result.manuscript_comparison,
            configuration=result.details,
        )

    def numbered_sections(self, supplementary: bool):
        sections = self.supplementary_sections if supplementary else self.primary_sections
        number = sum(len(section.tables) for section in self.primary_sections) if supplementary else 0
        for section in sections:
            yield section, enumerate(section.tables, number + 1)
            number += len(section.tables)

    def plain_text(self):
        parts = [self.title, self.comparison]
        for heading, text in (('Methods', self.methods), ('Results', self.results)):
            if text.strip():
                parts.extend((heading, report_numbers(text) if heading == 'Results' else text))
        for number, figure in enumerate(self.figures, 1):
            if figure.paragraphs:
                parts.extend((f'Figure {number}. {figure.title}', *figure.paragraphs))
        number = 0
        for section in self.sections:
            if section.source_key == "References":
                parts.append("References")
            for table in section.tables:
                number += 1
                parts.append(f'Table {number}. {table.title}')
                parts.append('\t'.join(table.headers))
                parts.extend('\t'.join(report_numbers(cell) if numeric_cell(cell) else cell for cell in row)
                             for row in table.rows)
            parts.extend(map(report_numbers, section.paragraphs))
        if self.configuration:
            parts.extend(('Model configuration', self.configuration))
        return '\n\n'.join(parts)

    def html(self, supplementary=False, *, heading=True):
        parts = [f'<h1>{escape(self.title)}</h1><p>{escape(self.comparison)}</p>'] if heading else []
        for name, text in (('Methods', self.methods), ('Results', self.results)):
            if text.strip():
                formatted = ''.join('<i>' + escape(part) + '</i>' if italic else escape(part) for part, italic in _methods_fragments(text)) if name == 'Methods' else escape(report_numbers(text)).replace('\n', '<br>')
                parts.append(f'<a name="{name.lower()}"></a><h2>{name}</h2><p>{formatted}</p>')
        if supplementary:
            parts = []
        else:
            for number, figure in enumerate(self.figures, 1):
                if figure.paragraphs:
                    parts.append(f'<p><b>Figure {number}. {escape(figure.title)}</b><br>'
                                 + '<br>'.join(map(escape, figure.paragraphs)) + '</p>')
        configuration = ''
        if supplementary and self.configuration:
            configuration = '<a name="model-configuration"></a><h2>Model configuration</h2><p>' + escape(self.configuration).replace('\n', '<br>') + '</p>'
        return ''.join(parts) + self.tables_html(supplementary) + configuration

    def tables_html(self, supplementary=False):
        parts = ['<a name="report-tables"></a>'] if not supplementary else []
        if supplementary and self.has_supplementary_details:
            parts.append('<h2>Supplementary details</h2>')
        for section, tables in self.numbered_sections(supplementary):
            if section.source_key == 'References':
                parts.append('<a name="references"></a><h2>References</h2>')
            for table_number, table in tables:
                parts.append(f'<a name="table-{table_number}"></a>')
                parts.append(_table_html(table, table_number))
            parts.extend(f'<p>{escape(report_numbers(paragraph))}</p>' for paragraph in section.paragraphs)
        return ''.join(parts)


def _tsa_accrued_number(value: float, hr: bool) -> str:
    number = Decimal(f"{value:.6g}" if hr else str(value)).normalize()
    return f"{number:,f}"


def _tsa_methods(run: "TsaRun", request: "TsaRequest") -> list[str]:
    from rc_metastudio.trial_sequential_analysis import EFFECT_SOURCES, HKSJ_NOTE

    options = request.options
    hr = request.metric == "HR"
    units = "units of statistical information" if hr else "participants"
    order = {"year": "publication-year order", "table": "table order"}[options.order]
    left, right = request.favoured_labels()
    test = {"two-sided": "two-sided test", "benefit": f"one-sided test favouring {left}",
            "harm": f"one-sided test favouring {right}"}[options.test]
    measure_name = {"RR": "risk ratios", "OR": "odds ratios", "RD": "risk differences",
                    "MD": "mean differences", "HR": "hazard ratios"}[request.metric]

    effect = f"{run.anticipated_effect:.4g}"
    effect_phrase = {"OR": "an OR", "RR": "an RR", "RD": "an RD", "MD": "a mean difference",
                     "HR": "an HR", "Peto OR": "a Peto OR"}[request.measure]
    source = (" (entered)" if run.effect_source == "user" else
              f", the {EFFECT_SOURCES[run.effect_source]}")
    ris_label = "entered required information size" if options.manual_ris is not None else "required information size"
    model = (f"random-effects model with the {request.tau_method} estimator of between-study variance"
             if request.model == "random" else request.model_label.replace("fixed", "fixed-effect") + " model")
    method = [
        f"We pooled {measure_name} ({request.metric}) using a {model} and the Wald z statistic.",
        f"Studies were added in {order}.",
        f"The {ris_label} was {_tsa_accrued_number(run.ris, hr)} {units} using a {test} "
        f"with α = {options.alpha:g} and {options.power:.0%} power. "
        f"The anticipated intervention effect was {effect_phrase} of {effect}{source}.",
    ]
    if request.inference in {"knha", "adhoc"}:
        method.insert(1, HKSJ_NOTE)
    if run.control_proportion is not None:
        control = "entered" if run.control_source == "user" else "unweighted mean of control arms"
        method.append(f"The control event proportion was {run.control_proportion:.2%} ({control}).")
    if request.metric == "MD" and run.variance is not None:
        variance = "entered" if run.variance_source == "user" else "fixed-effect-weighted pooled arm variance"
        method.append(f"The participant variance was {run.variance:.4g} ({variance}).")
    method.append(_tsa_heterogeneity_prose(run, request, units))
    method.extend(_tsa_monitoring_methods(run, request))
    return method


def _tsa_heterogeneity_prose(run: "TsaRun", request: "TsaRequest", units: str) -> str:
    hr = request.metric == "HR"
    options = request.options
    if request.model != "random":
        if run.fixed_effect_note is None:
            return "Heterogeneity adjustment was inapplicable to the fixed-effect model."
        d2, ris = run.fixed_effect_note.d2, _tsa_accrued_number(run.fixed_effect_note.ris, hr)
        size, note_units = ("required information", "units of information") if hr else ("required information size", units)
        return (f"The fixed-effect model does not adjust the information size for heterogeneity; "
                f"a random-effects model gave D² = {d2:.1%} and a {size} of {ris} "
                f"{note_units} (Wetterslev 2017).")
    if options.heterogeneity == "none":
        return "The analysis used no heterogeneity adjustment."
    measure, value = ("D²", run.d2) if options.heterogeneity == "d2" else ("I²", run.i2)
    return f"The information size was adjusted for {measure} = {value:.1%}."


def _tsa_monitoring_methods(run: "TsaRun", request: "TsaRequest") -> list[str]:
    options = request.options
    method: list[str] = []
    spending = "O’Brien-Fleming" if options.spending == "obf" else "Pocock"
    method.append(f"Monitoring boundaries used Lan-DeMets {spending} spending.")
    method.append("Futility boundaries were non-binding." if options.futility else "Futility boundaries were omitted.")
    if run.lil_lambda is not None:
        method.append(f"The penalised Z-curve used the law of the iterated logarithm with λ = {run.lil_lambda:g} (Hu 2007).")
    if run.excluded_studies:
        method.append("The fitted model excluded " + ", ".join(run.excluded_studies) + ".")
    if options.manual_ris is None:
        method.append("Sensitivity analyses repeated the analysis with alternative anticipated intervention effects.")
    method.append("The analysis used " + run.result.software.replace(", ", " and ") + ".")

    return method


def _tsa_crossing_prose(run: "TsaRun", request: "TsaRequest") -> list[str]:
    hr = request.metric == "HR"
    units = "units of statistical information" if hr else "participants"
    left, right = request.favoured_labels()
    effect = f"{run.anticipated_effect:.4g}"
    crossing = run.crossing
    results: list[str] = []
    if crossing is not None:
        at = f"when {crossing.study} was added ({_tsa_accrued_number(crossing.accrued, hr)} {units}, {crossing.fraction:.0%} of the required information size)."
        if run.conclusion == "crossed-futility":
            results.append(f"The cumulative Z-curve crossed the futility boundary {at}")
            results.append(f"This suggests that an intervention effect of {effect} is unlikely, "
                           "without establishing its absence.")
        else:
            favoured = left if run.conclusion == "crossed-benefit" else right
            results.append(f"The cumulative Z-curve crossed the monitoring boundary favouring {favoured} {at}")
    elif run.conclusion == "ris-reached":
        results.append("Accrued information reached the required information size without the cumulative Z-curve crossing a monitoring boundary.")
    elif run.conclusion == "none":
        results.append("The cumulative Z-curve crossed neither a monitoring nor a futility boundary.")
    else:
        raise ValueError("Trial sequential analysis returned an invalid conclusion.")
    return results


def _tsa_interval_prose(run: "TsaRun", confidence: float) -> list[str]:
    final = run.final
    results: list[str] = []
    if run.crossing != final:
        results.append(f"Accrued information is {final.fraction:.0%} of the required information size.")
    results.append(f"The conventional {confidence:g}% CI was {final.lower:.4g} to {final.upper:.4g}.")
    if final.fraction >= 1:
        results.append("A TSA-adjusted CI is not reported because the required information size was reached.")
    elif final.adjusted_lower is not None and final.adjusted_upper is not None:
        results.append(f"The TSA-adjusted CI was {final.adjusted_lower:.4g} to {final.adjusted_upper:.4g}.")
    elif final.adjusted_lower is not None:
        results.append(f"The one-sided TSA-adjusted lower limit was {final.adjusted_lower:.4g}.")
    elif final.adjusted_upper is not None:
        results.append(f"The one-sided TSA-adjusted upper limit was {final.adjusted_upper:.4g}.")
    if run.lil_lambda is not None:
        results.append(f"The final penalised Z-score was {final.penalised_z:.4g}." if final.penalised_z is not None
                       else "The final penalised Z-score was unavailable at the accrued statistical information.")
    return results


def _tsa_results(run: "TsaRun", request: "TsaRequest") -> tuple[str, ...]:
    effect = f"{run.anticipated_effect:.4g}"
    results = _tsa_crossing_prose(run, request)
    results.extend(_tsa_interval_prose(run, request.confidence))
    if run.conclusion in {"crossed-benefit", "crossed-harm"}:
        results.append("Because the cumulative Z-curve crossed the monitoring boundary, the result remains "
                       "statistically significant after accounting for repeated significance testing.")
    elif run.conclusion == "ris-reached":
        results.append(f"The required information size was reached without demonstrating an intervention effect of {effect}.")
    elif run.conclusion == "none":
        results.append(f"More information is needed before an intervention effect of {effect} can be confirmed or rejected.")

    return tuple(results)


def _tsa_references(run: "TsaRun", request: "TsaRequest") -> ResultSection:
    references = [
        "Wetterslev J, Thorlund K, Brok J, Gluud C. J Clin Epidemiol. 2008;61:64–75.",
        "Wetterslev J, Thorlund K, Brok J, Gluud C. BMC Med Res Methodol. 2009;9:86.",
        "Lan KKG, DeMets DL. Discrete sequential boundaries for clinical trials. Biometrika. 1983;70:659–663.",
    ]
    if (request.options.manual_ris is None or run.effect_source == "wetterslev-2017-nearest-95-ci" or run.control_source.startswith("wetterslev-2017")
            or run.variance_source.startswith("wetterslev-2017")):
        references.append("Wetterslev J, Jakobsen JC, Gluud C. BMC Med Res Methodol. 2017;17:39.")
    if run.effect_source == "imberger-2016-10-percent-rrr":
        references.append("Imberger G, Thorlund K, Gluud C, Wetterslev J. BMJ Open. 2016;6:e011890.")
    if run.lil_lambda is not None:
        references.append("Hu M, Cappelleri JC, Lan KKG. Clin Trials. 2007;4:329–340.")
    return ResultSection("trial-sequential.references", "text", 2, "References",
                         "\n".join(references), "References", paragraphs=tuple(references))


def trial_sequential_report(run: "TsaRun", request: "TsaRequest", context: str) -> ManuscriptReport:
    from rc_metastudio.trial_sequential_analysis import TSA_TITLE

    return ManuscriptReport(
        TSA_TITLE, " ".join(_tsa_methods(run, request)), tuple(section for section in run.result.sections if section.tables),
        (_tsa_references(run, request),), tuple(
            replace(section, paragraphs=("Marker area is proportional to the information each trial added.",))
            for section in run.result.sections if section.kind == "image"
        ),
        _tsa_results(run, request), comparison=context.replace("\n", " · "),
    )


def figure_source(path, clip_bounds=None):
    if str(path).lower().endswith(('.svg', '.svgz')):
        svg = QSvgRenderer(svg_bytes_for_qt(path, clip_bounds))
        size = svg.defaultSize()
        return svg, size.width() / size.height()
    image = QImage(str(path))
    if image.isNull():
        raise ValueError(f'Cannot read figure: {path}')
    return image, image.width() / image.height()


def paint_figure(painter, source, rect):
    if isinstance(source, QSvgRenderer):
        source.render(painter, rect)
    else:
        painter.drawImage(rect, source)


def _workflow_prose(workflow, parameters, details, *, missing_years=False):
    parts = []
    if workflow == 'subgroup':
        parts.append(f"Subgroup analyses were performed by {parameters.get('cov_name', 'the selected covariate')}.")
    elif workflow == 'meta-regression':
        moderators = next((line.removeprefix('Moderators: ') for line in details.splitlines() if line.startswith('Moderators: ')), '')
        if moderators:
            parts.append(f"The meta-regression model included {moderators}.")
    elif workflow == 'cumulative':
        sequence = {'table': 'study table order', 'year': 'publication-year order (earliest first)',
                    'effect': 'ascending order of the individual study effect estimates'}.get(parameters.get('cum_sequence', 'table'), 'study table order')
        sentence = f'Cumulative meta-analysis refitted the model after each study was added in {sequence}'
        if parameters.get('cum_sequence') == 'year' and missing_years:
            sentence += '; studies without a year were added last, in table order'
        parts.append(sentence + '.')
    elif workflow == 'leave-one-out':
        parts.append('Leave-one-out analyses refitted the model after omitting each study in turn. Each fit’s pooled estimate and confidence interval are reported, with I² where the package reports it.')
    return parts


def _docx_table(document, table):
    target = document.add_table(rows=1, cols=len(table.headers))
    target.autofit = True
    section = document.sections[-1]
    available = section.page_width - section.left_margin - section.right_margin
    widths = _docx_column_widths(table, available)
    for column, width in zip(target.columns, widths):
        column.width = width
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'bottom'):
        rule = OxmlElement('w:' + edge)
        rule.set(qn('w:val'), 'single')
        rule.set(qn('w:sz'), '6')
        borders.append(rule)
    target._tbl.tblPr.append(borders)
    target.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
    numeric = numeric_columns(table.rows) or (False,) * len(table.headers)
    for index, (row, values) in enumerate(zip([target.rows[0], *[target.add_row() for _ in table.rows]], (table.headers, *table.rows))):
        for column, (cell, value) in enumerate(zip(row.cells, values)):
            _style_docx_cell(cell, value, widths[column], numeric[column], index == 0)


def _docx_sections(document, report, supplementary):
    if supplementary and report.has_supplementary_details:
        document.add_heading('Supplementary details', 1)
    for section, tables in report.numbered_sections(supplementary):
        if section.source_key == 'References':
            document.add_heading('References', 1)
        for table_number, table in tables:
            caption = document.add_paragraph(f'Table {table_number}. {table.title}', style='Caption')
            caption.paragraph_format.keep_with_next = True
            _docx_table(document, table)
            document.add_paragraph()
        for paragraph in section.paragraphs:
            document.add_paragraph(report_numbers(paragraph))


def _docx_styles(document):
    document.styles['Normal'].font.size = Pt(11)
    for name in ('Normal', 'Title', 'Heading 1', 'Caption'):
        document.styles[name].font.name = 'Arial'
        fonts = document.styles[name].element.rPr.rFonts
        for attribute in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
            fonts.attrib.pop(qn('w:' + attribute), None)
        document.styles[name].font.color.rgb = RGBColor(0, 0, 0)
    title_properties = document.styles['Title'].element.pPr
    if title_properties is not None:
        border = title_properties.find(qn('w:pBdr'))
        if border is not None:
            title_properties.remove(border)


def _docx_figures(document, figures):
    from PyQt6.QtCore import QBuffer, QIODevice
    for number, figure in enumerate(figures, 1):
        source, ratio = figure_source(figure.display_image or figure.value)
        width = _figure_width(figure, ratio)
        pixel_width = round(width / 25.4 * 300)
        pixel_height = round(pixel_width / ratio)
        page_height = round(230 / 25.4 * 300)
        for top in range(0, pixel_height, page_height):
            image = QImage(pixel_width, min(page_height, pixel_height-top), QImage.Format.Format_RGB32)
            image.fill(Qt.GlobalColor.white)
            painter = QPainter(image)
            painter.translate(0, -top)
            paint_figure(painter, source, QRectF(0, 0, pixel_width, pixel_height))
            painter.end()
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, 'PNG')
            document.add_page_break()
            document.add_picture(io.BytesIO(bytes(required(buffer.data().data(), "encoded figure"))), width=Mm(width))
            document.add_paragraph(f'Figure {number}. {figure.title}' + (' (continued)' if top else ''))
            if not top:
                for note in figure.paragraphs:
                    document.add_paragraph(note)



def write_docx(report, path):
    document = Document()
    _docx_styles(document)
    section = document.sections[0]
    section.page_width = Mm(210)
    section.left_margin = section.right_margin = Mm(15)
    document.add_heading(report.title, 0)
    document.add_paragraph(report.comparison)
    for heading, text in (('Methods', report.methods), ('Results', report.results)):
        if text.strip():
            document.add_heading(heading, 1)
            paragraph = document.add_paragraph()
            for part, italic in (_methods_fragments(text) if heading == 'Methods' else ((report_numbers(text), False),)):
                paragraph.add_run(part).italic = italic
    _docx_sections(document, report, False)
    _docx_figures(document, report.figures)
    _docx_sections(document, report, True)
    if report.configuration:
        document.add_heading('Model configuration', 1)
        for line in report.configuration.splitlines():
            document.add_paragraph(line)
    document.save(path)


def _print_document():
    document = QTextDocument()
    document.setDefaultFont(QFont('Arial', 11))
    option = document.defaultTextOption()
    option.setWrapMode(QTextOption.WrapMode.WordWrap)
    document.setDefaultTextOption(option)
    # Qt's default print palette inherits the application's text colour.
    # Exported pages are white even when the application uses a dark palette.
    document.setDefaultStyleSheet('* { color: #000000; background-color: #ffffff; }')
    return document


def write_pdf(report, path):
    writer = QPdfWriter(str(path))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setResolution(600)
    document = _print_document()
    document.setHtml(report.html())
    # QTextDocument prints paginated real tables; figures get their own pages so
    # long reports cannot overwrite a figure or split its caption.
    from PyQt6.QtCore import QSizeF
    scale = writer.resolution() / 96
    page = writer.pageLayout().paintRectPixels(writer.resolution())
    width, height = page.width() / scale, page.height() / scale
    document.setPageSize(QSizeF(width, height))
    painter = QPainter(writer)
    _print_pdf_pages(document, writer, painter, width, height, scale)
    for number, figure in enumerate(report.figures, 1):
        title = figure.title
        path_ = figure.display_image or figure.value
        writer.newPage()
        source, ratio = figure_source(path_)
        mm = _figure_width(figure, ratio)
        w = mm / 25.4 * writer.resolution()
        h = w / ratio
        caption = _print_document()
        caption.setTextWidth(width)
        note = ''.join('<br><span>' + escape(line) + '</span>' for line in figure.paragraphs)
        caption.setHtml(f'<b>Figure {number}. {escape(title)} (continued)</b>' + note)
        # Lay out captions in the same 96-DPI coordinates as table captions.
        available = page.height() - (caption.size().height() + 12) * scale
        import math
        for part in range(math.ceil(h / available)):
            if part:
                writer.newPage()
            painter.save()
            painter.setClipRect(QRectF(0, 0, page.width(), available))
            rect = QRectF((page.width() - w) / 2, -part * available, w, h)
            page_source = source
            if isinstance(source, QSvgRenderer):
                # Qt's symbol viewport replaces the painter clip. Intersect the
                # SVG groups themselves with this page's slice to preserve it.
                bounds = source.viewBoxF()
                page_source, _ = figure_source(path_, (
                    bounds.x(), bounds.y() + part * available * bounds.height() / h,
                    bounds.width(), min(available, h - part * available) * bounds.height() / h,
                ))
            paint_figure(painter, page_source, rect)
            painter.restore()
            painter.save()
            painter.scale(scale, scale)
            caption_y = min(h - part * available, available) / scale + 12
            caption.setHtml(f'<b>Figure {number}. {escape(title)}'
                            + (' (continued)</b>' if part else '</b>' + note))
            painter.translate(0, caption_y)
            caption.drawContents(painter)
            painter.restore()
    if report.configuration or report.supplementary_sections:
        document.setHtml(report.html(supplementary=True))
        _print_pdf_pages(document, writer, painter, width, height, scale, first_page=True)
    painter.end()


def _figure_width(figure: ResultSection, ratio: float) -> int:
    return 180 if ratio > 1.4 or figure.plot_kind in {
        "forest", "cumulative_forest", "leave_one_out_forest", "subgroup_forest",
    } else 85


def _table_roles(table):
    return {quantity.role for row in table.quantities for cell in row for quantity in cell}


def _pooled_standard_error(combined, combined_qs, metric):
    se_header = next((h for h, qs in combined_qs.items() if any(q.role == 'se' for q in qs)), None)
    if se_header is None:
        return ('—', ()), '—'
    scale = next(q.scale for q in combined_qs[se_header] if q.role == 'se')
    labels = {'display': 'standardized' if metric == 'SMD' else 'outcome', 'freeman-tukey': 'Freeman-Tukey'}
    return (combined[se_header], combined_qs[se_header]), labels.get(scale, scale) or '—'


def _pooled_effect_label(values, table, vertical, effect_metric, coefficient, multiple_metrics):
    context = table.title if vertical else table.metric_label or effect_metric
    effect = values.get('Term', values.get('Covariate', values.get('Subgroups', values.get('Level', context))))
    if not coefficient and multiple_metrics and effect.casefold() != effect_metric.casefold():
        effect = (effect_metric[:1].upper() + effect_metric[1:]) + ': ' + effect
    return effect


def _prediction_notes(text_sections):
    prediction_notes = {}
    for section in text_sections:
        for note in section.prediction_notes:
            prediction_notes.setdefault(note, []).append(section.title)
    notes = tuple((' / '.join(dict.fromkeys(titles)) + ': ' + note) if len(prediction_notes) > 1 else note
                  for note, titles in prediction_notes.items())
    return notes


def _heterogeneity_fit_rows(values, quantities, fit):
    labels = {'Q': 'Cochran’s Q', 'df': 'Heterogeneity degrees of freedom', 'p-value': 'Heterogeneity P', 'I²': 'I²', 'τ²': 'Between-study variance, τ²'}
    for h, label in labels.items():
        if h not in values:
            continue
        qs = quantities.get(h, ())
        if h == 'τ²' and qs and qs[0].scale not in ('', 'display'):
            label += f' (squared {qs[0].scale} scale)'
        label += ' (' + values['Subgroups'] + ')' if 'Subgroups' in values else ''
        fit.append(((label, ()), (p_value(values[h], qs) if h == 'p-value' else values[h], qs)))


def _residual_heterogeneity_sentence(values, quantities, residual):
    combined = {**values, **(residual or {})}
    return ' '.join(_heterogeneity_sentence(combined, quantities, heading='Residual heterogeneity'))


def _docx_column_widths(table, available):
    lengths = [max(len(line) for row in (table.headers, *table.rows)
                   for line in (row[column].splitlines() or [''])) for column in range(len(table.headers))]
    weights = [max(5, min(45, length)) for length in lengths]
    minimums = [Pt(12 + 6 * max((len(row[column]) for row in table.rows
                                if numeric_cell(row[column])), default=0))
                for column in range(len(table.headers))]
    remaining = max(0, available - sum(minimums))
    return [round(minimum + remaining * weight / sum(weights))
            for minimum, weight in zip(minimums, weights)]


def _style_docx_cell(cell, value, width, numeric, heading):
    from docx.oxml import OxmlElement
    is_numeric = not heading and numeric_cell(value)
    cell.text = report_numbers(value) if is_numeric else value
    cell.width = width
    if is_numeric or (numeric and not heading):
        cell._tc.get_or_add_tcPr().append(OxmlElement('w:noWrap'))
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    for paragraph in cell.paragraphs:
        paragraph.paragraph_format.space_before = Pt(2)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.line_spacing = 1
        right = numeric if heading else is_numeric or (value in ('', 'NA', '—', 'Not estimable') and numeric)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT if right else WD_ALIGN_PARAGRAPH.LEFT
        if heading:
            paragraph.paragraph_format.keep_with_next = True
        for run in paragraph.runs:
            run.font.size = Pt(10)
            run.bold = heading


def _print_pdf_pages(document, writer, painter, width, height, scale, first_page=False):
    from PyQt6.QtGui import QAbstractTextDocumentLayout
    _keep_pdf_tables_together(document, height)
    for number in range(document.pageCount()):
        if number or first_page:
            writer.newPage()
        painter.save()
        painter.scale(scale, scale)
        painter.setClipRect(QRectF(0, 0, width, height))
        painter.translate(0, -number * height)
        context = QAbstractTextDocumentLayout.PaintContext()
        context.clip = QRectF(0, number * height, width, height)
        required(document.documentLayout(), "report document layout").draw(painter, context)
        painter.restore()


def _keep_pdf_tables_together(document, page_height):
    from PyQt6.QtGui import QTextCursor, QTextFormat, QTextTable

    layout = required(document.documentLayout(), "report document layout")
    for table in required(document.rootFrame(), "report root frame").childFrames():
        if not isinstance(table, QTextTable):
            continue
        cursor = QTextCursor(document)
        cursor.setPosition(table.firstPosition() - 1)
        caption = layout.blockBoundingRect(cursor.block())
        bottom = layout.frameBoundingRect(table).bottom()
        formatting = cursor.blockFormat()
        margin = 2 * document.documentMargin() + formatting.topMargin()
        # Keep a short table and its caption intact; longer tables retain Qt's
        # pagination and repeated headers.
        if (bottom - caption.top() < page_height - margin
                and int(caption.top() / page_height) != int((bottom - 1) / page_height)):
            formatting.setPageBreakPolicy(QTextFormat.PageBreakFlag.PageBreak_AlwaysBefore)
            cursor.setBlockFormat(formatting)


def _multiple_metrics(result):
    return len({t.metric for s in result.sections for t in s.tables if t.metric}) > 1
