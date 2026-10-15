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

## Initial statistical/presentation gates

`uv run python scripts/verify_golden_compatibility.py --output-dir build/qt6-verification/golden-compatibility-release-fixes` exited 2 (harness CLI typo):

```
verify_golden_compatibility.py: error: unrecognized arguments: --output-dir build/qt6-verification/golden-compatibility-release-fixes
```

Corrected `--output-root` command, golden-1, exited 0 with `passed: true`. No refresh of any golden was needed. `uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-release-fixes` exited 0: `415 original fields exactly unchanged; maximum difference 0; original numerical contracts, tolerances, and exceptions unchanged.`

## Native header and retained GUI proof

`uv run python docs/ux-audit/2026-10-16-round6-release-fixes/native.py headers-fixed-3` exited 0, WORKFLOW PASSED. Twelve style/name cases; six long-name cases export all four formats. Both initial names, every wrapped word, device top, caption and rule clearance pass in actual display/export SVGs. INSPECTIONS.md records personal inspection of six native after frames and all 24 export renderings.

Retained GUI command: `env QT_QPA_PLATFORM=offscreen uv run python -m pytest tests/python/gui/test_main_window_automation_launch.py tests/python/gui/test_analysis_configuration_layout.py -q`. gui-retained-1 exited 1: 89 passed, 1 skipped; stale popup-scroll assertion requires scroll even when the shown popup fits its complete choices. Verbatim assertion:

```
E                   AssertionError: assert 0 > 0
FAILED tests/python/gui/test_analysis_configuration_layout.py::test_method_parameters_variants_stay_bounded_and_stable
```

A detached test-owned c37e427 worktree reproduced the same failure (`gui-baseline-popup`: 1 failed, 23 deselected). The broader baseline attempt additionally failed its subprocess form-manifest path because forms were not generated in that checkout; its full error remains raw/gui-baseline-check.log. No baseline product file was edited. The owned clean worktree was removed after the comparison. Corrected the assertion to evaluate overflow against the **shown** popup viewport, retaining the scroll requirement when content actually overflows. gui-retained-2 exited 0: **90 passed, 1 skipped**, 18.60s.

Curation initially failed before PDF rendering (`curate-1`):

```
TypeError: QPdfDocument(parent: QObject|None): not enough arguments
```

Passing the required parent argument fixed the evidence script; curate-2 completed, retaining 55 artifacts. A pre-start queue waiter was stopped by exact owned PID to correct timeout-runner flags; no native child had started (raw/QUEUE-RESTART.json).

The first coefficient helper returned exit 0 but its artifact inventory showed only the matrix's ordinary result captures: the targeted loop compared human titles against semantic image keys and exercised no coefficient editors. That receipt is **not** accepted as R6-07 proof. Corrected selection to both exact coefficient semantic IDs and required exactly two exercised plots. The replay additionally uses the exact six-study re-audit input (TP 19–24, FN 10–15, FP 1, TN 81–86, Dose 1–6), saved/reopened before fitting. This is a harness coverage repair, not a statistical assertion relaxation.

Stress-1 failed an added assertion that incorrectly equated an asymmetric entered interval bound with the symmetric log-scale fitted interval reconstructed from that interval. Stored input/public-conversion checks passed. Verbatim failure (HR, reported-ratio input):

```
AssertionError: ('tiny positive bound lost', '0.123457 [1.371742e-11, 1.1111e+09]', {'estimate': 0.12345678901234566, 'lower': 1.2345678901234567e-08, 'upper': 1000000000000.0, 'se': 0.2626128657194451, 'scale': 'ratio', 'confidence': 95.0, 'source': 'reported', 'unit': 'person-years'})
```

Corrected the assertion to compare the displayed positive bound with the independently validated fitted effect/SE's 95% normal interval. No production estimate or stored input was changed. Stress-2 is a fresh replay; stress-1 remains failed.
