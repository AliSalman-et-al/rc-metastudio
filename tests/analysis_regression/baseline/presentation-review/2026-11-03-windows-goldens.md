# Windows presentation goldens after sheets UX

Base: `bca2b333947fe951f65e1581c9e6e65c8f86ab84` on `ux/sheets`.
Original failure: [run 41561334631](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/41561334631).
Artifact `13197674507`, `full-r-stack-windows-golden-capture`, has SHA-256
`ced16a56262e9b3e2b15667abcc61057f3f4365ffdacf8f71bdcb0436f9f0810`.
The downloaded ZIP digest was verified before refresh; see
[download provenance](2026-11-03-windows-goldens/download-provenance.json).

The reviewer (the user) personally inspected all ten old/new Windows pairs and
approved every change: compact effect-axis ticks for continuous and sequential
plots, shared label baselines and tightened spacing, and the authorized
subgroup-difference statistic already recorded in
[statistical reference decisions](statistical-reference-decisions.md). Amino Q/p changes from
0.187/0.666 to 0.307/0.579; continuous from 0.226/0.634 to 0.293/0.589,
with label Qm → Q. Rows, estimates and intervals are unchanged.
Continuous meta-regression is visually identical; only its bytes differ.
This records the reviewer's inspection, not a new agent visual review.

| Case | Reviewed old/new Windows PNG |
| --- | --- |
| amino-binary-cumulative | [old/new](2026-11-03-windows-goldens/amino-binary-cumulative-pair.png) |
| amino-binary-leave-one-out | [old/new](2026-11-03-windows-goldens/amino-binary-leave-one-out-pair.png) |
| amino-binary-random | [old/new](2026-11-03-windows-goldens/amino-binary-random-pair.png) |
| amino-binary-subgroup | [old/new](2026-11-03-windows-goldens/amino-binary-subgroup-pair.png) |
| continuous-cumulative | [old/new](2026-11-03-windows-goldens/continuous-cumulative-pair.png) |
| continuous-leave-one-out | [old/new](2026-11-03-windows-goldens/continuous-leave-one-out-pair.png) |
| continuous-meta-regression | [old/new](2026-11-03-windows-goldens/continuous-meta-regression-pair.png) |
| continuous-random | [old/new](2026-11-03-windows-goldens/continuous-random-pair.png) |
| continuous-subgroup | [old/new](2026-11-03-windows-goldens/continuous-subgroup-pair.png) |
| lymph-diagnostic-random-dor | [old/new](2026-11-03-windows-goldens/lymph-diagnostic-random-dor-pair.png) |

The sanctioned `scripts/regenerate_golden_presentation.py` refreshed only these
ten Windows plot artifacts. Only hash-verified `bundle_path` locations were
relocated in a working copy of the per-case captures; the downloaded capture and
actual manifest remain unchanged. See [relocation ledger](2026-11-03-windows-goldens/capture-relocation.json).

Replay of that unchanged Windows actual manifest through the existing strict
comparator: **462 pass, 13 existing accepted exceptions, zero drift**.
See [full replay](2026-11-03-windows-goldens/windows-strict-replay.json).
[Archive audit](2026-11-03-windows-goldens/archive-audit.json) confirms every text,
numerical output and non-hash case metadata is unchanged. Only ten plot hash
bindings and the corresponding PNG members changed inside the archive.
Outer archive/contract hash bindings and archive size were refreshed; numeric
values, tolerances, descriptors and exceptions remain frozen.

## Repeatable verification

The original base-specific refresh and replay source is retained as
[refresh-and-audit.py.txt](2026-11-03-windows-goldens/refresh-and-audit.py.txt)
and [replay.py.txt](2026-11-03-windows-goldens/replay.py.txt), with identical bytes.
Those sources contain historical machine paths and original output destinations.
Use them to inspect that review, not to overwrite current references. For current
comparison commands, use the [baseline guide](README.md).

Historical Local Linux strict after refresh: **462 pass, 13 existing accepted exceptions, zero drift**. Linux is unaffected. See [full report](2026-11-03-windows-goldens/linux-strict-report.json); real-R capture inputs, outputs and artifacts are retained at `build/qt6-verification/golden-compatibility-2026-11-03/`.
