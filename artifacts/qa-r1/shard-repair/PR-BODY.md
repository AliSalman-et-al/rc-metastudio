## Summary

Fix F6, F10, F11, F13, F16, F17 and F20 without changing fitted results. The broad F14 p-value/CI notation and precision rewrite is reverted completely: master styles and user-selected decimal places remain, including six decimals when selected.

```text
unchanged fitted result
  -> plots: directions anchored at null; clearer SE label; omission header once
  -> reports: metric identity, plain wording, available columns
  -> in-app views: initial fit; readable word/CI wrapping
```

The only F14 remainder is report-only suppression of numerical noise in Q (`0 < abs(Q) < 1e-10`), displayed as zero at the selected precision. It does not apply to effect estimates, p-values, raw fitted objects, R output, or the full-precision appendix. No golden field changes for this rule.

Merged origin/master through e7d7389c, including #553, #554, #555, #557, #558, #559 and #560. The merged Peto→OR null label, fit-based contribution rules, BMJ method labels, axis validation, CSV import and diagnostic label wrapping are retained. The #555 stacked diagnostic layout, sheet strip and publication-bias layout are retained. The merged export drive exposed that AdaptiveComboBox exported long choice widths as minimums, forcing the combined form beyond the viewport. Its minimumSizeHint now permits horizontal shrinking while retaining the same preferred hint, natural height and complete popup choices. #555 stacking and the strict visibility assertion are unchanged. The #557 `_print_document` black-on-white / Arial 9 pt PDF body/caption fix and black DOCX styles are intact. Export functions compare exactly with master.

## Evidence

- Golden verifier/tamper-contract tests: 43 passed previously; final Windows-capture recomparison and structural audit pass.
- Strict repository typing passes with the win32 target and generated Qt paths after the final master merges. Focused Results layout tests: **65 passed**, `-n 1`.
- Final focused private-library R tests (`forest-metafor-renderer`, `summary-display`, `ratios`): **1,258 passed expectations, zero failures or errors**. The earlier full package suite also passed. The existing opt-in visual-QA test remains opt-in; no skip was added.
- Focused Results/analysis/compact-transient/diagnostic GUI checks: 103 passed, 1 existing opt-in skip. Windows deployment contracts plus earlier Results checks: 75 passed, 5 existing platform skips. Both use `-n 1`.
- **23/23 real Qt/R scenarios pass**, serially: all 19 failed scenarios across the three Windows shards, plus both manuscript export paths and Peto/MH integration. Final scenario commands, exit codes and evidence directories are indexed in `artifacts/qa-r1/shard-repair/replay-results.json`.
- Interrupted IRR attempts (lost supervisor, then shared disk exhaustion) are excluded from the success index; the identical scenario was restarted after space recovered. No expectation was changed for these environment failures.
- No local full pre-push run: deferred to CI as instructed.
- Final native dark/+6 pt amino screenshot shows a 123% initial width fit and single-line favours labels separated at the null, clear of axis/ticks. Session stopped immediately after capture. Full native light/dark/font matrix remains incomplete; Windows native execution awaits CI.

The deeper HR replay exposed a separate F11 scrollbar feedback loop while opening a plot context menu. Using the actual retained HR SVG, the before probe recorded 198 refits; the corrected view settles after four. Fit width now reserves the vertical scrollbar's width consistently, so hiding that scrollbar cannot enlarge the plot and make it necessary again. Exports retain their original dimensions. The E2E context path observes viewport resize events and requires it to settle before opening the menu.

