# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Own persisted plot editing and export operations at the R boundary."""

from __future__ import annotations

import gzip
import io
import os
import re
import shutil
import tempfile
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, cast
from xml.etree import ElementTree as ET

from PyQt6.QtCore import QMarginsF, QRectF, QSettings
from PyQt6.QtGui import QPageSize, QPainter, QPdfWriter
from PyQt6.QtSvg import QSvgRenderer

from rc_metastudio import r_bridge
from rc_metastudio.results.svg_rendering import svg_bytes_for_qt
from rc_metastudio.results.plot_capabilities import PlotRegenerator
from rc_metastudio.r_call_serialization import serialized_r_call


# Match RCMetaR's bitmap device guard.
RASTER_MAX_DIMENSION = 32000
RASTER_MAX_PIXELS = 150_000_000


class PlotServiceError(RuntimeError):
    """Raised when a persisted plot cannot be edited or exported."""


class PlotService:
    """Apply plot edits and render exports without leaking R into the UI."""

    @serialized_r_call
    def load_params(self, params_path: str) -> dict[str, object] | None:
        """Load persisted plot parameters, returning ``None`` when unavailable."""
        params = r_bridge.load_plot_parameters(params_path)
        if params is None:
            return None
        if not isinstance(params, Mapping):
            raise PlotServiceError("R returned invalid plot parameters")
        result: dict[str, object] = {}
        for key, value in params.items():
            if not isinstance(key, str):
                raise PlotServiceError("R returned invalid plot parameter names")
            result[key] = value
        return result

    @serialized_r_call
    def apply_edits(
        self,
        *,
        regenerator: PlotRegenerator,
        params_path: str,
        updated_params: Mapping[str, object],
        output_path: str,
    ) -> None:
        """Persist parameters, regenerate data, and render an edited plot."""
        if regenerator == "none":
            raise PlotServiceError(f"Plot is not editable: {regenerator}")
        target = Path(output_path)
        if regenerator == "funnel" and target.suffix.lower() == ".svgz":
            raise ValueError(
                "SVGZ output is not supported when editing funnel plots; use SVG instead."
            )

        staging = Path(tempfile.mkdtemp(prefix=".rcms-plot-", dir=str(target.parent)))
        retain_recovery = False
        backups: dict[Path, Path] = {}
        promoted: list[Path] = []
        try:
            prepared = r_bridge.prepare_plot_edit(
                params_path, regenerator, updated_params, output_path, str(staging)
            )
            if prepared is None:
                raise PlotServiceError(f"Stored {regenerator} plot bundle is incomplete: {params_path}")
            replacements = _staged_files(prepared, staging)
            for index, destination in enumerate(replacements):
                if destination.exists():
                    backup = staging / f"backup-{index}"
                    shutil.copy2(destination, backup)
                    backups[destination] = backup
            for destination, source in replacements.items():
                os.replace(source, destination)
                promoted.append(destination)
        except Exception as error:
            if not _restore_files(promoted, backups, error):
                retain_recovery = True
                error.add_note(f"Plot recovery files retained at {staging}")
            raise
        finally:
            if not retain_recovery:
                shutil.rmtree(staging, ignore_errors=True)

    @serialized_r_call
    def export_sized(self, *, regenerator: PlotRegenerator, params_path: str,
                     output_path: str, width: float, height: float, dpi: int,
                     include_title: bool = True, geometry: tuple[float, float] | None = None) -> None:
        """Render at publication dimensions without changing analysis state."""
        if geometry is None and regenerator == "forest":
            geometry = r_bridge.forest_export_dimensions(params_path, width, include_title)
        if geometry is not None:
            height, minimum_width = geometry
            if width < minimum_width - 1e-8:
                raise PlotServiceError(f"Minimum width for this figure: {minimum_width * 25.4:.1f} mm")
        with tempfile.TemporaryDirectory(prefix='rcms-export-') as directory:
            source = Path(directory) / 'plot.svg'
            extension = Path(output_path).suffix.lower()
            if geometry is not None and extension == ".pdf" and height > 267 / 25.4 and _paginate_pdf():
                page_width = min(width, 180 / 25.4)
                if page_width < geometry[1] - 1e-8:
                    raise PlotServiceError("This figure is too wide for A4. Turn off A4 pages to export a single PDF page.")
                paths = r_bridge.render_plot_bundle(
                    params_path, regenerator, str(source), include_title=include_title,
                    width=page_width, page_height=250 / 25.4,
                )
                with staged_output(output_path) as temporary:
                    _write_a4_pdf(str(temporary), paths)
                return
            paths = r_bridge.render_plot_bundle(
                params_path, regenerator, str(source), include_title=include_title,
                width=width if regenerator == "forest" else None,
            )
            if not paths:
                raise PlotServiceError(f"Stored {regenerator} plot bundle is incomplete: {params_path}")
            ET.register_namespace('', 'http://www.w3.org/2000/svg')
            ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
            tree = ET.parse(source)
            root = tree.getroot()
            root.set('width', f'{width}in')
            root.set('height', f'{height}in')
            x, y, view_width, view_height = map(float, root.attrib['viewBox'].split())
            # Center the unchanged artwork and fill the physical paper, including
            # the space freed when the title is excluded.
            paper_width = max(view_width, view_height * width / height)
            paper_height = max(view_height, view_width * height / width)
            x -= (paper_width - view_width) / 2
            y -= (paper_height - view_height) / 2
            root.set('viewBox', f'{x} {y} {paper_width} {paper_height}')
            paper = ET.Element('{http://www.w3.org/2000/svg}rect', {
                'x': str(x), 'y': str(y), 'width': str(paper_width), 'height': str(paper_height), 'fill': 'white',
            })
            root.insert(0, paper)
            tree.write(source, encoding='utf-8', xml_declaration=True)
            if extension in (".svg", ".svgz"):
                with staged_output(output_path) as temporary:
                    _copy_export_svg(source, temporary, compressed=extension == ".svgz")
            else:
                r_bridge.export_svg_artwork(str(source), output_path, width, height, dpi)

    @serialized_r_call
    def export(
        self, *, regenerator: PlotRegenerator, params_path: str, output_path: str,
        include_title: bool = True, outline_text: bool = True,
    ) -> None:
        """Render a stored plot to an already validated destination path."""
        if regenerator == "none":
            raise PlotServiceError(f"Plot is not regeneratable: {regenerator}")
        if not r_bridge.render_plot_bundle(params_path, regenerator, output_path,
                                           include_title=include_title, outline_text=outline_text):
            raise PlotServiceError(f"Stored {regenerator} plot bundle is incomplete: {params_path}")


