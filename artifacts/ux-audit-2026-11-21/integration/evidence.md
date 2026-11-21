# RC MetaStudio UX integration

Branch `polish/ux-2026-11`, Windows x64 worktree `C:/Users/Ali-Salman/.t3/worktrees/rc-metastudio/t3-379a67ab-b3fea2b183c77dbb`. Application qualification began at `16835c4e38fe5c11c6d4a45c8b680fe058752d28`. The branch is local.

## Merges and conflict resolution

| Commit | Parents | Integration |
| --- | --- | --- |
| `d260302f` | `9f7ee5f4`, `e5750107` | B2 merged cleanly from master. B1 `5307bec2` is an ancestor of B2. |
| `bb29b562` | `d260302f`, `262c9058` | A merged after B2. Git reported three textual conflicts. |
| `16835c4e` | `bb29b562` | Refreshed eleven reviewed exact Windows image references. |

- `src/rc_metastudio/results/report.py` retains A's `QWidget` import for its report UI and B2's page-margin and font-metric imports. The merged report retains A's participant and study contribution wording alongside B2's manuscript layout, decimal TSA formatting, and figure handling.
- `tests/e2e/manuscript_export.py` opens A's relocated continuous fixture and keeps B2's signed direction choice before swapping the arms.
- `tests/e2e/ux_workflows.py` opens the same exact relocated fixture and drives B2's Dataset effect-direction action. The fixture keeps the inputs expected by these drives.
- `src/rc_metastudio/analysis/setup_dialog.py` was an automatic merge. The resolved sequence runs A's missing-input check before the progress window opens. B2 tracks fitting progress when a sequential run starts. Cancellation exits silently, disposes the progress window and leaves setup open. A's error details, contributing-study counts and replacement of the originating Results window after a successful rerun all remain connected.
- `src/rc_metastudio/results/window.py` was an automatic merge. It retains A's titles, Change settings and copy feedback, as well as B1/B2's measured forest dimensions, natural width and shared last-used export directory.
- `CHANGELOG.md` has one Unreleased section for the published samples, analysis journeys, sequential progress, figures and publication exports.

## Golden image refresh

The reviewed differences cover the random, cumulative, leave-one-out, meta-regression and subgroup plots on the Amino and continuous inputs, plus the Lymph diagnostic odds ratio forest. B1 and B2 yield identical `outputs` and `additional_outputs` for all eleven cases. The changed plots reflect the accepted measured forest spacing, column and interval typography, and fixed regression-axis typography. The integrated RCMetaR source tree equals B2's.

The accepted capture is the B2 `golden-compatibility-r-stack-v2-3325b54e824c/capture` run. Use the recorded B2 worktree path and the sanctioned updater.

```powershell
$b2 = '../t3-1c1b23e4-c72767a10a38eb0a'
$cap = "$b2/build/qt6-verification/golden-compatibility-r-stack-v2-3325b54e824c/capture"
uv run python scripts/regenerate_golden_presentation.py $cap
uv run python artifacts/ux-audit-2026-11-21/integration/audit-goldens.py
```

The [refresh transcript](golden-refresh.log) and [archive audit](golden-archive-audit.log) identify all eleven changes. Inside the ZIP, only the eleven PNG payloads and their SHA-256 bindings change. Manifest, descriptor and numeric-contract archive SHA bindings follow the new ZIP. Numeric values, texts, tolerance policy and the exception manifest match the pre-refresh integration commit. B1's approved exception entries arrived through the unmodified merge of B2. [B1/B2 numeric equality](accepted-golden-numerics.log).

