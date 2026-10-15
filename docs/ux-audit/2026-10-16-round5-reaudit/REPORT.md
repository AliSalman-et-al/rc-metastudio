# RC MetaStudio native round-five re-audit — 16 October 2026

## 1. Executive summary

Round five substantially improves ordinary work: readable default arm names, optional wizard names, useful standalone figure context, one weights presentation, calmer reports, a clearer Analyses control and recoverable recent projects. **The most serious finding is R5-10: a valid calculator SD 0.00001 becomes0.0 and remains zero after Save/reopen.** A legal editable-cell keyboard replay confirmed stored data loss. Its responsible code matches round four, so this is a newly discovered pre-existing defect, not a confirmed round-five regression.

**Against round four:83 tracked IDs —6 fixed,37 improved,39 unchanged,1 regressed. F11–F15 —5 fixed. Combined 88 items —11 fixed,37 improved,39 unchanged,1 regressed.** There are **11 new R5 findings:1 high,6 medium,4 low**. The one confirmed round-five regression is oversized long-forest CI caps (R5-04). The visible `TX Mean: Mean` submenu means the all-visible-Tx naming claim remains incomplete; legacy user names are correctly preserved.

The 50-cell native matrix completed, with all 100 first figure/report images visually inspected; independent authority comparisons passed 91/91. All 112 maintained native scenarios were attempted:111 passed; `project-shell` failed two immediate native-window-state assertions. An independent bounded drive confirmed correct settled Qt/native WM states and existing shell/guard transactions passed separately. Three Qt scales, the complete loaded-project keyboard task,12 calculator modes,11 editor workflows/four export formats and targeted 1.5-scale calculator/editor checks completed. Successful observational probes are not UX passes: they exposed the data-loss and legend defects.

This independent read-and-report audit began at `ddeef0a` on `ux/audit-improvements`. Only audit documents/scripts/screenshots and HANDOFF changed. Native doctor passed with DISPLAY=:0/xcb, pinned R 4.6.1 and the test-owned library; all 55 source and24 installed receipt hashes match [current bytes](SOURCE-INTEGRITY.json). The requested folder/date is 16 October; actual host/run timestamps are 15 October UTC. Coverage and limits below do not claim every possible value combination, platform or assistive technology is qualified.

## 2. Scorecard and independent verification

**Final comparative verdicts:**83 inherited IDs:6 fixed,37 improved,39 unchanged,1 regressed. The separate F11–F15 table adds5 fixed. Fixed closes the observed issue; improved closes part; unchanged includes previously repaired behavior retained; regressed requires observed worse behavior. A newly discovered pre-existing defect does not automatically make comparative behavior regressed. [Machine-readable scorecard](SCORECARD.json).

