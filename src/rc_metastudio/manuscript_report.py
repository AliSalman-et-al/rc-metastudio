"""Manuscript content taken exclusively from an executed result."""
from rc_metastudio.qt_object_guard import required
from dataclasses import dataclass, replace
import re
from rc_metastudio.analysis_results import ResultTable
from rc_metastudio.svg_rendering import svg_bytes_for_qt
from rc_metastudio.result_formatting import numeric_columns, table_html
from html import escape
import io
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QFont, QImage, QPainter, QPdfWriter, QTextDocument, QPageSize
from PyQt6.QtSvg import QSvgRenderer
from docx import Document
from docx.shared import Mm, RGBColor
from rc_metastudio import __version__


def binary_correction_prose(method, adjust, label, double_zero):
    if method in ("binary.fixed.mh", "binary.fixed.peto"):
        estimator = "Mantel-Haenszel" if method.endswith("mh") else "Peto"
        return f"A continuity correction of {adjust} was applied to individual study estimates only; the pooled {estimator} estimate uses the original counts."
    text = f"A continuity correction of {adjust} was applied to {label}."
    if method in ("binary.random", "binary.fixed.inv.var") and double_zero:
        text += f" {double_zero} studies with no events in either arm were retained with this correction."
    return text


def methods_prose(metric, model, parameters, confidence, workflow, details, fits):
    from rc_metastudio.analysis_method_labels import parameter_value_display_label
    plural = {"odds ratio": "Odds ratios", "risk ratio": "Risk ratios", "hazard ratio": "Hazard ratios",
              "mean difference": "Mean differences", "standardized mean difference": "Standardized mean differences"}.get(metric, metric.capitalize() + " estimates")
    sentence = f"{plural} were pooled using a {model} model"
    estimator = parameters.get('rm.method', parameters.get('estimator'))
    if estimator and model == 'random-effects':
        label = parameter_value_display_label('rm.method', estimator).replace('DerSimonian-Laird', 'DerSimonian–Laird')
        sentence += f" with the {label} estimator of between-study variance"
    parts = [sentence + '.']
    if any('reitsma' in method.lower() for _, method, _ in fits):
        parts = []
        for label, method, fit_parameters in fits:
            if 'reitsma' in method.lower():
                continue
            text = f'{label.capitalize()} estimates were pooled using the {method} method'
            estimator = fit_parameters.get('rm.method')
            if estimator and 'random' in method.lower():
                name = parameter_value_display_label('rm.method', estimator).replace('DerSimonian-Laird', 'DerSimonian–Laird')
                text += f' with the {name} estimator of between-study variance'
            parts.append(text + '.')
    inference = parameters.get('inference.method')
    if inference in ('z', 'normal'):
        parts.append(f"Confidence intervals ({float(confidence):g}%) used the normal approximation.")
    elif inference:
        parts.append(f"Confidence intervals ({float(confidence):g}%) used {parameter_value_display_label('inference.method', inference)}.")
    parts.extend(_workflow_prose(workflow, parameters, details))
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

def _p_clause(value):
    return "P " + (value if value.startswith(("<", ">")) else "= " + value)


def _row(table, index):
    numbers = table.quantities[index] if table.quantities else ((),) * len(table.headers)
    values, quantities = dict(zip(table.headers, table.rows[index])), dict(zip(table.headers, numbers))
    labels = {'estimate': 'Estimate', 'q': 'Q', 'df': 'df', 'p': 'p-value', 'i2': 'I²', 'tau2': 'τ²', 'k': 'k'}
    for header, qs in zip(table.headers, numbers):
        for q in qs:
            label = labels.get(q.role)
            if q.role == 'se':
                label = header if header.startswith('SE') else 'SE'
            elif q.role == 'statistic':
                label = 't' if header in ('t', 't-value') else 'Z'
            if label:
                values[label], quantities[label] = values[header], qs
    return values, quantities


def _cells(table, index):
    numbers = table.quantities[index] if table.quantities else ((),) * len(table.headers)
    return list(zip(table.rows[index], numbers))


