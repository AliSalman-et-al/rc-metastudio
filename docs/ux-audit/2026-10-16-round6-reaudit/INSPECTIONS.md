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
- project-axis-proportions sheets 00–08, all 36 selected frames: PLO, PAS, PFT
  and PLN × Default/RevMan/BMJ natural defaults, actual editor choices and reopened
  transformed plots. Natural defaults use even 0–1 spacing. Transformed alternatives
  carry explicit logit/arcsine/Freeman–Tukey/log-scale axis titles. Marks, annotations
  and pooled results agree. Retained assertions prove unchanged fits/weights,
  Cancel rollback, persisted export and rerun. Scale-specific Apply gets its own
  additional audit drive because this maintained route clicks OK.
- PLN optional fitted axes in journal styles (steps 163/178): mathematically valid
  but overprecise non-round ticks differ from Default; recorded as R6-04 low.
- Historical-ID reconciliation across every previous REPORT table/heading found
  F16 omitted from the round-five scorecard. It is restored, unchanged, alongside
  the 99 round-five IDs (100 total). No historical ID is silently dropped.
- project-axis-others sheets 00–07, all 30 selected frames: OR log-spaced default
  and opt-in linear; sensitivity/specificity natural 0–1 and opt-in fitted logit;
  MD linear, across three styles. Native editor choices and reopened plots reviewed;
  annotations stay on their clinical scale while axis titles identify fitted
  alternatives. No new defect. Geometry, unchanged fits/weights, Cancel rollback,
  export/rerun persistence passed. Apply-specific replay remains separately queued.
- project-axis-sequential sheet 00, three frames: PFT cumulative, omission and
  subgroup endpoint inverses matched actual public subset fits and harmonic N.
- calculator-grid-precision sheets 00–01, eight frames: tiny/huge/decimal/exponent
  raw grid edits, exact CSV preview/reopen, entered-effect/coefficient reopening.
  Compact painted values are distinct from full editor/model precision.
- calculator-ratio-precision sheets 00–02, ten frames, plus full-size step 13:
  all five HR/IRR source modes, exact input and post-reopen independent fits.
  Stress IRR numeric strings overflow journal output columns (R6-05 low); inputs
  and fitted references remain correct. Ordinary log/SE views remain readable.
- project-display-labels sheets 00–06, all 26 selected frames: ten workspaces and
  actual calculators, six contextual metric popups, diagnostic selector. Mean,
  Regression coefficient and Entered effect are readable; no built-in TX prefix.
  Actual Intervention/Control and clinical ratio arm names remain. Recursive
  attached action/choice/tooltip inventory passes for all ten families and is
  retained in REACHABLE-MENUS.json. Grid screenshots alone are not screenshots of
  expanded menus; the later shell/options drive supplies visible menu captures.
  Continuous calculator whitespace and diagnostic horizontal scrolling remain
  existing G07/F06/N11 layout debt, not closed by naming/input integrity fixes.
- Two actual vector artifacts retained and rendered with current QtSvg offscreen:
  full-size export-R6-03-revman-long-arm.png confirms clipping/caption collision;
  export-R6-01-bmj-single-arm.png confirms the unlabeled raw count column. Both
  derived images inspected individually; they are explicitly not native captures.
  EXPORT-EVIDENCE.json binds original/vector/render hashes. An initial attempt to
  retain the stress IRR vector failed because that step recorded no plots mapping;
  its screenshot remains valid, but no vector/export claim is made for R6-05.
- Full-size native long-name wizard step 171 inspected: entire 89-character name
  fits and includes follow-up. Its actual later properties record carries only
  80 characters in the generated heading. The omission noted under R6-03 has a
  separate setup input-limit cause (R6-06); full dataset/caption names are intact.
- audit-round3-round5 sheets 00–02, twelve native upper/lower standard/subgroup
  65-study HR frames in Default/RevMan/BMJ reviewed. Caps remain inside study
  row bands, type stays readable, subgroup/overall blocks and axis/footer clear.
  Direct cap/diamond-to-row geometry and exported SVG checks pass. This closes
  the observed R5-04/R17 regression on the retained long-figure paths.

### Diagnostic forests and metric-specific bubbles

