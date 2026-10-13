# Review 1 verification

Run from the repository root in PowerShell. `ENV.ps1` selects the manifest-pinned
packaged R runtime and the persistent, test-owned library. It does not modify
system libraries or user projects. The full R-stack lane rebuilds current RCMetaR
source in its own temporary library; native runs use the separately installed
current source in the persistent library.

```powershell
. ./docs/ux-audit/2026-10-14-round2/ENV.ps1
uv run python docs/ux-audit/2026-10-14-round2/run.py <label> <command and arguments>
```

Each ignored `raw/<label>.json` records the exact command, cwd, revision, elapsed
time, environment, exit status and SHA-256 of its log. Desktop bundles under
`artifacts/verification/rcms/` retain copied inputs/projects, runtime identity,
actions, exported figures, numerical comparisons and native screenshots.
`REPRODUCE.ps1` reruns the full lanes; `NATIVE.ps1` runs the native cases serially
and copies the selected frames without image editing. Hashes below bind the local
evidence; a fresh checkout can reproduce it with the retained scripts and fixtures.

## Final results

Production source is committed at `32db50b`. Later commits change review evidence
and reproduction only. All final runs below use that production source.
Earlier failed attempts are retained locally and are not counted as passing runs.

| Lane | Result | Command (inside wrapper) |
|---|---|---|
| Full Python | 905 passed, 2 skipped; 272.20 s | `uv run python scripts/run_with_timeout.py --timeout-seconds 600 --label review1-accepted-python -- uv run python -m pytest tests --ignore=tests/r_stack --ignore=tests/e2e -q -ra --durations=10` |
| Strict typing | Exit 0 | `uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path . --extra-search-path src/rc_metastudio --extra-search-path src --extra-search-path scripts --extra-search-path tests/python/gui src/rc_metastudio scripts tests r/RCMetaR/inst/qa` |
| Golden | Exit 0; 461 pass, 13 accepted exceptions; 474 comparisons across 11 cases | `uv run python scripts/verify_golden_compatibility.py --output build/qt6-verification/golden-compatibility-review1-accepted` |
| Numerical equivalence | 415 original fields exactly equal; maximum absolute difference 0; original 91 authority case dictionaries identical | `uv run python docs/ux-audit/2026-10-14-round2/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-review1-accepted` |
| Authority matrix | 91 cases passed | `$env:RCMS_R_HOME/bin/Rscript.exe .agents/skills/verify-rcms/scripts/analysis_authorities.R docs/ux-audit/2026-10-14-round2/raw/authorities-results.json` |
| New displayed quantities | 92 cases passed | `$env:RCMS_R_HOME/bin/Rscript.exe docs/ux-audit/2026-10-14-round2/output-authorities.R docs/ux-audit/2026-10-14-round2/raw/new-quantities-accepted.json` |
| Full desktop | Exit 0; 86 passed in 1,324.72 s | `uv run python -m pytest tests/e2e -q -ra --durations=10 --dist loadfile -n 2` |
| Full R-stack | Exit 0; 9 bridge tests (53.82 s), 86 desktop tests (724.55 s), 21 deterministic visual cases, final golden exit 0; whole lane 1,144.17 s | `uv run python scripts/verify.py r-stack` |
| R package build/check | Exit 0; 0 errors, 0 warnings, 1 NOTE; 1,804 assertions passed, 1 opt-in visual skip; 259.22 s | `uv run python docs/ux-audit/2026-10-14-round2/package_check.py` |
| Forest matrix | Exit 0; 300 cases, 0 renderer errors; render 768.95 s, complete decode/hash validation 29.36 s | `$env:RCMETASTUDIO_QA_ROOT = "$PWD/artifacts/verification/rcms/forest-review1-accepted"; $env:RCMS_R_HOME/bin/Rscript.exe r/RCMetaR/inst/qa/render_forest_visual_qa.R` |

