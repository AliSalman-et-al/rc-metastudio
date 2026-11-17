# Verify HR and IRR workflows

The [user guide](hr-irr.md) describes supported inputs and interpretation.
[ADR-0010](adr/0010-distinguish-hazard-and-incidence-rate-ratios.md) and
the [package reference](hr-irr-metafor-review.md) state statistical decisions.
The [ratio feature map](../.agents/skills/verify-rcms/features/ratios.md) identifies
exercised paths and limits; it is the maintained scenario map.

## Replay

Configure the pinned test-owned R runtime/library and generated Qt resources,
then run the repository-wide strict typing gate before any GUI test, following
the [verification skill](../.agents/skills/verify-rcms/SKILL.md).

```powershell
uv run python scripts/verify_rcms.py ratios-hr
uv run python scripts/verify_rcms.py ratios-irr
uv run python scripts/verify_rcms.py ratios-samples
uv run python scripts/verify_rcms.py options-zero-cells
```

Shared analysis/R changes also require the full profile prescribed by the skill.
Each run retains inputs, exact command, runtime and installed-source identity,
action records, screenshots, decoded exports and saved projects under
`artifacts/verification/rcms/`. Check those manifests after cleanup; an installed
version string alone does not prove that current source was executed.

Check selected raw/reported/log inputs, per-study source confidence, mixed IRR
sources, raw-only MH, non-estimable subsets, sorted deletion and undo/redo,
save/reopen, direct public-package fits, report content, plot editing and exports.
Bundled sample checks retain every original source row and covariate.

## Scope limits

The automated moderator drive is numeric. Factor/interactions, legacy
bootstrap/permutation, every estimator/inference UI pairing and every import
entry point need targeted evidence. CSV automation starts at the import page
with a controlled picker return. Native OS picking, fractional DPI and release
packages require their own drives. Offscreen source evidence does not qualify
other operating systems or shipped bytes. Historical run diaries are available
in Git; their success counts do not qualify the current revision.
