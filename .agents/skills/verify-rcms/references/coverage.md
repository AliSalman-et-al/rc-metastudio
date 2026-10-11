# Coverage and change checklist

Use this before declaring an app change verified. These are behavior obligations, not source-string inventories or a quota of tests. A full desktop pass establishes the automated paths below; affected targeted paths still need an actual drive and independent assertion. Mark each affected row exercised, failed, or unexercised with its evidence and reason. Never turn an unexercised row into a pass because a nearby path ran.

| Surface | Automated proof | Additional obligations when affected |
| --- | --- | --- |
| New Dataset | Eight `analysis-data-*` real wizard paths, default analysis and reopen | Invalid/duplicate outcome name, Back/Cancel, alternate metric, empty/one-study guardrails |
| Open/save/import | Editing rollback and CSV covariate reopen | Menu/toolbar/shortcut/recent/startup entry; CSV dialect/schema/Excel; interrupted saves and resource limits |
| Structure and navigation | Source recipes in projects.md; targeted drive required | Outcome/group/follow-up CRUD, retain data while navigating, factor/numeric covariate CRUD and reference levels |
| Table | Rename, undo/redo, calculator raw acceptance | Inclusion, insertion/deletion, sorting identity, rectangular paste/clear, invalid-paste atomic rollback |
| Data/model boundary | Eight default dataset types; all metric families in public-package matrix | Raw versus entered/reconstructed effects, one/two arms, missing data, corrections, excluded studies, nondefault CI |
| Analysis actions | Standard, cumulative, leave-one-out, subgroup and regression; all three families | Complete numerical sections, selected method/metric/parameters, correct study subset, error recovery |
| Estimators | All fixed selector keys; default random and joint Reitsma | Unsupported combinations, alternative UI enum propagation; public `metafor`/`mada` reference |
| Heterogeneity/inference | Ten × four backend combinations and 90% CI | Alternate choices through UI; df/singular/zero-variance limits, same coverage for affected family |
| Diagnostics | Joint Sens/Spec, combined five metrics, univariate sequential/subgroup; three regression moderator shapes | Entered-estimate restrictions, missing counts, single metric, no selection, shared parameter conflict |
| Small-study effects | Binary/SMD ordinary+contour+trim-and-fill+extrapolation; diagnostic Deeks | Low-tau² Harbord, MD Egger/Begg, descriptive-only metrics, unavailable reasons, direct package numerical oracles |
| Calculators | Actual row gesture and three raw-data Accept/Cancel/undo/redo/reopen paths | One arm, entered effects, Clear, partial data, nested back-calculation, pre/post correlation |
| Results/plots | Real scene, standard forest Apply/Cancel, PDF exports | Navigation/copy; each changed producer/editor; menu gestures; all offered export formats and rollback |
| Shell/native | Runtime doctor; native lanes in lanes.md | Help/legal, close/dirty prompts, state restoration, focus/keyboard, platform DPI/accessibility |
| Release | Packaging lane in lanes.md | Actual supported target artifacts, provenance/relocation/trust; local source proof cannot qualify a release |

## Choosing scope

For a local behavior fix, run its mapped scenario plus its boundary/error case and targeted rows above. For shared analysis/data type/reconstruction/R changes, run `verify_all.py --full`, complete affected parameter/eligibility/error rows, and inspect every report. For a requested all-app maintenance audit, source-read every feature, run the complete desktop matrix, and drive all additional changed or claimed-complete surfaces. If any required path remains unavailable, report the exact attempt/prerequisite; do not claim the whole app is verified.

Independent authority checks compare externally constructed input with public pinned packages. Comparing two calls to the same app adapter proves routing at most. Successful rendering alone cannot detect a wrong estimator. Reuse frozen/public authority evidence instead of duplicating test formulas or blessing current output.

## Evidence audit

Check child exit status, assertion transcript, method/configuration and observed state; validate manifest hashes after teardown. Confirm reopened raw/entered/covariate values, not logged constants. Preserve canonical rendered plot paths even when a legacy `images` path names an absent PNG. Copy R-session plots before shutdown. Confirm owned scratch is empty and no owned child survives. Keep failed runs available. Link aggregate and per-scenario records and state source/runtime provenance and native/OS limitations.