| ID | Verdict vs round four | Observation / remaining gap | Evidence |
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
| G07 | **improved** | Names and mode-specific controls improve entry; scale 1.5 pre/post fits, but whitespace/long-field and R5-10 data-loss gaps remain. | [scope](OUTCOMES.json) |
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
| R09 | **improved** | Bubble guides are panel-bounded; context helps, but hidden-band legend mismatch remains (R5-11). | [scope](screenshots/matrix-onearm-proportion-meta-regression-figure.png) |
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
| E01 | **improved** | Standalone context improves exports;11 fresh editor workflows/four decoded export formats passed; layout/legend findings remain. | [scope](OUTCOMES.json) |
| E02 | **unchanged** | Clean/dirty guards and original sample bytes retained; R5-10 exposes pre-existing calculator data loss before saving. | [scope](screenshots/design-08-round5-grid-cues.png) |
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
| N11 | **unchanged** | Regular diagnostic CI digits remain visible; long back-calculated strings still scroll away leading digits. | [regular](screenshots/calculator-diagnostic-readable-ci.png) / [back-calculated](screenshots/calculator-contact-01.png) |
| R2-01 | **unchanged** | Previously repaired HR/IRR omission identities remain correct. | [scope](screenshots/matrix-irr-leave-one-out-figure.png) |
| R2-02 | **unchanged** | Copy/export retains executed identity and matches saved bytes. | [scope](OUTCOMES.json) |
| R2-03 | **unchanged** | Structured table exports remain tab-separated, not one-cell-per-line text. | [scope](OUTCOMES.json) |
| F01 | **unchanged** | Fixed-model inactive tau-squared omission retained; fresh fixed-IV figure/report agree on estimate, CI and heterogeneity. | [scope](screenshots/fixed-iv-footer.png) / [report](screenshots/fixed-iv-report.png) |
| F02 | **unchanged** | Applicable executed methods and fitted references retained. | [scope](screenshots/matrix-twoarm-proportion-standard-report.png) |
| F03 | **improved** | HR/IRR subgroup tables now remove legacy prose while retaining tests and prediction intervals. | [scope](screenshots/matrix-irr-subgroup-report.png) |
| F04 | **improved** | MD negative zero is repaired; diagnostic precision, tiny Qm and calculator rounding/data loss (R5-10) remain. | [scope](screenshots/matrix-twoarm-mean-meta-regression-report.png) |
| F05 | **unchanged** | Prior comparative test and named actual-null presentation retained. | [scope](screenshots/matrix-onearm-proportion-standard-figure.png) |
| F06 | **improved** | Actual arm names/integer previews improve modes; high-severity small-summary persistence loss remains (R5-10). | [scope](OUTCOMES.json) |
| F07 | **improved** | Navigator separators, naming/help and many controls improve; title-case/raw report remnants remain. | [scope](screenshots/shell-quick-start.png) |
| F08 | **unchanged** | Prior BMJ coefficient/entered-effect identity retained at six digits; three-style presentation/export sweeps passed. | [scope](screenshots/bmj-entered-effect-six-digits.png) |
| F09 | **unchanged** | Prior short-label numerical annotation clearance retained; new BMJ wrapped-name collision is R5-06. | [scope](OUTCOMES.json) |
| F10 | **unchanged** | IRR duplicate-author subgroup rows retain distinct identities and overall weights. | [scope](screenshots/matrix-irr-standard-figure.png) |
| R3-01 | **unchanged** | Sequential null guide stays within study rows clear of the footer. | [scope](screenshots/matrix-onearm-mean-cumulative-figure.png) |
| R3-02 | **unchanged** | Round linear bubble ticks and title clearance remain readable. | [scope](screenshots/matrix-onearm-proportion-meta-regression-figure.png) |

The five additional round-four findings are tracked separately:

| ID | Verdict | Observation / scope | Evidence |
|---|---|---|---|
| F11 | **fixed** | Exterior bubble guide removed; fresh 18-case metric/explicit-bound geometry sweep passed; decoded editor exports are separately recorded. | [bubble](screenshots/matrix-onearm-proportion-meta-regression-figure.png) |
| F12 | **fixed** | Legacy scene weights removed; report/Tables retain structured rows and existing component identities. | [figure](screenshots/matrix-twoarm-proportion-standard-figure.png) / [report](screenshots/matrix-onearm-proportion-standard-report.png) |
| F13 | **fixed** | Content-sized cards and Locate/Remove recovery; fresh native Qt 1.25/1.5/2.0 design runs passed. | [start](screenshots/design-00-review1-start-before-check.png) / [recovery](screenshots/design-01-round5-recent-missing.png) |
| F14 | **fixed** | Labelled Analyses group and actual prerequisite tooltip. | [toolbar](screenshots/design-12-round5-analysis-prerequisite-tooltip.png) |
| F15 | **fixed** | Navigator/results label/value spacing is consistent. | [grid](screenshots/design-08-round5-grid-cues.png) |

## 3. Regressions and the round-five claims

**One confirmed round-five presentation regression: R5-04.** Fitted results for the retained matrix inputs agree with the independent authorities. **R5-10 separately establishes a high-severity current data-integrity defect:** calculator editing can save a valid small raw SD as zero. Its responsible code is unchanged from round four; do not treat passing ordinary fixtures as qualification of small-valued input preservation. The fresh 18-case bubble sweep passed displayed/production geometry checks across 16 metrics, including explicit bounds. Visually inspected [proportion](screenshots/bubble-explicit-proportion.png) and [IRR](screenshots/bubble-explicit-irr.png) examples support F11; four-format editor qualification remains independently bounded by completed runs.

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

