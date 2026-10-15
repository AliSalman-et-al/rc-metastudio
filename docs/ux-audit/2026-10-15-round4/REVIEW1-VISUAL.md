# Review 1 — actual visual inspection

These are native Linux QScreen captures, inspected directly at full image size.
Copied frames are unmodified. Automated SVG geometry and export decoding are
separate proof; a copied image is not automatically an inspected image.
Historical development captures remain in the receipt index and are not presented
as final evidence. The CSV wizard frame in `review1-native-design-final` caught a
compositor transition; its replacement waits for the native dialog to settle.

| Native receipt / exact frame numbers | What was inspected and observed |
| --- | --- |
| REVIEW1-RESUME: 30, 31, 72, 73 | BMJ binary 3/6 digits and bottom views: pooled label clears 39 / 135; test and first tick clear. |
| review1-native-diagnostic-complete: 15, 36, 99, 120 | Default and journal diagnostic leading, round 0.5/0.6/0.7 ticks and distinct title baseline; no cropped or overprinted header. Default null guide was subsequently bounded by cab0d7a; this historical default frame still shows the earlier guide. |
| review1-native-figures-binary: 42, 84 | BMJ binary at 3/6 digits: raw totals, weights, CIs, footer and ticks clear. |
| review1-final-twoarm-mean: 14, 28, 42, 84 | MD, three styles at default precision plus BMJ 6: aligned columns, concise conventional test, no annotation collisions. |
| review1-final-twoarm-smd: 14, 28, 42, 84 | SMD equivalent style/precision probe: no collisions or wrong labels. |
| review1-verified-generic-effect: 14, 28, 42, 84 | Journal pooled/100% padding clear. Default exposed the reference line crossing footer prose; retained as the contact-sheet before frame. |
| review1-bounded-generic-effect: 14, 56 | Default after: reference stops within studies at 3/6 digits; footer clear. |
| review1-verified-reg-coef: 14, 28, 84 | Explicit coefficient null and contextual axes, journal headers/columns/footers clear. Historical default reference subsequently repaired. |
| review1-native-design-final: 02, 03, 04, 05, 06, 07, 08, 12, 13, 14, 18 | Pristine start, wrapped full/missing paths, actual light/dark palettes, wizard actions, 1000×720 navigator, result-first report, configuration, tables and remembered SVG. CSV frame 07 had a native transition, replaced after settling; frame18's earlier installed forest separator is superseded by final source captures. |
| review1-bounded-subgroup: 33 | Actual BMJ subgroup footer: heterogeneity, overall, subgroup difference, PI; first tick clear. |
| review1-bounded-calculator-mode-entered-continuous: 02 | 95% confidence interval, native action sizes; compact entered inputs, result and actions visible. |
| review1-bounded-calculator-mode-pre-post: 02 | Input/result/action geometry clear; no result or action trapped in the scroller. |
| review1-bounded-calculator-binary/continuous/diagnostic: 04 each | All three calculator interval labels, active inputs and action rows clear; no clipping. |

All 16 derived publication previews in REVIEW1-EXPORTS.json were inspected:
BMJ binary and RevMan sensitivity, 3/6 digits × PDF/PNG/TIFF/SVG. They preserve
column/header/footer/tick clearance. TIFF previews were also inspected individually
after a batched image-display quirk; decoded pixels match. These are renderings of
actual exported bytes, clearly separated from native screenshots.

Final source replacement frames and the contact-sheet check are appended below.

- `review1-qualified-audit-round3-presentation-transforms` frames 16/48 (PLN
  default/BMJ), 64/80/96 (PLO all styles), 144 (PAS BMJ), 192 (PFT BMJ) inspected:
  clinical Proportion headers, actual concise nulls, round display ticks and
  default bounded guides are correct. PLN's 0.05 endpoint clears the BMJ test.
  PFT pooled values use the independently verified harmonic conversion and PI
  remains explicitly Freeman–Tukey scale. No header/column/footer collisions.
- `review1-bounded-ux-improvements` original evidence frames 04/19/26 and
  `review1-bounded-review-workflows` 08-0/08-1 inspected: error/setup controls,
  mapped CSV preview and concise ordering menu clear. Covariate-error frame 26
  caught native resize before the action row finished settling; supplemental
  proof waits and asserts full error/action bounds before recording it.

- `review1-qualified-audit-round3-presentation-onearm-proportion` 14/28/84
  inspected: default/RevMan 3 and BMJ 6 show Proportion, the actual zero null,
  separated headers and clear pooled/footer/axis columns.
- `review1-publication-ux-improvements` 26 inspected: settled native resize shows
  the complete validation message and both Cancel/Add covariate controls. The
  driver asserts the full message/action bounds before capture.
- `review1-publication-review1-design` 02/04/07/12/18 inspected: pristine page,
  light palette, settled CSV wizard, key-first report and clean rerun figure
  header. Frame12 exposed a stale sidebar highlight; 8ef7468 synchronizes actual
  toolbar navigation and disables plot actions in Tables. Final replacement
  native report capture follows this repair.

