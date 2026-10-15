# RC MetaStudio native round-four re-audit — 15 October 2026

## 1. Executive summary

Round four is a substantial improvement over the [round-three re-audit](../2026-10-14-round3-reaudit/REPORT.md). The two confirmed round-three regressions are repaired on inspected paths, duplicate-name subgroup weights retain their proper study identity, BMJ labels are contextual, and reports now lead with the result. The native start page, explicit test nulls, whole confidence levels in output, clearer navigation and shared controls improve ordinary work.

**Verdicts against round three: 68 inherited IDs — 4 fixed, 27 improved, 37 unchanged, 0 regressed. Fifteen additional IDs — 6 fixed, 3 improved, 6 unchanged, 0 regressed.** Across all 83 tracked IDs this is **10 fixed, 30 improved, 43 unchanged**. Unchanged includes previously fixed behavior retained. There are **six new findings: two medium and four low**, with no confirmed new numerical or functional regression. F11 is demonstrably pre-existing. No high-severity new finding or wrong fitted estimate/CI was established.

The 50-cell native matrix completed: ten data types including HR/IRR, each with standard, cumulative, leave-one-out, subgroup and meta-regression figure/report evidence. Every first figure/report pair was visually inspected, with numerical comparisons to reports and independent package checks. The independent authority sweep passed 91/91. This is a broad independent audit, **not literal qualification of every possible GUI value or option combination**. The coverage and failures below preserve that distinction.

This read-and-report review began at `f1aa24d` on `ux/audit-improvements`. Only audit documents/scripts/screenshots and HANDOFF were changed. Linux visible xcb windows used DISPLAY=:0, pinned R 4.6.1, and the test-owned library. Doctor passed; all 55 source and 24 installed RCMetaR receipt hashes matched. Round-four implementation claims were treated as hypotheses, not substituted for fresh evidence.

## 2. Scorecard and independent verification

Fixed closes the observed defect; improved closes part; unchanged retains the previous state; regressed requires observed worse behavior. Linux cannot qualify the baseline's Windows layout or other platforms. Evidence links refer to actual captures or machine-readable exercised-path records; an inventory does not imply every listed value was executed.

