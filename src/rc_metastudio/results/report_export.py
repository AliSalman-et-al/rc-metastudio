"""Render a manuscript as Word or PDF and publish it after composition succeeds."""

import io
import math
import re
from collections.abc import Generator, Sequence
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor
from PyQt6.QtCore import QMarginsF, QRectF, Qt
from PyQt6.QtGui import QFont, QFontMetricsF, QImage, QImageReader, QPageLayout, QPageSize, QPainter, QPdfWriter, QTextDocument, QTextOption
from PyQt6.QtSvg import QSvgRenderer

from rc_metastudio import r_operations
from rc_metastudio.qt_object_guard import required
from rc_metastudio.results.contract import ResultSection
from rc_metastudio.results.export_files import check_export_cancelled, compose_export, staged_output
from rc_metastudio.results.formatting import numeric_cell, numeric_columns, report_cell, report_numbers
from rc_metastudio.results.plot_capabilities import uses_forest_layout
from rc_metastudio.results.report import ManuscriptReport, methods_fragments
from rc_metastudio.results.svg_rendering import svg_bytes_for_qt, svg_view_box_size


def figure_source(path):
    if str(path).lower().endswith(('.svg', '.svgz')):
        svg = QSvgRenderer(svg_bytes_for_qt(path))
        size = svg.viewBoxF()
        return svg, size.width() / size.height()
    image = QImage(str(path))
    if image.isNull():
        raise ValueError(f'Cannot read figure: {path}')
    return image, image.width() / image.height()


def _figure_ratio(path):
    if str(path).lower().endswith((".svg", ".svgz")):
        width, height = svg_view_box_size(path)
    else:
        size = QImageReader(str(path)).size()
        width, height = size.width(), size.height()
    if width <= 0 or height <= 0:
        raise ValueError(f"Cannot read figure size: {path}")
    return width / height


def paint_figure(painter, source, rect):
    if isinstance(source, QSvgRenderer):
        source.render(painter, rect)
    else:
        painter.drawImage(rect, source)


def _docx_table(document, table):
    target = document.add_table(rows=1, cols=len(table.headers))
    target.autofit = False
    section = document.sections[-1]
    available = section.page_width - section.left_margin - section.right_margin
    widths, font_size = _docx_column_widths(table, available)
    for column, width in zip(target.columns, widths):
        column.width = width
    from docx.oxml import OxmlElement

    properties = target._tbl.tblPr
    _add_docx_rules(properties, 'tblBorders', ('top', 'bottom'))
    margins = OxmlElement('w:tblCellMar')
    for edge in ('left', 'right'):
        margin = OxmlElement('w:' + edge)
        margin.set(qn('w:w'), '40')
        margin.set(qn('w:type'), 'dxa')
        margins.append(margin)
    properties.insert_element_before(margins, 'w:tblLook')
    target.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
    numeric = numeric_columns(table.rows) or (False,) * len(table.headers)
    for index, (row, values) in enumerate(zip([target.rows[0], *[target.add_row() for _ in table.rows]], (table.headers, *table.rows))):
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        edges = tuple(edge for edge, rows in (('top', (0, 1)), ('bottom', (0, len(table.rows)))) if index in rows)
        for column, (cell, value) in enumerate(zip(row.cells, values)):
            _style_docx_cell(cell, value, widths[column], numeric[column], index == 0, font_size)
            if edges:
                _add_docx_rules(cell._tc.get_or_add_tcPr(), 'tcBorders', edges)


def _add_docx_rules(properties, kind, edges):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    borders = OxmlElement('w:' + kind)
    for edge in edges:
        rule = OxmlElement('w:' + edge)
        for attribute, value in (('val', 'single'), ('sz', '8'), ('space', '0'), ('color', '000000')):
            rule.set(qn('w:' + attribute), value)
        borders.append(rule)
    properties.insert_element_before(
        borders, 'w:shd', 'w:noWrap', 'w:tcMar', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook'
    )


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
    caption = document.styles['Caption']
    caption.font.size = Pt(11)
    caption.font.bold = True
    caption.font.italic = False
    title_properties = document.styles['Title'].element.pPr
    if title_properties is not None:
        border = title_properties.find(qn('w:pBdr'))
        if border is not None:
            title_properties.remove(border)