- `review1-publication-audit-round3-presentation-diagnostic` 15/36/120/126
  inspected: default null guide now ends at studies; Sens/Spec headers have
  separated baselines, round probability ticks and clear titles at 3/6 digits.
- All 16 **final** previews regenerated from `review1-publication-...` receipts
  in REVIEW1-EXPORTS.json were inspected individually: BMJ binary and RevMan
  sensitivity, PDF/PNG/TIFF/SVG at 3/6 digits. Pooled label/totals, test/first
  tick, multiline header, numeric columns and axis/title are clear in each.

- `review1-reading-qualified` 05/07/08/12/13/14 inspected: final dark recents,
  settled CSV dialog, labeled dataset navigation, correct Text report/Tables/
  Model configuration sidebar highlights, aligned result/weight tables, one
  inference configuration and clear 95% confidence wording. Plot actions are
  disabled in Tables; real toolbar round-trip restores the same selected plot.
- `review1-publication-audit-round3-presentation-twoarm-proportion` 42/84
  inspected: all three originally reported BMJ collisions are clear at 3/6
  digits in the current final native/export proof.
- Final `contact-sheet.html`: T3 html_preview at 1200 px, 17 native frames,
  content height 5054, only console message `Native comparison frames: 17`, no
  console errors. Inspected paired layout/captions/path wrapping and individual
  full-resolution frames. Published with html_render; CONTACT-SHEET-REVIEW.json
  binds the standalone file SHA and preview observations.

Duplicate development PNG copies were omitted from the curated folder by
`curate_review1.py`; no original native artifact, receipt or user-provided draft
was removed. Historical frame numbers above resolve under each receipt's
`evidence` directory and `observed.captures` in REVIEW1-NATIVE.json. Final native
families and the two development frames used by the contact sheet remain copied.

- `review1-coefficient-qualified` 14/28/42/84 inspected after the final serialized
  install at `8c8e8a3`: default/RevMan/BMJ at three decimals plus BMJ six;
  coefficient context and H₀ are correct, zero bound prints zero, model/100%
  spacing clear and default guide ends within study rows. The earlier in-flight
  coefficient drive remains development proof, superseded by this clean receipt.

- Clinical follow-up: the first `clinical-qualified` capture exposed screenshot
  instrumentation leaving Tables highlighted; that development frame is not a
  final app-state claim. The actual startup mismatch was reproduced separately
  by `review1-clinical-sidebar-before`. `febd7d6` routes startup through the same
  report action and restores selection after automatic native report/table/figure
  capture. The driver asserts Text report before and after instrumentation.
- `review1-reading-finished-analysis-diagnostic-joint` 06 inspected individually:
  clinical interpretation and operating-point tables lead, Text report is selected,
  report text wraps, and the repeated clinical table caption is removed.
- `review1-reading-finished-analysis-diagnostic-regression-multiple` 04-report
  inspected: a single overall likelihood-ratio heading and clear Group/Dose block
  tables; numerical values unchanged. The matching `clinical-complete` frame is
  retained as the caption before image. Combined diagnostic report 05-report
  was also inspected: Sens/Spec key results, heterogeneity, explicit null and PI
  precede configuration.
- Final contact-sheet update: 19 native frames, html_preview width 1200, content
  height 5534, no console errors, console `Native comparison frames: 19`.
  Caption pair inspected at full native resolution; latest html_render published.
  CONTACT-SHEET-REVIEW.json binds the updated standalone HTML bytes.

- Final corrected UX gesture drive `review1-ux-gestures`: native frames 14 and 15
  inspected individually. The report at deliberately selected 200% zoom has clear
  aligned estimate/heterogeneity/test/PI tables; returning to Forest Plot restores
  its separate 100% zoom and sidebar selection. The 3-decimal figure has distinct
  totals, footer and axis baselines; actual PDF export succeeds. These are current
  toolbar gestures, independently repeated through offscreen Qt with exit zero.

- Final qualification follow-up: `review1-coefficient-editor-after` frame 07
  inspected individually: the native coefficient editor opens with clear label,
  bound/tick controls and Apply/Cancel/OK actions. The real workflow proves
  Cancel/reopen and all four exports. `review1-singlearm-onearm-proportion` and
  `review1-singlearm-onearm-mean` frame 10 inspected individually: derived
  estimate, 95% confidence interval, Clear and OK are visible; unsupported
  Back-calculate is absent. The mean form retains generous unused vertical
  space; no new layout change is claimed for that existing form.

- The recovered coefficient workflow's native frame 09-figure was also inspected:
  Dose estimate and interval, null reference, round axis values and custom edited
  label remain distinct. The 100% view scrolls vertically; four-format exports
  are independently decoded by the workflow. No renderer/layout change is
  claimed by the default-lookup repair.
