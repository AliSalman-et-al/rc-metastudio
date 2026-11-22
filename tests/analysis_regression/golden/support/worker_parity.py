"""Compare every model result field across both live R backends."""

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
import json
import os
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from rc_metastudio import r_bridge, r_worker
from tests.analysis_regression.golden.support import golden_analysis, headless_analysis


def comparable(value):
    if is_dataclass(value):
        return {field.name: comparable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {key: comparable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [comparable(item) for item in value]
    if isinstance(value, str) and Path(value).is_absolute() and "\n" not in value:
        suffix = Path(value).suffix
        return {"artifact": suffix}
    return value


def capture(output: Path) -> None:
    app = QApplication([])
    r_bridge.load_required_packages()
    worker = r_worker.current_worker()
    worker.ensure_ready()
    try:
        capture_cases(output)
    finally:
        worker.close()
        app.quit()


def capture_cases(output: Path) -> list[str]:
    output.mkdir(parents=True, exist_ok=True)
    cases = golden_analysis.curated_golden_bundles()
    assert len(cases) == 11
    matched = []
    for case in cases:
        values = {}
        for backend in ("embedded", "worker"):
            with patch.dict(os.environ, {"RCMS_R_BACKEND": backend}):
                result = headless_analysis.run_headless_analysis(case["case"])
            values[backend] = comparable(result)
        (output / f"{case['id']}.json").write_text(
            json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        assert values["worker"] == values["embedded"], case["id"]
        print(case["id"], "full payload matched", flush=True)
        matched.append(case["id"])
    return matched
