# RCMS UX audit implementation — 13 October 2026

Implemented on `ux/audit-improvements`; no push or PR. This report covers the
recommendations in [the native audit](../2026-10-13-native/REPORT.md), including
its Top 10 and microcopy review. Statistical computations and frozen numerical
oracles were not changed. Backend metric keys and the CSV storage schema remain
the statistical/import contract; presentation labels can differ from those keys.

`done` means the stated bounded recommendation was delivered. `partial` names
both the delivered behavior and remaining work. `skipped` is a deliberate scope
decision or a verification gap, not a claim that the original problem vanished.

## Commits

| Commit | Change |
| --- | --- |
| e78ee751 | Readable results, analysis identity, visible copy/export controls |
| 779afe36 | CSV mapping, template, and inline import/name validation |
| ba8125af | Active analysis page sizing, scale explanations, correction controls |
| 56af5d9b | Workspace guidance and clearer study/structure controls |
| 312441b9 | Subtype identity and usable enlarged result text |
| 629404e0 | Real desktop proof of exports, mapping, and input recovery |
| 1e69d5a2 | Empty-workspace help and native scale evidence |
| f78744be | Single-arm group identity in result headers |
| b0aa76de | Covariate validation in both editors and complete prevalence values |
| b0ed8b91 | Explain missing-data analysis prerequisites |
| 8cbdeddf | Reject cleared required mappings; preserve regression axis defaults; fit wrapped context labels; prove recovery |
| 3cacb3d | Supply required CSV fields in the existing parser-error fixture so it reaches the intended failure boundary |

## Finding map

Evidence aliases below link to selected screenshots. Full action/result records,
runtime identities, inputs, exports, and manifests are indexed in
[finish-evidence.json](finish-evidence.json). A screenshot illustrates the UI;
the corresponding assertions and saved/reopened inputs establish behavior.