The package NOTE is the existing unused `tiff` import. Its skipped opt-in visual
test is exercised through the separate full matrix and PNG validation below.
The Python skips are the native macOS PyInstaller BUNDLE check and POSIX
process-group teardown check. Neither can execute on Windows. The independent
output checks cover 21 metrics × z/t/Knapp–Hartung/ad hoc inference plus eight
subgroup prediction intervals compared to separately fitted public metafor models.
PAS checks its bounded inverse; PFT prediction limits remain on calculation scale
without an unspecified new-study sample size.

## Review of all 14 original golden differences

The original gate passed before round 2, then reported 447 pass + 13 accepted +
14 presentation differences. Every row below was inspected and retained as intended.
Numerical outputs, numeric fields, tolerances, coverage, descriptor semantics and
exception policy retain their original contents. Archive/artifact integrity bindings
and outer manifest hashes necessarily change with the reviewed presentation bytes.

| Case | Artifact | Intended change |
|---|---|---|
| amino-binary-random | Summary text | Overall effect and prediction interval |
| amino-binary-random | Forest Plot | Metric/CI headings, axis spacing, summary and footer |
| continuous-random | Summary text | Overall effect and prediction interval |
| continuous-random | Forest Plot | Metric/CI headings, axis spacing, summary and footer |
| lymph-diagnostic-random-dor | Odds Ratio Summary text | Overall effect and prediction interval |
| lymph-diagnostic-random-dor | Odds Ratio Forest Plot | Diagnostic headings, scale and model information |
| amino-binary-cumulative | Cumulative Forest Plot | Explicit sequence, readable interval labels and final-model footer |
| amino-binary-leave-one-out | Leave-one-out Forest plot | Omission context, interval labels and original-model footer |
| continuous-cumulative | Cumulative Forest Plot | Explicit sequence, readable interval labels and final-model footer |
| continuous-leave-one-out | Leave-one-out Forest plot | Omission context, interval labels and original-model footer |
| amino-binary-subgroup | Subgroup Summary text | Package comparison test with correct statistic/df/P |
| amino-binary-subgroup | Subgroup Forest Plot | Group and overall diamonds, labels, totals and comparison footer |
| continuous-subgroup | Subgroup Summary text | Package comparison test with correct statistic/df/P |
| continuous-subgroup | Subgroups Forest Plot | Group and overall diamonds, labels, totals and comparison footer |

The sanctioned capture is the real R/Qt path used by
`verify_golden_compatibility.py`; after inspection,
`scripts/regenerate_golden_presentation.py <capture-directory>` copies only rows
classified as presentation drift. `0ada606` commits the reviewed refresh. The ZIP
is 9,037,488 bytes, so its archive limit becomes 16 MiB; member, count and unpacked
limits are unchanged. This is an archive-size allowance, not a numerical tolerance.
`numerical_equivalence.py` compares original archive outputs and all policies to
Git's `84fdbc57` content, excluding only those integrity bindings.

## Failure-first evidence and corrected drives

- `db42c01`: the real Properties/ordering drive failed before implementation because
  Change settings was absent. It now verifies saved method/metric/inference/CI/
  digits, Cancel, reuse of the result's dataset after the main project changes,
  all four order choices with exact numerical-section equality, and cumulative
  ordering protection. Prefill/Cancel is also exercised throughout the desktop matrix.
- `8fed3ec`: the real continuous raw-data drive first failed with only a Weight
  column; it now requires both arms' N/mean/SD plus Weight (seven columns).
- `9de3345`: before the MH renderer fix, the isolated ratio file reported five
  failures and three warnings, including the full-row/weight mismatch and forest
  length error. After `3f8bb14`, all 384 assertions passed. A later failure-first check
  (`7be7a2f`) exposed effect sorting using the shortened MH array in all three
  styles. `32db50b` fixes that alignment; the file now passes all 390 assertions. The new check renders
  all three styles and requires the pooled result object to remain identical.