def _table(title, headers, rows):
    return ResultTable(title, tuple(headers), tuple(tuple(text for text, qs in row) for row in rows),
                       tuple(tuple(qs for text, qs in row) for row in rows) if any(qs for row in rows for text, qs in row) else ())


def _interval_fields(table):
    fields = {q.role: (header, q) for row in table.quantities for header, qs in zip(table.headers, row) for q in qs}
    kind = 'pi' if 'pi_lower' in fields else 'ci'
    lower, upper = fields.get(kind+'_lower'), fields.get(kind+'_upper')
    if not lower or not upper:
        return None, None, ''
    return lower[0], upper[0], f'{lower[1].level:g}% {kind.upper()}'

def _heterogeneity_sentence(values, quantities, prefix=""):
    parts = []
    if "Q" in values:
        test = f"Q = {values['Q']}"
        if "df" in values:
            test += f", df = {values['df']}"
        if "p-value" in values:
            test += ", " + _p_clause(p_value(values['p-value'], quantities.get('p-value', ())))
        parts.append(prefix + "Heterogeneity: " + test + ".")
    if values.get('I²') and values['I²'] not in ("NA", "NaN"):
        parts.append(prefix + f"I² = {values['I²']}.")
    if 'τ²' in values:
        parts.append(prefix + f"Between-study variance was τ² = {values['τ²']}.")
    return parts

def _study_inputs(result):
    for section in result.sections:
        for table in section.tables:
            if table.title == 'Study weights':
                yield section, table


def _study_result_rows(result):
    rows = []
    for section, table in _study_inputs(result):
        analysis = section.title.removesuffix(' summary')
        if section.source_key == 'Weights':
            analysis = result.manuscript_metric or section.title
        for i, row in enumerate(table.rows):
            cells = _cells(table, i)
            values = (cells[0], cells[1], (row[2] + ' to ' + row[3], cells[2][1]+cells[3][1]), cells[4]) if len(row) == 5 else (cells[0], ('—', ()), ('—', ()), cells[1])
            rows.append(((analysis, ()), *values))
    return rows

def _study_results(result, template, level):
    rows = _study_result_rows(result)
    row_label = 'Fit' if any('leave-one-out' in s.title.casefold() for s in result.sections) else 'Study'
    headers = ('Analysis', row_label, 'Effect', level, 'Weight')
    if rows and all(row[2][0] == row[3][0] == '—' for row in rows):
        headers = ('Analysis', row_label, 'Weight')
        rows = [(row[0], row[1], row[4]) for row in rows]
    if len({row[0] for row in rows}) == 1:
        headers = headers[1:]
        rows = [row[1:] for row in rows]
    paragraphs = () if rows else ('No study-level estimates or weights are available for this workflow.',)
    return replace(template, title='Study results', paragraphs=paragraphs,
                   tables=(_table('Study results', headers, rows),) if rows else ())


def _held_section_content(section):
    tables = tuple(replace(table, title=table.title if section.title == table.title else section.title + ' — ' + table.title) for table in section.tables)
    paragraphs = section.paragraphs
    if section.source_key == 'References':
        tables = ()
        paragraphs = tuple(f"{number}. {line}" if not re.match(r"^\d+[.)]\s", line) else line
                           for number, line in enumerate(filter(None, section.value.splitlines()), 1))
    elif not tables and section.value:
        tables = (ResultTable(section.title, ('',),
                              tuple((line,) for line in section.value.splitlines())),)
    return tables, paragraphs


def _held_sections(result):
    sections = []
    for section in result.sections:
        if section.kind != 'text':
            continue
        tables, paragraphs = _held_section_content(section)
        sections.append(replace(section, title='Supplementary details', value='',
                                paragraphs=tuple(note for note in paragraphs if 'prediction' not in note.casefold()), tables=tables))
    return sections


def _prediction_rows(table, lower, upper, ci_level, vertical, fit, summary, analysis_context=''):
    for index in range(len(table.rows)):
        values, quantities = _row(table, index)
        context = values.get('Subgroups', table.title if vertical else analysis_context)
        interval = values[lower] + ' to ' + values[upper]
        fit.append(((ci_level.replace(' PI', '') + ' prediction interval' + (' (' + context + ')' if context else ''), ()),
                    (interval, quantities[lower]+quantities[upper])))
        summary.append((context + ': ' if context else '') + f"The {ci_level.replace(' PI', '')} prediction interval was {interval}.")

