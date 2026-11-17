# Maintain golden references

The frozen release oracle, accepted tolerances and documented exceptions are
compatibility contracts. Compare current output with those references before
considering a refresh. Inspect every drift and obtain the required independent
justification; a passing current implementation cannot supply its own expected
answer. A presentation refresh must preserve numerical quantities unless a
specific numerical change was explicitly authorized.

[Baseline provenance](../../tests/analysis_regression/baseline/presentation-review/README.md)
retains the reviewed Windows images, downloaded-artifact identities,
before/after bindings and narrowly authorized historical statistical changes.
These records describe their named revisions, not the current source or a new
release. Preserve the bytes and original identity records when relocating them.

Use the [testing guide](../testing.md),
[verification skill](../../.agents/skills/verify-rcms/SKILL.md), and
[release process](../release.md) for current qualification. Source execution,
collection, or success on another platform cannot qualify shipped bytes.
