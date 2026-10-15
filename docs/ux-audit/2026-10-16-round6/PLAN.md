# Round 6 plan — written before implementation

Starting revision: 80e4bee, branch ux/audit-improvements. Linux native Qt, pinned
R 4.6.1 and the round-three test-owned library. No new statistical procedures.
Original 415 numerical fields and independent authority/golden gates remain exact.

## R5-10 — first: numeric input integrity

Failure modes to trace and prove before changing product code:

- Display rounding written back into raw model values or reconstructed summaries.
- Validators/spinbox decimals truncating a legal finite value or rejecting exponents.
- Float formatting in calculator tables, line edits, grid EditRole and delegates.
- Accept/focus-out/commit rereading a rounded preview; invalid CI commit continuing.
- Project serialization rounding, converting types, or selecting stale effect sources.
- CSV import/export formatting losing digits, locale commas, or exponent notation.
- Dialog and workspace undo/redo restoring rounded/stale input or derived summaries.
- Locale decimal separators parsed differently by different editors.
- Very large values/scientific notation overflowing, becoming zero or losing digits.
- Previously generated SD/SE/CI/P summaries being mistaken for independent supplied
  inputs after an authoritative field changes; obsolete derived preview persists.

Proof: extend retained real keyboard E2E before implementation. Cover every existing
calculator mode, applicable tiny/huge/many-decimal/exponent values (counts remain
integers and proportions remain in range), decimal commas, grid editing including
unchanged commits, Accept/Cancel, undo/redo, CSV and save/reopen. Assert exact floats
at model/storage boundaries; compare effects and subsequent real fits against
independent math/public package calculations. Reject invalid bounds without commit.
Capture before/after screenshots and observed values; retain failing baseline.

## Remaining priority order and required proof

| Item | Failure to prevent | Real-system proof planned |
| --- | --- | --- |
| R5-09 | Internal key used instead of contextual display identity | Attached menu recursion for ten families, open dialogs/choices/tooltips and result text; fail forbidden built-in labels, preserve user names; retain sweep in E2E |
| R5-04 | CI caps larger than study spacing | Short/65-study standard/subgroup, default/RevMan/BMJ; measure SVG cap-to-row geometry, display and export; fitted horizontal values unchanged |
| R5-06 | Headers cross unequal wrapped arm names | Three styles with long custom names; measured SVG header blocks and native/export inspection |
| R5-03 | Diagnostic coefficient/ML tables bypass precision | Two and six digits, numeric/factor/interaction diagnostic regressions; Text/Tables/copy/export equality; independent fitted fields unchanged |
| R5-01 | Fitted SE beside transformed estimate without scale | Sequential/subgroup all transformed families, readable fitted-scale headings in report/Tables/export |
| R5-11 | Hidden bands still in legend | Regression/CI/PI toggles with legend on, all styles, displayed SVG and exports; keys match marks |
| R5-07/D04 | Invalid contour fields and unhelpful eligibility | Invalid submit stays in configuration with inline reason; recover/run; excluded-study reason reflects actual inputs |
| R5-08 | Requested unsupported style silently ignored | Each affected figure family's setup/editor shows available layout or explicit fallback explanation |
| R5-05 | Raw package labels reach reports | Reachable labels sweep plus diagnostic outputs; readable display boundary without renaming model/package identities |
| R5-02 | Duplicate generated captions | New default captions have one identity; explicit investigator text preserved through edits/reopen/export |
| Group: Group | Unnamed default group repeated | Single-arm context hides unnamed default, meaningful custom group remains; inspect analogous context |
| Accessibility/shell | Contrast/focus and window-state races | Native keyboard focus/restore and sampled palette contrast; project-shell waits boundedly for real Qt/WM settled states, original assertions retained |

No isolated tests are planned initially; extend actual Qt/R drivers and existing
R geometry/authority checks. If isolation becomes necessary, list its distinct
failure modes and write that check before implementing the corresponding change.

## Execution and evidence

Commit/push this plan first. Fix and prove R5-10 before other product changes.
Keep small commits, push each fast-forward immediately; on failure wait 30 seconds,
retry once, then stop/report. Reinstall changed RCMetaR before desktop driving.
Reuse round-five recorder/install/drivers and pinned environment. Raw logs go in
ignored raw/. Curate inspected before/after screenshots, contact-sheet.html, README,
CHANGES (items → commits → evidence), TESTS (commands/exits/verbatim failures),
COMMITS and REPRODUCE.sh. Update HANDOFF with proved paths and explicit limits.
Run numerical equivalence, golden gates, affected fresh native drives, then once
`verify_all.py --full --fresh`. Preserve every failed attempt and exact result.
Extra taste changes require an addition to this plan before implementation.
