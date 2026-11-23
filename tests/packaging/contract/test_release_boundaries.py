"""Local release pipelines: actual CLI, archives and controlled GitHub responses."""

import json
import subprocess
import sys
import os
import re
import shutil
import base64
import tarfile
from pathlib import Path

import pytest
import yaml

from tests.packaging.contract.test_delivery_state_machine import load_delivery

ROOT = Path(__file__).resolve().parents[3]
BASH = shutil.which("bash") or "C:/Program Files/Git/bin/bash.exe"


def release_proof_source(path):
    # Also permits replay against the pre-fix definitions without touching Git.
    revision = os.environ.get("RELEASE_PROOF_REVISION")
    return (
        subprocess.check_output(
            ["git", "show", f"{revision}:{path}"],
            cwd=ROOT,
            text=True,
        )
        if revision
        else (ROOT / path).read_text(encoding="utf-8")
    )


def workflow(name):
    return yaml.safe_load(release_proof_source(f".github/workflows/{name}.yml"))


def shell_step(step, tmp_path, values, prelude=""):
    def render(text):
        return re.sub(r"\$\{\{\s*(.*?)\s*\}\}", lambda m: values.get(m[1], ""), text)

    env = {
        k: v
        for k, v in os.environ.items()
        if not any(
            word in k.upper() for word in ("TOKEN", "SECRET", "CREDENTIAL", "PASSWORD")
        )
    }
    env.update({k: render(str(v)) for k, v in step.get("env", {}).items()})
    env.update(
        {"GITHUB_OUTPUT": str(tmp_path / "outputs"), "GITHUB_REPOSITORY": "owner/repo"}
    )
    script = tmp_path / "step.sh"
    script.write_text(prelude + "\n" + render(step["run"]), encoding="utf-8")
    result = subprocess.run(
        [BASH, str(script)], cwd=tmp_path, env=env, capture_output=True, text=True
    )
    (tmp_path / "observed.json").write_text(
        json.dumps(
            {
                "command": [BASH, str(script)],
                "cwd": str(tmp_path),
                "inputs": values,
                "exit": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
            indent=2,
        )
    )
    return result


@pytest.mark.parametrize(
    "old,new,event,draft,expected",
    [
        ("src/removed.py", "docs/moved.txt", "pull_request", False, {"qt6-verification", "remaining-surface-verification", "source-fast-targets", "full-r-stack"}),
        ("", "docs/maintaining.md", "pull_request", False, set()),
        ("", "src/rc_metastudio/calculators/binary_dialog.py", "pull_request", True, {"qt6-verification", "remaining-surface-verification", "source-fast-targets", "full-r-stack"}),
        ("", "r/RCMetaR/R/binary_methods.R", "push", False, {"source-fast-targets", "full-r-stack"}),
        ("", "packaging/app.spec", "pull_request", True, {"windows-package-qualification"}),
        ("", "packaging/app.spec", "pull_request", False, {"windows-package-qualification", "macos-package-qualification", "linux-package-qualification", "packaging-contract-macos"}),
        ("", ".github/workflows/fast-verification.yml", "pull_request", False, None),
        ("", "docs/maintaining.md", "schedule", False, None),
    ],
)
def test_input_classification_executes_workflow(tmp_path, old, new, event, draft, expected):
    workflow_jobs = workflow("fast-verification")["jobs"]
    step = workflow_jobs["change-classifier"]["steps"][1]
    git = f"function git() {{ if [[ \"$1\" == diff ]]; then printf '%s\\0' {old or new} {new}; fi; }}"
    result = shell_step(
        step,
        tmp_path,
        {
            "github.event_name": event,
            "github.event.pull_request.draft": str(draft).lower(),
            "github.event.pull_request.base.sha": "base",
            "github.event.before": "base",
        },
        f'{git}\nexport PYTHONPATH={ROOT.as_posix()!r}\nfunction python3() {{ "{Path(sys.executable).as_posix()}" "$@"; }}',
    )
    assert result.returncode == 0, result.stderr
    fields = dict(line.split("=", 1) for line in (tmp_path / "outputs").read_text().splitlines())
    lanes = set(json.loads(fields["lanes"]))
    assert lanes == (expected if expected is not None else set(workflow_jobs["fast-verification-gate"]["needs"]) - {"change-classifier", "quick", "code-health"})
    if draft and "source-fast-targets" in lanes:
        assert [target["platform"] for target in json.loads(fields["targets"])] == ["windows"]
        parts = json.loads(fields["r-stack-parts"])
        assert parts and all(row["scenarios"] for row in parts)
    if new.startswith("r/"):
        assert {row["part"] for row in json.loads(fields["r-stack-parts"])} == {"checks", "1", "2", "3"}


@pytest.mark.parametrize("selected,result,passes", [(False, "skipped", True), (True, "success", True), (True, "skipped", False), (True, "failure", False)])
def test_verification_gate_requires_selected_jobs(tmp_path, selected, result, passes):
    step = workflow("fast-verification")["jobs"]["fast-verification-gate"]["steps"][0]
    required = dict.fromkeys(("change-classifier", "quick", "code-health"), {"result": "success"})
    observation = shell_step(step, tmp_path, {
        "toJSON(needs)": json.dumps(required | {"full-r-stack": {"result": result}}),
        "needs.change-classifier.outputs.lanes": json.dumps(["full-r-stack"] if selected else []),
    }, f'function python3() {{ "{Path(sys.executable).as_posix()}" "$@"; }}')
    assert (observation.returncode == 0) is passes, observation.stderr


def test_historical_master_ancestor_executes_workflow(tmp_path):
    remote = tmp_path / "remote"
    remote.mkdir()

    def git(*args, cwd=remote):
        return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()

    git("init", "-b", "master")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "Fixture")
    for n in range(4):
        (remote / "data").write_text(str(n))
        git("add", "data")
        git("commit", "-m", str(n))
    source = git("rev-parse", "HEAD~3")
    definition = workflow("candidate")["jobs"]["initialize"]["steps"]
    clone = tmp_path / "checkout"
    depth = definition[0]["with"].get("fetch-depth", 1)
    args = ["clone"] + ([] if depth == 0 else ["--depth", str(depth)])
    git(*args, remote.as_uri(), str(clone), cwd=tmp_path)
    git("fetch", "origin", source, "--depth=1" if depth else "--no-tags", cwd=clone)
    git("checkout", source, cwd=clone)
    result = shell_step(definition[1], clone, {"inputs.source_sha": source})
    assert result.returncode == 0, result.stderr


