# Round 6 plan — written before implementation

Starting revision: 80e4bee, branch ux/audit-improvements. Linux native Qt, pinned
R 4.6.1 and the round-three test-owned library. No new statistical procedures.
Original 415 numerical fields and independent authority/golden gates remain exact.

## R5-10 — first: numeric input integrity

Failure modes to trace and prove before changing product code:

- Display rounding written back into raw model values or reconstructed summaries.
- Validators/spinbox decimals truncating a legal finite value or rejecting exponents.
- Float formatting in calculator tables, line edits, grid EditRole and delegates.
- Accept/focus-out/commit rereading a rounded preview; invalid CI commit continuing.
- Project serialization rounding, converting types, or selecting stale effect sources.
- CSV import/export formatting losing digits, locale commas, or exponent notation.
- Dialog and workspace undo/redo restoring rounded/stale input or derived summaries.
- Locale decimal separators parsed differently by different editors.
- Very large values/scientific notation overflowing, becoming zero or losing digits.
- Previously generated SD/SE/CI/P summaries being mistaken for independent supplied
  inputs after an authoritative field changes; obsolete derived preview persists.

Proof: extend retained real keyboard E2E before implementation. Cover every existing
calculator mode, applicable tiny/huge/many-decimal/exponent values (counts remain
integers and proportions remain in range), decimal commas, grid editing including
unchanged commits, Accept/Cancel, undo/redo, CSV and save/reopen. Assert exact floats
at model/storage boundaries; compare effects and subsequent real fits against
independent math/public package calculations. Reject invalid bounds without commit.
Capture before/after screenshots and observed values; retain failing baseline.

## Remaining priority order and required proof

| Item | Failure to prevent | Real-system proof planned |
| --- | --- | --- |
| R5-09 | Internal key used instead of contextual display identity | Attached menu recursion for ten families, open dialogs/choices/tooltips and result text; fail forbidden built-in labels, preserve user names; retain sweep in E2E |
| Axis conventions | Misleading spacing, stale axes or altered fitted data | Source-verified defaults and persisted editor option; native three-style family matrix, endpoint/tick geometry and exports |
| R5-04 | CI caps larger than study spacing | Short/65-study standard/subgroup, default/RevMan/BMJ; measure SVG cap-to-row geometry, display and export; fitted horizontal values unchanged |
| R5-06 | Headers cross unequal wrapped arm names | Three styles with long custom names; measured SVG header blocks and native/export inspection |
| R5-03 | Diagnostic coefficient/ML tables bypass precision | Two and six digits, numeric/factor/interaction diagnostic regressions; Text/Tables/copy/export equality; independent fitted fields unchanged |
| R5-01 | Fitted SE beside transformed estimate without scale | Sequential/subgroup all transformed families, readable fitted-scale headings in report/Tables/export |
| R5-11 | Hidden bands still in legend | Regression/CI/PI toggles with legend on, all styles, displayed SVG and exports; keys match marks |
| R5-07/D04 | Invalid contour fields and unhelpful eligibility | Invalid submit stays in configuration with inline reason; recover/run; excluded-study reason reflects actual inputs |
| R5-08 | Requested unsupported style silently ignored | Each affected figure family's setup/editor shows available layout or explicit fallback explanation |
| R5-05 | Raw package labels reach reports | Reachable labels sweep plus diagnostic outputs; readable display boundary without renaming model/package identities |
| R5-02 | Duplicate generated captions | New default captions have one identity; explicit investigator text preserved through edits/reopen/export |
| Group: Group | Unnamed default group repeated | Single-arm context hides unnamed default, meaningful custom group remains; inspect analogous context |
| Accessibility/shell | Contrast/focus and window-state races | Native keyboard focus/restore and sampled palette contrast; project-shell waits boundedly for real Qt/WM settled states, original assertions retained |

The retained label assertion also runs at the shared desktop evidence boundary,
so dialogs exercised by the complete matrix are scanned alongside the ten-family
menu sweep. Captured labels/tooltips/combo items are retained with each step.

