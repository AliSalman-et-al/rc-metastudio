# RC MetaStudio native round-five re-audit — 16 October 2026

## 1. Executive summary

**IN PROGRESS. No final verdict counts or all-app qualification yet.** Independent read-and-report audit at `ddeef0a` on `ux/audit-improvements`. No application, test or R package edits. The requested folder/date follows the task; the host clock reports 15 October UTC.

Native doctor passed using DISPLAY=:0, xcb, pinned R 4.6.1 and the round-five test-owned library. All 55 source and 24 installed-file receipt hashes match current bytes; see [provenance](PROVENANCE.json). Implementation claims await fresh driving and inspection.

## 2. Scorecard and independent verification

**Provisional while the native finishing registry/scaling runs complete:** 83 inherited IDs: 6 fixed, 37 improved, 39 unchanged, 1 regressed. This is not the final outcome count. Unchanged includes previously repaired behavior retained. Verdicts apply to observed paths, not every platform/parameter combination. Pending finishing proof is explicit.

| ID | Provisional verdict vs round four | Observation / remaining gap | Evidence |
|---|---|---|---|
| L01 | **unchanged** | Type tiles remain readable; no step indicator and field-page scrolling remain. | [scope](screenshots/shell-types.png) |
| L02 | **unchanged** | Pristine Untitled dataset and no welcome modal retained. | [scope](screenshots/design-00-review1-start-before-check.png) |
| L03 | **improved** | Canonical CSV/template headers use actual arm names and readable field names. | [scope](screenshots/shell-csv-entry.png) |
| L04 | **improved** | Entered-effect identity now travels in editable standalone context; dedicated units remain absent. | [scope](screenshots/matrix-generic-effect-standard-figure.png) |
| L05 | **improved** | Required outcome and optional meaningful arm-name fields improve the final naming step. | [scope](screenshots/arms-custom-wizard.png) |
| L06 | **improved** | Integer count preview and named headers improve import; all dialect/filesystem faults unqualified. | [scope](screenshots/shell-csv-entry.png) |
| G01 | **unchanged** | Linux grid is readable; old persisted Windows width trigger remains unqualified. | [scope](screenshots/design-08-round5-grid-cues.png) |
| G02 | **improved** | Neutral Group/Index test defaults and actual calculator names reduce decoding; the metric submenu still leaks TX Mean (R5-09). | [scope](OUTCOMES.json) |
| G03 | **improved** | Calculator glyphs and italic derived values add non-colour cues; assistive-tech qualification remains open. | [scope](screenshots/design-08-round5-grid-cues.png) |
| G04 | **fixed** | Named navigation retained and metadata spacing now reads Follow-up: first consistently. | [scope](screenshots/design-08-round5-grid-cues.png) |
| G05 | **improved** | Actual clinical arm names replace opaque defaults across inspected grid/calculator/output paths. | [scope](screenshots/arms-custom-wizard.png) |
| G06 | **unchanged** | Readable diagnostic input/CI fields retained; exact leading zeros visible in fresh native edit preview. | [scope](screenshots/calculator-diagnostic-readable-ci.png) |
| G07 | **improved** | Names and compact controls improve data entry; scaled/native finishing evidence is still pending. | [scope](OUTCOMES.json) |
| G08 | **unchanged** | Numeric/Category wording and separated destructive actions retained. | [scope](screenshots/shell-structure.png) |
| M01 | **improved** | A labelled Analyses group gives analysis actions one recognition rule; minor case remnants persist. | [scope](screenshots/design-12-round5-analysis-prerequisite-tooltip.png) |
| M02 | **fixed** | Missing recent files expose Locate/Remove and recover to real project entries. | [scope](screenshots/design-01-round5-recent-missing.png) |
| M03 | **improved** | Actual disabled subgroup prerequisite tooltip works within the labelled analysis menu. | [scope](screenshots/design-12-round5-analysis-prerequisite-tooltip.png) |
| M04 | **unchanged** | Structure tabs remain a dense three-pane editor; actual arm names are readable. | [scope](screenshots/shell-structure.png) |
| S01 | **unchanged** | Separate report/figure zoom and scoped confidence controls retained. | [scope](screenshots/design-18-review1-report-tables.png) |
| D01 | **improved** | Pinned actions and named controls retained; native Qt 1.25/1.5/2.0 design runs passed (application scaling only). | [scope](OUTCOMES.json) |
| D02 | **improved** | Context uses actual names and readable metric; repetitive method description remains. | [scope](screenshots/design-14-round5-keyboard-setup-page-0.png) |
| D03 | **improved** | Editable context and actual group headings improve setup/editing; hex colour fields and long forms remain. | [scope](screenshots/design-14-round5-keyboard-setup-page-0.png) |
| D04 | **unchanged** | Recoverable errors retained; inline small-study validation/progress finishing remains incomplete. | [scope](EXTRA.json) |
| D05 | **unchanged** | Existing corrections and eligibility retained; universal affected-study accounting remains incomplete. | [scope](screenshots/design-14-round5-keyboard-setup-page-0.png) |
| R01 | **improved** | Duplicate report headings and scene paragraphs are reduced; raw model vocabulary still leaks (R5-05). | [scope](screenshots/matrix-twoarm-proportion-standard-report.png) |
| R02 | **fixed** | Existing outcome/comparison/follow-up identity is in editable standalone captions; IRR exposure is explicit. | [scope](screenshots/matrix-irr-standard-figure.png) |
| R03 | **improved** | One weights presentation and readable growing figures improve Results; R5-04/R5-06 need repair. | [scope](screenshots/design-18-review1-report-tables.png) |
| R04 | **unchanged** | Previously fixed sequential reference bounds retained on inspected paths. | [scope](screenshots/matrix-onearm-mean-cumulative-figure.png) |
| R05 | **unchanged** | Original coefficient Fixture 2 lower bound remains zero; tiny-effect protection retained. | [scope](screenshots/matrix-reg-coef-standard-figure.png) |
| R06 | **unchanged** | Study added (k) and sequence/display-order guidance retained. | [scope](screenshots/matrix-onearm-mean-cumulative-figure.png) |
| R07 | **unchanged** | HR/IRR omitted-study identity and visible row intervals remain aligned. | [scope](screenshots/matrix-irr-leave-one-out-figure.png) |
| R08 | **improved** | Structured subgroup results/test/PI replace remaining HR/IRR package prose; SE scale remains implicit. | [scope](screenshots/matrix-irr-subgroup-report.png) |
| R09 | **improved** | Bubble guides are panel-bounded; standalone context helps, but study identity/units remain limited. | [scope](screenshots/matrix-onearm-proportion-meta-regression-figure.png) |
| R10 | **unchanged** | Single-arm proportion's actual tested null remains explicit. | [scope](screenshots/matrix-onearm-proportion-standard-figure.png) |
| R11 | **improved** | Mean caption carries investigator context and can state units; no dedicated unit field. | [scope](screenshots/matrix-onearm-mean-standard-figure.png) |
| R12 | **improved** | Coefficient/entered-effect standalone context added; duplicate coefficient phrase is R5-02. | [scope](screenshots/matrix-reg-coef-standard-figure.png) |
| R13 | **improved** | Actual arm names clarify comparative interpretation without invented clinical conclusions. | [scope](screenshots/matrix-twoarm-proportion-standard-report.png) |
| R14 | **improved** | MD/SMD subtraction explicitly names Intervention minus Control; existing scale guidance retained. | [scope](screenshots/matrix-twoarm-mean-standard-report.png) |
| R15 | **improved** | Diagnostic component headings and separators are calmer and clinical-first; regression tables lag. | [scope](screenshots/matrix-diagnostic-standard-report.png) |
| R16 | **unchanged** | Diagnostic contrast/reference identities retained; precision and raw labels remain (R5-03/R5-05). | [scope](screenshots/matrix-diagnostic-meta-regression-report.png) |
| R17 | **regressed** | Long HR type is larger, but default subgroup CI caps now span 1.41 rows and overlap adjacent studies (R5-04). | [scope](screenshots/matrix-hr-subgroup-figure.png) |
| R18 | **fixed** | IRR actual arms, catheter-day exposure, raw columns and independently checked totals are explicit. | [scope](screenshots/matrix-irr-standard-figure.png) |
| R19 | **unchanged** | Existing small-study cautions/eligibility retained; no universal asymmetry-oracle claim. | [scope](EXTRA.json) |
| E01 | **improved** | Standalone context improves exports; complete fresh four-format editor qualification is pending registry. | [scope](OUTCOMES.json) |
| E02 | **unchanged** | Clean/dirty state, save/reopen and unchanged original sample archives retained. | [scope](screenshots/design-08-round5-grid-cues.png) |
| H01 | **improved** | Quick start explains naming, existing legacy names, row calculators and output tools. | [scope](screenshots/shell-quick-start.png) |
| X01 | **unchanged** | Blank/duplicate validation remains recoverable; arm duplicates now have explicit inline feedback. | [scope](screenshots/arms-custom-wizard.png) |
| X02 | **unchanged** | Local covariate empty-state guidance remains; broader contextual workflow help is modest. | [scope](screenshots/shell-structure.png) |
| A01 | **improved** | Named controls and selectable tables improve access; no screen-reader qualification. | [scope](screenshots/design-18-review1-report-tables.png) |
| A02 | **improved** | Non-colour calculator/derived-cell cues added; measured contrast/high-contrast qualification remains open. | [scope](screenshots/design-08-round5-grid-cues.png) |
| A03 | **improved** | Readable growing figures improve access; long-cap regression and OS/scaling limits remain explicit. | [scope](screenshots/matrix-hr-subgroup-figure.png) |
| A04 | **fixed** | Consistent labelled Analyses group replaces the mixed labelled/icon-only analysis toolbar. | [scope](screenshots/design-12-round5-analysis-prerequisite-tooltip.png) |
| A05 | **improved** | Actual Tab/arrow/Escape paths run for workspace/setup/results; full no-mouse and assistive-tech scope remains open. | [scope](DESIGN.json) |
| RG01 | **improved** | Clinical diagnostic report gains simpler component hierarchy; moderator-output finishing remains. | [scope](screenshots/matrix-diagnostic-standard-report.png) |
| RG02 | **unchanged** | Independent report/figure zoom retained; Fit width remains figure-scoped. | [scope](screenshots/design-18-review1-report-tables.png) |
| RG03 | **unchanged** | Diagnostic shared notes precede components and executed-method identity remains intact. | [scope](screenshots/matrix-diagnostic-standard-report.png) |
| RG04 | **unchanged** | CSV guidance stays outside the scrolling field area. | [scope](screenshots/shell-csv-entry.png) |
| N01 | **unchanged** | Prior contextual BMJ coefficient identity is retained at six digits; new long-name header defect is separate. | [scope](screenshots/bmj-coefficient-six-digits.png) |
| N02 | **unchanged** | Diagnostic moderator/contrast names retained; all long-label/reference permutations unqualified. | [scope](screenshots/matrix-diagnostic-meta-regression-report.png) |
| N03 | **fixed** | Previously bounded sequential guides/round ticks now joined by clipped bubble guides on inspected paths. | [scope](screenshots/matrix-onearm-proportion-meta-regression-figure.png) |
| N04 | **improved** | Calmer structured reports replace HR/IRR subgroup prose; raw labels/SE-scale finishing remain. | [scope](screenshots/matrix-irr-subgroup-report.png) |
| N05 | **unchanged** | Existing subgroup-difference tests are present in figures and reports. | [scope](screenshots/matrix-irr-subgroup-report.png) |
| N06 | **unchanged** | Report identity and tab-separated export rows remain intact. | [scope](OUTCOMES.json) |
| N07 | **unchanged** | HR/IRR cumulative/omission study labels and intervals remain correct on inspected rows. | [scope](screenshots/matrix-irr-leave-one-out-figure.png) |
| N08 | **improved** | Actual arm names improve calculator labels; persisted Windows-width case remains unqualified. | [scope](OUTCOMES.json) |
| N09 | **improved** | Existing named dimension navigation gains consistent metadata spacing. | [scope](screenshots/design-08-round5-grid-cues.png) |
| N10 | **improved** | Actual defaults, Automatic and sentence-case controls improve language; R5-05/R5-09 and minor case remnants remain. | [scope](screenshots/arms-custom-wizard.png) |
| N11 | **unchanged** | Diagnostic estimate/CI leading digits remain visible in fresh native edit preview; persistence assertions passed. | [scope](screenshots/calculator-diagnostic-readable-ci.png) |
| R2-01 | **unchanged** | Previously repaired HR/IRR omission identities remain correct. | [scope](screenshots/matrix-irr-leave-one-out-figure.png) |
| R2-02 | **unchanged** | Copy/export retains executed identity and matches saved bytes. | [scope](OUTCOMES.json) |
| R2-03 | **unchanged** | Structured table exports remain tab-separated, not one-cell-per-line text. | [scope](OUTCOMES.json) |
| F01 | **unchanged** | Fixed-model inactive tau-squared omission retained; fresh fixed-IV figure/report agree on estimate, CI and heterogeneity. | [scope](screenshots/fixed-iv-footer.png) / [report](screenshots/fixed-iv-report.png) |
| F02 | **unchanged** | Applicable executed methods and fitted references retained. | [scope](screenshots/matrix-twoarm-proportion-standard-report.png) |
| F03 | **improved** | HR/IRR subgroup tables now remove legacy prose while retaining tests and prediction intervals. | [scope](screenshots/matrix-irr-subgroup-report.png) |
| F04 | **improved** | MD negative zero is repaired; diagnostic regression ignores selected precision and tiny Qm differs across views. | [scope](screenshots/matrix-twoarm-mean-meta-regression-report.png) |
| F05 | **unchanged** | Prior comparative test and named actual-null presentation retained. | [scope](screenshots/matrix-onearm-proportion-standard-figure.png) |
| F06 | **improved** | Actual calculator arm names and integer count previews improve the existing compact modes. | [scope](OUTCOMES.json) |
| F07 | **improved** | Navigator separators, naming/help and many controls improve; title-case/raw report remnants remain. | [scope](screenshots/shell-quick-start.png) |
| F08 | **unchanged** | Prior BMJ coefficient/entered-effect identity retained at six digits; three-style presentation/export sweeps passed. | [scope](screenshots/bmj-entered-effect-six-digits.png) |
| F09 | **unchanged** | Prior short-label numerical annotation clearance retained; new BMJ wrapped-name collision is R5-06. | [scope](OUTCOMES.json) |
| F10 | **unchanged** | IRR duplicate-author subgroup rows retain distinct identities and overall weights. | [scope](screenshots/matrix-irr-standard-figure.png) |
| R3-01 | **unchanged** | Sequential null guide stays within study rows clear of the footer. | [scope](screenshots/matrix-onearm-mean-cumulative-figure.png) |
| R3-02 | **unchanged** | Round linear bubble ticks and title clearance remain readable. | [scope](screenshots/matrix-onearm-proportion-meta-regression-figure.png) |

