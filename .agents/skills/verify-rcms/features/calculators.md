# Effect-size calculators

Users edit a study's raw inputs, inspect the derived effect preview, accept or cancel the change, and analyze the durable accepted data.

## Sub-features

- `calculator-binary`: events/totals, comma-decimal input, valid accepted counts.
- `calculator-continuous`: sample size, mean and standard deviation.
- `calculator-diagnostic`: TP/FN/FP/TN inputs.
- `calculator-rollback`: Cancel, undo/redo, dirty state and reopen.

## How to get to it (user POV)

- Open a matching project and single-click the study row header (`sectionClicked`).
- Analysis > Effect-size tools selects the workspace metric; it does not launch a calculator. The menu is disabled for diagnostic projects; that calculator offers Sens/Spec internally.

## Driving it with Qt E2E

Preconditions: doctor passes; the matching committed sample supplies compatible raw inputs.

- **Binary.** Run `uv run python scripts/verify_rcms.py calculator-binary`. The row-header path opens `BinaryDataDialog`; `raw_data_table` accepts the first study's increased event count and corresponding total.
- **Continuous.** Run `uv run python scripts/verify_rcms.py calculator-continuous`. `ContinuousDataDialog.simple_table` changes the first study mean by `1.5` using a comma decimal.
- **Diagnostic.** Run `uv run python scripts/verify_rcms.py calculator-diagnostic`. `DiagnosticDataDialog.two_by_two_table` changes the first study TP count by one.
- **Acceptance and rollback.** All scenarios click the real dialog OK/Cancel buttons, observe accepted raw values and dirty state, cancel a second edit, undo to the clean original, redo, save and reopen `workflow/calculator.rcms`, then analyze through R. `calculator-before`, `calculator-accept`, `calculator-cancel`, and `calculator-reopened` preserve the observed sequence.

## Gotchas

- Cancellation must preserve the last accepted data, not the draft preview.
- A derived effect preview is not the statistical authority for analysis. Accepted raw data must survive reopening and feed the real R analysis.
- These scenarios do not validate every numerical edge. Entered effect estimates, partial data, back-calculation, and zero-cell corrections require the relevant retained numerical/failure tests and targeted UI proof.

## Additional modes after calculator changes

The baseline clicks the actual vertical-header viewport at the first section's center and requires the correct modal. Source owners: `dataset_table_view.py:row_header_clicked`, `binary_data_dialog.py`, `continuous_data_dialog.py`, `diagnostic_data_dialog.py`, `calculator_service.py`.

- **Binary:** select OR/RR/RD and a one-arm metric with `effect_combo_box` item data. Verify partial-count imputation, entered estimate/CI, Clear, and zero cells. Back-calculation uses `back_calculate_button`; ambiguous alternatives appear in `BinaryBackCalculationDialog.choice1_btn`/`choice2_btn`. Compare independently known counts and effect/variance; cancel the nested dialog before accepting a candidate.
- **Continuous:** exercise MD/SMD and one-arm mean/entered-effect data. Check `simple_table` N/Mean/SD/SE consistency; MD equal/unequal SD and SMD Hedges/Cohen choices; `g1_pre_post_table`, `g2_pre_post_table`, and `correlation_pre_post` for pre/post reconstruction. Test inconsistent input rejection, missing-data back-calculation, Clear, and nested Cancel. Correlation changes must change reconstructed variance without overwriting unrelated raw values.
- **Diagnostic:** Sens/Spec entered estimates and `prevalence_text_box` back-calculation must reconstruct the 2×2 table consistently. Reject negative/impossible counts and invalid intervals; preserve accepted data after Cancel.

For each changed mode, assert raw/entered values, independent preview expectations, acceptance, outer/nested cancellation, undo/redo, dirty state, and save/reopen. Analyze accepted data through R. Dataset creation coverage does not establish all calculator modes above.