### R5-10 — High: calculator formatting overwrites a valid small raw SD with zero

In a one-arm-mean fixture (N 20, mean 4, original SD 2), entering **SD 0.00001** into the actual editable cell yields **SD 0.0** in the dialog's raw numeric model. Its mean CI preview collapses to 4.0–4.0. Accept displays [“The lower CI must be less than the point estimate!”](screenshots/calculator-tiny-raw-warning.png), but acknowledging that warning still applies the zero. **Save and reopen persist SD 0.0**, losing the requested valid positive summary. [Preview](screenshots/calculator-tiny-keyboard-replay-preview.png), [reopened calculator](screenshots/calculator-tiny-keyboard-replay-reopened.png), [full keyboard observations/input and saved-project hashes](TINY-RAW-KEYBOARD-REPLAY.json). The source fixture's bytes remain unchanged; only owned test copies were saved.

An initial real-cell/signal probe and an independent ordinary **editable QLineEdit delegate → F2/type 0.00001/Tab** replay produced the same saved-project hash and zero SD. The keyboard replay asserts the cell is editable and records its delegate type, dialog raw values, accepted values and reopened values. This is **stored data loss**, not just a rounded screenshot. The first keyboard driver's double-click did not open a delegate; its failed attempt is retained separately, and the corrected F2 replay completed. A completed observational drive is not a preservation pass: `stored_sd_preserved` is explicitly **false**.

The UI rounds numeric table values to four decimals, then copies those formatted strings back into the raw analysis unit. [AST comparisons](TINY-SOURCE-COMPARE.json) show the formatter, display setter, cell handler and table-to-raw copying functions are identical at the round-four revision. This supports a **pre-existing data-integrity defect**, rather than a confirmed round-five regression; no old-runtime tiny-SD replay was performed. No new fitted-model defect is inferred from the unchanged-input 50-cell matrix.

The same formatter also presents a tiny derived group-mean probability as [0.0](screenshots/calculator-group-summary-tiny-p.png). For N60/mean95.5/SD 22, the existing two-sided normal calculation independently gives 7.3479476072438575e-248; [exact calculation/source receipt](CALCULATOR-TINY-P.json). That preview symptom alone was low severity; the confirmed raw-value persistence loss makes the combined finding high.

A related ordinary-value inconsistency appears in the [one-arm-mean preview](screenshots/calculator-contact-04.png): after editing Mean from 4 to 5 with N 20/SD 2, the group table retains bounds 3.1235–4.8765, while the current effect preview correctly shows 4.1235–5.8765. The upper group bound is even below the displayed mean. Recompute derived fields from current supplied summaries, rather than treating old generated values as fresh input. The R imputation file is byte-identical to round four; this is another existing calculator state/presentation gap.

**Principle:** presentation must never change the research data. **Recommendation:** preserve full-precision numeric summaries through calculator editing, validation, Accept, Save and reopen. Use round-trip-safe text in editable numeric fields; keep formatted derived previews from overwriting raw values. Retain tiny positive derived probabilities visibly, and ensure failed CI validation prevents an invalid commit. Prove the entire valid-small-input path, including reopening the saved project and an independent subsequent fit. This repairs existing data handling and adds no statistical procedure.

### R5-11 — Medium: a hidden bubble confidence band remains in the legend

The regression editor's [native controls](screenshots/editor-contact-03.png) turn off **Show confidence band** while keeping the legend. The production-applied parameters assert `bp_show_confidence_band:false`. In the [actual edited BMJ bubble](screenshots/bubble-hidden-ci-legend.png), the band is absent, but the legend still says **95% CI**, with the same solid-line key as “Regression line”. That key now describes no plotted uncertainty component. The exported SVG retains the label; [parameters, source comparison and export hash](BUBBLE-LEGEND.json).

