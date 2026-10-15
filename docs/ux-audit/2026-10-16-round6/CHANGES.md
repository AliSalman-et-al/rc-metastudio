# Changes and proof — work in progress

- R5-10: full-precision calculator item/editor text; compact numeric painting is
  separate from stored text. Explicit input provenance prevents generated group
  SE/CI/P values becoming new imputation inputs. Undo snapshots retain that flag.
  Grid EditRole and clipboard use full stored float text. Unchanged calculator
  focus traversal does not reconvert previews. Failed CI edits block acceptance.
- Retained E2E: twelve calculator modes use actual delegate/line-edit keyboard
  entry, meaningful precision classes, Save/reopen, undo/redo and public fits.
  New grid/clipboard/CSV/entered-effect precision scenario is registered.
- Deleted obsolete isolated rounding and mandatory-overflow tests: the former
  required data loss, the latter required overflow even when compact columns fit.
  Corrected stale fake outcome/UI and explicit-input setup in retained checks.

Native observations, commit mapping and final qualification are pending.

## Presentation checkpoint

- R5-09: contextual metric actions (Mean/Regression coefficient/Entered effect),
  readable diagnostic choices and SMD tile; retained ten-family attached-menu,
  dialog/tooltip/choice/result sweep passed. Current built-ins change; user group
  names remain investigator text. One-arm method families use the metric identity.
- R5-04: disable metafor's device-scaled caps; shared interval-end drawing uses
  row units. Six native 65-study standard/subgroup style routes pass a matched
  whisker/cap bound; SVG exports receive the same check.
- R5-06: BMJ rules/superheadings follow measured wrapped-name height; three styles
  with one-, two- and unequal longer names have vector/display/export checks.
- R5-03: raw numeric result formatting receives the selected result precision in
  one scoped context; Text and Tables use it without changing raw fitted objects.
  Diagnostic numeric/factor/multiple regressions passed two/six digit checks.
- R5-01: transformed sequential/subgroup/calculation tables state the fitted SE
  scale. All 415 original numerical fields stay exact. Reviewed golden text is
  changed only with the sanctioned presentation-only tool (GOLDEN-PRESENTATION).
- R5-11: legend labels and samples follow regression/CI/PI visibility; all three
  styles and twelve toggle combinations passed, alongside decoded exports.
- R5-07/D04: actual eligibility reasons and usable count; validate contour text
  before starting work; failure exits busy state and leaves an editable dialog.
- R5-08: subgroup setup/editor explicitly explain the default-layout fallback and
  style accent colours instead of silently promising standard-forest layouts.
- R5-05/R5-02 and Group: Group: readable package labels, no repeated default
  metric caption, and no unnamed default group line. Researcher text is preserved.
- Shell: bounded stable waits observe actual normal/maximized/fullscreen states
  before placement snapshots and assertions. Original assertions remain.

The first broad Python run found stale round-five default-name/UI/rounding
assumptions; those were corrected or deleted. Replay: 386 passed, 6 skipped.
Repository-wide strict types initially failed (67 diagnostics); introduced nullable
lookups were repaired. Remaining platform and pre-existing audit-driver diagnostics
are being separated from a focused changed-code check. Full qualification pending.