| ID | Verdict vs round three | Current observation / remaining gap | Evidence |
|---|---|---|---|
| L01 | **unchanged** | Type choices fit; field scrolling and lack of a step indicator remain. | [wizard](screenshots/shell-types.png) |
| L02 | **fixed** | Pristine start page says Untitled dataset and is not dirty; no redundant welcome modal. | [start](screenshots/design-00-review1-start-before-check.png) |
| L03 | **unchanged** | Template/import route retained; export and mapping checks remain in the native registry. | [csv](screenshots/shell-csv-entry.png) |
| L04 | **unchanged** | Entered-effect guidance retained; user effect labels/units remain limited. | [generic](MATRIX-generic-effect.json) |
| L05 | **unchanged** | Task/type/metric guidance retained; final review remains sparse. | [wizard](screenshots/shell-types.png) |
| L06 | **unchanged** | CSV preview retained; automatic dialect recovery and all filesystem failures are unqualified. | [csv](screenshots/shell-csv-entry.png) |
| G01 | **unchanged** | Linux grid readable; old Windows persisted-width trigger remains unqualified. | [grid](screenshots/shell-grid.png) |
| G02 | **improved** | Single-arm grid remains compact; calculator active-mode disclosure improves. | [calculator](OUTCOMES.json) |
| G03 | **unchanged** | Inclusion/derived-cell explanation retained; selection/colour qualification remains open. | [grid](screenshots/shell-grid.png) |
| G04 | **improved** | Named dimension selector and Previous/Next/Add replace the compass; Follow-up:first spacing remains. | [grid](screenshots/shell-grid.png) |
| G05 | **improved** | Existing arm identity and pinned calculator result/actions reduce decoding and scrolling. | [calculator](OUTCOMES.json) |
| G06 | **unchanged** | Diagnostic estimate/CI digits remain readable; prevalence remains labelled. | [calculator-diagnostic](OUTCOMES.json) |
| G07 | **improved** | Active calculator modes are more compact; complete grid-width/scaling qualification remains open. | [calculator](OUTCOMES.json) |
| G08 | **improved** | Numeric/Category wording improves; destructive context actions stay separated. | [covariates](screenshots/shell-covariates.png) |
| M01 | **improved** | Sentence-case actions/ellipses improve; toolbar text/icon consistency still incomplete. | [menus](MENU-INVENTORY.json) |
| M02 | **improved** | Start page disambiguates full recent paths and disables missing files; locate/remove recovery absent. | [start](screenshots/design-00-review1-start-before-check.png) |
| M03 | **unchanged** | Disabled subgroup/regression toolbar tooltips give a covariate prerequisite; source comparison shows this is retained, not a round-four addition. | [toolbar](TOOLBAR.json) |
| M04 | **unchanged** | Structure tabs and named add/remove controls retained; three-pane density remains. | [structure](screenshots/shell-structure.png) |
| S01 | **unchanged** | Independent report/figure zoom and scoped confidence controls retained. | [zoom](DESIGN.json) |
| D01 | **improved** | Shared button sizing and pinned calculator actions improve reachability; OS scaling unqualified. | [calculator](OUTCOMES.json) |
| D02 | **unchanged** | Task/outcome and Run analysis retained; repetitive setup description remains. | [setup](OPTIONS.json) |
| D03 | **improved** | Automatic and contextual defaults improve; hex colours and long editor forms remain. | [editor](OUTCOMES.json) |
| D04 | **unchanged** | Recoverable analysis errors retained; full progress/phase feedback not qualified. | [error](screenshots/extra-irr-invalid-contour-error.png) |
| D05 | **unchanged** | Correction/eligibility controls retained; universal affected-study accounting remains incomplete. | [setup](OPTIONS.json) |
| R01 | **improved** | Result-first report, named calculation table and study-weight table improve reading; legacy scene/package text remains. | [report](screenshots/design-07-review1-report-top.png) |
| R02 | **unchanged** | Copy/export identity retained; standalone figure clinical/exposure identity remains incomplete. | [irr](MATRIX-irr.json) |
| R03 | **improved** | Text/Tables/plot navigation works and export preference persists; legacy scene weights and long figures remain. | [results](DESIGN.json) |
| R04 | **fixed** | Sequential null references stop at plotted rows and clear the footer on inspected paths. | [sequential](MATRIX-twoarm-mean.json) |
| R05 | **fixed** | Original coefficient Fixture 2 lower bound renders zero; genuine tiny effects remain in precision checks. | [coefficient](MATRIX-reg-coef.json) |
| R06 | **improved** | Study added (k) retained; current help distinguishes fitting sequence and display order. | [help](screenshots/shell-quick-start.png) |
| R07 | **unchanged** | Previously repaired HR/IRR omission identities remain correct. | [omission](MATRIX-hr.json) |
| R08 | **unchanged** | Subgroup k/heterogeneity/PI tables retained; HR/IRR difference-test package prose remains. | [subgroup](MATRIX-irr.json) |
| R09 | **improved** | Round compact bubble ticks clear metric titles; missing study identity/units and outside-box null remain. | [bubble](MATRIX-generic-effect.json) |
| R10 | **improved** | Single-arm proportion now names its actual tested null; clinical estimate remains primary. | [proportion](MATRIX-onearm-proportion.json) |
| R11 | **improved** | Mean null is explicit; user outcome units remain unavailable in standalone figure context. | [mean](MATRIX-onearm-mean.json) |
| R12 | **unchanged** | Coefficient/entered-effect identity remains correct on inspected standard routes. | [coefficient](MATRIX-reg-coef.json) |
| R13 | **unchanged** | Comparative arm identity/scale guidance retained; no automatic clinical interpretation added. | [report](screenshots/design-07-review1-report-top.png) |
| R14 | **unchanged** | MD/SMD signs and SD-unit guidance retained; user units remain limited. | [continuous](MATRIX-twoarm-mean.json) |
| R15 | **improved** | Diagnostic report leads with clinical summaries and tables; repeated headings and dense technical blocks remain. | [diagnostic](MATRIX-diagnostic.json) |
| R16 | **unchanged** | Diagnostic moderator/contrast/reference naming retained; coefficient chart uses its separate renderer. | [diagnostic-regression](MATRIX-diagnostic.json) |
| R17 | **improved** | HR report gains clearer result-first structure/weights; long forest still needs scrolling/small type. | [hr](MATRIX-hr.json) |
| R18 | **unchanged** | IRR identity/exclusions retained; events/exposure units remain absent from forest columns. | [irr](MATRIX-irr.json) |
| R19 | **unchanged** | Small-study cautions and procedures retained; ordinary funnel key remains limited. | [small-study](EXTRA.json) |
| E01 | **improved** | Remembered plot format joins intact report identity/table rows and real four-format exports. | [results](DESIGN.json) |
| E02 | **unchanged** | Saved/reopened data and dirty state retained; pristine start corrected under L02. | [grid](screenshots/shell-grid.png) |
| H01 | **improved** | Quick start covers result tools and order distinction; complete contextual help/accessibility remains open. | [help](screenshots/shell-quick-start.png) |
| X01 | **unchanged** | Blank/duplicate-name validation remains recoverable. | [covariates](screenshots/shell-covariates.png) |
| X02 | **unchanged** | Local covariate empty-state guidance retained; broader workflow guidance remains modest. | [covariates](screenshots/shell-covariates.png) |
| A01 | **unchanged** | Real selectable table cells retained; screen-reader qualification remains open. | [results](DESIGN.json) |
| A02 | **unchanged** | Grid meaning retained; measured contrast/high-contrast qualification remains open. | [grid](screenshots/shell-grid.png) |
| A03 | **improved** | Calculator actions and plot spacing improve; long figures/OS DPI remain open. | [calculator](OUTCOMES.json) |
| A04 | **improved** | Shared button policy and named navigation improve targets; unlabelled analysis icons remain. | [toolbar](TOOLBAR.json) |
| A05 | **unchanged** | Existing shortcut/copy gestures run; full keyboard-only/focus qualification remains open. | [menus](MENU-INVENTORY.json) |
| RG01 | **improved** | Clinical-first diagnostic report gains result-first reading order; legacy details remain. | [diagnostic](MATRIX-diagnostic.json) |
| RG02 | **unchanged** | Independent view zoom retained; Fit width remains scoped to figures. | [zoom](DESIGN.json) |
| RG03 | **unchanged** | Shared diagnostic notes precede component blocks; executed estimators retained. | [diagnostic](MATRIX-diagnostic.json) |
| RG04 | **unchanged** | CSV instructions remain outside the scrolling fields. | [csv](screenshots/shell-csv-entry.png) |
| N01 | **fixed** | BMJ contextual axis labels now retain entered-effect/coefficient identity. | [bmj](MATRIX-generic-effect.json) |
| N02 | **unchanged** | Diagnostic moderator labels/contrasts retained; all long-label permutations unqualified. | [diagnostic-regression](MATRIX-diagnostic.json) |
| N03 | **improved** | Compact ticks, bounded sequential guides and contextual BMJ labels improve; bubble null guard still incomplete. | [bubble](MATRIX-generic-effect.json) |
| N04 | **improved** | Result-first structured report/weights improve; HR/IRR subgroup package prose remains. | [report](screenshots/design-07-review1-report-top.png) |
| N05 | **unchanged** | Existing subgroup difference tests remain in reports and figures. | [subgroup](MATRIX-irr.json) |
| N06 | **unchanged** | Previously repaired report identity and tab-separated table rows retained. | [export](DESIGN.json) |
| N07 | **unchanged** | HR/IRR cumulative and omission labels/estimate-CIs remain aligned. | [omission](MATRIX-hr.json) |
| N08 | **improved** | Active calculator modes/pinned actions reduce density; persisted Windows width case remains open. | [calculator](OUTCOMES.json) |
| N09 | **improved** | Named dimension navigation replaces compass without adding another navigation subsystem. | [grid](screenshots/shell-grid.png) |
| N10 | **improved** | Numeric/Category/Automatic and contextual estimate labels improve; some tooltip/title-case remnants persist. | [covariates](screenshots/shell-covariates.png) |
| N11 | **unchanged** | Diagnostic calculator leading digits remain visible in native checks. | [calculator-diagnostic](OUTCOMES.json) |

