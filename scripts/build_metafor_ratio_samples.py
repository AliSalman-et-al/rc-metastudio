"""Build reproducible RCMS examples from the retained metadat source tables."""

import hashlib
import json
import math
from pathlib import Path

from rc_metastudio.project_domain import reconstruct_analysis_dataset
from rc_metastudio.project_format import load_project, save_project

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "sample_projects"
SOURCE = SAMPLES / "sources/metadat-ratios.json"


def study_inputs(row, hazard):
    record = dict(estimate=None, lower=None, upper=None, se=None, scale="ratio", confidence=95.0, source="raw", unit="catheter-days")
    if hazard:
        record.update(estimate=row["OmE"] / row["V"], se=math.sqrt(1 / row["V"]), scale="log", source="reported", unit="person-years")
    timing = {1: "Adjuvant", 2: "Neoadjuvant", 3: "Concomitant"}
    covariates = {"Original study ID": row["id"], "Chemotherapy timing": timing[int(row["grp"])], "Observed minus expected deaths": row["OmE"], "Log-rank variance": row["V"]} if hazard else {}
    return record, covariates


def study_groups(row, hazard, groups):
    return sorted([dict(id=i, name=group, raw_data=[] if hazard else [row[f"x{i+1}i"], row[f"t{i+1}i"]]) for i, group in enumerate(groups)], key=lambda group: group["name"])


def build(name, hazard, source):
    rows = source["rows"]
    family, metric, subtype, data_type = (
        ("time_to_event", "HR", "hazard_ratio", 5) if hazard else
        ("event_rates", "IRR", "incidence_rate_ratio", 6)
    )
    outcome = "Mortality" if hazard else "Catheter-related bloodstream infection"
    groups = ["Locoregional treatment plus chemotherapy", "Locoregional treatment alone"] if hazard else ["Anti-infective catheter", "Standard catheter"]
    studies = []
    for index, row in enumerate(rows, 1):
        identifier = row["id"] if hazard else row["study"]
        record, covariates = study_inputs(row, hazard)
        studies.append(dict(
            id=index, name=row["trial"] if hazard else row["authors"],
            year=None if hazard else int(row["year"]), include=True,
            manually_excluded=False, sample_size=None,
            notes=f"metadat {name}; original study ID {identifier}",
            covariates=covariates,
            analysis_units=[dict(
                outcome=outcome, follow_up="first", entered_effects={},
                groups=study_groups(row, hazard, groups),
                ratio_inputs=[dict(groups=groups, input=record)],
            )],
        ))
    notes = f"Source: metadat::{name}. Documentation: {source['documentation']}. Original publication: {source['doi']}. "
    notes += "HR input is log(HR)=OmE/V and SE=sqrt(1/V). Trial years are unavailable and left blank. Chemotherapy timing is the original grp classification." if hazard else "IRR uses original event counts and catheter-days. Group 1 is anti-infective catheter; group 2 is standard catheter. Nine studies are available, below the ten-study threshold for asymmetry tests."
    dataset = dict(
        analysis_family=family, title="Pignon 2000 — Head and neck cancer" if hazard else "Niel-Weise 2008 — Catheter infections",
        notes=notes, is_diagnostic=False, studies=studies,
        covariates=[dict(name=label, data_type=kind, stable_id=stable) for label, kind, stable in (
            ("Original study ID", 1, "pignon2000-id"),
            ("Chemotherapy timing", 4, "pignon2000-timing"),
            ("Observed minus expected deaths", 1, "pignon2000-ome"),
            ("Log-rank variance", 1, "pignon2000-variance"),
        )] if hazard else [],
        outcomes=[dict(name=outcome, data_type=data_type, sub_type=subtype, follow_ups=["first"])],
        summary=dict(arms="two", data_type=family, effect=metric, metric_choices=[metric], name=outcome, sub_type=subtype),
    )
    project = dict(schema_version=2, dataset=dataset)
    state = dict(schema_version=2, active_outcome=outcome, active_follow_up="first", active_groups=groups, active_effect=metric, confidence_level=95.0)
    filename = "Pignon2000-HR.rcms" if hazard else "NielWeise2008-IRR.rcms"
    path = SAMPLES / filename
    save_project(path, project, state)
    loaded = load_project(path)
    assert loaded.project == project and loaded.state == state
    return dict(
        file=filename, format_version=2, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        semantic_sha256=reconstruct_analysis_dataset(loaded.project, loaded.state).semantic_sha256,
        analysis_evidence="ratios-samples",
        scientific_name=dataset["title"], analysis_family=family, study_count=len(rows),
        provenance=f"metadat::{name}; original data retained in sources/metadat-ratios.json",
        source_url=source["documentation"], source_doi=source["doi"],
        source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        workflow_coverage=["source data preservation", "project open/save/reopen", "pooled estimates compared with metafor"],
        test_usage=[".agents/skills/verify-rcms/scripts/ratio_workflows.py"],
    )


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    additions = [build(name, hazard, source["datasets"][name]) for name, hazard in (("dat.pignon2000", True), ("dat.nielweise2008", False))]
    manifest_path = SAMPLES / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = 3
    manifest["storage_note"] = "Schema-validated Versioned Project Format ZIP/JSON containers. format_version is the default for the original frozen sample corpus; per-project format_version overrides it for newer examples."
    names = {item["file"] for item in additions}
    manifest["projects"] = [item for item in manifest["projects"] if item["file"] not in names] + additions
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for item in additions:
        print(f"Built {item['file']}: {item['study_count']} studies")


if __name__ == "__main__":
    main()
