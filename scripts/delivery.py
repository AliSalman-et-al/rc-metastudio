#!/usr/bin/env python3
"""Build-once delivery state machine for RC MetaStudio release sets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS_PATH = ROOT / "delivery" / "targets.json"
POLICY_INPUTS = (
    ".python-version",
    ".github/workflows/candidate.yml",
    ".github/workflows/community-release-candidate.yml",
    ".github/workflows/macos-trusted-release-candidate.yml",
    ".github/workflows/package-linux.yml",
    ".github/workflows/package-verification.yml",
    ".github/workflows/promote.yml",
    "uv.lock",
    "pyproject.toml",
    "config/r-dependencies.json",
    "r/RCMetaR/DESCRIPTION",
    "delivery/targets.json",
    "delivery/release-set.schema.json",
    "delivery/stage-result.schema.json",
    "scripts/build-windows-package.ps1",
    "scripts/package-windows.ps1",
    "scripts/windows-package-process.ps1",
    "scripts/windows-package-download.ps1",
    "scripts/test-bounded-package-process.ps1",
    "scripts/test-package-download-retry.ps1",
    "scripts/inspect_windows_deployment.py",
    "scripts/windows_system_imports.py",
    "packaging/pyinstaller/rc-metastudio.spec",
    "scripts/build-macos-package.sh",
    "scripts/build_macos_direct_provenance.py",
    "scripts/dependency_lock.py",
    "scripts/package-macos.sh",
    "scripts/package-linux.sh",
    "scripts/build-linux-package.sh",
    "scripts/finalize-linux-package.sh",
    "scripts/finalize-macos-package.sh",
    "scripts/install-r-deps-linux.R",
    "scripts/r_binary_policy.R",
    "scripts/r_dependency_policy.py",
    "scripts/inspect_macos_deployment.py",
    "scripts/normalize_macos_macho.py",
    "scripts/sign_macos_app.py",
    "scripts/sign-notarize-macos-artifact.sh",
    "config/macos-package-targets.json",
    "scripts/resolve_macos_package_target.py",
    "scripts/macos_rcc.py",
    "scripts/macos_direct_build_contract.py",
    "scripts/packaged_smoke_contract.py",
    "scripts/process_groups.py",
    "scripts/run_bounded_process.py",
    "scripts/package_input_policy.py",
    "packaging/pyinstaller/rc-metastudio-macos.spec",
    "packaging/pyinstaller/rc-metastudio-linux.spec",
)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def canonical_digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def release_identity_digest(manifest: dict) -> str:
    return canonical_digest(
        {
            "schema_version": manifest["schema_version"],
            "product": manifest["product"],
            "version": manifest["version"],
            "channel": manifest["channel"],
            "trust_profile": manifest["trust_profile"],
            "source": manifest["source"],
            "policy_inputs": manifest["policy_inputs"],
            "release_targets": manifest["release_targets"],
        }
    )


def chain_identity_digest(manifest: dict) -> str:
    # Promotion changes only channel/version. Reconstruct the initial identity
    # from the recorded promotion, retaining every immutable source/policy field.
    identity = dict(manifest)
    for event in reversed(manifest["history"]):
        if event["event"] == "promoted":
            identity["channel"] = event["from"]
            if "from_version" in event:
                identity["version"] = event["from_version"]
    return release_identity_digest(identity)


def validate_record(record: dict, target: str, commit: str, previous: str) -> None:
    if record["target"] != target or record["source_commit"] != commit:
        raise ValueError("stage target or source does not match release set")
    if record["input_digest"] != previous:
        raise ValueError(
            "stage input digest does not bind the preceding immutable state"
        )
    outputs = record.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        raise ValueError("stage outputs must not be empty")
    names = set()
    for output in outputs:
        name = output.get("name", "")
        if not name or Path(name).name != name or name in names:
            raise ValueError("invalid or duplicate stage output name")
        names.add(name)
        if (
            not isinstance(output.get("size"), int)
            or output["size"] <= 0
            or re.fullmatch(r"[0-9a-f]{64}", output.get("sha256", "")) is None
        ):
            raise ValueError("invalid stage output size or digest")


def check_output(record: dict, path: Path) -> None:
    matches = [item for item in record["outputs"] if item["name"] == path.name]
    if (
        len(matches) != 1
        or matches[0]["sha256"] != digest(path)
        or matches[0]["size"] != path.stat().st_size
    ):
        raise ValueError(f"archive does not match stage output: {path.name}")


def verify_archive(args: argparse.Namespace) -> None:
    check_candidate_archive(
        load(Path(args.manifest)), load(Path(args.result)), args.target, Path(args.archive),
        source_sha=getattr(args, "source_sha", None),
        repository=getattr(args, "repository", None),
        trust_profile=getattr(args, "trust_profile", None),
        version=getattr(args, "version", None),
    )


def check_candidate_archive(
    manifest: dict, record: dict, target: str, archive: Path, *,
    source_sha: str | None = None, repository: str | None = None,
    trust_profile: str | None = None, version: str | None = None,
) -> None:
    for actual, expected in (
        (manifest["source"]["commit"], source_sha),
        (manifest["source"]["repository"], repository),
        (manifest["trust_profile"], trust_profile),
        (manifest["version"], version),
    ):
        if expected is not None and actual != expected:
            raise ValueError(
                "candidate manifest does not match selected release identity"
            )
    configured = targets().get(target)
    if configured is None or archive.name != candidate_artifact(configured):
        raise ValueError("candidate archive name does not match target")
    if record["stage"] != "assembled":
        raise ValueError("candidate archive requires assembled record")
    validate_record(
        record,
        target,
        manifest["source"]["commit"],
        chain_identity_digest(manifest),
    )
    check_output(record, archive)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def targets() -> dict:
    return load(TARGETS_PATH)["targets"]


def candidate_artifact(target: dict) -> str:
    return target.get("candidate_artifact", target["artifact"])


def required_stages(manifest: dict, target: str) -> list[str]:
    registry = load(TARGETS_PATH)
    profile = registry["trust_profiles"][manifest["trust_profile"]]
    if "stages" in profile:
        return profile["stages"]
    os_name = registry["targets"][target]["os"]
    return profile[f"{os_name}_stages"]


def repository_version() -> str:
    import tomllib

    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["version"]


def assert_commit(commit: str) -> None:
    if len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit):
        raise ValueError("source commit must be a full lowercase 40-character Git SHA")


def init_release(args: argparse.Namespace) -> None:
    assert_commit(args.commit)
    version_match = re.fullmatch(
        r"(?P<base>[0-9]+\.[0-9]+\.[0-9]+)-rc\.[0-9]+", args.version
    )
    if version_match is None:
        raise ValueError("candidate version must be an RC version such as 0.4.0-rc.1")
    current_version = repository_version()
    if version_match.group("base") != current_version:
        raise ValueError(
            f"requested version {args.version} does not match repository version {current_version}"
        )
    configured = targets()
    selected_targets = list(dict.fromkeys(getattr(args, "target", None) or configured))
    unsupported = sorted(set(selected_targets) - set(configured))
    if unsupported:
        raise ValueError(f"unsupported release targets: {', '.join(unsupported)}")
    if not selected_targets or set(selected_targets) != set(configured):
        raise ValueError("release set must contain exactly the supported future targets")
    manifest = {
        "schema_version": 1,
        "product": "RC MetaStudio",
        "version": args.version,
        "channel": "candidate",
        "trust_profile": args.trust_profile,
        "source": {"repository": args.repository, "commit": args.commit},
        "policy_inputs": {name: digest(ROOT / name) for name in POLICY_INPUTS},
        "release_targets": selected_targets,
        "targets": {},
        "history": [{"event": "initialized", "at": now(), "commit": args.commit}],
    }
    write(Path(args.output), manifest)


def inventory(args: argparse.Namespace) -> None:
    write(Path(args.output), inventory_tree(Path(args.root).resolve()))


def inventory_tree(root: Path) -> dict:
    if not root.is_dir():
        raise ValueError(f"inventory root does not exist: {root}")
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": digest(path),
            }
        )
    return {"schema_version": 1, "root": root.name, "files": files}


def sbom(args: argparse.Namespace) -> None:
    write(Path(args.output), cyclonedx(load(Path(args.inventory)), args.version))


def cyclonedx(source: dict, version: str) -> dict:
    components = [
        {
            "type": "file",
            "name": item["path"],
            "hashes": [{"alg": "SHA-256", "content": item["sha256"]}],
        }
        for item in source["files"]
    ]
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": "urn:uuid:"
        + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical_digest(source))),
        "version": 1,
        "metadata": {
            "timestamp": now(),
            "component": {
                "type": "application",
                "name": "RC MetaStudio",
                "version": version,
            },
        },
        "components": components,
    }


def make_stage_record(
    target: str, stage: str, commit: str, input_digest: str, paths: list[Path]
) -> dict:
    assert_commit(commit)
    if target not in targets():
        raise ValueError(f"unsupported target: {target}")
    outputs = []
    for path in paths:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"stage output is missing or empty: {path}")
        outputs.append(
            {"name": path.name, "sha256": digest(path), "size": path.stat().st_size}
        )
    return {
        "schema_version": 1,
        "target": target,
        "stage": stage,
        "source_commit": commit,
        "input_digest": input_digest,
        "outputs": outputs,
        "completed_at": now(),
    }


def stage_result(args: argparse.Namespace) -> None:
    record = make_stage_record(
        args.target, args.stage, args.commit, args.input_digest,
        [Path(value) for value in args.output_file],
    )
    write(Path(args.result), record)


def write_distribution_metadata(
    tree: Path, output: Path, target: str, version: str
) -> list[Path]:
    inventory_path = output / f"{target}.inventory.json"
    sbom_path = output / f"{target}.cdx.json"
    source = inventory_tree(tree.resolve())
    write(inventory_path, source)
    write(sbom_path, cyclonedx(source, version))
    return [inventory_path, sbom_path]


def record_assembled(args: argparse.Namespace) -> None:
    target = args.target
    manifest = load(args.manifest)
    if manifest["channel"] != "candidate" or target not in manifest["release_targets"]:
        raise ValueError("assembled record requires a selected candidate target")
    if args.archive.name != candidate_artifact(targets()[target]):
        raise ValueError("candidate archive name does not match target")
    output = args.manifest.parent
    metadata = write_distribution_metadata(args.tree, output, target, manifest["version"])
    record = make_stage_record(
        target, "assembled", manifest["source"]["commit"],
        release_identity_digest(manifest), [args.archive, *metadata],
    )
    write(output / f"{target}.assembled.json", record)


def record_unsigned_qualification(args: argparse.Namespace) -> None:
    target, commit = args.target, args.commit
    archive = args.candidate / "artifacts" / candidate_artifact(targets()[target])
    candidate_records = args.candidate / "candidate"
    manifest = load(candidate_records / "release-set.json")
    assembled_path = candidate_records / f"{target}.assembled.json"
    assembled = load(assembled_path)
    check_candidate_archive(manifest, assembled, target, archive, source_sha=commit, version=args.version)
    if required_stages(manifest, target)[1:3] != ["unsigned-qualified", "verified"]:
        raise ValueError(f"{target} requires a different qualification path")

    output = args.qualified
    metadata = write_distribution_metadata(output / "tree", output, target, args.version)
    carried = output / archive.name
    shutil.copyfile(archive, carried)
    check_output(assembled, carried)
    records = output / "records"
    records.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(assembled_path, records / assembled_path.name)
    unsigned = make_stage_record(
        target, "unsigned-qualified", commit, canonical_digest(assembled), [carried]
    )
    verified = make_stage_record(
        target, "verified", commit, canonical_digest(unsigned), [carried, *metadata]
    )
    write(records / f"{target}.unsigned-qualified.json", unsigned)
    write(records / f"{target}.verified.json", verified)


def attach(args: argparse.Namespace) -> None:
    path = Path(args.manifest)
    manifest = load(path)
    record = load(Path(args.result))
    if record["source_commit"] != manifest["source"]["commit"]:
        raise ValueError("stage result source commit does not match release set")
    target = manifest["targets"].setdefault(record["target"], {"stages": []})
    stages = target["stages"]
    required = required_stages(manifest, record["target"])
    expected = required[len(stages)] if len(stages) < len(required) else None
    if record["stage"] != expected:
        raise ValueError(
            f"invalid stage transition: expected {expected}, received {record['stage']}"
        )
    expected_input = (
        release_identity_digest(manifest)
        if not stages
        else canonical_digest(stages[-1])
    )
    if record["input_digest"] != expected_input:
        raise ValueError(
            "stage input digest does not bind the preceding immutable state"
        )
    validate_record(
        record, record["target"], manifest["source"]["commit"], expected_input
    )
    stages.append(record)
    manifest["history"].append(
        {
            "event": record["stage"],
            "target": record["target"],
            "at": record["completed_at"],
        }
    )
    write(path, manifest)


def verify_manifest(manifest: dict, repository: str | None = None) -> dict[str, dict]:
    assert_commit(manifest["source"]["commit"])
    configured = targets()
    selected = manifest.get("release_targets")
    if not isinstance(selected, list) or len(selected) != len(configured) or set(selected) != set(configured):
        raise ValueError(
            "release set must contain exactly the supported future targets"
        )
    if set(manifest["targets"]) != set(selected):
        raise ValueError("release set does not contain exactly its selected targets")
    attested = {}
    for name in selected:
        stages = manifest["targets"][name].get("stages", [])
        if [item["stage"] for item in stages] != required_stages(manifest, name):
            raise ValueError(f"{name} has incomplete or out-of-order stages")
        if any(
            item["source_commit"] != manifest["source"]["commit"] for item in stages
        ):
            raise ValueError(f"{name} contains a foreign source commit")
        previous = chain_identity_digest(manifest)
        for record in stages:
            validate_record(record, name, manifest["source"]["commit"], previous)
            previous = canonical_digest(record)
        attested[name] = stages[-1]
    if repository and manifest["source"]["repository"] != repository:
        raise ValueError("release source repository mismatch")
    return attested


def target_asset_names(name: str, target: dict, trust_profile: str) -> tuple[str, str]:
    archive = (
        target["artifact"]
        if trust_profile in target.get("final_artifact_profiles", ())
        else candidate_artifact(target)
    )
    return archive, f"{name}.cdx.json"


def verify(args: argparse.Namespace) -> None:
    manifest = load(Path(args.manifest))
    attested = verify_manifest(manifest, getattr(args, "repository", None))
    if getattr(args, "artifact_root", None):
        configured = targets()
        for name, record in attested.items():
            for member in target_asset_names(name, configured[name], manifest["trust_profile"]):
                check_output(record, Path(args.artifact_root) / member)
    print(canonical_digest(manifest))


def promote(args: argparse.Namespace) -> None:
    verify(argparse.Namespace(manifest=args.manifest))
    source = load(Path(args.manifest))
    expected = {"candidate": "rc", "rc": "stable"}
    if expected.get(source["channel"]) != args.channel:
        raise ValueError(f"cannot promote {source['channel']} to {args.channel}")
    if args.channel == "stable" and source["trust_profile"] != "macos-trusted":
        raise ValueError("stable promotion requires the macos-trusted profile")
    source_digest = canonical_digest(source)
    from_version = source["version"]
    if args.from_channel != source["channel"]:
        raise ValueError("promotion source channel mismatch")
    if args.version:
        if (
            args.channel != "stable"
            or source["version"].split("-rc.", 1)[0] != args.version
        ):
            raise ValueError("stable version must equal the RC base version")
        source["version"] = args.version
    source["channel"] = args.channel
    source["history"].append(
        {
            "event": "promoted",
            "from": args.from_channel,
            "from_version": from_version,
            "to": args.channel,
            "at": now(),
            "source_manifest_sha256": source_digest,
        }
    )
    write(Path(args.output), source)


def verified_publication_files(
    manifest: dict, root: Path, target_prefix: str = "",
) -> tuple[list[Path], dict[Path, str]]:
    attested = verify_manifest(manifest)
    configured = targets()
    archives = []
    files = {}
    for target, record in attested.items():
        archive, sbom = target_asset_names(target, configured[target], manifest["trust_profile"])
        outputs = {item["name"]: item["sha256"] for item in record["outputs"]}
        if outputs.keys() != {archive, sbom}:
            raise ValueError(f"{target} must attest exactly its archive and SBOM")
        directory = root / f"{target_prefix}-{target}" if target_prefix else root
        for name in (archive, sbom):
            path = directory / name
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"missing regular publication asset: {path}")
            check_output(record, path)
            files[path] = outputs[name]
        archives.append(directory / archive)
    if len({path.name for path in files}) != 2 * len(attested):
        raise ValueError("publication names must be distinct across release targets")
    return archives, files


def checksum_lines(files: dict[Path, str]) -> str:
    by_name = sorted((path.name, sha) for path, sha in files.items())
    return "".join(f"{sha}  {name}\n" for name, sha in by_name)


def stage_publication(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest)
    _, files = verified_publication_files(load(manifest), Path(args.target_root), args.target_prefix)
    for path in files:
        shutil.copyfile(path, manifest.parent / path.name)
    (manifest.parent / "SHA256SUMS").write_text(checksum_lines(files), encoding="utf-8")


def publication_assets(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest)
    archives, files = verified_publication_files(load(manifest), manifest.parent)
    sums = manifest.parent / "SHA256SUMS"
    if sorted(sums.read_text(encoding="utf-8").splitlines()) != sorted(checksum_lines(files).splitlines()):
        raise ValueError("publication checksum file does not match the attested outputs")
    print(json.dumps({
        "archives": [str(path) for path in archives],
        "files": [*(str(path) for path in files), str(sums), str(manifest)],
    }))


def print_digest(args: argparse.Namespace) -> None:
    value = load(Path(args.json))
    print(
        release_identity_digest(value)
        if args.release_identity
        else canonical_digest(value)
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(required=True)
    init = commands.add_parser("init")
    init.add_argument("--version", required=True)
    init.add_argument("--commit", required=True)
    init.add_argument("--repository", required=True)
    init.add_argument(
        "--trust-profile",
        choices=tuple(load(TARGETS_PATH)["trust_profiles"]),
        default="unsigned-community",
    )
    init.add_argument(
        "--target",
        action="append",
        help="Release target to include; repeat as needed. Defaults to all configured targets.",
    )
    init.add_argument("--output", required=True)
    init.set_defaults(func=init_release)
    inv = commands.add_parser("inventory")
    inv.add_argument("--root", required=True)
    inv.add_argument("--output", required=True)
    inv.set_defaults(func=inventory)
    bom = commands.add_parser("sbom")
    bom.add_argument("--inventory", required=True)
    bom.add_argument("--version", required=True)
    bom.add_argument("--output", required=True)
    bom.set_defaults(func=sbom)
    stage = commands.add_parser("stage-result")
    stage.add_argument("--target", required=True)
    stage.add_argument("--stage", required=True)
    stage.add_argument("--commit", required=True)
    stage.add_argument("--input-digest", required=True)
    stage.add_argument("--output-file", action="append", required=True)
    stage.add_argument("--result", required=True)
    stage.set_defaults(func=stage_result)
    assembled = commands.add_parser("record-assembled")
    assembled.add_argument("--target", required=True, choices=tuple(targets()))
    assembled.add_argument("--archive", required=True, type=Path)
    assembled.add_argument("--manifest", required=True, type=Path)
    assembled.add_argument("--tree", required=True, type=Path)
    assembled.set_defaults(func=record_assembled)
    unsigned = commands.add_parser("record-unsigned-qualification")
    unsigned.add_argument("--target", required=True, choices=tuple(targets()))
    unsigned.add_argument("--commit", required=True)
    unsigned.add_argument("--version", required=True)
    unsigned.add_argument("--candidate", required=True, type=Path)
    unsigned.add_argument("--qualified", required=True, type=Path)
    unsigned.set_defaults(func=record_unsigned_qualification)
    attach_parser = commands.add_parser("attach")
    attach_parser.add_argument("--manifest", required=True)
    attach_parser.add_argument("--result", required=True)
    attach_parser.set_defaults(func=attach)
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("--manifest", required=True)
    verify_parser.add_argument("--artifact-root")
    verify_parser.add_argument("--repository")
    verify_parser.set_defaults(func=verify)
    archive_parser = commands.add_parser("verify-archive")
    for option in ("manifest", "result", "target", "archive"):
        archive_parser.add_argument("--" + option, required=True)
    for option in ("source-sha", "repository", "trust-profile", "version"):
        archive_parser.add_argument("--" + option)
    archive_parser.set_defaults(func=verify_archive)
    promote_parser = commands.add_parser("promote")
    promote_parser.add_argument("--manifest", required=True)
    promote_parser.add_argument("--from-channel", required=True)
    promote_parser.add_argument("--channel", required=True)
    promote_parser.add_argument("--version")
    promote_parser.add_argument("--output", required=True)
    promote_parser.set_defaults(func=promote)
    stage_publication_parser = commands.add_parser("stage-publication")
    stage_publication_parser.add_argument("--manifest", required=True)
    stage_publication_parser.add_argument("--target-root", required=True)
    stage_publication_parser.add_argument("--target-prefix", required=True)
    stage_publication_parser.set_defaults(func=stage_publication)
    publication_parser = commands.add_parser("publication-assets")
    publication_parser.add_argument("--manifest", required=True)
    publication_parser.set_defaults(func=publication_assets)
    digest_parser = commands.add_parser("digest")
    digest_parser.add_argument("--json", required=True)
    digest_parser.add_argument("--release-identity", action="store_true")
    digest_parser.set_defaults(func=print_digest)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"delivery: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
