# Review qualification

User-requested PNG/TIFF exports retain their requested dpi (default 600).
The meantime PNG export header is 9712 × 19679; no Qt decoder is used on that export.
PDF/DOCX embedding uses manuscript display_images, selecting SVG; DOCX renders page-sized chunks.

Commands and transcripts:
- typing-export-review.log: repository-wide strict Ty, win32 target, PASS.
- gui-review.log: both unchanged requested GUI test files, 73 passed.
- code-health-review-final.log: requested origin/master..HEAD command, Gate PASS.
- export-review-offscreen.log and export-review/: real Qt/R meantime subgroup,
  SVG preview, full-resolution export header, forced plot-load failure, PASS.
- export-review-final.log: final native retry timed out during startup; retained, not a pass.

Statistics, tests named by the reviewer, gate exceptions, and baseline files are unchanged.