Additional IDs retain their original identities:

| ID | Verdict | Independent observation / scope | Evidence |
|---|---|---|---|
| R2-01 | **unchanged** | Repaired HR/IRR omission identities retained; labels and estimate/CI rows agree. | [evidence](MATRIX.md) |
| R2-02 | **unchanged** | Export/copy retains executed identity and matches saved bytes. | [evidence](DESIGN.json) |
| R2-03 | **unchanged** | Structured export rows remain tab-separated rather than one cell per line. | [evidence](DESIGN.json) |
| F01 | **unchanged** | Fixed-model footers omit inactive tau-squared; prior repair retained. | [evidence](HELPER-SCREENSHOTS.json) |
| F02 | **unchanged** | Applicable model settings and fitted references retained on fixed/random paths. | [evidence](HELPER-SCREENSHOTS.json) |
| F03 | **unchanged** | Structured standard/subgroup statistics and existing prediction intervals retained; residual package prose remains. | [evidence](MATRIX.md) |
| F04 | **improved** | Original coefficient zero-bound residue repaired and main ticks round; negative zero and separate coefficient tick formatting remain. | [evidence](MATRIX-twoarm-mean.json) |
| F05 | **fixed** | RevMan-form comparative test; named actual nulls for single-arm, diagnostic, entered and coefficient output. | [evidence](MATRIX.md) |
| F06 | **improved** | Active calculator modes and pinned actions reduce density; grid and platform limits remain. | [evidence](OUTCOMES.json) |
| F07 | **improved** | Numeric/Category/Automatic and current Quick start; some tooltips and spacing still lag. | [evidence](screenshots/shell-quick-start.png) |
| F08 | **fixed** | BMJ generic/coefficient metric labels are contextual on inspected style captures. | [evidence](HELPER-SCREENSHOTS.json) |
| F09 | **fixed** | Observed six-digit annotation collisions repaired on inspected standard/style paths; MD gap remains tight. | [evidence](HELPER-SCREENSHOTS.json) |
| F10 | **fixed** | Duplicate-name IRR subgroup rows retain distinct weights; independent original-order weights total 100%. | [evidence](MATRIX-irr.json) |
| R3-01 | **fixed** | Sequential null guide ends at study rows clear of footer. | [evidence](MATRIX-twoarm-mean.json) |
| R3-02 | **fixed** | Linear bubble round ticks and title clearance repaired on inspected paths. | [evidence](MATRIX-twoarm-mean.json) |

