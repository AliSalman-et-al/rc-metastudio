"""Failure controls for verification orchestration, isolated from GUI/R installs."""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import r_verification_support, verify, verify_rcmetar_r_stack as stack, verify_rcms
from scripts import audit_report_retention as audit
from scripts.code_health import build_evidence, git_as_of, load_config

ROOT = Path(__file__).resolve().parents[3]


def test_selected_python_rpy2_identity(tmp_path):
    # A real different interpreter (stdlib-only venv) cannot inherit our metadata.
    subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(tmp_path / 'python')], check=True)
    python = tmp_path / 'python/Scripts/python.exe' if sys.platform == 'win32' else tmp_path / 'python/bin/python'
    assert stack.verify_rpy2_identities(sys.executable) == r_verification_support.locked_rpy2_versions()
    with pytest.raises(stack.VerificationError):
        stack.verify_rpy2_identities(str(python))


@pytest.mark.parametrize("unverified_context", [None, '{"source_sha256":"same"}', "invalid-json"])
def test_typing_before_direct_desktop(monkeypatch, unverified_context):
    calls = []
    def typing(root):
        calls.append('typing')
        raise verify.VerificationError('controlled typing failure')
    monkeypatch.setattr(verify, 'run_typing', typing)
    monkeypatch.setattr(verify_rcms, '_reuse_evidence', lambda *a: calls.append('desktop') or True)
    monkeypatch.setattr(verify_rcms, 'source_digest', lambda _root: 'same')
    monkeypatch.setattr(sys, 'argv', ['verify_rcms', 'doctor'])
    monkeypatch.delenv('RCMS_E2E_CONTEXT', raising=False)
    if unverified_context is not None:
        monkeypatch.setenv('RCMS_E2E_CONTEXT', unverified_context)
    with pytest.raises(verify.VerificationError, match='controlled typing'):
        verify_rcms.main()
    assert calls == ['typing']


@pytest.mark.parametrize("mismatch", [None, "source_sha256", "build_root", "command", "stderr.log", "missing"])
def test_typing_receipt_is_reused_only_for_the_same_completed_check(monkeypatch, tmp_path, mismatch):
    from scripts import verification_evidence as evidence_store

    monkeypatch.setattr(evidence_store, "ROOT", tmp_path)
    monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(verify, "source_digest", lambda root: "source")
    monkeypatch.setattr(verify.subprocess, "run", lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "", ""))
    build = tmp_path / "generated-ui"
    receipt = verify.run_typing(build)
    record = json.loads(receipt.read_text(encoding="utf-8"))
    if mismatch in record:
        record[mismatch] = record["command"][:-1] if mismatch == "command" else "other"
        receipt.write_text(json.dumps(record), encoding="utf-8")
    elif mismatch == "missing":
        receipt.unlink()
    elif mismatch == "stderr.log":
        receipt.with_name(mismatch).unlink()

    reused = verify.ensure_typing(build, {verify.TYPING_RECEIPT_ENV: str(receipt)})
    assert (reused == receipt) == (mismatch is None)


def test_explicit_rscript_cannot_be_overridden(tmp_path):
    root = tmp_path / 'R'
    (root / 'bin').mkdir(parents=True)
    (root / 'bin/Rscript.exe').touch()
    other = tmp_path / 'other.exe'
    other.touch()
    with pytest.raises(verify.VerificationError, match='conflict'):
        verify.selected_rscript(argparse.Namespace(rscript=str(other), r_runtime_root=str(root)))


def test_source_lane_passes_one_selected_rscript_to_pytest_and_r_evidence(monkeypatch, tmp_path):
    selected = tmp_path / "selected-Rscript"
    selected.touch()
    monkeypatch.setenv("RCMS_RSCRIPT", str(tmp_path / "ambient-Rscript"))
    monkeypatch.setattr(verify, "prepare_qt_environment", lambda _root: {})
    monkeypatch.setattr(verify, "run_typing", lambda _root: None)
    children = []
    monkeypatch.setattr(verify, "run", lambda command, **options: children.append((command, options)))
    assert verify.main(["fast", "--rscript", str(selected)]) == 0
    environments = [options["env"] for _, options in children]
    assert all(env["RCMS_RSCRIPT"] == str(selected.resolve()) for env in environments)
    assert str(selected.resolve()) in children[-1][0]


