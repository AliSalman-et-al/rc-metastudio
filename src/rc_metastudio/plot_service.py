# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Own persisted plot editing and export operations at the R boundary."""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Callable, Protocol, cast

from rc_metastudio import r_bridge
from rc_metastudio.analysis_results import PlotRegenerator


class PlotServiceError(RuntimeError):
    """Raised when a persisted plot cannot be edited or exported."""


class PlotBackend(Protocol):
    def load_vars_for_plot(
        self, params_path: str, return_params_dict: bool = False
    ) -> object: ...

    def update_plot_params(
        self,
        plot_params: Mapping[str, object],
        plot_params_name: str = "params",
        write_them_out: bool = False,
        outpath: str | None = None,
    ) -> object: ...

    def regenerate_plot_data(self) -> object: ...

    def regenerate_regression_plot_data(self) -> object: ...

    def regenerate_small_study_effects_funnel(
        self, params_path: str, output_path: str | None = None
    ) -> object: ...

    def load_in_r(self, fpath: str) -> object: ...

    def generate_forest_plot(self, file_path: str) -> object: ...

    def generate_reg_plot(self, file_path: str) -> object: ...

    def generate_sroc_plot(self, file_path: str) -> object: ...

    def generate_small_study_effects_funnel(self, file_path: str) -> object: ...

    def write_out_plot_data(
        self, params_out_path: str, plot_data_name: str = "plot.data"
    ) -> object: ...


