from __future__ import annotations

import os
from pathlib import Path
import shlex
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]
BASH = shutil.which("bash") or ("C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else None)


def posix(path: Path) -> str:
    value = path.resolve().as_posix()
    return "/" + value[0].lower() + value[2:] if len(value) > 1 and value[1] == ":" else value


def run_fixture(tmp_path: Path, output: Path, *, valid_source: bool = True):
    if not BASH:
        pytest.skip("bash is required")
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "scripts/produce-r-integration-kit-macos.sh", scripts)
    source = tmp_path / "source/R.framework/Resources"
    (source / "bin").mkdir(parents=True, exist_ok=True)
    (source / "sentinel").write_text("source unchanged")
    work = repo / "build/r-kit-producer/macos-arm64"
    work.mkdir(parents=True, exist_ok=True)
    (work / "sentinel").write_text("previous evidence")
    commands = tmp_path / "commands"
    commands.mkdir(exist_ok=True)
    # These doubles only test shell control flow. They never install or download.
    bodies = {
        "python": '''case "$1" in
- ) printf '%s\\n' "$FIXTURE/source/R.framework" ;;
*/profile_macos_embedded_r_runtime.py )
  phase="$2"; shift 2
  evidence=""; quarantine=""
  while [ "$#" -gt 0 ]; do
    case "$1" in --evidence) evidence="$2";; --quarantine-evidence) quarantine="$2";; esac
    shift
  done
  case "$phase" in
    quarantine) printf quarantine > "$evidence" ;;
    finalize) [ "$(cat "$quarantine")" = quarantine ] || exit 81; [ "$evidence" != "$quarantine" ] || exit 82; printf finalize > "$evidence" ;;
    *) exit 83 ;;
  esac ;;
*/relocate_macos_r_kit.py ) exit 73 ;;
*) exit 84 ;;
esac
''',
        "ditto": 'cp -R "$1" "$2"\n',
        "curl": 'while [ "$1" != --output ]; do shift; done; touch "$2"\n',
        "tar": 'mkdir -p "$4/fixture/r/RCMetaR"; touch "$4/fixture/r/RCMetaR/DESCRIPTION"\n',
        "git": 'printf fixture-commit\n',
        "Rscript": 'exit 0\n',
    }
    for name, body in bodies.items():
        path = commands / name
        path.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "' + name + ' $*" >> "$FIXTURE/events"\n' + body, newline="\n")
        path.chmod(0o755)
    shutil.copy2(commands / "Rscript", source / "bin/Rscript")
    env = dict(os.environ, FIXTURE=posix(tmp_path), PATH=posix(commands) + os.pathsep + os.environ["PATH"])
    # Set PATH inside Bash: Windows subprocess PATH uses semicolons.
    args = [BASH, "-c", 'export PATH="$FIXTURE/commands:$PATH"; exec bash "$@"', "fixture",
            posix(scripts / "produce-r-integration-kit-macos.sh"), "macos-arm64",
            posix(source if valid_source else tmp_path / "missing"), "python",
            "pkg", "url", "signature", "sdist", "url", "interface", "url", "objects", "url", posix(output)]
    result = subprocess.run(args, env=env, capture_output=True, text=True)
    (tmp_path / "invocation.txt").write_text(shlex.join(args))
    (tmp_path / "stdout.log").write_text(result.stdout)
    (tmp_path / "stderr.log").write_text(result.stderr)
    (tmp_path / "exit.txt").write_text(str(result.returncode))
    return result, repo, source


@pytest.mark.parametrize("kind", ["directory", "file", "outside", "source", "work", "invalid-source"])
def test_producer_rejects_output_without_mutation(tmp_path: Path, kind: str):
    output = tmp_path / "repo/artifacts/kit"
    output.parent.mkdir(parents=True)
    if kind == "directory":
        output.mkdir()
        (output / "sentinel").write_text("existing output")
    elif kind == "file":
        output.write_text("existing output")
    elif kind == "outside":
        output = tmp_path / "arbitrary-new-output"
    elif kind == "source":
        output = tmp_path / "source"
    elif kind == "work":
        output = tmp_path / "repo/build/r-kit-producer"
    result, repo, source = run_fixture(tmp_path, output, valid_source=kind != "invalid-source")
    assert result.returncode != 0
    assert (source / "sentinel").read_text() == "source unchanged"
    assert (repo / "build/r-kit-producer/macos-arm64/sentinel").read_text() == "previous evidence"
    if kind == "directory":
        assert (output / "sentinel").read_text() == "existing output"
    elif kind == "file":
        assert output.read_text() == "existing output"
    events = (tmp_path / "events").read_text() if (tmp_path / "events").exists() else ""
    assert "ditto " not in events
    assert "Rscript " not in events
    assert "curl " not in events


def test_producer_profiles_in_order_with_distinct_evidence(tmp_path: Path):
    output = tmp_path / "repo/artifacts/kit"
    output.parent.mkdir(parents=True)
    result, repo, source = run_fixture(tmp_path, output)
    assert result.returncode == 73, result.stderr
    events = (tmp_path / "events").read_text().splitlines()
    quarantine = next(i for i, line in enumerate(events) if "runtime.py quarantine " in line)
    deps = next(i for i, line in enumerate(events) if "install-r-deps.R" in line)
    rc = next(i for i, line in enumerate(events) if "install-rcmetar-source.R" in line)
    finalize = next(i for i, line in enumerate(events) if "runtime.py finalize " in line)
    relocation = next(i for i, line in enumerate(events) if "relocate_macos_r_kit.py" in line)
    assert quarantine < deps < rc < finalize < relocation
    assert (repo / "build/r-kit-producer/macos-arm64/sentinel").read_text() == "previous evidence"
    assert (source / "sentinel").read_text() == "source unchanged"


def test_staged_r_probe_emits_exact_marker_bytes(tmp_path: Path):
    rscript = shutil.which("Rscript")
    if not rscript:
        pytest.skip("real Rscript is required for marker-byte proof")
    # Execute the actual shell argument, not a Python imitation of R escaping.
    line = next(line for line in (ROOT / "scripts/build-macos-package.sh").read_text().splitlines()
                if 'cat("staged-r-ok' in line)
    expression = shlex.split(line.removesuffix("\\"))[-1]
    home = subprocess.check_output([rscript, "-e", "cat(R.home())"], text=True).strip()
    args = [rscript, "-e", expression]
    result = subprocess.run(args, env=dict(os.environ, R_HOME=home, RHOME=home), capture_output=True)
    (tmp_path / "command.txt").write_text(subprocess.list2cmdline(args))
    (tmp_path / "stdout.bin").write_bytes(result.stdout)
    (tmp_path / "stderr.bin").write_bytes(result.stderr)
    assert result.returncode == 0, result.stderr
    assert result.stdout.replace(b"\r\n", b"\n") == b"staged-r-ok\n"
