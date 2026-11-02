"""Manuscript content taken exclusively from an executed result."""
from rc_metastudio.runtime_types import required
from dataclasses import dataclass, replace
from decimal import Decimal
from rc_metastudio.analysis_results import ResultTable
from html import escape
import io
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QImage, QPainter, QPdfWriter, QTextDocument, QPageSize
from PyQt6.QtSvg import QSvgRenderer
from docx import Document
from docx.shared import Mm
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


def p_value(value):
    """Presentation only: the producer's held p-value or bound is authoritative."""
    if not value or value in ("NA", "—"):
        return "—"
    if value.strip().startswith("<"):
        bound = Decimal(value.strip().removeprefix("<").strip())
        return "< .001" if bound <= Decimal('.001') else "< " + f"{bound:.3f}".removeprefix("0")
    number = Decimal(value)
    if not number.is_finite():
        return f"{float(value):.3f}"
    if number < Decimal('.001'):
        return "< .001"
    return f"{number:.3f}".removeprefix("0")


def _p_clause(value):
    return "p " + (value if value.startswith("<") else "= " + value)


def _interval_fields(headers):
    lower = next((h for h in headers if h.startswith("Lower bound")), None)
    upper = next((h for h in headers if h.startswith("Upper bound")), None)
    level = lower.partition("(")[2].removesuffix(")").strip() if lower else "95% CI"
    return lower, upper, level or "95% CI"


def _interval_meaning(lower, upper, metric, arms, *, coefficient=False):
    if lower in (None, "", "NA") or upper in (None, "", "NA"):
        return ""
    ratio = metric in ("odds ratio", "risk ratio", "hazard ratio", "incidence rate ratio") and not coefficient
    if not coefficient and not ratio and metric not in ("mean difference", "standardized mean difference", "risk difference"):
        return ""
    if not coefficient and len(arms) != 2:
        return ""
    null = 1 if ratio else 0
    lo, hi = float(lower), float(upper)
    if lo <= null <= hi:
        return _included_interval(null, arms, coefficient)
    if coefficient:
        return f"The confidence interval is entirely {'above' if lo > 0 else 'below'} 0."
    quantity = {
        "odds ratio": "odds of the outcome",
        "risk ratio": "risk",
        "risk difference": "risk",
        "mean difference": "mean values",
        "standardized mean difference": "mean values",
        "hazard ratio": "hazard",
        "incidence rate ratio": "event rate",
    }[metric]
    direction = "lower" if hi < null else "higher"
    return f"The confidence interval excludes {null}, with {direction} {quantity} in {arms[0]} than in {arms[1]}."


def _included_interval(null, arms, coefficient):
    comparison = f" between {arms[0]} and {arms[1]}" if len(arms) == 2 and not coefficient else " from zero" if coefficient else ""
    return f"The confidence interval includes {null}, so these data do not show a clear difference{comparison}."


def _heterogeneity_sentence(values, prefix=""):
    parts = []
    if "Q" in values:
        test = f"Q = {values['Q']}"
        if "df" in values:
            test += f", df = {values['df']}"
        if "p-value" in values:
            test += ", " + _p_clause(p_value(values['p-value']))
        parts.append(prefix + "Heterogeneity: " + test + ".")
    if values.get('I²') and values['I²'] not in ("NA", "NaN"):
        value = values['I²']
        number = float(value.rstrip('%'))
        descriptions = []
        if number <= 40:
            descriptions.append("heterogeneity that might not be important")
        for low, high, label in ((30, 60, "moderate"), (50, 90, "substantial"), (75, 100, "considerable")):
            if low <= number <= high:
                descriptions.append(label + " heterogeneity")
        parts.append(prefix + f"I² = {value}, which may represent " + " or ".join(descriptions) + " (Cochrane Handbook ranges).")
    if 'τ²' in values:
        parts.append(prefix + f"Between-study variance was τ² = {values['τ²']}.")
    return parts



def _study_inputs(result):
    for section in result.sections:
        for table in section.tables:
            if table.title == 'Study weights':
                yield section, table


def _study_results(result, template, level):
    rows = []
    for section, table in _study_inputs(result):
        analysis = section.title.removesuffix(' Summary')
        if section.source_key == 'Weights':
            analysis = result.manuscript_metric or section.title
        for row in table.rows:
            values = (row[0], row[1], row[2] + ' to ' + row[3], row[4]) if len(row) == 5 else (row[0], '—', '—', row[1])
            rows.append((analysis, *values))
    row_label = 'Fit' if any('leave-one-out' in s.title.casefold() for s in result.sections) else 'Study'
    headers = ('Analysis', row_label, 'Effect', level, 'Weight')
    if rows and all(row[2:4] == ('—', '—') for row in rows):
        headers = ('Analysis', row_label, 'Weight')
        rows = [(row[0], row[1], row[4]) for row in rows]
    paragraphs = () if rows else ('No study-level estimates or weights are held for this workflow.',)
    return replace(template, title='Study results', paragraphs=paragraphs,
                   tables=(ResultTable('Study results', headers, tuple(rows)),))


