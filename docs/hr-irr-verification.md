# HR/IRR verification

Source verification on Windows, 2026-10-11. The implementation follows ADR-0014 through ADR-0016 and the [metafor review](hr-irr-metafor-review.md). The [user guide](hr-irr.md) describes the final compact workflow.

## Statistical and desktop evidence

The complete profile passed at `artifacts/verification/rcms/20261011T130509Z-98e4ba38-complete/summary.json`: current-source R-stack, 91 independent authority comparisons, and all 83 serial desktop scenarios with durable manifests. The R-stack includes a clean R CMD check, eight live bridge drivers, Reitsma comparisons/visual evidence, frozen numerical contracts, and 83 E2E cases. R source was unchanged during the later Python UI fixes.

Final targeted runs are retained separately because the wizard, deletion, and non-estimable display evolved during verification:

| Evidence directory under `artifacts/verification/rcms/` | Proves |
| --- | --- |
| `20261011T135417Z-731b29bf-ratios-hr` | Shared wizard entry/metric navigation, compact input, CSV, identity-safe deletion/undo/redo/reopen, all HR analysis families, numerical comparisons, plot edits and decoded exports |
| `20261011T140059Z-ac1cf4fc-ratios-irr` | Same IRR workflow, explicit double-zero label/tooltip, mixed sources, raw MH workflows, eligible-study bias procedures |
| `20261011T141051Z-81b83e9e-options-zero-cells` | Binary zero policies against the public-package oracle; SMD Not estimable/interval dashes, MD remains numeric, save/reopen, data correction and incomplete-input recovery |

The post-formatter E2E rerun passed all 83 scenarios in 909.63 seconds, recorded in `artifacts/verification/hr-irr-native/generalized-ux-e2e.log`. The subsequent startup change passed `20261011T142426Z-dd24b99c-project-shell`: launch maximizes after remembered normal and full-screen sessions. The failing pre-change reproduction is retained in `20261011T142339Z-adbe08a7-project-shell`. Final repository-wide type checking, including the verification harness and generated Qt forms, passes.

## Native Windows review

`artifacts/verification/hr-irr-native/` retains UI screenshots and accessibility trees, original synthetic HR/IRR project copies, launch/install transcripts, and replay instructions. Native driving uses the ordinary Qt/R source application with isolated test settings. It exercised compact tables; raw, reported, and log-input dialogs; missing-SE validation; cumulative and publication-bias results; contour layout; the shared wizard tile and both Matplotlib metric icons; actual right-click deletion and undo/redo; and the visible double-zero IRR label.

The first native review found crowded input fields and excessive table columns. The conditional study dialog and hidden input metadata fixed those. A later review caught illegible metric icons; their combo-box size is now 44 × 36. Context-menu deletion initially left a stale visible row and could choose the wrong study after sorting. Reset synchronizes displayed studies by identity, and the menu resolves the displayed study to its canonical record. Undo also exposed a read-side mutation: a ratio model reset created empty analysis units and cleared redo. Ratio previews now bypass the irrelevant legacy recalculation path, and empty-cell rendering does not create units.

The latest table convention is **Not estimable** in an undefined effect cell and **—** in its interval cells. Complete calculated previews are distinguished from incomplete input. Original numeric inputs are preserved; these labels are display values, not stored effect estimates. IRR explains two zero-event groups explicitly. The shared formatter applies the same convention to binary, continuous, and diagnostic previews when the selected metric returns an undefined effect; a corrected finite result remains numeric. Native capture 28 confirms the SMD label and interval dashes fit the existing table. Capture 29 shows a fresh ordinary launch maximized behind the welcome dialog.

Retained failures include the sorted-delete target mismatch, stale-row deletion, IRR redo loss, and the SMD undefined-effect reproduction. Failed runs remain labelled failed in their manifests; they are not counted as passed evidence.

## v0.4.2 release verification

The updated matrix adds `ratios-samples`: all original HR/IRR rows, source covariates, independent metafor fits, HR timing subgroups, descriptive IRR funnels, and save/reopen equality. All 84 desktop workflows plus the runtime doctor passed in `artifacts/verification/rcms/20261011T150050Z-e58e32f3-complete/summary.json` before the final complexity cleanup. The final current-source R-stack transcript is `artifacts/verification/metafor-samples/final-v042-r-stack.log`; it records R CMD check with 1,757 passing assertions, one skipped standalone visual test, no errors or warnings, and one existing NOTE about the declared `tiff` import. Its separate 21 Reitsma visual cases and eight live bridge tests pass.

`artifacts/verification/v042-final/` retains 91 independent statistical authority comparisons, installed-source equality for all 710 named RCMetaR function signatures and bodies, source hashes, byte-identical rebuilding of all seven sample archives, repository-wide typing, and code-health evidence. The retained Python failure suite passes 369 checks with one skip; the corrected current-schema application-shell fixture passes all 18 checks. Complexity thresholds and exceptions were not relaxed.

`v042-final/native-proof.json` binds 32 screenshot/accessibility files from the final ordinary Windows source application: original IRR counts/person-time, all 65 HR source rows, log HR/SE input, actual Windows project picker, nine-study publication-bias eligibility, invalid contour input, correction, and real result/funnel recovery. Invalid contour input still shows the generic unexpected-error dialog and leaves the busy indicator visible until retry. Valid correction succeeds; this presentation issue remains recorded in the feature map. The owned preview was closed after capture.

The initial Windows package qualification exposed omitted v2 schemas: source execution could open the new samples, but the frozen app timed out opening HR. All three platform recipes now preserve both schema directories. The failed CI diagnostics and failure inventory are retained in `v042-final/package-diagnostics/` and `package-schema-failures.txt`. Actual qualification of the corrected Windows package is reported by [PR #527's checks](https://github.com/AliSalman-et-al/rc-metastudio/pull/527/checks), including opening every shipped sample. Source execution alone does not establish package qualification.

An incorrectly selected application scratch directory cleared earlier local evidence directly under `metafor-samples`; the main per-workflow E2E evidence and `hr-irr-native` captures survived. The final native proof was recreated outside that scratch directory in `v042-final`. Use that manifest for the final review.

## Replay and limits

Follow [.agents/skills/verify-rcms/SKILL.md](../.agents/skills/verify-rcms/SKILL.md), configure the pinned test-owned R library, generate Qt resources, and run:

```powershell
uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full
uv run python scripts/verify_rcms.py ratios-hr
uv run python scripts/verify_rcms.py ratios-irr
uv run python scripts/verify_rcms.py options-zero-cells
uv run python -m pytest tests/e2e -n 2 --durations=10
```

The final pinned runtime is R 4.6.1, RCMetaR 0.4.2, metafor 5.0-1, meta 8.5-0, mada 0.5.12, Qt 6.11.1, PyQt 6.11.0, and Python 3.11.9. Earlier captures used RCMetaR 0.4.1. A matching package version alone does not prove installed-source equality; the current-source installation transcript and provenance hashes are retained.

The automated moderator drive is numeric. Factor/interactions, legacy bootstrap/permutation, every estimator/inference UI pairing, all OS import entry points, fractional DPI, other operating systems and release packages are not newly qualified by this work. CSV automation starts at the import page with controlled picker paths; native Windows project picking is exercised separately. The existing Begg result displays an unavailable CI in prose; it is not a newly introduced numerical estimate. See the verification feature maps for the precise coverage.