def _pooled_statistics(values, quantities, overall, calculation):
    overall_values, overall_qs = overall
    calc_values, calc_qs = calculation
    combined, combined_qs = {**calc_values, **overall_values, **values}, {**calc_qs, **overall_qs, **quantities}
    stat = next((key for key in ('t', 'Z') if key in combined), None)
    statistic = 't' if stat == 't' else 'z'
    df, method = combined.get('df'), ''
    if statistic == 't' and df:
        statistic += f' (df = {df})'
        method = f'The overall effect was tested using t with {df} degrees of freedom.'
    se_header = next((h for h, qs in combined_qs.items() if any(q.role == 'se' for q in qs)), None)
    se = (combined[se_header], combined_qs[se_header]) if se_header else ('—', ())
    se_scale = se_header.removeprefix('SE').strip() or '—' if se_header else '—'
    if se_header and se_scale == '—':
        scale = next(q.scale for q in combined_qs[se_header] if q.role == 'se')
        se_scale = f'({scale if scale != "display" else "outcome"} scale)' if scale else '—'
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
    inference = '' if within_subgroup else (f", {statistic} = {test}" if test != '—' else '') + (', ' + _p_clause(p) if p != '—' else '')
    summary.append(f"{lead} was {values['Estimate']} ({level} [{values[lower]}, {values[upper]}]{inference}).")


def _effect_metric(metric, section, table, vertical, coefficient):
    if vertical:
        metric = table.title.lower()
    elif ',' in metric:
        metric = section.title.removesuffix(' summary').lower()
    if not coefficient and metric.endswith('transformed proportion'):
        return 'proportion'
    return metric


def _pooled_rows(result, section, table, lower, upper, ci_level, vertical, overall, calculation, pooled, fit, summary, methods):
    metric = result.manuscript_metric or "effect"
    statistic, level = "z", ci_level
    coefficient = table.title == 'Regression coefficients' or table.title.startswith('Coefficient estimates')
    for index in range(len(table.rows)):
        values, quantities = _row(table, index)
        if not values.get('Estimate'):
            continue
        if 'k' in values and 'Subgroups' in values:
            fit.append((('Studies (k) (' + values['Subgroups'] + ')', ()), (values['k'], quantities.get('k', ()))))
        effect_metric = _effect_metric(metric, section, table, vertical, coefficient)
        context = next((values[h] for h in table.headers if h.startswith(('Study added', 'Study omitted'))), table.title if vertical else effect_metric)
        effect = values.get('Term', values.get('Covariate', values.get('Subgroups', values.get('Level', context))))
        if not coefficient and ',' in metric and effect.casefold() != effect_metric.casefold():
            effect = effect_metric.capitalize() + ': ' + effect
        statistic, se, se_scale, test, p, method = _pooled_statistics(values, quantities, overall, calculation)
        if not coefficient and not vertical and values.get("Subgroups", "Overall").casefold() == "overall":
            methods.append(method)
        pooled.append(((effect[:1].upper() + effect[1:], ()), (values['Estimate'], quantities['Estimate']),
                       (values[lower] + ' to ' + values[upper], quantities[lower]+quantities[upper]), se, (se_scale, ()), test, p))
        _pooled_prose(result, values, effect, effect_metric, coefficient, statistic, test[0], p[0], level, lower, upper, summary)
    return level, statistic

