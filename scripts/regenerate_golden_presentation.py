"""Refresh reviewed text/figure goldens from the sanctioned real-R capture.

Numerical outputs and policy stay unchanged; archive SHA bindings are refreshed. Run
verify_golden_compatibility.py first and inspect its report and figures before
using this command with that capture directory.
"""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()
    capture = args.capture.resolve()
    report = json.loads((capture / "compatibility-report.json").read_text(encoding="utf-8"))
    if any(row["classification"] not in {"pass", "accepted_exception", "text_artifact_drift"}
           for row in report["comparison"]["rows"]):
        raise ValueError("Capture has failures beyond reviewed presentation drift.")
    baseline = ROOT / "tests/analysis_regression/baseline"
    archive_path = baseline / "observed-golden-baseline.zip"
    with zipfile.ZipFile(archive_path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
        member_info = {item.filename: item for item in archive.infolist()}
    manifest = json.loads(members["manifest.json"])
    changes = [item for item in report["comparison"]["rows"] if item["classification"] == "text_artifact_drift"]
    for row in manifest["curated_golden_set"]:
        current = json.loads((capture / "captures" / (row["id"] + ".json")).read_text(encoding="utf-8"))
        if current["status"] != "success":
            raise ValueError(f"Failed capture: {row['id']}")
        # The original numerical outputs remain the oracle, including exceptions.
        reviewed = [item["detail"] for item in changes if item["id"] == row["id"]]
        for detail in reviewed:
            if detail.startswith("Text section ") and detail.endswith(" changed."):
                name = detail.removeprefix("Text section ").removesuffix(" changed.")
                row["texts"][name] = current["texts"][name]
        old_artifacts = {item["label"]: item for item in row["artifacts"]}
        if set(old_artifacts) != {item["label"] for item in current["artifacts"]}:
            raise ValueError(f"Artifact families changed: {row['id']}")
        for artifact in current["artifacts"]:
            if not any(detail.startswith(f"Artifact {artifact['label']} ") for detail in reviewed):
                continue
            old = old_artifacts[artifact["label"]]
            source = Path(artifact["bundle_path"])
            contents = source.read_bytes()
            if hashlib.sha256(contents).hexdigest() != artifact["sha256"]:
                raise ValueError(f"Capture artifact hash mismatch: {source}")
            member = f"artifacts/{row['id']}/{Path(old['bundle_path'] or old['path']).name}"
            members[member] = contents
            old["sha256"] = artifact["sha256"]
        members[f"captures/{row['id']}.json"] = json.dumps(row, indent=2, sort_keys=True).encode()
    members["manifest.json"] = json.dumps(manifest, indent=2, sort_keys=True).encode()
    temporary = archive_path.with_suffix(".refresh.zip")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, contents in members.items():
            archive.writestr(member_info[name], contents)
    temporary.replace(archive_path)
    outer_path = baseline / "manifest.json"
    outer = json.loads(outer_path.read_text(encoding="utf-8"))
    entry = outer["observed_golden_analysis_bundle"]
    entry.update(sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest(), size=archive_path.stat().st_size)
    for filename, field in (("numeric-contract.json", "golden_numeric_contract"),
                            ("plot-descriptors.json", "golden_plot_descriptor_contract")):
        path = baseline / filename
        contract = json.loads(path.read_text(encoding="utf-8"))
        contract["oracle_sha256"] = entry["sha256"]
        if filename == "plot-descriptors.json":
            artifacts = {(case["id"], artifact["label"]): artifact["sha256"]
                         for case in manifest["curated_golden_set"] for artifact in case["artifacts"]}
            for row in contract["rows"]:
                row["artifact_oracle_sha256"] = artifacts[(row["id"], row["artifact_label"])]
        path.write_text(json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                        encoding="utf-8", newline="\n")
        outer[field].update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size=path.stat().st_size)
    outer_path.write_text(json.dumps(outer, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("Refreshed text/figure members and archive SHA bindings; numerical outputs and policy retained.")


if __name__ == "__main__":
    main()
