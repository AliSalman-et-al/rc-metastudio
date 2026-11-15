# UI/UX review implementation — 15 November 2026

This follows the [whole-app review](ui-ux-review-2026-11-15.md). All eight ranked
priorities are implemented. The user also selected icon family B from the Opus
5.5 High pilot. Earlier accepted grid, outcome-tab and confidence-button choices
are preserved. Work is retained on `ui/desktop-polish-and-icons` in coherent
commits; publication is outside this change.

| Review | Result |
| --- | --- |
| UI-1 | Analysis menus use the shared application style. Advanced and CSV options use native disclosures. Inline errors, Results scene titles/manuscript rules and About links refresh on palette changes. |
| UI-2 | Prediction-interval explanations appear once beneath Model fit, outside Results prose and statistic rows. Transform caveats remain verbatim. |
| UI-3 | Funnel-family editors hide internal render paths. Apply/Cancel remain editing operations; user export remains in Results. |
| UI-4 | Supplementary results preserve original structured tables, complete headers/cells and source titles. References remain prose; unstructured output retains every line. |
| UI-5 | Non-forest vector plots initially fit both dimensions when that preserves at least 9 pt body text. Forest plots and explicit Fit width keep width fitting. All funnel families use clipping-aware PNG previews; PNG metadata retains measured body-text geometry from the source SVG so the 9 pt floor also applies to these previews. SVG publication export remains available. |
| UI-6 | Diagnostic metrics use sentence case and place Next before Cancel. |
| UI-7 | Plot-editor field labels use consistent punctuation and sentence case. |
| UI-8 | Results/calculator tables use bold, data-aligned headers. Results columns stay near their contents rather than spreading across the viewport. |

Home action cards now size to their contents. Fourteen action/analysis designs
use family B, including six compact analysis masters and both calculator
resources. The folder amber is slightly darker for light toolbar contrast.
Compact menu masters are drawn on an 18 px grid. At the user’s request, cumulative and leave-one-out restore the earlier plus/minus mnemonic with prominent operators and simplified study rows. Scientific formula illustrations and application branding are outside this icon pilot. The metric-page definition and converted-input display suggestions were
unranked candidates, rather than agreed implementation priorities.

## Evidence

The [native screenshot viewer](../artifacts/verification/ui-ux-implementation-2026-11-15/gallery.html)
and [proof obligations](../artifacts/verification/ui-ux-implementation-2026-11-15/proof-plan.md)
retain the review surfaces and planned failure checks. The
[icon comparison](../artifacts/verification/icon-design-2026-11-15/index.html)
retains the editable vector proposals and actual-size QtSvg samples.

Native Windows runs use Python 3.14.10, Qt/PyQt 6.12.0, R 4.6.2, current-source
RCMetaR 0.5.4, the pinned development library, and effective 100% scale on this
host. Strict win32 typing precedes GUI work. Source hashes and the installation
transcript are retained under the implementation evidence directory.

- `20261115T093926Z-6dce58b8-ui-crawl`: home/shell, menus, calculators, analysis
  setup and outcome management; native light/dark captures, passed.
- `20261115T110929Z-cfc40d1a-ui-fine-tuning`: 80 native steps, passed. Real
  rendered import-error colours, success recovery, disclosures, complete PI notes
  and supplementary tables, subgroup/Reitsma retention, and initial chart fitting.
  All five funnel variants had zero region-fill pixels outside the plot box;
  fitted funnel text remained approximately 10.2–10.4 pt.
- `20261115T115758Z-f2ba99c5-review1-design`: native home cards at 800×480 and
  800×700 have identical compact heights and fully visible descriptions. Grid,
  menu, theme and keyboard checks passed. This includes the final home-layout
  correction.
- The earlier GUI suite passed all 401 cases in 191.19 seconds, retained in
  `gui-reviewed-transcript.log` and `gui-reviewed-results.xml`. It predates the
  final home-layout and Default interval corrections; it is supporting evidence,
  not a final-source suite pass.

### Final qualification and recovery

Application Python, R and resource files are unchanged since `85a9c298`, the
production revision examined by the final Opus correction review. Subsequent
commits `a89ff0b2` and `319d3e1f` repair verification assumptions without changing
statistical oracles. Each run's manifest retains its actual revision and inputs;
the runs are not relabeled as one green full-profile invocation.