def _heterogeneity_rows(table, fit, summary, residual=None):
    for index in range(len(table.rows)):
        values, quantities = _row(table, index)
        prefix = values.get('Subgroups', '')
        prefix = prefix + ': ' if prefix else 'Residual ' if table.title == 'Residual heterogeneity' else ''
        if table.title == 'Residual heterogeneity':
            combined = {**values, **(residual or {})}
            summary.append("Residual heterogeneity: " + ", ".join(
                _p_clause(p_value(combined[h], quantities.get(h, ()))) if h == 'p-value' else f"{h} = {combined[h]}"
                for h in ('Q', 'df', 'p-value', 'τ²', 'I²') if h in combined) + ".")
        else:
            summary.extend(_heterogeneity_sentence(values, quantities, prefix))
        labels = {'Q': 'Cochran’s Q', 'df': 'Heterogeneity degrees of freedom', 'p-value': 'Heterogeneity p', 'I²': 'I²', 'τ²': 'Between-study variance (τ²)'}
        for h, label in labels.items():
            if h not in values:
                continue
            qs = quantities.get(h, ())
            if h == 'τ²' and qs and qs[0].scale not in ('', 'display'):
                label += f' (squared {qs[0].scale} scale)'
            label += ' (' + values['Subgroups'] + ')' if 'Subgroups' in values else ''
            fit.append(((label, ()), (p_value(values[h], qs) if h == 'p-value' else values[h], qs)))

def _fit_table(table, fit, summary):
    if table.title == 'Test of subgroup differences' and table.rows:
        values, numbers = _row(table, 0)
        test = 'F' if '(F)' in values['Test'] else 'Q'
        summary.append(f"Test for subgroup differences: {test} = {values['Statistic']}, df = {values['df']}, {_p_clause(p_value(values['p-value'], numbers.get('p-value', ())))}.")
        fit.extend(((label, ()), (p_value(values[key], numbers.get(key, ())) if key == 'p-value' else values[key], numbers.get(key, ())))
                   for key, label in (("Test", "Between-group test"), ("Statistic", "Between-group statistic"), ("df", "Between-group degrees of freedom"), ("p-value", "Between-group p")))
        return True
    return _model_fit_table(table, fit, summary)

def _model_fit_table(table, fit, summary):
    if table.title in ('Model overview', 'Residual model fit') and table.headers == ('Statistic', 'Value'):
        fit.extend(_cells(table, index) for index in range(len(table.rows)))
        return True
    if table.title == 'Model tests':
        for index in range(len(table.rows)):
            values, numbers = _row(table, index)
            name = values['Test']
            fit.extend(((label + ' (' + name + ')', ()), (p_value(values[key], numbers.get(key, ())) if key == 'p-value' else values[key], numbers.get(key, ())))
                       for key, label in (('Statistic', 'Test statistic'), ('df', 'Test degrees of freedom'), ('p-value', 'Test p')))
        return True
    if table.title == 'Model specification':
        return True
    if table.rows and any(q.role == 'statistic' for row in table.quantities for cell in row for q in cell) and not any(q.role == 'estimate' for row in table.quantities for cell in row for q in cell):
        return True
    return False

def _horizontal_table(table):
    vertical = table.headers == ('Statistic', 'Value') and any(q.role == 'estimate' for row in table.quantities for cell in row for q in cell)
    if vertical:
        table = _table(table.title, [row[0] for row in table.rows], [[_cells(table, i)[1] for i in range(len(table.rows))]])
    return table, vertical

def _residual_statistics(section):
    held = dict(row for source in section.tables if source.headers == ('Statistic', 'Value') for row in source.rows)
    return {key: held[label] for key, label in
            (('df', 'Residual degrees of freedom'), ('I²', 'Residual I²')) if label in held}


def _report_table(result, section, table, summary, pooled, fit, level, statistic, overall, calculation, methods):
    table, vertical = _horizontal_table(table)
    if table.title.startswith('Calculation scale'):
        return level, statistic
    if section.source_key == 'Weights' or table.title == 'Study weights':
        return level, statistic
    lower, upper, ci_level = _interval_fields(table)
    if lower and upper and ci_level.endswith(' PI'):
        context = section.title.removesuffix(' summary') if ',' in result.manuscript_metric else ''
        _prediction_rows(table, lower, upper, ci_level, vertical, fit, summary, context)
        return level, statistic
    if lower and upper and ci_level.endswith(' CI') and any(q.role == 'estimate' for row in table.quantities for cell in row for q in cell):
        level, statistic = _pooled_rows(result, section, table, lower, upper, ci_level, vertical, overall, calculation, pooled, fit, summary, methods)
        return level, statistic
    if any(q.role == 'q' for row in table.quantities for cell in row for q in cell):
        start = len(fit)
        _heterogeneity_rows(table, fit, summary, _residual_statistics(section))
        if ',' in result.manuscript_metric:
            fit[start:] = [((label[0] + ' (' + section.title.removesuffix(' summary') + ')', label[1]), value) for label, value in fit[start:]]
        return level, statistic
    _fit_table(table, fit, summary)
    return level, statistic


