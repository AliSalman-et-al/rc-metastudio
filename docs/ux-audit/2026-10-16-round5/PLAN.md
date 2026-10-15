# Round five plan — before implementation

Baseline: df71e82, ux/audit-improvements, clean. Linux native Qt and pinned R 4.6.1; test-owned library only. No new statistical analyses or numerical changes. Review and independent native re-audit follow this implementation round.

| Priority / item | Failure modes to prevent | End-to-end proof decided before coding |
| --- | --- | --- |
| 1 F11 bubble guides | A zero guide below/above the panel; clipping lost during exports; transformed null uses wrong coordinates | Existing real Qt/R precision and regression editor drives extended with automatic/explicit bounds, inspect SVG panel/reference geometry and decoded exports across metrics |
| 2 F12 weights | Legacy scene block disagrees with structured rows; duplicate weights; HR/IRR row drift; mixed diagnostic components | Existing report copy/export equality and public-fit row checks; scene omits legacy weights while Text/Tables retain exact structured rows; binary, HR/IRR and diagnostic native screenshots |
| 3 Figure readability | Study-count-dependent shrinking; capped height compresses rows; subgroup gaps; export and screen differ | Short/65-study HR and subgroup native figures in default/RevMan/BMJ; inspect SVG text sizes, height, row spacing and scrolling; exports from existing editor drives |
| 4 Standalone context | Missing outcome/comparison/follow-up; invented clinical interpretation; uneditable defaults; context overlaps header | Real project analysis and plot-editor Apply/reopen/Cancel/export; inspect caption, exact supplied metadata, blank removal and investigator direction labels |
| 5 Precision | Negative zero; real tiny values erased; diagnostic renderer differs; selected digits ignored | Existing precision drive plus report/table/figure comparisons at 3/6 digits, tiny-effect fixture and diagnostic coefficients; 415 exact-field and golden gates |
| 6 Accessibility | Unnamed icon controls; broken tab traversal/focus; derived/selection state conveyed by colour alone; scale clipping | Native main/setup/calculator/results keyboard drives, widget names, visible focus and grid cues; native runs at QT_SCALE_FACTOR=1.25/1.5/2; screen readers and Windows/macOS OS scaling explicitly unqualified |
| 7 F14 toolbar | Labels disappear at ordinary widths; shortcuts/prerequisite explanations lost | Main window at normal/narrow sizes, compact labelled analysis menu invokes existing actions; keyboard and prerequisites retained |
| 8 Report hierarchy | Repeated headings/weights/references; free-form subgroup/diagnostic prints; numeric alignment inconsistent | Native Text/Tables/copy/export for standard, subgroup, moderator and diagnostic; inspect result-first section order and use only existing fitted values |
| 9 F13 start/recent | Cards stretch with height; missing-file recovery loses recent entries or opens wrong document | Native maximize/restore; Locate/Remove against owned recent paths; saved storage reread and project identity checked |
| 10 F15/F07 microcopy | Joined metadata; stale title case/tooltips/help | Native navigator, menus, calculators and help; inspect labels and shortcuts |

No extra taste-driven work chosen yet. Add an explicit reason here before any extra change.

## Evidence and gates

Reuse tests/e2e/audit_round3.py, the round-three recorder/installer/numerical_equivalence.py and round-four curate/contact-sheet machinery. Keep exact commands, outcomes and failures in TESTS and raw receipts, inputs and installed-source provenance. Before/after pairs use the committed independent baseline screenshots plus fresh native after captures, with differences in fixture/entry point identified. Inspect retained screenshots, rather than infer aesthetic approval from assertions. Commit/push each small unit fast-forward; retry one failed push after 30 seconds then stop.

At completion run verify_all.py --full --fresh once, numerical equivalence (415 exact) and strict golden gates. Only reviewed presentation text may use the sanctioned refresh tool. Record unfinished/unproven paths honestly. Update HANDOFF, CHANGES, TESTS, COMMITS, README, REPRODUCE and contact-sheet.html.

Verification refinement: the initial round-five bubble loop covered seven original non-diagnostic fixture families, rather than all nine including HR/IRR. Expand that same drive to every supported metric (six two-arm binary, five proportion, MD/SMD, entered/mean/coefficient and HR/IRR), using actual metric actions and the existing setup bound fields. Verify guide coordinates against the bubble panel's clip rectangle, including legacy gray guides, and retain separate metric receipts. This is completion of F11's planned proof, not a statistical extension.

Native inspection caught a 2.0-scale clipped card description despite the initial drive passing. Add a direct label height-for-width contract; allow the card and wrapped label to grow to that height while the existing final stretch owns spare page height. Keep the failed capture as development evidence. Editor visual acceptance uses a desktop-root crop after scrolling the caption into view; direct X11 window grabs with underlying plot paint are rejected, as in the independent re-audit. These are proof/layout corrections within F13/accessibility/context scope.