- The original full desktop run had 84 pass / 2 fail (MH and a subgroup bitmap
  allocation); the R-stack run had 85 pass / 1 fail (MH). Final heavy lanes are
  separated. The first separated R-stack run passed package/visual/bridge checks
  and 53 desktop cases, then was stopped through its verified owned process tree
  to include the MH ordering fix. Its partial log and owned PID record remain local;
  the accepted-source full runs restart from the beginning. `review1-mh-desktop-fixed` passed in 126.55 s, including independent
  MH comparisons and decoded exports. `review1-subgroup-export-fixed` passed in
  75.48 s, including TIFF. The final full runs supersede these targeted checks.
- A setup/editor group-title typo was caught by strict typing and native setup;
  `4db73e8` and `3f8bb14` correct the actual generated widget name. Failed attempts
  remain in `raw/`.

## Evidence hygiene

`ebadfd7` removes 442 files from the round-2 Git index only. All 442 local files
match their original Git contents when checkout line endings are accounted for
(`git hash-object --path=<file> <file>`); the removal commit deletes no path outside
this folder. `raw/evidence-retention.json` records this check. Other untracked audit
folders were left untouched. The old curation helper remains locally retained;
`review_screenshots.py` is the smaller, retained Review 1 reproduction helper.

## Native screenshot inspection

All 15 `review1-accepted-native-*` drives and the additional `ratios-irr --native`
drive exit 0 on qwindows from source `32db50b`. The latter retains 112 actions,
independent MH/subgroup/sequential comparisons and decoded exports. Each bundle
records shown HWND capture through QScreen, Qt/R identities and input/action evidence.
The 20 unmodified selected frames below were each visually inspected for glyphs,
alignment, labels, totals, diamonds and the requested workflow controls. The final
source recapture matches all 20 previously inspected PNGs byte for byte
(`raw/native-frame-comparison.json`). No model label overlaps an arm total;
references use the proportional font and hanging numbered lines. Top/bottom frames
show different scroll positions; the options frame is the native popup HWND.

```powershell
./docs/ux-audit/2026-10-14-round2/NATIVE.ps1 -LabelPrefix review1-accepted-native
uv run python scripts/verify_rcms.py ratios-irr --native
```

