I found one blocker and one small path-state fix. The rest of the dead-code removal is clean. This was a read-only review: I made no edits and ran no tests.

## Blocker

**The verify-rcms advanced drive will crash on the funnel editor.** [advanced_workflows.py:560](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py:560) still checks `dialog.path_label`, `dialog.path_edit` and `dialog.browse_button`. Those widgets no longer exist in `funnel_plot_editor_dialog.ui`, so this line raises `AttributeError` before the wheel-scroll check. If the running native matrix includes that lane, it will fail there.
- **Fix:** delete line 560.
- **Same cleanup:** [ui_crawl.py:297](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/tests/e2e/ui_crawl.py:297) was rewritten to assert that `browse_button` doesn't exist. That only guards something we removed on purpose, which AGENTS.md rules out. Delete it rather than keep it.

## Small fixes

1. **The plot editor no longer unwraps the stored path.** At [plot_editor_dialog.py:475](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/src/rc_metastudio/plot_editor_dialog.py:475), `_image_path = str(image_path or self._params.get(...outpath))` skips two steps the old `_set_text` path did: `_scalar` and `to_native_text`. If the parameter comes back from R as a one-item list and `image_path` is empty, the path is saved as `"['C:/…png']"`. Today every caller in `results_window.py` passes `artifact.image_path`, so this can't happen yet. It is still a one-line fix:
   `self._image_path = qt_text.to_native_text(self._scalar(image_path or self._params.get(self._param_name("outpath"), "")))`
   The funnel side is already safe because `_value` unwraps lists.
2. **Cosmetic:** each deleted method left two blank lines behind, at [plot_editor_dialog.py:304](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/src/rc_metastudio/plot_editor_dialog.py:304) and line 565.

## Checked and clean

- **Add Study removal:** nothing in `src`, `tests`, `scripts` or `.agents` still mentions `AddStudyDialog`, `new_study`, `add_study` or `add-study`. The form manifest, form-ownership inventory, native smoke script and evidence fixture are all updated. Moving the fixture to `add-covariate` is sound.
- **Main footer and CSV page:** nothing still uses `frame`, `control_button_layout` or `confidence_interval_layout`. With the file label gone, the CSV page still shows the chosen file: `main_wizard.py:691` puts the file name on the button and the full path in its tooltip.
- **Funnel editor:** `funnel.outpath` keeps the same order as before (saved value first, then `image_path`), so the saved path is preserved.
- **Workspace:** removing `WorkspaceSession.mutate` left no callers, and `copy` is still used in that file. The `copy` import dropped from `workspace_editing.py` had no remaining users.
- **R:** none of the 20 removed functions is referenced anywhere in R, Python, scripts or tests. I found no lookups that build these function names as strings. The functions the R tests now call do the same thing as the old wrappers: `rcmetar.revman.layout` was a wrapper for `…layout.coordinates`, and `measure.metafor.forest.device` called `default.device.metrics` through another wrapper. The test regex `sub(...)` gives the same result as `canonical_svg_path` for paths that have an extension.
- **Docs:** the cleanup is recorded in `docs/ui-refresh-2026-11.md:64-66`.

I didn't run anything or look at screenshots, so this covers the code only, not a visual UI/UX check. The full matrix, native and R testthat runs are still going, so there's no pass to report yet. Once the blocker line is deleted, the native advanced lane needs another run.
