"""Retain real held/presented tables and compare exported report data."""
from dataclasses import asdict
import hashlib
import json
import re
import subprocess
from pathlib import Path
import sys
import unicodedata
import xml.etree.ElementTree as ET

from docx import Document
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QTextCursor, QTextDocument, QTextTable
from rc_metastudio.manuscript_report import write_docx, write_pdf
from rc_metastudio.runtime_types import required


def numeric_tokens(text):
    return re.findall(r"(?<![\w.])[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?%?(?![\w.])", text)


def _pdf_line(words: list[ET.Element]) -> list[ET.Element]:
    top = float(words[0].attrib['yMin'])
    return [word for word in words if abs(float(word.attrib['yMin']) - top) < .01]


def _restore_page_cell(previous: list[ET.Element], visible: list[ET.Element],
                       clipped: list[ET.Element]) -> None:
    # A clipped duplicate identifies a cell continued from the previous page.
    # Move its first visible line beside that exact prefix, ahead of sibling
    # cells, only when both text and horizontal coordinates identify the row.
    if not clipped or not visible:
        return
    clipped = _pdf_line(clipped)
    continuation = _pdf_line(visible)
    left = float(clipped[0].attrib['xMin'])
    if abs(float(continuation[0].attrib['xMin']) - left) >= .01:
        return
    if float(continuation[0].attrib['yMin']) > 2 * (float(continuation[0].attrib['yMax']) - float(continuation[0].attrib['yMin'])):
        return
    expected = [(w.text, w.attrib['xMin']) for w in clipped]
    observed = [(w.text, w.attrib['xMin']) for w in previous]
    for start in range(len(previous) - len(clipped) - 1, -1, -1):
        end = start + len(clipped)
        if observed[start:end] != expected:
            continue
        sibling = previous[end]
        if abs(float(sibling.attrib['yMin']) - float(previous[start].attrib['yMin'])) >= .01:
            return
        if max(float(w.attrib['xMax']) for w in continuation) >= float(sibling.attrib['xMin']):
            return
        previous[end:end] = continuation
        del visible[:len(continuation)]
        return


def _restore_header_units(words: list[ET.Element], visible: list[ET.Element],
                          previous_page: list[ET.Element], previous_height: float) -> None:
    if not previous_page or not visible:
        return
    continuation = _pdf_line(visible)
    if not all(re.fullmatch(r'\([^()]+\)', word.text or '') for word in continuation):
        return
    line_height = float(continuation[0].attrib['yMax']) - float(continuation[0].attrib['yMin'])
    if float(continuation[0].attrib['yMin']) > 2 * line_height:
        return
    last_y = max(float(word.attrib['yMin']) for word in previous_page)
    if previous_height - last_y > 4 * line_height:
        return
    last_line = [word for word in previous_page if abs(float(word.attrib['yMin']) - last_y) < .01]
    insertions = []
    for unit in continuation:
        center = (float(unit.attrib['xMin']) + float(unit.attrib['xMax'])) / 2
        matches = [word for word in last_line
                   if abs((float(word.attrib['xMin']) + float(word.attrib['xMax'])) / 2 - center) < .01]
        if len(matches) != 1:
            return
        insertions.append((words.index(matches[0]) + 1, unit))
    # Centered units can wrap onto the next page independently in several
    # header cells. Exact column centers retain their original cell order.
    for index, unit in sorted(insertions, key=lambda entry: entry[0], reverse=True):
        words.insert(index, unit)
    del visible[:len(continuation)]


def _ordered_pdf_text(bbox: str) -> str:
    words = []
    previous_page = []
    previous_height = 0.0
    for page in ET.fromstring(bbox).iter('{http://www.w3.org/1999/xhtml}page'):
        width, height = float(page.attrib['width']), float(page.attrib['height'])
        visible, clipped = [], []
        for word in page.iter('{http://www.w3.org/1999/xhtml}word'):
            x, y, right, bottom = (float(word.attrib[key]) for key in ('xMin', 'yMin', 'xMax', 'yMax'))
            if 0 <= x <= right <= width and 0 <= y <= bottom <= height:
                visible.append(word)
            elif 0 <= x <= right <= width and y < 0 < bottom:
                clipped.append(word)
        _restore_page_cell(words, visible, clipped)
        _restore_header_units(words, visible, previous_page, previous_height)
        words.extend(visible)
        previous_page, previous_height = visible, height
    text = []
    previous = None
    for word in words:
        x, y, bottom = (float(word.attrib[key]) for key in ('xMin', 'yMin', 'yMax'))
        value = word.text or ''
        # Join only a decimal's digit continuation on the next line of its cell.
        if (previous is not None and re.fullmatch(r'[+-]?\d+\.\d+', text[-1])
                and value.isascii() and value.isdigit()
                and abs(x - previous[0]) < .01 and -1 <= y - previous[1] <= .5):
            text[-1] += value
        else:
            text.append(value)
        previous = (x, bottom)
    return ' '.join(text)