The five additional round-four findings are tracked separately:

| ID | Provisional verdict | Observation / scope | Evidence |
|---|---|---|---|
| F11 | **fixed** | Exterior bubble guide removed; fresh 18-case metric/explicit-bound geometry sweep passed; decoded editor exports are separately recorded. | [bubble](screenshots/matrix-onearm-proportion-meta-regression-figure.png) |
| F12 | **fixed** | Legacy scene weights removed; report/Tables retain structured rows and existing component identities. | [figure](screenshots/matrix-twoarm-proportion-standard-figure.png) / [report](screenshots/matrix-onearm-proportion-standard-report.png) |
| F13 | **fixed** | Content-sized cards and Locate/Remove recovery; fresh native Qt 1.25/1.5/2.0 design runs passed. | [start](screenshots/design-00-review1-start-before-check.png) / [recovery](screenshots/design-01-round5-recent-missing.png) |
| F14 | **fixed** | Labelled Analyses group and actual prerequisite tooltip. | [toolbar](screenshots/design-12-round5-analysis-prerequisite-tooltip.png) |
| F15 | **fixed** | Navigator/results label/value spacing is consistent. | [grid](screenshots/design-08-round5-grid-cues.png) |

## 3. Regressions and the round-five claims

**One confirmed presentation regression: R5-04.** No wrong fitted estimate/CI or confirmed new functional regression has been established on exercised paths. The fresh 18-case bubble sweep passed displayed/production geometry checks across 16 metrics, including explicit bounds. Visually inspected [proportion](screenshots/bubble-explicit-proportion.png) and [IRR](screenshots/bubble-explicit-irr.png) examples support F11; four-format editor qualification remains independently bounded by completed runs.