| Case | B1 | B2 |
| --- | --- | --- |
| amino-binary-cumulative | [PNG](accepted-golden-pairs/b1/amino-binary-cumulative/golden_amino_cumulative_forest.png) | [PNG](accepted-golden-pairs/b2/amino-binary-cumulative/golden_amino_cumulative_forest.png) |
| amino-binary-leave-one-out | [PNG](accepted-golden-pairs/b1/amino-binary-leave-one-out/golden_amino_loo_forest.png) | [PNG](accepted-golden-pairs/b2/amino-binary-leave-one-out/golden_amino_loo_forest.png) |
| amino-binary-meta-regression | [PNG](accepted-golden-pairs/b1/amino-binary-meta-regression/reg.png) | [PNG](accepted-golden-pairs/b2/amino-binary-meta-regression/reg.png) |
| amino-binary-random | [PNG](accepted-golden-pairs/b1/amino-binary-random/golden_amino_forest.png) | [PNG](accepted-golden-pairs/b2/amino-binary-random/golden_amino_forest.png) |
| amino-binary-subgroup | [PNG](accepted-golden-pairs/b1/amino-binary-subgroup/golden_amino_subgroup_forest.png) | [PNG](accepted-golden-pairs/b2/amino-binary-subgroup/golden_amino_subgroup_forest.png) |
| continuous-cumulative | [PNG](accepted-golden-pairs/b1/continuous-cumulative/golden_continuous_cumulative_forest.png) | [PNG](accepted-golden-pairs/b2/continuous-cumulative/golden_continuous_cumulative_forest.png) |
| continuous-leave-one-out | [PNG](accepted-golden-pairs/b1/continuous-leave-one-out/golden_continuous_loo_forest.png) | [PNG](accepted-golden-pairs/b2/continuous-leave-one-out/golden_continuous_loo_forest.png) |
| continuous-meta-regression | [PNG](accepted-golden-pairs/b1/continuous-meta-regression/reg.png) | [PNG](accepted-golden-pairs/b2/continuous-meta-regression/reg.png) |
| continuous-random | [PNG](accepted-golden-pairs/b1/continuous-random/golden_continuous_forest.png) | [PNG](accepted-golden-pairs/b2/continuous-random/golden_continuous_forest.png) |
| continuous-subgroup | [PNG](accepted-golden-pairs/b1/continuous-subgroup/golden_continuous_subgroup_forest.png) | [PNG](accepted-golden-pairs/b2/continuous-subgroup/golden_continuous_subgroup_forest.png) |
| lymph-diagnostic-random-dor | [PNG](accepted-golden-pairs/b1/lymph-diagnostic-random-dor/golden_lymph_forest_dor.png) | [PNG](accepted-golden-pairs/b2/lymph-diagnostic-random-dor/golden_lymph_forest_dor.png) |

## Qualification commands

Run these commands from the integration worktree. The warm and native drives use Python 3.14.10, Qt 6.12.0 and embedded R 4.6.2. The Win32 typing gate ran before GUI work. [First typing command and exit code](../../verification/typing/20261121T210836-6a7cd664/command.json) · [Typing transcript](../../verification/typing/20261121T210836-6a7cd664/stdout.log).

```powershell
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
uv run python -c "from pathlib import Path; from scripts.verify import run_typing; run_typing(Path('build/qt6-verification').resolve())"

$d = 'artifacts/ux-audit-2026-11-21/integration'
. "./$d/environment.ps1"
$cache = (Resolve-Path ../t3-80d202b8-9a4e74e4f8467968/artifacts/r-library-cache).Path
& "$env:RCMS_R_HOME/bin/R.exe" CMD INSTALL "--library=$env:RCMS_R_LIBS" r/RCMetaR
uv run python scripts/verify.py r-stack --rscript "$env:RCMS_R_HOME/bin/x64/Rscript.exe" --r-library-cache-root "$cache" --build-root build/qt6-integration-r-stack --skip-desktop
uv run python scripts/verify_rcms.py doctor
uv run python -m pytest tests/e2e -n 3 --fresh --durations=10 --tb=short --junitxml="$d/warm-results.xml" -v
uv run python scripts/verify_rcms.py polish-journeys --native
Remove-Item Env:RCMS_UI_CRAWL_SECTIONS -ErrorAction SilentlyContinue
uv run python scripts/verify_rcms.py ui-crawl --native
```

The fresh matrix produced 151 desktop receipts with the controller fingerprint and three plot-geometry controls. The receipt audit validated the current-source IDs, exit codes and SHA-256 digests for every retained artifact from the matrix, both native drives and seven targeted replays. Run it with `uv run python artifacts/ux-audit-2026-11-21/integration/audit-manifests.py . --final`. The persistent warm library contains the pinned dependency cache's `library/` contents and a fresh install from this branch. The R-stack builds and installs a separate source package in its owned library. Its desktop leg is supplied by the separately recorded fresh warm run. All nine published archive hashes agree with the shipped manifest after the native drives. [Sample hashes](published-sample-sha256.log).