The legend-label function unconditionally includes Regression line and CI, while PI already has a conditional branch. It is identical at the round-four revision: **source-supported pre-existing**, not a confirmed new regression. No changed fitted estimate or interval calculation is alleged.

**Principle:** a figure key must describe the marks actually shown. **Recommendation:** derive legend entries and their line/fill samples from the same enabled regression/CI/PI options and styles used to draw the panel. Remove entries for hidden components in displayed and exported figures. Exercise each existing visibility toggle with the legend on; add no statistical quantity.

## 5. Microcopy and information design

The [actual optional-name wizard](screenshots/arms-custom-wizard.png) accepts full clinical names; [duplicate names](screenshots/arms-duplicate-rejected.png) are rejected inline after whitespace normalization. [Blank optional names](screenshots/arms-blank-defaults.png) use Intervention/Control; [calculator](screenshots/arms-default-calculator.png), [canonical CSV mapping](screenshots/arms-current-csv-map.png) and [legacy-header mapping](screenshots/arms-legacy-csv-map.png) use the same readable fields. [Legacy user-project names](screenshots/arms-legacy-preserved.png) remain exactly tx A/tx B, as required. The fresh 175-step arm-name scenario passed, including report/copy/export and three styles. Native start/recent/Analyses/CSV/structure/help frames are inspected: [start](screenshots/design-00-review1-start-before-check.png), [missing recovery controls](screenshots/design-01-round5-recent-missing.png), [recovered list](screenshots/design-02-round5-recent-recovered.png), [actual disabled-action tooltip](screenshots/design-12-round5-analysis-prerequisite-tooltip.png), [CSV entry](screenshots/shell-csv-entry.png), [Quick start](screenshots/shell-quick-start.png). F13, F14 and F15 are fixed on these paths. The [grid](screenshots/design-08-round5-grid-cues.png) has Intervention/Control, calculator glyphs and italic derived values as non-colour cues. The 171 native header/study/method states were visually reviewed in [contact sheets](OPTIONS-CONTACTS.json), alongside exact control/choice inventories. The existing “Binary” method family in single-arm proportion and “Continuous” family in coefficient/entered-effect setups still asks the user to translate package taxonomy; prefer metric-specific display identity using the existing selection. IRR Mantel–Haenszel also reuses a generic log-hazard/rate description; describe the selected existing method precisely. Some offscreen header-coordinate samples repeat adjacent menus, so these alone do not prove every individual column gesture. All 12 maintained calculator-mode drives passed their existing persistence/analysis assertions, with all 12 previews visually inspected in [six contact sheets](CALCULATOR-CONTACTS.json). Group summaries still reserve substantial vertical whitespace; back-calculated 17-digit CIs horizontally scroll and can hide leading digits (N11). Improve readable display while preserving full-precision input/storage; rounding the model is unacceptable (R5-10). Remaining minor copy debt includes Open Recent/Follow-Ups/Treatment Groups title case and Yes/No dirty-prompt actions; explicit Save/Discard action labels would scan faster. These are polish opportunities, not new functional failures.

The real exported UTF-8 report was opened in [native xedit](screenshots/shell-exported-report-editor.png). Its content/numbers agree with copied output; xedit misrenders some Unicode characters on this host. This editor limitation is also documented in round four and is not evidence of corrupted export bytes. Native Gtk template Save picker was actually driven; other helper picker substitutions do not qualify all OS picker routes.

## 6. Coverage matrix

The independent public-package authority sweep passed 91/91; [receipt](AUTHORITIES.json). All ten families × five workflows passed; every first figure/report pair is visually inspected in [MATRIX](MATRIX.md). Completed runs below are fresh Linux native runs. All 112 maintained scenarios were attempted;111 passed. `project-shell` failed two immediate native-state assertions; the separate [state-settling drive](STARTUP-SETTLED.json) reached the correct Qt/EWMH states in 214–296 ms including a 200 ms stability floor. [Maximized](screenshots/startup-settled-after-fullscreen.png) and [restored normal](screenshots/startup-settled-restore-normal.png) states were visually inspected. The failed gate remains failed; no application or test was changed to hide it.