def test_candidate_records_archive_from_historical_source(tmp_path):
    remote = tmp_path / "remote"
    remote.mkdir()

    def git(*args, cwd=remote):
        return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()

    git("init", "-b", "master")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "Fixture")
    (remote / "scripts").mkdir()
    script = remote / "scripts/delivery.py"
    script.write_text("raise SystemExit('historical CLI has no record-assembled command')\n")
    registry = json.loads((ROOT / "delivery/targets.json").read_text(encoding="utf-8"))
    target = "linux-x64"
    artifact = "historical-linux.tar.gz"
    registry["targets"][target]["candidate_artifact"] = artifact
    (remote / "delivery").mkdir()
    (remote / "delivery/targets.json").write_text(json.dumps(registry), encoding="utf-8")
    git("add", "scripts", "delivery")
    git("commit", "-m", "Historical source")
    source = git("rev-parse", "HEAD")
    script.write_text(release_proof_source("scripts/delivery.py"), encoding="utf-8")
    shutil.copyfile(ROOT / "delivery/targets.json", remote / "delivery/targets.json")
    git("add", "scripts", "delivery")
    git("commit", "-m", "Dispatching workflow source")
    workflow_sha = git("rev-parse", "HEAD")
    checkout = tmp_path / "checkout"
    git("clone", "--depth=1", remote.as_uri(), str(checkout), cwd=tmp_path)
    git("fetch", "--depth=1", "origin", source, cwd=checkout)
    git("checkout", source, cwd=checkout)
    (checkout / "candidate").mkdir()
    delivery = load_delivery()
    manifest = {
        "schema_version": 1,
        "product": "RC MetaStudio",
        "version": "0.6.0-rc.99",
        "channel": "candidate",
        "trust_profile": "macos-trusted",
        "source": {"commit": source},
        "policy_inputs": {},
        "release_targets": [target],
    }
    (checkout / "candidate/release-set.json").write_text(json.dumps(manifest), encoding="utf-8")
    (checkout / "artifacts").mkdir()
    payload = checkout / "launcher"
    payload.write_text("historical application", encoding="utf-8")
    archive = checkout / "artifacts" / artifact
    with tarfile.open(archive, "w:gz") as bundle:
        bundle.add(payload, arcname="launcher")

    values = {"github.workflow_sha": workflow_sha, "matrix.target": target, "matrix.artifact": artifact}
    python = Path(sys.executable).as_posix()
    for step in workflow("candidate")["jobs"]["build"]["steps"]:
        if step.get("name") in {"Extract Linux candidate", "Record assembled candidate"}:
            observed = shell_step(step, checkout, values, f'function uv() {{ shift 3; "{python}" "$@"; }}')
            assert observed.returncode == 0, observed.stderr

    record = delivery.load(checkout / f"candidate/{target}.assembled.json")
    assert record["source_commit"] == source
    assert record["input_digest"] == delivery.release_identity_digest(manifest)
    assert {item["name"]: item["sha256"] for item in record["outputs"]}[artifact] == delivery.digest(archive)
    inventory = delivery.load(checkout / f"candidate/{target}.inventory.json")
    assert inventory["files"][0]["sha256"] == delivery.digest(payload)