No isolated tests are planned initially; extend actual Qt/R drivers and existing
R geometry/authority checks. If isolation becomes necessary, list its distinct
failure modes and write that check before implementing the corresponding change.

## Axis conventions — added after R5-09, before implementation

Failure modes: natural labels on transformed positions mistaken for a linear axis;
transforming fitted inputs/SEs/weights instead of coordinates; double transformation;
study-specific Freeman–Tukey inverses confused with the pooled harmonic-mean inverse;
summary/subgroup diamonds, whiskers, cap endpoints or nulls left on the old scale;
round tick labels drifting from actual positions; stale axis titles;
automatically resolved bounds/titles saved as explicit user choices, then transformed
a second time on regeneration; editor choice
lost on Apply/Cancel/reopen, regeneration or export; changing funnel/ROC conventions
through a shared helper. Proof is required before claiming this item complete.

Documentation checked 2026-10-15:

- [RevMan manual-input analyses](https://documentation.cochrane.org/revman-kb/manual-input-analyses-259686817.html)
  documents graph controls. Its default scale value of 100 describes plot range;
  it does not independently establish the coordinate transformation.
- [Cochrane chapter 6, §6.1.2.1](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-06)
  explicitly recommends log graphical scales for ratios, with symmetric intervals;
  ratios have null 1, differences null 0. Use natural measure names on the axes.
- [Chapter 10, §§10.2–10.3 and 10.11.4](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-10)
  distinguishes effect estimation, inverse-variance weighting and meta-regression.
  Axis edits must leave those calculations intact.
- [Chapter 15, §15.4](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-15)
  supports interpreting relative effects as ratios and absolute effects in natural
  units; it does not prescribe a proportion-bubble coordinate default.
- [RevMan DTA graphs](https://documentation.cochrane.org/revman-kb/analysis-graphs-in-dta-reviews-236847627.html)
  separates sensitivity/specificity forests from SROC graphs.
  [DTA Handbook v1 chapter 10, §§10.3.3–10.3.4, p17](https://methods.cochrane.org/sites/methods.cochrane.org.sdt/files/public/uploads/Chapter%2010%20-%20Version%201.0.pdf)
  shows both forest axes at evenly spaced 0, .2, .4, .6, .8, 1 without a null line.
  Downloaded the actual PDF and inspected page 17; retained source in ignored
  raw/sources/dta-ch10 and rendered page in raw/sources/dta-page17.png.
- [metafor forest.rma, Applying a Transformation](https://wviechtb.github.io/metafor/reference/forest.rma.html)
  distinguishes `transf` (coordinates and intervals) from `atransf` (labels only).
  `atransf=exp` retains logarithmic ratio spacing. A linear natural axis needs
  transformed coordinates, including asymmetric confidence intervals.
- [meta forest.meta](https://guido-s.r-universe.dev/meta/doc/manual.html#forest.meta)
  documents `backtransf=TRUE`; transformed proportions are displayed as proportions.
  Verified spacing against the [maintainer's implementation](https://github.com/guido-s/meta/blob/master/R/forest.R):
  `log.xaxis <- backtransf & is_relative`, then non-relative coordinates and bounds
  are back-transformed. Thus natural-scale proportion forests are linear. Retained
  retrieved source raw/sources/meta-forest. PFT pooled inversion uses its effective N.
- [metafor regplot](https://wviechtb.github.io/metafor/reference/regplot.html)
  permits both coordinate and label transformations, including curved natural-scale
  regression lines; it does not mandate natural-scale proportion bubbles. Retain
  the fitted transformed axis as their default and label the transformation clearly.
  Ratio bubbles retain straight fitted lines with log spacing and natural labels.
  The CMA regression manual download returned HTTP 403; no unsupported CMA-specific
  claim is used to choose behavior.

Decision: ratio forests/bubbles default log spacing, natural labels/titles; forest
editor offers linear natural ratio coordinates. Transformed proportion and diagnostic
sensitivity/specificity forests default linear natural coordinates (0–1), with no
arbitrary null line; transformed coordinates are opt-in with an explicit scale title.
MD/SMD/RD/mean/coefficient/entered-effect axes remain linear. Proportion bubbles keep
clearly labelled fitted-scale coordinates. Funnel, contour, trim-and-fill, Deeks and
SROC keep their existing family-specific conventions.

E2E proof: retain before figures, then keyboard/UI editor changes for ratios,
log/logit/arcsine/PFT proportions and diagnostic sensitivity/specificity across all
three styles. Measure tick positions in actual SVG, compare study/summary endpoints
to independently transformed original effects, and verify every numeric fitted field and weight remains
unchanged. Reopen the editor, rerun and export saved plot parameters; exercise Cancel.
Retain native screenshots and decoded exports plus original input/observed state.
PFT cumulative/omission/subgroup figures additionally compare each inverse against
a public fit of its actual subset and that subset's harmonic sample size.
Run the 415-field exact comparison and golden gates; use the sanctioned tool only
for reviewed presentation labels. Do not refresh numerical contracts.

## Execution and evidence

Commit/push this plan first. Fix and prove R5-10 before other product changes.
Keep small commits, push each fast-forward immediately; on failure wait 30 seconds,
retry once, then stop/report. Reinstall changed RCMetaR before desktop driving.
Reuse round-five recorder/install/drivers and pinned environment. Raw logs go in
ignored raw/. Curate inspected before/after screenshots, contact-sheet.html, README,
CHANGES (items → commits → evidence), TESTS (commands/exits/verbatim failures),
COMMITS and REPRODUCE.sh. Update HANDOFF with proved paths and explicit limits.
Run numerical equivalence, golden gates, affected fresh native drives, then once
`verify_all.py --full --fresh`. Preserve every failed attempt and exact result.
Extra taste changes require an addition to this plan before implementation.

## Additional completion fix — closed result-window ownership

Reason: repeated axis edits/reruns retain closed result widgets and their SVG scenes
until application exit. The expanded real workflow grows to gigabytes and times out.
Failure modes: hidden scenes/renderers remain owned by the main window; callbacks
keep snapshots alive; queued refits target closed widgets; premature deletion loses
settings or evidence. Before implementation, extend the real axis drive to close a
result, flush Qt deferred deletion and assert the owned QObject is deleted. Keep
all render/fit/persistence checks and the existing timeout. Compare the repeat run
with the retained timeout and process-memory observation; do not relax the deadline.

The native before/after numerical matrix excludes only metafor's `time` field
(elapsed computation time, recorded separately). All numeric statistical fields
and weights use bit-exact equality; the original 415-field gate is unchanged.

## Final presentation checks caught by native driving

- BMJ's padded x-coordinate range compressed its measured footer width. The new
  natural zero tick exposed a PFT null-test collision. Keep measured physical
  column widths by including the range padding and right margin in device width;
  retain the native SVG text-gap assertion and four-format transformed exports.
- R5-01 includes funnel SE axes. Existing ordinary/contour/trim-fill defaults must
  state the fitted scale; Deeks stays in its established diagnostic coordinates.
  Use readable metric names rather than bare codes. Add default-axis assertions
  to the existing real plot-editor drives before changing these labels. Extend
  the retained label sweep to actual SVG text, alongside Qt widgets. These are
  label-only funnel changes; positions, fitted values and variances stay exact.

The unchanged-default contour drive caught a related validation boundary: the UI
showed suggested levels only as a placeholder, while the new validator correctly
rejected its empty value. Populate the established 90, 95, 99 defaults as editable
text. Explicitly clearing the field must still fail inline. Retain both triggers.

Selected precision also needs a univariate diagnostic check: a hard minimum of
three SE decimals can override a two-decimal selection. Before changing that
formatter, extend the real cumulative/subgroup report drive to require the chosen
SE precision while retaining scientific notation for genuinely small nonzero SEs.
Original default three-decimal numerical fields remain exact.

The broadened SE formatting attempt failed the frozen contract for three historical regression SE fields at digits=2 (0.004, 0.002 and 0.003 differences). Restrict removal of the three-decimal SE floor to diagnostic summaries/sequential/subgroup reports; retain the original non-diagnostic numerical presentation contract. No golden numerical refresh.

## Final-profile diagnostic axis-title clearance

The final fresh profile exposed an actual retained geometry failure in `audit-round3-presentation-diagnostic`: BMJ axis title/tick gap was 2.73 physical points, below the unchanged 4-point bound. Fixed row coordinates place larger six-digit diagnostic typography too close. Before changing the renderer, retain this failing native-equivalent vector artifact and its exact assertion; then derive title spacing from the device font height and a physical 5-point gap. Reuse the existing diagnostic presentation driver at digits 3/6 in all three styles and exports, then repeat final full fresh qualification. Do not loosen its assertion.

The first physical-spacing replay measured 3.90 points and correctly failed the unchanged four-point check: point size alone excludes device character leading and text anchor differences. Use the device character-line height (`par("csi")`) at actual cex plus the same five-point gap, then replay before full qualification.

## Final-profile stale ratio-label assertion

`review-workflows` still asserts `Odds ratio (log scale)`, despite the source-reviewed natural title decision. The rendered ticks and all preceding numerical/order assertions pass. Update this exact expected title to `Odds ratio`, retain all numerical checks, and fail explicitly if the retired title returns. A sweep of all E2E/skill/R-test expected strings found this one remaining obsolete axis-label expectation. Replay the real review workflow before another final full fresh run; retain the actual failed profile.

## Final-profile entered-CI recovery focus

The full offscreen profile fails the valid correction after an invalid upper CI in all three entered-effect calculator families, despite their passing native replays. Before changing product or driver, record actual editor text, focus, editingFinished delivery, stored entered bounds and the validation flag. Distinguish a missing real focus transition from stale validation/model commit logic. Retain the invalid-Accept block and assert valid keyboard correction, model commit, Accept/save/reopen and independent fit in both native and offscreen modes; do not clear the flag blindly or weaken the assertions.

## Final-profile shared funnel metric identity

The final two HR/IRR workflows exposed a new test-helper assumption: the shared funnel label check hard-coded Odds ratio. Both actual figures correctly show Hazard ratio / Incidence rate ratio and fitted log SE. Use the current contextual readable metric identity in that shared check, preserving its SE-scale and all numerical/export assertions. Replay the complete HR/IRR scenarios (all editor families/four-format exports), then repeat full fresh qualification. The failed profile (117 passes, two assertion failures) remains explicit.

## Reviewer fixes — accepted round-six follow-up, before implementation

Starting revision dc235ab. Preserve the existing fits, weights, statistical tests,
415-field exact contract and numerical golden oracles. Use only pinned R 4.6.1.

1. **PFT prediction intervals.** Failure modes: transformed PI printed beside a
   natural-scale pooled result; different inverses in forest/report/Table/export;
   whole-dataset N reused for a subset; unavailable/invalid N silently mapped to a
   proportion; a fitted-scale zero test misread as testing proportion zero. Extend
   the real Qt/R axis drives before product edits to compare each displayed PI
   against public `meta::metaprop(sm="PFT")` and/or `metafor::transf.ipft.hm`
   with the actual fit's harmonic mean N. Retain raw and inverse bounds, fitted N,
   authority/package versions and differences for bundled/single-arm fixtures and
   sequential/subgroup subsets. Exercise PFT/PLO/PAS in Default/RevMan/BMJ, Text,
   Tables, copy and export. Undefined inverses must retain explicitly labelled
   transformed bounds. Clarify the existing PFT null wording without new tests.
2. **Single-arm group spanners.** Failure modes: default `Group` printed above raw
   counts/means/rates; custom group names lost; one style behaving differently.
   Before changing the renderer, extend native single-arm drives to assert absent
   unnamed spanners and preserved meaningful names in all three styles, including
   proportion, mean and rate families. Retain before/after figures and SVG text.
3. **Diagnostic regression headers.** Failure modes: logit bounds ambiguous;
   exponentiated bounds inconsistently labelled; Text/Tables/copy/export disagree;
   presentation edits alter coefficients. Extend the existing native diagnostic
   precision drive first to require compact, explicit logit/odds-ratio CI headings
   on all surfaces at two/six digits, retaining fitted numerical comparisons.
4. **0.5.0 release identity.** Failure modes: Python/R/About/project/package version
   disagreement; duplicate VERSION drifts; bump script breaks after deduplication;
   stale installed-source/qualification bindings. Use `__version__` for runtime
   identity, update current release surfaces and lock metadata, leave historical
   records intact. Native About and save/reopen must observe 0.5.0, including the
   saved `application.version`. Reinstall RCMetaR and record installed 0.5.0 plus
   source hashes. Replace Unreleased with today's dated 0.5.0 entry and concise
   user-facing rounds 3–6 changes; inspect packaging consumers and current docs.

Retain exact commands, exits and verbatim failures in additive REVIEWER-* records,
curated inspected before/after screenshots and contact-sheet entries. Reinstall
changed RCMetaR before native drives. Run affected fresh native workflows, strict
goldens and the unchanged 415-field gate, then one final
`verify_all.py --full --fresh`. Refresh installed-source/provenance records rather
than loosening bindings. Update CHANGES/TESTS/COMMITS and HANDOFF. Small commits,
each immediately fast-forward pushed; on push failure wait 30 seconds, retry once,
then stop/report. No force push, history rewrite or PR. Finish clean and pushed;
state any unproved release/platform surfaces explicitly.

5. **Default plot colours (additional user request).** Failure modes: black study
   markers/CI lines/caps beside blue summaries; one forest variant or export still
   inconsistent; clipped arrows or legend samples retain black; colour changes
   accidentally affect journal styles or fitted geometry. Before implementation,
   extend native Default family checks to compare actual SVG marker/interval/cap/
   arrow colours with the summary colour and verify four-format exports. Cover
   standard/subgroup/cumulative/omission, one-arm, diagnostic Sens/Spec and HR/IRR;
   inspect bubble/funnel for the same inconsistency and change only affected marks.
   Use one shared blue definition, retain readable contrast against both zebra
   backgrounds, and preserve exact numerical/geometry checks. RevMan/BMJ unchanged.
6. **Default style label (additional user request).** Failure modes: old label in
   setup/editor/tooltips/report/help; renamed persisted key breaks saved settings.
   Keep internal `default`, use visible `Default` consistently, update current docs
   while preserving historical evidence. Native setup/editor and save/reopen must
   observe `Default` from an existing project carrying the original style key.

Reviewer-drive findings: hiding the spanner also requires removing the empty
name from Default's `ilab.groups`; otherwise measured layout indexes an empty
named width and fails before drawing. Retain that exact failed native trigger and
replay all unnamed/custom cases. The authority script must supply meta's inverse
with one harmonic N per endpoint (its API indexes N by endpoint); retain the
initial NA/comparison failure and corrected public-API replay. Neither changes
fits or accepted numerical tolerances.

Visual reviewer-fix inspection found that `forest.default(col=accent)` also
colours study-name text. Preserve black text: suppress package slab drawing and
render study names once at the existing text position with the existing cex and
black ink; keep sequential's existing manual text path. Extend the native SVG
colour assertion to require black study labels before this correction. Existing
row/interval geometry checks remain unchanged.

The journal subgroup renderers reuse Default layout with their original style in
`params`. Bound the colour change to the persisted Default key; preserve the old
journal fallback ink selection. Native PFT subgroup drives will explicitly assert
black study CI lines for RevMan/BMJ while checking the new PI values separately.

Clipped-CI proof must classify the drawn marks, not infer the plot bounds from
its outermost tick: ticks may stop inside the clipping range. Exclude full-width
subgroup separator rules and check every study CI stroke in the row region.
Unclipped views still require caps; the intentionally clipped view instead
requires actual blue arrow polygons (a capped endpoint can legitimately disappear).
Add native funnel/bubble editor replays and reject the retired Default label at
all recorded visible Qt/SVG boundaries in the full registry.