| Screenshot | Native evidence directory / frame | SHA-256 |
|---|---|---|
| [review1-binary-default.png](screenshots/review1-binary-default.png) | `20261013T215829Z-4c80c4ca-amino/04-0-analysis-results.png` | `76372e1d4009930c316e12589411a20a320235352416e3c8714a13a3afce28bf` |
| [review1-report-top.png](screenshots/review1-report-top.png) | `20261013T215829Z-4c80c4ca-amino/04-0-analysis-results-report.png` | `66344ceae3dede985fdd447fe0bb14c7ee68e968bbc1a395afda139d16e1cbb4` |
| [review1-binary-summary.png](screenshots/review1-binary-summary.png) | `20261013T215829Z-4c80c4ca-amino/04-0-analysis-results-bottom.png` | `b632e92604e8a9511b7abb04ea7f81ab8a8b8144a1ec4310b973d0003b93165c` |
| [review1-continuous-default.png](screenshots/review1-continuous-default.png) | `20261013T215842Z-c232a682-continuous/04-0-analysis-results.png` | `1ee45b9071dcdb2a6334d25ccd9cdbd4d041437c944e1fa65ad715ca7983f9e2` |
| [review1-single-arm-default.png](screenshots/review1-single-arm-default.png) | `20261013T215854Z-37a47ad7-analysis-data-onearm-proportion/07-0-matrix-results.png` | `9759652352f5478b17caff125d5daf38fec132ca2590a3421b096d663be21785` |
| [review1-subgroup-default.png](screenshots/review1-subgroup-default.png) | `20261013T215907Z-4c38f46c-analysis-amino-binary-subgroup/04-0-matrix-results.png` | `668be614a5aeaa3e17a045ef50607c373aa09b6682b8baeb7f86ed6c9518cf8b` |
| [review1-subgroup-difference.png](screenshots/review1-subgroup-difference.png) | `20261013T215907Z-4c38f46c-analysis-amino-binary-subgroup/04-0-matrix-results-bottom.png` | `99fb0cad332588f21e864cbf753857a9bf520299787266c5f5eb2627b4a713f4` |
| [review1-cumulative.png](screenshots/review1-cumulative.png) | `20261013T215925Z-a1388303-analysis-amino-binary-cumulative/04-0-matrix-results.png` | `2f0ff487e522bbad322ad317391e918fd7b6edfc7fdeb7d0637bac7ecf1d52ca` |
| [review1-cumulative-summary.png](screenshots/review1-cumulative-summary.png) | `20261013T215925Z-a1388303-analysis-amino-binary-cumulative/04-0-matrix-results-bottom.png` | `256f163abd4b1dcf049679820f4fa74465328532adaab48ca6b1caf22559b5a8` |
| [review1-leave-one-out.png](screenshots/review1-leave-one-out.png) | `20261013T215940Z-cb7c1855-analysis-amino-binary-leave-one-out/04-0-matrix-results.png` | `b8f11474f0cf3b5db0dd4a65dbee3933b8e8690cb44c8a4d539d7f12c62af189` |
| [review1-omission-summary.png](screenshots/review1-omission-summary.png) | `20261013T215940Z-cb7c1855-analysis-amino-binary-leave-one-out/04-0-matrix-results-bottom.png` | `6e7e143373a5e16cb6167ce197b569bb85f12e713d26279401059566aa93fca3` |
| [review1-bubble.png](screenshots/review1-bubble.png) | `20261013T215954Z-737057a5-analysis-amino-binary-meta-regression/04-0-matrix-results.png` | `a3429fb4cf619bad34e401a4e16c818a4ed069278e529a94ab287600d970e552` |
| [review1-diagnostic-summary.png](screenshots/review1-diagnostic-summary.png) | `20261013T220106Z-a5b41bc9-analysis-diagnostic-joint/05-0-matrix-results.png` | `14cf4e06552f29b60c5522d35cdee0de4016d6fb819efd35a2708335e7a60d5f` |
| [review1-continuous-raw.png](screenshots/review1-continuous-raw.png) | `20261013T220222Z-d60e23ec-analysis-data-twoarm-mean/07-0-matrix-results.png` | `99bd38defa20afa5ded9fa7a125aa1ab9a0a450f9902ac10ed0436734ba90a59` |
| [review1-properties.png](screenshots/review1-properties.png) | `20261013T220119Z-8c5a3118-review-workflows/05-0-review-properties-prefilled.png` | `6c431f9e99f671ba6f25f5de176a3c21a2aec1d4c5e18fd706b6d78baf77050c` |
| [review1-settings-rerun.png](screenshots/review1-settings-rerun.png) | `20261013T220119Z-8c5a3118-review-workflows/16-0-review-settings-rerun.png` | `be6d62117cb0d5561f702a15de18eb538f3e5cc3fa972ccab130c8e28ab28a6e` |
| [review1-cumulative-order.png](screenshots/review1-cumulative-order.png) | `20261013T220119Z-8c5a3118-review-workflows/17-0-review-cumulative-order.png` | `3db08c13c994a9a6b75d2da7b4e85426e82c92922287ae8638d856e82df162e7` |
| [review1-study-order.png](screenshots/review1-study-order.png) | `20261013T220119Z-8c5a3118-review-workflows/07-0-review-study-order-year.png` | `dd90ce7fb492363d84c7891b46af3c8a419c49ae0afee0f45f20b4c10aaaa906` |
| [review1-study-order-options.png](screenshots/review1-study-order-options.png) | `20261013T220119Z-8c5a3118-review-workflows/08-1-review-study-order-options.png` | `9f31819fff5c22f64385e2ed843c93573b4672b8221e326601f20f11241c4abd` |
| [review1-direction-fields.png](screenshots/review1-direction-fields.png) | `20261013T220147Z-0d04315c-plot-workflow-forest/07-0-family-editor-controls.png` | `e12acedf3650371c7ff439ad67c4b50e89bbfec292982563fec605c8686b2deb` |

Native qualification is Windows qwindows on the available display. Existing
fractional process-scale checks remain; OS High Contrast, screen readers, multiple
displays and other operating systems are not claimed as newly qualified.

The matrix command is followed by:

```powershell
uv run python docs/ux-audit/2026-10-14-round2/validate_forest.py artifacts/verification/rcms/forest-review1-accepted docs/ux-audit/2026-10-14-round2/raw/forest-validation-accepted.json
```

Coverage is 5 data families × 4 forest variants × 3 styles × 5 input/layout cases.
All 300 case tuples are present, every error field is empty, all PNG byte sizes match
the manifest, and every PNG was fully decoded. The retained validation JSON binds
its case, dimensions, bytes and SHA-256. This establishes rendering/decoding coverage;
the 20 curated native frames are the manually inspected aesthetic evidence.

## Runtime and source provenance

All final production source is `32db50b`; subsequent commits change documentation
and reproduction only. `git diff --exit-code 32db50b..HEAD -- src r scripts tests
.agents/skills/verify-rcms/scripts` is empty. The warm install receipt records R CMD
INSTALL from that committed source before the accepted native drives. The R-stack
builds/checks/installs the same source in its own temporary library. Parent wrapper
ENV records do not describe a child's library override; the actual runtime files do:

- R-stack `artifacts/verification/rcms/20261013T221602Z-129b7f48-calculator-diagnostic/runtime.json` selects `C:/Users/Ali-Salman/AppData/Local/Temp/RCMetaR-r-stack-qbg0np9u/library` first.
- Standalone `artifacts/verification/rcms/20261013T222907Z-e9d48fe0-amino/runtime.json` selects `build/verification/round2-r-library` first.

Both record R 4.6.1, RCMetaR 0.4.2, metafor 5.0-1, meta 8.5-0, mada 0.5.12,
rsvg 2.7.0, svglite 2.2.2, tiff 0.1-12, rpy2 3.6.7, Qt 6.11.1 and PyQt 6.11.0.
Suite children use offscreen; the sixteen native drives record qwindows. The
R-stack temporary library is removed by its owner after completion; input/action/
result/runtime evidence and the standalone source-package check remain retained.

## Verified command/log receipts

Every receipt below was opened, required to exit 0, and its log bytes checked against
the recorded full SHA-256. Command argv and runtime ENV remain in ignored
`raw/<label>.json`; each digest below refers to `raw/<label>.log`.
Elapsed time here is the whole wrapped command, which can exceed pytest's reported
execution time in the results table.