Viewed `inspect-audit-round3-presentation-diagnostic-00` through `05`: all 24 selected native upper/lower annotation frames, sensitivity and specificity in Default/RevMan/BMJ at three and six digits. Natural 0–1 forest axes, explicit counts and effect/CI columns, bounded caps and matching Default blue remain coherent. Journal six-digit columns fit this ordinary six-study fixture. RevMan's repeated numeric/graphic measure heading and BMJ's Study or subgroup heading remain familiar journal conventions. The generated Follow-up: first copy remains a minor unfinished default (R5-02 improved, not fixed).

Viewed `inspect-audit-round3-bubble-metrics-00` through `05`: all 24 selected frames, 16 metric-specific bubbles plus HR/IRR setup tabs and results. CI legend samples, panel-bounded guides, meaningful natural ratio labels and explicit transformed proportion scale labels are legible. PAS has relatively long inverse tick labels; this is similar numeric polish to R6-04, not a wrong transformation. Plot bottom labels require scrolling in some current viewports; retained full-device evidence and later matrix lower captures distinguish viewport clipping from export clipping. The HR/IRR three setup tabs expose real covariates, method/inference/precision and plot options; selected controls have visible focus.

### Ordinary single-arm and comparative binary forests

Viewed all six sheets `inspect-audit-round3-presentation-{onearm-proportion,twoarm-proportion}-00..02` (24 native frames): three and six digits in every style, upper/lower views. PRAW single-arm defaults show linear 0–1, OR uses natural labels on logarithmic spacing. Default raw events/non-events and journal events/total presentations match their stated headings, with explicit null/heterogeneity/PI footers. BMJ single-arm raw heading is absent as R6-01 already records. Opened the six-digit BMJ single-arm original full-size (`...-90-0-round4-annotations.png`) to check the tightly stacked summary: its two-line model label clears the last study and heterogeneity text; no additional collision found. Ordinary Intervention/Control headings fit in every style.

### Continuous and coefficient publication layouts

Viewed all nine sheets `inspect-audit-round3-presentation-{twoarm-mean,twoarm-smd,reg-coef}-00..02`, 36 native frames. MD/SMD and regression coefficient axes are linear, ordinary named arm/count/mean/SD headings fit, and Default interval components share blue. At six digits the journal columns are denser but remain separated for these fixtures. Coefficient Fixture 2 retains its exact zero lower bound; linear reference guides and model/CI/PI footers are coherent. Default coefficient figures need vertical scrolling in the native viewport: lower captures show complete axis/label/footer, distinguishing scrolling from cropped figure output. No new finding in this set.

### Entered effects and sequential style variants

Viewed `inspect-audit-round3-presentation-generic-effect-00..02` (12 frames): three/six-digit entered effects have linear axes, correct entered-effect identity and complete PI/footer in lower views. No new collision. Viewed `inspect-audit-round3-presentation-sequential-00..04` (18 frames): MD cumulative and omission in all styles, plus each cumulative editor and deliberately null-excluding rendered bounds. Study added (k), Study omitted and All studies labels remain explicit; reference guides stop before footer; clipped intervals use direction arrows in the matching style colour. Editors visibly say Default/RevMan/BMJ. These journal sequential outputs intentionally share a common layout with different accents; style labels do not promise a standard-forest column arrangement.

### All transformed-proportion standard forests

Viewed all 24 selected native frames on `inspect-audit-round3-presentation-transforms-00..05`: PLN/PLO/PAS/PFT × Default/RevMan/BMJ, upper/lower annotation views. All default forests have natural 0–1 axes; reported study/model bounds and prediction limits use proportions. Footers name the actual null (PLN proportion=1; PLO proportion=0.5; PAS/PFT transformed null=0) instead of inventing the same clinical null for every fit. Default blue remains consistent and ordinary footers fit. The public-package comparison and all 48 four-format export decodes passed. R6-01's missing BMJ single-arm raw-data heading remains; no additional transformed-layout defect found.

### Runtime wording inventory (first sweep)

Read all 186 recorded tooltip strings and all 152 combo-choice strings from the first `TEXT-INVENTORY.json` sweep (3,468 recorded steps; 818 unique short UI strings). This is reading actual runtime properties, not claiming every tooltip was physically displayed. Visible wording generally explains scale/order/confidence scope well. The generic 80-character label tooltip qualifies R6-06 and is explicitly acknowledged there; automated heading shortening still needs inline feedback or lossless handling. Retained polish debt includes method-family package taxonomy, `metafor correction target`, and duplicated Automatic text in some tooltips (F07/D02 improved, not universally closed). No additional numbered blocker follows from these strings alone. Final inventory will include the remaining completed registry.

