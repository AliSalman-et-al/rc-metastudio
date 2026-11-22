from pathlib import Path

import pytest
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()

from rc_metastudio import app_error_handler
from rc_metastudio.results import (
    funnel_editor as funnel_plot_editor_dialog,
    plot_service,
    window as results_window,
)
from rc_metastudio.results.contract import parse_analysis_result
from rc_metastudio.results.plot_capabilities import PlotCapability
from rc_metastudio.results.funnel_editor import FunnelPlotEditorDialog


def _params(kind):
    return {
        "funnel.kind": kind,
        "metric": "OR",
        "trim.and.fill.estimator": "L0",
        "trim.and.fill.side": "left",
        "deeks.ess": [12.0, 20.0],
        "funnel.point.size": 1.0,
        "funnel.label.policy": "none",
    }


def _funnel_capability():
    return PlotCapability("funnel", True, True, "funnel")


def test_funnel_editor_preserves_statistical_params_and_updates_presentation(qapp):
    dialog = FunnelPlotEditorDialog(
        _params("ordinary"), "ordinary.png", plot_type="funnel"
    )
    try:
        dialog.point_size_spin.setValue(2.0)
        dialog.point_color_edit.setText("#123456")
        dialog.label_policy_combo.setCurrentText("All")
        dialog.reference_visible_check.setChecked(False)
        params = dialog.plot_params()
        assert params["trim.and.fill.estimator"] == "L0"
        assert params["trim.and.fill.side"] == "left"
        assert params["deeks.ess"] == [12.0, 20.0]
        assert params["funnel.kind"] == "ordinary"
        assert params["funnel.point.size"] == 2.0
        assert params["funnel.point.color"] == "#123456"
        assert params["funnel.label.policy"] == "all"
        assert params["funnel.reference.visible"] is False
    finally:
        dialog.close()


