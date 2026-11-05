# #567: approved diagnostic label projection and CI recovery

Source: `gh run download 41960942547 -n full-r-stack-windows-golden-capture -D build/qa567-windows-capture`, checks job 127027031169. The retained raw capture identifies virtual CI commit d85f3831ab64b20c9879ec0bcd3741d0890a3387. It is not modified or replaced with Linux results.

Merged master before changes, then fetched/merged master 8d3609d2 (#568) before qualification and push. This also retains master's approved amino subgroup preview/reference update; no subgroup reference is changed here.

## Approved reference change

Only `lymph-diagnostic-random-dor`:

- Numeric section and coverage keys: `Odds Ratio Summary` → `Diagnostic Odds Ratio Summary`.
- Text section key: same rename. Four line-leading `Odds Ratio -` headings gain `Diagnostic `. The existing `H₀: diagnostic Odds Ratio = 1` text stays identical.
- Display identity: `Odds Ratio Forest Plot` → `Diagnostic Odds Ratio Forest Plot`. Artifact label/path/name/type, SHA, strict nonempty-content requirement and all five capability fields remain unchanged.
- Outer ZIP/contract SHA and size bindings are refreshed as required by the existing frozen-reference mechanism.

`apply.py` uses the guarded archive projection and SHA rebinding mechanism from #556's `artifacts/qa-r1/golden-proof/apply.py`; it does not regenerate fits, numeric values, raster artifacts or tolerances. `proof.json` is written before applying the projection. It pairs every one of the 14 numeric fields from the old frozen section with the new section in the sanctioned Windows capture. The field sets are identical, every delta is exactly zero, and every original tolerance is retained (`max(0.001, 1e-9 * abs(expected))`). Numeric text tokens (including the overall test and prediction interval) also match exactly. The sanctioned Windows PNG has the original SHA.

`update-audit.json` independently reverses the allowed label/key projection and compares the complete structures: only the target capture JSON and manifest JSON change inside the ZIP. Every other case and every raster payload is byte-identical. Numeric contract content reverses exactly after restoring the section/coverage keys and archive binding. Descriptor contract content reverses exactly after restoring that one identity and archive binding. No authority or exception policy changes.

## Capture lookup defect: do not freeze null metadata

The old-title lookup in the downloaded capture missed the renamed forest. Its display identity/name/type/SHA and capabilities are null. Those nulls are NOT accepted as new expectations. The golden harness now falls back to the configured artifact file's basename when the display title changes. A fresh real Qt/R lymph fit exercises this path in `check_descriptor.py`, retaining strict actual SVG content, identity, filename/type and capabilities. The baseline retains all existing content/capability requirements and only renames identity.

Replay against the unmodified older Windows capture (`recompare.py`) gives 460 pass / 13 existing accepted exceptions / two artifact drifts. Every numerical and text comparison passes. The two remaining raw-capture artifacts are explicitly retained in `recomparison.json`:

1. Lymph null descriptor, repaired by the harness rather than freezing missing metadata. Fresh Windows CI must exercise the repaired lookup.
2. Amino subgroup PNG: this capture predates the approved preview reference now merged on master. Before/after equality of that entire reference case is asserted. It is outside this change and remains untouched.

## CI failure fixes

The one-arm mean failure reproduces before the fix in the unchanged `calculator-mode-onearm-mean` scenario (`onearm-before.log`). This was an authority-initialization bug, not a number-parsing problem: initial derived-summary rendering read the empty entered authority before input mode existed. Initializing the active mode before raw imputation restores the raw summary preview; no guard is added to the test and no test input/assertion is removed.

Stale grid assertions now use exact values: Giamarellou `0.004`, its row `['0.08', '0.004', '1.44']`, and the UX small OR `0.0001`. Diagnostic authority and legacy-sheet section lookups use the new section key. The authority comparison math and numeric fixtures are unchanged.

## Reproduce

Source `/home/ali/.t3/qa-env/ENV.sh`; use this checkout's `PYTHONPATH=$PWD/src:$PWD`, `RCMS_QT6_BUILD_ROOT=$PWD/build/qt6-verification`; install current-source RCMetaR in build/rcmetar-lib and prepend it to RCMS_R_LIBS/R_LIBS/R_LIBS_USER. Typing targets win32 on Linux; exact commands/transcripts are retained.

```
python artifacts/qa-r1/golden-proof/qa567/recompare.py
QT_QPA_PLATFORM=offscreen python artifacts/qa-r1/golden-proof/qa567/check_descriptor.py
python -m pytest tests/analysis_regression/golden -q
python scripts/verify_rcms.py results-window
python scripts/verify_rcms.py lymph
python scripts/verify_rcms.py options-diagnostic
python scripts/verify_rcms.py analysis-dialog
python scripts/verify_rcms.py calculator-mode-onearm-mean
python scripts/verify_rcms.py sheets-legacy
python scripts/verify_rcms.py ux-improvements
```

The updater requires original references in `old/` (retained locally but not duplicated as a ZIP in Git); reconstruct those files from the parent of the reference-update commit. Download the source artifact again to reproduce the raw-capture proofs. E2E manifests retain commands, input files, screenshots, runtime and action/results under artifacts/verification/rcms; replay-results.json indexes final exit status and transcripts.
