# Review 2 verification

R production source is finalized at `77a9bf2`; GUI source at `679b2125`.
Later commits update verification and retained evidence only. No push or PR.

The implementation commits are `9b8eea71` through `679b2125`, based on
`29e7434d`. Inspect every small unit with
`git log --reverse --oneline 29e7434d..679b2125`. The final bounded SVG geometry
is in `91c8bdd1`, subgroup range correction in `77a9bf26`, header restoration in
`acbd50d9`, presentation refresh in `74ad86ee`, and nullable-caption correction
in `679b2125`; intermediate clipping attempts were simplified in the final code.

Run [REVIEW2.ps1](REVIEW2.ps1) from the repository root. It selects the pinned
packaged R 4.6.1 runtime through [ENV.ps1](ENV.ps1), installs current RCMetaR into
the test-owned `build/verification/round2-r-library`, checks versions and drives
the real application. Each evidence wrapper retains its exact command, source
revision, environment, exit status, elapsed time and transcript SHA-256 under
ignored `raw/`. Desktop helpers retain inputs, runtime identity, actions, plots,
exports, projects and file hashes under `artifacts/verification/rcms/`.

## Accepted results

| Lane | Result | Exact command inside `run.py` |
|---|---|---|
| Python | 905 passed, 2 skipped; 265.20 s; exit 0 | `uv run python scripts/run_with_timeout.py --timeout-seconds 600 --label review2-python-accepted -- uv run python -m pytest tests --ignore=tests/r_stack --ignore=tests/e2e -q -ra --durations=10` |
| R package | 1,818 assertions passed; 0 failures, 0 test warnings, 1 opt-in visual skip; check exit 0, 0 errors, 0 warnings, 1 NOTE | `uv run python docs/ux-audit/2026-10-14-round2/package_check.py` |
| Live bridge | 9 passed in 58.89 s; exit 0 | `uv run python -m pytest tests/r_stack -q -ra --durations=10` |
| Complete desktop | 86 passed in 1,368.64 s; exit 0 | `uv run python -m pytest tests/e2e -q -ra --durations=10 --dist loadfile -n 2` |
| Golden | 461 pass, 13 existing accepted exceptions; 474 comparisons; exit 0 | `uv run python scripts/verify_golden_compatibility.py --output build/qt6-verification/golden-compatibility-review2-complete` |
| Numerical equivalence | 415 fields exactly unchanged, maximum absolute difference 0; 91 authority case dictionaries identical; exit 0 | `uv run python docs/ux-audit/2026-10-14-round2/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-review2-complete --authorities docs/ux-audit/2026-10-14-round2/raw/review2-complete-authorities-results.json` |
| Public authorities | 91 cases passed; exit 0 | `$env:RCMS_R_HOME/bin/Rscript.exe .agents/skills/verify-rcms/scripts/analysis_authorities.R docs/ux-audit/2026-10-14-round2/raw/review2-complete-authorities-results.json` |
| Reitsma visual | 21 cases rendered twice; deterministic raster/SVG hashes and matching normalized PDF/descriptor contracts; exit 0 | `uv run python docs/ux-audit/2026-10-14-round2/reitsma_check.py` |
| Forest matrix | 300 cases, 0 renderer errors; every PNG fully decoded and hash-bound; exit 0 | `$env:RCMETASTUDIO_QA_ROOT = "$PWD/artifacts/verification/rcms/forest-review2-complete"; $env:RCMS_R_HOME/bin/Rscript.exe r/RCMetaR/inst/qa/render_forest_visual_qa.R` followed by `uv run python docs/ux-audit/2026-10-14-round2/validate_forest.py $env:RCMETASTUDIO_QA_ROOT docs/ux-audit/2026-10-14-round2/raw/review2-forest-validation-results.json` |
| Strict typing | Exit 0; all checks passed | `uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path . --extra-search-path src/rc_metastudio --extra-search-path src --extra-search-path scripts --extra-search-path tests/python/gui src/rc_metastudio scripts tests r/RCMetaR/inst/qa` |

The forest matrix rendered in 814.33 s; complete PNG decode/hash validation took
30.61 s. All accepted runs use the finalized R/GUI production source.

[REVIEW2-EVIDENCE.json](REVIEW2-EVIDENCE.json) retains the accepted command records,
log hashes, source revisions and all curated screenshot hashes. The final audit
checked every retained file in the 86 desktop and ten native bundles, and verified
3,046 file hashes and that the 19 curated frames are byte-identical to their
native originals. Run
`uv run python docs/ux-audit/2026-10-14-round2/validate_review2.py` to repeat that
audit against the retained local evidence. All reproduction scripts passed Python
compilation and PowerShell parsing.

