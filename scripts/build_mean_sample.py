# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build an illustrative one-arm Mean project with synthetic measurements."""

import hashlib
import json
from pathlib import Path

from rc_metastudio.project_format import load_project, save_project

ROOT = Path(__file__).resolve().parents[1]


def main():
    arm_id = "mean:arm"
    sheet_id = "mean:sheet"
    rows = [dict(id=f"mean:row:{i}", label=f"Illustrative study {i + 1}",
                 year=2020 + i, sample_size=None, include=True, manually_excluded=False,
                 notes="Synthetic measurements for learning RCMS; not research evidence.",
                 covariates={}, raw_data={arm_id: [20 + i, 4 + i, 2 + i]},
                 entered_effects=[], ratio_inputs=[]) for i in range(6)]
    project = dict(schema_version=3, title="Illustrative one-arm Mean",
                   notes="Synthetic example, not a published dataset. Six study means with N and SD. Values have no clinical interpretation.",
                   sheets=[dict(id=sheet_id, name="Illustrative measurement", family="continuous",
                       data_type=1, sub_type="mean", arms=[dict(id=arm_id, name="Participants")],
                       covariates=[], settings=dict(metric="Mean", confidence_level=95.0, arms=[arm_id]),
                       rows=rows)])
    state = dict(schema_version=3, current_sheet_id=sheet_id)
    path = ROOT / "sample_projects/Illustrative-Mean.rcms"
    save_project(path, project, state)
    reopened = load_project(path)
    assert reopened.project == project and reopened.state == state
    manifest_path = ROOT / "sample_projects/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = dict(file=path.name, format_version=3,
                 sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                 semantic_sha256=hashlib.sha256((json.dumps(project, sort_keys=True, ensure_ascii=False,
                     allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")).hexdigest(),
                 provenance="Synthetic illustrative values; no publication or clinical interpretation.",
                 analysis_evidence="analysis-data-onearm-mean",
                 workflow_coverage=["raw one-arm Mean", "save and reopen", "pooling compared with metafor"],
                 test_usage=["tests/e2e/mean_metric_migration.py"])
    manifest["projects"] = [p for p in manifest["projects"] if p["file"] != path.name] + [entry]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {path.name}: {len(rows)} synthetic studies")


if __name__ == "__main__":
    main()
