# New findings (draft while broad sweep continues)

## R6-01 — Low: BMJ single-arm counts have no column label

Reproduce: create Single-arm proportion with the default unnamed group; enter
six studies with events 4–9 and totals 20–25; select Freeman–Tukey proportion,
random DL and BMJ style; run standard analysis. The same issue is visible in
subgroup analysis. The raw column shows `4 / 20`, `5 / 21`, … and pooled
`39 / 135`, with nothing above it identifying the numerator and denominator.

[Inspected standard native screenshot](screenshots/project-reviewer-predictions-40-0-reviewer-prediction-after.png)
and [BMJ subgroup](screenshots/prediction-remaining-14-0-reviewer-prediction-after.png).
The blank column header also exists in the actual SVG. Default and RevMan keep
Events/Non-events or Events/Total headers when the unnamed spanner is hidden.

Keep the requested hidden unnamed spanner; label this column `Events / Total`.
A meaningful custom group name should be an additional spanner, not the sole
explanation of the data. No estimate, interval or count error was found.

Source corroboration: `rcmetar.bmj.binary.ilab` creates an empty raw column
header; `rcmetar.draw.bmj.headers` adds `No of events / total` only for two arms.
The empty subheader predates round six; removing the meaningless Group spanner
makes the remaining blank particularly visible. This is a newly identified
presentation gap, not evidence of changed statistics. It need not block merge.

## R6-02 — Low: About opens as an unnecessarily narrow scrolling panel

Reproduce: Help → About and Legal at ordinary native scaling on this 1600×860
Linux desktop. The initial dialog is 278×246 pixels. Its issue URL wraps across
lines and warranty/provenance information lies below the fold despite abundant
screen space. [Inspected full-size capture](screenshots/project-reviewer-groups-148-0-reviewer-about-version.png).

Use a screen-bounded preferred width/height that exposes this short information
page comfortably, retaining scrolling for smaller screens. The title correctly
shows 0.5.0, the Close control is visible and no information is inaccessible.
This is existing polish debt (the round-five shell-about.png has the same
278×246 dimensions), not a release identity failure or merge blocker.

## R6-03 — Medium / merge blocker: long RevMan arm header crosses the caption and device edge

Reproduce: create two-arm proportions, name the arms `Intensive individualized
cognitive behavioural therapy plus structured clinical follow-up` and `Standard
clinical care`; enter events/totals 4–9/20–25 versus 6–11/22–27; run random DL OR
at six digits with RevMan style and the default caption. The first arm wraps
upward through the caption and above the figure boundary.
[Full native screenshot](screenshots/project-round6-polish-180-0-measured-wrapped-arm-headers.png).

This is also present in `workflow/headers-revman-89.svg`, not merely a viewport
crop. [Retained actual exported SVG](exports/R6-03-revman-long-arm.svg) and [exact artifact hashes/nodes](R6-03.json) show the first arm baseline
at y=1.95 with 12.96-pixel type (measured top −8.418); `cognitive` at y=30.05
crosses the caption at y=28.80. The final `follow-up` word is absent from the arm
header nodes although the full name remains in the caption. Estimates/intervals
are unchanged. Default/BMJ cases in the same drive do not show this collision.

Reserve actual top device/caption clearance for the entire wrapped block. Keep
all words, readable type and the repaired rule/data clearance. Verify full native
figure and actual exports, including the device top and caption. The current
passing header assertions only check inter-column/rule clearance, so their exit
zero is not visual acceptance. R5-06 is improved rather than fully fixed. This
publication-output defect should be repaired before merging the 0.5.0 candidate;
no product change is made by this audit.

## R6-04 — Low: fitted log-proportion axes expose excessive tick precision in journal styles

Reproduce: Single-arm proportion → log-transformed proportion (PLN), RevMan or
BMJ; run, Edit plot → Effect axis scale → Fitted transformation → OK, reopen.
The natural default is clear. The optional fitted log axis uses ticks such as
−2.995732, −1.609438 and −0.6931472, whereas Default chooses short round fitted
values. [RevMan](screenshots/project-axis-proportions-163-0-axis-option-reopened.png)
and [BMJ](screenshots/project-axis-proportions-178-0-axis-option-reopened.png).

Choose a small set of round values on the currently displayed fitted scale and
position those exact values, without rounding positions independently of labels.
The labels are mathematically valid and legible; this is consistency/precision
polish, not a numerical error or merge blocker. Natural default axes are unaffected.

## R6-05 — Low: extreme legal numeric inputs overflow journal forest columns

Reproduce: open the bundled IRR project; edit the first study through its row
calculator using Events/person-time: intervention events `1e6`, intervention time
`1.2345678901234567e-8`, control events `5`, control time `1e12`; Accept, Save,
reopen and run the six-digit RevMan random-effects analysis.
[Actual post-reopen figure](screenshots/calculator-ratio-precision-13-0-ratio-precision-reopened-fit.png)
shows the first raw-data/estimate row and total row running across adjacent
columns. The persistence/public-fit assertions pass; this is a display failure.

Use compact scientific notation and measured clearance for very small/large raw
values, totals, interval bounds and ticks, without changing full-precision editable
or stored data. The reported-ratio precision fixture also illustrates a positive
very small CI bound displayed as `0.000000`; scientific notation would retain its
meaning. These are intentionally extreme stress inputs, not an ordinary clinical
sample or evidence of incorrect fitted values. Record as robustness/finishing
debt rather than an additional merge blocker.