def _held_sections(result):
    sections = []
    for section in result.sections:
        if section.kind != 'text':
            continue
        tables = tuple(replace(table, title=table.title if section.title == table.title else section.title + ' — ' + table.title) for table in section.tables)
        if section.tables and section.paragraphs:
            tables += (ResultTable(section.title + ' — Held notes', ('Held note',),
                                   tuple((paragraph,) for paragraph in section.paragraphs)),)
        if not tables and section.value:
            tables = (ResultTable(section.title + ' — Held output', ('Held output',),
                                  tuple((line,) for line in section.value.splitlines())),)
        sections.append(replace(section, title='Supplementary details', value='', paragraphs=(), tables=tables))
    return sections


def _prediction_rows(table, lower, upper, ci_level, vertical, fit, summary):
    for row in table.rows:
        values = dict(zip(table.headers, row))
        context = values.get('Subgroups', table.title if vertical else '')
        interval = values[lower] + ' to ' + values[upper]
        fit.append((ci_level.replace(' PI', '') + ' prediction interval' + (' (' + context + ')' if context else ''), interval))
        summary.append((context + ': ' if context else '') + f"The {ci_level.replace(' PI', '')} prediction interval was {interval}.")



def _pooled_statistics(values, overall, calculation):
    stat = next((key for key in ('t', 'z', 'Z', 'z-value', 't-value') if key in values or key in overall), None)
    statistic = 't' if stat in ('t', 't-value') else 'z'
    se = next((v for h, v in {**calculation, **values}.items() if h.startswith('SE')), '—')
    test = values.get(stat, overall.get(stat, '—')) if stat else '—'
    p = p_value(values.get('p-value', overall.get('p-value', '')))
    return statistic, se, test, p


def _pooled_prose(result, values, effect, effect_metric, coefficient, statistic, test, p, level, lower, upper, summary):
    lead = f"For {effect}, the coefficient" if coefficient else f"For {effect}, the pooled {effect_metric}" if 'Subgroups' in values or 'Term' in values else f"The pooled {effect_metric}"
    inference = (f", {statistic} = {test}" if test != '—' else '') + (', ' + _p_clause(p) if p != '—' else '')
    summary.append(f"{lead} was {values['Estimate']} ({level} [{values[lower]}, {values[upper]}]{inference}).")
    meaning = _interval_meaning(values[lower], values[upper], effect_metric, result.manuscript_arms, coefficient=coefficient)
    if meaning:
        summary.append(meaning)


def _pooled_rows(result, section, table, lower, upper, ci_level, vertical, overall, calculation, pooled, fit, summary):
    metric = result.manuscript_metric or "effect"
    statistic = "z"
    level = ci_level
    coefficient = table.title == 'Regression coefficients'
    for row in table.rows:
        values = dict(zip(table.headers, row))
        if not values.get('Estimate'):
            continue
        if 'k' in values and 'Subgroups' in values:
            fit.append(('Studies (k) (' + values['Subgroups'] + ')', values['k']))
        effect_metric = table.title.lower() if vertical else section.title.removesuffix(' Summary').lower() if ',' in metric else metric
        if not coefficient and effect_metric.endswith('transformed proportion'):
            effect_metric = 'proportion'
        context = next((values[h] for h in table.headers if h.startswith(('Study added', 'Study omitted'))), table.title if vertical else effect_metric)
        effect = values.get('Term', values.get('Subgroups', context))
        statistic, se, test, p = _pooled_statistics(values, overall, calculation)
        pooled.append((effect, values['Estimate'], values[lower] + ' to ' + values[upper], se, test, p))
        _pooled_prose(result, values, effect, effect_metric, coefficient, statistic, test, p, level, lower, upper, summary)
    return level, statistic



def _heterogeneity_rows(table, fit, summary):
    for row in table.rows:
        values = dict(zip(table.headers, row))
        prefix = values.get('Subgroups', '')
        prefix = prefix + ': ' if prefix else 'Residual ' if table.title == 'Residual heterogeneity' else ''
        summary.extend(_heterogeneity_sentence(values, prefix))
        labels = {'Q': 'Cochran’s Q', 'df': 'Heterogeneity degrees of freedom', 'p-value': 'Heterogeneity p', 'I²': 'I²', 'τ²': 'Between-study variance (τ²)'}
        fit.extend((labels[h] + (' (' + values['Subgroups'] + ')' if 'Subgroups' in values else ''), p_value(v) if h == 'p-value' else v) for h, v in values.items() if h in labels)