| Area | Exercised / inspected | Scope and limits |
|---|---|---|
| Runtime | Native doctor; R 4.6.1; current-source/install receipts |55 source / 24 installed hashes; no system-library modification. |
| Start and recents | Light/dark start; missing-file Locate cancel/relocation/same-path recovery/Remove | Content-sized cards; fresh Qt 1.25/1.5/2.0 runs passed. |
| Menus and toolbar | Recursive actual menus/submenus and tooltips, enabled/disabled states; labelled Analyses and prerequisite tooltip | [Attached trees for all ten families](REACHABLE-MENUS.json), exact text/shortcuts and native nested-menu proof; not every desktop-environment mnemonic combination. |
| Creation and CSV | All ten create/data-type/ratio paths; optional blank/custom/duplicate arm names; new/legacy CSV header mapping, templates and preview | Native Gtk Save template picker actually driven; other pickers are test-owned substitutions. Dialect/filesystem fault combinations not universal. |
| Grid and structure | Ten-family data, context/menu inventories, 171 states; inclusion/covariates; structure tabs/settings; Save As/recent reopen | Some offscreen header-coordinate samples repeat adjacent menus; do not infer every individual column gesture from the inventory. |
| Samples | All 7 bundled archives opened/analyzed/saved/reopened; 14 figure/report images inspected | Original bytes unchanged. BCG 13/13 rows agree with original pinned data; readable names preserved. [Proof](SAMPLE-NATIVE.json), [source comparison](BCG-SOURCE.json). |
| Core analysis | 50 cells: 10 families × standard/cumulative/leave-one-out/subgroup/meta-regression | Each first figure/report pair inspected; selected endpoint/pooled/statistic agreement recorded. Not every cell of every long table manually transcribed. |
| Diagnostics and small-study | Joint Reitsma SROC, combined metrics, moderator shapes; extended binary/continuous and diagnostic Deeks; IRR contour error/recovery | All mapped variants were driven; existing procedures only, with public numerical contracts. No new statistical method recommended. |
| Results | Text, selectable Tables, copy/export identity, zoom/Fit width, Change settings/rerun; no legacy scene weights | Real UTF-8 export opened in native xedit; host editor Unicode limitation retained. |
| Figure presentation | Three long-figure styles, three realistic-name styles; editable standalone context; 18 bubble metric/bound cases; IRR exposure/totals | Some collisions are real findings despite passing render assertions. All 11 editor workflows decoded all 4 formats; [controls/exports](EDITOR-WORKFLOWS.json), [visual control review](EDITOR-CONTACTS.json). |
| Help and states | Both Help actions: Quick start/shortcuts and About/licenses; empty start/grid/covariates; duplicate-name/invalid-contour recoveries | No documentation claim substitutes for interaction. Dirty Open Cancel/Yes/No and cancelled Save As all driven; saved/reopened and preservation assertions passed. |
| Access and scale | Native Tab/arrow/Escape for main/setup/results, named controls and non-colour grid cues | All 12 calculator-mode main-control traversals, loaded-project keyboard task and Qt 1.25/1.5/2design runs passed; targeted 1.5calculator/editor runs also passed. No screen-reader/OS-DPI/cross-platform qualification. |

[OUTCOMES](OUTCOMES.json) binds exact commands, observed exit statuses, logs and helper manifest/artifact hashes; [INSPECTIONS](INSPECTIONS.json) records visual observations. Inventoried choices are not equivalent to every possible value combination being executed.

## 7. Accessibility

Fresh native Tab/arrow/Escape traversal passed for the workspace, both setup pages and Results table/selector/sidebar; focus sequences are retained in [DESIGN](DESIGN.json). [Grid cues](screenshots/design-08-round5-grid-cues.png) show calculator glyphs and italic derived values as well as gold colour. The labelled Analyses control has real prerequisite tooltips, and the selectable Results table has a meaningful accessible name. Empty accessibleName properties alone are not treated as defects: labelled Qt controls may derive their names through buddy/label relations.

