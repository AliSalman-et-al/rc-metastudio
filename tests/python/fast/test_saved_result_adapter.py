# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""A project can reopen captured figures after their original files disappear."""

from pathlib import Path

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
    original["display_images"]["forest"] = str(display)

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
    record.value["results"]["image_params_paths"] = {
        "forest": "/tmp/unrelated-plot-data"
    }
    record.value["results"]["plot_capabilities"]["forest"].update(
        editable=True, styleable=True, regenerator="forest"
    )
    restored = saved_result_adapter.restore_result(record, tmp_path / "reopened")

    assert original["images"]["forest"] == str(source)
    assert record.value["results"]["images"]["forest"].startswith("assets/")
    assert len(record.value["figures"]) == 2
    assert QImage(restored.images["forest"]).width() == 2
    assert Path(restored.display_images["forest"]).read_bytes() == vector
    assert restored.plot_capabilities["forest"].editable is False
    assert restored.image_params_paths == {}
    assert record.value["specification"]["params"] == {"conf.level": 95}
    assert record.value["presentation"] == {"fp_style": "classic"}


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
    assert "unavailable" in record.value["warnings"][0]
    assert restored.images["forest"] == ""
    assert restored.sections[1].semantic_id == "forest"