### Joint diagnostic workflow

Viewed `inspect-analysis-diagnostic-joint-00..01`, eight frames: real metric selection, Reitsma setup, report, selectable table, SROC upper/lower and clinical report. Method/continuity settings are explicit. Clinical interpretation states the study count and average operating characteristics, cautions against assuming a common threshold, and distinguishes sensitivity/specificity from false-positive rate. SROC uses natural 0–1 axes and distinct line patterns for confidence versus joint prediction regions; its lower capture contains the full axis and legend. Tables leave substantial empty space and report overview still requires scrolling (retained hierarchy/efficiency debt); no new misleading statistic or figure defect found.

### Eleven maintained plot-editor workflows

Viewed six combined `inspect-editors-00..05` sheets (22 candidate native frames): actual editor controls plus reopened results for forest, cumulative, omission, subgroup, regression, SROC, diagnostic coefficient, ordinary/contour/trim-fill funnels and Deeks. All eleven maintained Apply→draft Cancel→reopen transactions and four-format exports pass. Regression's hidden CI has no CI legend; Deeks's disabled regression line is absent. Ordinary forest deliberate clipping has matching directional arrows; captions and point multipliers survive reopen. Lower sections require additional scroll captures and are not deemed visually audited merely because properties exist.

Rejected the contour/trim-fill `family-plot-reopened` screenshots as selected-figure evidence: the maintained harness explicitly sets the vertical scrollbar to zero immediately before this capture, showing the ordinary funnel while the actual contour/trim-fill navigation row stays selected. This is an audit-drive limitation, not proof of a product navigation bug. Those two curated candidates were removed; their original raw captures and exports remain. The additional editor inventory clicks the actual selected row and captures its current figure after Cancel, without forcing the whole multi-figure scene to its top. SROC still has individual curve/region colour controls; journal style is not assumed to recolour every independently set component.

### Twelve calculator modes, reconstruction and reopening

Viewed all seven `inspect-calculators-00..06` sheets (26 selected native frames): raw binary/continuous/diagnostic metrics, one-arm proportion/mean, entered binary/continuous/diagnostic, pre/post, and three reconstruction paths. Raw/entered mode labels and Intervention/Control identity are clear; derived summaries update, and invalid CI acceptance is blocked (the driver acknowledges the real validation message before its blocked-state screenshot). All twelve retained helper receipts pass exact persistence plus independent post-reopen analysis; the earlier high-severity R5-10 data-loss trigger is closed.

Continuous forms still spend much of their height around one/two table rows, and some fields need horizontal scrolling. Diagnostic focus can scroll the left labels/error text out of view (existing G07/N11/F06 limits remain). Tiny binary/continuous reconstruction prompts hide question/alternatives despite ample screen space; expanded R6-02 to record this same dialog-sizing issue with exact repro/screenshots. Those small originals are displayed at native pixel size within the sheet, so their constrained opening geometry is directly visible. Cancel and reopened grid state are retained; no additional data loss found.

### Default matrix: single-arm proportion and mean

Viewed primary sheets `inspect-MATRIX-onearm-proportion-00..02` and `inspect-MATRIX-onearm-mean-00..02` (20 frames), plus distinct lower sheets `inspect-lower-MATRIX-onearm-proportion-00..01` (7 frames) and `inspect-lower-MATRIX-onearm-mean-00..01` (8 frames). All ten workflow cells pass. Standard/cumulative/omission/subgroup/regression Text and figures use readable metric headings, explicit SE outcome scales, PI interpretation, subgroup-difference tests and model configuration. Lower report views retain weights/references and the warning that bubble sizes are rescaled for legibility. Subgroup overall rows/tests/PI and axes clear the footer. Mean plots use entered-effect-style columns even for the raw group-summary fixture, so no unobserved raw-data spanner is claimed. Context/caption identifies the investigator outcome and mean. No new finding in these 35 frames.

### Default matrix: regression coefficients