@pytest.mark.parametrize(
    ("reuse", "cached_head", "expected_passes"),
    [(True, verify.STABLE_BASELINE, 1), (True, "wrong", 2), (True, None, 2),
     (False, verify.STABLE_BASELINE, 2)],
)
def test_code_health_always_checks_current_commit(monkeypatch, tmp_path, reuse, cached_head, expected_passes):
    monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
    if cached_head is not None:
        directory = tmp_path / "artifacts/code-health"
        directory.mkdir(parents=True)
        (directory / "baseline.json").write_text(
            json.dumps({"schema_version": 1, "head": cached_head}), encoding="utf-8"
        )
        (directory / "baseline.txt").write_text("cached report", encoding="utf-8")
    commands = []
    monkeypatch.setattr(verify, "run", commands.append)

    verify.run_code_health("base-commit", "current-commit", reuse_baseline=reuse)

    assert len(commands) == expected_passes
    assert commands[-1][commands[-1].index("--head") + 1] == "current-commit"
    assert "--baseline" in commands[-1]


def test_pre_push_uses_one_prepared_build_for_all_checks(monkeypatch, tmp_path):
    build = tmp_path / "generated-ui"
    receipt = tmp_path / "pre-push.json"
    head = "a" * 40
    monkeypatch.setenv("RCMS_QT6_BUILD_ROOT", str(build))
    monkeypatch.setattr(verify, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(verify, "PRE_PUSH_RECEIPT", receipt)
    monkeypatch.setattr(verify.sys, "platform", "win32")
    monkeypatch.setattr(verify, "git_output", lambda command, *_args: head if command == "rev-parse" else "")
    monkeypatch.setattr(verify, "pinned_r_environment", lambda env: env.update(RCMS_RSCRIPT="pinned/Rscript"))
    commands = []
    monkeypatch.setattr(verify, "run", lambda command, **options: commands.append((command, options)))
    monkeypatch.setattr(verify, "run_typing", lambda root: commands.append((["ty", str(root)], {})))

    assert verify.main(["pre-push"]) == 0
    result = json.loads(receipt.read_text(encoding="utf-8"))
    assert result["head"] == head and result["clean"] is True
    assert all(row["status"] == "pass" for row in result["steps"] if row["step"] in verify.pre_push_steps())
    assert [command[0][0] for command in commands].count("ty") == 1
    assert len([command for command, _ in commands if "scripts/build_qt6.py" in command]) == 1
    gui = next(options for command, options in commands if "tests/python/gui" in command)
    assert gui["env"]["RCMS_QT6_BUILD_ROOT"] == str(build)
    native = [command for command, _ in commands if "scripts/verify-qt6.ps1" in command]
    assert [(command[-3], command[-1]) for command in native] == [
        ("Core", str(build)),
        ("RemainingSurfaces", str(build)),
    ]


def test_r_version_is_part_of_manifest_check(monkeypatch):
    policy = json.loads((ROOT / 'config/r-dependencies.json').read_text())
    packages = {d['name']: d['installed_version'] for d in policy['direct_RCMetaR_dependencies']}
    for version in [policy['target_runtime']['r'], '0.0.0']:
        monkeypatch.setattr(stack, 'run_json', lambda *a, **k: dict(r_version=version, packages=packages))
        if version == '0.0.0':
            with pytest.raises(stack.VerificationError, match='R runtime'):
                stack.verify_manifest_versions(ROOT, sys.executable, Path('Rscript'), {})
        else:
            stack.verify_manifest_versions(ROOT, sys.executable, Path('Rscript'), {})


def test_comparison_disables_reuse(monkeypatch, tmp_path):
    monkeypatch.setenv('RCMS_E2E_REUSE_PASSED', '1')
    monkeypatch.setattr(verify_rcms, 'passed_evidence', lambda *a: tmp_path)
    args = argparse.Namespace(native=False, scenario='hillclimb', compare_measures=tmp_path / 'different.json')
    assert not verify_rcms._reuse_evidence({}, args)
    args.compare_measures = None
    assert verify_rcms._reuse_evidence({}, args)


@pytest.mark.parametrize("exit_code", [0, 1])
def test_desktop_preserves_private_workspace_and_recorded_tools(monkeypatch, tmp_path, exit_code):
    from scripts import verification_evidence as evidence_store

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(verify_rcms, "ROOT", tmp_path)
    monkeypatch.setattr(verify_rcms, "run_metadata", lambda *_args: {})
    monkeypatch.setattr(verify_rcms, "git_output", lambda *_args: "")
    monkeypatch.setattr(verify_rcms, "source_digest", lambda _root: "source")
    monkeypatch.setattr(verify, "run_typing", lambda _root: tmp_path / "typing.json")
    monkeypatch.setattr(evidence_store, "_runtime_environment", lambda env: {"PATH": env["PATH"]})
    monkeypatch.delenv("RCMS_E2E_CONTEXT", raising=False)
    monkeypatch.setattr(sys, "argv", ["verify_rcms", "doctor"])
    tool_dir = tmp_path / "oracles"
    tool_dir.mkdir()
    extension = ".exe" if sys.platform == "win32" else ""
    paths = {name: tool_dir / (name + extension) for name in ("pdftotext", "Rscript")}
    for path in paths.values():
        path.write_bytes(path.name.encode())
        path.chmod(0o755)
    monkeypatch.setenv("PATH", "oracles")
    monkeypatch.setenv("RCMS_RSCRIPT", str(paths["Rscript"].relative_to(tmp_path)))

    def run_child(command, *, cwd, env, stdout, **_kwargs):
        assert cwd != tmp_path
        with monkeypatch.context() as child:
            child.chdir(cwd)
            child.setenv("RCMS_E2E_TOOL_PATHS", env["RCMS_E2E_TOOL_PATHS"])
            child.setenv("PATH", "")
            for name, path in paths.items():
                assert Path(evidence_store.desktop_tool_executable(name)) == path
        (cwd / "result.bin").write_bytes(b"workflow artifact")
        stdout.write(b"WORKFLOW FAILED\n" if exit_code else b"WORKFLOW PASSED\n")
        return subprocess.CompletedProcess(command, exit_code)

    monkeypatch.setattr(verify_rcms.subprocess, "run", run_child)
    assert verify_rcms.main() == exit_code
    receipt = next((tmp_path / "artifacts").rglob("manifest.json"))
    manifest = json.loads(receipt.read_text())
    assert manifest["passed"] is (exit_code == 0)
    artifact = receipt.parent / "workflow/result.bin"
    assert artifact.read_bytes() == b"workflow artifact"
    assert {"path": "workflow/result.bin", "sha256": evidence_store.file_digest(artifact)} in manifest["files"]
    assert not list((tmp_path / "build/verification/rcms").iterdir())
    recorded = manifest["external_tools"]
    for name, path in paths.items():
        assert recorded[name] == {"path": str(path), "sha256": evidence_store.file_digest(path)}


def test_desktop_reuses_only_intact_evidence_for_the_same_launch_inputs(monkeypatch, tmp_path, capsys):
    from scripts import verification_evidence as evidence_store

    monkeypatch.setattr(evidence_store, 'ROOT', tmp_path)
    monkeypatch.setattr(evidence_store, 'CACHE', tmp_path / 'cache')
    monkeypatch.setattr(verify_rcms, 'ROOT', tmp_path)
    monkeypatch.setattr(verify_rcms, 'git_output', lambda *args: '')
    driver = tmp_path / 'tests/e2e/desktop_driver.py'
    driver.parent.mkdir(parents=True)
    driver.touch()
    monkeypatch.setattr(verify_rcms, 'source_digest', lambda root: 'same-source')
    monkeypatch.setattr(evidence_store, 'source_digest', lambda root: 'same-source')
    monkeypatch.setattr(evidence_store, '_runtime_roots', lambda env, runtime: [])
    from scripts import r_verification_support

    executable_suffix = ".exe" if sys.platform == "win32" else ""
    tool_path = tmp_path / "oracles"
    tool_path.mkdir()
    pdf_text = tool_path / ("pdftotext" + executable_suffix)
    rscript = tool_path / ("Rscript" + executable_suffix)
    pdf_text.write_bytes(b"oracle build A")
    rscript.write_bytes(b"reference build A")
    pdf_text.chmod(0o755)
    monkeypatch.setattr(evidence_store.subprocess, 'check_output', lambda *args, **kwargs: json.dumps({
        'PATH': str(tool_path),
        'R_ENVIRON': None, 'R_ENVIRON_USER': None, 'R_PROFILE': None, 'R_PROFILE_USER': None,
    }))
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("RCMS_RSCRIPT", str(rscript))
    monkeypatch.setattr(r_verification_support, "r_home_from_r_command", lambda env: None)
    monkeypatch.setattr(r_verification_support, "windows_registry_r_homes", lambda: [])
    monkeypatch.delenv('RCMS_AXIS_BASELINE', raising=False)
    monkeypatch.setenv('RCMS_E2E_REUSE_PASSED', '1')
    monkeypatch.setattr(sys, 'argv', ['verify_rcms', 'doctor'])
    env = evidence_store.desktop_environment()
    context = evidence_store.verification_context(env)
    receipt = tmp_path / 'artifacts/verification/typing/gate/command.json'
    receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({
        'exit_code': 0, 'python_platform': 'win32',
        'command': evidence_store.typing_command(Path(env['RCMS_QT6_BUILD_ROOT'])),
        'build_root': env['RCMS_QT6_BUILD_ROOT'],
        'source_sha256': 'same-source', 'source_unchanged': True,
    }))
    for name in ('stdout.log', 'stderr.log'):
        (receipt.parent / name).touch()
    monkeypatch.setenv('RCMS_E2E_CONTEXT', json.dumps({
        'typing': str(receipt), 'verification': context,
        'launch_inputs': evidence_store.verification_launch_inputs(env),
    }))

    evidence = tmp_path / 'evidence'
    evidence.mkdir()
    transcript = evidence / 'stdout.log'
    transcript.write_text('WORKFLOW PASSED\n')
    (evidence / 'manifest.json').write_text(json.dumps({
        'passed': True, 'exit_code': 0, 'verification_context': context,
        'files': [{'path': transcript.name, 'sha256': evidence_store.file_digest(transcript)}],
    }))
    evidence_store.remember_evidence(context, 'doctor', evidence)
    assert verify_rcms.main() == 0
    assert 'Reused passed evidence' in capsys.readouterr().out

    for tool in (pdf_text, rscript):
        original = tool.read_bytes()
        tool.write_bytes(b"replacement bytes")
        changed = evidence_store.verification_context(evidence_store.desktop_environment())
        assert evidence_store.passed_evidence(changed, "doctor") is None
        with pytest.raises(RuntimeError, match="Verification tools changed"):
            verify_rcms.main()
        tool.unlink()
        missing = evidence_store.verification_context(evidence_store.desktop_environment())
        assert evidence_store.passed_evidence(missing, "doctor") is None
        tool.write_bytes(original)
        tool.chmod(0o755)

    def fresh_drive(*args):
        raise RuntimeError('Fresh desktop command required')

    monkeypatch.setattr(verify_rcms, '_desktop_command', fresh_drive)
    with monkeypatch.context() as changed:
        changed.setenv("RCMS_RSCRIPT", str(tmp_path / "other-Rscript"))
        with pytest.raises(RuntimeError, match="Fresh desktop command required"):
            verify_rcms.main()
    monkeypatch.setenv('RCMS_AXIS_BASELINE', '1')
    diagnostic = evidence_store.verification_context(evidence_store.desktop_environment())
    assert diagnostic['sha256'] != context['sha256']
    with pytest.raises(RuntimeError, match='Fresh desktop command required'):
        verify_rcms.main()
    monkeypatch.delenv('RCMS_AXIS_BASELINE')
    with monkeypatch.context() as changed:
        changed.setenv('RCMS_R_LIBS', str(tmp_path / 'different-library'))
        with pytest.raises(RuntimeError, match='Fresh desktop command required'):
            verify_rcms.main()
    with monkeypatch.context() as fresh:
        fresh.setenv('RCMS_E2E_REUSE_PASSED', '0')
        with pytest.raises(RuntimeError, match='Fresh desktop command required'):
            verify_rcms.main()
    transcript.write_text('damaged transcript')
    with pytest.raises(RuntimeError, match='Fresh desktop command required'):
        verify_rcms.main()
    index = next(evidence_store.CACHE.rglob('doctor.json'))
    index.write_text('[]')
    with pytest.raises(RuntimeError, match='Fresh desktop command required'):
        verify_rcms.main()


