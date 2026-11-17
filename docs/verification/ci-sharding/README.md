# Desktop CI sharding

CI runs strict R-stack checks and three parallel desktop jobs. Each owns a
freshly built/installed RCMetaR and manifest-validated dependencies. Local
`r-stack` runs the complete suite by default.

`config/desktop-durations.json` holds measured durations used for balancing.
Unmeasured scenarios receive a 60-second estimate and join the lightest bin;
ties use node ID and bin index. Every shard collects the complete suite and
checks that the partition contains each collected node exactly once before
selecting its bin. New cases must not silently disappear. Workers retain full
partitions, JUnit output and per-scenario evidence.

After the repository-wide strict typing gate, inspect a partition with:

```powershell
uv run python -m pytest --strict-markers tests/e2e --collect-only -q --desktop-shard 1 --shard-report artifacts/verification/desktop-partition.json
```

Collection proves partition selection, not desktop execution. The
[testing guide](../../testing.md) and
[verification skill](../../../.agents/skills/verify-rcms/SKILL.md) define the
runtime and evidence requirements. Historical CI timing tables and local
collection transcripts are in Git; they do not qualify a current revision.
