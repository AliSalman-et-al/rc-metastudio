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
crop. [Exact artifact hashes and nodes](R6-03.json) show the first arm baseline
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
