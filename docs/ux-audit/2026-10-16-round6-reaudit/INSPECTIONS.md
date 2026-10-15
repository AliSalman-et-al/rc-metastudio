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
