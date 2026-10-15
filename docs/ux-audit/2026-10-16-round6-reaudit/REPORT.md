# RC MetaStudio v0.5.0 — independent round-six native re-audit

**IN PROGRESS. Current confirmed merge blockers: R6-03 and R6-06.** The longest supported RevMan arm name overlaps the caption and crosses the figure-device top in native and exported SVG output. Automatic arm headings also shorten a valid 89-character investigator name to 80 characters. Numerical results are unchanged. These are publication-output defects, not failed statistical fits.

Round six is substantially better at preserving input, identifying scales and presenting results. PFT prediction limits use the natural proportion scale; Default intervals/markers/caps/arrows match the summary blue while study names remain black; internal metric labels and the retired Default suffix are removed on inspected paths. About and new saved-project metadata show 0.5.0. The remaining release concerns are publication layout and faithful generated heading text; the repaired calculator path is separate.

This audit started at **b48c802**, branch **ux/audit-improvements**. Only audit artifacts/scripts changed. Actual host/run timestamps are 15 October UTC (continuations may be later); the folder date follows the requested 16 October naming. All native drives use DISPLAY=:0/xcb, pinned R 4.6.1 and the test-owned retained library. [Provenance](PROVENANCE.json) checks all 80 RCMetaR source/install hashes. No system R library was changed.

Across **100 prior IDs: 14 fixed, 22 improved, 64 unchanged, 0 confirmed regressions**. This includes the 99 round-five IDs plus historical F16, accidentally omitted from that scorecard and restored here. Unchanged includes retained fixes and qualification gaps; improved does not imply universal closure. [Scorecard](SCORECARD.json).

## Evidence and scope

[Exact command/exit/environment/log and manifest inventory](OUTCOMES.json),
[replay](REPLAY.md), [image inspection journal](INSPECTIONS.md),
[contact sheet](contact-sheet.html) and SELECTED-*.json bind the evidence.
Raw transcripts/owned inputs remain in ignored raw/ and under the helper's printed
artifacts/verification/rcms directory. A passing driver is not visual acceptance:
R6-03 was found in a driver that passes its narrower geometry assertions.

The independent authority sweep passes **91/91**. Strict golden replay passes;
all **415 original fields are exact**, maximum difference zero, with original
numerical contracts/tolerances/exceptions unchanged.
[Authorities](AUTHORITIES.json), [exact field comparison](NUMERICAL-EQUIVALENCE.json), [18-case prediction recovery](PREDICTION-RECOVERY.json).

Linux source/native Qt proof does not qualify packaged Windows/macOS targets,
actual OS DPI, screen readers, every filesystem/dialect fault or an arbitrary
parameter/value Cartesian product. Control/choice inventories are distinguished
from executing every possible choice combination. Four-format export decoding
is distinguished from inspecting every exported pixel.

## Round-six acceptance review

| Area | Observation / evidence |
|---|---|
| Axes | Ratio log spacing/natural labels with opt-in linear; proportion and Sens/Spec natural 0–1; differences linear. Optional fitted transformations name their scale. Fresh geometry, exact fits/weights and persistence checks are in project-axis-* receipts/selected images; Apply has an additional targeted audit drive. |
| PFT PI | All three styles, standard/cumulative/omission/subgroup, Text/Tables/copy/export; public inverse agreement and subgroup-specific N. Seventeen pre-interruption completed cases retained, only missing BMJ subgroup replayed. |
| Default colours/style | Native project-reviewer-colours passes nine families/components and actual clipped arrows, four-format exports, black labels. Group/release drive visibly opens old-key Plots tab showing Default. |
| Groups/version | Unnamed spanners hidden; meaningful Participants preserved. Mean entered-effect fixture carries identity in caption and has no raw-data spanner. About and saved/reopened application.version show 0.5.0. |
| Diagnostic output | Numeric/factor/multiple moderators at two/six digits, explicit logit/OR CI headers, actual Tables/copy/CSV agreement; public coefficients unchanged. |
| Long headers | Default/BMJ improve, but longest RevMan case fails full-device/caption clearance (R6-03). R5-06 remains improved. |
| Calculator data | Fresh maintained keyboard, raw/entered/reconstructed mode, grid/import/clipboard, undo/save/reopen and post-reopen authority checks; final status requires completed registry listed in OUTCOMES. |
| Legends/contours | Actual component visibility governs legend samples. Invalid contour inputs show inline errors, stop progress and retain editable/recoverable state. |

