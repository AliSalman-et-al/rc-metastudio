# Round six implementation — in progress

[PLAN](PLAN.md) predates product edits. R5-10 is being implemented first.
Raw exact commands, transcripts and exit receipts are in ignored `raw/`, recorded
with the retained round-three `run.py` and pinned ENV.sh. The real keyboard
baseline `baseline-tiny-sd-focused` failed with:

```
AssertionError: ('raw precision lost', 'continuous-metrics', '0.00001', 0.0)
```

The initial formatter/provenance fix passed a native continuous precision drive,
including exact save/reopen values and independent public metafor analysis.
The expanded twelve-mode/grid/native checks and invalid-CI recovery checks are
still in progress. Early test-driver and stale isolated-fixture failures remain
in the raw receipts; this checkpoint does not claim qualification.