def _fit_table(table, fit, summary):
    if table.title.endswith('Prediction interval') and len(table.rows) == 1:
        row = table.rows[0]
        pi_level = table.headers[0].partition('(')[2].removesuffix(')') or '95% PI'
        fit.append((pi_level.replace(' PI', '') + ' prediction interval', row[0] + ' to ' + row[1]))
        summary.append(f"The {pi_level.replace(' PI', '')} prediction interval was {row[0]} to {row[1]}.")
        return True
    if table.title == 'Test of subgroup differences' and table.rows:
        values = dict(zip(table.headers, table.rows[0]))
        summary.append(f"Between-group test: {values['Test']} = {values['Statistic']} (df = {values['df']}, {_p_clause(p_value(values['p-value']))}).")
        fit.extend((label, p_value(values[key]) if key == 'p-value' else values[key])
                   for key, label in (("Test", "Between-group test"), ("Statistic", "Between-group statistic"), ("df", "Between-group degrees of freedom"), ("p-value", "Between-group p")))
        return True
    return _model_fit_table(table, fit, summary)


def _model_fit_table(table, fit, summary):
    if table.title in ('Model overview', 'Residual model fit') and table.headers == ('Statistic', 'Value'):
        fit.extend(table.rows)
        values = {row[0]: row[1] for row in table.rows}
        if 'Residual I²' in values:
            summary.extend(_heterogeneity_sentence({'I²': values['Residual I²']}, 'Residual '))
        return True
    if table.title == 'Model tests':
        for row in table.rows:
            values = dict(zip(table.headers, row))
            name = values['Test']
            fit.extend((label + ' (' + name + ')', p_value(values[key]) if key == 'p-value' else values[key])
                       for key, label in (('Statistic', 'Test statistic'), ('df', 'Test degrees of freedom'), ('p-value', 'Test p')))
        return True
    if table.title == 'Model specification':
        return True
    if table.rows and ('Z' in table.headers or 't' in table.headers) and 'Estimate' not in table.headers:
        return True
    return False


def _horizontal_table(table):
    vertical = table.headers == ('Statistic', 'Value') and 'Estimate' in {row[0]: row[1] for row in table.rows}
    if vertical:
        values = {row[0]: row[1] for row in table.rows}
        table = ResultTable(table.title, tuple(values), (tuple(values.values()),))
    return table, vertical


def _report_table(result, section, table, summary, pooled, fit, level, statistic, overall, calculation):
    table, vertical = _horizontal_table(table)
    if table.title.startswith('Calculation scale'):
        return level, statistic
    if section.source_key == 'Weights' or table.title == 'Study weights':
        return level, statistic
    lower, upper, ci_level = _interval_fields(table.headers)
    if lower and upper and ci_level.endswith(' PI'):
        _prediction_rows(table, lower, upper, ci_level, vertical, fit, summary)
        return level, statistic
    if 'Estimate' in table.headers and lower and upper and section.title != 'Marginal prediction':
        level, statistic = _pooled_rows(result, section, table, lower, upper, ci_level, vertical, overall, calculation, pooled, fit, summary)
        return level, statistic
    if table.title.endswith('Heterogeneity') or table.title == 'Residual heterogeneity':
        start = len(fit)
        _heterogeneity_rows(table, fit, summary)
        if ',' in result.manuscript_metric:
            fit[start:] = [(label + ' (' + section.title.removesuffix(' Summary') + ')', value) for label, value in fit[start:]]
        return level, statistic
    _fit_table(table, fit, summary)
    return level, statistic


def _section_statistics(section):
    overall = next((dict(zip(t.headers, t.rows[0])) for t in section.tables
                    if len(t.rows) == 1 and ('Z' in t.headers or 't' in t.headers)), {})
    calculation = next((dict(zip(t.headers, t.rows[0])) for t in section.tables
                        if t.title.startswith('Calculation scale') and t.rows), {})
    return overall, calculation


def _report_sections(result, summary):
    text_sections = [section for section in result.sections if section.kind == 'text']
    if not text_sections:
        return [], []
    pooled, fit = [], list(result.manuscript_model_info)
    level, statistic = '95% CI', 'z'
    for section in text_sections:
        overall, calculation = _section_statistics(section)
        for table in section.tables:
            level, statistic = _report_table(result, section, table, summary, pooled, fit, level, statistic, overall, calculation)
    return _primary_sections(result, text_sections, pooled, fit, level, statistic), _held_sections(result)