def test_funnel_editor_supports_visual_presets_symbols_and_color_picker(
    qapp, monkeypatch
):
    dialog = FunnelPlotEditorDialog(
        _params("ordinary"), "ordinary.png", plot_type="funnel"
    )
    monkeypatch.setattr(
        funnel_plot_editor_dialog.QColorDialog,
        "getColor",
        lambda *args, **kwargs: QColor("#AABBCC"),
    )
    try:
        dialog.style_combo.setCurrentText("BMJ")
        assert dialog.point_color_edit.text() == "#6B58A6"
        assert dialog.reference_color_edit.text() == "#6B58A6"
        assert dialog.region_color_edit.text() == "#E8E2F4"
        assert dialog.point_symbol_combo.currentText() == "Diamond"
        dialog.background_color_button.click()

        params = dialog.plot_params()
        assert params["funnel.style"] == "bmj"
        assert params["funnel.point.symbol"] == 18
        assert params["funnel.background.color"] == "#AABBCC"
        swatch = next(label for label in dialog.findChildren(QLabel) if label.accessibleName() == 'Funnel plot background color swatch')
        rendered = swatch.grab().toImage()
        assert rendered.pixelColor(rendered.width() // 2, rendered.height() // 2) == QColor('#AABBCC')
    finally:
        dialog.close()


def test_funnel_editor_disables_inapplicable_controls_by_kind(qapp):
    contour = FunnelPlotEditorDialog(
        _params("contour"), "contour.png", plot_type="contour_funnel"
    )
    deeks = FunnelPlotEditorDialog(
        _params("deeks"), "deeks.png", plot_type="deeks_funnel"
    )
    trimfill = FunnelPlotEditorDialog(
        _params("trimfill"), "trimfill.png", plot_type="trimfill_funnel"
    )
    try:
        assert contour.contour_levels_edit.isEnabled()
        assert not contour.sampling_region_check.isEnabled()
        assert (
            deeks.label_policy_combo.findText("Outside pseudo-confidence region") == -1
        )
        assert not deeks.sampling_confidence_spin.isEnabled()
        assert deeks.regression_visible_check.isEnabled()
        assert trimfill.rerun_note.text() == "Rerun the analysis to change statistical settings."
    finally:
        for dialog in (contour, deeks, trimfill):
            dialog.close()


def test_funnel_editor_rejects_kind_descriptor_mismatch(qapp):
    try:
        FunnelPlotEditorDialog(_params("trimfill"), "ordinary.png", plot_type="funnel")
    except ValueError as error:
        assert "does not match" in str(error)
    else:
        raise AssertionError("mismatched funnel descriptor was accepted")


def test_funnel_editor_reads_persisted_second_plot_settings_by_index(qapp):
    params = _params("contour")
    params.update(
        {
            "funnel.index": 2,
            "funnel.point.size": [1.0, 2.0],
            "funnel.label.policy": ["none", "all"],
            "funnel.xlab": ["first", "second"],
            "funnel.ylab": ["one", "two"],
        }
    )
    dialog = FunnelPlotEditorDialog(params, "contour.png", plot_type="contour_funnel")
    try:
        assert dialog.point_size_spin.value() == 2.0
        assert dialog.label_policy_combo.currentText() == "All"
        assert dialog.x_label_edit.text() == "second"
        assert dialog.y_label_edit.text() == "two"
    finally:
        dialog.close()


def test_funnel_editor_prefers_persisted_output_path_on_reopen(qapp, tmp_path):
    persisted = tmp_path / "edited-funnel.png"
    dialog = FunnelPlotEditorDialog(
        {**_params("ordinary"), "funnel.outpath": str(persisted)},
        str(tmp_path / "original-funnel.png"),
        plot_type="funnel",
    )
    try:
        assert dialog.plot_params()["funnel.outpath"] == str(persisted)
    finally:
        dialog.close()


def test_funnel_editor_apply_then_ok_does_not_regenerate_twice(qapp):
    applied = []
    dialog = FunnelPlotEditorDialog(
        _params("ordinary"), "ordinary.png", plot_type="funnel", on_commit=applied.append
    )
    try:
        apply_button = dialog.button_box.button(QDialogButtonBox.StandardButton.Apply)
        ok_button = dialog.button_box.button(QDialogButtonBox.StandardButton.Ok)
        assert apply_button is not None
        assert ok_button is not None
        apply_button.click()
        assert len(applied) == 1
        ok_button.click()
        assert len(applied) == 1
        assert dialog.result() == QDialog.DialogCode.Accepted
    finally:
        dialog.close()


@pytest.mark.parametrize("change", ["point-size", "caption", "label-policy"])
def test_funnel_editor_ok_commits_new_change_and_closes(qapp, change):
    applied = []
    dialog = FunnelPlotEditorDialog(
        _params("ordinary"), "ordinary.png", plot_type="funnel", on_commit=applied.append
    )
    try:
        if change == "caption":
            dialog.figure_caption.setText("Only the caption changed")
            key, expected = "plot_caption", "Only the caption changed"
        elif change == "label-policy":
            dialog.label_policy_combo.setCurrentText("All")
            key, expected = "funnel.label.policy", "all"
        else:
            dialog.point_size_spin.setValue(2.0)
            key, expected = "funnel.point.size", 2.0
        ok_button = dialog.button_box.button(QDialogButtonBox.StandardButton.Ok)
        assert ok_button is not None
        ok_button.click()
        assert len(applied) == 1
        assert applied[0][key] == expected
        assert dialog.result() == QDialog.DialogCode.Accepted
    finally:
        dialog.close()


@pytest.mark.parametrize("kind,fields", [
    ("ordinary", {"x_lower_edit": "0"}),
    ("ordinary", {"x_lower_edit": "2", "x_upper_edit": "1"}),
    ("ordinary", {"x_lower_edit": "NaN", "x_upper_edit": "2"}),
    ("ordinary", {"x_ticks_edit": "0,wrong,2"}),
    ("ordinary", {"x_ticks_edit": "0,Inf"}),
    ("contour", {"contour_levels_edit": "90,wrong,99"}),
    ("contour", {"contour_levels_edit": "0,95"}),
    ("contour", {"contour_levels_edit": "100"}),
    ("contour", {"contour_levels_edit": ""}),
])
def test_funnel_editor_rejects_ignored_numeric_edits(qapp, kind, fields):
    dialog = FunnelPlotEditorDialog(_params(kind), "funnel.png", plot_type="contour_funnel" if kind == "contour" else "funnel")
    try:
        for name, value in fields.items():
            getattr(dialog, name).setText(value)
        with pytest.raises(ValueError):
            dialog.plot_params()
    finally:
        dialog.close()


def test_funnel_editor_invalid_ok_stays_open_and_recovers(qapp, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox

    applied, warnings = [], []
    dialog = FunnelPlotEditorDialog(
        _params("ordinary"), "funnel.png", plot_type="funnel", on_commit=applied.append
    )
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args[2]))
    try:
        dialog.show()
        ok = dialog.button_box.button(QDialogButtonBox.StandardButton.Ok)
        assert ok is not None
        dialog.x_lower_edit.setText("0")
        ok.click()
        assert dialog.isVisible()
        assert warnings and not applied
        dialog.x_upper_edit.setText("2")
        dialog.x_ticks_edit.setText("0,1,2")
        ok.click()
        assert dialog.result() == QDialog.DialogCode.Accepted
        assert len(applied) == 1
        assert applied[0]["funnel.xlim.lower"] == "0"
    finally:
        dialog.close()


