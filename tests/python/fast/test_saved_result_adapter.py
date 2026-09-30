# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""A project can reopen captured figures after their original files disappear."""

from pathlib import Path
from typing import cast

from PyQt6.QtGui import QImage

from rc_metastudio import saved_result_adapter


def _result(path: Path) -> dict[str, object]:
    return {
        "version": 1,
        "texts": {"summary": "Two-arm result"},
        "images": {"forest": str(path)},
        "display_images": {"forest": str(path)},
        "image_params_paths": {"forest": "temporary-plot-data"},
        "plot_capabilities": {
            "forest": {
                "plot_kind": "forest",
                "editable": True,
                "styleable": True,
                "composition": "single",
                "regenerator": "forest",
            }
        },
        "sections": [
            {
                "id": "summary",
                "kind": "text",
                "order": 0,
                "title": "Summary",
                "source_key": "summary",
            },
            {
                "id": "forest",
                "kind": "image",
                "order": 1,
                "title": "Forest plot",
                "source_key": "forest",
            },
        ],
    }


def test_captured_figure_reopens_without_its_source_file(tmp_path):
    source = tmp_path / "worker-forest.png"
    image = QImage(2, 2, QImage.Format.Format_ARGB32)
    image.fill(0xFF225588)
    assert image.save(str(source), "PNG")
    display = tmp_path / "worker-forest.svg"
    vector = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="2" height="2"/></svg>'
    display.write_bytes(vector)
    original = _result(source)
    display_images = original["display_images"]
    assert isinstance(display_images, dict)
    assert all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in display_images.items()
    )
    cast(dict[str, str], display_images)["forest"] = str(display)

    record = saved_result_adapter.capture_result(
        {"outcome": "Mortality", "study_ids": [1, 2]},
        {
            "method": "Inverse variance",
            "measure": "OR",
            "params": {
                "conf.level": 95,
                "fp_outpath": str(source),
                "fp_style": "classic",
            },
        },
        original,
        backend_versions={"R": "4.3.3", "RCMetaR": "0.4.1"},
    )
    source.unlink()
    display.unlink()
    # Simulate an otherwise valid archive carrying old machine-local plot data.
    results = record.value["results"]
    assert isinstance(results, dict)
    results["image_params_paths"] = {
        "forest": "/tmp/unrelated-plot-data"
    }
    capabilities = results["plot_capabilities"]
    assert isinstance(capabilities, dict)
    forest = capabilities["forest"]
    assert isinstance(forest, dict)
    restored = saved_result_adapter.restore_result(record, tmp_path / "reopened")

    original_images = original["images"]
    assert isinstance(original_images, dict)
    assert all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in original_images.items()
    )
    assert cast(dict[str, str], original_images)["forest"] == str(source)
    stored_images = results["images"]
    assert isinstance(stored_images, dict)
    assert isinstance(stored_images["forest"], str)
    assert stored_images["forest"].startswith("assets/")
    figures = record.value["figures"]
    assert isinstance(figures, list)
    assert len(figures) == 2
    assert QImage(restored.images["forest"]).width() == 2
    assert Path(restored.display_images["forest"]).read_bytes() == vector
    assert restored.plot_capabilities["forest"].editable is False
    assert restored.plot_capabilities["forest"].regenerator == "forest"
    assert restored.image_params_paths == {}
    specification = record.value["specification"]
    assert isinstance(specification, dict)
    assert specification["params"] == {"conf.level": 95}
    assert record.value["presentation"] == {"fp_style": "classic"}


def test_saved_figure_update_changes_only_portable_appearance(tmp_path):
    source = tmp_path / "worker-forest.png"
    image = QImage(2, 2, QImage.Format.Format_ARGB32)
    image.fill(0xFF225588)
    assert image.save(str(source), "PNG")
    record = saved_result_adapter.capture_result(
        {"outcome": "Mortality", "study_ids": [1, 2]},
        {
            "version": 1,
            "method": "Inverse variance",
            "metric": "OR",
            "params": {"conf.level": 95, "fp_outpath": str(source), "fp_xlabel": "Effect"},
        },
        _result(source),
        backend_versions={"R": "4.3.3", "RCMetaR": "0.4.1"},
    )
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="3" height="3"/></svg>'
    candidate_path = tmp_path / "updated-forest.png"
    updated_image = QImage(3, 3, QImage.Format.Format_ARGB32)
    updated_image.fill(0xFFAA3366)
    assert updated_image.save(str(candidate_path), "PNG")
    png_candidate = candidate_path.read_bytes()
    updated = saved_result_adapter.replace_saved_figure(
        record,
        "forest",
        png_candidate,
        "image/png",
        display_data=svg,
        display_media_type="image/svg+xml",
        presentation_update={"fp_xlabel": "Qualification effect direction", "fp_outpath": "/tmp/local.png"},
    )

    assert updated.value["id"] == record.value["id"]
    assert updated.value["input_identity"] == record.value["input_identity"]
    assert updated.value["specification_identity"] == record.value["specification_identity"]
    assert updated.value["created_at"] == record.value["created_at"]
    assert updated.value["presentation"]["fp_xlabel"] == "Qualification effect direction"
    assert "fp_outpath" not in updated.value["presentation"]
    assert record.value["presentation"] == {"fp_xlabel": "Effect"}
    old_results = record.value["results"]
    new_results = updated.value["results"]
    assert old_results["texts"] == new_results["texts"]
    assert old_results["images"]["forest"] != new_results["images"]["forest"]
    assert record.value["specification"]["params"] == {"conf.level": 95}

    restored = saved_result_adapter.restore_result(updated, tmp_path / "updated")
    assert Path(restored.display_images["forest"]).read_bytes() == svg
    assert restored.plot_capabilities["forest"].regenerator == "forest"


def test_missing_figure_is_preserved_as_partial_result(tmp_path):
    missing = tmp_path / "missing.svg"
    record = saved_result_adapter.capture_result(
        {"outcome": "Mortality"},
        {"measure": "OR"},
        _result(missing),
        backend_versions={"R": "4.3.3"},
    )

    restored = saved_result_adapter.restore_result(record, tmp_path / "reopened")

    assert record.value["status"] == "partial"
    assert record.value["figures"] == []
    warnings = record.value["warnings"]
    assert isinstance(warnings, list)
    assert isinstance(warnings[0], str)
    assert "unavailable" in warnings[0]
    assert restored.images["forest"] == ""
    assert restored.sections[1].semantic_id == "forest"


def test_independent_sequential_recovery_marks_missing_native_figure_partial():
    result = {
        "version": 1,
        "texts": {"sequential_recovery": "Native sequence failed; individual fits were retained."},
        "sections": [{
            "id": "sequential-recovery", "kind": "text", "order": 0,
            "title": "Incomplete sequence", "source_key": "sequential_recovery",
        }],
        "leave_one_out_numerics": {"version": 1, "rows": [{"status": "available"}]},
    }

    record = saved_result_adapter.capture_result(
        {"outcome": "Mortality"},
        {"workflow": "leave-one-out", "method": "binary.random", "metric": "OR"},
        result,
        backend_versions={"R": "4.6.1"},
    )

    assert record.value["status"] == "partial"
    warnings = record.value["warnings"]
    assert isinstance(warnings, list)
    assert isinstance(warnings[0], str)
    assert "figure was unavailable" in warnings[0]
