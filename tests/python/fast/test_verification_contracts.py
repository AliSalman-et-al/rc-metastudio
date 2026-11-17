"""Failure controls for verification orchestration, isolated from GUI/R installs."""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import verify, verify_rcmetar_r_stack as stack, verify_rcms
from scripts import audit_report_retention as audit
from scripts import qt6_build_impl as qtbuild
from scripts.code_health import build_evidence, git_as_of, load_config

ROOT = Path(__file__).resolve().parents[3]


def test_smoke_regenerates_existing_inputs(monkeypatch, tmp_path):
    module = tmp_path / 'generated/rc_metastudio/forms/ui_about_legal.py'
    resource = tmp_path / 'resources/icons.rcc'
    for path in (module, resource):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('stale')
    def generate(root):
        for path in (module, resource):
            path.write_text('current')
        return module, resource
    monkeypatch.setattr(qtbuild, 'generate', generate)
    assert qtbuild._smoke_inputs(tmp_path) == (module, resource)
    assert module.read_text() == resource.read_text() == 'current'


def test_selected_python_rpy2_identity(tmp_path):
    # A real different interpreter (stdlib-only venv) cannot inherit our metadata.
    subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(tmp_path / 'python')], check=True)
    python = tmp_path / 'python/Scripts/python.exe' if sys.platform == 'win32' else tmp_path / 'python/bin/python'
    assert stack.verify_rpy2_identities(sys.executable) == stack.REQUIRED_RPY2_IDENTITIES
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


def test_explicit_rscript_cannot_be_overridden(tmp_path):
    root = tmp_path / 'R'
    (root / 'bin').mkdir(parents=True)
    (root / 'bin/Rscript.exe').touch()
    other = tmp_path / 'other.exe'
    other.touch()
    with pytest.raises(verify.VerificationError, match='conflict'):
        verify.selected_rscript(argparse.Namespace(rscript=str(other), r_runtime_root=str(root)))


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
    monkeypatch.setattr(evidence_store.subprocess, 'check_output', lambda *args, **kwargs: json.dumps({
        name: None for name in ('R_ENVIRON', 'R_ENVIRON_USER', 'R_PROFILE', 'R_PROFILE_USER')
    }))
    monkeypatch.delenv('RCMS_AXIS_BASELINE', raising=False)
    monkeypatch.setenv('RCMS_E2E_REUSE_PASSED', '1')
    monkeypatch.setattr(sys, 'argv', ['verify_rcms', 'doctor'])
    env = evidence_store.desktop_environment()
    context = evidence_store.verification_context(env)
    receipt = tmp_path / 'artifacts/verification/typing/gate/command.json'
    receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({
        'exit_code': 0, 'python_platform': 'win32', 'command': [sys.executable, '-m', 'ty', 'check'],
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

    def fresh_drive(*args):
        raise RuntimeError('Fresh desktop command required')

    monkeypatch.setattr(verify_rcms, '_desktop_command', fresh_drive)
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
    (source / 'project_fixture.py').write_text('import PyQt6\n')
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
    (source / 'project_fixture.py').write_text('')
    git('add', '.')
    git('commit', '-qm', 'base removes forbidden import')
    base = git('rev-parse', 'HEAD')
    r.write_text(r.read_text().replace('  x <- x + 1\n', ''))
    (source / 'project_fixture.py').write_text('import PyQt6\n')
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