Fresh native design runs passed at QT_SCALE_FACTOR=1.25, 1.5 and 2.0; [scale receipts and sampled grid colour measurements](SCALES.json), visually inspected [1.25 start](screenshots/scale125-start.png), [1.5 start](screenshots/scale15-start.png), [1.5 setup](screenshots/scale15-setup.png), [2.0 start](screenshots/scale20-start.png) and [2.0 setup](screenshots/scale20-setup.png). The derived-cell normal and selection foreground/background pairs measured at least 4.5:1 on these captured palettes; that is a sampled check, not every application colour or a high-contrast theme. The complete loaded-project keyboard task passed through Tab/Control-Tab → Analyses → Space/arrows → Meta-analysis → Enter → report/copy/export shortcuts. [Focus](screenshots/keyboard-toolbar-focus.png), [menu](screenshots/keyboard-analysis-menu.png), [report](screenshots/keyboard-report-copied-exported.png), and [assertion/artifact summary](GUARD-SUMMARY.json) record it. Save/Discard/cancelled Save As also passed; [cancelled-save preservation](screenshots/guard-save-as-cancel-preserved.png). Two earlier driver assumptions (F10 and Home/Down) failed and remain verbatim in FAILURES; the final replay passed without application changes. All 12 calculator-mode main-control traversals completed. Targeted [pre/post calculator](screenshots/scale15-calculator-prepost.png) and [regression editor](screenshots/scale15-editor-regression.png) runs also passed at 1.5; [receipts](SCALED-DIALOGS.json). These are application-level Qt scale checks, not actual OS display-scaling or screen-reader qualification. The loaded-project task uses no initial widget focus assignment; arbitrary whole-application tasks from process launch, Orca/AT-SPI relationships, high contrast, a full measured-contrast audit, multi-monitor behavior and Windows/macOS remain unqualified.

## 8. Ranked round-six list

1. **R5-10, high:** preserve full-precision raw calculator inputs through editing/Accept/Save/reopen; stop formatted previews from overwriting values, and block invalid commits.
2. **R5-09, medium acceptance gap:** remove the built-in TX Mean menu prefix using existing contextual display identity; preserve internal keys and legacy user names.
3. **R5-04, medium regression:** bound long default/subgroup CI caps to actual row spacing; preserve horizontal intervals and fitted values.
4. **R5-06, medium:** finish BMJ header clearance using measured real arm names, including unequal wrapped lengths; check exports.
5. **R5-03 / F04, medium:** route diagnostic meta-regression coefficient and ML-test tables through selected precision, with consistent readable headings.
6. **R5-01, medium:** put fitted SE scale beside clinical-scale sequential/subgroup estimates in Text, Tables and exports.
7. **R5-11, medium:** make bubble legend entries and line samples follow the actual visible regression/CI/PI components.
8. **D04 / R5-07, existing medium finishing gap plus low copy defect:** use actual eligibility reasons; validate contour fields inline and stop busy state after failure while preserving recovery.
9. **R5-08, low:** make subgroup style choices describe the actual supported layout; eliminate silent fallback promises.
10. **R5-05, low:** finish package-owned Intercept/Moderator/Statistic, diagnostic and validation labels at the display boundary.
11. **R5-02, low:** remove identical type/metric repetitions and uninformative generated defaults from new captions; preserve investigator text.
12. **A01/A05, qualification gap:** extend the completed loaded-project keyboard task to other entry points, focus restoration and screen-reader relationships; retain actual Qt-scale proof and OS limits.
13. **F07 / M01 / H01, low:** finish action-labelled Save/Discard prompts, case consistency, concise contextual guidance and existing plot units/identity presentation.
14. **Platform qualification:** exercise remaining native picker routes and supported packaged targets; do not promote Linux source proof into cross-platform release proof.

RCMS is visibly closer to a coherent, polished analysis workbench: actual arm names, useful standalone context, simpler start/recovery, readable growing figures and one weights presentation improve normal work. The reachable TX Mean remnant and BMJ long-name collision leave the naming work incomplete. **The high-severity calculator data-loss path is the first issue to fix.** A polished report cannot compensate for changed raw summaries. Round six should preserve calculator numbers end to end, then finish the existing naming, layout and precision paths and qualify access/recovery. Additional statistical breadth is unnecessary for this round.