![Native dark + large font forest footer](https://raw.githubusercontent.com/AliSalman-et-al/rc-metastudio/fix/qa-r1-presentation/artifacts/qa-r1/shard-repair/native/16-final-favours.png)

### Exact remaining expectation changes

| Location | Before | After / reason |
| --- | --- | --- |
| `r/RCMetaR/tests/testthat/test-forest-metafor-renderer.R:707` | left footer x = midpoint of axis left edge and 0 | left footer x = 0; F6 text ends at null; same `expect_equal`, tolerance 1e-8 |
| `r/RCMetaR/tests/testthat/test-forest-metafor-renderer.R:708` | right footer x = midpoint of 0 and axis right edge | right footer x = 0; F6 text starts at null; same assertion/tolerance |
| `r/RCMetaR/tests/testthat/test-forest-metafor-renderer.R:1850` | `paste0("Study omitted: ", study.labels)` | exact `study.labels`; F20 prefix retained once in header |
| `tests/e2e/report_retention.py:214` | repeated diagnostic Fixture rows without metric | exact `Sensitivity: Fixture…` / `Specificity: Fixture…`; F10 |
| `tests/e2e/report_retention.py:278,285` | tiny heterogeneity / subgroup-test Q retained as floating-point noise | explicit Q statistics only below 1e-10 display zero at selected precision; other values unchanged |
| `tests/e2e/report_retention.py:342` | Study results table always required | table required iff study rows exist; F16 |
| `tests/e2e/report_retention.py:353` | fixed SE/z-or-t/p columns and complete rows | exact available-column projection of the same complete rows; strict header names and all available values retained; F16 |
| `tests/e2e/report_retention.py:383` | full-precision table located after fixed three-table prefix | located by exact title because empty scaffolding can disappear; retained values still compared exactly |
| `tests/e2e/report_retention.py:398` | `Clinical interpretation — Output` / `Output: …` | exact source title / original content without developer prefixes; F13 |
| `tests/e2e/report_retention.py:406` | literal HTML spaces | normalize NBSP to space for the exact text comparison; only in-app CI wrapping protection, F17 |
| `.agents/skills/verify-rcms/scripts/analysis_matrix.py:206` | smaller figures must remain at native width | every initial figure fills at least 90% of viewport, including upscaling small figures; existing no-overflow assertion retained; F11 |
| `tests/e2e/desktop_driver.py:328` | initial width not asserted | rendered selected plot must fill at least 90% of viewport; F11 |
| `tests/analysis_regression/golden/support/golden_analysis.py:1105` | omission identity inferred from repeated row prefix | infer omitted-fit context from `Study omitted` header; preserve the SAME frozen numeric keys/values |
| golden `amino-binary-leave-one-out`, `texts.Leave-one-out Summary` | `Study omitted: Name, year` repeated on 19 rows | exact `Name, year`; header once; every number identical |
| golden `continuous-leave-one-out`, `texts.Leave-one-out Summary` | same prefix on 6 rows | exact `Name, year`; header once; every number identical |

Additional exact expectation changes from the Windows shard repair:

| Location | Before | After / reason |
| --- | --- | --- |
| `test-forest-metafor-renderer.R:945` | `expect_gte(direction_lines, 3)` | `expect_equal(direction_lines, 1L)`; F6 now fits each full label on one line |
| `tests/e2e/header_geometry.py:69` | reconstruct labels from all text sharing x, interleaving both sides | exact full single-node strings, opposite start/end anchors and a narrow measured null gutter; existing device/overlap checks retained; Qt-painted ink must have a gap ≥ 0.25 of the font size |
| `tests/e2e/ux_workflows.py:463` | accumulate wrapped tokens at the same x | exact one-node `Favours <arm>` string for each arm |
| `.agents/skills/verify-rcms/scripts/advanced_workflows.py:483` | exact `Standard error (log scale)` | exact `Standard error of log odds ratio`, or hazard/incidence rate ratio for the selected ratio metric; membership strictness unchanged |
| `.agents/skills/verify-rcms/scripts/advanced_workflows.py:553` | two labels required even for a one-sided axis | exact full labels when the saved plot range leaves room on both sides of null; exact empty tuple otherwise |
| `tests/e2e/report_retention.py:341` | first two report tables always mean Pooled effect / Model fit, even when empty | identify by exact title; each table required iff its expected rows exist; exact available headers and every value retained |
| `.agents/skills/verify-rcms/scripts/advanced_workflows.py:711`, plot context path | no idle resize stability check | after settling, observe 100 ms and require at most two viewport resize events; prevents the proven F11 loop |

The actual Windows HR/leave-one-out renders were inspected before edits. Qt trims outer whitespace, so the gutter uses measured drawing coordinates. The ink check renders a small region at sufficient resolution for tiny fitted stress labels, without weakening its gap requirement. HR showed `FavoursFavours Control` with `Intervention` on a second line: a real rendering regression. Shared measured font fitting and a one-space gutter in drawing coordinates fix it; assertions were not relaxed to accept interleaving/wrapping.

![HR before: wrapped/interleaved labels](https://raw.githubusercontent.com/AliSalman-et-al/rc-metastudio/fix/qa-r1-presentation/artifacts/qa-r1/shard-repair/review/hr-before.png)

![HR after: single-line null labels](https://raw.githubusercontent.com/AliSalman-et-al/rc-metastudio/fix/qa-r1-presentation/artifacts/qa-r1/shard-repair/review/hr-after.png)

All F14 notation-only E2E/testthat/golden expectation changes are reverted; no match was loosened, expectation skipped, or numerical tolerance changed. Existing test and authority tolerances remain untouched.

### Mechanical golden proof

The two previously approved text changes remain: `texts.Leave-one-out Summary` removes 19 repeated prefixes in amino and six in continuous. The original checker pairs 164 numeric tokens exactly; no number is added or removed.

Windows run 41820827724 exposed the same intended F20 change under the Windows exact-artifact policy. After the user's explicit approval of the narrower canvases, the repository updater replaced ONLY these two PNG artifacts and their SHA bindings:

| Case | Before | After |
| --- | --- | --- |
| `amino-binary-leave-one-out` | 6391×5880; 19 `Study omitted: Name, year` rows | 5700×5880; `Name, year`, heading retained once |
| `continuous-leave-one-out` | 6941×3229; six repeated prefixes | 6287×3229; names/years only, heading retained once |

Review PNGs:

![Windows amino leave-one-out](https://raw.githubusercontent.com/AliSalman-et-al/rc-metastudio/fix/qa-r1-presentation/artifacts/qa-r1/golden-proof/windows-plot-proof/amino-binary-leave-one-out-new.png)

![Windows continuous leave-one-out](https://raw.githubusercontent.com/AliSalman-et-al/rc-metastudio/fix/qa-r1-presentation/artifacts/qa-r1/golden-proof/windows-plot-proof/continuous-leave-one-out-new.png)

Proof under `artifacts/qa-r1/golden-proof/windows-plot-proof/`: `check_windows.py`, `proof.json`, `check_data_coordinates.py`, `data-coordinates-proof.json`, `apply_windows.py`, `audit_update.py`, `update-audit.json`, `reference-diff-stat.txt`, and transcripts. These are throwaway evidence, not product tests or reference generators.

- Exact frozen numeric contract, numeric strings, row order/count and descriptor identity/capabilities are unchanged. Only the specified prefix is removed from source row text.
- Every rendered numeric annotation and study-label remainder (including years), both headings, all four inference/model footer lines and axis ticks are checked. Raster glyph edges and axis-normalized endpoints/estimate squares agree within finite raster rounding (two pixels); absolute canvas coordinates intentionally change.
- A separate real-R replay of both actual golden cases switches only the master/current row-label producer and uses R `identical()` on full-precision effects, estimate/CI display coordinates, SEs, weights and fitted statistics. No numerical comparison tolerance is used.
- The update audit permits exactly five changed archive members: two PNGs, their capture JSON artifact-SHA fields, and the same SHA fields in the archive manifest. All nine other PNGs and all text/numerical fields are identical. Numerical contract and authority tolerances never change; the numeric JSON changes only its archive SHA binding. Plot-descriptor JSON changes only the archive binding and two artifact-oracle hashes.
- Recomparison of the downloaded Windows capture: **475 rows, no failures**. The 13 existing accepted exceptions are unchanged.

Reference diff stat is retained in `reference-diff-stat.txt`:

```text
 tests/analysis_regression/baseline/manifest.json   |   8 ++++----
 .../baseline/numeric-contract.json                 |   2 +-
 .../baseline/observed-golden-baseline.zip          | Bin 11774097 -> 11335217 bytes
 .../baseline/plot-descriptors.json                 |   6 +++---
 4 files changed, 8 insertions(+), 8 deletions(-)
```

### Packaged smoke failure diagnosis

Uploaded Windows job 126509715667 evidence confirms the failure was solely summary identity after F14: native scales and log markers passed. Restoring master p-value notation reproduces pinned hash `61ea84ba73eab657282ceabdf3ee1f29ab0ed55a1be574023017bc490d279ab5` exactly. The real source application through the package-analysis entry also produces that hash after the revert. No smoke/inspection scripts, pinned hashes or package expectations were changed. The subsequent run 41820827724 confirms **Required Windows x64 Package Qualification succeeded** (job 126543479317), along with packaging contracts. This success precedes the present footer/reference follow-up; its new push still requires CI.

## Merge Danger

**Door:** two-way

**Blast Radius:** presentation

Fits and authority gates are unchanged. Do not merge automatically; user requested a ready PR only.