| Check | Result | Evidence |
| --- | --- | --- |
| Strict typing | Passed, Win32 | [Command and transcript](../../verification/typing/20261121T210836-6a7cd664/command.json) |
| Source install and runtime doctor | Passed | [Install](install-r.log) · [Doctor manifest](../../verification/rcms/20261121T161212Z-1e3eda68-doctor/manifest.json) |
| R-stack | Passed. R CMD check OK, 103 authority comparisons, 21 Reitsma cases on each of two runs, and 9 Python/R bridge tests. Goldens had 453 passes, 23 existing exceptions and zero drift across 11 analyses and 416 numerical fields. | [Transcript](r-stack.log) · [Golden report](golden-report.json) |
| Fresh warm matrix | 154 passed, 0 failed, 0 skipped in 33:50. | [Transcript](warm.log) · [JUnit counts](warm-results.xml) · [Manifest and artifact audit](manifest-audit.log) |
| Native polish journeys | Passed | [Manifest](../../verification/rcms/20261121T161226Z-e5181548-polish-journeys/manifest.json) |
| Native full UI crawl | Passed, 268 indexed captures across all nine sections, zero missing paths. | [Manifest](../../verification/rcms/20261121T161551Z-9283302f-ui-crawl/manifest.json) · [Index](../../verification/rcms/20261121T161551Z-9283302f-ui-crawl/ui-crawl-index.md) |

## Editorial replay

- The six fresh 10-study binary forests match the same-fit B2 replay byte for byte, at natural width and 180 mm. The original sweep's 180 mm Default fixture reused a B1 fit whose columns had already been materialized. Fresh fits in both B2 and integration produce Events and Total. The BMJ and RevMan fixed-width renders also match the archived sweep. [Inputs, SVGs and PNGs](forest-10/) · [Comparison and hashes](forest-comparison.log).
- All twelve Recovery cases match the accepted B2 results. The three standard fits retain OR 2.22, with the same direction labels, label positions and manuscript language. The saved choice survives reopen and appears in the three presets for cumulative, omission and subgroup fits. [Integrated manifest and captures](direction-integrated/manifest.json) · [Comparison](direction-comparison.log).
- The 95- and 400-study projects match the accepted B1 input hashes. The app generated PDF and DOCX, and Microsoft Word exported the DOCX to PDF. Both integrated sizes retain every study in order, with 3 forest panels for 95 studies and 10 for 400, matching B1 panel counts. The app PDFs use vector figures. The DOCX files use A4, 20 mm margins and Word compatibility 15. Total app PDF and Word page counts are 8 and 8 at 95 studies, and 25 and 22 at 400. B2 pagination shifts page and row breaks relative to B1. Replaying the two exact input archives from B2 produces pixel-identical results on all 63 pages across both PDF series and both study counts. Every DOCX ZIP member also matches B2 byte for byte. [B2 comparison](manuscript-b2-comparison.log). [95-study manifest](manuscript-integrated/095/manifest.json) · [400-study manifest](manuscript-integrated/400/manifest.json) · [Page and study-order comparison](manuscript-comparison.log).
- The original published-sample desktop drives passed for Colditz TSA, Kearon SROC and Deeks, and Poole ordinary funnel and trim-and-fill. Fourteen re-rendered SVGs match the accepted B2 renderer byte for byte using the saved published-sample fits. [Colditz](../../verification/rcms/20261121T161659Z-9140adf6-sample-colditz/manifest.json) · [Kearon](../../verification/rcms/20261121T161659Z-350e2da1-sample-kearon/manifest.json) · [Poole](../../verification/rcms/20261121T161659Z-93a83c44-sample-poole/manifest.json) · [SVGs and PNGs](sample-figures-integrated/) · [Hashes](sample-figures-comparison.log).

```powershell
$rscript = "$env:RCMS_R_HOME/bin/x64/Rscript.exe"
& $rscript --vanilla "$d/forest-10.R" "$d/forest-10" "$d/forest-10"
# Replay the same command into forest-b2-replay using the B2 r-library-handoff first on R_LIBS.
$env:QT_QPA_PLATFORM = 'offscreen'
uv run python "$d/compare-forests.py" "$d/forest-10" "$d/forest-b2-replay"
Remove-Item Env:QT_QPA_PLATFORM
$env:RCMS_B2_RECOVERY = 'C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/ux-audit-2026-11-21/sol/inputs/recovery.csv'
$env:RCMS_B2_CAPTURE = 'integrated'
uv run python "$d/b2-replay.py" direction
uv run python "$d/compare-direction.py" "$d/direction-integrated" "$b2/artifacts/ux-audit-2026-11-21/batch-b2/direction-replay"
$env:RCMS_B2_400_PROJECT = (Resolve-Path "$d/manuscript-inputs/400.rcms").Path
uv run python "$d/b2-replay.py" progress
$env:RCMS_B1_CAPTURE = 'manuscript-integrated'
foreach ($n in 95,400) { uv run python "$d/manuscript-replay.py" $n }
foreach ($sample in 'colditz','kearon','poole') { uv run python scripts/verify_rcms.py "sample-$sample" }
```

