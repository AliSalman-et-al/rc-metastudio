# PR #556 final reduced scope

Later user decision supersedes F14 notation unification. All broad p/CI notation changes, selected-precision caps, subgroup-label deduplication and their expectation rewrites are reverted to master. F6/F10/F11/F13/F16/F17/F20 remain. Only explicit Q statistics with 0 < abs(Q) < 1e-10 display zero at selected precision in Python report projection. The raw results and full-precision appendix remain unchanged.

Merged master through 2f84c2b6 (#553/#554/#555/#557). #555 layouts are retained. The inherited strict visibility assertion exposed a shared AdaptiveComboBox minimum-hint bug; the corrected minimum permits horizontal shrinking while its preferred hint/height/popups remain unchanged. The failed method-row-only size-policy attempt was removed; #557 PDF black-on-white / Arial 9 pt body and captions and black DOCX styles are intact. Export functions compare exactly to master. No export colour/layout code is changed by this PR.

## Local qualification

- `typing-final-confirmed.log` and `typing-2f84c2b6.log`: repository-wide strict Ty with win32 target and generated form paths passes.
- `r-tests.log`: complete private-library package testthat suite, zero failures. Existing optional visual-QA test remains opt-in; no skip added. Exact command: source qa-env ENV.sh, prepend build/rcmetar-lib to R library variables, then Rscript -e 'library(RCMetaR); rcmetar.set.global.conf.level(95); options(testthat.progress.max_fails=Inf); testthat::test_dir("r/RCMetaR/tests/testthat", package="RCMetaR", load_package="installed", reporter="summary", stop_on_failure=TRUE)'. R source is unchanged by subsequent Python-only fixes/master merges.
- `layout-and-package-contracts.log`: python -m pytest tests/python/gui/test_results_workspace_layout.py tests/packaging/contract/test_windows_distributable_contract.py -n 1 -q: 75 passed, 5 existing platform skips.
- `e2e.log`: sequential real-R drives for continuous leave-one-out, fixed cumulative, diagnostic matrix, one-arm proportion, two-arm mean and small-study-effects passed. The initial manuscript attempt caught an already-labelled metric being prefixed twice; fixed by case-insensitive metric identity, preserving coefficient labels.
- `e2e-final.log`: replayed two-arm mean proves the requested subgroup Q example displays 0.000000, while 1.000000 and [-0.127412, 2.127412] retain selected six-place notation. Joint diagnostic then caught an old native-width cap expectation, replaced by the requested >=90% width fill while retaining no-overflow checks.
- `e2e-joint-and-export.log`: final joint diagnostic/manuscript-export replay; each helper prints retained manifest/runtime/input/screenshot/export evidence directories.

All E2E drives run one at a time. Full local pre-push is not run as instructed; CI owns it. Native light/dark/font-size screenshot matrix is still incomplete; offscreen evidence is not native platform qualification.

## Package failure

Job 126509715667 diagnostics retained locally in package-ci/. `package-diagnosis.json` isolates the failure to the F14 summary hash; scales and log markers pass. Restoring master p-value notation recovers the unchanged pinned hash. `check-package-summary.py` runs the real source application through the package-analysis entry with isolated settings/base and the private R library; package-source/summary-identity.json passes at hash 61ea84ba73eab657282ceabdf3ee1f29ab0ed55a1be574023017bc490d279ab5. This is Linux source proof, not Windows package qualification. Smoke/inspection scripts and pinned expectations remain unchanged.

## Expectations and goldens

Three strict testthat expectations change: test-forest-metafor-renderer.R:707/708 anchor x=0 instead of side midpoints; :1850 uses exact study labels instead of repeated omission prefixes. All notation-only testthat expectations are restored to master; only the three F6/F20 expectations above differ. E2E/golden changes and exact locations are enumerated in the PR description.

../golden-proof/ contains the throwaway pre-update proof and output: only two leave-one-out text fields, 164 number pairs, all exact, all 11 PNGs unchanged, every numerical field/tolerance unchanged. Contract JSON changes only their required ZIP-binding hash; outer manifest changes bindings/ZIP size. Recomparison passes 475 rows. Old unification attempts are superseded and not committed as final evidence.

Layout diagnosis: reproduce-combined-layout.py builds the real application and combined diagnostic form at 14 pt, no analysis/fit fake. Before: method row 793 wide inside a 680 viewport, overflowing controls. A row-only policy did not fix it. Probe ignoring combo minima passed; reducing visible-character hints did not. Fix: AdaptiveComboBox.minimumSizeHint permits width 0 while preserving height; actual assigned method-row width is now 646, preferred hint remains 964, zero controls overflow. combined-layout-after.log and combined-layout/dialog.png retain evidence. No debug instrumentation was added to product code.

Final shared-minimum-hint qualification: layout-final-shrinking.log: 103 passed, 1 pre-existing opt-in skip. e2e-merged-final.log: small-study-effects, diagnostic-joint and complete manuscript-export all passed after the fix. e2e-summary.json indexes all eight relevant passed scenarios; some earlier numerical/format paths precede the geometry-only shared fix, while final manuscript coverage spans the ordinary/extended analysis families. package-source-final.log rechecks the pinned summary identity on the final source.