def test_funnel_editor_failed_ok_stays_open_and_retries_the_draft(qapp, monkeypatch):
    applied, errors = [], []

    def commit(params):
        applied.append(params["funnel.point.size"])
        if len(applied) == 1:
            raise RuntimeError("render failed")

    monkeypatch.setattr(
        app_error_handler, "handle_exception", lambda _type, error, _traceback, **_kw: errors.append(str(error))
    )
    dialog = FunnelPlotEditorDialog(
        _params("ordinary"), "ordinary.png", plot_type="funnel", on_commit=commit
    )
    try:
        dialog.show()
        dialog.point_size_spin.setValue(2.0)
        ok_button = dialog.button_box.button(QDialogButtonBox.StandardButton.Ok)
        assert ok_button is not None
        ok_button.click()
        assert dialog.isVisible()
        assert errors == ["render failed"]
        ok_button.click()
        assert dialog.result() == QDialog.DialogCode.Accepted
        assert applied == [2.0, 2.0]
    finally:
        dialog.close()


def test_funnel_editor_failed_second_apply_preserves_last_good_artifacts(
    qapp, monkeypatch, tmp_path
):
    base = tmp_path / "funnel"
    params_path = Path(str(base) + ".params")
    params_path.write_text("initial", encoding="utf-8")
    Path(str(base) + ".data").write_text("data", encoding="utf-8")
    Path(str(base) + ".res").write_text("res", encoding="utf-8")
    image_path = tmp_path / "funnel.png"
    image_path.write_bytes(b"old image")
    artifact = results_window.PlotArtifact(
        "Ordinary Funnel Plot",
        str(image_path),
        _funnel_capability(),
        params_path=str(base),
    )
    window = results_window.ResultsWindow(parse_analysis_result({"version": 1, "sections": []}))
    regenerate_count = [0]

    def prepare(_prefix, regenerator, changed, output, directory):
        assert regenerator == "funnel"
        regenerate_count[0] += 1
        if regenerate_count[0] != 1:
            raise RuntimeError("render failed")
        staged_params = Path(directory) / "funnel.params"
        staged_render = Path(directory) / "funnel.png"
        staged_params.write_text(repr(sorted(changed.items())), encoding="utf-8")
        staged_render.write_bytes(b"first good image")
        return {str(params_path): str(staged_params), output: str(staged_render)}

    monkeypatch.setattr(plot_service.r_operations, "prepare_plot_edit", prepare)
    errors = []
    monkeypatch.setattr(
        app_error_handler, "handle_exception", lambda _type, error, _traceback, **_kw: errors.append(str(error))
    )
    dialog = FunnelPlotEditorDialog(
        {"funnel.kind": "ordinary", "funnel.point.size": 1.0},
        str(image_path),
        plot_type="funnel",
        on_commit=lambda parameters: window._apply_plot_edits(parameters, artifact, None),
    )
    try:
        dialog.show()
        apply_button = dialog.button_box.button(QDialogButtonBox.StandardButton.Apply)
        assert apply_button is not None
        dialog.point_size_spin.setValue(2.0)
        apply_button.click()
        assert regenerate_count == [1]
        assert image_path.read_bytes() == b"first good image"
        import ast
        persisted = dict(ast.literal_eval(params_path.read_text(encoding="utf-8")))
        assert float(persisted["funnel.point.size"]) == 2.0
        committed_params = params_path.read_bytes()
        committed_image = image_path.read_bytes()
        dialog.point_size_spin.setValue(3.0)
        apply_button.click()
        assert errors == ["render failed"]
        assert params_path.read_bytes() == committed_params
        assert image_path.read_bytes() == committed_image
        assert dialog.isVisible()
    finally:
        dialog.close()


def test_funnel_editor_rejects_svgz_output_path(qapp, tmp_path):
    output = tmp_path / "edited-funnel.svgz"
    output.write_bytes(b"previous export")
    artifact = results_window.PlotArtifact(
        "Ordinary Funnel Plot",
        "funnel.png",
        _funnel_capability(),
        params_path="funnel",
    )
    window = results_window.ResultsWindow(parse_analysis_result({"version": 1, "sections": []}))
    dialog = FunnelPlotEditorDialog(
        {**_params("ordinary"), "funnel.outpath": str(output)},
        artifact.image_path,
        plot_type="funnel",
    )
    try:
        with pytest.raises(ValueError, match="SVGZ output is not supported"):
            window._apply_plot_edits(dialog.plot_params(), artifact, None)
        assert output.read_bytes() == b"previous export"
    finally:
        dialog.close()