@pytest.mark.parametrize('code,records,expected', [(0, True, 0), (7, True, 1), (0, False, 1)])
def test_retention_exit_retains_report(monkeypatch, tmp_path, code, records, expected):
    # The desktop subprocess is the external boundary; audit aggregation is real.
    def child(command, **kwargs):
        if records:
            target = tmp_path / 'amino/current'
            target.mkdir(parents=True)
            (target / 'audit.json').write_text(json.dumps({'missing': {s: [] for s in ('copy', 'pdf', 'docx')}}))
        return subprocess.CompletedProcess(command, code, 'controlled child', '')
    monkeypatch.setattr(audit.subprocess, 'run', child)
    monkeypatch.setattr(sys, 'argv', ['audit', '--output', str(tmp_path), 'amino'])
    assert audit.main() == expected
    assert json.loads((tmp_path / 'summary.json').read_text())[0]['exit_code'] == code


def test_missing_rscript_retains_summary(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location('verify_all', ROOT / '.agents/skills/verify-rcms/scripts/verify_all.py')
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from scripts import r_verification_support
    monkeypatch.setattr(r_verification_support, 'resolve_rscript', lambda *a: None)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module.subprocess, 'check_output', lambda *a, **k: '')
    monkeypatch.setattr(sys, 'argv', ['verify_all', '--full'])
    assert module.main() == 1
    summary = next(tmp_path.glob('artifacts/verification/rcms/*/summary.json'))
    assert json.loads(summary.read_text())['passed'] is False
    assert 'Rscript' in (summary.parent / 'preflight.log').read_text()