Early binary standard evidence: [figure](screenshots/matrix-twoarm-proportion-standard-figure.png) and [report](screenshots/matrix-twoarm-proportion-standard-report.png) agree on OR 0.761368, 95% CI 0.458516–1.264253, P 0.292012. Intervention/Control names are readable. Duplicate scene weights are absent; standalone context is present. All 50 first figure/report pairs have now been inspected; the arm/context and weights improvements hold on those paths. The shared precision claim remains incomplete (R5-03), and long subgroup marks regress (R5-04).

## 4. New and remaining findings

### R5-01 — Medium: transformed-effect tables leave the standard-error scale implicit

The [OR subgroup table](screenshots/matrix-twoarm-proportion-subgroup-report.png) puts clinical OR 0.746519 beside “Std. error” 0.375206. The estimate/CI are exponentiated; the SE remains on the fitted log scale (`results_display.R`, sequential/subgroup formatters). Sequential rows do the same. The [diagnostic cumulative table](screenshots/matrix-diagnostic-cumulative-report.png) similarly pairs sensitivity 0.632248 with fitted logit-scale SE 0.145264 under the same bare label. A reader copying the table can mistake that number for an SE of the displayed OR. The [round-four counterpart](../2026-10-15-round4-reaudit/screenshots/matrix-twoarm-proportion-subgroup-report.png) already has this label: **pre-existing, not a round-five regression**. No wrong fitted value is alleged.