class PlotService:
    """Apply plot edits and render exports without leaking R into the UI."""

    def __init__(self, bridge: PlotBackend | None = None) -> None:
        self.bridge = bridge if bridge is not None else cast(PlotBackend, r_bridge)

    def load_params(self, params_path: str) -> dict[str, object] | None:
        """Load persisted plot parameters, returning ``None`` when unavailable."""
        params = self.bridge.load_vars_for_plot(params_path, return_params_dict=True)
        if params is False:
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
        if regenerator == "funnel":
            self._apply_funnel_edits(
                params_path, updated_params, output_path, self.bridge
            )
            return
        if regenerator == "forest":
            self._apply_standard_edits(
                params_path,
                updated_params,
                output_path,
                bridge=self.bridge,
                regenerate=self.bridge.regenerate_plot_data,
                generate=self.bridge.generate_forest_plot,
                output_param="fp_outpath",
                display_param="fp_display_path",
            )
            return
        if regenerator == "regression":
            self._apply_standard_edits(
                params_path,
                updated_params,
                output_path,
                bridge=self.bridge,
                regenerate=self.bridge.regenerate_regression_plot_data,
                generate=self.bridge.generate_reg_plot,
                output_param="bp_outpath",
                display_param="bp_display_path",
            )
            return
        if regenerator == "sroc":
            self._apply_standard_edits(
                params_path,
                updated_params,
                output_path,
                bridge=self.bridge,
                regenerate=self.bridge.regenerate_plot_data,
                generate=self.bridge.generate_sroc_plot,
                output_param="fp_outpath",
                display_param="fp_display_path",
            )
            return
        raise PlotServiceError("Plot is not editable: %s" % regenerator)

    def export(
        self, *, regenerator: PlotRegenerator, params_path: str, output_path: str
    ) -> None:
        """Render a stored plot to an already validated destination path."""
        if regenerator == "funnel":
            self.bridge.load_vars_for_plot(params_path)
            self.bridge.generate_small_study_effects_funnel(output_path)
            return
        if regenerator == "forest":
            self.bridge.load_in_r("%s.plotdata" % params_path)
            self.bridge.generate_forest_plot(output_path)
            return
        if regenerator == "regression":
            self.bridge.load_in_r("%s.plotdata" % params_path)
            self.bridge.generate_reg_plot(output_path)
            return
        if regenerator == "sroc":
            self.bridge.load_in_r("%s.plotdata" % params_path)
            self.bridge.generate_sroc_plot(output_path)
            return
        raise PlotServiceError("Plot is not regeneratable: %s" % regenerator)

    @staticmethod
    def _apply_standard_edits(
        params_path: str,
        updated_params: Mapping[str, object],
        output_path: str,
        *,
        bridge: PlotBackend,
        regenerate: Callable[[], object],
        generate: Callable[[str], object],
        output_param: str,
        display_param: str,
    ) -> None:
        target_path = Path(output_path)
        transaction_dir = Path(
            tempfile.mkdtemp(prefix=".rcms-plot-", dir=str(target_path.parent))
        )
        temporary_base = transaction_dir / "plot"
        temporary_output = transaction_dir / (
            "render" + (target_path.suffix or ".png")
        )
        original_display = updated_params.get(display_param)
        display_target = (
            Path(str(original_display))
            if isinstance(original_display, str) and original_display
            else None
        )
        temporary_display = (
            transaction_dir / "display.svg" if display_target is not None else None
        )
        final_params = transaction_dir / "final.params"
        persisted_params = Path(f"{params_path}.params")
        persisted_plotdata = Path(f"{params_path}.plotdata")
        targets = [persisted_params, persisted_plotdata, target_path]
        if display_target is not None:
            target_keys = {
                os.path.normcase(os.path.abspath(str(path))) for path in targets
            }
            if os.path.normcase(os.path.abspath(str(display_target))) not in target_keys:
                targets.append(display_target)
        backups: dict[Path, Path] = {}
        promotion_started = False
        try:
            for index, path in enumerate(targets):
                if not path.exists():
                    continue
                backup = transaction_dir / f"backup-{index}"
                shutil.copyfile(path, backup)
                backups[path] = backup

            # Keep all writes in the scratch directory until R has regenerated
            # and rendered the candidate. The persisted config and artifact
            # therefore remain the last-good pair on every failure path.
            candidate_params = dict(updated_params)
            candidate_params[output_param] = str(temporary_output)
            if temporary_display is not None:
                candidate_params[display_param] = str(temporary_display)
            bridge.update_plot_params(
                candidate_params,
                write_them_out=True,
                outpath=f"{temporary_base}.params",
            )
            regenerate()
            generate(str(temporary_output))

            # The candidate paths are only for rendering. Persist the user's
            # actual paths after the candidate has succeeded, while keeping
            # the R session aligned with the committed parameter file.
            bridge.update_plot_params(
                dict(updated_params),
                write_them_out=True,
                outpath=str(final_params),
            )
            regenerate()
            bridge.write_out_plot_data(str(temporary_base))

            promotion_started = True
            os.replace(str(final_params), str(persisted_params))
            os.replace(str(temporary_base) + ".plotdata", str(persisted_plotdata))
            os.replace(str(temporary_output), str(target_path))
            if temporary_display is not None and display_target is not None:
                os.replace(str(temporary_display), str(display_target))
        except Exception as error:
            if promotion_started:
                PlotService._restore_standard_files(targets, backups, error)
            raise
        finally:
            shutil.rmtree(transaction_dir, ignore_errors=True)

    @staticmethod
    def _restore_standard_files(
        targets: Sequence[Path],
        backups: Mapping[Path, Path],
        original_error: Exception,
    ) -> None:
        """Restore each last-good standard plot file without hiding the error."""
        for path in targets:
            backup = backups.get(path)
            try:
                if backup is not None and backup.exists():
                    shutil.copyfile(backup, path)
                elif backup is None and path.exists():
                    path.unlink()
            except OSError as restore_error:
                original_error.add_note(
                    "Plot rollback failed for %s: %s" % (path, restore_error)
                )

    @staticmethod
    def _apply_funnel_edits(
        params_path: str,
        updated_params: Mapping[str, object],
        output_path: str,
        bridge: PlotBackend,
    ) -> None:
        target_path = Path(output_path)
        if target_path.suffix.lower() == ".svgz":
            raise ValueError(
                "SVGZ output is not supported when editing funnel plots; use SVG instead."
            )

        transaction_dir = Path(
            tempfile.mkdtemp(prefix=".rcms-funnel-", dir=str(target_path.parent))
        )
        temporary_base = transaction_dir / "plot"
        temporary_output = transaction_dir / (
            "render" + (target_path.suffix or ".png")
        )
        persisted_params = Path("%s.params" % params_path)
        persisted_backup = transaction_dir / "params.backup"
        had_persisted_params = persisted_params.exists()
        try:
            for suffix in ("data", "res"):
                source = Path("%s.%s" % (params_path, suffix))
                shutil.copyfile(source, "%s.%s" % (temporary_base, suffix))
            bridge.update_plot_params(
                dict(updated_params),
                plot_params_name="params",
                write_them_out=True,
                outpath="%s.params" % temporary_base,
            )
            if had_persisted_params:
                shutil.copyfile(persisted_params, persisted_backup)
            bridge.regenerate_small_study_effects_funnel(
                str(temporary_base), output_path=str(temporary_output)
            )
            bridge.update_plot_params(
                dict(updated_params),
                plot_params_name="params",
                write_them_out=True,
                outpath=str(persisted_params),
            )
            os.replace(str(temporary_output), str(target_path))
        except Exception as error:
            PlotService._restore_params(
                persisted_params,
                persisted_backup,
                had_persisted_params,
                error,
            )
            raise
        finally:
            shutil.rmtree(transaction_dir, ignore_errors=True)

    @staticmethod
    def _restore_params(
        persisted_params: Path,
        persisted_backup: Path,
        had_persisted_params: bool,
        original_error: Exception,
    ) -> None:
        """Restore the parameter file without hiding the rendering failure."""
        try:
            if had_persisted_params and persisted_backup.exists():
                shutil.copyfile(persisted_backup, persisted_params)
            elif not had_persisted_params and persisted_params.exists():
                persisted_params.unlink()
        except OSError as restore_error:
            original_error.add_note(
                "Plot parameter rollback failed: %s" % restore_error
            )


__all__ = ["PlotService", "PlotServiceError"]