Viewed `inspect-MATRIX-reg-coef-00..02` (10 primary frames) and `inspect-lower-MATRIX-reg-coef-00..01` (8 distinct lower frames). Five workflow cells pass. Linear coefficient axes and the true zero lower bound remain intact; structured subgroup tests/PI match visible figure summaries. Dose/reference identity and extrapolated-intercept wording are explicit. The lower regression report retains model/weights/reference context. No new finding across these 18 frames.

### Default matrix: generic entered effects

Viewed `inspect-MATRIX-generic-effect-00..02` (10 primary frames) and `inspect-lower-MATRIX-generic-effect-00..01` (8 distinct lower frames). All five cells pass. Entered-effect identity, linear effect/SE scale and actual null are explicit. Subgroup rows/overall intervals/difference test remain separate; regression notes distinguish model weights from rescaled bubble sizes. No new layout, wording or numerical finding in these 18 frames. Dedicated investigator units remain absent as the inherited scorecard states.

### Default matrix: comparative binary and mean difference

Viewed all primary `inspect-MATRIX-twoarm-{proportion,mean}-00..02` sheets (20 frames) and lower `inspect-lower-MATRIX-twoarm-{proportion,mean}-00..01` sheets (16 frames). Ten cells pass. OR ratios are naturally labelled on logarithmic spacing; Text explicitly states fitted log scales and the clinical equal-odds null. MD is linear with Intervention minus Control stated in outcome units. Raw comparative counts or N/mean/SD align with arm labels. Subgroup totals, group-difference tests, model/PI summaries and footer axes remain clear. Regression labels distinguish fitted coefficient scale from natural ratio output. No new finding across these 36 frames.

### Default matrix: standardized mean difference

Viewed `inspect-MATRIX-twoarm-smd-00..02` (10 primary frames) and `inspect-lower-MATRIX-twoarm-smd-00..01` (7 distinct lower frames). All five cells pass. Standardized-scale SEs and Intervention-minus-Control direction are explicit; the small negative pooled lower bound remains negative at six digits. Subgroup clinical intervals/tests and full footer are present. The longer SMD caption wraps into available top space without colliding with the header or regression panel. No new finding in these 17 frames.

### Default matrix: diagnostic components and dedicated coefficients

Viewed `inspect-MATRIX-diagnostic-00..03` (15 primary frames) and initial `inspect-lower-MATRIX-diagnostic-00..03` (14 candidate lower frames). Five workflow cells pass, with both sensitivity and specificity components. Natural 0–1 axes, actual TP/FP/FN/TN counts, logit SE headings and clinical nulls remain explicit. Reitsma coefficient Text uses readable logit/OR CI headings and six digits; package/model/continuity/reference details are retained. Opened the Specificity OR coefficient lower original full-size and measured its actual retained SVG: equal OR increments 0.6…1 have equal physical spacing. R6-07 records this declared linear coefficient exception as a low-severity consistency recommendation, not wrong statistics or another merge blocker.

Rejected five first-component `...-figure-bottom.png` candidates: the original matrix driver scrolled to the whole scene bottom, so those frames show specificity while sensitivity remains selected. They were removed from the curated lower inventory, but original raw captures/index hashes remain intact. The nine correct lower frames are retained. Future matrix captures now align to the selected plot item's bottom, not the whole scene; a small separate Default component-footer recovery will fill the five missing first-component views without overwriting or relabelling the original run. The source of this evidence limitation is the audit driver, not a product navigation defect. Final review must include the recovery receipt and its inspected captures.

### Shell continuation inspection

Viewed all 33 native shell frames in `inspect-SHELL-00..08`, individually. Startup, empty wizard validation, generic metric explanation, loaded grid, dirty Open cancellation, saved/reopened recent project, File/Edit/View/Analysis/metric/Dataset/Help menus, structure/studies/covariates, duplicate covariate validation, confidence explanation, About 0.5.0, quick-start, import entry, native template picker/save and exported report in xedit are readable. The picker shows only the owned audit directory and generic sidebar locations. About remains unnecessarily narrow (R6-02); no additional blocker. Header inventories distinguish actual attached actions from separately demonstrated menu gestures. Also viewed `inspect-OPTIONS-00..08` (first 36 frames): single-arm proportion/mean context menus and fixed/random method forms. Repeated adjacent metric menus are retained as capture limitations, not evidence of distinct successful header gestures.

### Main method and plot-option inventory