**Principle:** a quantity's scale belongs with its label. **Recommendation:** label the existing column “SE (log OR)” / corresponding HR, IRR or transformed metric, and logit sensitivity/specificity where applicable, or add a concise table-local scale note shared by Text, Tables, copy and exports. Preserve existing fitted values and clinical CIs. Regression coefficient tables already explicitly name their log scale.


### R5-02 — Low: the new caption repeats the same identity

The [coefficient figure](screenshots/matrix-reg-coef-standard-figure.png) reads “Regression coefficient · Regression coefficient”. The workspace identity already repeated type and metric; round five carries that duplication into standalone output. “Group: Group” adds little context when defaults are unchanged, and “Follow-up: first” still exposes a container default rather than a clinical time point. The caption itself is a substantial improvement; this is a new copy remnant, not a claim that the old captionless output was better.

**Principle:** every identity fragment should add information. **Recommendation:** collapse identical adjacent type/metric labels in the default caption and preserve investigator-authored captions verbatim. Retain actual outcome, arm and follow-up identity. Avoid adding uninformative generated defaults to a new caption; offer the existing caption editor to state the clinical time point, while preserving stored researcher labels verbatim.

Remaining F04 precision detail: the [MD regression report](screenshots/matrix-twoarm-mean-meta-regression-report.png) now prints slope/Z as zero, closing the observed negative-zero case. The [MD subgroup table](screenshots/matrix-twoarm-mean-subgroup-report.png) still prints Qm `1.428745e-31` while its figure uses `0.000000`; round four exported the identical tiny statistic. This is presentation consistency, not a numerical regression. Prefer the selected decimal policy for test statistics, retaining the separate protection for genuinely tiny effects/intervals.

### R5-03 — Medium: diagnostic meta-regression bypasses selected output precision

The [native diagnostic moderator report](screenshots/matrix-diagnostic-meta-regression-report.png) shows likelihood-ratio statistic `3.802`, P `0.149`, sensitivity coefficient `-0.03388`, CI `-0.2018` to `0.134`, and odds ratio `0.9667`. The actual configured/reopened method parameters in `raw/matrix-diagnostic/steps.jsonl`, step 71, record `digits: 6`. Its residual I² block does use six decimals, while coefficient/test data frames use package-style significant digits. The exported text retains the inconsistency. The round-four exported report contains the same strings: **pre-existing, not a new regression**. Thus the round-five “single precision policy” claim is incomplete for this existing analysis.