## 3. Regressions and the round-four claims

No confirmed new numerical or functional regression was established on the exercised paths. This does not turn unexercised combinations into passes. The mixed toolbar labels and oversized empty start cards are unfinished design introduced with otherwise useful round-four work; they are not evidence that the old launcher or toolbar worked better overall.

R3-01 is closed on inspected sequential paths: the MD cumulative guide now stops at the study rows, clear of the model heading and statistical footer. R3-02 is closed on inspected linear bubble paths: compact round ticks and adequate metric-title clearance replace six-decimal tick/title collisions. The native style/precision drives supplement these representative matrix views. HR/IRR omission identities remain repaired.

The original coefficient Fixture 2 lower bound now displays zero. F04 is nevertheless **improved**, rather than universally closed: the MD regression report still prints `-0.000000` for its negligible slope and Z; the separate diagnostic coefficient renderer retains six-decimal round tick strings. These are presentation remnants, not evidence of changed fitted values. Genuine tiny values must remain distinguishable.

F09's observed collisions are repaired on inspected standard/style/export paths. The six-decimal MD weight-to-estimate gap is still visually tight; non-overlap is a minimum, not the ideal finished layout. F10's duplicated-author subgroup weight mapping is repaired: Jaeger 2001/2005 retain distinct contributions and the IRR overall subgroup weight is 100.0%. Native checks independently compare every subgroup weight with a public-package overall fit in original-row order.