@contextmanager
def _figure_panels(figure: ResultSection, width_mm: float, height_mm: float) -> Generator[tuple[str, ...]]:
    if uses_forest_layout(figure.plot_kind) and figure.plot_data:
        with TemporaryDirectory(prefix="rcms-figure-") as directory:
            paths = r_operations.render_plot_bundle(
                figure.plot_data, "forest", str(Path(directory) / "panel.svg"),
                width=width_mm / 25.4, page_height=height_mm / 25.4, include_title=False,
            )
            if paths:
                yield paths
                return
    yield (figure.display_image or figure.value,)


def _figure_caption(number: int, figure: ResultSection, continued: bool) -> str:
    return f"Figure {number}. {figure.title}" + (" (continued)" if continued else "")


def _caption_document(text: str, notes: tuple[str, ...], width_mm: float) -> QTextDocument:
    caption = _print_document()
    caption.setTextWidth(width_mm / 25.4 * 96)
    caption.setHtml(f"<b>{escape(text)}</b>" + "".join(f"<br>{escape(note)}" for note in notes))
    return caption


def _figure_height_budget(number: int, figure: ResultSection, width_mm: float, height_mm: float) -> float:
    caption = _caption_document(_figure_caption(number, figure, True), figure.paragraphs, width_mm)
    return min(250, height_mm - caption.size().height() / 96 * 25.4 - 9)


@dataclass(frozen=True)
class _ReportFigure:
    section: ResultSection
    width_mm: float
    height_mm: float
    paths: tuple[str, ...]


@contextmanager
def _report_figures(report: ManuscriptReport, width_mm: float, height_mm: float
                    ) -> Generator[list[_ReportFigure]]:
    with ExitStack() as stack:
        figures = []
        for number, figure in enumerate(report.figures, 1):
            ratio = _figure_ratio(figure.display_image or figure.value)
            width = min(width_mm, _figure_width(figure, ratio))
            available = _figure_height_budget(number, figure, width_mm, height_mm)
            paths = stack.enter_context(_figure_panels(figure, width, available))
            figures.append(_ReportFigure(figure, width, available, paths))
        yield figures


_DOCX_WIDTH_MM = 210
_DOCX_HEIGHT_MM = 297
_DOCX_MARGIN_MM = 20


def _docx_figures(document, figures: Sequence[_ReportFigure]) -> None:
    for number, figure in enumerate(figures, 1):
        for index, path in enumerate(figure.paths):
            check_export_cancelled()
            _add_docx_figure_panel(document, path, figure.width_mm, figure.height_mm, number, index)
            _add_docx_figure_caption(document, figure.section, number, index)


def _add_docx_figure_caption(document, figure: ResultSection, number: int, index: int) -> None:
    caption = document.add_paragraph(_figure_caption(number, figure, bool(index)), style='Caption')
    caption.paragraph_format.keep_with_next = index == 0 and bool(figure.paragraphs)
    if index == 0:
        for note in figure.paragraphs:
            document.add_paragraph(note)


def _add_docx_figure_panel(document, path, width: float, available: float, number: int, index: int) -> None:
    from PyQt6.QtCore import QBuffer, QIODevice

    source, ratio = figure_source(path)
    placed_width = min(width, available * ratio)
    pixel_width = round(placed_width / 25.4 * 300)
    pixel_height = round(pixel_width / ratio)
    image = QImage(pixel_width, pixel_height, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)
    paint_figure(painter, source, QRectF(0, 0, pixel_width, pixel_height))
    painter.end()
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.space_after = Pt(0)
    picture = paragraph.add_run().add_picture(
        io.BytesIO(bytes(required(buffer.data().data(), "encoded figure"))), width=Mm(placed_width)
    )
    if Path(path).suffix.lower() == ".svg":
        part = Part(PackURI(f"/word/media/figure-{number}-{index + 1}.svg"),
                    "image/svg+xml", Path(path).read_bytes(), document.part.package)
        relationship = document.part.relate_to(part, RELATIONSHIP_TYPE.IMAGE)
        blip = picture._inline.xpath(".//a:blip")[0]
        blip.append(parse_xml(
            '<a:extLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main">'
            '<a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}">'
            f'<asvg:svgBlip r:embed="{relationship}"/></a:ext></a:extLst>'
        ))


