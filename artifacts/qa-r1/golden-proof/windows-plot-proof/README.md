# Windows leave-one-out reference audit

Source: GitHub Actions run 41820827724, artifact `full-r-stack-windows-golden-capture`.
Only `amino-binary-leave-one-out` and `continuous-leave-one-out` are approved.

The downloaded plots are attached as `*-new.png`. Their narrower canvases are
expected: amino 6391 → 5700 px, continuous 6941 → 6287 px. Heights and row baselines
are unchanged. Absolute canvas coordinates are deliberately not an invariant.

## Before-update proof

`check_windows.py` and `proof.json` check the frozen numerical contract by exact
Python equality, all summary numeric strings, row order/count, descriptor
identity/capabilities, and the original master text after removing only the
`Study omitted: ` prefixes. No displayed number appears or disappears.

The raster audit checks every estimate/CI annotation and the study-label
remainder (including years), both column headings, all four model/inference
footer lines, and the axis tick glyphs. Identical fonts can rasterize a shifted
edge one pixel differently, so the glyph audit allows a two-pixel edge envelope.
It separately extracts every CI endpoint and estimate-square center and compares
coordinates after mapping each image to its own axis. The finite raster
comparison allows two pixels; exact numerical identity is checked separately.
Neither allowance changes any baseline or statistical authority tolerance.

`check_data_coordinates.py` supplements the raster proof with the actual two
sample-project golden cases. It reruns each with the master and current label
producer, then uses R `identical()` on every full-precision effect, displayed
estimate/CI coordinate, SE, weight and fitted statistical value. The numerical projection excludes runtime/call metadata; every projected
statistic is compared exactly. The label vectors permit only prefix removal. This is a
throwaway artifact, not a product test or numerical reference generator.

## Sanctioned update and audit

`apply_windows.py` verifies each downloaded PNG hash, relocates only capture
`bundle_path` values in a working copy, requires exactly the two approved drift
rows, and calls `scripts/regenerate_golden_presentation.py`. It never edits
reference values itself.

`audit_update.py` checks archive members and JSON fields against its pre-update
snapshot. Exactly five archive members change: the two PNGs, their two capture
JSONs (artifact SHA only), and the archive manifest (the same SHA fields).
`numeric-contract.json` changes only its archive SHA binding.
`plot-descriptors.json` changes only the archive binding and two artifact-oracle
SHA bindings. Every other field and all nine other PNGs remain identical.
See `update-audit.json`, `reference-diff-stat.txt`, and `audit.log`.

`recompare_windows.py` reapplies the existing verifier to the downloaded Windows
capture and updated references: 475 rows, no failures. The 13 pre-existing
accepted exceptions remain unchanged. No numerical reference was regenerated.

Commands use the configured private R library and locked Python environment;
outputs are retained beside each checker. Bulk downloads, intermediate runtime
files and the archive snapshot remain local; the proof and new review PNGs are
retained in the PR.

The pre-update reference is anchored at commit
`2974b88b3a9f2727036fde015750a54eb1f99637`. The checker reconstructs old
PNGs from that commit if local copies are absent. The two downloaded per-case
JSONs and Windows manifest are retained; other bulk inputs can be recovered with
`gh run download 41820827724 -n full-r-stack-windows-golden-capture`.