@pytest.mark.parametrize(
    "name,job,step_name",
    [
        ("candidate", "initialize", "Initialize three-target release set"),
        (
            "community-release-candidate",
            "publish-rc",
            "Publish clearly labeled immutable unsigned RC",
        ),
        (
            "macos-trusted-release-candidate",
            "publish-rc",
            "Publish immutable macOS-trusted RC",
        ),
        ("promote", "promote", "Publish stable release without rebuilding"),
    ],
)
def test_shell_inputs_remain_data(tmp_path, name, job, step_name):
    step = next(
        s for s in workflow(name)["jobs"][job]["steps"] if s.get("name") == step_name
    )
    payload = '1.0.0-rc.1"; touch INJECTION; #'
    values = {
        "inputs.version": payload,
        "inputs.source_sha": "a" * 40,
        "github.repository": "owner/repo",
        "inputs.trust_profile": "unsigned-community",
        "inputs.stable_version": payload,
        "inputs.rc_tag": "v1.0.0-rc.1'; touch INJECTION; #",
    }
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/delivery.py").write_text("import sys\nraise SystemExit(2)\n")
    prelude = """function gh() { if [ "$2" = view ]; then return 1; fi; return 0; }
function git() { return 1; }
function jq() { if [ "$2" = .trust_profile ]; then echo macos-trusted; else printf 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\\n'; fi; }
"""
    shell_step(step, tmp_path, values, prelude)
    assert not (tmp_path / "INJECTION").exists()


def cli(*args, ok=True):
    command = [sys.executable, str(ROOT / "scripts/delivery.py"), *map(str, args)]
    inputs = {
        str(arg): base64.b64encode(Path(arg).read_bytes()).decode()
        for arg in args
        if Path(str(arg)).is_file()
    }
    result = subprocess.run(command, capture_output=True, text=True)
    if os.environ.get("RELEASE_EVIDENCE_LOG"):
        with open(os.environ["RELEASE_EVIDENCE_LOG"], "a", encoding="utf-8") as stream:
            stream.write(
                json.dumps(
                    {
                        "command": command,
                        "cwd": str(Path.cwd()),
                        "inputs_base64": inputs,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "exit": result.returncode,
                    }
                )
                + "\n"
            )
    assert (result.returncode == 0) == ok, result.stdout + result.stderr
    return result


@pytest.fixture
def pipeline(tmp_path):
    d = load_delivery()
    manifest = tmp_path / "release-set.json"
    cli(
        "init",
        "--version",
        d.repository_version() + "-rc.1",
        "--commit",
        "a" * 40,
        "--repository",
        "owner/repo",
        "--trust-profile",
        "macos-trusted",
        "--output",
        manifest,
    )
    initial = d.load(manifest)
    for target in initial["release_targets"]:
        previous = d.release_identity_digest(initial)
        artifact = tmp_path / d.targets()[target]["artifact"]
        if target == "macos-arm64":
            artifact = tmp_path / "RCMetaStudio-macos-arm64.dmg"
        artifact.write_bytes(("fixture:" + target).encode())
        sbom = tmp_path / f"{target}.cdx.json"
        sbom.write_text(json.dumps({"fixture": target}))
        for stage in d.required_stages(initial, target):
            record = tmp_path / f"{target}.{stage}.json"
            cli(
                "stage-result",
                "--target",
                target,
                "--stage",
                stage,
                "--commit",
                "a" * 40,
                "--input-digest",
                previous,
                "--output-file",
                artifact,
                "--output-file",
                sbom,
                "--result",
                record,
            )
            cli("attach", "--manifest", manifest, "--result", record)
            previous = d.canonical_digest(d.load(record))
    cli("verify", "--manifest", manifest)
    return d, manifest


@pytest.mark.parametrize("damage", ["digest", "empty", "target", "source", "identity"])
def test_verify_rechecks_downloaded_chain(pipeline, damage):
    d, path = pipeline
    manifest = d.load(path)
    stage = manifest["targets"]["windows-x64"]["stages"][1]
    if damage == "digest":
        stage["input_digest"] = "0" * 64
    if damage == "empty":
        stage["outputs"] = []
    if damage == "target":
        stage["target"] = "linux-x64"
    if damage == "source":
        stage["source_commit"] = "b" * 40
    if damage == "identity":
        manifest["policy_inputs"]["uv.lock"] = "0" * 64
    d.write(path, manifest)
    cli("verify", "--manifest", path, ok=False)


