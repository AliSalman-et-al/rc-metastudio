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

No isolated tests are planned initially; extend actual Qt/R drivers and existing
R geometry/authority checks. If isolation becomes necessary, list its distinct
failure modes and write that check before implementing the corresponding change.

## Axis conventions — added after R5-09, before implementation

Failure modes: natural labels on transformed positions mistaken for a linear axis;
transforming fitted inputs/SEs/weights instead of coordinates; double transformation;
study-specific Freeman–Tukey inverses confused with the pooled harmonic-mean inverse;
summary/subgroup diamonds, whiskers, cap endpoints or nulls left on the old scale;
round tick labels drifting from actual positions; stale axis titles; editor choice
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
to independently transformed original effects, and verify weights/fit bytes remain
unchanged. Reopen the editor, rerun and export saved plot parameters; exercise Cancel.
Retain native screenshots and decoded exports plus original input/observed state.
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
