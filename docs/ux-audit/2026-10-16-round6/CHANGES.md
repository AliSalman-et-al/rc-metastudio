# Changes and proof

Final full fresh qualification passed: 119 desktop scenarios plus doctor, strict
goldens and 91 authorities. All 415 original fields are exact. Individual native
manifests retain their actual source/runtime provenance; EVIDENCE-INTEGRITY binds
final executable bytes and all selected artifacts.

| Item | Commits | Retained end-to-end proof |
| --- | --- | --- |
| R5-10: input loss | 0ae1b2f, f4fe5bf | Twelve `calculator-mode-*` routes: real keyboard editors, valid tiny/huge/many-decimal/exponent inputs, Accept/undo/save/reopen, independent effects/public fits. `calculator-grid-precision`: raw/effect grids, unchanged commits, clipboard and CSV import. `calculator-ratio-precision`: all HR/IRR input sources. |
| R5-09: metric labels | e4b9824, 291c22c | `project-display-labels`: ten data families, attached menus, actual one-arm popups, setup/calculator widgets, tooltips, combos and reports. Every recorded desktop step also checks visible Qt strings and actual SVG text. Investigator names remain. |
| Axis conventions | 4e8f0e5, 2af53d7 | `project-axis-proportions`: PLO/PAS/PFT/PLN × three styles. `project-axis-others`: OR/sensitivity/specificity/MD × three styles. Actual ticks, intervals, diamonds, nulls, toggle/reopen/Cancel, export and rerun persistence. `project-axis-sequential`: PFT cumulative/omission/subgroup endpoints against public subset fits. AXIS-NUMERICAL-EQUIVALENCE: 24 fits/weights exact. |
| R5-04: CI caps | e4b9824, 4e8f0e5 | Disable device-sized metafor caps; shared caps follow actual row spacing. `audit-round3-round5`: 65-study standard/subgroup × three styles. Axis/transform drives cover short figures. Display/export vectors receive the same geometry check. |
| R5-06: headers | e4b9824, 291c22c, 3600c2a, 036a1a5 | `project-round6-polish`: actual header boxes/rules, three name pairs × three styles, displayed/exported SVG. BMJ physical width includes margins. `audit-round3-presentation-transforms`: natural-zero/footer clearance, four measures × three styles and four-format exports. |
| R5-03: diagnostic precision | e4b9824, 8416f96 | `project-round6-polish`: two/six digits, numeric/factor/multiple moderators, raw references, Text/Tables/copy/export. Two-digit cumulative/subgroup SE assertions prevent a hidden three-digit floor. Original non-diagnostic numerical presentation remains exact. |
| R5-01: SE scales | d747d49, 291c22c, 4638cf8 | Fitted-scale report/calculation/sequential/subgroup headings. Ordinary/contour/trim-fill funnel SVG axes and four decoded export formats identify the SE scale. Seven sanctioned golden text-heading changes preserve all original numbers. |
| R5-11: legends | e4b9824 | `plot-workflow-regression`: twelve visibility/style combinations, actual legend entries/samples and four-format exports. |
| R5-07 / D04 | e4b9824, 291c22c | Actual nine-of-ten usable-study explanation. Four invalid contour inputs stop busy state, stay editable and recover to real output. Unchanged defaults contain actual editable `90, 95, 99` text. |
| R5-08: style fallback | e4b9824 | Subgroup setup/editor explain default layout and journal-style accents. Native subgroup/editor workflows retain these capability notes. |
| R5-05 / R5-02 / Group: Group | e4b9824 | Readable package-owned diagnostic names; remove identical captions and unnamed group lines; preserve investigator names. Maintained all-step label guard and ten-family sweep. |
| Accessibility/shell | e4b9824 | Native `review1-design` at Qt 1.5/2: grid/selection contrast, focus traversal, keyboard grid exit. `project-shell`: stable actual normal/maximized/fullscreen states before unchanged placement assertions. Main palette text/base/button pairs meet 4.5:1 here. |
| Extra: result ownership | 82b582a | Planned real close/deferred-delete assertion exposed retained SVG scenes. One-line disposal releases the QObject after saving state. Axis helpers assert deletion through repeated report-view reruns; retained GUI contracts pass. |

The input fix separates exact editor/model text from compact painting. Explicit
supplied-input provenance prevents generated SE/CI/P previews becoming independent
inputs; undo retains provenance. Invalid bounds cannot be accepted; unchanged focus
traversal does not reconvert effects. Obsolete tests requiring data loss or
unnecessary overflow were removed.

Axis projection changes coordinates only. A canonical fitted range prevents double
transforms; automatic bounds/titles stay automatic. PFT sequential display supplies
actual subset sample sizes to the established inverse. Unneeded legacy binary
figure construction was deleted.

FAILURES retains the original tiny-SD loss, stale fixtures, axis persistence and
geometry failures, closed-window ownership, empty default contours, BMJ zero-tick/
footer collision, installation overlap, and overly broad precision formatting
that changed three historical displayed SEs. The first full run was deliberately
interrupted during the footer correction and is not qualification. A separate
wrapper exit 143 is retained without inventing a passing wrapper receipt.

The first complete desktop qualification also caught six-digit diagnostic BMJ axis-title/tick clearance below the unchanged four-point bound. 3600c2a/036a1a5 derive clearance from device character-line height plus a five-point gap; the exact failing driver is replayed before restarting the full profile.

Final status: all requested implementation items have passing affected native proof and the complete fresh profile. The final profile has no failed or skipped desktop scenarios. R CMD check has its single documented opt-in gallery skip; the separate gallery scope/limits remain explicit in QUALIFICATION. External Opus acceptance review and independent native re-audit follow.

## Reviewer fixes — implementation and targeted verification in progress

- 8f997c1 prepares 0.5.0 (dated 2026-10-15), derives runtime VERSION from
  `__version__`, updates the bump tool/lock/R DESCRIPTION and summarizes rounds 3–6.
- 9e4dcdd / 9285a2c remove unnamed single-arm spanners in the shared/default
  layouts, retaining meaningful names. Empty spanner names are absent from layout
  metadata. Single-arm rates are not an offered RCMS data family; the supported
  IRR workflow has two event/person-time arms and is included in native checks.
- 548e354 back-transforms PFT PI endpoints with `transf.ipft.hm`, shares display
  policy across standard/subgroup reports and all forest styles, and uses each
  subgroup's N for its inference footer. Undefined inverse contexts retain labelled
  transformed limits. The existing explicitly named FT-zero test is retained;
  report notes distinguish its null from proportion zero. Public meta/metafor
  inverses agree on six fits (REVIEWER-PFT-AUTHORITIES).
- c7a04b4 labels diagnostic coefficient estimates/bounds as logit and exponentiated
  bounds as OR, using the shared structured tables for Text/Tables/copy/export.
  The R coefficient matrices and their internal keys are unchanged.
- c52e797 shortens setup/editor/funnel style labels to Default, retaining `default`.
- 9e4dcdd / 807656b route every Default forest mark through its existing shared
  accent helper while preserving black study names. Bubble and funnel presets
  already use consistent accents for points/fitted/reference lines; no colour
  change is needed there. Reitsma coefficient marks already share the forest
  accent. RevMan/BMJ renderer colours are unchanged.

Native contracts were added before their product changes. Development failures
are retained verbatim; final native/full-profile qualification is still pending.