## New findings

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


## Every prior ID

Status is comparative to round five (F16 restored from round four). Detailed scope is bounded by the evidence map above and the inspection journal.

| ID | Status | Observation | Evidence |
|---|---|---|---|
| L01 | **unchanged** | Type tiles remain readable; no step indicator and field-page scrolling remain. | [Native wizard/import/help/validation inventory](DESIGN.json) |
| L02 | **unchanged** | Pristine Untitled dataset and no welcome modal retained. | [Native wizard/import/help/validation inventory](DESIGN.json) |
| L03 | **unchanged** | Canonical CSV/template headers use actual arm names and readable field names. | [Native wizard/import/help/validation inventory](DESIGN.json) |
| L04 | **unchanged** | Entered-effect identity now travels in editable standalone context; dedicated units remain absent. | [Native wizard/import/help/validation inventory](DESIGN.json) |
| L05 | **unchanged** | Required outcome and optional meaningful arm-name fields improve the final naming step. | [Native wizard/import/help/validation inventory](DESIGN.json) |
| L06 | **unchanged** | Integer count preview and named headers improve import; all dialect/filesystem faults unqualified. | [Native wizard/import/help/validation inventory](DESIGN.json) |
| G01 | **unchanged** | Linux grid is readable; old persisted Windows width trigger remains unqualified. | [Actual input edits and save/reopen](SELECTED-calculator-grid-precision.json) |
| G02 | **improved** | Built-in TX Mean/menu identity repaired in ten-family label sweep; investigator names preserved. General terminology polish remains. | [Ten-family live labels and selectors](SELECTED-project-display-labels.json) |
| G03 | **unchanged** | Calculator glyphs and italic derived values add non-colour cues; assistive-tech qualification remains open. | [Actual input edits and save/reopen](SELECTED-calculator-grid-precision.json) |
| G04 | **unchanged** | Named navigation retained and metadata spacing now reads Follow-up: first consistently. | [Workspace navigation and structure dialogs](SHELL.json) |
| G05 | **unchanged** | Intervention/Control defaults, optional wizard names and preserved investigator/legacy names retained. | [Workspace navigation and structure dialogs](SHELL.json) |
| G06 | **unchanged** | Readable diagnostic input/CI fields retained; exact leading zeros visible in fresh native edit preview. | [Actual input edits and save/reopen](SELECTED-calculator-grid-precision.json) |
| G07 | **improved** | Calculator exact entry/provenance and live derived summaries repaired; dense layouts remain. | [Actual input edits and save/reopen](SELECTED-calculator-grid-precision.json) |
| G08 | **unchanged** | Numeric/Category wording and separated destructive actions retained. | [Workspace navigation and structure dialogs](SHELL.json) |
| M01 | **unchanged** | A labelled Analyses group gives analysis actions one recognition rule; minor case remnants persist. | [Opened native menus and recovery/eligibility](SHELL.json) |
| M02 | **unchanged** | Missing recent files expose Locate/Remove and recover to real project entries. | [Opened native menus and recovery/eligibility](SHELL.json) |
| M03 | **unchanged** | Actual disabled subgroup prerequisite tooltip works within the labelled analysis menu. | [Opened native menus and recovery/eligibility](SHELL.json) |
| M04 | **unchanged** | Structure tabs remain a dense three-pane editor; actual arm names are readable. | [Workspace navigation and structure dialogs](SHELL.json) |
| S01 | **unchanged** | Separate report/figure zoom and scoped confidence controls retained. | [Result navigation/zoom and dialog sizing](DESIGN.json) |
| D01 | **unchanged** | Content-sized cards, named controls and Locate/Remove recovery retained; current 1×/1.5×/2× application-scale proof is separate from historical 1.25× evidence and actual OS-DPI qualification. | [Result navigation/zoom and dialog sizing](DESIGN.json) |
| D02 | **improved** | Contextual metric labels improved; some general method-family descriptions still need translation. | [Ten-family live labels and selectors](SELECTED-project-display-labels.json) |
| D03 | **unchanged** | Editable context and actual group headings improve setup/editing; hex colour fields and long forms remain. | [Actual unnamed/named arms and reopened context](SELECTED-project-reviewer-groups.json) |
| D04 | **fixed** | Invalid contour input is inline, stops busy state, stays editable and recovers to real output. | [Eligibility and invalid-contour recovery](SELECTED-project-round6-polish.json) |
| D05 | **unchanged** | Existing corrections and eligibility retained; universal affected-study accounting remains incomplete. | [Eligibility and invalid-contour recovery](SELECTED-project-round6-polish.json) |
| R01 | **improved** | Readable package-owned labels and reduced duplicate identity; remaining report hierarchy is coherent. | [Live report overview and structured tables](SELECTED-project-round6-polish.json) |
| R02 | **unchanged** | Existing outcome/comparison/follow-up identity is in editable standalone captions; IRR exposure is explicit. | [Actual unnamed/named arms and reopened context](SELECTED-project-reviewer-groups.json) |
| R03 | **improved** | Long-figure caps and wrapped arm headers repaired; long outputs still require deliberate zoom/scroll. | [Dense 65-study upper/lower figures in all styles](SELECTED-audit-round3-round5.json) |
| R04 | **unchanged** | Previously fixed sequential reference bounds retained on inspected paths. | [Sequential reference/scale paths](SELECTED-project-axis-sequential.json) |
| R05 | **unchanged** | Original coefficient Fixture 2 lower bound remains zero; tiny-effect protection retained. | [Sequential reference/scale paths](SELECTED-project-axis-sequential.json) |
| R06 | **unchanged** | Study added (k) and sequence/display-order guidance retained. | [HR cumulative and omission identities](MATRIX-hr.json) |
| R07 | **unchanged** | HR/IRR omitted-study identity and visible row intervals remain aligned. | [HR cumulative and omission identities](MATRIX-hr.json) |
| R08 | **fixed** | Structured subgroup results now identify fitted SE scales alongside natural-scale effects. | [Sequential/subgroup clinical and fitted scales](SELECTED-project-reviewer-predictions.json) |
| R09 | **fixed** | Bubble legend entries/samples follow visible regression/CI/PI components; panel-bounded guides retained. | [Metric-specific bubbles and guide bounds](SELECTED-audit-round3-bubble-metrics.json) |
| R10 | **unchanged** | Single-arm proportion's actual tested null remains explicit. | [Single-arm natural-scale null/interval presentation](SELECTED-project-reviewer-predictions.json) |
| R11 | **unchanged** | Mean caption carries investigator context and can state units; no dedicated unit field. | [Actual unnamed/named arms and reopened context](SELECTED-project-reviewer-groups.json) |
| R12 | **improved** | Duplicate default metric/type captions removed; investigator context retained. | [Live report overview and structured tables](SELECTED-project-round6-polish.json) |
| R13 | **unchanged** | Actual arm names clarify comparative interpretation without invented clinical conclusions. | [Actual unnamed/named arms and reopened context](SELECTED-project-reviewer-groups.json) |
| R14 | **unchanged** | MD/SMD subtraction explicitly names Intervention minus Control; existing scale guidance retained. | [Actual unnamed/named arms and reopened context](SELECTED-project-reviewer-groups.json) |
| R15 | **improved** | Diagnostic coefficient precision and readable logit/OR interval headings finish the shared table surfaces. | [Diagnostic coefficients at two/six digits; Tables/copy/CSV](SELECTED-project-round6-polish.json) |
| R16 | **improved** | Reference/moderator identities retained with selected precision and readable coefficient headings. | [Diagnostic coefficients at two/six digits; Tables/copy/CSV](SELECTED-project-round6-polish.json) |
| R17 | **fixed** | Dense Default/subgroup CI caps now follow row spacing; prior long-forest regression closed. | [Dense 65-study upper/lower figures in all styles](SELECTED-audit-round3-round5.json) |
| R18 | **unchanged** | IRR actual arms, catheter-day exposure, raw columns and independently checked totals are explicit. | [IRR raw exposure, totals and subgroup identities](MATRIX-irr.json) |
| R19 | **unchanged** | Existing small-study cautions/eligibility retained; corrected contour recovery is tracked under D04/R5-07. | [Eligibility and invalid-contour recovery](SELECTED-project-round6-polish.json) |
| E01 | **improved** | Exports preserve axes, colours and semantic legends; the long RevMan header/caption defect R6-03 limits layout acceptance. | [Retained actual vectors and long-heading defects](EXPORT-EVIDENCE.json) |
| E02 | **improved** | Raw calculator/grid input integrity repaired through undo and save/reopen; existing dirty guards retained. | [Actual input edits and save/reopen](SELECTED-calculator-grid-precision.json) |
| H01 | **unchanged** | Quick start explains naming, existing legacy names, row calculators and output tools. | [Native wizard/import/help/validation inventory](DESIGN.json) |
| X01 | **unchanged** | Blank/duplicate validation remains recoverable; arm duplicates now have explicit inline feedback. | [Native wizard/import/help/validation inventory](DESIGN.json) |
| X02 | **unchanged** | Local covariate empty-state guidance remains; broader contextual workflow help is modest. | [Covariate and analysis setup empty-state controls](OPTIONS.json) |
| A01 | **unchanged** | Named controls and selectable tables improve access; no screen-reader qualification. | [Named controls, contrast samples; bounded accessibility scope](DESIGN.json) |
| A02 | **improved** | Sampled normal/selection contrast and non-colour cues; universal high-contrast qualification remains open. | [Named controls, contrast samples; bounded accessibility scope](DESIGN.json) |
| A03 | **improved** | Readable growing figures retain bounded caps; actual OS scaling/platform limits remain. | [Result navigation/zoom and dialog sizing](DESIGN.json) |
| A04 | **unchanged** | Consistent labelled Analyses group replaces the mixed labelled/icon-only analysis toolbar. | [Opened native menus and recovery/eligibility](SHELL.json) |
| A05 | **unchanged** | Actual Tab/arrow/Escape paths run for workspace/setup/results; full no-mouse and assistive-tech scope remains open. | [Loaded-project keyboard/report/dirty-guard task](GUARD-KEYBOARD.json) |
| RG01 | **improved** | Diagnostic overview and coefficient tables have readable selected-precision clinical/fitted scale identity. | [Live report overview and structured tables](SELECTED-project-round6-polish.json) |
| RG02 | **unchanged** | Independent report/figure zoom retained; Fit width remains figure-scoped. | [Result navigation/zoom and dialog sizing](DESIGN.json) |
| RG03 | **unchanged** | Diagnostic shared notes precede components and executed-method identity remains intact. | [Live report overview and structured tables](SELECTED-project-round6-polish.json) |
| RG04 | **unchanged** | CSV guidance stays outside the scrolling field area. | [Native wizard/import/help/validation inventory](DESIGN.json) |
| N01 | **unchanged** | Prior contextual BMJ coefficient identity is retained at six digits; new long-name header defect is separate. | [Retained actual vectors and long-heading defects](EXPORT-EVIDENCE.json) |
| N02 | **improved** | Diagnostic moderator tables now honour precision and label logit/OR intervals; arbitrary long labels remain unqualified. | [Diagnostic coefficients at two/six digits; Tables/copy/CSV](SELECTED-project-round6-polish.json) |
| N03 | **unchanged** | Previously bounded sequential guides/round ticks now joined by clipped bubble guides on inspected paths. | [Sequential reference/scale paths](SELECTED-project-axis-sequential.json) |
| N04 | **fixed** | Subgroup structured report retains tests and explicitly identifies SE scale. | [Sequential/subgroup clinical and fitted scales](SELECTED-project-reviewer-predictions.json) |
| N05 | **unchanged** | Existing subgroup-difference tests are present in figures and reports. | [Sequential/subgroup clinical and fitted scales](SELECTED-project-reviewer-predictions.json) |
| N06 | **unchanged** | Report identity and tab-separated export rows remain intact. | [Maintained report/Tables copy/export assertions and manifest paths](OUTCOMES.json) |
| N07 | **unchanged** | HR/IRR cumulative/omission study labels and intervals remain correct on inspected rows. | [HR cumulative and omission identities](MATRIX-hr.json) |
| N08 | **improved** | Calculator exact input, derived preview and persistence improve; historical Windows-width trigger remains unqualified. | [Actual input edits and save/reopen](SELECTED-calculator-grid-precision.json) |
| N09 | **unchanged** | Existing named dimension navigation gains consistent metadata spacing. | [Workspace navigation and structure dialogs](SHELL.json) |
| N10 | **improved** | Built-in internal menu/report vocabulary repaired; minor case/method-family wording remains. | [Ten-family live labels and selectors](SELECTED-project-display-labels.json) |
| N11 | **improved** | Round-trip-safe editors preserve data precision; the ordinary diagnostic form still needs horizontal scrolling and long fields remain a visibility gap. | [Actual input edits and save/reopen](SELECTED-calculator-grid-precision.json) |
| R2-01 | **unchanged** | Previously repaired HR/IRR omission identities remain correct. | [HR cumulative and omission identities](MATRIX-hr.json) |
| R2-02 | **unchanged** | Copy/export retains executed identity and matches saved bytes. | [Maintained report/Tables copy/export assertions and manifest paths](OUTCOMES.json) |
| R2-03 | **unchanged** | Structured table exports remain tab-separated, not one-cell-per-line text. | [Maintained report/Tables copy/export assertions and manifest paths](OUTCOMES.json) |
| F01 | **unchanged** | Fixed-model inactive tau-squared omission retained; fresh fixed-IV figure/report agree on estimate, CI and heterogeneity. | [Fixed/clinical-null authority and rendered presentation scenarios](OUTCOMES.json) |
| F02 | **unchanged** | Applicable executed methods and fitted references retained. | [Fixed/clinical-null authority and rendered presentation scenarios](OUTCOMES.json) |
| F03 | **unchanged** | HR/IRR subgroup tables now remove legacy prose while retaining tests and prediction intervals. | [Sequential/subgroup clinical and fitted scales](SELECTED-project-reviewer-predictions.json) |
| F04 | **improved** | Diagnostic selected precision and tiny numeric entry repaired while retaining genuine small effects; no universal formatting claim. | [Diagnostic coefficients at two/six digits; Tables/copy/CSV](SELECTED-project-round6-polish.json) |
| F05 | **unchanged** | Prior comparative test and named actual-null presentation retained. | [Fixed/clinical-null authority and rendered presentation scenarios](OUTCOMES.json) |
| F06 | **improved** | Raw precision/provenance and live derived summaries repaired; calculator layout remains dense. | [Actual input edits and save/reopen](SELECTED-calculator-grid-precision.json) |
| F07 | **improved** | Readable internal labels and Default style name repaired; case consistency and action-labelled dirty prompts remain polish. | [Ten-family live labels and selectors](SELECTED-project-display-labels.json) |
| F08 | **unchanged** | Prior BMJ coefficient/entered-effect identity retained at six digits; three-style presentation/export sweeps passed. | [Retained actual vectors and long-heading defects](EXPORT-EVIDENCE.json) |
| F09 | **unchanged** | Short-label annotation clearance retained; former BMJ long-name layout improved. RevMan collision/truncation remain R6-03/R6-06. | [Retained actual vectors and long-heading defects](EXPORT-EVIDENCE.json) |
| F10 | **unchanged** | IRR duplicate-author subgroup rows retain distinct identities and overall weights. | [IRR raw exposure, totals and subgroup identities](MATRIX-irr.json) |
| R3-01 | **unchanged** | Sequential null guide stays within study rows clear of the footer. | [Sequential reference/scale paths](SELECTED-project-axis-sequential.json) |
| R3-02 | **unchanged** | Round linear bubble ticks and title clearance remain readable. | [Metric-specific bubbles and guide bounds](SELECTED-audit-round3-bubble-metrics.json) |
| F11 | **unchanged** | Exterior bubble guide removed; fresh 18-case metric/explicit-bound geometry sweep passed; decoded editor exports are separately recorded. | [Metric-specific bubbles and guide bounds](SELECTED-audit-round3-bubble-metrics.json) |
| F12 | **unchanged** | Legacy scene weights removed; report/Tables retain structured rows and existing component identities. | [Structured results navigation and component identities](DESIGN.json) |
| F13 | **unchanged** | Content-sized cards, named controls and Locate/Remove recovery retained; current 1×/1.5×/2× application-scale proof is separate from historical 1.25× evidence and actual OS-DPI qualification. | [Opened native menus and recovery/eligibility](SHELL.json) |
| F14 | **unchanged** | Labelled Analyses group and actual prerequisite tooltip. | [Opened native menus and recovery/eligibility](SHELL.json) |
| F15 | **unchanged** | Navigator/results label/value spacing is consistent. | [Workspace navigation and structure dialogs](SHELL.json) |
| R5-01 | **fixed** | Sequential/subgroup SE headings explicitly identify fitted scale; funnel SE axes do likewise. | [Sequential/subgroup clinical and fitted scales](SELECTED-project-reviewer-predictions.json) |
| R5-02 | **improved** | Identical type/metric captions and Group: Group context removed; generated Follow-up: first still exposes the container default, so copy finishing remains partial. | [Live report overview and structured tables](SELECTED-project-round6-polish.json) |
| R5-03 | **fixed** | Diagnostic coefficients/ML tests honour two/six digits; logit/OR bounds explicit across Text/Tables/copy/export. | [Diagnostic coefficients at two/six digits; Tables/copy/CSV](SELECTED-project-round6-polish.json) |
| R5-04 | **fixed** | Long standard/subgroup CI caps bounded by row spacing in all three styles. | [Dense 65-study upper/lower figures in all styles](SELECTED-audit-round3-round5.json) |
| R5-05 | **fixed** | Package-owned Intercept/Moderator/Statistic labels are readable; internal keys remain internal. | [Diagnostic coefficients at two/six digits; Tables/copy/CSV](SELECTED-project-round6-polish.json) |
| R5-06 | **improved** | BMJ measured unequal wrapped headers improve; longest RevMan header overlaps caption/device top (R6-03), so not fully closed. | [Retained actual vectors and long-heading defects](EXPORT-EVIDENCE.json) |
| R5-07 | **fixed** | Eligibility explains usable study count and invalid contours recover inline without stuck progress. | [Eligibility and invalid-contour recovery](SELECTED-project-round6-polish.json) |
| R5-08 | **fixed** | Subgroup setup/editor explicitly explain shared layout with journal accents. | [Subgroup setup/editor shared-layout wording](OPTIONS.json) |
| R5-09 | **fixed** | Attached menus/calculators/reports use contextual readable metrics; no built-in TX Mean prefix. | [Ten-family live labels and selectors](SELECTED-project-display-labels.json) |
| R5-10 | **fixed** | Tiny/huge/decimal/exponent input survives real editing, Accept, undo/save/reopen and independent post-reopen fit. | [Exact HR/IRR modes and post-reopen authority fit](SELECTED-calculator-ratio-precision.json) |
| R5-11 | **fixed** | Legend entries and samples follow actual regression/CI/PI visibility in display/export. | [Metric-specific bubbles and guide bounds](SELECTED-audit-round3-bubble-metrics.json) |
| F16 | **unchanged** | Historical report-hierarchy finding omitted from the round-five scorecard, restored here. Calmer hierarchy retained; diagnostic overviews still need scrolling and retain multiple headings. No new round-six closure claimed. | [Live report overview and structured tables](SELECTED-project-round6-polish.json) |