## 9. Limits, replay and evidence inventory

[OUTCOMES](OUTCOMES.json) records 153 completed recorder invocations:145 exit 0 and8 exit 1. The doctor run is separately bound. These counts are process outcomes, not counts of UX issues fixed. In particular the tiny-SD observational probes exit 0 after writing `stored_sd_preserved:false`. Every completed helper manifest and retained-file hash was checked. [FAILURES](FAILURES.json) preserves failures verbatim, their classification, the interruption and ancillary errors.

| Failed recorded invocation | Observed failure / outcome |
|---|---|
| `native-design-serial` | `FileExistsError` from an interrupted run's owned fixture directory; archived, fresh replay passed. |
| `native-shell-serial` | `AssertionError` because the prior design export was missing; design then shell replay passed. |
| `native-all-samples` | Audit wrapper chose a continuous method for binary meantime; `StopIteration`; corrected seven-sample replay passed. |
| `native-guard-keyboard-priority` | F10 assumption produced no active menu; driver entry assumption. |
| `native-guard-keyboard-replay` | Home/Down selected Effect-size tools; bounded arrow-selection replay passed. |
| `native-tiny-raw-keyboard` | Double-click did not open a QLineEdit delegate; corrected editable-cell/F2 replay completed and confirmed actual data loss. |
| `helper-project-shell` | Immediate normal-to-maximize assertion failed after one event-processing call. |
| `helper-project-shell-replay` | Initial maximize passed, immediate fullscreen-to-maximize assertion failed. Separate observed settling passed; both unmodified failures remain. |

The earlier outer matrix shell exited 143 after four completed families, leaving an owned generic-effect child briefly overlapping design. Only documented owned trees were stopped; overlapping partial frames were rejected and replayed serially. This is a runner interruption, not a product regression. A manual acknowledgment in the first tiny-SD probe let it finish before a follow-up Escape activation; that activation failed with native `BadWindow`, and no Escape key was sent. The final self-contained keyboard probe handles its own warning. Ancillary bookkeeping errors (missing system `python`, initial scorecard key, a deleted temporary export path) are preserved separately; corrected tools use `uv run python` and retained manifest copies. No failed run was silently converted into a pass.

Replay from the repository root using [REPLAY](REPLAY.md): source `docs/ux-audit/2026-10-14-round3/ENV.sh`, export DISPLAY=:0, and run native doctor first. Exact commands/environment/revisions are in OUTCOMES; additional driver sources and hashes are embedded in [REPLAY-SOURCES](REPLAY-SOURCES.json). Raw logs, owned inputs, SVGs and detailed helper evidence remain in ignored directories. [Evidence inventory](EVIDENCE.md), [curated image hashes/observations](INSPECTIONS.json), [raw capture relocation map](CURATION.json), [matrix](MATRIX.md), [source-label dispositions](LABELS.md) and [commit list](COMMITS.md) make the retained evidence reviewable.

Limits remain explicit: this is Linux source/native Qt proof, not packaged Windows/macOS or actual OS-DPI/screen-reader qualification. Most file-picker paths use test-owned substitutions; the native Gtk template Save picker was actually driven. The UTF-8 report was opened in native xedit, whose host font/rendering misdisplays some Unicode; bytes match copied output. Some header-coordinate samples repeat adjacent menus; current attached menu trees and targeted nested hover proof are separate. All100first matrix images and cited curated frames were visually inspected, but not every pixel of every decoded export or every cell of every long table was manually checked. No arbitrary parameter Cartesian product, all filesystem/dialect faults, all long labels, universal contrast or complete from-launch keyboard task is claimed. Source-confirmed validation copy and pre-existing-code comparisons are distinguished from native reproductions. The retained 50-cell inputs do not qualify preservation of newly edited small values; R5-10 demonstrates that limit concretely.