**Principle:** a visible presentation setting must govern the whole output. **Recommendation:** render the existing numeric diagnostic regression coefficient/ML-test tables through the shared presentation policy, preserving raw fitted numbers and existing inference. Normalize `moderator`, `statistic`, `Std Error`, `p-value` into readable, consistently cased headings and explicitly distinguish modeled-scale coefficients from odds ratios. No new statistical quantity is needed.

### R5-04 — Medium regression: long subgroup CI end caps overlap adjacent rows

The [fresh 65-study default subgroup forest](screenshots/matrix-hr-subgroup-figure.png) has oversized vertical CI caps that cross neighboring row bands, producing a picket-fence cluster around the near-null HRs. Text/row height improved, but interval tracking became worse. The [round-four same-sample counterpart](../2026-10-15-round4-reaudit/screenshots/matrix-hr-subgroup-figure.png) has much shorter caps.

[SVG geometry](HR-CAP-GEOMETRY.json) measures cap height about 33.22 pt against 23.54 pt row spacing (1.41 rows), versus about 14.61/14.42 pt (1.01 rows) before. These are vector geometry measurements, independent of window zoom; they explain the visible overlap. This is a confirmed round-five presentation regression, not changed CI endpoints or fitted values.

**Principle:** each study's marks must stay visually associated with its row. **Recommendation:** bound CI cap height by actual study-row spacing in the existing default renderer; check short/65-study standard and subgroup figures and their exports. Keep horizontal endpoints, weights and estimates unchanged. This needs the same row-aware treatment already applied to pooled diamonds. Additional inspected [default standard](screenshots/long-default-standard.png), [RevMan subgroup](screenshots/long-revman-subgroup-footer.png) and [BMJ subgroup](screenshots/long-bmj-subgroup-footer.png) frames also show over-tall caps; [RevMan standard](screenshots/long-revman-standard-footer.png) and [BMJ standard](screenshots/long-bmj-standard.png) are cleaner. Only the default subgroup has the measured same-input round-four comparison.

### R5-05 — Low: raw model and validation vocabulary survives

The [IRR moderator report](screenshots/matrix-irr-meta-regression-report.png) labels the main coefficient “Intercept” but reverts to `intrcpt` in its exponentiated-coefficient table; HR does the same. The [diagnostic regression report](screenshots/matrix-diagnostic-meta-regression-report.png) exposes lowercase `moderator` / `statistic`, and diagnostic navigation retains “Sens Forest Plot” / “Spec Forest Plot” beside full-name reports. The [native diagnostic calculator](screenshots/calculator-diagnostic-readable-ci.png) likewise displays metric “Sens” in a wide selector that could show Sensitivity. `DTA` is still the raw-count superheading instead of the actual index-test name. These are pre-existing remnants, not round-five regressions; actual user-supplied covariate names must remain intact. The continuous calculator source additionally returns “pval must be between 0 and 1” and interpolates lowercase se/var/pval into “cannot be negative” warnings, then passes them to QMessageBox.warning. [Source/sink trace](VALIDATION-COPY.json) confirms the copy; those exact invalid-field gestures were not separately captured natively.

**Principle:** users should recognize one concept by one clear name. **Recommendation:** normalize package-owned row/column/navigation labels at the display boundary (Intercept, Moderator, Test statistic, Sensitivity/Specificity; actual test name for the count block). For calculator validation, use the existing readable table heading rather than an internal field key. Leave internal keys and stored researcher names alone. This finishes existing output rather than extending analyses.

### R5-06 — Medium: BMJ count-header rule crosses a wrapped actual arm name

The [BMJ long-name figure](screenshots/long-arm-bmj-matrix-twoarm-proportion-standard-figure.png) uses “Cognitive behavioural therapy plus usual care” and “Usual care alone”. The first name wraps to two lines, but the count-header underline crosses “Cognitive behavioural”. [Default](screenshots/long-arm-default-matrix-twoarm-proportion-standard-figure.png) and [RevMan](screenshots/long-arm-revman-matrix-twoarm-proportion-standard-figure.png) wrap the same supplied names cleanly. All three drives passed their numerical/report assertions, illustrating why rendering success is insufficient aesthetic proof.

[Vector/font geometry](BMJ-LONG-HEADER.json) confirms the rule at y=66.62 lies within the first line's glyph ink bounds. The actual names are preserved and report/figure estimates still agree; this is a header-clearance defect. There is no same-input round-four replay, so its introduction date is unqualified rather than called a confirmed regression.

**Principle:** meaningful clinical names must be first-class layout inputs. **Recommendation:** position BMJ's count superheading/rule using the measured full wrapped name block and the existing clearance policy; preserve the user names and column meanings. Check unequal one/two/four-line group names in default/RevMan/BMJ and exported figures, without shortening investigator text silently.

### R5-07 — Low: small-study preview gives the wrong unavailability reason

The [nine-study IRR setup](screenshots/extra-irr-invalid-contour-recoverable.png) says “No formal asymmetry test is available for this effect measure.” Its actual completed report says Classical Egger requires at least ten usable studies and nine were available; the method-detail rows likewise say disabled below ten. The preview is confusing study-count eligibility with an unsupported measure. The same fallback string exists at the round-four audit revision `f1aa24d`: **pre-existing, not a round-five regression**.

