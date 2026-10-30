"""Pre-migration numerical capture; assertions use the existing frozen gates."""

import hashlib
import json
import os
from pathlib import Path

from tests.analysis_regression.golden.support.golden_analysis import parsed_numeric_sections


def run(app, window, record, analyze):
    output = Path(os.environ["RCMS_SHEETS_BASELINE"])
    inventory = json.loads((output / "inventory.json").read_text())
    results = []
    for sample in inventory["samples"]:
        source = output / "originals" / sample["file"]
        assert window.open(str(source), raise_on_error=True)
        for pair in sample["pairs"]:
            window.display_outcome(pair["outcome"], follow_up_name=pair["follow_up"])
            app.processEvents()
            family = window.model.get_current_outcome_type()
            method = family + ".random"
            view = analyze(app, window, method)
            sections = parsed_numeric_sections(view.results)
            assert sections, (sample["file"], pair)
            result = {"file": sample["file"], "pair": pair, "method": method,
                      "metric": window.model.current_effect, "sections": sections}
            results.append(result)
            record("sample-pair-numerics", view, **result)
            view.close()
            app.processEvents()
        assert hashlib.sha256(source.read_bytes()).hexdigest() == sample["sha256"]
    (output / "numerics.json").write_text(json.dumps(results, indent=2) + "\n")
