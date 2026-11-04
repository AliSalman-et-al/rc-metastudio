# Calculator round-one fixes

Branch: fix/qa-r1-calculator. Native display: Linux/X11, real Qt/R, ui.py session calc-fix. No R/form/model numerical algorithms changed.

## Reproduction before edits

Opened sample_projects/continuous.rcms with the real file picker; clicked Carroll row header. Switched Group summaries -> Entered estimate, entered SMD 0.3, returned to summaries. Estimate stayed 0.3 while summaries stayed N60/mean94/SD22 and N60/mean92/SD20 (SMD approximately .0945). OK closed; reopening reconstructed the raw preview .0945. Thus this particular entered-effect mismatch did not survive reopening.

Populated pre/post through actual grid editors: intervention N20, pre mean10 SD2, post mean15 SD2; control N20, pre mean10 SD2, post mean12 SD2; correlation0. In summaries changed intervention mean change5 to1, then returned to pre/post. Visible changes remained5 and2 but SMD was -.3465. OK closed successfully. This is a settled mode mismatch, not a mid-edit delay. F25/before-prepost.png retains it. The existing E2E drive independently demonstrated accepted hidden summaries before this fix; the tightened assertion now requires restored MD3 and original pre/post-derived raws.

## Commands

Environment: source /home/ali/.t3/qa-env/ENV.sh; export PYTHONPATH=$PWD/src:$PWD. Generated forms: /home/ali/.t3/qa-env/qt6. Each typing transcript retains the full exact strict Ty command and win32 target.

- python -c 'from scripts.verify import run_typing; from pathlib import Path; run_typing(Path("/home/ali/.t3/qa-env/qt6"))'
- QT_QPA_PLATFORM=offscreen python -m pytest tests/python/gui/test_continuous_data_transactional_layout.py tests/python/gui/test_continuous_signal_blocker_contract.py -n 1 -q
- python scripts/verify_rcms.py calculator-mode-pre-post
- python scripts/verify_rcms.py calculator-mode-back-continuous
- RCMS_QA_APP_SRC=$PWD /home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session calc-fix start [--dark --large-font]
- Same ui.py prefix: key ctrl+o; key ctrl+l; type /home/ali/.t3/qa-env/src/sample_projects/continuous.rcms; key Return; click first row header. Screenshots use shot <path>; stop after session.

## Observations and limitations

Strict typing passed; 33 targeted GUI tests passed. Earlier layout failures asserted intentionally removed Stretch and stale preview behavior; updated tests assert readable widths and empty failed pre/post preview. E2E evidence lives under artifacts/verification/rcms and includes exact commands, runtime, saved/reopened data and numerical comparisons.

Light/default: entered SD .00001 in the main grid, committed Tab: F7/after-light-default.png shows 1e-05. Opened calculator: F12/after-light-default.png shows SE1.291e-06, complete Variance header and readable cells. Switched to empty pre/post: F25/after-empty-prepost-light.png shows cleared effect/CI/readout.

Dark/large: F27/after-dark-large.png shows compact SE1.291e-06 and variance1e-10 after leaving the editor; F12/after-dark-large.png deliberately retains the full precision active editor (not a rounded stored value). These sizing captures precede the final tiny change restricting fixed-decimal formatting to computed columns; raw N/mean are more compact in final source. F7/after-dark-large.png was captured before the modal closed and is NOT grid proof.

Not a complete light/dark x default/large before/after matrix: only light/default before reproduction and light/default plus dark/large after sizing were captured. Existing full-size QA frames remain original before evidence. No package/native Windows/macOS qualification or full authority/golden/pre-push run locally; user explicitly reserved pre-push for CI due host overload. No golden numeric/presentation references regenerated. SE compact painting existed already; the long SE string is the exact editor text, intentionally retained. Content column sizing fixes elision of the compact readout.