The results page needs a careful distinction. **Text report and Tables have the new Study / Weight (%) table; the graphics scene still contains the old monospace weights block.** Changing the forest style does not replace that surrounding scene text. The user's observation is reproducible and is F12 below, not a stale installed-package hypothesis.

## 4. New and remaining findings

### F11 — Medium: bubble null guides can be drawn outside the plotting box

The [single-arm proportion bubble](screenshots/matrix-onearm-proportion-meta-regression-figure.png) has its zero reference below the lower plot boundary, between the x ticks and Dose title. The [generic-effect bubble](screenshots/matrix-generic-effect-meta-regression-figure.png) has the same smaller remnant. This is pre-existing: the round-three proportion screenshot already has the exterior line. It must not be called a round-four regression.

**Principle:** data marks belong to their coordinate region. **Recommendation:** draw the existing null guide only when it lies within the displayed y range, and clip it to the plotting region. Retain the 0/1 semantics and the useful in-range reference. Check explicit ranges and exported plots; change no fit.

### F12 — Medium: two competing weights presentations remain

The [binary figure page](screenshots/matrix-twoarm-proportion-standard-figure.png) still shows monospace `Fixture 5: 19.1%` lines; the [structured report](screenshots/matrix-twoarm-proportion-standard-report-bottom.png) contains the Study / Weight (%) table. Similar legacy blocks remain for single-arm, coefficient, entered-effect and continuous output. HR/IRR have the structured report route too; diagnostic results do not expose an equivalent top-level weights section even though their forests show component-specific weights. These are different views/producers, not evidence of a wrong weight.

**Principle:** one quantity should have one readable representation and explicit model context. **Recommendation:** retire the legacy graphics-scene weights text or render the existing structured table there. Use the same existing row identity and values in Text, Tables, copied/exported reports and the scene; identify diagnostic component weights separately if exposed. Keep style choice confined to figure appearance. Do not calculate a new quantity or silently mix component weights.

### F13 — Low: start cards expand beyond their content

The [maximized pristine page](screenshots/design-00-review1-start-before-check.png) gives each action card a conspicuous empty lower area after its two-line description. The [normal-size recent-project page](screenshots/design-01-review1-start-recents.png) is much tighter. The native page is a clear improvement over the blank grid and redundant welcome modal, but its density depends unnecessarily on available height.

**Principle:** space should reinforce grouping and priority. **Recommendation:** size the action row to its contents and put spare height below the task content. Keep the three entry actions and full recent paths. Missing-file entries are honestly disabled, but an existing-workflow locate/remove action would provide a clearer recovery than a permanently dead button.

### F14 — Low: the toolbar teaches two recognition rules

The [actual cumulative tooltip](screenshots/design-17-toolbar-tooltip.png) is useful, but only Meta-analysis has a visible analysis label; cumulative, leave-one-out, subgroup, regression and small-study actions remain icon-only. The hover inventory includes all toolbar entries. Disabled subgroup/regression tooltips explain prerequisites, which source comparison shows is retained behavior.

**Principle:** recognition should not depend on remembering near-identical icons. **Recommendation:** use a consistent compact labelled analysis group, with a menu/dropdown when ordinary window width cannot hold all labels. Preserve shortcuts, prerequisites and existing actions; no new command subsystem is needed.

### F15 — Low: navigator metadata still joins label and value

The [grid](screenshots/design-06-review1-workspace-navigation.png) reads `Follow-up:first`, while its upper context uses a space. The old round-three grid has the same lower-label defect, so this is not a new regression.

**Principle:** metadata should scan as label/value pairs. **Recommendation:** render `Follow-up: first` consistently, including outcome/comparison labels, and retain the much clearer named navigation selector.

