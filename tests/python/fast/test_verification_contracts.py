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


def test_typing_before_direct_desktop(monkeypatch, tmp_path):
    calls = []
    def typing(root):
        calls.append('typing')
        raise verify.VerificationError('controlled typing failure')
    monkeypatch.setattr(verify, 'run_typing', typing)
    monkeypatch.setattr(verify_rcms, '_reuse_evidence', lambda *a: calls.append('desktop') or True)
    monkeypatch.setattr(verify_rcms, 'source_digest', lambda: 'same')
    monkeypatch.setattr(sys, 'argv', ['verify_rcms', 'doctor'])
    monkeypatch.delenv('RCMS_E2E_CONTEXT', raising=False)
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
