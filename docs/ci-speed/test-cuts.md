# Conservative Python test cuts

This pass removes two exact duplicate tests and merges two pairs of identical
setups into parametrized cases. It removes 52 lines, without changing product
code, references, assertion thresholds, or any GUI test. The ZIP CLI case gains
the inventory assertions already applied to JSON.

`test-cuts.tsv` records original test IDs, including baseline parameter cases.
Keep decisions are conservative: the recorded assertion or rejection boundary
has no established equivalent E2E failure trigger. They are not claims that
mutation survival proves usefulness. No GUI, Windows layout, enlarged-font,
fatal-warning, persistence failure, or parser boundary check is removed.
This is a narrow duplicate-removal pass, not a completed semantic redundancy
audit of every test body and its E2E counterparts.

## Evidence inputs

- Source: `0f34722f1b081f29c3a327cdded110ca571af8ed`.
- `origin/ci/planted-bugs`: `18f9f60ecc6b930030b44d9720d5500050e16502`.
- `origin/ci/baseline-tests`: `cedb30169eb0b7d6af70e13a13ddd67648fd9cb7`.

The fetched results report `state=running`, 13 measured mutants of 31, and no
fast/gui catches. This does not match the complete catcher matrix described in
the task. No deletion relies on that incomplete matrix. The five explicitly
requested mutants are dispatched on CI; no mutant executes locally.

## Local reproduction

Use the supplied warm runtime:

```bash
source /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/build/sheets-baseline/ENV.sh
export RCMS_R_LIBS=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/build/sheets-r-library
export R_LIBS="$RCMS_R_LIBS" R_LIBS_USER="$RCMS_R_LIBS"
export RCMS_QT6_BUILD_ROOT=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/build/qt6-verification
export PYTHONPATH="$PWD/src:$PWD"
export PATH=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/.venv/bin:$PATH
python -m ty check --python-platform win32 \
  --extra-search-path "$RCMS_QT6_BUILD_ROOT/generated/rc_metastudio" \
  --extra-search-path "$RCMS_QT6_BUILD_ROOT/generated/rc_metastudio/forms" \
  --extra-search-path . --extra-search-path src/rc_metastudio \
  --extra-search-path src --extra-search-path scripts \
  --extra-search-path tests/python/gui src/rc_metastudio scripts tests r/RCMetaR/inst/qa
/usr/bin/time -p python scripts/verify.py pre-push
/usr/bin/time -p python scripts/verify.py fast
python -m pytest tests/python/gui -q
python -m pytest --strict-markers tests --collect-only -q
```

Host: Linux x86_64; strict typing target: win32. The typing gate passed before
GUI execution. `pre-push` fails argument parsing on this revision: only `smoke`,
`fast`, and `r-stack` exist. Its failure is retained, not reported as success.
The maintained `fast` lane passed before edits in 85.16 seconds.
Transcripts are retained in `test-cuts-evidence/`.

Python fast/gui collected cases: 741 before, 739 after (two duplicate cases
removed; parametrization preserves four merged cases). Fast Python source lines:
9,782 before, 9,730 after. GUI Python source lines including support: 16,063 both.