@contextmanager
def staged_output(path: str | Path) -> Generator[Path]:
    destination = Path(path).resolve()
    with tempfile.TemporaryDirectory(prefix=".rcms-export-", dir=destination.parent) as directory:
        temporary = Path(directory) / destination.name
        yield temporary
        temporary.replace(destination)


def _copy_export_svg(source: Path, destination: Path, *, compressed: bool) -> None:
    if compressed:
        with source.open("rb") as input_file, gzip.open(destination, "wb") as output_file:
            shutil.copyfileobj(input_file, output_file)
    else:
        shutil.copyfile(source, destination)


def _paginate_pdf() -> bool:
    return str(QSettings().value("export/paginate_pdf", True)).lower() == "true"


def _write_a4_pdf(output: str, paths: tuple[str, ...]) -> None:
    writer = QPdfWriter(output)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageMargins(QMarginsF(15, 15, 15, 15))
    writer.setResolution(600)
    page = writer.pageLayout().paintRectPixels(writer.resolution())
    painter = QPainter(writer)
    try:
        for index, path in enumerate(paths):
            if index:
                writer.newPage()
            svg = QSvgRenderer(svg_bytes_for_qt(path))
            bounds = svg.viewBoxF()
            scale = min(writer.resolution() / 72, page.width() / bounds.width(), page.height() / bounds.height())
            w, h = bounds.width() * scale, bounds.height() * scale
            svg.render(painter, QRectF((page.width() - w) / 2, 0, w, h))
    finally:
        painter.end()


def svg_text_points_per_inch(path: str | Path, height_per_width: float) -> float:
    """Measure the smallest SVG font against the physical export viewport."""
    opener = gzip.open if str(path).lower().endswith(".svgz") else open
    with opener(path, "rb") as source:
        svg = source.read()
    view_width, view_height = _view_box_size(io.BytesIO(svg))
    sizes = map(float, re.findall(rb"font-size:\s*([\d.]+)px", svg))
    return min(sizes, default=0.0) * 72 * min(1 / view_width, height_per_width / view_height)


def svg_view_box_size(path: str | Path) -> tuple[float, float]:
    opener = gzip.open if str(path).lower().endswith(".svgz") else open
    with opener(path, "rb") as source:
        return _view_box_size(source)


def _view_box_size(source: BinaryIO | gzip.GzipFile) -> tuple[float, float]:
    with_root = ET.iterparse(source, events=("start",))
    _, root = cast(tuple[str, ET.Element], next(with_root))
    _, _, width, height = map(float, root.attrib["viewBox"].replace(",", " ").split())
    return width, height


def _staged_files(prepared: object, staging: Path) -> dict[Path, Path]:
    if not isinstance(prepared, Mapping) or not prepared:
        raise PlotServiceError("R returned invalid staged plot files")
    replacements: dict[Path, Path] = {}
    seen: set[str] = set()
    owned_directory = staging.resolve()
    for target, source in prepared.items():
        if not isinstance(target, str) or not target or not isinstance(source, str) or not source:
            raise PlotServiceError("R returned invalid staged plot file names")
        destination = Path(target)
        staged = Path(source)
        normalized_target = os.path.normcase(os.path.abspath(destination))
        if normalized_target in seen:
            raise PlotServiceError(f"Several staged plot files target {destination}")
        if staged.resolve().parent != owned_directory or not staged.is_file():
            raise PlotServiceError(f"Staged plot file is missing or outside the edit directory: {staged}")
        replacements[destination] = staged
        seen.add(normalized_target)
    return replacements


def _restore_files(
    promoted: list[Path],
    backups: Mapping[Path, Path],
    original_error: Exception,
) -> bool:
    restored = True
    for destination in reversed(promoted):
        try:
            if destination in backups:
                os.replace(backups[destination], destination)
            else:
                destination.unlink(missing_ok=True)
        except OSError as restore_error:
            restored = False
            original_error.add_note(f"Plot rollback failed for {destination}: {restore_error}")
    return restored


__all__ = ["PlotService", "PlotServiceError"]
