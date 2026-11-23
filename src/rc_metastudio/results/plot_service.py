# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Own persisted plot editing and export operations at the R boundary."""

from __future__ import annotations

import gzip
import os
import shutil
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from xml.etree import ElementTree as ET

from PyQt6.QtCore import QMarginsF, QRectF
from PyQt6.QtGui import QImage, QPageSize, QPainter, QPdfWriter
from PyQt6.QtSvg import QSvgRenderer

from rc_metastudio import r_operations
from rc_metastudio.results.export_files import check_export_cancelled, compose_export, staged_output
from rc_metastudio.results.svg_rendering import plot_text_layout_issue, svg_bytes_for_qt, svg_text_points_per_inch, svg_view_box_size
from rc_metastudio.results.plot_capabilities import PlotCapability, PlotRegenerator, uses_forest_layout
from rc_metastudio.results.plot_geometry import A4_CONTENT_HEIGHT_INCHES


@dataclass(frozen=True, slots=True)
class PlotExportGeometry:
    width: float
    height: float
    native_dpi: int = 96
    text_per_inch: tuple[float, float] = (0.0, 0.0)
    forest_measurement: Callable[[float, bool], tuple[float, float] | None] | None = None
    check_layout: Callable[[float, bool], None] | None = None


class PlotServiceError(RuntimeError):
    """Raised when a persisted plot cannot be edited or exported."""


