# Sheet caller migration proof

Runtime: `source build/sheets-baseline/ENV.sh`; generated forms with `uv run --no-sync python scripts/build_qt6.py generate --build-root build/qt6-verification`. Each scenario used `uv run --no-sync python scripts/verify_rcms.py <scenario>` (offscreen Qt, pinned real R). `--no-sync` preserves the locally compiled rpy2 bridge documented in SHEETS.md.

Exact requested rg inventory: **363 before → 60 after**. Remaining matches: project_domain.py (38), project_format.py (10), v1/v2 validation schemas (12). No runtime/UI caller remains. Retained inventories and failed/retry transcripts: `build/sheets-caller-migration/`.

Product diff against 6c19fd04: **263 added / 1384 deleted** lines under src/rc_metastudio. Frozen numerical contracts were not changed.

| Scenario | Result | Evidence directory under artifacts/verification/rcms |
| --- | --- | --- |
| amino | PASS | `20261031T000330Z-265b2643-amino` |
| continuous | PASS | `20261031T000515Z-ae338127-continuous` |
| ratios-hr | PASS | `20261030T235756Z-fea9c402-ratios-hr` |
| ratios-irr | PASS | `20261030T235959Z-ca594f5e-ratios-irr` |
| analysis-data-diagnostic | PASS | `20261031T000534Z-8dff07a8-analysis-data-diagnostic` |
| sheets | PASS | `20261031T000600Z-b97d1c2d-sheets` |
| project-table-covariates | PASS | `20261031T000631Z-550a5ba4-project-table-covariates` |
| analysis-amino-binary-subgroup | PASS | `20261031T000357Z-16a50278-analysis-amino-binary-subgroup` |
| analysis-amino-binary-meta-regression | PASS | `20261031T000419Z-bde700c3-analysis-amino-binary-meta-regression` |
| calculator-binary | PASS | `20261031T000431Z-a11337c8-calculator-binary` |
| calculator-continuous | PASS | `20261031T000514Z-f3124b39-calculator-continuous` |
| calculator-diagnostic | PASS | `20261031T000539Z-1c5ec301-calculator-diagnostic` |
| csv | PASS | `20261031T000528Z-f3597d40-csv` |
| analysis-data-twoarm-proportion | PASS | `20261030T235719Z-d5efeab7-analysis-data-twoarm-proportion` |
| project-structure | PASS | `20261031T000431Z-c815bb82-project-structure` |

Every directory retains the exact command, inputs/workflow artifacts, screenshots, stdout/stderr and hashed manifest. Original failed attempts remain retained. The covariate scenario includes independent metafor regression/subgroup comparisons and sheet-local add, edit, type conversion, rename, delete/undo and reopen. `project-structure` now runs the sheet tab transaction drive because the old dialog is deleted.

## Hillclimb limitation

`uv run --no-sync python scripts/verify_rcms.py hillclimb` exits **2**: invalid scenario. `--help` does not register hillclimb, and `docs/ux-hill-climb/SCOREBOARD.md` is absent at supplied HEAD 6c19fd04. T1–T5 counts and baseline comparisons are therefore **unavailable**, not zero or passing. The rejection is retained in `build/sheets-caller-migration/hillclimb.log`. No replacement baseline or synthetic counts were invented.