| ID | Status | Delivered behavior / remaining work and reason | Commit(s) | Screenshot evidence |
| --- | --- | --- | --- | --- |
| L01 | partial | Fit wizard content to active page; import mapping/preview use tabs. A step indicator and an exhaustive native creation-page sweep remain open. | 779afe36, ba8125af | [CSV mapping](screenshots/csv-cleared-required.png), [creation](screenshots/onearm-creation.png) |
| L02 | partial | Neutral project state and Create/Import/Open actions in an empty workspace. A dedicated example-dataset button was not added; examples remain available through Open. | 56af5d9b, b0ed8b91 | [Workspace](screenshots/empty-workspace.png) |
| L03 | done | Honest UTF-8/header instructions, template, required-field mapping, row preview, duplicate/missing mapping errors, preserved file, and disabled completion on error. Clearing a field also rejects exact template headers and clears stale payload; restoring it recovers. | 779afe36, 629404e0, 8cbdeddf | [Cleared custom headers](screenshots/csv-cleared-required.png), [exact headers](screenshots/csv-cleared-exact-headers.png), [recovery](screenshots/csv-recovered.png) |
| L04 | partial | Shorter metric/scale guidance and distinct Mean/Coefficient/Entered effect labels. User-defined effect labels/units would require durable metadata and are deferred rather than inferred from outcome names. | 779afe36, 312441b9 | [Single-arm result](screenshots/onearm-results.png), supplemental subtype records |
| L05 | partial | Persistent task/type/metric summary and Create/Import completion verbs. A complete final review including all import options/outcome details is not a separate new page. | 779afe36 | [Import](screenshots/csv-recovered.png) |
| L06 | partial | Picker begins in Documents/current selected folder; UTF-8/delimiter, row count and covariate types appear with preview. No cross-session last-import-folder setting or automatic encoding/delimiter detection was added; UTF-8 is the explicit contract. Native picker interaction is unverified. | 779afe36 | [Preview](screenshots/csv-recovered.png) |
| G01 | partial | Grid Events/Total, Mean/Coefficient/Estimate and Numeric/Category labels replace compressed labels. Group-header redesign and covariate-width caps are deferred; manual resizing remains. Legacy CSV header names are intentionally retained for existing files. | 56af5d9b, 312441b9 | [Grid](screenshots/small-ratio-grid.png) |
| G02 | partial | Hide unused second-arm columns for one-arm proportions/means and raw columns for entered coefficients. A complete input-mode redesign of every calculator is deferred. | 56af5d9b | [Single-arm grid](screenshots/onearm-grid.png) |
| G03 | skipped | The palette/selection and calculated-cell legend were not redesigned. Changing shared selection/error semantics needs a separate theme/high-contrast visual qualification; guidance now explains how raw/entered data are used. | — | [Current grid](screenshots/small-ratio-grid.png) |
| G04 | partial | Outcome/follow-up text uses the theme's normal plain-text colour. The existing compass navigation remains; replacing its selection model was deferred beyond this presentation pass. | 56af5d9b | [Workspace/grid](screenshots/small-ratio-grid.png) |
| G05 | partial | Row calculators identify the actual study in their title. Named-group reuse and progressive disclosure across binary/continuous calculator modes remain a dedicated interaction redesign. | 56af5d9b | [Diagnostic calculator](screenshots/diagnostic-calculator.png) |
| G06 | done | Diagnostic numeric editors expand to show full values; prevalence explicitly states the 0–1 convention. Existing calculation/input behavior is preserved. | ba8125af, b0aa76de | [Diagnostic calculator](screenshots/diagnostic-calculator.png) |
| G07 | skipped | No focus-dependent rounding or wholesale calculator layout conversion. These edits must preserve entered precision and distinguish committed values from previews; existing calculators remain fully tested. | — | Existing calculator E2E records in finish index |
| G08 | skipped | No destructive menu reordering/category conversion redesign in this pass. Existing delete/convert transactions are retained; a new conversion explanation and confirmation flow require targeted destructive-action proof. | — | Existing structure/table E2E records |
| M01 | partial | New Dataset is also in File; small-study action uses the domain name. Metric-menu flattening and comprehensive menu/ellipsis normalization remain open to avoid conflating cosmetic edits with routing changes. | 56af5d9b | [Workspace](screenshots/empty-workspace.png) |
| M02 | partial | Main and result windows identify project/analysis; project path is in the status tooltip. Recent-file missing-path indicators and disambiguating duplicate names are unchanged. | 56af5d9b, e78ee751 | [Reopened project](screenshots/mapped-reopened.png), [result](screenshots/readable-report.png) |
| M03 | partial | Workspace explains covariate prerequisites and disabled analyses; actions have prerequisite tooltips. Dedicated keyboard-reachable Add buttons in each empty covariate panel are not added. | 56af5d9b, b0ed8b91 | [Guidance](screenshots/empty-workspace.png), [structure](screenshots/structure-editor.png) |
| M04 | partial | Structure actions have visible Add/Remove text and target-specific accessible names; guidance explains double-click rename and covariates. The list-pane model and explicit Rename buttons are unchanged. | 56af5d9b | [Structure](screenshots/structure-editor.png) |
| S01 | done | Confidence dialog explains actual scope; result text/figure zoom is exposed at point of use. No new preferences subsystem. | 56af5d9b, e78ee751 | [Result controls](screenshots/plot-toolbar.png), confidence dialog source/E2E |
| D01 | partial | Complete method/parameter hints contribute to initial size; inactive plot tabs no longer force method-page scrolling. Native default and scale probes pass. Exhaustive labels, monitor/text scaling and every dialog size remain unqualified. | ba8125af, 312441b9 | [Setup](screenshots/analysis-setup.png), [200%](screenshots/report-200.png) |
| D02 | partial | Setup titles include workflow/outcome and use Run analysis; selected model and parameters reach report identity. Backend descriptions are not comprehensively rewritten. | ba8125af | [Setup](screenshots/analysis-setup.png) |
| D03 | partial | Sequential/subgroup and group column labels are meaningful; Show controls have accessible column names. Colour swatches, Automatic bounds/reset and basic/advanced figure grouping remain renderer/editor work. | ba8125af | [Cumulative setup](screenshots/cumulative-setup.png) |
| D04 | partial | Progress names the analysis and says fitting model/drawing plots. Separate phase/elapsed updates and interruption were not invented for synchronous R calls; real cancellability needs runtime support. | 56af5d9b | Source `progress_dialog.py`; no live transient screenshot claim |
| D05 | partial | Shared Continuity correction/Apply correction to labels; double-zero exclusion is a checkbox with unchanged enum values. Detailed affected/excluded-study accounting remains in backend output, not a newly computed UI statistic. | ba8125af | [Setup](screenshots/analysis-setup.png) |
| R01 | partial | Narrow remembered navigation, larger text, selectable text report, fit-width figures and explicit zoom. Reports retain aligned preformatted numerical output; native semantic tables/proportional prose remain open. | e78ee751, 312441b9, 8cbdeddf | [Report](screenshots/readable-report.png), [plot](screenshots/plot-toolbar.png) |
| R02 | partial | Workflow/outcome/type/metric/groups/follow-up/model/confidence/estimator/inference identity. Single-arm headers identify only the analyzed group; input-study count is distinguished from model weight count when available. Universal excluded counts and source-project identity are not inferred from rendered text. | e78ee751, 312441b9, f78744be | [Report](screenshots/readable-report.png), [single-arm](screenshots/onearm-results.png) |
| R03 | partial | Selecting a section aligns its heading; plot selection switches to figure view. Integrating/collapsing weights and sticky figure headers are deferred renderer/layout work. | e78ee751 | [Plot](screenshots/plot-toolbar.png), [HR](screenshots/hr-results.png) |
| R04 | partial | Fit-width plot navigation and context in the result surface. Plot font normalization, complete off-scale CIs/arrows, standalone figure identity/direction labels were not changed in R. Exported plots therefore retain their existing renderer limitations. | e78ee751 | [Plot](screenshots/plot-toolbar.png) |
| R05 | partial | Grid values that would round a nonzero estimate to zero use additional significant digits without changing computations. Report/forest p-value, variance and bound formatting policy is not globally replaced. | ba8125af | [Tiny positive ratio](screenshots/small-ratio-grid.png) |
| R06 | partial | Setup/report explicitly state current study order and explain each addition; plot column says Study added. Step/year/cumulative-k columns, direct order selector and reference lines remain R output work. Sorting the table is the existing order control. | ba8125af | [Cumulative](screenshots/cumulative-results.png) |
| R07 | partial | Study omitted heading and report explanation remove ambiguous plot semantics. Backend Overall/`-Study` row labels, studies-remaining and difference columns/reference estimate are unchanged. | ba8125af | [Leave-one-out](screenshots/leave-one-out-results.png), suite records |
| R08 | partial | Report prominently names the subgroup covariate and tells readers to use the subgroup-difference test. No statistic is copied or recomputed to normalize the different backend summary shapes. | ba8125af | [Subgroup](screenshots/subgroup-results.png), suite records |
| R09 | partial | Regression legend defaults on when there is no persisted choice; moderators are in the header. Existing user choices and moderator-axis default are preserved. Unit metadata, accessible study hover and ratio coefficient interpretation remain unimplemented. | ba8125af, 8cbdeddf | [Regression](screenshots/regression-results.png) |
| R10 | partial | Single-arm proportion identity and correct group in all shared headers. Percentage headline/null-test reprioritization would change backend report presentation and remains open. | 312441b9, f78744be | [Single-arm](screenshots/onearm-results.png) |
| R11 | partial | Mean replaces TX Mean in selected mean results and appropriate plot axes. Persisted outcome-unit metadata is absent and was not fabricated. | 312441b9, 8cbdeddf | Single-arm-mean suite and supplemental records |
| R12 | partial | Coefficient/generic effect retain their distinct subtype in shared headers and metric/axis labels. User-defined label/scale metadata is deferred as in L04. | 312441b9 | Supplemental coefficient/generic result records |
| R13 | partial | Neutral ratio/null/log-scale explanation and named comparison in report header. A per-result interval-includes-null interpretation is not newly calculated. | ba8125af | [Binary report](screenshots/readable-report.png) |
| R14 | partial | MD/SMD state first-minus-second and outcome/SD units, with zero as no difference. User-specific MD units and renderer off-scale CI treatment remain open. | ba8125af | Continuous suite records |
| R15 | skipped | Existing diagnostic clinical interpretation is preserved. Regrouping navigation and explaining multiple I² definitions requires a focused validated diagnostic report redesign; no numerical section was removed. | — | [Joint diagnostic](screenshots/diagnostic-results.png) |
| R16 | partial | Two raw diagnostic coefficient section identifiers become readable sensitivity/specificity headings. Factor contrast decoding and false-positive-rate sign interpretation are not guessed; authority-backed semantic mapping remains required. | ba8125af | Diagnostic-regression multiple-moderator suite records |
| R17 | partial | Readable fit-width HR result surface and explicit cumulative order. Weights-in-forest and large-study-list/sticky-heading redesign remain renderer work. | e78ee751, ba8125af | [HR](screenshots/hr-results.png) |
| R18 | partial | IRR retains type/metric/group context in report header and existing exclusion/unit reporting. Extra event/exposure columns and unit metadata on each standalone figure are not added. | e78ee751, ba8125af | [IRR](screenshots/irr-results.png) |
| R19 | partial | Main action says Small-study effects; existing cautious interpretation retained. Dialog-wide renaming, visible funnel legends and expandable backend details remain open. | 56af5d9b | Small-study E2E records |
| E01 | partial | Visible copy/report/plot export, keyboard shortcuts, format selector and saved path feedback; cancellation and actual PDF/text contents proven. Dedicated table CSV export, Open folder and context-derived filenames remain open. | e78ee751, 629404e0 | [Export](screenshots/plot-toolbar.png), [report](screenshots/readable-report.png) |
| E02 | done | Project filename/dirty marker in title; Saved/Opened/Unsaved changes states distinct; full path tooltip. | 56af5d9b | [Reopened](screenshots/mapped-reopened.png) |
| H01 | partial | Task-focused Quick start/shortcuts describes data, CSV, covariates, report/export and interpretation caveats. Copy citation and openable legal/provenance links are not added; external destinations remain unverified. | 56af5d9b, 1e69d5a2 | [Guide](screenshots/quick-start.png) |
| X01 | done | Blank Add disabled; duplicate names leave inline error and form open; corrected name accepts. Both main-window and structure-editor entry points validate before closing. | 779afe36, b0aa76de | [Recovery](screenshots/covariate-error.png) |
| X02 | partial | Empty workspace/data and structure/covariate guidance explain next actions/prerequisites. Dedicated study/covariate empty-state panels and all disabled-action explanations are not claimed. | 56af5d9b, b0ed8b91 | [Workspace](screenshots/empty-workspace.png), [structure](screenshots/structure-editor.png) |
| A01 | partial | QTextBrowser exposes selectable text and heading content; plot descriptions and keyboard export exist. Native semantic table cells and Narrator/NVDA operation remain unverified; screenshots do not establish accessibility compliance. | e78ee751, 629404e0 | [Report](screenshots/readable-report.png) |
| A02 | partial | Removed forced blue rich-text outcome/follow-up colour; theme text now applies. Actual contrast ratios, control boundaries and high-contrast themes were not measured. | 56af5d9b | [Grid](screenshots/small-ratio-grid.png) |
| A03 | partial | Larger result text/zoom, complete diagnostic fields, content-aware dialog sizing; native scale probes supplement ordinary Windows runs. Qt scale factors are not a change to Windows OS scaling; full text-size/motor/small-monitor qualification remains open. | ba8125af, 312441b9, b0aa76de, 8cbdeddf | [200%](screenshots/report-200.png), [calculator](screenshots/diagnostic-calculator.png) |
| A04 | partial | Programmatic column-specific Show names; visible Add/Remove labels with structural targets. The complete label-buddy/checkbox naming sweep remains open. | ba8125af, 56af5d9b | [Structure](screenshots/structure-editor.png), [setup](screenshots/cumulative-setup.png) |
| A05 | partial | Native Ctrl+Shift+E plot export and report actions are exercised. Full keyboard-only focus order, all accelerators/context menus, colour-blind/high-contrast and screen-reader operation remain a separate qualification. | 629404e0 | [Plot export](screenshots/plot-toolbar.png) |

