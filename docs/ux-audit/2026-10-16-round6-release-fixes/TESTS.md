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

The corrected exact-input coefficient-2 drive failed the real editor-default assertion: the renderer defaulted to log spacing, but the editor still inferred the natural default from the parent Sens/Spec metric. Verbatim failure:

```
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/release_fixes.py", line 49, in edit
    assert dialog.axis_scale.isVisible() and dialog.axis_scale.currentData() == 'transformed'
AssertionError
```

The dedicated OR coefficient editor now resolves ratio scale before its parent's proportion metric. This is a product correction, not a relaxed expectation.

Renderer checks exited 1 on three obsolete blank-header expectations, and no other failure:

```
── 1. Failure ('test-forest-metafor-renderer.R:885:5'): BMJ Forest Style builds 
Expected `bundle$ilab$headers` to equal `case$expected_headers`.
Differences:
`actual`:   "Events / Total" "Events / Total" "Weight (%)"
`expected`: ""               ""               "Weight (%)"
── 2. Failure ('test-forest-metafor-renderer.R:1438:3'): single-arm binary RevMa
Expected `bmj.bundle$ilab$headers` to equal `c("", "Weight (%)")`.
Differences:
`actual`:   "Events / Total" "Weight (%)"
`expected`: ""               "Weight (%)"
── 3. Failure ('test-forest-metafor-renderer.R:1983:3'): subgroup workflow saves
Expected `bundle$ilab$headers` to equal `c("", "", "Weight (%)")`.
Differences:
`actual`:   "Events / Total" "Events / Total" "Weight (%)"
`expected`: ""               ""               "Weight (%)"
```

Updated those existing presentation assertions and removed the unused BMJ group-rule generator/assertions replaced by shared measured headers. Reinstall precedes further native driving.

Small-screen-1 exited 1 because the synthetic geometry patch changed only the default geometry function; native screen-change handling correctly switched back to the real 1600px screen. Its width therefore expanded to the real-screen 720px preference:

```
AssertionError: ('AboutLegalDialog', PyQt6.QtCore.QRect(86, 74, 720, 216), PyQt6.QtCore.QRect(50, 50, 360, 240))
```

Small-screen-2 uses the adaptive controller's explicit available-geometry provider, which is the supported seam for synthetic bounds. This is native rendering/scrolling under a synthetic 360×240 available rectangle, **not** an OS-resolution or DPI qualification. Ordinary screen proof uses the real native screen, without that substitution.

Small-screen-2 proved About's bounded frame and scrolling, then failed a harness assumption that the shorter continuous question must also overflow:

```
AssertionError: ('ContinuousBackCalculationDialog', PyQt6.QtCore.QRect(86, 74, 324, 216), 0)
```

Its content fits in that rectangle. The final proof accepts a fully fitting content widget with visible choices, or native scrolling when content needs it; About's long content must scroll. This preserves the actual reachability requirement rather than requiring an unnecessary scrollbar.


## Final qualification

Exactly one `uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh` invocation ran in this release-fix round: **full-release, exit 0**, 2,978.018603 seconds. Source/test HEAD 07c4f4a; worktree clean before and after. Native and full qualification use private pinned R 4.6.1; no system R library was changed.

Verbatim full-profile results:

```
Status: OK
============================== 9 passed in 53.50s ==============================
======================= 123 passed in 2454.75s (0:40:54) =======================
[RCMetaR-r-stack] RCMetaR R Stack Slice verification complete
```

Complete-run directory: `artifacts/verification/rcms/20261015T221301Z-c7951fab-complete/`. All three outer commands exit 0, summary passed true. Authorities: passed true, case_count 91. Strict golden capture: passed true, 11 cases; no refresh. Doctor exit 0. FULL-PROFILE.json binds all 124 child receipts and retained artifacts, with observed runtime identities.

Final exact-field check against `build/qt6-verification/golden-compatibility-r-stack-v2` exited 0:

```
415 original fields exactly unchanged; maximum difference 0; original numerical contracts, tolerances, and exceptions unchanged.
```

