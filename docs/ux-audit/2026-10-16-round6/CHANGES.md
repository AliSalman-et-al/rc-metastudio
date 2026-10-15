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
