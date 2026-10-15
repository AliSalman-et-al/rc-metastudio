# Reassessment with the corrected lexer

Compared c62df31 with 09c240b and read every extracted body/caller. Corrected
cyclomatic counts below use the repaired lexer on c62df31, before any CI split.
Python counts are unaffected. The unchanged changed-code limits remain 15
cyclomatic / 20 cognitive / 4 nesting, subject to existing exemptions.

| Original function | Corrected original CC | Decision and readability reason |
| --- | ---: | --- |
| verification_evidence.verification_context | 16 | Keep runtime/font-root collection separate from evidence signature assembly. |
| verification_resources.desktop_resources | 13 | Keep cgroup ancestor traversal and limit reading separate from worker selection; removes nested filesystem loop. |
| verify_rcms.main | 22 | Keep scenario timeout, evidence reuse and failure transcript responsibilities separate from process lifecycle. |
| AnalysisSetupDialog._diagnostic_analysis_requests | 22 | Keep ordered/joint request preparation separate from per-request validation and dispatch. |
| AnalysisSetupDialog.__init__ | 19 | Keep result identity/accessibility setup as one stage. |
| AnalysisSetupDialog._restore_settings | 16 | Keep plot controls separate from estimator/moderator restoration. |
| AnalysisSetupDialog._deliver_result | 22 | Keep identity/fit details separate from result ownership/callback delivery. |
| FunnelPlotEditorDialog._load_params | 20 | Keep axis controls and scale-label selection together, separate from appearance/path controls. |
| EditPlotDialog.__init__ | 18 | Keep effect-axis construction as one coherent control group. |
| r_bridge._structured_result_reports | 25 | Keep summary-display extraction distinct from matrix/named-summary dispatch. |
| r_bridge._structured_matrix | 17 | Keep diagnostic coefficient heading conversion as a named operation. |
| r_bridge._format_r_table_cell | 22 | Keep numeric precision/p-value formatting separate from R-value shape/type handling. |
| ResultsWindow._report_table_html | 26 | Keep heterogeneity and interval column transformations distinct from HTML generation. |
| ResultsWindow._setup_report_controls | 17 | Keep initial figure selection separate from navigation construction. |
| ResultsWindow._report_blocks | 25 | Keep each semantic section's ordering/heading work separate from whole-report deferred sections. |
| ResultsWindow.item_clicked | 13 | Keep export-format state updates separate from navigation; reduces cognitive nesting 28 to 12. |
| rcmetar.bubble.axis.ticks | 17 | Keep manual tick transformation distinct from automatic range/tick selection. |
| rcmetar.forest.regeneration.state | 18 | Keep named override validation distinct from sequential/subgroup state construction. |
| rcmetar.continuous.default.ilab | 17 | Keep arm-name precedence distinct from raw column value/heading construction. |
| rcmetar.draw.default.forest | 31 | Keep panel drawing, study marks, annotations and headers as actual drawing stages using bundle/plan; the real branches still exist. Correct helper indentation only. |
| rcmetar.reitsma.plot.data | **8** | **Undo all three style/visibility/axis helper extractions.** Original 37 includes 29 false `%||%` branches. One flat list is easier to follow than three single-use mappings combined by `c()`, and restores field order visibly at the construction site. File now byte-identical to c62df31. |
| create.summary.disp | 21 | Keep prediction-interval presentation and PFT sample sizes separate from overall report assembly. One false `%||%` branch does not account for the real work. |
| create.subgroup.display | 22 | Keep per-fit subgroup/heterogeneity/prediction row construction separate from table assembly. Eight inputs express actual row dependencies and replace loop-wide mutations; no false operator count motivated this seam. |

Thus 22 original refactors are retained, one is undone in an ordinary new commit.
No fit, transform, output oracle, threshold, exemption or operation order changes.
Qualification must establish numerical and visual equivalence; metric success alone
is insufficient. The full table of historical inflated counts remains in
CI-COMPLEXITY.json and is not relabelled corrected evidence.
