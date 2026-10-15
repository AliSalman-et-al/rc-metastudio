# Release-fix verification

Commands run from repository root. Environment: source `docs/ux-audit/2026-10-14-round3/ENV.sh`; `DISPLAY=:0`; `RCMS_AUDIT_DIR=$PWD/docs/ux-audit/2026-10-16-round6-release-fixes`. The retained runner records exact argument arrays, exits, environment and transcript hashes in raw/.

## Before implementation

`uv run python -c 'from tests.e2e.header_geometry import check_headers; check_headers("docs/ux-audit/2026-10-16-round6-reaudit/exports/R6-03-revman-long-arm.svg", ("Intensive individualized cognitive behavioural therapy plus structured clinical follow-up", "Standard clinical care"))'` — exit 1, expected failure of stronger assertion on current-code exported figure:

```
AssertionError: ('header outside device top', 'docs/ux-audit/2026-10-16-round6-reaudit/exports/R6-03-revman-long-arm.svg', 'Intensive', (369.85, -8.418000000000003, 425.97, 4.542000000000001))
```

Harness setup failures retained: an editing command used unavailable bare `python` (`/bin/bash: line 50: python: command not found`); baseline-native then exited 1 because that edit had not run:

```
ImportError: cannot import name 'run_headers' from 'tests.e2e.round6_polish' (/home/ali/Documents/Code/rc-metastudio/tests/e2e/round6_polish.py)
```

The corrected baseline is labelled baseline-native-2. No product source has changed at this stage.
