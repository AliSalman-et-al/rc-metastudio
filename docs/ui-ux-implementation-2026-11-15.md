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
- `20261115T105214Z-02d68633-ui-fine-tuning`: 80 native steps, passed. Real
  rendered import-error colours, success recovery, disclosures, complete PI notes
  and supplementary tables, subgroup/Reitsma retention, and initial chart fitting.
  All five funnel variants had zero region-fill pixels outside the plot box;
  fitted funnel text remained approximately 10.2–10.4 pt.
- The corrected GUI suite passed all 401 cases in 191.19 seconds, retained in
  `gui-reviewed-transcript.log` and `gui-reviewed-results.xml`. Earlier failed
  attempts remain available. The final dead-code/import/comment cleanup followed
  these runs, so final-source qualification is still required.

The initial broad offscreen desktop run failed its readiness gate because Qt
selected Agency FB as the default font. Its failed evidence is preserved. The
corrected qualification uses a test-owned Segoe UI directory with required Greek
glyphs; this changes the test environment, not the application's native font.

The first independent Opus review found clipping and error-colour regressions;
its original findings remain in `opus-final-review.md`. The fresh Opus 5.5 High
recheck in `opus-corrected-final-review.md` found all F1–F9 resolved and no remaining
product blockers, including the user-requested plus/minus menu icons. It identified
final-source qualification and evidence freshness as outstanding obligations.
The earlier complete run failed during the temporary SVG experiment; another
passed its R/bridge gates but invalidated desktop collection when inputs changed
mid-run. Neither is a passed full profile. Their failed transcripts are retained.
This is source verification on Windows, not release-package
or cross-platform qualification. External DOCX page rendering remains outside
the screenshot inventory; DOCX structure and report text retention are checked.