Accepted final native receipts: headers-fixed-3, presentation-1, back-continuous-1, back-binary-1, pln-axes-1, stress-2, coefficient-4 and small-screen-3 — all exit 0. Earlier failures/incomplete zero-exit receipts are retained and excluded from acceptance. R package checks in the final full run pass the corrected semantic BMJ header assertions.

Final evidence integrity passes: 124 profile receipts / 9,469 retained artifacts, 89 curated files / 65 inspected images, current source/install bytes, unchanged baseline files and no surviving recorded owned roots. `bash -n REPRODUCE.sh` and `git diff --check` exit 0.

## Exact run ledger (generated)

Argument arrays, environment, dates, elapsed time and transcript hashes are in OUTCOMES.json. Earlier failed attempts remain failed.

### back-binary-1 — exit 0

```sh
uv run python scripts/run_with_timeout.py --timeout-seconds 900 --label back-binary-1 -- uv run python scripts/verify_rcms.py calculator-mode-back-binary --native
```

Transcript: `raw/back-binary-1.log`; SHA-256 `1806ba47fdb784ef6b135342376c4e75535b40c9bb940f096e0bcb19d7eeb6ab`.

### back-continuous-1 — exit 0

```sh
uv run python scripts/run_with_timeout.py --timeout-seconds 900 --label back-continuous-1 -- uv run python scripts/verify_rcms.py calculator-mode-back-continuous --native
```

Transcript: `raw/back-continuous-1.log`; SHA-256 `29ac80c8030712876ec30f1405f86391ee41c4fdceced37a1fc5a9a8a6824ca6`.

### baseline-geometry — exit 1

```sh
uv run python -c 'from tests.e2e.header_geometry import check_headers; check_headers("docs/ux-audit/2026-10-16-round6-reaudit/exports/R6-03-revman-long-arm.svg", ("Intensive individualized cognitive behavioural therapy plus structured clinical follow-up", "Standard clinical care"))'
```

Transcript: `raw/baseline-geometry.log`; SHA-256 `3b382cbc357b2904d368fd23e3d381ec6a6c13fb77d4c7409f1709d12019fe7a`.

### baseline-native-2 — exit 1

```sh
uv run python docs/ux-audit/2026-10-16-round6-release-fixes/native.py baseline-headers-2
```

Transcript: `raw/baseline-native-2.log`; SHA-256 `c99f0a4bb2214746a9d3e7cb39df67534cf429c775482a74e7e4730a530b47fe`.

### baseline-native — exit 1

```sh
uv run python docs/ux-audit/2026-10-16-round6-release-fixes/native.py baseline-headers
```

Transcript: `raw/baseline-native.log`; SHA-256 `8f1ca76c3e4f6b40ad2321beea53035471bc5fe399728a333359a370d3874e41`.

### coefficient-1 — exit 0

```sh
uv run python scripts/run_with_timeout.py --timeout-seconds 900 --label coefficient-1 -- uv run python scripts/verify_rcms.py project-release-coefficients --native
```

Transcript: `raw/coefficient-1.log`; SHA-256 `56dbb0f2e064d03d58540f60b071255ddd8e9899bb9926e8a7b726913d558bd0`.

### coefficient-2 — exit 1

```sh
uv run python scripts/verify_rcms.py project-release-coefficients --native
```

Transcript: `raw/coefficient-2.log`; SHA-256 `f4568c3061fb4ad6f1d85704287ef53c471df36f6f9858695909af3ec6cd75b4`.

### coefficient-3 — exit 0

```sh
uv run python scripts/verify_rcms.py project-release-coefficients --native
```

Transcript: `raw/coefficient-3.log`; SHA-256 `2112da9fbc07598ec740eef2c87924236d3a22de03af23855784887b735ba84b`.

### coefficient-4 — exit 0

```sh
uv run python scripts/verify_rcms.py project-release-coefficients --native
```

Transcript: `raw/coefficient-4.log`; SHA-256 `1e3d779a5dcb42544e107c10cd1726b4a88cd171f29123cc8a33dd4f9f7fede0`.

### curate-1 — exit 1

```sh
env QT_QPA_PLATFORM=offscreen uv run python docs/ux-audit/2026-10-16-round6-release-fixes/curate.py
```