**Principle:** a disabled or unavailable action should explain the actual prerequisite. **Recommendation:** reuse the existing eligibility report's method reasons in the preview (“At least 10 usable studies are required; 9 available”), retaining descriptive funnels and all current eligibility rules. Do not change thresholds or add procedures.

### R5-08 — Low: subgroup style choices silently use the default layout

The inspected [RevMan subgroup](screenshots/long-revman-subgroup-footer.png) and [BMJ subgroup](screenshots/long-bmj-subgroup-footer.png) share the default subgroup layout, with their accent differences, rather than the respective standard-forest column arrangements seen in [RevMan standard](screenshots/long-revman-standard-footer.png) and [BMJ standard](screenshots/long-bmj-standard.png). The actual style choice survives in parameters; the renderer silently falls back. [Current and round-four source excerpts](STYLE-FALLBACK.json) confirm this is **pre-existing**, not a new regression. Fitted subgroup estimates/tests are unaffected.

**Principle:** a selected presentation option should describe the output actually produced. **Recommendation:** make the existing subgroup selector label/explanation accurately describe its supported default-layout variants and accent colours. If the existing RevMan/BMJ layout is extended to subgroup rows later, qualify its count/weight/header/footer layout with realistic names and long groups. No additional statistical method is needed.

### R5-09 — Medium: a reachable metric submenu still displays “TX Mean: Mean”

In a fresh single-arm-mean dataset, **Analysis → Effect-size tools → One-arm metrics** visibly shows the checked action **“TX Mean: Mean”**; [actual native three-level popup](screenshots/metric-menu-visible-tx-mean.png). The grid correctly says Mean. The [attached-menu inventory](REACHABLE-MENUS.json) also records this action on coefficient, entered-effect, MD and SMD routes. Unlike legacy researcher arm names, this is current built-in interface text. Thus round five's “every visible Tx/TX label replaced” claim is incomplete.

The main-window action builder concatenates the internal metric key with its readable name; the literal Tx grep did not find that expression. [Source and round-four inventory comparison](TX-MENU-SOURCE.json) shows it is **pre-existing**, not a new regression. The final broader sweep’s 163 core source locations are individually classified, with three additional display-path hits (166 total), including this dynamic construction in [LABEL-INVENTORY](LABEL-INVENTORY.json). Walking only attached menus avoids mistaking stale QMenu children for visible options.

**Principle:** internal identifiers belong behind the interface; acceptance claims must include reachable nested menus. **Recommendation:** format this action using the existing contextual Mean/Coefficient/Entered effect display identity, without the internal `TX Mean` prefix. Keep the stored metric key and user arm names unchanged. Verify the reachable menu after each continuous-family open/create path, as well as wizard, calculator, CSV, report and figure labels.

### R5-10 — Low: the continuous calculator presents a tiny derived probability as zero

The [native Group summaries calculator](screenshots/calculator-group-summary-tiny-p.png) shows Intervention N60, mean95.5, SD22 and a derived `p-value` of `0.0`. The existing R calculation is a two-sided normal group-mean test against zero. Repeating its formula independently in pinned base R yields **7.3479476072438575e-248**, a finite positive number; [inputs, exact command/result and source hashes](CALCULATOR-TINY-P.json). The UI rounds numeric cells to four decimals before converting them to text. The same expression exists at the round-four revision: **pre-existing**, not a round-five numerical regression. The SMD/CI and saved raw summaries are unaffected.

**Principle:** very small is different from exactly zero, including calculator previews. **Recommendation:** retain the unrounded numeric value and display scientific notation for positive derived probabilities that would round to zero, with a concise explanation of the existing tested null. Keep editable numeric values, inputs and the existing procedure unchanged. Qualify this existing calculator formatter alongside the analysis precision work; a consistent analysis report alone does not close every numeric surface.

## 5. Microcopy and information design

The [actual optional-name wizard](screenshots/arms-custom-wizard.png) accepts full clinical names; [duplicate names](screenshots/arms-duplicate-rejected.png) are rejected inline after whitespace normalization. [Blank optional names](screenshots/arms-blank-defaults.png) use Intervention/Control; [calculator](screenshots/arms-default-calculator.png), [canonical CSV mapping](screenshots/arms-current-csv-map.png) and [legacy-header mapping](screenshots/arms-legacy-csv-map.png) use the same readable fields. [Legacy user-project names](screenshots/arms-legacy-preserved.png) remain exactly tx A/tx B, as required. The fresh 175-step arm-name scenario passed, including report/copy/export and three styles. Native start/recent/Analyses/CSV/structure/help frames are inspected: [start](screenshots/design-00-review1-start-before-check.png), [missing recovery controls](screenshots/design-01-round5-recent-missing.png), [recovered list](screenshots/design-02-round5-recent-recovered.png), [actual disabled-action tooltip](screenshots/design-12-round5-analysis-prerequisite-tooltip.png), [CSV entry](screenshots/shell-csv-entry.png), [Quick start](screenshots/shell-quick-start.png). F13, F14 and F15 are fixed on these paths. The [grid](screenshots/design-08-round5-grid-cues.png) has Intervention/Control, calculator glyphs and italic derived values as non-colour cues. The 171 native header/study/method states were visually reviewed in [contact sheets](OPTIONS-CONTACTS.json), alongside exact control/choice inventories. The existing “Binary” method family in single-arm proportion and “Continuous” family in coefficient/entered-effect setups still asks the user to translate package taxonomy; prefer metric-specific display identity using the existing selection. IRR Mantel–Haenszel also reuses a generic log-hazard/rate description; describe the selected existing method precisely. Some offscreen header-coordinate samples repeat adjacent menus, so these alone do not prove every individual column gesture. The group-summary calculator still reserves substantial vertical whitespace around its small table; content-size the active panel while retaining its pinned actions. Remaining minor copy debt includes Open Recent/Follow-Ups/Treatment Groups title case and Yes/No dirty-prompt actions; explicit Save/Discard action labels would scan faster. These are polish opportunities, not new functional failures.

