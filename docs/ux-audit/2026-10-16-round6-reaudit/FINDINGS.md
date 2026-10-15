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
