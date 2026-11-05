# Windows golden and shard/package correction proof

Base includes the user's two fixes: **5c213523**. Run **42024841510**,
checks job **127237038438**, shard (3) **127237038379**, package job
**127237038608**. No numeric reference values or tolerances changed.

## Trusted Windows input

The checks-evidence artifact contains desktop receipts. The actual golden input
is the separately uploaded **full-r-stack-windows-golden-capture**, artifact
**13414176767**. Its downloaded ZIP SHA-256 exactly matches GitHub's digest:
`f2944e50d964a65d7741ac3bfcd545fb2cf01569685d4d33a48baecb16ce42a4`.
See `download-provenance.json`. All PNG SHA bindings were independently verified
against the original per-case captures before the sanctioned updater ran.
The original manifest/report/captures remain unchanged under
`/tmp/ci575-golden`; only hash-verified bundle paths were relocated in
`build/batch7-windows-updater`, with the ledger in `capture-relocation.json`.

`apply_windows.py` invokes `scripts/regenerate_golden_presentation.py`.
`audit_update.py` proves exactly ten PNG replacements and the necessary
artifact/archive SHA bindings. JSON serialization whitespace can differ;
**all text, numeric outputs, parameters, descriptor policy and tolerances are
semantically identical**. The numeric contract differs only in archive binding.
`windows-strict-replay.json`: **462 pass, 13 existing accepted exceptions, zero
drift**, replaying the original Windows manifest under the existing exact policy.
`linux-strict-replay.json`: the ordinary real-R Linux golden gate also passes.

## Geometry and numbers

Ten retained `*-pair.png` files show before/current Windows pixels. Visual review
finds sentence-case headings/metric names, compact adaptive small limits, and
label-width-driven horizontal layout changes only. The standard amino plot is
byte-identical and was not replaced. These frozen cases do not set custom
Favours text; the earlier Batch 7 native evidence covers those labels.

`check_windows.py` compares every dark data-mark pixel in nine plots under
horizontal layout translation (and axis normalization for omission). The bound
is two raster pixels per coordinate. It includes CI strokes, estimates,
pooled diamonds and reference lines, excluding text/annotation/footer regions.
For continuous regression the four-pixel canvas-width change rescales the axis:
all circle-fill component centres agree within two pixels after normalization;
0.0544% of dark curve-edge pixels differ beyond that edge bound. This residual is
reported, not hidden or accepted as a numerical tolerance. The full-precision
proof below establishes that the underlying regression coordinates/predictions
are identical. `windows-data-marks.json` retains the measured bounds.

`check_data_coordinates.py` runs all eleven actual golden workflows with the
original a1ae1b49 and current plot producers, in the real Qt/R stack. Every numeric
leaf of **every persisted plot-data field** is compared with R `identical()`;
only elapsed runtime is excluded. Fits, effects, confidence limits, standard
errors, weights, raw data, covariates and plotting coordinates are identical.
`data-coordinates-proof.json` records per-field leaf counts. This Linux execution
is supplemental data proof, never a substitute for Windows reference pixels.
All **416** frozen numerical fields also match the original Windows capture
exactly, without applying their statistical tolerance.

## Shard corrections

- Fixed numeric matrix/coefficient tables again use fixed decimals; the original
  nonzero-never-zero fallback remains. Adaptive effect/CI presentation no longer
  leaks into matrix tables. The diagnostic precision test was **not changed**.
- `project-table-covariates` also had an old `Subgroup Summary` lookup; only that
  literal was changed to `Subgroup summary`.
- The meantime export is now **9676 px** wide on both platforms. Its width
  shrinks 36 px (0.06 inches at 600 dpi) when sentence-case metric headings are
  remeasured. Height stays **19694 Windows / 19679 Linux**. The body-font floor,
  DPI and height assertions remain unchanged. The exact expected width was
  updated, not relaxed. All three failed scenarios pass locally with receipts.

## Exact-archive package diagnosis

This failure is **not** a Windows plot-reference mismatch. Both locale SVG
hashes are identical. The original evidence says passed/clean exit, but the
inspector's expected normalized summary hash was stale. Changing only
`Metric: Odds ratio` back to `Metric: Odds Ratio` reproduces its previous hash
`61ea84ba…`; the current spelling produces `16303526…`. The Windows/macOS
inspectors and direct packaged-automation bindings now use that verified hash.
`check_package.py` replays the original exact-extracted evidence through the
unchanged smoke validators. Both pass (`package-proof.json`); no guard or
comparison policy was loosened. Original evidence is retained in `package/`.

## Repeat

Source the QA environment; set PYTHONPATH to this worktree and select the
installed `build/rcmetar-review-lib` RCMetaR. Use the shared locked Python env
with `UV_PROJECT_ENVIRONMENT=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/.venv`.
Always use `uv run --no-sync`.

```
gh run download 42024841510 -n full-r-stack-windows-golden-capture -D /tmp/ci575-golden
gh run download 42024841510 -n RCMetaStudio-0.5.1-windows-x64-diagnostics -D /tmp/ci575-diagnostics
uv run --no-sync python artifacts/batch7-windows/check_windows.py
uv run --no-sync python artifacts/batch7-windows/check_data_coordinates.py
uv run --no-sync python artifacts/batch7-windows/apply_windows.py
uv run --no-sync python artifacts/batch7-windows/audit_update.py
uv run --no-sync python artifacts/batch7-windows/recompare_windows.py
uv run --no-sync python artifacts/batch7-windows/check_package.py
uv run --no-sync python scripts/verify_rcms.py project-round6-polish
uv run --no-sync python scripts/verify_rcms.py project-table-covariates
uv run --no-sync python scripts/verify_rcms.py subgroup-image-dark-large
git fetch origin master
uv run --no-sync python scripts/verify.py pre-push
```

Run the updater from base 5c213523; replay/audit can run after refresh. The exact
Windows package itself must rerun in Windows CI; this host replays its original
evidence without claiming a new packaged Windows execution.
