# Narrowed qualification

Final product source: 14f2538a.
Strict typing (win32 target), unchanged GUI files (73 tests), code-health Gate PASS,
plot-workflow-deeks, small-study-continuous-extended, and subgroup-image all pass.

Only internal previews above 256 MiB decoded reduce DPI. Other previews and all
user exports keep master DPI and rounding. Normal raster loading/scaling is back
to master; refits reload the original file. No golden references were changed.
The meantime drive retains SVG-loaded and forced-failure screenshots and checks
the original 9712 × 19679 user PNG export header without Qt decoding.

Exact commands and runtime identities are in the logs and manifests here.
Full local evidence, including workflow inputs and exports, remains under
artifacts/verification/rcms at the matching directory names.
Earlier evidence outside narrow describes superseded iterations.
