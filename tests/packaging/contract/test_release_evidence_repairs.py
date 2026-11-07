"""Disposable release inputs and single-defect qualification controls.

No native installer, mount, signing service or statistical backend is invoked.
"""
from pathlib import Path
import importlib.util
import json
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows argument transport')
@pytest.mark.parametrize('shell', ['pwsh', 'powershell'])
def test_private_installer_watchdog_preserves_directory_arguments(tmp_path, shell):
    """Paths with spaces must reach the child without literal quote characters.

    Run the actual array and watchdog invocation with an argv recorder replacing
    the installer, so no registry, download or installation is involved.
    """
    executable = shutil.which(shell)
    if not executable:
        pytest.skip(f'{shell} unavailable')
    source = (ROOT / 'scripts/package-windows.ps1').read_text()
    argument_start = source.index('    $installerArgs = @(')
    argument_end = source.index('\n    $registrySnapshots', argument_start)
    call_start = source.index('            & uv run --locked python', argument_end)
    call_end = source.index('\n            $installerExitCode', call_start)
    recorder = tmp_path / 'record args.py'
    output = tmp_path / 'argv.json'
    recorder.write_text('import json, os, sys\nfrom pathlib import Path\n'
                        'Path(os.environ["RCMS_ARGV_OUTPUT"]).write_text(json.dumps(sys.argv[1:]))\n')
    quote = lambda value: "'" + str(value).replace("'", "''") + "'"
    stage = tmp_path / 'private R stage'
    log = tmp_path / 'installer log.txt'
    script = tmp_path / 'drive.ps1'
    script.write_text('\n'.join([
        '$ErrorActionPreference = "Stop"',
        '$repoRoot = ' + quote(ROOT), '$rStage = ' + quote(stage),
        '$installerLog = ' + quote(log), '$rInstaller = ' + quote(sys.executable),
        '$env:RCMS_ARGV_OUTPUT = ' + quote(output),
        source[argument_start:argument_end],
        '$installerArgs = @(' + quote(recorder) + ') + $installerArgs',
        source[call_start:call_end], 'exit $LASTEXITCODE',
    ]))
    command = [executable, '-NoProfile', '-File', str(script)]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=45)
    (tmp_path / 'command.json').write_text(json.dumps(command))
    (tmp_path / 'stdout.log').write_text(result.stdout)
    (tmp_path / 'stderr.log').write_text(result.stderr)
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text()) == [
        '/CURRENTUSER', '/VERYSILENT', '/SUPPRESSMSGBOXES', '/SP-', '/NORESTART',
        f'/DIR={stage}', f'/LOG={log}',
    ]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def version_tree(tmp_path):
    for name in ('pyproject.toml', 'uv.lock', 'src/rc_metastudio/__init__.py',
                 'r/RCMetaR/DESCRIPTION', 'CHANGELOG.md'):
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dest)
    return {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}