### F16 — Low: report hierarchy remains heavier than its information

The [report top](screenshots/design-07-review1-report-top.png) is readable and usefully result-first. Heading size alone is not excessive on this host: the HTML h2 size is 1.18 times the native body size. The repeated Summary / Model Results and Weights / Study weights headings, bold pooled sentence and repeated generous margins create more visual competition than the size ratio suggests. Diagnostic prefixes such as `Sensitivity -Model Results` and the [HR/IRR subgroup package prose](screenshots/matrix-irr-subgroup-report.png) interrupt the otherwise structured reading page.

**Principle:** hierarchy should reduce reading work. **Recommendation:** keep the result-first order, remove redundant nested headings, use sentence case and consistent separator spacing, and structure the existing HR/IRR subgroup-difference output like the other report tables. Keep meaningful detail available. Prefer fewer heading levels to simply shrinking all text.

### Remaining inherited work

Long HR/subgroup figures still have small type and require scrolling. Sparse subgroup layouts reserve large vertical gaps around short statistical footers. Improve density using the existing layout/spacing controls while preserving a readable minimum font. Standalone figure exports still need the already available outcome/comparison/follow-up context; IRR figures omit event/exposure columns and exposure identity. These are R02/R03/R17/R18, not new IDs or requests for new statistical methods.

F06 is improved by active modes and pinned actions; continuous still reserves a large empty area around a dense summary table, and diagnostic retains older Clear Form/back-calculation vocabulary; the old Windows persisted grid-width case is not qualified by Linux screenshots. F07 is improved by Numeric/Category/Automatic and updated help, but retained tooltips still contain `Publication Bias and Small-Study Effects`, and some capitalization/abbreviation inconsistencies remain. A coherent finish should include these small strings, not a new theme or generic configuration framework.

[Official design references](REFERENCES.md) informed the recommendations: RevMan links effect/CI/confidence level to identified results; metafor/meta expose explicit label/weight/scale and spacing controls; JASP's documentation presents model output with forest plots. This is a documentation comparison, not an installed RevMan/JASP/CMA usability test. CMA's current vendor page returned 403, and no unsupported live comparison is claimed. No new statistical feature is recommended.

## 5. Microcopy

| Observed | Recommendation | Status |
|---|---|---|
| Follow-up:first | Follow-up: first | F15, retained gap |
| Weights → Study weights | One Study weights heading; Study / Weight (%) columns | F12/F16 |
| Sensitivity -Model Results | Sensitivity — model results, or a single component heading above Model results | F16 |
| Publication Bias and Small-Study Effects tooltip | Small-study effects, followed by the existing caution where relevant | F07/F14 |
| Summary → Model Results → repeated pooled value | One result heading and one clear pooled-estimate sentence, retaining the table | F16 |
| -0.000000 for negligible MD slope/Z | 0 at the selected precision, with a row-aware presentation rule that preserves genuine tiny effects | F04 |
| Missing file (disabled recent entry) | Keep the explicit missing state; provide Locate… / Remove from recent projects in the existing recent-file workflow | F13 |

Retain the concise RevMan-form comparative `Test for overall effect`, explicit H₀ for ambiguous single-arm/diagnostic/entered/coefficient tests, Study added (k), Study omitted, and whole confidence levels. A test against sensitivity/specificity 0.5 is not a clinical-usefulness verdict.

## 6. Native coverage

The [50-cell matrix](MATRIX.md) contains an inspected figure/report pair for each of ten data types × standard, cumulative, leave-one-out, subgroup and meta-regression. Diagnostic component captures and lower-figure evidence supplement it. The maintained native registry and targeted shell/option drives are indexed in the evidence inventory. A menu item being visible is not the same proof as executing its action; each limit below remains explicit.