Viewed all 139 frames in `inspect-OPTIONS-00..34`, individually, covering seven families through SMD. All offered fixed/random method forms and enabled plot tabs/scroll positions are readable. Binary Peto/Mantel–Haenszel/inverse-variance alternatives and continuity controls are visible. Plot options remain dense with repeated Show labels, technical capitalization and generic disabled second-group controls; these support existing polish findings, not a new blocker. The six-study small-study dialog clearly disables formal asymmetry tests. Repeated effect header captures cannot prove every header right-click target; attached menu inventories supply the action labels.

### Diagnostic and time-to-event option inventory

Viewed all 72 frames in `inspect-OPTIONS-REMAINDER-00..17`, individually. Diagnostic metric selection, Reitsma/independent fixed/random method forms, HR fixed/random and IRR fixed/random/raw Mantel–Haenszel forms and all enabled plot-tab scroll regions are readable. The joint method identifies mada 0.5.12. IRR exposes double-zero exclusion and continuity controls. Nine-study asymmetry guard is explicit. Existing inconsistent method capitalization and generic disabled group headings remain low polish concerns. HR/IRR offscreen covariate header repetitions are capture limitations, not distinct menu gesture proof. No additional merge blocker.

### RevMan matrix: four single-arm/entered-effect families

Viewed `inspect-MATRIX-{onearm-proportion,onearm-mean,reg-coef,generic-effect}-revman-00..01` and each corresponding `inspect-lower-...-00` sheet: 20 primary figures and 16 distinct lower views, covering standard, cumulative, leave-one-out, subgroup and meta-regression. Proportion axes are natural linear 0–1; continuous/coefficient/entered-effect axes linear. Subgroup totals, difference tests, model/heterogeneity and prediction intervals are visible in lower views. No new overlap in these short-label fixtures. Ordinary single-arm mean omits raw means/sample-size columns despite generic setup controls; retain the prior output-density recommendation rather than a new finding. Six-digit labels remain legible at the selected fit width.

### RevMan matrix: comparative, diagnostic and time-to-event

Viewed all primary/lower sheets for `MATRIX-{twoarm-proportion,twoarm-mean,twoarm-smd,diagnostic,hr,irr}-revman`: 35 primary figures and 29 distinct lower views. All 30 workflow cells completed; diagnostic contributes two components per cell. Ratios use natural ticks with log spacing, MD/SMD linear, diagnostic sensitivity/specificity natural 0–1. Diagnostic coefficient exception remains R6-07. Comparative arm names and IRR person-time units are explicit. Dense 65-study HR outputs require scrolling; upper/lower identities match. HR/IRR leave-one-out journal plots omit the all-studies/model annotation block seen for other data families; this is an output-consistency optimization, with fitted results retained in Text/Tables, not an incorrect-result claim. HR/IRR meta-regression execution carries the recorded R6-08 wording exception; exit zero is not wording acceptance. No additional blocker in these ordinary-label fixtures.

### Axis Apply / later draft Cancel continuation

Viewed all 66 selected frames in `inspect-axis-apply-00..16`. This native variant clicks Apply on the alternate scale, changes a later draft back to the default, Cancels that draft, reopens and exports, with original axis-conventions assertions and decoded four-format exports retained. PLO/PAS/PFT/PLN and OR/diagnostic sensitivity/specificity run through all three styles; MD confirms linear-only behavior. Reopened state and post-export figures preserve the applied choice; fitted fields/weights remain unchanged. Captures labelled `axis-option-reopened` show the result after the reopened-dialog assertion, not the dialog itself. Optional journal PLN long tick labels reproduce R6-04; natural defaults were separately inspected. Default boxes/whiskers and diamonds remain blue. No state-persistence regression observed.

### BMJ matrix: first five families

Viewed primary sheets 00..01 and lower sheet 00 for `MATRIX-{onearm-proportion,onearm-mean,reg-coef,generic-effect,twoarm-proportion}-bmj`: 25 primary figures and 20 lower views. All 25 workflow cells complete. Natural proportion and log-spaced ratio axes are consistent with round 6. Purple regression intervals and summary diamonds are readable; subgroup study symbols differ from sequential diamonds but remain recognizable. Unlabelled single-arm n/N column repeats R6-01, including subgroup views. No additional blocker.