def test_publication_selects_only_verified_downloaded_files(pipeline, tmp_path):
    _, candidate = pipeline
    staging = tmp_path / "publication"
    staging.mkdir()
    manifest = staging / "release-set-rc.json"
    cli("promote", "--manifest", candidate, "--from-channel", "candidate",
        "--channel", "rc", "--output", manifest)
    targets = {
        "windows-x64": "RCMetaStudio-windows-x64.zip",
        "macos-arm64": "RCMetaStudio-macos-arm64.dmg",
        "linux-x64": "RCMetaStudio-linux-x64.tar.gz",
    }
    downloads = staging / "targets"
    for target, filename in targets.items():
        download = downloads / f"macos-trusted-{target}"
        download.mkdir(parents=True)
        for name in (filename, f"{target}.cdx.json"):
            shutil.copyfile(tmp_path / name, download / name)
    archive = downloads / "macos-trusted-macos-arm64" / targets["macos-arm64"]
    original = archive.read_bytes()
    archive.write_bytes(b"changed after attestation")
    stage = ("stage-publication", "--manifest", manifest,
             "--target-root", downloads, "--target-prefix", "macos-trusted")
    assert "does not match stage output" in cli(*stage, ok=False).stderr
    assert {item.name for item in staging.iterdir()} == {manifest.name, downloads.name}
    archive.write_bytes(original)
    cli(*stage)

    (staging / "unselected.cdx.json").write_text("{}")
    sums = staging / "SHA256SUMS"
    sums.write_text("".join(reversed(sums.read_text().splitlines(keepends=True))))
    selection = json.loads(cli("publication-assets", "--manifest", manifest).stdout)
    assert {Path(file).name for file in selection["archives"]} == set(targets.values())
    assert {Path(file).name for file in selection["files"]} == {
        manifest.name, "SHA256SUMS", *targets.values(), *(f"{target}.cdx.json" for target in targets),
    }
    assert (staging / archive.name).read_bytes() == original
    sums.write_text("")
    assert "checksum file does not match" in cli("publication-assets", "--manifest", manifest, ok=False).stderr


def test_promoted_chain_and_archive_binding(pipeline, tmp_path):
    d, path = pipeline
    rc = tmp_path / "rc.json"
    cli(
        "promote",
        "--manifest",
        path,
        "--from-channel",
        "candidate",
        "--channel",
        "rc",
        "--output",
        rc,
    )
    cli(
        "verify",
        "--manifest",
        rc,
        "--artifact-root",
        tmp_path,
        "--repository",
        "owner/repo",
    )
    stable = tmp_path / "stable.json"
    cli(
        "promote",
        "--manifest",
        rc,
        "--from-channel",
        "rc",
        "--channel",
        "stable",
        "--version",
        d.repository_version(),
        "--output",
        stable,
    )
    cli(
        "verify",
        "--manifest",
        stable,
        "--artifact-root",
        tmp_path,
        "--repository",
        "owner/repo",
    )
    artifact = tmp_path / "RCMetaStudio-windows-x64.zip"
    assembled = tmp_path / "windows-x64.assembled.json"
    cli(
        "verify-archive",
        "--manifest",
        path,
        "--result",
        assembled,
        "--target",
        "windows-x64",
        "--archive",
        artifact,
    )
    cli(
        "verify-archive",
        "--manifest",
        path,
        "--result",
        assembled,
        "--target",
        "windows-x64",
        "--archive",
        artifact,
        "--source-sha",
        "b" * 40,
        ok=False,
    )
    cli(
        "verify",
        "--manifest",
        rc,
        "--artifact-root",
        tmp_path,
        "--repository",
        "foreign/repo",
        ok=False,
    )
    artifact.write_bytes(b"wrong bytes with a matching independent checksum")
    cli(
        "verify",
        "--manifest",
        rc,
        "--artifact-root",
        tmp_path,
        "--repository",
        "owner/repo",
        ok=False,
    )
    cli(
        "verify-archive",
        "--manifest",
        path,
        "--result",
        assembled,
        "--target",
        "windows-x64",
        "--archive",
        artifact,
        ok=False,
    )


def test_actions_with_controlled_github(tmp_path):
    result = subprocess.run(
        [
            "node",
            "--test",
            str(ROOT / "tests/packaging/contract/release_actions.test.cjs"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