def _section_statistics(section):
    overall = next((_row(t, 0) for t in section.tables if t.title != 'Test of subgroup differences' and len(t.rows) == 1 and
                    any(q.role == 'statistic' for row in t.quantities for cell in row for q in cell) and
                    not any(q.role == 'estimate' for row in t.quantities for cell in row for q in cell)), ({}, {}))
    calculation = next((_row(t, 0) for t in section.tables if t.title.startswith('Calculation scale') and t.rows), ({}, {}))
    return overall, calculation

def _report_sections(result, summary, methods):
    text_sections = [section for section in result.sections if section.kind == 'text']
    if not text_sections:
        return [], []
    pooled, fit = [], [((label, ()), (value, ())) for label, value in result.manuscript_model_info]
    level, statistic = '95% CI', 'z'
    for section in text_sections:
        for table in section.tables:
            if table.title == 'Test of subgroup differences':
                _fit_table(table, fit, summary)
    for section in result.sections:
        if section.kind != 'text':
            continue
        overall, calculation = _section_statistics(section)
        for table in section.tables:
            if table.title == 'Test of subgroup differences':
                continue
            level, statistic = _report_table(result, section, table, summary, pooled, fit, level, statistic, overall, calculation, methods)
    return _primary_sections(result, text_sections, pooled, fit, level, statistic), _held_sections(result)


def _primary_sections(result, text_sections, pooled, fit, level, statistic):
    template = text_sections[0]
    primary_title = 'Diagnostic summary' if result.analysis_method == 'diagnostic.reitsma' else 'Pooled effect'
    prediction_notes = {}
    for section in text_sections:
        for note in section.paragraphs:
            if 'prediction' in note.casefold():
                prediction_notes.setdefault(note, []).append(section.title)
    notes = tuple((' / '.join(dict.fromkeys(titles)) + ': ' + note) if len(prediction_notes) > 1 else note
                  for note, titles in prediction_notes.items())
    sections = [replace(template, title=primary_title, paragraphs=(() if pooled else
                         ('No structured pooled estimates are available for this workflow; the complete output is in Supplementary details.',)),
                        tables=(_table(primary_title, ('Effect', 'Estimate', level, 'SE', 'SE scale', statistic, 'p'), pooled),)),
                replace(template, title='Model fit', paragraphs=notes,
                        tables=(_table('Model fit', ('Statistic', 'Value'), fit),)),
                _study_results(result, template, level)]
    if not any(section.tables for section in text_sections):
        comparisons = [s for s in text_sections if s.title in ('Pooled comparison', 'Extrapolation') or s.title.startswith('Trim-and-fill')]
        sections[0] = replace(template, title='Pooled effect', paragraphs=('Model comparisons and sensitivity analyses.',),
                              tables=(ResultTable('Pooled effect', ('Analysis', 'Output'), tuple((s.title, s.value) for s in comparisons)),))
        sections[1] = replace(template, title='Model fit', paragraphs=sections[1].paragraphs,
                              tables=(ResultTable('Model fit', ('Statistic', 'Value'), tuple((s.title, s.value) for s in text_sections if s.title in ('Data and eligibility', 'Tests'))),))
    return [replace(section, tables=tuple(_available_columns(table) for table in section.tables if table.rows)) for section in sections]


def _available_columns(table):
    indexes = [i for i in range(len(table.headers)) if any(row[i] not in ('', '—', 'NA') for row in table.rows)]
    return replace(table, headers=tuple(table.headers[i] for i in indexes),
                   rows=tuple(tuple(row[i] for i in indexes) for row in table.rows),
                   quantities=tuple(tuple(row[i] for i in indexes) for row in table.quantities))


