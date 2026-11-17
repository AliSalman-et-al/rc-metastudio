# Presentation-reference provenance

These records belong to the frozen regression baseline. They explain reviewed
changes and retain the evidence needed to inspect them; they do not qualify
current source or authorize another refresh.

- [October Windows review](2026-10-16-windows-goldens.md): artifact identities,
  locale/glyph corrections, reviewed image pairs and exact text differences.
- [November Windows review](2026-11-03-windows-goldens.md): reviewed sheet/axis
  presentation and narrowly authorized subgroup-statistic changes.
- [Statistical reference decisions](statistical-reference-decisions.md): the
  subgroup Q convention, one authorized cumulative P-value addition, and raw-count
  MH/Peto reference semantics.

The dated subdirectories contain original PNG, JSON and diff bytes relocated
from `docs/ci/` and its linked audit review. Original hashes, host paths and
approval records remain historical observations. The two `.py.txt` files are
unchanged historical source captures with machine-specific paths; their suffix
keeps them out of active Python typing and test collection.

The documentation pruning retained a per-file old/new path and SHA-256 ledger
under `artifacts/planning/joss/`; the commit diff records the published relocation.
Frozen ZIPs, numerical-contract files, tolerances and approval bindings were not
changed by that relocation.

Configure the current source and pinned runtime according to the
[verification skill](../../../../.agents/skills/verify-rcms/SKILL.md), run its
strict typing gate, then compare without refreshing:

```powershell
uv run python scripts/verify_golden_compatibility.py --root . --output-root artifacts/verification/golden-review
```

Retain the command, runtime/source identity, input digests, comparison report and
decoded output. See the [reference policy](../../../../docs/ci/README.md),
[testing guide](../../../../docs/testing.md) and
[release process](../../../../docs/release.md) for qualification requirements.