The Python skips are the macOS PyInstaller BUNDLE and POSIX process-group checks,
which cannot run on Windows. The package NOTE is the pre-existing unused `tiff`
import. Its opt-in visual test is exercised by the separate 300-case matrix.

## Presentation oracle review

The seven inspected changed figures are binary/continuous/diagnostic standard,
binary/continuous cumulative and binary/continuous leave-one-out forests. They
restore axis identity, separate the binary table from wide intervals, and draw
bounded marks once. The sanctioned command was:

```powershell
uv run python scripts/regenerate_golden_presentation.py build/qt6-verification/golden-compatibility-review2-reviewed
```

`74ad86ee` refreshes only those figure members and their archive/artifact SHA
bindings. R summaries, numerical outputs, numeric fields, tolerances, coverage,
descriptor semantics and the 13-exception policy retain their original contents.
The fresh `review2-complete` capture passes the gate; the numerical-equivalence
script also verifies the original `84fdbc57` numerical outputs and policy.

## Native captures

The ten serial real Qt/R native scenarios are `amino`, `continuous`, binary
subgroup/cumulative/leave-one-out, `review-workflows`, `plot-workflow-forest`,
`lymph`, one-arm proportion and two-arm raw mean. They all exit 0. The 19 curated
PNG files are unmodified `QScreen.grabWindow` captures. Each was visually checked
for readable glyphs, CI/text separation and the compact header; the summary
frames also show the actual metric axis label. The narrow 10–11 editor capture
shows truncation arrows and both direction labels below the custom axis caption.

Most frames come from `review2-complete-native-*` on the final R source. Five
properties/order/rerun frames were refreshed from `review2-final-native-review-workflows`
after the nullable-label GUI fix. `raw/curated-review2.json` binds all 19 files to
their untouched native originals and observed source revisions. The default
forests use the ordinary generated device and the result window's fit-width view.
The matrix separately exercises export-sized default/RevMan/BMJ figures.

- [Wide-CI binary rows](screenshots/review2-binary-default.png)
- [Binary summary and axis](screenshots/review2-binary-summary.png)
- [Settings rerun and restored metric caption](screenshots/review2-settings-rerun.png)
- [Continuous forest](screenshots/review2-continuous-default.png)
- [Subgroup forest](screenshots/review2-subgroup-default.png)
- [Subgroup footer](screenshots/review2-subgroup-difference.png)
- [Cumulative forest](screenshots/review2-cumulative.png)
- [Cumulative axis](screenshots/review2-cumulative-summary.png)
- [Leave-one-out forest](screenshots/review2-leave-one-out.png)
- [Leave-one-out axis](screenshots/review2-omission-summary.png)
- [Directions and clipped intervals](screenshots/review2-directions-and-clipping.png)
- [Configuration-first report and header](screenshots/review2-report-top.png)

Native evidence covers the Windows qwindows runtime and shown workflows, not
unexercised DPI, accessibility or operating-system file-picker behavior.

## Superseded attempts and full-profile prerequisite

Initial geometry/header drives failed before implementation. Native inspection
then exposed SVG clip-path limitations and the settings-restoration `None`
caption. The heterogeneous subgroup check failed at ±10.6 while its actual
pooled CI reached ±19.6; the corrected automatic range contains the entire CI.
These failed/superseded transcripts and native images remain local.

The full `verify_all.py --full` helper was attempted repeatedly. It failed before
test execution at the pinned Posit binary dependency-index preflight, even though
direct HTTPS/R index probes and the exact installer probe succeeded. One prior
dependency cache was revalidated against the manifest and copied into the owned
cache; the failed helper then discarded that cache during its retry. No system
library, package qualification, numerical oracle or application dependency was
changed to bypass this failure.

The accepted package, live bridge, complete desktop, 21-case deterministic visual
check, authorities and golden commands run directly against the existing pinned
runtime and current-source test-owned RCMetaR library. These are the same checks
the full helper runs after dependency preparation. The helper itself is recorded
as blocked at its remote preflight, not as green. `REVIEW2.ps1 -FullBootstrap`
retries it when that dependency service is available; the default reproduction
uses the already configured pinned runtime.

The first desktop suite had 84 passes and two stale report-order assertions. The
targeted joint/combined cases subsequently passed after those assertions were
updated for the requested configuration-first report. The final complete run
supersedes that attempt.