The real exported UTF-8 report was opened in [native xedit](screenshots/shell-exported-report-editor.png). Its content/numbers agree with copied output; xedit misrenders some Unicode characters on this host. This editor limitation is also documented in round four and is not evidence of corrupted export bytes. Native Gtk template Save picker was actually driven; other helper picker substitutions do not qualify all OS picker routes.

## 6. Coverage matrix

The independent public-package authority sweep passed 91/91; [receipt](AUTHORITIES.json). All ten families × five workflows passed; every first figure/report pair is visually inspected in [MATRIX](MATRIX.md). Completed runs below are fresh Linux native runs. The remaining registry/scaling finish is explicitly pending, rather than inferred from round-five claims.

| Area | Exercised / inspected | Scope and limits |
|---|---|---|
| Runtime | Native doctor; R4.6.1; current-source/install receipts |55 source / 24 installed hashes; no system-library modification. |
| Start and recents | Light/dark start; missing-file Locate cancel/relocation/same-path recovery/Remove | Content-sized cards; fresh Qt 1.25/1.5/2.0 runs passed. |
| Menus and toolbar | Recursive actual menus/submenus and tooltips, enabled/disabled states; labelled Analyses and prerequisite tooltip | [Attached trees for all ten families](REACHABLE-MENUS.json), exact text/shortcuts and native nested-menu proof; not every desktop-environment mnemonic combination. |
| Creation and CSV | All ten type paths in matrix; optional blank/custom/duplicate arm names; new/legacy CSV header mapping, templates and preview | Native Gtk Save template picker actually driven; other pickers are test-owned substitutions. Dialect/filesystem fault combinations not universal. |
| Grid and structure | Ten-family data, context/menu inventories, 171 states; inclusion/covariates; structure tabs/settings; Save As/recent reopen | Some offscreen header-coordinate samples repeat adjacent menus; do not infer every individual column gesture from the inventory. |
| Samples | All 7 bundled archives opened/analyzed/saved/reopened; 14 figure/report images inspected | Original bytes unchanged. BCG 13/13 rows agree with original pinned data; readable names preserved. [Proof](SAMPLE-NATIVE.json), [source comparison](BCG-SOURCE.json). |
| Core analysis | 50 cells: 10 families × standard/cumulative/leave-one-out/subgroup/meta-regression | Each first figure/report pair inspected; selected endpoint/pooled/statistic agreement recorded. Not every cell of every long table manually transcribed. |
| Diagnostics and small-study | Joint Reitsma SROC, combined metrics, moderator shapes; extended binary/continuous and diagnostic Deeks; IRR contour error/recovery | Existing procedures only. Dedicated remaining maintained variants are finishing; no new statistical method recommended. |
| Results | Text, selectable Tables, copy/export identity, zoom/Fit width, Change settings/rerun; no legacy scene weights | Real UTF-8 export opened in native xedit; host editor Unicode limitation retained. |
| Figure presentation | Three long-figure styles, three realistic-name styles; editable standalone context; 18 bubble metric/bound cases; IRR exposure/totals | Some collisions are real findings despite passing render assertions. All four export-format/editor finishing remains separately enumerated by run. |
| Help and states | Both Help actions: Quick start/shortcuts and About/licenses; empty start/grid/covariates; duplicate-name/invalid-contour recoveries | No documentation claim substitutes for interaction. Dirty Open Cancel/Yes/No and cancelled Save As all driven; saved/reopened and preservation assertions passed. |
| Access and scale | Native Tab/arrow/Escape for main/setup/results, named controls and non-colour grid cues | Calculator traversal, complete loaded-project keyboard task and Qt 1.25/1.5/2 scale runs passed; complete keyboard continuation still finishing. No screen-reader/OS-DPI/cross-platform qualification. |

[OUTCOMES](OUTCOMES.json) binds exact commands, observed exit statuses, logs and helper manifest/artifact hashes; [INSPECTIONS](INSPECTIONS.json) records visual observations. Inventoried choices are not equivalent to every possible value combination being executed.

## 7. Accessibility

Fresh native Tab/arrow/Escape traversal passed for the workspace, both setup pages and Results table/selector/sidebar; focus sequences are retained in [DESIGN](DESIGN.json). [Grid cues](screenshots/design-08-round5-grid-cues.png) show calculator glyphs and italic derived values as well as gold colour. The labelled Analyses control has real prerequisite tooltips, and the selectable Results table has a meaningful accessible name. Empty accessibleName properties alone are not treated as defects: labelled Qt controls may derive their names through buddy/label relations.

