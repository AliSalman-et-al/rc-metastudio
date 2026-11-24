"""Inspect exported PDFs in the desktop verification environment."""

from pathlib import Path
from typing import NamedTuple

import pymupdf


class PdfWord(NamedTuple):
    left: float
    top: float
    right: float
    bottom: float
    text: str


class PdfPageWords(NamedTuple):
    width: float
    height: float
    words: list[PdfWord]


def pdf_text(path: Path) -> str:
    with pymupdf.open(path) as document:
        return "\n".join(page.get_text("text") for page in document)


def pdf_words(path: Path) -> list[PdfPageWords]:
    with pymupdf.open(path) as document:
        return [
            PdfPageWords(page.rect.width, page.rect.height, [
                PdfWord(left, top, right, bottom, text)
                for left, top, right, bottom, text, *_ in page.get_text("words", clip=pymupdf.INFINITE_RECT())
            ])
            for page in document
        ]


def pdf_line_colours(path: Path) -> list[tuple[str, list[int]]]:
    with pymupdf.open(path) as document:
        return [
            ("".join(span["text"] for span in line["spans"]), [span["color"] for span in line["spans"]])
            for page in document
            for block in page.get_text("dict", flags=pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES)["blocks"]
            for line in block["lines"]
        ]


def pdf_image_count(path: Path) -> int:
    with pymupdf.open(path) as document:
        return sum(len(page.get_image_info()) for page in document)


def render_pdf_page(path: Path, output: Path, page_index: int = 0, *,
                    dpi: int = 72, long_edge: int | None = None) -> None:
    with pymupdf.open(path) as document:
        page = document[page_index]
        if long_edge is None:
            pixmap = page.get_pixmap(dpi=dpi)
        else:
            scale = long_edge / max(page.rect.width, page.rect.height)
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))
        pixmap.save(output)