## Old bundled sample lookup

`git grep -in -E 'sample_projects[/\\]+(amino|lymph|bcg|continuous)\.rcms' -- . ':!artifacts/**' ':!CHANGELOG.md'` returned exit 1 and no matches. A raw basename search still finds references to the explicitly retained fixtures and historical golden provenance. Those archives bind numerical and migration expectations to the original inputs. The raw search returned 48 paths. [Grep receipt](old-sample-grep.log).

### Word, PDF and published figures

```powershell
$cacheKey = 'R-4.6.2-x86_64-win.binary-rdeps-47b73827be58'
# To initialize an empty test library, copy the dependency folders from "$cache/$cacheKey/library" before installing RCMetaR.
foreach ($n in '095','400') {
    $w = (Resolve-Path "$d/manuscript-integrated/$n/workflow").Path
    & ./.agents/skills/verify-rcms/scripts/render_word_pdf.ps1 -InputPath "$w/manuscript.docx" -OutputPath "$w/manuscript-word.pdf"
    foreach ($name in 'manuscript','manuscript-word') {
        pdftoppm -r 96 -png "$w/$name.pdf" "$w/$name-page"
        pdftotext -bbox-layout "$w/$name.pdf" "$w/$name-layout.html"
        pdfimages -list "$w/$name.pdf" | Set-Content "$w/$name-images.txt"
    }
}
$b1 = '../t3-80d202b8-9a4e74e4f8467968/artifacts/ux-audit-2026-11-21/batch-b1/editorial/qt-final'
uv run python "$d/compare-manuscripts.py" "$d/manuscript-integrated" $b1
$base = 'artifacts/verification/rcms'
$source = @(
    "$base/20261121T161659Z-9140adf6-sample-colditz/workflow/analysis",
    "$base/20261121T161659Z-350e2da1-sample-kearon/workflow/analysis",
    "$base/20261121T161659Z-93a83c44-sample-poole/workflow/analysis"
)
& $rscript --vanilla "$d/sample-figures.R" "$d/sample-figures-integrated" @source
# Run the same command with the accepted B2 library in R_LIBS and R_LIBS_USER, writing to sample-figures-b2.
$env:QT_QPA_PLATFORM = 'offscreen'
uv run python "$d/compare-forests.py" "$d/sample-figures-integrated" "$d/sample-figures-b2"
```

The [95-study app PDF](manuscript-integrated/095/workflow/manuscript.pdf) and [Word PDF](manuscript-integrated/095/workflow/manuscript-word.pdf) both put their first figure on page 6. The [400-study app PDF](manuscript-integrated/400/workflow/manuscript.pdf) starts figures on page 16 and the [Word PDF](manuscript-integrated/400/workflow/manuscript-word.pdf) on page 13. Both page series are rasterized beside their respective PDFs.

The 400-study cancellation replay recorded both dialogs at “Fitting 120 of 400…”. Both checks returned to visible setup with no Results window, error, or progress dialog. [Manifest](progress-integrated/manifest.json) · [Actions and results](progress-integrated/steps.jsonl).

For the B2 manuscript comparison, run the same manuscript drive from that sibling worktree with `RCMS_REPLAY_ROOT` set to its path, `RCMS_B1_CAPTURE=manuscript-b2`, its generated Qt forms, and its `r-library-handoff` set in `RCMS_R_LIBS`, `R_LIBS` and `R_LIBS_USER`. The B2 Python interpreter ran its Win32 typing gate before both drives. Render the resulting PDF and DOCX pairs into `manuscript-b2` with the same Word and Poppler commands above, then run:

```powershell
uv run python "$d/compare-b2-manuscripts.py" "$d"
```


## Replay setup corrections

The first warm-library setup attempt resolved the sibling environment script one directory too high and treated the R cache root as the package directory. The corrected environment resolves the sibling script and installs into the copied cache's `library`. A standalone golden attempt also used an output directory outside the verifier's required `build/qt6-verification` root and stopped before capture. The passing R-stack invocation used the verifier's standard output root.

The first PDF comparison read Poppler text in block order. On the 400-study figure this can interleave adjacent study labels with wide wrapped labels. Sorting extracted study labels by their page coordinates verified all 400 rows in drawing order. Word's PDF does not yield the embedded figure text to Poppler. The ordered row audit reads the original SVG members in the DOCX and the page comparison renders Word's PDF.