All Top 10 priorities map to the rows above. None of the partial plot/accessibility
recommendations is claimed complete merely because the full desktop matrix passes.

## Microcopy decisions

Applied the table with judgment through the shared controls: neutral project
states; New dataset/Small-study effects; Create/Import completion verbs; shorter
metric guidance; Mean/Regression coefficient/Entered effect identity;
Events/Total and Numeric/Category grid labels; prevalence (0–1); Run analysis;
workflow/outcome titles; Continuity correction/Apply correction to and a
double-zero checkbox; Study added/Study omitted/Subgroup/group-name plot columns;
named Show controls; actual study calculator titles; visible report/plot exports;
and contextual quick-start/empty-state instructions.

The legacy CSV schema keeps `Tx A #evts`/`#total`: silently renaming file headers
would reject existing datasets. Mapping makes those headers optional in user
files while the template documents the exact storage contract. Follow-up `first`
is dataset content, not a claim of baseline timing. No sample metadata was renamed.

Retained the audit's unchanged/Retain entries. Deferred launcher/data-type tile
wording, comprehensive sentence-case/ellipsis normalization, calculator group
labels/Estimate/Sensitivity changes outside the grid, context-menu deletion and
conversion language, Automatic sentinels/colour editors, backend report row labels
and heterogeneity/log-scale wording, and legal/citation links. These belong to the
explicit partial/skipped rows above: no brittle string replacement was used to
rewrite statistical term meanings, units, factor contrasts or stored file data.

