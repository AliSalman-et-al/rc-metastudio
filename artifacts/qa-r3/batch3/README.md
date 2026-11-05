# Batch 3 proof

Base fetched before work: origin/master 6f85f47f. Linux source app, real Qt/R,
win32 strict typing target. No numerical references or tolerances changed.

Reproduce:
```bash
source /home/ali/.t3/qa-env/ENV.sh
export PYTHONPATH=$PWD/src:$PWD
mkdir -p build/rcmetar-lib
"$RCMS_R_HOME/bin/R" CMD INSTALL -l "$PWD/build/rcmetar-lib" r/RCMetaR
export RCMS_R_LIBS=$PWD/build/rcmetar-lib:$RCMS_R_LIBS
export R_LIBS=$RCMS_R_LIBS R_LIBS_USER=$RCMS_R_LIBS
python -c 'from scripts.verify import run_typing; import os; from pathlib import Path; run_typing(Path(os.environ["RCMS_QT6_BUILD_ROOT"]))'
python scripts/verify_rcms.py plot-edit
python scripts/verify_rcms.py project-axis-sequential
python scripts/verify_rcms.py analysis-amino-binary-meta-regression
python scripts/code_health.py --base origin/master --head HEAD
```

Native sessions batch3 (light/default) and batch3-dark (dark/+6pt) used ui.py
with RCMS_QA_APP_SRC=$PWD and RCMS_QA_R_LIB=$PWD/build/rcmetar-lib.
Both stopped. Open amino → Analysis/Meta-analysis → Run → raise clinical failure
→ Edit plot → BMJ → untick study labels and estimate → scroll to ticks → enter
bad text → Apply → inline error → replace with `0.1, 1, 10` → Apply → Cancel.
Screenshots native-invalid/dark-invalid and native-bmj-hidden/dark-bmj-hidden
retain outcomes. Settings screenshots retain the single references block.
Before evidence: /home/ali/.t3/qa-round3/H/shots/{20-settings-crop-2x,33-applied,35-applied}.png.
No fresh before dark capture was made. Added cumulative/prerequisite copy has
Qt/R scenario proof, not a separate manual native pass.

Exact numerical proof: plot-edit snapshots all numeric fields of plot.data$res
and uses R identical() after edits. Whole-object serialization was initially
attempted and failed because fit objects retain environment state; the failed
run is retained in the local verification tree. A later extra assertion initially
expected two decimals, but the scenario uses three; corrected to the actual
0.770 (0.485 to 1.222). Neither failure changed estimator code or references.

CI owns the remaining authority/golden/platform/package and full pre-push lanes.
This is not release qualification. No export-file matrix repeated locally.

Merged current origin/master 8d3609d2 (#568) before PR creation. Final tick-domain
assertions also exercise zero/negative logarithmic ticks after a prior Apply.
That exposed lost metric metadata in mark_commit_succeeded: replacing _params
with presentation-only fields dropped measure. Updating the existing dictionary
retains that metadata, so repeated Apply validates the same axis domain.
