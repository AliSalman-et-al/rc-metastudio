"""Check the app models and replay existing persistence fault tests on a scratch copy."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback
import urllib.request
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
JAR_URL = "https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar"
JAR_SHA = "936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88"
TESTS = [
    "test_failed_atomic_replace_preserves_the_previous_project",
    "test_pre_replace_failures_preserve_previous_project_and_clean_temporary_files",
    "test_serialization_and_schema_recursion_errors_use_project_format_boundary",
    "test_cleanup_failure_preserves_and_annotates_the_primary_error",
    "test_supported_directory_fsync_runs_after_atomic_replacement",
    "test_post_replace_directory_fsync_failure_reports_new_file_is_installed",
    "test_post_replace_directory_close_failure_reports_durability_uncertainty",
    "test_directory_close_failure_annotates_primary_post_replace_fsync_error",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--mutation", choices=["none", "truncate", "skip-validation", "misclassify"], default="none")
    args = parser.parse_args()
    out = args.out.resolve() if args.out else Path(tempfile.mkdtemp(prefix="rcms-formal-"))
    if args.out:
        out.mkdir(parents=True, exist_ok=False)
    print(f"Evidence: {out}", flush=True)
    cache = Path(tempfile.gettempdir()) / "rcms-formal-tools" / "tla2tools-1.7.4.jar"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        with urllib.request.urlopen(JAR_URL, timeout=60) as response:
            payload = response.read()
        if hashlib.sha256(payload).hexdigest() != JAR_SHA:
            raise RuntimeError("Downloaded TLC digest mismatch")
        cache.write_bytes(payload)
    if hashlib.sha256(cache.read_bytes()).hexdigest() != JAR_SHA:
        raise RuntimeError("Cached TLC digest mismatch")

    commands = []

    def run(command: list[str], name: str, env=None) -> int:
        commands.append({"name": name, "argv": command})
        completed = subprocess.run(command, cwd=out, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
        (out / f"{name}.log").write_text(completed.stdout, encoding="utf-8")
        commands[-1]["exit"] = completed.returncode
        print(f"{name}: exit {completed.returncode}", flush=True)
        return completed.returncode

    models = ("App", "ProjectSave", "UnsavedActions")
    for model in models:
        for suffix in (".tla", ".cfg"):
            shutil.copy2(HERE / f"{model}{suffix}", out / f"{model}{suffix}")
    for name in ("app.view.ts", "analysis.view.ts", "save.view.ts", "unsaved.view.ts"):
        shutil.copy2(HERE / name, out / name)
    config = out / "ProjectSave.cfg"
    config.write_text(config.read_text().replace('Mutation = "none"', f'Mutation = "{args.mutation}"'))
    java = shutil.which("java")
    if java is None:
        raise RuntimeError("Install Java 11 or later and put java on PATH")
    java_code = run([java, "-version"], "java-version")
    codes = []
    for model in models:
        codes.append(run([java, "-XX:+UseParallelGC", "-cp", str(cache), "tlc2.TLC", "-workers", "1", "-fp", "0", "-lncheck", "final", "-config", f"{model}.cfg", f"{model}.tla"], model))

    # Use existing hostile-I/O checks, unchanged, against production source bytes.
    scratch = out / "replay"
    shutil.copytree(ROOT / "src/rc_metastudio", scratch / "src/rc_metastudio", ignore=shutil.ignore_patterns("__pycache__"))
    source = scratch / "src/rc_metastudio/project_format.py"
    text = source.read_text(encoding="utf-8")
    replacements = {
        "truncate": ("        os.replace(temporary_path, destination)", '        destination.write_bytes(b"destroyed previous project")\n        os.replace(temporary_path, destination)'),
        "skip-validation": ("        load_project(temporary_path, limits=selected_limits)", "        pass  # deliberately omit temporary validation"),
        "misclassify": ("durability_error = ProjectDurabilityError(", "durability_error = ProjectFormatError("),
    }
    if args.mutation != "none":
        before, after = replacements[args.mutation]
        if before not in text:
            raise RuntimeError("Mutation no longer matches: review code/model correspondence")
        source.write_text(text.replace(before, after), encoding="utf-8")
    test = scratch / "tests/python/fast/test_project_format.py"
    test.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "tests/python/fast/test_project_format.py", test)
    env = {**os.environ, "PYTHONPATH": str(scratch / "src")}
    replay_code = run([sys.executable, "-m", "pytest", *(f"{test}::{name}" for name in TESTS), "--rootdir", str(scratch), "--confcutdir", str(scratch), "--basetemp", str(out / "pytest-data"), "--junitxml", str(out / "replay.xml"), "-v"], "replay", env)
    replay_coverage: dict[str, object] = {"required": TESTS}
    try:
        cases = ET.parse(out / "replay.xml").getroot().findall(".//testcase")
        observed = {case.attrib["name"].split("[", 1)[0] for case in cases}
        skipped = [case.attrib["name"] for case in cases if case.find("skipped") is not None]
        complete = observed == set(TESTS) and not skipped
        replay_coverage.update(observed=sorted(observed), skipped=skipped, complete=complete)
    except (OSError, ET.ParseError, KeyError) as error:
        complete = False
        replay_coverage.update(complete=False, error=str(error))
    # A missing check or tool failure is inconclusive, not a product defect.
    inconclusive = (
        java_code != 0 or any(code not in {0, 11, 12, 13} for code in codes)
        or replay_code not in {0, 1} or not complete
    )
    exit_code = 2 if inconclusive else 1 if replay_code or any(codes) else 0
    outcome = {0: "passed", 1: "failed", 2: "not_checked"}[exit_code]
    manifest = {
        "command": [sys.executable, *sys.argv], "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "mutation": args.mutation, "python": sys.version, "tlc_sha256": JAR_SHA,
        "commands": commands, "outcome": outcome, "exit_code": exit_code,
        "replay_coverage": replay_coverage,
        "hashes": {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob("*") if p.is_file()},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Outcome: {outcome}; required replay coverage complete: {complete}", flush=True)
    return exit_code


if __name__ == "__main__":
    try:
        result = main()
    except Exception:
        traceback.print_exc()
        print("Outcome: not_checked; verification could not complete", file=sys.stderr)
        result = 2
    raise SystemExit(result)
