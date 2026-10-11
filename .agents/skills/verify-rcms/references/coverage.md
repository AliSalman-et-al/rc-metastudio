# Coverage and change checklist

Use this before declaring an app change verified. These are behavior obligations, not source-string inventories or a quota of tests. A full desktop pass establishes the automated paths below; affected targeted paths still need an actual drive and independent assertion. Mark each affected row exercised, failed, or unexercised with its evidence and reason. Never turn an unexercised row into a pass because a nearby path ran.

| Surface | Automated proof | Additional obligations when affected |
| --- | --- | --- |
| New Dataset | Eight `analysis-data-*` plus two HR/IRR real wizard paths, default analysis and reopen | Invalid/duplicate outcome name, Back/Cancel, alternate metric, empty/one-study guardrails |
| Open/save/import | Editing rollback and CSV covariate reopen | Menu/toolbar/shortcut/recent/startup entry; CSV dialect/schema/Excel; interrupted saves and resource limits |
| Structure and navigation | Structure add/rename/Cancel/undo/redo/reopen; numeric/factor covariate creation and analysis | Deletion, navigation permutations, reference-level changes |
| Table | Rename, inclusion, paste/copy rectangle, sorting identity, undo/redo, calculator raw acceptance | Insertion/deletion, rectangular Clear, invalid-paste atomic rollback |
| Data/model boundary | Ten dataset types; raw/entered/reconstructed one/two-arm calculator data; exclusion, CI, zero cells; public metric matrix | Missing-data/error recovery and remaining correction/data combinations |
| Analysis actions | Standard, cumulative, leave-one-out, subgroup and regression; the original three families plus HR/IRR | Complete numerical sections, selected method/metric/parameters, correct study subset, error recovery |
| Estimators | All fixed selector keys; default random and joint Reitsma | Unsupported combinations, alternative UI enum propagation; public `metafor`/`mada` reference |
| Heterogeneity/inference | Ten × four backend combinations; three alternate UI pairs × binary/continuous/diagnostic at 90% CI | Remaining UI pairs; df/singular/zero-variance limits |
| Diagnostics | Joint Sens/Spec, combined five metrics, univariate sequential/subgroup; three regression moderator shapes | Entered-estimate restrictions, missing counts, single metric, no selection, shared parameter conflict |
| Small-study effects | Binary/SMD ordinary+contour+trim-and-fill+extrapolation; diagnostic Deeks; HR/IRR generic procedures with direct primary Egger oracle | Low-tau² Harbord, MD Egger/Begg, descriptive-only metrics, unavailable reasons, direct package numerical oracles |
| Calculators | Actual row gesture; twelve original modes plus conditional HR/IRR input; preview references, entered bounds, Clear/Cancel, nested cancellation, pre/post, undo/redo/reopen and independent pooled analysis | RR/RD and second candidates, unequal SD/Cohen, remaining transformed metrics, invalid partial data |
| Results/plots | Eleven scene-context editors; Apply/reopen/Cancel and persisted parameters; PDF/PNG/TIFF/SVG decoded exports and save cancellation | Navigation/copy; remaining appearance controls; parameterless PNG; failed regeneration/IO rollback |
| Shell/native | Runtime doctor; Open/Save As/recent/legal; dirty-open Cancel; native lanes; default maximization and normal-size Restore | Close/dirty alternatives, focus/keyboard, platform DPI/accessibility |
| Release | Packaging lane in lanes.md | Actual supported target artifacts, provenance/relocation/trust; local source proof cannot qualify a release |

## Choosing scope

For a local behavior fix, run its mapped scenario plus its boundary/error case and targeted rows above. For shared analysis/data type/reconstruction/R changes, run `verify_all.py --full`, complete affected parameter/eligibility/error rows, and inspect every report. For a requested all-app maintenance audit, source-read every feature, run the complete desktop matrix, and drive all additional changed or claimed-complete surfaces. If any required path remains unavailable, report the exact attempt/prerequisite; do not claim the whole app is verified.

Independent authority checks compare externally constructed input with public pinned packages. Comparing two calls to the same app adapter proves routing at most. Successful rendering alone cannot detect a wrong estimator. Reuse frozen/public authority evidence instead of duplicating test formulas or blessing current output.

## Evidence audit

Check child exit status, assertion transcript, method/configuration and observed state; validate manifest hashes after teardown. Confirm reopened raw/entered/covariate values, not logged constants. Preserve canonical rendered plot paths even when a legacy `images` path names an absent PNG. Copy R-session plots before shutdown. Confirm owned scratch is empty and no owned child survives. Keep failed runs available. Link aggregate and per-scenario records and state source/runtime provenance and native/OS limitations.


## HR/IRR change evidence

`ratios-hr` and `ratios-irr` exercise the changed wizard, compact table,
conditional dialog, original-input CSV/defaults, transactional clipboard,
source-confidence undo/redo, save/reopen, and applicable main analyses. They compare
pooled and every sequential/subgroup row, numeric regression, and primary Egger
with public package calls, and decode four export formats for six plot contexts.
Raw IRR adds MH eligibility, original-count pooling and non-estimable subsets.
The [verification report](../../../../docs/hr-irr-verification.md) links completed
runs, native observations, fixes and source/runtime provenance. Factor/interactions,
legacy bootstrap/permutation, all alternate UI estimator/inference pairs,
fractional DPI and release packages remain unclaimed by these two scenarios.
