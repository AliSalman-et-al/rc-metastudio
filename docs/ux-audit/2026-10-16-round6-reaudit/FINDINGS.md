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

## R6-02 — Low: About and reconstruction prompts open needlessly small

Reproduce: Help → About and Legal at ordinary native scaling on this 1600×860
Linux desktop. The initial dialog is 278×246 pixels. Its issue URL wraps across
lines and warranty/provenance information lies below the fold despite abundant
screen space. [Inspected full-size capture](screenshots/project-reviewer-groups-148-0-reviewer-about-version.png).

Use a screen-bounded preferred width/height that exposes this short information
page comfortably, retaining scrolling for smaller screens. The title correctly
shows 0.5.0, the Close control is visible and no information is inaccessible.

The same initial-sizing problem affects reconstruction decisions. Reproduce in
the continuous row calculator: clear inputs, select MD, set Intervention N=20,
mean=10, SD=2; Control N=20, mean blank, SD=2; estimate=2 and 95% CI approximately
[0.76041, 3.23959], then Reconstruct group data. The relationship-of-SDs prompt
opens only 190×222 pixels and hides much of its question/options behind a
scrollbar. [Continuous prompt](screenshots/calculator-mode-back-continuous-02-0-back-calculation-nested-cancel.png).
The binary alternative-count decision also hides choices in its initial short
viewport: clear inputs, totals=100 per arm, OR=2.111111111111111 and CI
[0.6946538052093257, 6.415843557405645], then Reconstruct group data.
[Binary prompt](screenshots/calculator-mode-back-binary-02-0-back-calculation-nested-cancel.png).
Cancel remains visible and preserves calculator state. Give these short decision
prompts enough initial space to show the question and alternatives. This is
workflow/reading friction, not another numerical or persistence defect.

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

## R6-06 — Medium / merge blocker: automatic arm headings truncate a valid investigator name

Reproduce the long-name case in R6-03. The [wizard accepts the full name](screenshots/R6-06-171-0-round5-arm-wizard.png), including `follow-up`. Run without editing plot labels. The auto-generated arm heading ends at `clinical` in Default, RevMan and BMJ; the full name remains in the dataset and caption. [Native plot](screenshots/project-round6-polish-180-0-measured-wrapped-arm-headers.png), [exact entered/generated values](R6-06.json).

The native recorded name is 89 characters; `fp_col3_str` is only the first 80
characters, ending in a space. Setup applies an 80-character plot-only limit and
loads generated group names with `setText`; that loses the tail before plotting.
The existing lossless untouched-label path is not used for this generated name.
This is not corruption of the study dataset, but an investigator label is automatically
shortened in the resulting figure without inline notice. The editor tooltip does
state that plot labels are limited to 80 characters; this is a disclosed plot
limit, not an undisclosed storage defect. It does not tell the researcher that
the generated heading already lost the accepted name tail. Two names differing only after character 80
could become indistinguishable headings.

Preserve generated names losslessly, or require an explicit abbreviated heading
with visible feedback. The release-gate judgement is about faithful automatic investigator identity on
the accepted long-name path, despite the generic tooltip. Repair this alongside R6-03 and remeasure the full-name
block: simply making room for the already-truncated block is insufficient. No
wrong estimate is established. This is a second release gate on the same accepted long-name path: both faithful heading text and device/caption clearance must pass. The code path predates round six, so it is
not counted as a confirmed new regression.


## R6-07 — Low: dedicated diagnostic odds-ratio coefficient plots retain a separate linear convention

Reproduce: create Diagnostic studies with TP=19…24, FN=10…15, FP=1,
TN=81…86 and numeric covariate Dose=1…6; run Reitsma meta-regression with
Dose, Default style and six digits. Choose Specificity Moderator Coefficients.
The natural OR ticks 0.6, 0.7, 0.8, 0.9 and 1 are equally spaced. Edit plot
has bounds/ticks but no Effect axis scale chooser.
[Inspected native figure](screenshots/matrix-diagnostic-meta-regression-figure-1-bottom.png),
[editor](screenshots/plot-workflow-coefficient-08-0-family-editor-controls.png),
[actual retained display SVG and measured ticks](R6-07.json).

This is a legitimate linear ratio display: values/intervals are unchanged, and
the round-six plan explicitly keeps coefficient axes linear. It is an exception
to the otherwise consistent ratio-forest/bubble default, not a confirmed new
regression or an incorrect analysis. Consider using log spacing with natural OR
labels for exponentiated diagnostic coefficients and exposing the same opt-in
linear control; retain ordinary beta/logit coefficient coordinates as linear.
Make the specialized convention explicit if retained. This need not block merge.


## R6-08 — Low: HR/IRR exponentiated coefficient tables still expose `intrcpt`

Reproduce: open Pignon2000-HR or NielWeise2008-IRR; add numeric covariate Dose
with sequential values 1…k, then meta-regress on Dose using random effects/REML
and six digits. The primary coefficient table says Intercept, but the
Exponentiated coefficients table says `intrcpt` for its baseline multiplier.
The report itself explains that the intercept is the baseline ratio, so the
remaining internal token is unnecessary and inconsistent.

The two original custom Default matrix receipts fail at the real visible-label
assertion: `raw/matrix-hr.log` and `raw/matrix-irr.log`. Four earlier workflow
cells completed in each run and were retained. Confirmed native views: [HR](screenshots/matrix-hr-meta-regression-report-exponentiated--wording-recovery.png), [IRR](screenshots/matrix-irr-meta-regression-report-exponentiated--wording-recovery.png). Actual exported text contains intrcpt at line 25 in both raw/matrix-hr--wording-recovery/round3-report.txt and raw/matrix-irr--wording-recovery/round3-report.txt; report copy/export equality is asserted in the receipts.
The maintained 122-scenario registry still has no failed helper; this is a newly
exercised report branch in the additional matrix.

Use the same readable Intercept mapping in this secondary table and preserve
all fitted values/precision. This is wording debt, not an incorrect multiplier
or an additional merge blocker. R5-05 is improved rather than fixed. Later audit
continuations narrowly permit this known token at recording time, label that
exception R6-08, and retain the original failed receipts; they do not count the
wording as repaired or relax any statistical assertion.