| Area | Fresh exercised scope | Remaining limit |
|---|---|---|
| Start/recent/workspace | Pristine, normal/maximized, light/dark, existing and missing recent paths, Create/Open/Import cancellation, actual recent open | Missing entries disabled; all recovery/filesystem states not qualified |
| Menus/toolbars | Recursive visible menu/submenu inventory; actual toolbar hover inventory; type-dependent contexts and method forms | Initial diagnostic wrapper corrected in a separate continuation; all ten type-dependent method forms inventoried. Not every item/value combination executed |
| Creation/import/grid | Ten creation paths in native helpers; early CSV wizard, real GTK template Save picker; import mapping/preview; editing, structure and covariate transactions | Most helper pickers use owned paths; exhaustive encodings/dialects and OS failure paths not qualified |
| Analyses | 50 native matrix cells; diagnostic joint/combined/multiple moderator and binary/continuous/diagnostic small-study supplements | Controlled fixtures; no claim for every parameter combination |
| Calculators | Binary/continuous/diagnostic and all twelve existing modes passed in the native finishing registry | Persistence/numerical proof only for completed cases; not every invalid input |
| Results/output | Actual Text/Tables/sidebar, copy/export equality, selection/CSV, independent zoom/Fit width, Change settings; all eleven editor families passed with four-format exports | Actual exported text opened in native xedit; its Unicode glyph handling is limited. Export decoding is not a complete aesthetic inspection |
| Styles | Default/RevMan/BMJ, 3/6 digits for diagnostic, single-arm proportion, binary, MD/SMD, coefficient and entered effects in completed native publication drives | Not every study count/width/style option Cartesian product |
| Help/errors | About, current Quick start, empty workspace/outcome, duplicate covariate, dirty-open cancellation, invalid contour and valid recovery | Full help-link network, all malformed projects and filesystem faults not qualified |


## 7. Accessibility

Native Latin/numeric/mathematical text renders on the inspected Linux host. Tables provide selectable cells/headers, report and figure zoom are independent, and named navigation/shared button sizing improve recognition and reachability. Light/dark palette captures preserve the host palette. These are demonstrated controls, not a screen-reader or WCAG claim.

Complete keyboard-only traversal, focus restoration, Orca/screen-reader relationships, measured contrast, high contrast, fractional OS scaling, multi-monitor behavior and Windows/macOS remain unqualified. Long figures and icon-only analysis actions are still practical accessibility gaps. App zoom does not qualify OS display scaling. The external editor is separately identified; any editor glyph problem must be distinguished from the UTF-8 export bytes and clipboard equality.

## 8. Ranked top ten for round five

1. **F11, medium:** bound/clip bubble null guides to their actual displayed y range.
2. **F12, medium:** finish one consistent weights representation across report/Tables/graphics scene, with existing component identity.
3. **R03/R17, medium:** compact subgroup/long-forest spacing while protecting reading size and zoom.
4. **R02/R18, medium:** carry existing outcome/comparison/follow-up/exposure context into standalone output; improve existing IRR raw-data presentation.
5. **F04, medium:** finish row-aware precision across reports and the separate coefficient renderer; remove negative zero without erasing genuine small values.
6. **A01/A05, medium qualification gap:** drive native keyboard/focus/screen-reader paths and real OS scaling; repair demonstrated failures before claiming accessibility.
7. **F14, low:** make the analysis toolbar consistently recognisable at ordinary window widths.
8. **F16/R01, low–medium:** quiet duplicate report headings and finish the existing subgroup-difference tables.
9. **F13, low:** constrain start cards to content and improve missing-recent-file recovery.
10. **F07/F15, low:** complete terminology, separator spacing and help/tooltips across the same existing workflows.

The next round should finish these existing end-to-end experiences, not add statistical breadth. RCMS is substantially closer to a coherent analysis workbench: the result-first report, explicit nulls, corrected weights/labels and usable start page are tangible gains. It is not yet “great software” in the sense of uniformly polished, effortless output and independently qualified accessibility. Its remaining friction is now largely consistency, density and finishing rather than lack of analyses.

## 9. Limits, execution and replay

