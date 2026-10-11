# Effect-size calculators

Users edit a study's raw inputs, inspect the derived effect preview, accept or cancel the change, and analyze the durable accepted data.

## Sub-features

- `calculator-binary`: events/totals, comma-decimal input, valid accepted counts.
- `calculator-continuous`: sample size, mean and standard deviation.
- `calculator-diagnostic`: TP/FN/FP/TN inputs.
- `calculator-rollback`: Cancel, undo/redo, dirty state and reopen.

## How to get to it (user POV)

- Open a matching project and double-click the study row header.
- Analysis > Effect-size tools exposes metric/calculator tools; those entry points need a targeted drive when changed.

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
