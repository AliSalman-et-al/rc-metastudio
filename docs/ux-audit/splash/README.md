# Approved startup splash

`scripts/build_splash_artwork.py` is the sole artwork generator. `direction.html`
and `direction.png` are frozen approval references, used by `compare_artwork.py`.
The source logo remains because the generator uses it. The rejected design was
removed by resetting feat/startup-splash to master before implementation.

Build: `uv run python scripts/build_splash_artwork.py`; regenerate Qt resources
with `uv run python scripts/build_qt6.py generate --build-root build/qt6-verification`.
Compare: `uv run python docs/ux-audit/splash/compare_artwork.py`.
The SVG exactly equals the approval reference. The 2x comparison excludes runtime
text and the three-pixel presentation-shadow edge; mean absolute RGB error is
<0.055/255, maximum channel error 48. The live splash design is approved.

Runtime text has no artwork credit. Version comes from meta_globals.VERSION at
top 200. The legal lines are exactly:

> © 2026 Ali Salman and RC MetaStudio contributors.
> Released under GPL-3.0-or-later.

These match the source copyright headers and AboutLegalDialog's GPL-3.0-or-later
license. RCMetaR/DESCRIPTION imports metafor, meta and mada. The runtime names now
use Oxford commas: “Statistics by R, metafor, meta, mada, and RCMetaR.” and
“Built with Python, Qt, and rpy2.” The native probe measures the first line at
13.5 px against the unchanged 344 px clip width: 312 px at DPR 1 and
313.203125 px at DPR 2. The font size is unchanged; the observations JSON
retains these measurements.

## Review evidence

`evidence/commands.ps1` records the exact commands and pinned Windows R 4.6.1
runtime/library. Retained evidence contains only the strict typing transcript,
artwork diff, native 100%/200%/failure screenshots and their observations, and the
failure-mode list written before implementation. Full run output stays ignored
under `artifacts/`.

- Repository-wide strict Ty, win32: passed (`evidence/typing.log`).
- Focused GUI lane: 73 passed; transcript in `artifacts/splash-review-gui.log`.
- Native failure drive: passed, including a main-window Paint event before the
  dialog opens, the exact startup message, and editing/saving/reopening a project
  with analysis disabled. Desktop capture shows the shell behind the open modal.
- Native 100%/200% captures retain the approved geometry and typography. At DPR 2
  the existing screen-bounding helper scales the card to fit this host's screen.

The startup dialog says: “The analysis backend (R) could not start. Install or
repair the pinned R/RCMetaR runtime, then restart RC MetaStudio.” It retains the
existing exception details underneath. Analysis-dialog failures keep their
existing message.

Removed full runs can be regenerated under ignored `artifacts/` with `scripts/verify_rcms.py doctor|project-shell|amino --native` and `tests/e2e/startup_splash_driver.py` (see commands.ps1); `amino` requires `pdftotext` on PATH.
