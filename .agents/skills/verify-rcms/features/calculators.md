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
- The three baselines do not validate every numerical edge. Use the advanced modes below for entered estimates and reconstruction; retain distinct invalid-input and failure-injection checks.

## Additional modes after calculator changes

The baseline clicks the actual vertical-header viewport at the first section's center and requires the correct modal. Source owners: `dataset_table_view.py:row_header_clicked`, `binary_data_dialog.py`, `continuous_data_dialog.py`, `diagnostic_data_dialog.py`, `calculator_service.py`.

- **Binary:** select OR/RR/RD and a one-arm metric with `effect_combo_box` item data. Verify partial-count imputation, entered estimate/CI, Clear, and zero cells. Back-calculation uses `back_calculate_button`; ambiguous alternatives appear in `BinaryBackCalculationDialog.choice1_btn`/`choice2_btn`. Compare independently known counts and effect/variance; cancel the nested dialog before accepting a candidate.
- **Continuous:** exercise MD/SMD and one-arm mean/entered-effect data. Check `simple_table` N/Mean/SD/SE consistency; MD equal/unequal SD and SMD Hedges/Cohen choices; `g1_pre_post_table`, `g2_pre_post_table`, and `correlation_pre_post` for pre/post reconstruction. Test inconsistent input rejection, missing-data back-calculation, Clear, and nested Cancel. Correlation changes must change reconstructed variance without overwriting unrelated raw values.
- **Diagnostic:** Sens/Spec entered estimates and `prevalence_text_box` back-calculation must reconstruct the 2×2 table consistently. Reject negative/impossible counts and invalid intervals; preserve accepted data after Cancel.

For each changed mode, assert raw/entered values, independent preview expectations, acceptance, outer/nested cancellation, undo/redo, dirty state, and save/reopen. Analyze accepted data through R. Dataset creation coverage does not establish all calculator modes above.

## Automated mode proof

Run `uv run python scripts/verify_rcms.py calculator-mode-<suffix>`:

| Suffix | Actual controls and independent expectations |
| --- | --- |
| `binary-metrics` | OR/RR/RD selector and count edit; independently calculated previews |
| `continuous-metrics` | MD/SMD selector and mean edit; exact Hedges correction |
| `diagnostic-metrics` | Sens/Spec selector and count edit; proportions from counts |
| `onearm-proportion`, `onearm-mean` | Actual one-arm wizard, PR/mean calculator, accepted data and missing second arm |
| `entered-binary`, `entered-continuous`, `entered-diagnostic` | Clear, entered estimate and both CI bounds; independent log/identity/logit storage; entered triplet survives Cancel, undo/redo and reopen |
| `pre-post` | Both groups' pre/post tables; correlation 0 then .5 changes reconstructed SD; independent mean/variance |
| `back-binary` | Independently known OR/CI and totals reconstruct a valid ambiguous count candidate; nested Cancel before candidate 1 |
| `back-continuous` | MD/CI and partial N/mean/SD reconstruct the missing mean; nested Cancel before equal-SD candidate 1 |
| `back-diagnostic` | Independently known Sens/Spec logit intervals and prevalence reconstruct [80,20,10,90] |

Every mode uses the real row-header gesture, accepts, clears/cancels a subsequent draft, checks undo/redo and clean state, saves/reopens, and analyzes the accepted data with DL/z at six digits. Eight displayed pooled/inference/heterogeneity fields must match public `metafor::escalc`/`rma.uni`; entered variance is independently reconstructed from the entered interval. Diagnostic correction considers zeros in all four cells, even for a Sens analysis. Nested cancellation additionally preserves table cells, estimate/CI fields, metric parameter and button state.

This does not prove RR/RD back-calculation, candidate 2, unequal SD, Cohen reconstruction, PLN/PLO/PAS/PFT previews, or every invalid partial-input combination. Drive the affected alternative after changing it; do not infer its pass from OR/Hedges coverage.

Entered diagnostic acceptance must retain study inclusion. Require Sens enabled and the unavailable Spec/DOR/LR choices disabled after clearing counts and entering only Sens. Check the included count before acceptance and after reopen, then compare the mixed entered/raw pooled fit. An analyzable result that silently omits the edited study fails this contract. Finally accept Clear without replacement, undo, accept partial counts alongside the stored interval, and undo again: both unusable inputs must exclude the study, and both undos must restore the included entered-only data.


## Complete preview values

`calculator-diagnostic` and `calculator-continuous` require effect/CI fields to
contain enough pixel width for their actual displayed glyphs before editing. Shared
sizing expands with current values and resets the unfocused cursor to the start.
Inspect native captures for leading minus signs and digits; equal field widths alone
do not prove complete values. The diagnostic controls use Estimate rather than Est.

## HR and IRR

See [ratios.md](ratios.md) for the compact input, original-source persistence, analysis, plot and small-study workflows. Run `ratios-hr` and `ratios-irr` after changes affecting these families; the broader shared-change lane remains required.

`options-zero-cells` separately proves the generalized SMD table convention: Not estimable with interval dashes, save/reopen, finite recovery after correcting inputs, and blanks for incomplete input. This is grid evidence; it does not assert undefined labels inside calculator dialogs.

## Round-six numeric entry integrity

The twelve `calculator-mode-*` drives now use keyboard editing through real table
and line editors. Applicable tiny/huge/many-decimal/exponent values, decimal commas,
invalid entered intervals and correction, undo/redo and save/reopen are checked.
Continuous SDs exercise all four precision classes with independent group intervals
and public post-reopen fits. Compact summaries are paint-only; editor text stays
full precision. `calculator-grid-precision` covers raw and entered-effect grids,
unchanged commits, clipboard, CSV import, undo/redo and project reopening.
`calculator-ratio-precision` covers all five HR/IRR source modes and original-source
persistence with public effects. Domains remain constrained: counts are integers
and proportions remain in range. This does not qualify every reconstruction input
combination or a platform's native file picker.

## Calculator readouts

The three baseline drives assert compact estimate/CI text and bit-identical saved
raw/entered values against the retained pre-change accepted-row fixture.
`calculator-continuous` also requires no horizontal table scrollbar.
`calculator-binary` cross-checks OR/RR/RD intervals and selected Wald SE/Z/P using
independent `metafor::escalc` and `pnorm` calls, recording counts and full results.
These are offscreen Qt proofs, not native DPI qualification. Continuous arm
p-values remain reconstruction inputs; computed arm p-values are left blank.

`calculator-ratio-precision` also accepts reported HR/IRR intervals at a 90%
sheet confidence, verifies their SE by metafor::conv.wald and pooled weights
by rma.uni DL, then changes sheet confidence to 95%. Original bounds and
source confidence must remain unchanged, with the same analysis input SE.
The source interval level is stored per study; output confidence is separate.