| Gate | Observed result and retained evidence |
| --- | --- |
| Strict win32 typing | Passed before GUI qualification; recovery transcript retains the exact command and `typing/20261115T175256-d96e2f87`. Doctor repeats the gate in `typing/20261115T175701-b22aeac8`. |
| Current-source R gates | `rcms/20261115T115951Z-effbbb8c-complete/00.log`: R CMD check `Status: OK`, 103 independent statistical authority cases, 21 Reitsma visual cases, and 10 Python/R bridge tests passed. The outer profile was interrupted after these gates, before desktop collection. |
| Broad desktop matrix | `rcms/20261115T121307Z-8b956275-complete/00.log`: **127 passed, 7 failed** in 2288.67 seconds. Failures were stale assertions about disclosure event timing, raster dimensions, equal/stretched column widths and the relocated PI note. |
| Seven affected cases | `seven-assertion-recovery.log`: **7 passed** in 173.92 seconds after harness repairs in `319d3e1f`. Covers both subgroup-image cases, analysis-dialog, calculator-binary, ux-improvements and both manuscript-export cases. |
| Opus correction checks | `opus-corrections-targets.log`: **3 passed** in 66.22 seconds: review-workflows, review1-design and plot-workflow-mh-rd. Resolves explicit RevMan weight selection, palette restoration and Default non-table ordering coverage. |
| Final runtime doctor | `rcms/20261115T125702Z-06d9dc49-doctor/manifest.json` records a pass; `stdout.log` contains `WORKFLOW PASSED`. |
| Installed-source provenance | `r-install-default-provenance.json` records source/installed hashes. `installed-source-observation.log` confirms the changed interval and funnel function bodies match the current source. |
| Artifact integrity | `hash-audit-qualification-final.json`: 137 retained matrix/recovery/native/doctor runs, 17,530 file entries, zero missing manifests or hash mismatches. This includes all seven original failed runs and their successful recoveries. |

Paths beginning `rcms/` or `typing/` above are relative to `artifacts/verification/`;
the named logs and JSON files are under
`artifacts/verification/ui-ux-implementation-2026-11-15/`.
The [evidence index](../artifacts/verification/ui-ux-implementation-2026-11-15/final-evidence-index.json)
preserves individual workflow results. Failed and interrupted attempts remain
available. **No single `--full` invocation completed successfully.** The component
gates and affected-case recovery are the qualification evidence for this source.

The broad matrix command was
`uv run python -m pytest tests/e2e -n auto --durations=10`.
The recovery command was
`uv run python -m pytest tests/e2e -n auto -q -k 'subgroup-image or analysis-dialog or calculator-binary or ux-improvements or manuscript-export' --durations=7`.
Runtime environment and the exact child commands are retained in each manifest.

The initial broad offscreen desktop run failed its readiness gate because Qt
selected Agency FB as the default font. Its failed evidence is preserved. The
corrected qualification uses a test-owned Segoe UI directory with required Greek
glyphs; this changes the test environment, not the application's native font.

The first independent Opus review found clipping and error-colour regressions;
its original findings remain in `opus-final-review.md`. The fresh Opus 5.5 High
recheck in `opus-corrected-final-review.md` found all F1–F9 resolved and no remaining
product blockers, including the user-requested plus/minus menu icons. It identified
final-source qualification and evidence freshness as outstanding obligations.
The final correction review in `opus-default-corrections-final.md` accepted the
home and unavailable-interval source fixes, then found verification assumptions
to repair. The [resolution addendum](../artifacts/verification/ui-ux-implementation-2026-11-15/opus-default-corrections-resolution.md)
records their fixes and observed reruns; it is an implementation response, not
another independent Opus sign-off.
The earlier complete run failed during the temporary SVG experiment; another
passed its R/bridge gates but invalidated desktop collection when inputs changed
mid-run. Neither is a passed full profile. Their failed transcripts are retained.
This is source verification on Windows, not release-package
or cross-platform qualification. External DOCX page rendering remains outside
the screenshot inventory; DOCX structure and report text retention are checked.
Synthetic offscreen palette loops establish application-palette response;
following an OS theme change remains Qt's responsibility. Native captures cover
the recorded Windows scale and window sizes, not exhaustive DPI/layout states.

## Results research remains a proposal

The [reconciled Results design](results-presentation-2026-11-15.md) and
[independent Opus research](results-opus-design-2026-11-15.md) cover a separate,
deeper reporting redesign. Its precision, factual-wording, numeric-boundary and
paper-pagination changes are proposed future batches. This UI polish does not
claim to fix the scientific reporting defects identified in that research.
