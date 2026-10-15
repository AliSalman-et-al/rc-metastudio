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

Baseline-native-2 exited 1 on current code (45-character RevMan heading), proving the new caption assertion catches a defect the former rule-only assertion missed:

```
AssertionError: ('header/caption clearance', '/home/ali/Documents/Code/rc-metastudio/docs/ux-audit/2026-10-16-round6-release-fixes/raw/baseline-headers-2/analysis-scratch/forest-5ee417d61700.display.svg', {'text': 'Cognitive', 'box': (368.42, 34.391999999999996, 427.40000000000003, 47.352)}, 31.392000000000003)
```

First implementation replay headers-fixed-1 exited 1: the unified BMJ header placement still used the Default rule anchor while BMJ's rule is 0.55 rows higher. Kept the BMJ rule/data clearance and anchored headers/reservation to that actual rule for headers-fixed-2.

```
AssertionError: ('header rule crosses text', '/home/ali/Documents/Code/rc-metastudio/docs/ux-audit/2026-10-16-round6-release-fixes/raw/headers-fixed-1/analysis-scratch/forest-d1dc731759f3.display.svg', 'Events / Total', (220.14000000000001, 104.15199999999999, 303.34000000000003, 117.112), (0.0, 108.69, 1199.53, 108.69))
```

Headers-fixed-2 passed geometry through the short/medium names, then correctly failed complete-word identity on the full 89-character name. The independent R presentation normalizer also truncated forest labels to 80 characters, after the repaired setup field. Removed that forest truncation and its obsolete ceiling assertions; existing unrelated study/bubble display abbreviations retain their current policy.

```
AssertionError: ('arm header lost words', '/home/ali/Documents/Code/rc-metastudio/docs/ux-audit/2026-10-16-round6-release-fixes/raw/headers-fixed-2/analysis-scratch/forest-453bf8d763a8.display.svg', 'Intensive individualized cognitive behavioural therapy plus structured clinical follow-up', [{'text': 'Intensive', 'box': (401.65, 78.982, 457.77, 91.942)}])
```
