# Test record — in progress

All commands use `source docs/ux-audit/2026-10-14-round3/ENV.sh` and `RCMS_AUDIT_DIR=$PWD/docs/ux-audit/2026-10-16-round5`. Recorder: `uv run python docs/ux-audit/2026-10-14-round3/run.py LABEL COMMAND...`.

- `install-figures`: `uv run python docs/ux-audit/2026-10-14-round3/install_source.py`, exit 0. INSTALLED-SOURCE.json binds owned runtime/library.
- `native-figures-precision`: `uv run python scripts/verify_rcms.py audit-round3-precision --native`, exit 1. Verbatim failure: `AssertionError` at `analysis_matrix.py`, line 209 (old scene duplication requirement).
- `native-figures-precision-recovered`: same command, exit 0, 54.111s. Full per-run artifacts under artifacts/verification/rcms/20261015T020559Z-fd09f011-audit-round3-precision.
- Initial shell invocation used unavailable `python`; exact output: `/bin/bash: line 1: python: command not found`. Subsequent scripts use `uv run python`.
- `install-context`, then `native-context-irr`: `uv run python scripts/verify_rcms.py audit-round3-irr --native`, exit 0, 62.204s. Public-fit sequential/subgroup row/weight checks and report copy/export passed. Retained native subgroup report inspected: aligned interval/statistic table, structured subgroup test, no legacy package printout.
- `native-shell`: `uv run python scripts/verify_rcms.py review1-design --native`, exit 0, 25.693s. Missing recent Remove, Locate cancellation and validated relocation persist through existing recent storage; all original design assertions pass.