## Verification and limits

The [machine-readable result summary](finish-results.json) preserves commands,
counts, durations, exit codes and transcript hashes.

The complete `tests/` selection was run in two lanes. The first full non-R-stack
run produced **984 passed, 1 failed, 2 skipped in 1420.92 seconds**. All **85
desktop workflows passed**, including HR/IRR independent comparisons, sequential
analysis, calculator persistence and decoded exports. The one failure was
`test_csv_import_preview_failure_preserves_error_details`: its synthetic CSV
omitted OR/Lower/Upper, so the new required-column guard correctly rejected it
before its injected parser error. Commit `3cacb3d` supplies those fields without
changing the assertion or product behavior. The full non-desktop recheck result
is recorded below; desktop/R results remain applicable because this correction
changes only that test's input.

- [Full suite log](finish-full-suite.log): 984 passed, 1 failed, 2 skipped; exit 1.
- [Non-desktop recheck](finish-non-desktop-recheck.log): **900 passed, 2 skipped
  in 154.89 seconds**; exit 0. Combined final selections are **994 passed,
  2 platform skips** (900 non-desktop + 85 desktop + 9 R-stack). The full desktop
  selection was not repeated after changing only the parser-error fixture.
- [Serial real R-stack](finish-r-stack.log): **9 passed in 71.21 seconds**; exit 0.
- [Strict typing](finish-typing-final.log): **All checks passed**; exit 0, using the
  repository's generated-form search paths. The initial unconfigured invocation
  reported 85 diagnostics; configured typing then caught one optional table-item
  dereference in the new E2E assertion, corrected with the existing `required`
  helper. Both attempts are retained in `finish-typing*.log`.
