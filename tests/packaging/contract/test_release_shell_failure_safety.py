"""Execute release shell control flow against disposable trees and OS stand-ins."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

import pytest

ROOT = Path(os.environ.get('RCMS_REPAIR_SOURCE_ROOT', Path(__file__).resolve().parents[3]))
BASH = shutil.which('bash') or 'C:/Program Files/Git/bin/bash.exe'


def posix(path):
    value = Path(path).resolve().as_posix()
    return '/' + value[0].lower() + value[2:] if len(value) > 1 and value[1] == ':' else value


def run(tmp_path, script, extra=None):
    if not Path(BASH).is_file():
        pytest.skip('bash unavailable')
    path = tmp_path / 'drive.sh'
    path.write_text(script, newline='\n')
    command = [BASH, posix(path)]
    receipt = tmp_path / 'command.txt'
    receipt.write_text(f'{BASH} {posix(path)}\n', encoding='utf-8')
    stdout = tmp_path / 'stdout.log'
    stderr = tmp_path / 'stderr.log'
    with stdout.open('w', encoding='utf-8') as out, stderr.open('w', encoding='utf-8') as err:
        # This is a failure-recovery check, so allow for MSYS and Python startup under CI load.
        result = subprocess.run(command, stdout=out, stderr=err,
                                env={**os.environ, **(extra or {})}, timeout=120)
    with receipt.open('a', encoding='utf-8') as log:
        log.write(f'exit={result.returncode}\n')
    return subprocess.CompletedProcess(command, result.returncode,
                                       stdout.read_text(encoding='utf-8'),
                                       stderr.read_text(encoding='utf-8'))


def test_linux_failed_qualification_preserves_previous_final_archive(tmp_path):
    script = '''set -euo pipefail
cd "''' + posix(tmp_path) + '''"
step() { :; }
die() { echo "$*" >&2; exit 1; }
work_root="$PWD/work"; artifact_name=fixture; artifact_dir="$PWD"
archive_root="$PWD/app"; qualification_root="$PWD/qualification"
artifact_path="$PWD/release.tar.gz"; r_home="$PWD/R"
repo_root="$PWD"; smoke_log="$PWD/smoke.log"; smoke_evidence="$PWD/smoke.json"
python_exe="$PWD/fail-python"
mkdir -p "$archive_root" "$qualification_root" "$r_home" "$PWD/tools"
printf '#!/bin/sh\nexit 0\n' > "$archive_root/LaunchRCMetaStudio.sh"
chmod +x "$archive_root/LaunchRCMetaStudio.sh"
printf '#!/bin/sh\nshift\nexec "$@"\n' > "$PWD/tools/xvfb-run"
chmod +x "$PWD/tools/xvfb-run"
export PATH="$PWD/tools:$PATH"
printf '#!/bin/sh\necho injected-smoke-failure >&2\nexit 71\n' > "$python_exe"
chmod +x "$python_exe"
printf previous-qualified > "$artifact_path"
source "$RCMS_FINALIZE_SCRIPT"
'''
    result = run(tmp_path, script, {'RCMS_FINALIZE_SCRIPT': posix(ROOT / 'scripts/finalize-linux-package.sh')})
    assert result.returncode != 0
    assert (tmp_path / 'release.tar.gz').read_bytes() == b'previous-qualified'
    retained = list(tmp_path.glob('.linux-candidate.*/qualification/packaged-smoke.stderr.log'))
    assert len(retained) == 1 and 'injected-smoke-failure' in retained[0].read_text()


def test_macos_failed_archive_inspection_preserves_previous_zip(tmp_path):
    script = '''set -euo pipefail
cd "''' + posix(tmp_path) + '''"
step() { :; }
copy_tree() { mkdir -p "$(dirname "$2")"; cp -R "$1" "$2"; }
ditto() { printf new-unqualified > "${@: -1}"; }
python3() { echo injected-inspection-failure >&2; return 71; }
archive_staging_root="$PWD/staging"; archive_root_dir="$archive_staging_root/root"
app_bundle="$PWD/app"; qualification_root="$PWD/qualification"
artifact_dir="$PWD"; artifact_name=fixture; zip_path="$PWD/final.zip"
archive_inspection_path="$PWD/archive-inspection.json"
qualification_evidence_path="$PWD/evidence.json"
archive_root_name=root; skip_smoke=0; r_framework_version=4.6
mkdir -p "$app_bundle" "$qualification_root"
printf previous-qualified > "$zip_path"
source "$RCMS_FINALIZE_SCRIPT"
'''
    result = run(tmp_path, script, {'RCMS_FINALIZE_SCRIPT': posix(ROOT / 'scripts/finalize-macos-package.sh')})
    assert result.returncode == 71, result.stderr
    assert 'injected-inspection-failure' in result.stderr
    assert (tmp_path / 'final.zip').read_bytes() == b'previous-qualified'


@pytest.mark.parametrize('failure', ['wait', 'multiple-volumes'])
def test_macos_trust_cleanup_preserves_input_and_detaches_all(tmp_path, failure):
    commands = tmp_path / 'commands'
    commands.mkdir()
    input_path = tmp_path / 'app.tmp.dmg'
    input_path.write_bytes(b'only input')
    (tmp_path / 'submission.json').write_text('{"id":"fixture-id"}')
    bodies = {
        'python3': 'exec \"' + posix(sys.executable) + '\" \"$@\"\n',
        'xcrun': 'if [ "$2" = wait ]; then ' + ('exit 71' if failure == 'wait' else 'printf \'{"id":"fixture-id","status":"Accepted"}\'') + '; fi\n',
        'codesign': 'exit 0\n',
        'hdiutil': '''case "$1" in
attach) printf '%s' '<plist><dict><key>system-entities</key><array><dict><key>mount-point</key><string>/fixture-volume-one</string></dict><dict><key>mount-point</key><string>/fixture-volume-two</string></dict></array></dict></plist>' ;;
detach) printf '%s\n' "$2" >> "$FIXTURE/detached" ;;
esac
''',
    }
    for name, body in bodies.items():
        path = commands / name
        path.write_text('#!/bin/bash\n' + body, newline='\n')
        path.chmod(0o755)
    script = '''set -e
export PATH="''' + posix(commands) + ''':$PATH"
export APPLE_ID=fixture APPLE_APP_SPECIFIC_PASSWORD=fixture APPLE_TEAM_ID=fixture
export RUNNER_TEMP="''' + posix(tmp_path) + '''"
bash "''' + posix(ROOT / 'scripts/sign-notarize-macos-artifact.sh') + '''" --mode finalize \
  --input-archive "''' + posix(input_path) + '''" --output-archive "''' + posix(tmp_path / 'app.dmg') + '''" \
  --submission-result "''' + posix(tmp_path / 'submission.json') + '''" \
  --notarization-result "''' + posix(tmp_path / 'notarization.json') + '''" \
  --verification-result "''' + posix(tmp_path / 'verification.txt') + '''"
'''
    result = run(tmp_path, script, {'FIXTURE': posix(tmp_path)})
    assert result.returncode != 0
    assert input_path.read_bytes() == b'only input'
    if failure == 'multiple-volumes':
        assert 'Expected exactly one mounted' in result.stderr
        assert set((tmp_path / 'detached').read_text().splitlines()) == {'/fixture-volume-one', '/fixture-volume-two'}