Transcript: `raw/curate-1.log`; SHA-256 `8695f78eec00a83b40b5546065529fa1f697db3edb49e0494857a350ca1a037c`.

### curate-2 — exit 0

```sh
env QT_QPA_PLATFORM=offscreen uv run python docs/ux-audit/2026-10-16-round6-release-fixes/curate.py
```

Transcript: `raw/curate-2.log`; SHA-256 `1da715f78b4d2c3a0e580c153de30de5e72f6bf4546fda05b3d81cfa98466851`.

### full-release — exit 0

```sh
uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh
```

Transcript: `raw/full-release.log`; SHA-256 `fa722667c033b91bd472ca8b19d67967ab4664c89dd8c69648d93ef7583939bf`.

### golden-1 — exit 0

```sh
uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-release-fixes
```

Transcript: `raw/golden-1.log`; SHA-256 `1bf7185a7143ba38bd9a878433202f31c58222a4398800eca956d3412b81bab6`.

### golden-final — exit 0

```sh
uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-release-final
```

Transcript: `raw/golden-final.log`; SHA-256 `40411e9dc7fa4c9b67acbcc60ebd44c9d4900ffb63db14b428f20ed9c44f3c87`.

### golden-initial — exit 2

```sh
uv run python scripts/verify_golden_compatibility.py --output-dir build/qt6-verification/golden-compatibility-release-fixes
```

Transcript: `raw/golden-initial.log`; SHA-256 `294794d5365dd27591dcebf686ec4be8d4230dac100ac2b9163c5d7bb8aa4890`.

### gui-baseline-check — exit 1

```sh
env QT_QPA_PLATFORM=offscreen PYTHONPATH=/home/ali/Documents/Code/rc-metastudio/build/release-baseline-check/src:/home/ali/Documents/Code/rc-metastudio/build/release-baseline-check /home/ali/Documents/Code/rc-metastudio/.venv/bin/python -c 'import os,sys; os.chdir("build/release-baseline-check"); import pytest; sys.exit(pytest.main(["tests/python/gui/test_main_window_automation_launch.py","tests/python/gui/test_analysis_configuration_layout.py","-q"]))'
```

Transcript: `raw/gui-baseline-check.log`; SHA-256 `821ffc090fc9bcee717ffb092203d5bb06c90775a109ac2f736054ab5002c8f3`.

### gui-baseline-popup — exit 1

```sh
env QT_QPA_PLATFORM=offscreen PYTHONPATH=/home/ali/Documents/Code/rc-metastudio/build/release-baseline-check/src:/home/ali/Documents/Code/rc-metastudio/build/release-baseline-check /home/ali/Documents/Code/rc-metastudio/.venv/bin/python -c 'import os,sys; os.chdir("build/release-baseline-check"); import pytest; sys.exit(pytest.main(["tests/python/gui/test_analysis_configuration_layout.py","-k","method_parameters_variants_stay_bounded_and_stable","-q"]))'
```

Transcript: `raw/gui-baseline-popup.log`; SHA-256 `6317f2a9b7aa152c023b1d2f6431449902f664a64f920e6cb5c015f56ad6902c`.

### gui-retained-1 — exit 1

```sh
env QT_QPA_PLATFORM=offscreen uv run python -m pytest tests/python/gui/test_main_window_automation_launch.py tests/python/gui/test_analysis_configuration_layout.py -q
```

Transcript: `raw/gui-retained-1.log`; SHA-256 `19365c770b1b0e3844a3dfab6c1f916d8a5af76ba278024ab34de6211df2290b`.

### gui-retained-2 — exit 0

```sh
env QT_QPA_PLATFORM=offscreen uv run python -m pytest tests/python/gui/test_main_window_automation_launch.py tests/python/gui/test_analysis_configuration_layout.py -q
```

Transcript: `raw/gui-retained-2.log`; SHA-256 `ed63de1f078e3d9d7ca1c71954bbaf11a449d927df99eb5152831c063f31f321`.

### headers-fixed-1 — exit 1

```sh
uv run python docs/ux-audit/2026-10-16-round6-release-fixes/native.py headers-fixed-1
```

Transcript: `raw/headers-fixed-1.log`; SHA-256 `10161be80bf3fce7796cc930cd658057537b9785a7fa7bf617ab316ead4f7e91`.

