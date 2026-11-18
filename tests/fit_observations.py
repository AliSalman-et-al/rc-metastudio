"""Capture one real analysis fit for an independent R oracle."""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from rc_metastudio import r_bridge
from rc_metastudio.r_call_serialization import r_transaction


class FitObservation:
    def __init__(self, results: list[object]) -> None:
        self._results = results

    def evaluate(self, expression: str):
        """Evaluate an oracle with the observed fit bound locally as `result`."""
        result, = self._results
        with r_transaction():
            bindings = r_bridge.ro.ListVector({"result": result})
            parsed = r_bridge.execute_r_function("parse", text=expression)
            return r_bridge.execute_r_function("eval", parsed, bindings, r_bridge.ro.globalenv)

    def save(self, path: Path) -> None:
        result, = self._results
        r_bridge.execute_r_function("saveRDS", result, file=str(path))


@contextmanager
def observe_fit() -> Generator[FitObservation]:
    parse = r_bridge.parse_out_results
    results: list[object] = []

    def observe(raw_result):
        parsed = parse(raw_result)
        results.append(raw_result)
        return parsed

    with patch.object(r_bridge, "parse_out_results", side_effect=observe):
        yield FitObservation(results)
    assert len(results) == 1, f"Expected one successful R fit, observed {len(results)}"