def test_code_health_real_history(tmp_path):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=tmp_path, text=True).strip()
    git('init', '-q')
    git('config', 'user.name', 'Verification Fixture')
    git('config', 'user.email', 'fixture@example.invalid')
    source = tmp_path / 'src/rc_metastudio'
    source.mkdir(parents=True)
    (source / '__init__.py').touch()
    project = source / 'project'
    project.mkdir()
    (project / '__init__.py').touch()
    project_fixture = project / 'fixture.py'
    project_fixture.write_text('import PyQt6\n')
    r = tmp_path / 'r/RCMetaR/R/check.R'
    r.parent.mkdir(parents=True)
    r.write_text('text <- "first\nsecond\nthird"\nchoose <- function(x) {\n  x <- x + 1\n  if (x) x else 0\n}\n')
    git('add', '.')
    git('commit', '-qm', 'trend has forbidden import')
    trend = git('rev-parse', 'HEAD')
    config = load_config(ROOT)
    config['gates']['max_changed_cyclomatic'] = 1
    before = build_evidence(tmp_path, trend, trend, git_as_of(tmp_path, None, trend), config)
    baseline = tmp_path / 'trend.json'
    baseline.write_text(json.dumps(before))
    project_fixture.write_text('')
    git('add', '.')
    git('commit', '-qm', 'base removes forbidden import')
    base = git('rev-parse', 'HEAD')
    r.write_text(r.read_text().replace('  x <- x + 1\n', ''))
    project_fixture.write_text('import PyQt6\n')
    git('add', '.')
    git('commit', '-qm', 'delete in function and reintroduce forbidden import')
    head = git('rev-parse', 'HEAD')
    result = build_evidence(tmp_path, base, head, git_as_of(tmp_path, None, head), config, baseline)
    gate = json.loads(json.dumps(result))['gate']
    assert isinstance(gate, dict)
    assert 'forbidden imports' in gate['failures']
    assert 'changed-code complexity' in gate['failures']
    assert [(f['name'], f['line']) for f in gate['changed_functions']] == [('choose', 4)]
    clean = build_evidence(tmp_path, head, head, git_as_of(tmp_path, None, head), config)
    clean_gate = json.loads(json.dumps(clean))['gate']
    assert isinstance(clean_gate, dict)
    assert clean_gate['passed']