def _primary_sections(result, text_sections, pooled, fit, level, statistic):
    template = text_sections[0]
    sections = [replace(template, title='Pooled effect', paragraphs=(() if pooled else
                         ('No structured pooled estimates are held for this workflow; the complete held output is in Supplementary details.',)),
                        tables=(ResultTable('Pooled effect', ('Effect', 'Estimate', level, 'SE', statistic, 'p'), tuple(pooled)),)),
                replace(template, title='Model fit', paragraphs=(),
                        tables=(ResultTable('Model fit', ('Statistic', 'Value'), tuple(fit)),)),
                _study_results(result, template, level)]
    if not any(section.tables for section in text_sections):
        comparisons = [s for s in text_sections if s.title in ('Pooled comparison', 'Extrapolation') or s.title.startswith('Trim-and-fill')]
        sections[0] = replace(template, title='Pooled effect', paragraphs=('Held model comparisons and sensitivity analyses.',),
                              tables=(ResultTable('Pooled effect', ('Analysis', 'Held output'), tuple((s.title, s.value) for s in comparisons)),))
        sections[1] = replace(template, title='Model fit', paragraphs=(),
                              tables=(ResultTable('Model fit', ('Statistic', 'Value'), tuple((s.title, s.value) for s in text_sections if s.title in ('Data and eligibility', 'Tests'))),))
    return sections


def _report_methods(result):
    methods = result.manuscript_methods
    if any(t.headers[0] == 'Q' for s in result.sections for t in s.tables) and 'Reitsma' not in methods:
        methods += " Heterogeneity was assessed with Cochran's Q and I²."
    methods += f' Analyses were performed in RC MetaStudio {__version__}.'
    packages = ', '.join(p.strip() for p in result.software.split(',') if not p.strip().startswith('RCMetaR'))
    if packages:
        methods += ' R packages loaded for this analysis: ' + packages + '.'
    return methods


def _table_html(table, table_number):
    parts = []
    parts.append(f'<p><b>Table {table_number}. {escape(table.title)}</b></p><table width="100%" border="0" cellspacing="0" cellpadding="5">')
    for index, row in enumerate((table.headers, *table.rows)):
        tag = 'th' if index == 0 else 'td'
        border = 'border-top: 1px solid black;' if index == 0 else ''
        if index == len(table.rows):
            border += 'border-bottom: 1px solid black;'
        parts.append('<tr>' + ''.join(f'<{tag} style="white-space:pre-wrap; {border}">' + escape(c).replace('\n', '<br>') + f'</{tag}>' for c in row) + '</tr>')
    parts.append('</table>')
    return ''.join(parts)


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
        sections, supplementary = _report_sections(result, summary)
        methods = _report_methods(result)
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
            parts.extend(section.paragraphs)
            for table in section.tables:
                number += 1
                parts.append(f'Table {number}. {table.title}')
                parts.extend(('\t'.join(table.headers), *('\t'.join(row) for row in table.rows)))
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
            parts.extend(f'<p>{escape(paragraph)}</p>' for paragraph in section.paragraphs)
            for table in section.tables:
                table_number += 1
                parts.append(_table_html(table, table_number))
        return ''.join(parts)


def figure_source(path):
    if str(path).lower().endswith('.svg'):
        svg = QSvgRenderer(str(path))
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
    for row, values in zip([target.rows[0], *[target.add_row() for _ in table.rows]], (table.headers, *table.rows)):
        for cell, value in zip(row.cells, values):
            cell.text = value


def _docx_sections(document, report, supplementary, table_number):
    for number, section in enumerate(report.sections, 1):
        if (section.title == "Supplementary details") != supplementary:
            continue
        if section.title == 'Supplementary details' and (number == 1 or report.sections[number-2].title != section.title):
            document.add_heading('Supplementary details', 1)
        for paragraph in section.paragraphs or (() if section.tables else (section.value,)):
            document.add_paragraph(paragraph)
        for table in section.tables:
            table_number += 1
            document.add_paragraph(f'Table {table_number}. {table.title}', style='Caption')
            _docx_table(document, table)
            document.add_paragraph()
    return table_number


def write_docx(report, path):
    document = Document()
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


def write_pdf(report, path):
    writer = QPdfWriter(str(path))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setResolution(600)
    document = QTextDocument()
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
        caption = QTextDocument()
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
            paint_figure(painter, source, rect)
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
