"""Explore every terminal trace of the three-attempt staple-validation model."""

from dataclasses import dataclass
from itertools import product
from pathlib import Path
import sys

import pytest

from tests.packaging.contract.test_release_boundaries import release_proof_source
from tests.packaging.contract.test_release_shell_failure_safety import posix, run


@dataclass(frozen=True)
class Outcome:
    label: str
    status: int
    output: str


ACCEPTED = Outcome("valid", 0, "The validate action worked!")
TRANSIENT = (
    Outcome("connection-lost", 68, "NSURLErrorDomain Code=-1005"),
    Outcome("timeout", 68, "NSURLErrorDomain Code=-1001"),
)
TERMINAL_FAILURE = (
    Outcome("invalid-ticket", 68, "Could not validate ticket"),
    Outcome("different-status", 69, "NSURLErrorDomain Code=-1005"),
    Outcome("different-code", 68, "NSURLErrorDomain Code=-10010"),
)


def terminal_traces():
    for delays in ((), (15,), (15, 30)):
        for prefix in product(TRANSIENT, repeat=len(delays)):
            for last in (ACCEPTED, *TRANSIENT, *TERMINAL_FAILURE):
                if last in TRANSIENT and len(delays) < 2:
                    continue
                outcomes = (*prefix, last)
                trace = ["wait", "staple"]
                for delay in delays:
                    trace.extend(("validate", f"sleep {delay}"))
                trace.append("validate")
                if last == ACCEPTED:
                    trace.append("verify-signature")
                yield pytest.param(outcomes, trace, id="-".join(outcome.label for outcome in outcomes))


@pytest.mark.parametrize("outcomes,trace", tuple(terminal_traces()))
def test_staple_retry_model(tmp_path: Path, outcomes: tuple[Outcome, ...], trace: list[str]):
    source = tmp_path / "finalize.sh"
    source.write_text(release_proof_source("scripts/sign-notarize-macos-artifact.sh"), newline="\n")
    (tmp_path / "input.dmg").write_bytes(b"exact submitted DMG")
    (tmp_path / "output.dmg").write_bytes(b"previous qualified DMG")
    (tmp_path / "submission.json").write_text('{"id":"model-submission"}')
    (tmp_path / "outcomes.txt").write_text(
        "".join(f"{item.status} {item.output}\n" for item in outcomes), newline="\n",
    )
    result = run(tmp_path, '''
set -euo pipefail
cd "$RCMS_MODEL_ROOT"
export RUNNER_TEMP="$PWD" APPLE_ID=fixture APPLE_APP_SPECIFIC_PASSWORD=fixture APPLE_TEAM_ID=fixture
xcrun() {
    case "$1 $2" in
        'notarytool wait')
            printf 'wait\\n' >> trace.log
            printf '%s' '{"id":"model-submission","status":"Accepted"}'
            ;;
        'stapler staple') printf 'staple\\n' >> trace.log ;;
        'stapler validate')
            printf 'validate\\n' >> trace.log
            count="$(grep -cx validate trace.log)"
            response="$(sed -n "${count}p" outcomes.txt)"
            [[ -n "$response" ]] || exit 97
            printf '%s\\n' "${response#* }"
            return "${response%% *}"
            ;;
        *) exit 97 ;;
    esac
}
sleep() { printf 'sleep %s\\n' "$1" >> trace.log; }
codesign() { printf 'verify-signature\\n' >> trace.log; exit 75; }
python3() { "$RCMS_MODEL_PYTHON" "$@"; }
export -f xcrun sleep codesign python3
bash ./finalize.sh --mode finalize --input-archive input.dmg --output-archive output.dmg \\
    --submission-result submission.json --notarization-result notarization.json \\
    --verification-result validation.log
''', {"RCMS_MODEL_ROOT": posix(tmp_path), "RCMS_MODEL_PYTHON": posix(sys.executable)})
    observed = tmp_path / "trace.log"
    assert observed.is_file(), result.stderr
    assert observed.read_text().splitlines() == trace, result.stderr
    assert result.returncode == (75 if outcomes[-1] == ACCEPTED else outcomes[-1].status)
    assert (tmp_path / "input.dmg").read_bytes() == b"exact submitted DMG"
    assert (tmp_path / "output.dmg").read_bytes() == b"previous qualified DMG"
    validation = (tmp_path / "validation.log").read_text()
    assert all(item.output in validation for item in outcomes)