Execution is indexed in [OUTCOMES.json](OUTCOMES.json), with exact commands, timestamps, exit codes and log hashes. [FAILURES.json](FAILURES.json) preserves failed-run excerpts verbatim. All 53 selected maintained helper scenarios passed, including the 34-case finishing queue. The 50-cell matrix, shell/design/supplement and remaining diagnostic/HR/IRR options continuation passed. Doctor is separately retained. The options wrapper failed after seven method-form families because it expected AnalysisSetupDialog for diagnostic data; diagnostic analysis itself passed in the matrix and supplements. The corrected diagnostic/HR/IRR continuation passed; this is an audit-wrapper failure, not evidence that the production dialog cannot open.

The failed run ends verbatim:

```text
AssertionError: ('modal did not open', <class 'rc_metastudio.analysis_setup_dialog.AnalysisSetupDialog'>)
```

The [actual export in native xedit](screenshots/shell-exported-report-editor.png) retains clinical identity and table rows. xedit misrenders some Unicode glyphs; UTF-8 file contents and clipboard/export equality were checked separately. The prior intermediate-file capture was rejected and retained in ignored raw storage.

The audit began at `f1aa24d`; subsequent commits are audit-only. R 4.6.1 and the round-four test-owned library were selected through round-three ENV.sh with RCMS_R_HOME/RCMS_R_LIBS/RCMS_QT6_BUILD_ROOT. Doctor passed on visible xcb. All 55 receipt-bound source files and 24 installed RCMetaR files matched before driving. The independent authority sweep passed 91/91. The prior round-four full-profile/415-field exact-equivalence claims were reviewed as historical implementation evidence; this audit does not relabel them as its own fresh full-profile qualification.

The matrix and supplemental scripts own their settings, inputs and windows. They use real Qt/R composition and X11 window grabs. Maintained helpers use real native windows but their PNGs are QWidget.grab captures; the inventory labels the distinction. Native helper file-picker substitutions, early CSV entry differences and controlled error triggers do not qualify every OS picker/filesystem failure. Opening a real exported report in a native editor is separate evidence from decoding or reading the saved bytes.

Two early matrix processes briefly overlapped; their settings/R state were separate, but some desktop frames showed the other audit window. Those frames were rejected and the binary/proportion families were serially recaptured. No covered frame is used as a product finding. Some early report captures retain a plot sidebar selection because the inherited audit wrapper called a private view method; the later actual-toolbar design drive proves production navigation synchronization. Review-sheet generation was attempted twice before final screenshots existed and raised AssertionError; those were bookkeeping failures, not failed desktop analyses. Capacity interruption paused this agent's inspection/reporting; the owned runners continued, and completed runs were recovered rather than restarted.

Some helper editor QWidget captures contain underlying plot paint through controls; these were rejected as visual acceptance evidence, with no unsupported opacity-regression claim. Their successful control/export assertions remain execution proof. A calculator-sheet selection also raised StopIteration before the new receipt had been curated; selection succeeded after refreshing the curator.

Literal inspection of every possible control value, dependency state and option combination is not established. The coverage inventory records real method forms, available menu/control choices and exercised workflows; it distinguishes those from untouched combinations. Native release packages, other platforms, filesystem exhaustion, malformed encodings and full accessibility are not qualified. No application source, tests or R package code was edited.

Replay and provenance: [RUN-MATRIX.sh](RUN-MATRIX.sh), [RUN-NATIVE.sh](RUN-NATIVE.sh), the targeted native shell/options/precision/extra scripts, [OUTCOMES](OUTCOMES.json), [FAILURES](FAILURES.json), [PROVENANCE](PROVENANCE.json), [EVIDENCE](EVIDENCE.json), [INSPECTIONS](INSPECTIONS.json), [MATRIX-RUNS](MATRIX-RUNS.json), [DESIGN-RUN](DESIGN-RUN.json) and [AUTHORITIES](AUTHORITIES.json). Raw logs/work files remain in ignored raw storage or artifacts/verification/rcms; committed records retain exact commands, outcomes, paths and hashes. Every screenshot cited in this report or MATRIX.md was visually inspected; incidental execution captures are not represented as an aesthetic review.
