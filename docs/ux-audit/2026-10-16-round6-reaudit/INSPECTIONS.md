# Independent image inspection journal

Only frames listed here have been visually inspected by this audit. Inspection
sheets are derived thumbnails; cited originals are retained unchanged with hashes
in SELECTED-*.json. Full-size follow-up is required where thumbnail text is unclear.

- project-reviewer-predictions sheets 00–01 (first eight frames, steps 13–53):
  PFT Default/RevMan/BMJ and PLO Default. Figures show 0–1 linear natural axes;
  Default study intervals/summary blue, black labels; no unnamed Group spanner.
  PFT PI 0.211–0.370 agrees in the displayed table and footer. PLO PI
  0.221–0.375 agrees. Plot navigator and visible figure agree after Tables.
- project-reviewer-predictions sheets 02–07 (all 30 captured selected frames):
  remaining PLO/PAS three-style figures and Tables, PFT cumulative/omission all
  three styles, Default/RevMan subgroup upper/lower views and PI Tables reviewed.
  Natural-axis geometry and PI rows are coherent. Sequential screenshots at Fit
  width need vertical scrolling; clipped viewport footers are not clipped exports.
  Subgroup-specific PIs differ appropriately (B .167–.389; A .197–.420).

## Interruption and audit-driver failure

The deliberate interruption killed the outer queue/recorder, leaving only owned
PID 1726488. Its /proc command line identified the prediction child; SIGTERM was
sent only to that PID. Seventeen complete cases are retained, not rerun. The final
BMJ subgroup case runs separately. The first resume wrapper failed before app
startup because audit `inspect.py` shadowed Python's standard `inspect` module.
Renamed it `inspect_frames.py`; the exact failed traceback remains in raw/. This
is an audit harness failure, not a product defect.
- prediction-remaining sheet 00 and full-size original standard BMJ step 40:
  all three final BMJ subgroup frames reviewed. Actual figure selected after
  Tables; PI table/upper/lower figures agree. No unnamed spanner. One newly
  identified low-severity gap: the BMJ n/N raw-data column has no semantic label
  (R6-01). No numerical discrepancy found.
- Resume's second audit harness attempt lacked the new recorder's global window
  binding. Doctor had already written runtime.json, then its record callback
  raised and the production exception hook displayed a modal. Stopped only owned
  child PID 1729942, added the recorder namespace binding to reused audit scripts,
  and disabled the product exception hook in those drivers. Final remaining-case
  replay passed in 23.96 seconds. All failed/interrupted receipts remain raw.
- project-reviewer-groups sheets 00–03, all 15 selected frames, plus full-size
  About: unnamed/custom single-arm proportion and mean in three styles; custom
  Participants retained (mean via caption); old-key Plots tab visibly says Default;
  About visibly says 0.5.0; reopened project grid and application.version assertion
  agree. Mean fixture is entered-effect and has no raw-data spanner. About is
  unnecessarily narrow (R6-02); its version and Close control are correct.
- project-reviewer-colours sheets 00–05, all 21 selected frames: standard,
  cumulative, omission, subgroup, PFT, mean, diagnostic Sens/Spec, HR and IRR
  Default figures/editors plus actual clipped-arrow view reviewed. Blue intervals,
  caps/markers/arrows and diamonds agree; study text remains black. Defaults show
  log spacing/natural labels for ratios and linear natural units for proportions
  and diagnostics. All four export formats pass retained decoder/colour checks.
- project-round6-polish initial sheets 00–01 (seven frames through step 63):
  continuous/factor/multiple diagnostic reports at two/six digits and cumulative
  DOR report. Logit/OR CI headings and fitted SE scale are explicit. Multiple
  moderators require scrolling; dedicated Tables capture review follows.
- project-round6-polish completed sheets 00–08, all 33 selected frames: twelve
  actual coefficient Tables (Sens/Spec × numeric/factor/multiple × two/six digits),
  six report overviews, cumulative/subgroup DOR reports, four inline invalid
  contour states and nine three-style short/unequal/long arm-name figures reviewed.
  Coefficient headers distinguish logit and OR; values fit the native Tables.
  Long multiline headers clear rules and data, but full-size review rejects the longest RevMan case: its arm header crosses the caption/device top (R6-03). Contour errors preserve editable
  input, show a useful local reason and leave OK usable. Copy/CSV equality and
  independent raw coefficient comparisons passed. The initial thumbnail-level acceptance of all headers is superseded by the full-size R6-03 inspection; this is a product output defect despite the passing driver.