- Doctor: passed; native UX acceptance: passed before and after `8cbdeddf`;
  native Qt scale-factor 2 UX: passed; fresh native one-arm proportion: passed.
  Their assertion transcripts/inputs/exports are in the finish index.
- Supplemental native single-arm-mean meta-regression: passed after providing
  the required repository import path, real-R startup flag and absolute Python
  executable; scope is routing/rendering. Earlier launch errors and the one
  manually terminated owned startup process are retained in the corresponding
  `finish-native-mean-regression*.log` files. This run was not an independent
  numerical oracle.

The two suite skips are Windows platform exclusions: the POSIX process-group
teardown contract and the macOS PyInstaller BUNDLE adapter. No missing-R test was
silently skipped. The full R-stack packaging/install lane, exhaustive visual
matrix and release-package qualification were not run by this finishing pass:
no R calculation/renderer/package source changed. Existing independent numerical
desktop and retained R-stack tests were run with the actual pinned runtime.

Native grid copy remains **failed**, not waived or marked passed. The production
Qt/R `project-table-covariates --native` recheck reaches paste/undo/redo, then fails
the copy payload assertion. Earlier retained [Qt-only probe output](native-clipboard-probe.log)
shows an empty clipboard, no formats and lost ownership after `setText`, without
RCMS. The repeatable [probe](clipboard-probe.py) run during completion returned
all four payloads successfully ([log](finish-clipboard-probe.log)); the symptom is
intermittent. The evidence supports an environment/Qt ownership problem but does
not identify the external owner or certify native copy. No RCMS clipboard
retry/cache/workaround was added. Offscreen table/covariate persistence/analysis
proof is reported independently.