class PlotService:
    """Apply plot edits and render exports without leaking R into the UI."""

    def export_geometry(
        self, path: str, capability: PlotCapability, params_path: str | None,
    ) -> PlotExportGeometry:
        if not path.lower().endswith((".svg", ".svgz")):
            source = QImage(path)
            if source.isNull():
                raise ValueError("Could not read the plot image.")
            dpi = source.dotsPerMeterX() * .0254
            width = source.width() / max(1, dpi)
            return PlotExportGeometry(width, width / (source.width() / source.height()), round(dpi))

        view_width, view_height = svg_view_box_size(path)
        width = view_width / 72
        ratio = view_width / view_height
        height = width / ratio
        if not params_path:
            return PlotExportGeometry(width, height)
        if uses_forest_layout(capability.plot_kind):
            return PlotExportGeometry(width, height, forest_measurement=partial(
                r_operations.forest_export_dimensions, params_path,
            ))
        if capability.regenerator != "forest":
            return PlotExportGeometry(width, height, check_layout=partial(
                self._check_publication_layout, params_path, capability.regenerator, height / width,
            ))
        with tempfile.TemporaryDirectory(prefix="rcms-export-size-") as directory:
            untitled = Path(directory) / "untitled.svg"
            self.export(regenerator=capability.regenerator, params_path=params_path, output_path=str(untitled),
                        include_title=False, outline_text=False)
            text_per_inch = (svg_text_points_per_inch(untitled, 1 / ratio),
                             svg_text_points_per_inch(path, 1 / ratio))
        return PlotExportGeometry(width, height, text_per_inch=text_per_inch)

    def _check_publication_layout(self, params_path: str, regenerator: PlotRegenerator,
                                  height_per_width: float, width: float, include_title: bool) -> None:
        with tempfile.TemporaryDirectory(prefix="rcms-export-size-") as directory:
            source = Path(directory) / "plot.svg"
            paths = r_operations.render_plot_bundle(
                params_path, regenerator, str(source), width=width, height=width * height_per_width,
                include_title=include_title, outline_text=False,
            )
            if not paths:
                raise PlotServiceError("Plot layout is unavailable.")
            if issue := plot_text_layout_issue(source):
                raise PlotServiceError(issue)

    def load_params(self, params_path: str) -> dict[str, object] | None:
        """Load persisted plot parameters, returning ``None`` when unavailable."""
        params = r_operations.load_plot_parameters(params_path)
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
            prepared = r_operations.prepare_plot_edit(
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

    def export_sized(self, *, capability: PlotCapability, params_path: str,
                     output_path: str, width: float, height: float, dpi: int,
                     include_title: bool = True, geometry: tuple[float, float] | None = None,
                     paginate_pdf: bool = True) -> None:
        """Render at publication dimensions without changing analysis state."""
        regenerator = capability.regenerator
        if regenerator not in ("forest", "none"):
            with staged_output(output_path) as temporary:
                paths = r_operations.render_plot_bundle(
                    params_path, regenerator, str(temporary), width=width, height=height, dpi=dpi,
                    include_title=include_title,
                )
                if not paths:
                    raise PlotServiceError(f"Stored {regenerator} plot bundle is incomplete: {params_path}")
            return
        forest_layout = uses_forest_layout(capability.plot_kind)
        if geometry is None and forest_layout:
            geometry = r_operations.forest_export_dimensions(params_path, width, include_title)
        if geometry is not None:
            height, minimum_width = geometry
            if width < minimum_width - 1e-8:
                raise PlotServiceError(f"Minimum width for this figure: {minimum_width * 25.4:.1f} mm")
        with tempfile.TemporaryDirectory(prefix='rcms-export-') as directory:
            source = Path(directory) / 'plot.svg'
            extension = Path(output_path).suffix.lower()
            if (geometry is not None and forest_layout
                    and extension == ".pdf" and height > A4_CONTENT_HEIGHT_INCHES and paginate_pdf):
                _export_paged_forest(params_path, source, output_path, width, geometry[1], include_title)
                return
            paths = r_operations.render_plot_bundle(
                params_path, regenerator, str(source), include_title=include_title, width=width,
            )
            if not paths:
                raise PlotServiceError(f"Stored {regenerator} plot bundle is incomplete: {params_path}")
            with staged_output(output_path) as temporary:
                if extension in (".svg", ".svgz"):
                    compose_export(lambda: _size_export_svg(source, temporary, width, height))
                else:
                    compose_export(lambda: _size_export_svg(source, source, width, height))
                    r_operations.export_svg_artwork(str(source), str(temporary), width, height, dpi)

    def export(
        self, *, regenerator: PlotRegenerator, params_path: str, output_path: str,
        include_title: bool = True, outline_text: bool = True,
    ) -> None:
        """Render a stored plot to an already validated destination path."""
        if regenerator == "none":
            raise PlotServiceError(f"Plot is not regeneratable: {regenerator}")
        with staged_output(output_path) as temporary:
            if not r_operations.render_plot_bundle(params_path, regenerator, str(temporary),
                                               include_title=include_title, outline_text=outline_text):
                raise PlotServiceError(f"Stored {regenerator} plot bundle is incomplete: {params_path}")


def _export_paged_forest(prefix: str, source: Path, destination: str, width: float,
                         minimum_width: float, include_title: bool) -> None:
    page_width = min(width, 180 / 25.4)
    if page_width < minimum_width - 1e-8:
        raise PlotServiceError("This figure is too wide for A4. Turn off A4 pages to export a single PDF page.")
    paths = r_operations.render_plot_bundle(
        prefix, "forest", str(source), include_title=include_title,
        width=page_width, page_height=250 / 25.4,
    )
    if not paths:
        raise PlotServiceError(f"Stored forest plot bundle is incomplete: {prefix}")
    with staged_output(destination) as temporary:
        compose_export(lambda: _write_a4_pdf(str(temporary), paths))


def _size_export_svg(source: Path, destination: Path, width: float, height: float) -> None:
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    tree = ET.parse(source)
    root = tree.getroot()
    root.set('width', f'{width}in')
    root.set('height', f'{height}in')
    x, y, view_width, view_height = map(float, root.attrib['viewBox'].split())
    paper_width = max(view_width, view_height * width / height)
    paper_height = max(view_height, view_width * height / width)
    x -= (paper_width - view_width) / 2
    y -= (paper_height - view_height) / 2
    root.set('viewBox', f'{x} {y} {paper_width} {paper_height}')
    root.insert(0, ET.Element('{http://www.w3.org/2000/svg}rect', {
        'x': str(x), 'y': str(y), 'width': str(paper_width), 'height': str(paper_height), 'fill': 'white',
    }))
    if destination.suffix.lower() == ".svgz":
        with gzip.open(destination, "wb") as stream:
            tree.write(stream, encoding='utf-8', xml_declaration=True)
    else:
        tree.write(destination, encoding='utf-8', xml_declaration=True)


def _write_a4_pdf(output: str, paths: tuple[str, ...]) -> None:
    writer = QPdfWriter(output)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageMargins(QMarginsF(15, 15, 15, 15))
    writer.setResolution(600)
    page = writer.pageLayout().paintRectPixels(writer.resolution())
    painter = QPainter(writer)
    if not painter.isActive():
        raise OSError("Could not start PDF export.")
    try:
        for index, path in enumerate(paths):
            check_export_cancelled()
            if index:
                writer.newPage()
            svg = QSvgRenderer(svg_bytes_for_qt(path))
            bounds = svg.viewBoxF()
            scale = min(writer.resolution() / 72, page.width() / bounds.width(), page.height() / bounds.height())
            w, h = bounds.width() * scale, bounds.height() * scale
            svg.render(painter, QRectF((page.width() - w) / 2, 0, w, h))
    finally:
        painter.end()


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
