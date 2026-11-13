# About redesign

The agreed design follows Anki's About layout: centered RC MetaStudio branding,
left-aligned product information, a plain background, and a Close button. Both
the Help menu action and window title read **About**. The dialog remains
resizable and scrolls its content when space is limited.

The main view shows the version, description, maintainer credit, GPL license,
and links to report an issue or read credits and licenses. The credits link
opens the existing GitHub `NOTICE.md`, which retains the original-work attribution
and warranty details. No debug-information feature was added.

Opus 5.5 Medium independently reviewed light, dark, and narrow captures. Its
first review identified poor dark-mode logo contrast and excess transparent
padding. The dialog now crops the existing artwork's alpha bounds for display,
places the logo on white, and left-aligns the version. The source image is unchanged. A second review caught that the large-font
capture enlarged only Close. Removing the text browser stylesheet restored font
inheritance. The drive now enlarges the application font and asserts that both
the browser and its document use that size before capturing. Opus 5.5 Medium approved the final design and evidence
after inspecting the corrected captures at both scales.

## Verification

Evidence: `artifacts/verification/about-20261113/`. The `reviewed/` directory
contains the final light, dark, narrow, and minimum-width captures and observations.
`reviewed/scale-1.5/` repeats the native drive at fractional scaling.

- Full strict Ty: win32 target, passed. Exact command and transcripts:
  `artifacts/verification/typing/20261113T113449-808dde95/`.
- Six affected GUI tests passed: About through the production Help QAction,
  current content and link destinations, frame removal, bundled logo, screen
  bounds, explicit overflow, and keyboard focus.
- Targeted native Linux XCB drive passed at 1× and 1.5×. Default views have no
  scrollbars. Enlarged-font views scroll vertically, the minimum-width view has
  no horizontal scrollbar, and keyboard traversal reaches both links and Close.
  Clicking Close rejects the dialog and leaves the main window visible.

The native drive uses the repository's explicit R boundary double. This is
presentation and interaction evidence, not statistical qualification. Windows,
macOS, packaged builds, screen readers, and browser navigation were not exercised.
The maintained Windows/macOS native probe could not qualify this Linux host.