| Label | Revision | Elapsed seconds | Log SHA-256 |
|---|---|---|---|
| `review1-accepted-install` | `32db50b5` | 19.92 | `d6255be7acdb1722fb449f38b045f2b3e9125c0cc24909bdeae41fb6dfaed988` |
| `review1-accepted-python` | `32db50b5` | 273.39 | `dc66bb558eeaffeb2acb085406bfcd8af83c8e8c3c9a0fca0a544a8bdbc887b7` |
| `review1-accepted-typing` | `32db50b5` | 1.11 | `3e66bbbb9315ed4d49eeb485475493d7cc694d98a3c861346eaa8717237e0db4` |
| `review1-accepted-golden` | `32db50b5` | 33.98 | `2e7f3fca57ad1915c07a9eb5651edfef7944ef936ec46977a089bcf74a3968d0` |
| `review1-accepted-authorities` | `32db50b5` | 7.55 | `5445efa3219a124b50a7c0f5c8f50fbdd363fd972005c300016914e16e4223c4` |
| `review1-accepted-quantities` | `32db50b5` | 9.52 | `072e0fd8d20b51cfdca4f1ea1719171a6844ca4cf13d685425f9926952069b2e` |
| `review1-accepted-equivalence` | `32db50b5` | 0.72 | `3b821f76bc87695876c25e9df1abe256893231cf3827ace7affef239cd14572a` |
| `review1-accepted-package` | `32db50b5` | 259.22 | `c61cd46d917ee7fc8d147102516456ed0966b1bb8b7204c6d3738db028e5ef73` |
| `review1-accepted-r-stack` | `32db50b5` | 1144.17 | `48b03680b09b2deea955fd89ef06ed0b354dd51283fee8a5c44d38ceb1880949` |
| `review1-accepted-desktop` | `e0911d0c` | 1325.38 | `b29c20dc5899325baa34a271eb5638c5f07ecea92a2af957433294b998c837e3` |
| `review1-accepted-forest` | `e0911d0c` | 768.95 | `056146c5493a331bb5564195b7f3aab2211c942609b7eb697a8975460df5637a` |
| `review1-accepted-forest-validation` | `c1b26ca4` | 29.36 | `8a384ce8a9868b9d1e17a40add2a6f03b1549afc1c3a0f1961d79ee3e2890005` |
| `review1-mh-order-green` | `32db50b5` | 15.36 | `aa6fcacca0bea7536f20a3ab57c1294b607740f61183a3b02a37b82349415c73` |
| `review1-accepted-native-amino` | `32db50b5` | 13.01 | `7e5cdad7273e78df09e213d85fc86e219f70f2a6c71f3f8427409894346c3e26` |
| `review1-accepted-native-analysis-amino-binary-cumulative` | `32db50b5` | 14.36 | `a39fb1001df39dda59afc1b9637809301e0522dc9f6b25490f1384a1fdf5b34b` |
| `review1-accepted-native-analysis-amino-binary-leave-one-out` | `32db50b5` | 13.78 | `47959baa5139647cb5335a5ded68551be187cd6b74b8ff674fdc9fc089ae21c5` |
| `review1-accepted-native-analysis-amino-binary-meta-regression` | `32db50b5` | 12.69 | `56b7afd2fabd35176894830a903edc2672e13964d52a33682a305f34c671c141` |
| `review1-accepted-native-analysis-amino-binary-subgroup` | `32db50b5` | 17.95 | `29f4c2dbdeeda90e52cd632fbc8909876cdeab83fc08628a304e5d0fa645a58d` |
| `review1-accepted-native-analysis-continuous-cumulative` | `32db50b5` | 12.24 | `c48c891dae94cf8958c529d8c71dfa4cc565a3870a893a21a1be146e8d79707c` |
| `review1-accepted-native-analysis-continuous-leave-one-out` | `32db50b5` | 12.33 | `7b50fd2f9d4a004061a88d57928b56b6c456ab2ea4574007b40f42d469618895` |
| `review1-accepted-native-analysis-continuous-subgroup` | `32db50b5` | 19.38 | `8ccfd5f0cc64b5fc9e64f7ed3f06b43d110ec08039c53b068ab62935811135b5` |
| `review1-accepted-native-analysis-data-onearm-proportion` | `32db50b5` | 12.58 | `d5e45bd4706b46017f3b7596119b37ca2a5f2fc00b4542ae2e7c46795abadc25` |
| `review1-accepted-native-analysis-diagnostic-joint` | `32db50b5` | 12.55 | `c986569200991e447ab883234424d290b515569c1aeb832c6dd0260ddc2d6c5f` |
| `review1-accepted-native-continuous` | `32db50b5` | 12.16 | `d7f400d77e99f5a933a5a1090907dc5dd130cf5eafc4538e666f5eb8eb5e07f5` |
| `review1-accepted-native-lymph` | `32db50b5` | 13.58 | `efa4090e245d2685e95abe925a03ff1f5b70ab8b6ffabdd9b828ec955c3ce62a` |
| `review1-accepted-native-plot-workflow-forest` | `32db50b5` | 34.20 | `430d672d0e7ba90199d85ed535f2b452c134bec88ac2e6d5e61ad35c0e7182c3` |
| `review1-accepted-native-raw` | `32db50b5` | 13.09 | `5491548733e5d141c20f22f8bdfd2577dda305cb43c5491e13986bfa7a5a5906` |
| `review1-accepted-native-review-workflows` | `32db50b5` | 28.53 | `f3f2a89fd470334c863ffee83a024a58524b7f10fd387b26baa9bb2b1142e02a` |
| `review1-accepted-mh-native` | `32db50b5` | 149.73 | `6a2c5ee744d5ef94b4569bc4878f8880c3eef9992cbf3122df2df11ed82f5b7a` |