### headers-fixed-2 — exit 1

```sh
uv run python docs/ux-audit/2026-10-16-round6-release-fixes/native.py headers-fixed-2
```

Transcript: `raw/headers-fixed-2.log`; SHA-256 `bd05da10d26eb9c85e3a306c988cbf955961e0cffac2d759d9512d2e291a35cb`.

### headers-fixed-3 — exit 0

```sh
uv run python docs/ux-audit/2026-10-16-round6-release-fixes/native.py headers-fixed-3
```

Transcript: `raw/headers-fixed-3.log`; SHA-256 `8397d503e4b9e9e3b48f8be3acce24ee5879fff476f27d7efbbfc02b201eeda1`.

### numerical-1 — exit 0

```sh
uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-release-fixes
```

Transcript: `raw/numerical-1.log`; SHA-256 `2c4b944ff21449f69238bbd9679a969ef7c7333e1d343dded49b6b9d4c21c31f`.

### numerical-final — exit 0

```sh
uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-release-final
```

Transcript: `raw/numerical-final.log`; SHA-256 `80e023a31288780ecbdcc449dac0b16a498af9066bec485384a0dd8a88de2fab`.

### numerical-full — exit 0

```sh
uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-r-stack-v2
```

Transcript: `raw/numerical-full.log`; SHA-256 `76a8f82c1ff24661de6f514457622e7712b04eae91dbb2d738d331dd5d8cabd0`.

### pln-axes-1 — exit 0

```sh
uv run python scripts/run_with_timeout.py --timeout-seconds 900 --label pln-axes-1 -- uv run python scripts/verify_rcms.py project-axis-proportions --native
```

Transcript: `raw/pln-axes-1.log`; SHA-256 `88efa44e4f00af5f4b81e5f930f052e5880aa59a6779100f498f7c4f4a840735`.

### presentation-1 — exit 0

```sh
uv run python scripts/run_with_timeout.py --timeout-seconds 900 --label presentation-1 -- uv run python /home/ali/Documents/Code/rc-metastudio/docs/ux-audit/2026-10-16-round6-release-fixes/native.py presentation-1
```

Transcript: `raw/presentation-1.log`; SHA-256 `33d4a203781c09c804b9337e0e2074deaba4294c397e63e158803917eb48cba9`.

### r-renderer-checks-1 — exit 1

```sh
/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript -e 'pkgload::load_all("r/RCMetaR"); testthat::test_local("r/RCMetaR", filter="forest-metafor-renderer|reitsma|summary-display|bubble-metafor-renderer", reporter="summary")'
```

Transcript: `raw/r-renderer-checks-1.log`; SHA-256 `bd64e5db80c2bc61e70484a7621687627955e1575b1abe095fd51d7e5e4971ed`.

### reinstall-headers-2 — exit 0

```sh
uv run python docs/ux-audit/2026-10-14-round3/install_source.py
```

Transcript: `raw/reinstall-headers-2.log`; SHA-256 `f55c7b51e47ac37604815d1786c4fc71dd2aa39bb0bee702a5a35e67932e9f68`.

### reinstall-headers — exit 0

```sh
uv run python docs/ux-audit/2026-10-14-round3/install_source.py
```

Transcript: `raw/reinstall-headers.log`; SHA-256 `f55c7b51e47ac37604815d1786c4fc71dd2aa39bb0bee702a5a35e67932e9f68`.

### reinstall-release-1 — exit 0

```sh
uv run python docs/ux-audit/2026-10-14-round3/install_source.py
```

Transcript: `raw/reinstall-release-1.log`; SHA-256 `f55c7b51e47ac37604815d1786c4fc71dd2aa39bb0bee702a5a35e67932e9f68`.

### reinstall-release-2 — exit 0

```sh
uv run python docs/ux-audit/2026-10-14-round3/install_source.py
```

Transcript: `raw/reinstall-release-2.log`; SHA-256 `f55c7b51e47ac37604815d1786c4fc71dd2aa39bb0bee702a5a35e67932e9f68`.

### small-screen-1 — exit 1

```sh
uv run python docs/ux-audit/2026-10-16-round6-release-fixes/native.py small-screen-1
```

