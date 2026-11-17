"""Local release pipelines: actual CLI, archives and controlled GitHub responses."""

import json
import subprocess
import sys
import os
import re
import shutil
import base64
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
    "old,new,source_required,package_required",
    [
        ("src/removed.py", "docs/moved.txt", True, True),
        ("docs/old.txt", "src/new.py", True, True),
        ("packaging/old.spec", "docs/old.spec", True, True),
        ("", ".agents/skills/verify-rcms/scripts/analysis_matrix.py", True, True),
        ("", "scripts/qt6_build_impl.py", True, True),
        ("scripts/r-bundle-closure.R", "scripts/new-r-bundle-closure.R", True, True),
        ("", "scripts/prune_staged_r.py", True, True),
        ("", "scripts/configure_linux_r_launchers.py", True, True),
        ("", ".github/workflows/code-health.yml", True, False),
        ("", "config/desktop-durations.json", True, False),
        ("", "docs/maintaining.md", False, False),
    ],
)
def test_input_classification_executes_workflow(tmp_path, old, new, source_required, package_required):
    step = workflow("fast-verification")["jobs"]["change-classifier"]["steps"][1]
    files = [{"filename": new, "previous_filename": old}]
    (tmp_path / "files.json").write_text(json.dumps(files))
    # The fake API honors the actual jq projection supplied by the action.
    (tmp_path / "api.py").write_text(
        'import json,sys\nfor f in json.load(open("files.json")):\n print(f["filename"])\n if "previous_filename" in sys.argv[-1]: print(f["previous_filename"])\n'
    )
    (tmp_path / "scripts").mkdir()
    policy_path = "scripts/package_input_policy.py"
    (tmp_path / policy_path).write_text(release_proof_source(policy_path), encoding="utf-8")
    python = Path(sys.executable).as_posix()
    result = shell_step(
        step,
        tmp_path,
        {
            "github.event_name": "pull_request",
            "github.event.pull_request.number": "42",
            "github.repository": "owner/repo",
        },
        f'function gh() {{ "{python}" api.py "$@"; }}\nfunction python3() {{ "{python}" "$@"; }}',
    )
    assert result.returncode == 0, result.stderr
    outputs = (tmp_path / "outputs").read_text()
    fields = dict(line.split("=", 1) for line in outputs.splitlines())
    assert fields["run-windows"] == str(source_required).lower()
    assert fields["run-linux"] == str(source_required).lower()
    assert fields["run-windows-package"] == str(package_required).lower()


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
    # No command in this isolated replay can reach a real release or Git remote.
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