## Changelog and further work

The current 0.5.0 entry accurately describes the observed input/scale/colour/report
improvements. Its broad wrapped-header wording needs the R6-03 qualification;
publication layout is not uniformly finished. The portable Ubuntu download and
TIFF performance statements belong to separate package/benchmark evidence; this
audit does not requalify those claims. Historical version strings in older records
are not current-runtime version defects.

Repair R6-03 and R6-06 together, preserving the full investigator name while measuring its device/caption clearance. Then add the missing semantic BMJ Events/Total heading,
give About a sensible screen-bounded preferred size, and round optional fitted
PLN ticks coherently. Existing opportunities remain: compact calculator layouts,
less package-taxonomy translation, sentence-case/action-labelled prompts,
full from-launch keyboard tasks, actual assistive-technology and OS-scale checks.
No new statistical procedure is needed.

RevMan/Cochrane patterns inform the recommendations: clear distinction between
fitted and reported scales, concise visible footnotes, explicit uncertainty
controls and useful raw-data headings. [Primary references](DESIGN-REFERENCES.md).

## Failures, interruptions and cleanup

The deliberate interruption orphaned one owned prediction child; only its recorded
PID was stopped. Seventeen complete cases survived and were reused. Resume failures
were audit harness import shadowing and a missing recorder namespace binding;
the exact failed/terminated logs remain raw. The final missing-case replay passed.
The numerical helper's output was relocated into this audit and its historical
file restored byte-exact; raw/NUMERICAL-RELOCATION.json records hashes.
No failed receipt is relabelled as passing. Final cleanup and completion counts
must be reconciled against OUTCOMES before acceptance.