Transcript: `raw/small-screen-1.log`; SHA-256 `c298c06a4d87435cfd19e975a1351a53700fcb16126bebfe1b7936e508367573`.

### small-screen-2 — exit 1

```sh
uv run python docs/ux-audit/2026-10-16-round6-release-fixes/native.py small-screen-2
```

Transcript: `raw/small-screen-2.log`; SHA-256 `3c839fb4c9b6c76c299a0cd154426ac090dfaeae6700f9e66d80721c728edbef`.

### small-screen-3 — exit 0

```sh
uv run python docs/ux-audit/2026-10-16-round6-release-fixes/native.py small-screen-3
```

Transcript: `raw/small-screen-3.log`; SHA-256 `b957b80fdf8f7d2bf0c6e57e0583704fa4a351836118d7780b64a0cbeee2ba4b`.

### stress-1 — exit 1

```sh
uv run python scripts/run_with_timeout.py --timeout-seconds 900 --label stress-1 -- uv run python scripts/verify_rcms.py calculator-ratio-precision --native
```

Transcript: `raw/stress-1.log`; SHA-256 `4185c438c3a2e7ee816dffb6ba113292789b49a3212231a1347156bd06a4fd7b`.

### stress-2 — exit 0

```sh
uv run python scripts/verify_rcms.py calculator-ratio-precision --native
```

Transcript: `raw/stress-2.log`; SHA-256 `cf0e69717f20454b98981825bcbd073b569007d5099f5c4f5934f95cf9f1a070`.

## CI fixes

Initial job log: `raw/ci/vertical-before.log` (GitHub job 116720515774).
Exact Windows-target typing command uses the seven `--extra-search-path` entries
in `scripts/verify-qt6.ps1`, source scopes unchanged: all checks passed locally.
The Linux environment additionally needs Windows-only pefile for cross-target
checking; it was installed only in the test-owned .venv, no dependency change.
Results evidence contract was updated first to the actual current navigation;
configured pre-fix run: 13 failed / 7 passed (`results-contract-before-configured.log`).
Post-fix run is retained separately. Earlier unconfigured attempts failed R startup
and are retained, not counted as product failures or passing evidence.

CI repair receipts live in `raw/ci/`; reproducible qualification commands are in
[CI-REPRODUCE.sh](CI-REPRODUCE.sh). `raw/ci/raw/*.json` bind each command, revision,
environment, exit and log digest; desktop receipts separately bind inputs,
screenshots, plots, persisted projects and runtime.

- 20 existing native Results evidence-contract tests pass after correction.
- 131 focused configuration/results/funnel Qt cases pass; one Linux platform skip.
- Strict Windows-target typing passes without suppressions or scope changes.
- Strict golden compatibility passes (`build/qt6-verification/golden-compatibility-ci537`), no refresh.
- Exact numerical equivalence: all 415 original fields, maximum difference zero;
  original numeric contracts, tolerances and exceptions unchanged.
- cp1252 Git-boundary reproduction fails before the encoding repair on byte 0x9d
  and passes afterward with lossless UTF-8 text.
- Real native covariate acceptance reproduction fails before repair (disabled and
  unaccepted) and passes after valid input (default enabled and accepted). Blank
  name rejection remains required by the repaired driver.

The broad source sweep initially failed 12 cases (752 passed, eight platform skips):
ten stale small-study model fixtures, renamed sample groups and a radio hit target.
Windows Core independently exposed the same model/group cases plus synthetic
screen-provider and empty-start-page table assumptions. Logs retain both runs.
The targeted core replay initially passed 41 and failed one stale Mean Difference
label expectation; its corrected replay is separate. The radio diagnostic with
an assertion inside the mocked modal callback was interrupted after the application's
error dialog blocked; the nonblocking observed-selection replay retains the real
false selection and exact wrong-count assertion. No interrupted run is qualified.
Corrected core fixture replay: **42 passed**, preserving every numerical, selected
candidate, save/reopen, accessibility and layout assertion. Windows-target typing
passes again. Exact code-health gate: **PASS**, zero complexity violations; the
23 before/after measurements are retained in CI-COMPLEXITY.json.