def write_docx(report: ManuscriptReport, path: str | Path) -> None:
    with (
        staged_output(path) as temporary,
        _report_figures(report, _DOCX_WIDTH_MM - 2 * _DOCX_MARGIN_MM,
                        _DOCX_HEIGHT_MM - 2 * _DOCX_MARGIN_MM) as figures,
    ):
        compose_export(lambda: _write_docx(report, temporary, figures))


def _write_docx(report: ManuscriptReport, path: Path, figures: Sequence[_ReportFigure]) -> None:
    document = Document()
    _docx_styles(document)
    compatibility = document.settings.element.xpath('./w:compat/w:compatSetting[@w:name="compatibilityMode"]')[0]
    compatibility.set(qn('w:val'), '15')
    section = document.sections[0]
    section.page_width = Mm(_DOCX_WIDTH_MM)
    section.page_height = Mm(_DOCX_HEIGHT_MM)
    section.top_margin = section.bottom_margin = Mm(_DOCX_MARGIN_MM)
    section.left_margin = section.right_margin = Mm(_DOCX_MARGIN_MM)
    document.add_heading(report.title, 0)
    document.add_paragraph(report.comparison)
    for heading, text in (('Methods', report.methods), ('Results', report.results)):
        if text.strip():
            document.add_heading(heading, 1)
            paragraph = document.add_paragraph()
            for part, italic in (methods_fragments(text) if heading == 'Methods' else ((report_numbers(text), False),)):
                paragraph.add_run(part).italic = italic
    _docx_sections(document, report, False)
    _docx_sections(document, report, True)
    if report.configuration:
        document.add_heading('Model configuration', 1)
        paragraph = document.add_paragraph(report.configuration)
        paragraph.paragraph_format.keep_together = True
    _docx_figures(document, figures)
    check_export_cancelled()
    document.save(str(path))


def _print_document():
    document = QTextDocument()
    document.setDefaultFont(QFont('Arial', 11))
    option = document.defaultTextOption()
    option.setWrapMode(QTextOption.WrapMode.WordWrap)
    document.setDefaultTextOption(option)
    document.setDefaultStyleSheet('* { color: #000000; background-color: #ffffff; }')
    return document


_PDF_DPI = 600


def write_pdf(report: ManuscriptReport, path: str | Path) -> None:
    layout = QPageLayout(QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Portrait,
                         QMarginsF(20, 20, 20, 20), QPageLayout.Unit.Millimeter)
    page = layout.paintRectPixels(_PDF_DPI)
    with (
        staged_output(path) as temporary,
        _report_figures(report, page.width() / _PDF_DPI * 25.4, page.height() / _PDF_DPI * 25.4) as figures,
    ):
        compose_export(lambda: _write_pdf(report, temporary, layout, figures))


def _write_pdf(report: ManuscriptReport, path: Path, layout: QPageLayout,
               figures: Sequence[_ReportFigure]) -> None:
    writer = QPdfWriter(str(path))
    writer.setPageLayout(layout)
    writer.setResolution(_PDF_DPI)
    document = _print_document()
    document.setHtml(report.html(figure_notes=False) + report.html(supplementary=True))
    scale = writer.resolution() / 96
    page = writer.pageLayout().paintRectPixels(writer.resolution())
    width, height = page.width() / scale, page.height() / scale
    painter = QPainter(writer)
    if not painter.isActive():
        raise OSError("Could not start PDF export.")
    try:
        _print_pdf_pages(document, writer, painter, width, height, scale)
        for number, figure in enumerate(figures, 1):
            for index, panel in enumerate(figure.paths):
                check_export_cancelled()
                writer.newPage()
                source, ratio = figure_source(panel)
                w = min(figure.width_mm, figure.height_mm * ratio) / 25.4 * writer.resolution()
                h = w / ratio
                paint_figure(painter, source, QRectF((page.width() - w) / 2, 0, w, h))
                caption = _caption_document(
                    _figure_caption(number, figure.section, bool(index)),
                    () if index else figure.section.paragraphs, page.width() / writer.resolution() * 25.4,
                )
                painter.save()
                painter.scale(scale, scale)
                painter.translate(0, h / scale + 12)
                caption.drawContents(painter)
                painter.restore()
    finally:
        painter.end()


