# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Own persisted plot editing and export operations at the R boundary."""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path

from rc_metastudio import r_bridge
from rc_metastudio.plot_capabilities import PlotRegenerator
from rc_metastudio.r_call_serialization import serialized_r_call


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
                     include_title: bool = True) -> None:
        """Render at publication dimensions without changing analysis state."""
        if regenerator == "trial_sequential":
            if not r_bridge.render_plot_bundle(params_path, regenerator, output_path, width, height, dpi,
                                               include_title=include_title):
                raise PlotServiceError(f"Stored {regenerator} plot bundle is incomplete: {params_path}")
            return
        from xml.etree import ElementTree as ET
        with tempfile.TemporaryDirectory(prefix='rcms-export-') as directory:
            source = Path(directory) / 'plot.svg'
            if not r_bridge.render_plot_bundle(params_path, regenerator, str(source), include_title=include_title):
                raise PlotServiceError(f"Stored {regenerator} plot bundle is incomplete: {params_path}")
            ET.register_namespace('', 'http://www.w3.org/2000/svg')
            ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
            tree = ET.parse(source)
            root = tree.getroot()
            root.set('width', f'{width}in')
            root.set('height', f'{height}in')
            tree.write(source, encoding='utf-8', xml_declaration=True)
            if Path(output_path).suffix.lower() == '.svgz':
                import gzip
                with source.open('rb') as input_file, gzip.open(output_path, 'wb') as output_file:
                    shutil.copyfileobj(input_file, output_file)
            elif Path(output_path).suffix.lower() == '.svg':
                shutil.copyfile(source, output_path)
            else:
                r_bridge.export_svg_artwork(str(source), output_path, width, height, dpi)

    @serialized_r_call
    def export(
        self, *, regenerator: PlotRegenerator, params_path: str, output_path: str
    ) -> None:
        """Render a stored plot to an already validated destination path."""
        if regenerator == "none":
            raise PlotServiceError(f"Plot is not regeneratable: {regenerator}")
        if not r_bridge.render_plot_bundle(params_path, regenerator, output_path):
            raise PlotServiceError(f"Stored {regenerator} plot bundle is incomplete: {params_path}")


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