def visible_pdf_text(path):
    raw = subprocess.check_output(['pdftotext', '-enc', 'UTF-8', '-raw', str(path), '-'], text=True, encoding="utf-8")
    path.with_name('pdf-raw.txt').write_text(raw, encoding="utf-8")
    bbox = subprocess.check_output(['pdftotext', '-enc', 'UTF-8', '-raw', '-bbox', str(path), '-'], text=True, encoding="utf-8")
    path.with_name('pdf-bbox.xhtml').write_text(bbox, encoding="utf-8")
    return _ordered_pdf_text(bbox)



def capture(view, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    held = [dict(section=s.title, source=s.source_key, **asdict(t))
            for s in view.results.sections for t in s.tables]
    held_text = [dict(section=s.title, value=s.value) for s in view.results.sections
                 if s.kind == 'text' and not s.tables]
    held_notes = [dict(section=s.title, paragraphs=list(s.paragraphs)) for s in view.results.sections
                  if s.kind == 'text' and s.tables and s.paragraphs]
    presented = [dict(section=s.title, **asdict(t))
                 for s in view.manuscript.sections for t in s.tables]
    key = hashlib.sha256(json.dumps([held, held_text, held_notes, presented, view.manuscript.title,
                                    view.manuscript.methods, view.manuscript.results], sort_keys=True).encode()).hexdigest()[:16]
    target = directory / key
    view._copy_report()
    if (target / 'audit.json').exists():
        data = json.loads((target / 'audit.json').read_text(encoding="utf-8"))
        data['directory'] = str(target)
        return data
    target.mkdir(exist_ok=True)
    report = view.manuscript
    (target / 'copy.html').write_text(required(required(QApplication.clipboard(), 'clipboard').mimeData(), 'copied report').html(), encoding="utf-8")
    write_docx(report, target / 'report.docx')
    write_pdf(report, target / 'report.pdf')
    doc = Document(str(target / 'report.docx'))
    doc_tables = [[[c.text for c in row.cells] for row in table.rows] for table in doc.tables]
    pdf = visible_pdf_text(target / 'report.pdf')
    surfaces = {
        'copy': required(QApplication.clipboard(), 'clipboard').text(),
        'pdf': pdf,
        'docx': '\n'.join([*(p.text for p in doc.paragraphs), *(c for t in doc_tables for r in t for c in r)]),
    }
    missing = {}
    for surface, text in surfaces.items():
        tokens = set(numeric_tokens(text))
        missing[surface] = [dict(section=t['section'], table=t['title'], row=i,
                                 header=header, value=value)
                            for t in held for i, row in enumerate(t['rows'])
                            for header, value in zip(t['headers'], row)
                            if any(token not in tokens for token in numeric_tokens(value))]
        (target / (surface + '.txt')).write_text(text, encoding="utf-8")
    data = dict(title=report.title, held=held, held_text=held_text, held_notes=held_notes, presented=presented,
                docx_tables=doc_tables, missing=missing, directory=str(target))
    (target / 'audit.json').write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def expected_p(value):
    from decimal import Decimal
    if not value or value in ('NA', '—'):
        return '—'
    if value.startswith('<'):
        bound = Decimal(value.removeprefix('<').strip())
        return '< .001' if bound <= Decimal('.001') else '< ' + f'{bound:.3f}'.removeprefix('0')
    if Decimal(value) < Decimal('.001'):
        return '< .001'
    return f'{Decimal(value):.3f}'.removeprefix('0')


def expected_pooled(result):
    rows = []
    for section in result.sections:
        if section.title == 'Marginal prediction':
            continue
        overall = next((dict(zip(t.headers, t.rows[0])) for t in section.tables
                        if len(t.rows) == 1 and ('Z' in t.headers or 't' in t.headers)), {})
        calculation = next((dict(zip(t.headers, t.rows[0])) for t in section.tables
                            if t.title.startswith('Calculation scale') and t.rows), {})
        rows.extend(expected_effect_rows(result, section, overall, calculation))
    return tuple(rows)


def expected_effect_rows(result, section, overall, calculation):
    rows = []
    for table in section.tables:
        vertical = table.headers == ('Statistic', 'Value') and 'Estimate' in dict(table.rows)
        headers = tuple(dict(table.rows)) if vertical else table.headers
        values = [dict(table.rows)] if vertical else [dict(zip(headers, row)) for row in table.rows]
        low = next((h for h in headers if h.startswith('Lower bound')), None)
        high = next((h for h in headers if h.startswith('Upper bound')), None)
        if not low or not high or low.partition('(')[2].removesuffix(')').strip().endswith(' PI') or table.title.startswith('Calculation scale'):
            continue
        metric = table.title.lower() if vertical else section.title.removesuffix(' Summary').lower() if ',' in result.manuscript_metric else result.manuscript_metric or 'effect'
        if table.title != 'Regression coefficients' and metric.endswith('transformed proportion'):
            metric = 'proportion'
        rows.extend(expected_effect_values(values, headers, low, high, metric, vertical, table.title, overall, calculation))
    return rows


def expected_effect_values(values, headers, low, high, metric, vertical, title, overall, calculation):
    rows = []
    for row in values:
        if not row.get('Estimate'):
            continue
        context = next((row[h] for h in headers if h.startswith(('Study added', 'Study omitted'))), title if vertical else metric)
        label = row.get('Term', row.get('Subgroups', context))
        statistic = next((row.get(h, overall.get(h)) for h in ('t', 'z', 'Z', 'z-value', 't-value') if h in row or h in overall), '—')
        se = next((value for key, value in {**calculation, **row}.items() if key.startswith('SE')), '—')
        rows.append((label[:1].upper() + label[1:], row['Estimate'], row[low] + ' to ' + row[high], se, statistic, expected_p(row.get('p-value', overall.get('p-value', '')))))
    return rows


def expected_studies(result):
    rows = []
    for section in result.sections:
        for table in section.tables:
            if table.title != 'Study weights':
                continue
            label = result.manuscript_metric or section.title if section.source_key == 'Weights' else section.title.removesuffix(' Summary')
            for row in table.rows:
                cells = (row[0], row[1], row[2] + ' to ' + row[3], row[4]) if len(row) == 5 else (row[0], '—', '—', row[1])
                rows.append((label, *cells))
    if rows and all(row[2:4] == ('—', '—') for row in rows):
        return tuple((row[0], row[1], row[4]) for row in rows)
    return tuple(rows)


def expected_fit(result):
    if not any(s.tables for s in result.sections):
        return tuple((s.title, s.value) for s in result.sections if s.title in ('Data and eligibility', 'Tests'))
    rows = list(result.manuscript_model_info)
    for section in result.sections:
        for table in section.tables:
            rows.extend(expected_fit_table(result, section, table))
    return tuple(rows)


def expected_fit_table(result, section, source):
    vertical = source.headers == ('Statistic', 'Value') and 'Estimate' in dict(source.rows)
    headers = tuple(dict(source.rows)) if vertical else source.headers
    data = [dict(source.rows)] if vertical else [dict(zip(headers, row)) for row in source.rows]
    low = next((h for h in headers if h.startswith('Lower bound')), None)
    high = next((h for h in headers if h.startswith('Upper bound')), None)
    rows = []
    if source.title.startswith('Calculation scale') or source.title == 'Study weights':
        return rows
    if low and high and low.partition('(')[2].removesuffix(')').strip().endswith(' PI'):
        level = low.partition('(')[2].removesuffix(')').strip()
        for row in data:
            context = row.get('Subgroups', source.title if vertical else '')
            rows.append((level.removesuffix(' PI') + ' prediction interval' + (' (' + context + ')' if context else ''), row[low] + ' to ' + row[high]))
    elif 'Estimate' in headers and low and high and section.title != 'Marginal prediction':
        rows.extend(('Studies (k) (' + row['Subgroups'] + ')', row['k']) for row in data if 'k' in row and 'Subgroups' in row and row['Estimate'])
    elif source.title.endswith('Heterogeneity') or source.title == 'Residual heterogeneity':
        labels = {'Q': 'Cochran’s Q', 'df': 'Heterogeneity degrees of freedom', 'p-value': 'Heterogeneity p', 'I²': 'I²', 'τ²': 'Between-study variance (τ²)'}
        for row in data:
            context = (' (' + row['Subgroups'] + ')' if 'Subgroups' in row else '')
            if ',' in result.manuscript_metric:
                context += ' (' + section.title.removesuffix(' Summary') + ')'
            rows.extend((labels[h] + context, expected_p(v) if h == 'p-value' else v) for h, v in row.items() if h in labels)
    elif source.title == 'Test of subgroup differences' and data:
        rows.extend((label, expected_p(data[0][key]) if key == 'p-value' else data[0][key]) for key, label in (
            ('Test', 'Between-group test'), ('Statistic', 'Between-group statistic'), ('df', 'Between-group degrees of freedom'), ('p-value', 'Between-group p')))
    elif source.title in ('Model overview', 'Residual model fit') and source.headers == ('Statistic', 'Value'):
        rows.extend(source.rows)
    elif source.title == 'Model tests':
        for row in data:
            rows.extend((label + ' (' + row['Test'] + ')', expected_p(row[key]) if key == 'p-value' else row[key]) for key, label in (
                ('Statistic', 'Test statistic'), ('df', 'Test degrees of freedom'), ('p-value', 'Test p')))
    return rows


def assert_exports(view, data):
    tables = [table for section in view.manuscript.sections for table in section.tables]
    expected = [[list(table.headers), *[list(row) for row in table.rows]] for table in tables]
    assert data['docx_tables'] == expected, (data['docx_tables'], expected)
    copied = (Path(data['directory']) / 'copy.txt').read_text(encoding="utf-8")
    # PDF wraps URLs and hyphenated labels. Compare whole tables while preserving
    # every digit, sign and punctuation mark across those physical line breaks.
    pdf = re.findall(r'\w+|[^\w\s]', unicodedata.normalize('NFKC', (Path(data['directory']) / 'pdf.txt').read_text(encoding="utf-8")))
    cursor = 0
    for number, table in enumerate(tables, 1):
        caption = f'Table {number}. {table.title}'
        start = copied.splitlines().index(caption)
        offset = sum(len(line) + 1 for line in copied.splitlines(keepends=False)[:start])
        block = '\n\n'.join([caption, *['\t'.join(row) for row in (table.headers, *table.rows)]])
        assert copied[offset:offset + len(block)] == block, (caption, block)
        caption_tokens = re.findall(r'\w+|[^\w\s]', unicodedata.normalize('NFKC', caption))
        tokens = re.findall(r'\w+|[^\w\s]', unicodedata.normalize('NFKC', ' '.join([caption, *[' '.join(row) for row in (table.headers, *table.rows)]])))
        starts = [i for i in range(cursor, len(pdf)) if pdf[i] == 'Table' and pdf[i:i + len(caption_tokens)] == caption_tokens]
        assert len(starts) == 1, (caption, 'PDF caption missing or repeated', data['directory'])
        start = starts[0]
        assert pdf[start:start + len(tokens)] == tokens, (caption, 'PDF table differs from complete ordered held/presented rows', data['directory'])
        cursor = start + len(tokens)


def presentation_rows(rows, digits):
    from decimal import Decimal
    return tuple(tuple(re.sub(r"(?<![\w.])-?\d+\.\d+%?(?![\w.])",
                             lambda m: f"{Decimal(m[0][:-1]):.1f}%" if m[0].endswith("%") else f"{Decimal(m[0]):.{digits}f}", cell)
                       for cell in row) for row in rows)


def assert_retained_table(view, section, source):
    title = source.title if section.title == source.title else section.title + ' — ' + source.title
    tables = [table for table in view._report_tables if table.title == 'Full-precision results']
    assert len(tables) == 1, [table.title for table in view._report_tables]
    expected = tuple((title, '\n'.join(f'{h}: {v}' for h, v in zip(source.headers, row))) for row in source.rows)
    observed = tuple(row for row in tables[0].rows if row[0] == title)
    assert observed == expected, (title, observed, expected)
    return tables[0]


def assert_report(view):
    tables = [table for section in view.manuscript.sections for table in section.tables]
    assert [table.title for table in tables[:3]] == ['Pooled effect', 'Model fit', 'Study results']
    pooled, fit, studies = tables[:3]
    structured = any(s.tables for s in view.results.sections)
    if structured:
        assert pooled.headers[:2] == ('Effect', 'Estimate')
        assert pooled.headers[2].endswith('% CI')
        assert pooled.headers[3:] in (('SE', 'z', 'p'), ('SE', 't', 'p'))
        assert pooled.rows == presentation_rows(expected_pooled(view.results), view.results.manuscript_digits), (pooled.rows, expected_pooled(view.results))
    else:
        assert pooled.headers == ('Analysis', 'Output')
        assert pooled.rows == tuple((s.title, s.value) for s in view.results.sections
                                    if s.kind == 'text' and (s.title in ('Pooled comparison', 'Extrapolation') or s.title.startswith('Trim-and-fill')))
    assert fit.headers == ('Statistic', 'Value')
    row_label = 'Fit' if any('leave-one-out' in s.title.casefold() for s in view.results.sections) else 'Study'
    expected = expected_studies(view.results)
    headers = ('Analysis', row_label, 'Effect', pooled.headers[2] if structured else '95% CI', 'Weight')
    if expected and len(expected[0]) == 3:
        headers = ('Analysis', row_label, 'Weight')
    if len({row[0] for row in expected}) == 1:
        headers = headers[1:]
        expected = tuple(row[1:] for row in expected)
    assert studies.headers == headers
    assert fit.rows == presentation_rows(expected_fit(view.results), view.results.manuscript_digits), (fit.rows, expected_fit(view.results))
    assert studies.rows == presentation_rows(expected, view.results.manuscript_digits)
    for section in view.results.sections:
        for source in section.tables:
            title = source.title if section.title == source.title else section.title + ' — ' + source.title
            retained = next(t for t in tables[3:] if t.title == 'Full-precision results')
            expected = tuple((title, '\n'.join(f'{h}: {v}' for h, v in zip(source.headers, row))) for row in source.rows)
            assert tuple(row for row in retained.rows if row[0] == title) == expected, title
        if section.tables and section.paragraphs:
            assert any(s.paragraphs == section.paragraphs for s in view.manuscript.sections
                       if s.title == 'Supplementary details'), section.title
        if section.kind == 'text' and not section.tables and section.value:
            if section.source_key == 'References':
                references = [s for s in view.manuscript.sections if s.source_key == 'References'
                              and s.title == 'Supplementary details']
                assert len(references) == 1
                assert not references[0].tables
                expected = tuple(f"{n}. {line}" if not re.match(r"^\d+[.)]\s", line) else line
                                 for n, line in enumerate(filter(None, section.value.splitlines()), 1))
                assert references[0].paragraphs == expected
            else:
                retained = next(t for t in tables[3:] if t.title == 'Full-precision results')
                assert tuple(row for row in retained.rows if row[0] == section.title + ' — Output') == tuple((section.title + ' — Output', 'Output: ' + line) for line in section.value.splitlines())
    data = capture(view, Path(sys.argv[2]) / 'report-retention')
    assert_exports(view, data)
    document = QTextDocument()
    document.setHtml(required(required(QApplication.clipboard(), 'clipboard').mimeData(), 'copied report').html())
    assert document_tables(document) == [[list(t.headers), *[list(row) for row in t.rows]] for t in tables]
    prose_surfaces = [
        (Path(data['directory']) / 'copy.txt').read_text(encoding='utf-8'),
        (Path(data['directory']) / 'pdf.txt').read_text(encoding='utf-8'),
        '\n'.join(p.text for p in Document(str(Path(data['directory']) / 'report.docx')).paragraphs),
    ]
    for text in prose_surfaces:
        assert not re.search(r'\bHeld\b', text)
        normalized = re.sub(r'\s+', '', unicodedata.normalize('NFKC', text))
        for section in view.manuscript.sections:
            for paragraph in section.paragraphs:
                assert re.sub(r'\s+', '', unicodedata.normalize('NFKC', paragraph)) in normalized, paragraph
    selected = view.table_selector.currentIndex()
    for index, table in enumerate(tables):
        view.table_selector.setCurrentIndex(index)
        assert view.result_table.columnCount() == len(table.headers)
        assert view.result_table.rowCount() == len(table.rows)
        assert tuple(' '.join(required(view.result_table.horizontalHeaderItem(col), 'table header').text().split())
                     for col in range(len(table.headers))) == tuple(' '.join(header.split()) for header in table.headers)
        assert tuple(tuple(view.result_table.item(row, col).text() for col in range(len(table.headers)))
                     for row in range(len(table.rows))) == table.rows
    view.table_selector.setCurrentIndex(selected)
    return pooled, fit


def document_tables(document):
    tables = []
    for frame in document.rootFrame().childFrames():
        if not isinstance(frame, QTextTable):
            continue
        rows = []
        for row in range(frame.rows()):
            cells = []
            for col in range(frame.columns()):
                cell = frame.cellAt(row, col)
                cursor = cell.firstCursorPosition()
                cursor.setPosition(cell.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                cells.append(cursor.selectedText().replace('\u2029', '\n').replace('\u2028', '\n'))
            rows.append(cells)
        tables.append(rows)
    return tables


def install_capture(directory):
    from unittest.mock import patch
    from rc_metastudio.results_window import ResultsWindow
    original = ResultsWindow._setup_manuscript_page

    def observed(view):
        original(view)
        capture(view, directory)

    patch.object(ResultsWindow, '_setup_manuscript_page', observed).start()