def _figure_width(figure: ResultSection, ratio: float) -> int:
    return 180 if ratio > 1.4 or uses_forest_layout(figure.plot_kind) else 85


def _docx_column_widths(table, available):
    """Measure the 10 pt cell font at a larger pixel size for sub-point precision."""
    font = QFont('Arial')
    font.setPixelSize(100)
    body = QFontMetricsF(font)
    font.setBold(True)
    heading = QFontMetricsF(font)
    wrap_at = re.compile(r'(?<=-)|\s+')
    minimums = []
    for column, header in enumerate(table.headers):
        header_width = max(heading.horizontalAdvance(word) for word in wrap_at.split(header))
        body_width = max((
            body.horizontalAdvance(word)
            for value in (row[column] for row in table.rows)
            for word in ((report_cell(value),) if numeric_cell(value) else wrap_at.split(value))
        ), default=0)
        minimums.append(Pt(max(header_width, body_width) / 10))
    lengths = [max(len(line) for row in (table.headers, *table.rows)
                   for line in (row[column].splitlines() or [''])) for column in range(len(table.headers))]
    weights = [max(5, min(45, length)) for length in lengths]
    if table.role in ('coefficients', 'fitted'):
        weights = [1, *([0] * (len(weights) - 1))]
    padding = Pt(5)
    content = available - len(weights) * padding
    total = sum(minimums)
    scale = min(1.0, content / max(1, total))
    remaining = max(0, content - total)
    widths = [round(padding + minimum * scale + remaining * weight / sum(weights))
              for minimum, weight in zip(minimums, weights)]
    font_size = max(8, math.floor(20 * scale) / 2)
    return widths, font_size


def _style_docx_cell(cell, value, width, numeric, heading, font_size):
    from docx.oxml import OxmlElement
    is_numeric = not heading and numeric_cell(value)
    cell.text = report_cell(value) if is_numeric else value
    cell.width = width
    if not heading and (is_numeric or numeric):
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
            run.font.size = Pt(font_size)
            run.bold = heading


def _print_pdf_pages(document, writer, painter, width, height, scale):
    from PyQt6.QtCore import QSizeF

    document.setPageSize(QSizeF(width, height))
    required_width = document.idealWidth()
    if required_width > width:
        expansion = required_width / width
        width = required_width
        height *= expansion
        scale /= expansion
        document.setPageSize(QSizeF(width, height))
    _keep_pdf_tables_together(document, height)
    _keep_pdf_blocks_together(document, height)
    printable = document.clone()
    printable.setPageSize(QSizeF(width, height))
    for number in range(printable.pageCount()):
        check_export_cancelled()
        if number:
            writer.newPage()
        painter.save()
        painter.scale(scale, scale)
        painter.setClipRect(QRectF(0, 0, width, height))
        painter.translate(0, -number * height)
        printable.drawContents(painter, QRectF(0, number * height, width, height))
        painter.restore()


def _keep_pdf_blocks_together(document, page_height):
    from PyQt6.QtGui import QTextCursor, QTextFormat

    layout = required(document.documentLayout(), "report document layout")
    block = document.begin()
    while block.isValid():
        cursor = QTextCursor(block)
        if cursor.currentTable() is None:
            bounds = layout.blockBoundingRect(block)
            if (bounds.height() < page_height - 2 * document.documentMargin()
                    and int(bounds.top() / page_height) < int((bounds.bottom() - 1) / page_height)):
                formatting = cursor.blockFormat()
                formatting.setPageBreakPolicy(QTextFormat.PageBreakFlag.PageBreak_AlwaysBefore)
                cursor.setBlockFormat(formatting)
        block = block.next()


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
        body = table.cellAt(table.format().headerRowCount(), 0)
        first_row = layout.blockBoundingRect(body.firstCursorPosition().block()) if body.isValid() else caption
        caption_page = int(caption.top() / page_height)
        orphaned = int((first_row.bottom() - 1) / page_height) > caption_page
        if orphaned or (bottom - caption.top() < page_height - margin
                        and caption_page != int((bottom - 1) / page_height)):
            formatting.setPageBreakPolicy(QTextFormat.PageBreakFlag.PageBreak_AlwaysBefore)
            cursor.setBlockFormat(formatting)