@pytest.mark.parametrize('defect', ['late-field', 'changelog', 'duplicate', 'date'])
def test_bump_rejects_bad_inputs_without_writing(tmp_path, defect):
    version_tree(tmp_path)
    if defect == 'late-field':
        (tmp_path / 'r/RCMetaR/DESCRIPTION').write_text('malformed\n')
    if defect == 'changelog':
        (tmp_path / 'CHANGELOG.md').write_text('no release heading\n')
    if defect == 'duplicate':
        path = tmp_path / 'src/rc_metastudio/__init__.py'
        path.write_text(path.read_text() + '\n__version__ = "0.3.1"\n')
    before = {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    with pytest.raises(SystemExit):
        load('bump_version').main(['9.8.7', '--root', str(tmp_path), '--date',
                                  '2026-02-30' if defect == 'date' else '2026-02-28'])
    assert {p: p.read_bytes() for p in before} == before


def test_bump_write_failure_restores_bytes(tmp_path, monkeypatch):
    before = version_tree(tmp_path)
    bump = load('bump_version')
    write = bump.write_text
    def fail(path, text):
        if path.name == 'uv.lock':
            raise OSError('injected write failure')
        write(path, text)
    monkeypatch.setattr(bump, 'write_text', fail)
    with pytest.raises(OSError, match='injected'):
        bump.main(['9.8.7', '--root', str(tmp_path)])
    assert {p: p.read_bytes() for p in before} == before


def test_bump_success(tmp_path):
    version_tree(tmp_path)
    assert load('bump_version').main(['9.8.7', '--root', str(tmp_path), '--date', '2024-02-29']) == 0
    assert 'Version: 9.8.7' in (tmp_path / 'r/RCMetaR/DESCRIPTION').read_text()


@pytest.mark.parametrize('defect', ['aggregate', 'observation'])
def test_exact_windows_smoke_rejects_sample_failure(defect):
    inspector = load('inspect_windows_deployment')
    samples = {'passed': True, 'manifest_sha256': 'a'*64, 'projects': [
        {'project': 'a.rcms', 'sha256': 'a'*64, 'semantic_sha256': 'b'*64,
         'opened_in_packaged_application': True}]}
    value = {'passed': True, 'execution': {'positional_user_entry_exit_code': 0,
             'clean_exit': True}, 'workflows': {'sample_projects': samples}}
    log = 'startup-project:normal-entry-point-passed\npackaged-workflow:post-close'
    inspector._validate_windows_extracted_smoke(value, log)
    if defect == 'aggregate':
        samples['passed'] = False
    else:
        samples['projects'][0]['opened_in_packaged_application'] = False
    with pytest.raises(inspector.DeploymentInspectionError, match='incomplete'):
        inspector._validate_windows_extracted_smoke(value, log)


def test_sample_manifest_must_cover_shipped_files(tmp_path, monkeypatch):
    module = load('assemble_packaged_smoke_evidence')
    (tmp_path / 'manifest.json').write_text(json.dumps({'projects': []}))
    (tmp_path / 'unlisted.rcms').write_bytes(b'project')
    def unexpected(*args, **kwargs):
        pytest.fail('must reject inventory before running executable')
    monkeypatch.setattr(module, '_run_packaged', unexpected)
    with pytest.raises(ValueError, match='sample inventory'):
        module.capture_sample_observations(Path('unused'), sample_root=tmp_path,
                                           output=tmp_path / 'result.json')


def test_extracted_inventory_must_match_original():
    module = load('inspect_macos_deployment')
    probe = {'r': {'kit_sha256': 'a'*64}}
    original = {'source_commit': 'a'*40, 'inventory': {'files': [{'path': 'Contents/x', 'sha256': 'b'*64}]}}
    extracted = {**original, 'schema_version': 1, 'target': 'macos-arm64',
                 'architecture': 'arm64', 'stack': module.EXPECTED_VERSIONS,
                 'qt_dependency_collector': 'PyInstaller',
                 'runtime_probe_canonical_sha256': module._canonical_json_sha256(probe)}
    module._validate_extracted_deployment(original, probe, extracted, 'macos-arm64')
    extracted['inventory'] = {'files': [{'path': 'Contents/x', 'sha256': 'c'*64}]}
    with pytest.raises(module.MacOSDeploymentInspectionError, match='inventory'):
        module._validate_extracted_deployment(original, probe, extracted, 'macos-arm64')


def test_kit_probe_digest_must_match_manifest(monkeypatch):
    module = load('inspect_macos_deployment')
    manifest = {'kind': 'rc-metastudio-r-integration-kit', 'target': 'macos-arm64',
                'architecture': 'arm64', 'cffi_mode': 'API', 'kit_sha256': 'a'*64}
    derivation = {'kit_sha256': 'a'*64}
    # This boundary is separately validated by existing kit contract tests.
    monkeypatch.setattr(module, '_valid_r_kit_derivation', lambda *args: True)
    monkeypatch.setattr(module, '_valid_r_kit_probe_digests', lambda *args: True)
    assert module._valid_r_kit_identity(manifest, derivation, 'macos-arm64', 'arm64', {'kit_sha256': 'a'*64}, {})
    assert not module._valid_r_kit_identity(manifest, derivation, 'macos-arm64', 'arm64', {'kit_sha256': 'b'*64}, {})


def test_retained_symlink_escape(tmp_path):
    module = load('macos_evidence')
    root = tmp_path / 'evidence'
    root.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    try:
        (root / 'link').symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        if getattr(exc, 'winerror', None) == 1314:
            pytest.skip('Windows symlink privilege unavailable; requires capable lane')
        raise
    with pytest.raises(module.EvidenceError, match='within'):
        module._retained_path({'retained_path': 'link/record'}, 'probe', root)


@pytest.mark.parametrize('diagnostic', ['packaged_phases', 'packaged_smoke', 'packaged_r_graph', 'r_profile_quarantine'])
def test_standalone_diagnostics_reject_unrelated_contents(tmp_path, diagnostic):
    from tests.python.fast.test_qt6_macos_feasibility import _valid_evidence, _materialize_retained_evidence
    module = load('macos_evidence')
    evidence = _valid_evidence()
    _materialize_retained_evidence(evidence, tmp_path)
    module.validate_evidence(evidence, 'macos-arm64', evidence_dir=tmp_path,
                             architecture_reader=lambda path: ['arm64'])
    import hashlib
    record = evidence['diagnostics'][diagnostic]
    path = tmp_path / record['path']
    path.write_text('{}')
    record['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(module.EvidenceError, match='diagnostic'):
        module.validate_evidence(evidence, 'macos-arm64', evidence_dir=tmp_path,
                                 architecture_reader=lambda path: ['arm64'])


def test_sample_records_cover_deployment_inventory():
    module = load('inspect_macos_deployment')
    deployment = {'inventory': {'files': [
        {'path': 'Contents/Resources/sample_projects/a.rcms', 'sha256': 'a'*64},
        {'path': 'Contents/Resources/sample_projects/manifest.json', 'sha256': 'b'*64}]}}
    samples = {'passed': True, 'manifest_sha256': 'b'*64, 'projects': [
        {'project': 'a.rcms', 'sha256': 'a'*64, 'semantic_sha256': 'c'*64,
         'opened_in_packaged_application': True}]}
    smoke = {'workflows': {'sample_projects': samples}}
    module._validate_shipped_samples(deployment, smoke)
    deployment['inventory']['files'].append(
        {'path': 'Contents/Resources/sample_projects/omitted.rcms', 'sha256': 'd'*64})
    with pytest.raises(module.MacOSDeploymentInspectionError, match='sample inventory'):
        module._validate_shipped_samples(deployment, smoke)


def test_kit_probe_paths_bind_packaged_bytes(tmp_path):
    import hashlib
    module = load('inspect_macos_deployment')
    frameworks = tmp_path / 'Contents/Frameworks'
    frameworks.mkdir(parents=True)
    bridge = frameworks / '_rinterface_cffi_api.so'
    lib = frameworks / 'libR.dylib'
    bridge.write_bytes(b'bridge')
    lib.write_bytes(b'libR')
    derivation = {'final': {name: {'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                           for name, path in [('api_bridge', bridge), ('r_shared_library', lib)]}}
    r = {'shared_library_path': str(lib)}
    rpy2 = {'api_bridge_path': str(bridge)}
    module._validate_kit_probe_paths(tmp_path, derivation, r, rpy2)
    other = tmp_path / 'other'
    other.mkdir()
    (other / bridge.name).write_bytes(b'bridge')
    rpy2['api_bridge_path'] = str(other / bridge.name)
    with pytest.raises(module.MacOSDeploymentInspectionError, match='paths differ'):
        module._validate_kit_probe_paths(tmp_path, derivation, r, rpy2)