def _report_methods(result, pooled_methods):
    methods = " ".join(filter(None, (result.manuscript_methods, *dict.fromkeys(pooled_methods))))
    if any(q.role == 'q' for s in result.sections for t in s.tables for row in t.quantities for cell in row for q in cell):
        methods += " Heterogeneity" + (" for the separate univariate fits" if 'Reitsma' in methods else '') + " was assessed with Cochran's Q and I²."
    methods += f' Analyses were performed in RC MetaStudio {__version__}.'
    packages = ', '.join(p.strip() for p in result.software.split(',') if not p.strip().startswith('RCMetaR'))
    if packages:
        methods += ' R packages loaded for this analysis: ' + packages + '.'
    return methods


def _table_html(table, table_number):
    return f'<p style="page-break-after:avoid;"><b>Table {table_number}. {escape(table.title)}</b></p>' + table_html(table.headers, table.rows)


@dataclass(frozen=True)
class ManuscriptReport:
    title: str
    methods: str
    sections: tuple
    figures: tuple
    summary: tuple[str, ...]
    comparison: str = ''

    @property
    def results(self):
        return ' '.join(self.summary)

    @classmethod
    def from_result(cls, result):
        from dataclasses import replace
        from rc_metastudio.analysis_results import ResultTable
        summary = [result.manuscript_context] if result.manuscript_context else []
        pooled_methods = []
        sections, supplementary = _report_sections(result, summary, pooled_methods)
        methods = _report_methods(result, pooled_methods)
        details = tuple(line for line in result.details.splitlines()
                        if line.startswith(('Order:', 'Each row', 'Subgroups by', 'Moderators:', 'Omission-only fits:')))
        if details:
            supplementary.append(replace(next(s for s in result.sections if s.kind == 'text'),
                                         title='Supplementary details', paragraphs=details, tables=(), value=''))
        figures = tuple((s.title, result.display_images.get(s.source_key, s.value)) for s in result.sections if s.kind == 'image')
        return cls(result.manuscript_title or 'Meta-analysis', methods, tuple(sections + supplementary), figures, tuple(summary), result.manuscript_comparison)

    def plain_text(self):
        parts = [self.title, self.comparison]
        for heading, text in (('Methods', self.methods), ('Results', self.results)):
            if text.strip():
                parts.extend((heading, text))
        number = 0
        for section in self.sections:
            if section.source_key == "References":
                parts.append("References")
            for table in section.tables:
                number += 1
                parts.append(f'Table {number}. {table.title}')
                parts.extend(('\t'.join(table.headers), *('\t'.join(row) for row in table.rows)))
            parts.extend(section.paragraphs)
        return '\n\n'.join(parts)

    def html(self, supplementary=False):
        parts = [f'<h1>{escape(self.title)}</h1><p>{escape(self.comparison)}</p>']
        for heading, text in (('Methods', self.methods), ('Results', self.results)):
            if text.strip():
                parts.append(f'<h2>{heading}</h2><p>{escape(text)}</p>')
        if supplementary:
            parts = []
        return ''.join(parts) + self.tables_html(supplementary)

    def tables_html(self, supplementary=False):
        parts = []
        table_number = sum(len(section.tables) for section in self.sections
                           if section.title != "Supplementary details") if supplementary else 0
        for number, section in enumerate(self.sections, 1):
            if (section.title == "Supplementary details") != supplementary:
                continue
            if section.title == 'Supplementary details' and (number == 1 or self.sections[number-2].title != section.title):
                parts.append('<h2>Supplementary details</h2>')
            if section.source_key == 'References':
                parts.append('<h2>References</h2>')
            for table in section.tables:
                table_number += 1
                parts.append(_table_html(table, table_number))
            parts.extend(f'<p>{escape(paragraph)}</p>' for paragraph in section.paragraphs)
        return ''.join(parts)


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