Native E2E uses the production Windows Qt platform and embedded R, with test-owned
settings/projects. Picker paths are controlled; CSV proof enters at its import
page. This is source-worktree evidence, not qualification of a release package,
native picker behavior, screen-reader access, OS DPI settings, all keyboard paths,
or every metric/parameter combination. R runtime/package versions are recorded in
each run; version equality is not an installed-source provenance claim. The Python
presentation changes do not require an RCMetaR rebuild and do not claim that the
warm installed package equals a dirty R source tree.

Earlier intermediate failure logs and supplemental records are preserved under
this directory. They are historical attempts, not the final test verdict. The
aggregate supplemental JSON contains four old MD failures; later individual
`twoarm-mean-*-rechecked.log`/status records passed, so that aggregate is not used as
an all-green result.

## Reproduction and retained artifacts

See [FINISH-COMMANDS.ps1](FINISH-COMMANDS.ps1) for exact environment and commands,
and [finish-evidence.json](finish-evidence.json) for original and local evidence
paths, statuses and hashes. Run from the repository root. `uv sync --locked` and
Qt form generation completed successfully before doctor. The tests use Python
3.11.9, PyQt 6.11.0/Qt 6.11.1, R 4.6.1, RCMetaR 0.4.2, metafor 5.0-1, mada 0.5.12,
meta 8.5-0, svglite 2.2.2, rsvg 2.7.0 and tiff 0.1-12.

Selected screenshots, commands, logs, index and this report are committed. Large
raw evidence bundles and the original audit/runtime library remain intended local
evidence files; they were preserved rather than staging the runtime or unrelated
audit materials. The finishing collector verifies original manifest hashes before
copying complete bundles into `evidence/finish/`. The local Git attributes preserve
captured transcript bytes, including native console whitespace/line endings, so
their recorded SHA-256 values survive checkout on another platform.
