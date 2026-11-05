# Amino subgroup Windows golden review

Merged origin/master (including #563) before qualification.

Source: GitHub run 41954711509, checks job 127007002269, artifact
full-r-stack-windows-golden-capture (artifact ID 13383225884).

Descriptor diff (rendering DPI, not embedded PNG metadata):
- master: 9653 × 9230 pixels, 600 DPI, 356388760 bytes RGBA = 339.878807 MiB
- guarded: 1931 × 1846 pixels, 120 DPI, 14258504 bytes RGBA = 13.597969 MiB
- reader limit: 268435456 bytes = 256 MiB

Thus the master raster already exceeded Qt's default reader limit on Windows.
The local QImage proof rejects the exact old Windows PNG and loads the new one.
This does not imply the SVG itself could not render: master eagerly decoded the
oversized PNG for the SVG context menu.

Only the preview DPI changes in product rendering; canvas geometry, plot data,
labels and statistical fitting do not. All original Subgroup Summary and
References text match the current capture exactly. The capture additionally
contains Inference Method, covered by an existing accepted exception.

Refreshed with the existing mechanism:
python scripts/regenerate_golden_presentation.py /tmp/564-golden

Only the amino subgroup PNG and its SHA metadata changed inside the frozen ZIP.
All other cases, text, parameters and numerical outputs were asserted unchanged.
The numeric contract changes only its archive SHA binding, not any reference.
See verification.log: replay against the downloaded Windows capture gives
462 pass / 13 existing accepted exceptions, no drift.
43 existing golden comparator tests pass. Strict Ty (win32 target) passes.

No fresh Windows R execution was performed locally; the sanctioned CI capture
was replayed. The PR push reruns CI against the merged branch.
