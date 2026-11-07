"""Refresh reviewed text/figure goldens from the sanctioned real-R capture.

Numerical outputs and policy stay unchanged; archive SHA bindings are refreshed. Run
verify_golden_compatibility.py first and inspect its report and figures before
using this command with that capture directory.
"""

import argparse
import hashlib
import json
import io
import shutil
import tempfile
import sys
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _recover(outputs: dict[Path, bytes], published: list[Path], recovery: Path) -> None:
    try:
        for index, path in enumerate(outputs):
            if path in published:
                (recovery / f"{index}.backup").replace(path)
    except BaseException as error:
        raise RuntimeError(f"Golden refresh recovery failed; backups retained at {recovery}") from error


def _publish(outputs: dict[Path, bytes]) -> None:
    # Keep recovery bytes on disk until every binding has been replaced.
    originals = {path: path.read_bytes() for path in outputs}
    recovery = Path(tempfile.mkdtemp(prefix=".golden-refresh-", dir=next(iter(outputs)).parent))
    published = []
    try:
        (recovery / "paths.json").write_text(json.dumps([str(path) for path in outputs]), encoding="utf-8")
        for index, (path, contents) in enumerate(outputs.items()):
            (recovery / f"{index}.backup").write_bytes(originals[path])
            staged = recovery / f"{index}.staged"
            staged.write_bytes(contents)
        for index, path in enumerate(outputs):
            published.append(path)
            (recovery / f"{index}.staged").replace(path)
    except BaseException:
        _recover(outputs, published, recovery)
        shutil.rmtree(recovery)
        raise
    shutil.rmtree(recovery)


def _refresh_case(row: dict, changes: list[dict], capture: Path, members: dict[str, bytes]) -> None:
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


def _refresh_contracts(baseline: Path, manifest: dict, entry: dict, outer: dict, outputs: dict[Path, bytes]) -> None:
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
        outputs[path] = (json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        outer[field].update(sha256=hashlib.sha256(outputs[path]).hexdigest(), size=len(outputs[path]))


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
        _refresh_case(row, changes, capture, members)
    members["manifest.json"] = json.dumps(manifest, indent=2, sort_keys=True).encode()
    staged_archive = io.BytesIO()
    with zipfile.ZipFile(staged_archive, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, contents in members.items():
            archive.writestr(member_info[name], contents)
    outputs = {archive_path: staged_archive.getvalue()}
    outer_path = baseline / "manifest.json"
    outer = json.loads(outer_path.read_text(encoding="utf-8"))
    entry = outer["observed_golden_analysis_bundle"]
    entry.update(sha256=hashlib.sha256(outputs[archive_path]).hexdigest(), size=len(outputs[archive_path]))
    _refresh_contracts(baseline, manifest, entry, outer, outputs)
    outputs[outer_path] = (json.dumps(outer, indent=2, sort_keys=True) + "\n").encode("utf-8")
    from scripts import verify_golden_compatibility as verifier
    with tempfile.TemporaryDirectory(prefix="golden-refresh-validation-") as directory:
        staged_root = Path(directory).resolve()
        staged_baseline = staged_root / "tests/analysis_regression/baseline"
        staged_baseline.mkdir(parents=True)
        for path, contents in outputs.items():
            (staged_baseline / path.name).write_bytes(contents)
        staged_archive, reference = verifier._load_frozen_reference(staged_root)
        verifier._load_numeric_contract(staged_root, staged_archive, reference)
        verifier._load_plot_descriptor_contract(staged_root, staged_archive, reference)
    _publish(outputs)
    print("Refreshed text/figure members and archive SHA bindings; numerical outputs and policy retained.")


if __name__ == "__main__":
    main()
