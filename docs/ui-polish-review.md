# UI polish review — 15 November 2026

Agreed direction: New project starts a replacement workspace; Add outcome adds
an outcome sheet. Project identity belongs in the title bar. The status bar holds
brief feedback and a native bordered “95% CI…” button, hidden on the home page.
Effect and interval values remain upright. Missing plot styles use Default;
saved plot styles remain authoritative.

The bold, data-aligned headers and centered Include controls are implemented
for visual review, **pending user sign-off**. Row numbers retain their existing
weight. Checkbox focus surrounds the indicator; mouse and Space toggle inclusion.
Tab hover uses an underline; expanding Advanced preserves readable text.

## Evidence

- [Native Windows capture viewer](../artifacts/verification/ui-polish-review/index.html)
- [Passing native workflow manifest](../artifacts/verification/rcms/20261115T073707Z-a7f2c878-review1-design/manifest.json)
- [Steps and observations](../artifacts/verification/rcms/20261115T073707Z-a7f2c878-review1-design/steps.jsonl)
- [Passing sheet-navigation manifest](../artifacts/verification/rcms/20261115T073209Z-3dc2d40b-sheets/manifest.json)
- [Native runtime doctor](../artifacts/verification/rcms/20261115T070117Z-9c8d25a7-doctor/manifest.json)
- [Strict Windows typing gate](../artifacts/verification/typing/20261115T123707-8641448d/command.json)

The workflow passed with qwindows, Qt/PyQt 6.12.0, R 4.6.2, RCMetaR 0.5.4 and
the manifest-pinned authority packages. RCMetaR was installed from this tree into
the test-owned `build/ui-polish-r-library`; no system library was modified.
All 177 retained artifacts across the final native review and sheet-navigation runs were hash-checked after teardown.

```powershell
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
$env:RCMS_R_HOME = 'C:/Program Files/R/R-4.6.2'
$env:RCMS_R_LIBS = (Resolve-Path build/ui-polish-r-library).Path
$env:PATH = "$(Resolve-Path build/poppler/poppler-26.09.0/Library/bin);$env:PATH"
uv run python scripts/verify_rcms.py doctor --native
uv run python scripts/verify_rcms.py review1-design --native
uv run python scripts/verify_rcms.py sheets --native
```

The desktop helper runs and retains the strict win32 typing gate before GUI work.
The native drive proves CI editing/Undo, mouse and keyboard inclusion/Undo,
fresh Default plot configuration, light/dark table/tab and Advanced states,
wizard cancellation and project opening, followed by real analysis/report export.
Before the tab refinement, all 85 affected GUI cases passed; the selection is recorded in
`artifacts/verification/ui-polish-review/gui-tests.log`.

Earlier failed attempts remain under `artifacts/verification/rcms/`: the ambient R
library lacked meta; offscreen Qt selected Agency FB without required glyphs;
the new driver reused an index after Undo replaced its model; and Poppler was
initially missing from PATH. Native runtime setup, a fresh index and the existing
Poppler installation resolved those attempts. The final native workflow exited zero.

This is source UI verification on Windows, not release-package or other-platform
qualification. Saved-style migration was not added; explicit stored styles are
still restored through the existing path. No user project files or commits were changed.

## Design review corrections

The first light-mode preview was rejected: stylesheet palette colors were frozen
from startup, leaving dark headers and pale text in light mode. That preview
was insufficient visual proof despite its workflow assertions passing. The final
run above uses native headers and buttons, checks effective light/dark palette
contrast, and retains new captures after live theme switches. Bold headers and
cells now share one alignment policy (names left, numeric fields right, Include
centered). Numeric covariates follow the same rule. The confidence button has
regular text, a native border and focus/hover treatment, plus a value-aware
accessible name. The Add outcome hover rule survives theme changes.

Outcome-tab option A was approved and applied. The active tab matches the grid
fill; inactive hover uses a subtle background change. Text weight stays constant,
and the selected tab shows an accent only while the tab bar has keyboard focus.
The Add outcome control matches tab height and follows the live palette.


## Outcome tab decision

Opus 5.5 High recommends flat sheet tabs attached to the grid: selected fill
matches the grid, inactive tabs are quieter, hover changes the fill instead of
adding another underline, tab text keeps a constant weight, and the Add outcome
control shares the tab height. The alternative is native Qt RoundedSouth tabs.
Both retain sheet navigation, rename, reorder and scrolling behavior.

The Qt concept captures and their generating script are in
`artifacts/verification/ui-polish-review/`. Reproduce with
`uv run python artifacts/verification/ui-polish-review/tab_options.py`.
These are isolated visual concepts with sample rows, not application E2E proof.
Option A is now applied to the product. The concepts remain for reference.

The final native review checks constant tab widths while selecting outcomes,
matched Add outcome height, and hover/focus captures after live light/dark
switches. The final `sheets` drive also passes switching, overflow visibility,
rename cancellation, add/Cancel/Undo/Redo, drag reordering, keyboard switching,
context-menu deletion/Undo and saved-sheet reopening. All seven workspace GUI
cases passed during the tab refinement (`tab-gui-tests.log` beside the viewer).

The initial tab run caught selected-border width drift; another caught the strip
container retaining its old palette. The fixes reserve the same border space in
all states and refresh the container palette. A redundant scroll-area gutter was
also removed. Failed evidence is retained alongside the final passes.


## Four-pixel gutter follow-up

The dark bar immediately after the last outcome was the content layout's 4 px
right margin, not a tab control. Removing that margin makes the last tab and
Add outcome button adjacent. The native drive now measures their actual widget
edges: the failing run recorded a 4 px gap, and the fixed run records 0 px in both
light and dark mode, with captured hover and focus states.

- Reproduction: `artifacts/verification/rcms/20261115T073627Z-4d5c8697-review1-design/`.
- Fixed: `artifacts/verification/rcms/20261115T073707Z-a7f2c878-review1-design/`.

The fixed native review and strict win32 typing gate pass. The earlier sheet
navigation proof above preceded this spacing-only cleanup; it was not repeated.