Fresh native design runs passed at QT_SCALE_FACTOR=1.25, 1.5 and 2.0; [scale receipts and sampled grid colour measurements](SCALES.json), visually inspected [1.25 start](screenshots/scale125-start.png), [1.5 start](screenshots/scale15-start.png), [1.5 setup](screenshots/scale15-setup.png), [2.0 start](screenshots/scale20-start.png) and [2.0 setup](screenshots/scale20-setup.png). The derived-cell normal and selection foreground/background pairs measured at least 4.5:1 on these captured palettes; that is a sampled check, not every application colour or a high-contrast theme. The complete loaded-project keyboard task passed through Tab/Control-Tab → Analyses → Space/arrows → Meta-analysis → Enter → report/copy/export shortcuts. [Focus](screenshots/keyboard-toolbar-focus.png), [menu](screenshots/keyboard-analysis-menu.png), [report](screenshots/keyboard-report-copied-exported.png), and [assertion/artifact summary](GUARD-SUMMARY.json) record it. Save/Discard/cancelled Save As also passed; [cancelled-save preservation](screenshots/guard-save-as-cancel-preserved.png). Two earlier driver assumptions (F10 and Home/Down) failed and remain verbatim in FAILURES; the final replay passed without application changes. Calculator-mode traversal is still finishing. These are application-level Qt scale checks, not actual OS display-scaling or screen-reader qualification. The loaded-project task uses no initial widget focus assignment; arbitrary whole-application tasks from process launch, Orca/AT-SPI relationships, high contrast, measured contrast, multi-monitor behavior and Windows/macOS remain unqualified.

## 8. Ranked round-six list (provisional until finishing runs complete)

1. **R5-09, medium acceptance gap:** remove the built-in TX Mean menu prefix using the existing contextual display identity; preserve internal keys and legacy user names.
2. **R5-04, medium regression:** bound long default/subgroup CI caps to actual row spacing; preserve horizontal intervals and fitted values.
3. **R5-06, medium:** finish BMJ header clearance using measured real arm names, including unequal wrapped lengths; check exports.
4. **R5-03 / F04, medium:** route diagnostic meta-regression coefficient and ML-test tables through selected precision, with consistent readable headings.
5. **R5-01, medium:** put fitted SE scale beside clinical-scale sequential/subgroup estimates in Text, Tables and exports.
6. **D04 / R5-07, existing medium finishing gap plus low copy defect:** use actual eligibility reasons; validate existing contour fields inline and stop busy state after failure while preserving recovery.
7. **R5-10, low:** preserve tiny positive derived calculator probabilities in readable scientific notation and explain the existing null.
8. **R5-08, low:** make subgroup style choices describe the actual supported layout; eliminate silent fallback promises.
9. **R5-05, low:** finish package-owned Intercept/Moderator/Statistic and diagnostic labels at the existing display boundary.
10. **R5-02, low:** remove identical type/metric repetitions and uninformative generated defaults from new default captions; preserve investigator text.
11. **A01/A05, qualification gap:** extend the completed loaded-project keyboard task to other entry points, focus restoration and screen-reader relationships; retain actual Qt-scale proof and OS limits.
12. **F07 / M01 / H01, low:** finish action-labelled Save/Discard prompts, case consistency, concise contextual guidance and existing plot units/identity presentation.
13. **Platform qualification:** exercise remaining native picker routes and supported packaged targets; do not promote Linux source proof into cross-platform release proof.

RCMS is substantially closer to a coherent, polished analysis workbench. Actual arm names, useful standalone context, simpler start/recovery, growing readable figures and one weights presentation improve normal work. The reachable TX Mean menu remnant means the naming mandate is not fully complete, and long actual names still expose BMJ header clearance problems. The remaining defects are visible finishing problems in existing output and honest qualification gaps, not a reason to add statistical breadth. It is not yet uniformly publication-ready: cap/header collisions and inconsistent diagnostic report precision still weaken confidence in presentation. Round six should finish those paths with realistic clinical text, then qualify access and recovery end to end.


## 9. Limits, replay and evidence inventory

Source `docs/ux-audit/2026-10-14-round3/ENV.sh` and export DISPLAY=:0. Run `uv run python scripts/verify_rcms.py doctor --native` first. Its fresh receipt is `artifacts/verification/rcms/20261015T082425Z-d75ac4d2-doctor` (exit 0). Read-only native wrappers copied from round four own settings and inputs under ignored raw/. Run exact commands through `uv run python docs/ux-audit/2026-10-16-round5-reaudit/run.py LABEL COMMAND...`. Every cited screenshot is recorded with an inspection observation and SHA-256 in [INSPECTIONS](INSPECTIONS.json). Uninspected incidental captures are retained only in ignored raw storage.

Setup attempt: shell reported `/bin/bash: line 2: python: command not found`; no writes occurred. Corrected to python3 for audit-document setup; application commands use uv run python.

Execution interruption: outer matrix shell exit 143 after four completed families; generic-effect orphan briefly overlapped design. Only recorded owned trees were terminated; overlapping partial frames are rejected and the families replayed serially. This is an audit-runner interruption, not a product failure. Native single-invocation replay is now used.