def _workflow_prose(workflow, parameters, details):
    parts = []
    if workflow == 'subgroup':
        parts.append(f"Subgroup analyses were performed by {parameters.get('cov_name', 'the selected covariate')}.")
        parts.append("Subgroup differences were tested using heterogeneity Q among the subgroup estimates, weighted by their inverse variances.")
    elif workflow == 'meta-regression':
        moderators = next((line.removeprefix('Moderators: ') for line in details.splitlines() if line.startswith('Moderators: ')), '')
        if moderators:
            parts.append(f"Meta-regression was performed with {moderators} as moderators.")
    elif workflow == 'cumulative':
        parts.append('Cumulative meta-analysis was performed in current study order.')
    elif workflow == 'leave-one-out':
        parts.append('Leave-one-out analyses were performed by omitting each study in turn.')
    return parts


def _docx_table(document, table):
    target = document.add_table(rows=1, cols=len(table.headers))
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
            cell.text = value
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT if numeric[column] else WD_ALIGN_PARAGRAPH.LEFT
                for run in paragraph.runs:
                    from docx.shared import Pt
                    run.font.size = Pt(10)
                    run.bold = index == 0


def _docx_sections(document, report, supplementary, table_number):
    for number, section in enumerate(report.sections, 1):
        if (section.title == "Supplementary details") != supplementary:
            continue
        if section.title == 'Supplementary details' and (number == 1 or report.sections[number-2].title != section.title):
            document.add_heading('Supplementary details', 1)
        if section.source_key == 'References':
            document.add_heading('References', 1)
        for table in section.tables:
            table_number += 1
            caption = document.add_paragraph(f'Table {table_number}. {table.title}', style='Caption')
            caption.paragraph_format.keep_with_next = True
            _docx_table(document, table)
            document.add_paragraph()
        for paragraph in section.paragraphs:
            document.add_paragraph(paragraph)
    return table_number


def write_docx(report, path):
    document = Document()
    from docx.shared import Pt
    document.styles['Normal'].font.size = Pt(11)
    for name in ('Normal', 'Title', 'Heading 1', 'Caption'):
        document.styles[name].font.color.rgb = RGBColor(0, 0, 0)
    section = document.sections[0]
    section.page_width = Mm(210)
    section.left_margin = section.right_margin = Mm(15)
    document.add_heading(report.title, 0)
    document.add_paragraph(report.comparison)
    for heading, text in (('Methods', report.methods), ('Results', report.results)):
        if text.strip():
            document.add_heading(heading, 1)
            document.add_paragraph(text)
    table_number = 0
    table_number = _docx_sections(document, report, False, table_number)
    from PyQt6.QtCore import QBuffer, QIODevice
    for number, (title, path_) in enumerate(report.figures, 1):
        source, ratio = figure_source(path_)
        width = 180 if ratio > 1.4 or 'forest' in title.lower() else 85
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
            document.add_paragraph(f'Figure {number}. {title}' + (' (continued)' if top else ''))
    _docx_sections(document, report, True, table_number)
    document.save(path)


def _print_document():
    document = QTextDocument()
    document.setDefaultFont(QFont('Arial', 11))
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
    from PyQt6.QtGui import QAbstractTextDocumentLayout
    scale = writer.resolution() / 96
    page = writer.pageLayout().paintRectPixels(writer.resolution())
    width, height = page.width() / scale, page.height() / scale
    document.setPageSize(QSizeF(width, height))
    painter = QPainter(writer)
    def print_pages(first_page=False):
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
    print_pages()
    for number, (title, path_) in enumerate(report.figures, 1):
        writer.newPage()
        source, ratio = figure_source(path_)
        mm = 180 if ratio > 1.4 or 'forest' in title.lower() else 85
        w = mm / 25.4 * writer.resolution()
        h = w / ratio
        caption = _print_document()
        caption.setTextWidth(width)
        caption.setHtml(f'<b>Figure {number}. {escape(title)} (continued)</b>')
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
            caption.setHtml(f'<b>Figure {number}. {escape(title)}' + (' (continued)' if part else '') + '</b>')
            painter.translate(0, caption_y)
            caption.drawContents(painter)
            painter.restore()
    if any(section.title == 'Supplementary details' for section in report.sections):
        document.setHtml(report.html(supplementary=True))
        print_pages(first_page=True)
    painter.end()
