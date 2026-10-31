"""Manuscript content taken exclusively from an executed result."""
from dataclasses import dataclass
from html import escape
import io
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QImage, QPainter, QPdfWriter, QTextDocument, QPageSize
from PyQt6.QtSvg import QSvgRenderer
from docx import Document
from docx.shared import Mm
from rc_metastudio import __version__


@dataclass(frozen=True)
class ManuscriptReport:
    title: str
    methods: str
    sections: tuple
    figures: tuple
    summary: tuple[str, ...]

    @classmethod
    def from_result(cls, result):
        methods = 'The analysis used the following executed settings. ' + '. '.join(x.strip().rstrip('.') for x in result.details.splitlines() if x.strip()) + '.'
        methods += ' ' + result.manuscript_context
        methods += f' Analyses were performed with RC MetaStudio {__version__}.'
        if result.software:
            methods += ' R packages loaded for this analysis: ' + result.software + '.'
        sections = tuple(s for s in result.sections if s.kind == 'text')
        figures = tuple((s.title, result.display_images.get(s.source_key, s.value)) for s in result.sections if s.kind == 'image')
        summary = []
        for section in sections:
            for table in section.tables:
                if table.headers and table.headers[0] in ("Q", "Z", "t"):
                    for row in table.rows:
                        values = "; ".join(f"{header} = {value}" for header, value in zip(table.headers, row))
                        summary.append(("Heterogeneity: " if table.headers[0] == "Q" else "Overall test: ") + values + ".")
        return cls(result.identity, methods, sections, figures, tuple(summary))

    def plain_text(self):
        parts = [self.title, "Methods", self.methods, "Results", *self.summary]
        for section in self.sections:
            parts.append(section.title)
            parts.extend(section.paragraphs or (() if section.tables else (section.value,)))
            for table in section.tables:
                parts.append("\n".join("\t".join(row) for row in (table.headers, *table.rows)))
        return "\n\n".join(parts)

    def html(self):
        parts = [f'<h1>{escape(self.title)}</h1><h2>Methods</h2><p>{escape(self.methods)}</p><h2>Results</h2>']
        parts.extend(f"<p>{escape(p)}</p>" for p in self.summary)
        for section in self.sections:
            parts.append(f'<h3>{escape(section.title)}</h3>')
            parts.extend(f'<p>{escape(p)}</p>' for p in (section.paragraphs or (() if section.tables else (section.value,))))
            for table in section.tables:
                parts.append('<table border="1" cellpadding="5">')
                for row in (table.headers, *table.rows):
                    parts.append('<tr>' + ''.join('<td>' + escape(c) + '</td>' for c in row) + '</tr>')
                parts.append('</table>')
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


def write_docx(report, path):
    document = Document()
    section = document.sections[0]
    section.page_width = Mm(210)
    section.left_margin = section.right_margin = Mm(15)
    document.add_heading(report.title, 0)
    document.add_heading('Methods', 1)
    document.add_paragraph(report.methods)
    document.add_heading('Results', 1)
    for paragraph in report.summary:
        document.add_paragraph(paragraph)
    for section in report.sections:
        document.add_heading(section.title, 2)
        for paragraph in section.paragraphs or (() if section.tables else (section.value,)):
            document.add_paragraph(paragraph)
        for table in section.tables:
            target = document.add_table(rows=1, cols=len(table.headers))
            target.style = 'Table Grid'
            for row, values in zip([target.rows[0], *[target.add_row() for _ in table.rows]], (table.headers, *table.rows)):
                for cell, value in zip(row.cells, values):
                    cell.text = value
    from PyQt6.QtCore import QBuffer, QIODevice
    for number, (title, path_) in enumerate(report.figures, 1):
        source, ratio = figure_source(path_)
        width = 180 if ratio > 1.4 else 85
        image = QImage(round(width / 25.4 * 300), round(width / 25.4 * 300 / ratio), QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        paint_figure(painter, source, QRectF(image.rect()))
        painter.end()
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, 'PNG')
        document.add_picture(io.BytesIO(bytes(buffer.data())), width=Mm(width))
        document.add_paragraph(f'Figure {number}. {title}')
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
    for number in range(document.pageCount()):
        if number:
            writer.newPage()
        painter.save()
        painter.scale(scale, scale)
        painter.setClipRect(QRectF(0, 0, width, height))
        painter.translate(0, -number * height)
        context = QAbstractTextDocumentLayout.PaintContext()
        context.clip = QRectF(0, number * height, width, height)
        document.documentLayout().draw(painter, context)
        painter.restore()
    for number, (title, path_) in enumerate(report.figures, 1):
        writer.newPage()
        source, ratio = figure_source(path_)
        mm = 180 if ratio > 1.4 else 85
        w = mm / 25.4 * writer.resolution()
        h = w / ratio
        if h > page.height() - 200:
            painter.end()
            raise ValueError('Figure is too tall for an A4 manuscript page')
        rect = QRectF((page.width() - w) / 2, 0, w, h)
        paint_figure(painter, source, rect)
        painter.save()
        painter.scale(scale, scale)
        painter.drawText(QRectF(0, h / scale + 12, width, 60), Qt.TextFlag.TextWordWrap, f'Figure {number}. {title}')
        painter.restore()
    painter.end()
