# New sheet wizard proof

Source base: origin/master 95f8bef7. Linux native display, real Qt/R from `/home/ali/.t3/qa-env/ENV.sh`.

Real-app command: `RCMS_QA_APP_SRC=$PWD /home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session new-sheet-wizard start` (second run adds `--dark --large-font`). All sessions stopped. Review capture used session new-sheet-review.

Opened `/home/ali/.t3/qa-env/src/sample_projects/amino.rcms`, clicked the + beside the two existing binary outcome tabs. Data-type page opened immediately without a destructive prompt (light-wizard.png, dark-large-wizard.png). Selected Means, Next, default Mean difference, Next. Outcome 2 was prefilled. Finished with a name; continuous N/mean/SD columns appeared and both original tabs remained (light-grid.png, dark-large-grid.png). Review follow-up recaptured light/default: the title and final-page copy now say Add Outcome/Add outcome. Outcome 2 is focused and selected on entry; typing Continuous without clicking the field replaces it and creates exactly Continuous (light-grid.png). The earlier dark capture remains from the initial implementation.

Automated commands (source ENV.sh, export PYTHONPATH=$PWD/src:$PWD):
- Strict typing: `python -c 'from scripts.verify import run_typing; from pathlib import Path; import os; run_typing(Path(os.environ["RCMS_QT6_BUILD_ROOT"]))'`, win32 target, typing.log.
- `python scripts/verify_rcms.py sheets`, `sheets-edges`, `sheets-swap`, `project-structure`; logs here point to complete durable manifests, inputs, steps and screenshots under artifacts/verification/rcms. Initial swap failure retained: helper selected Means where diagnostic assertions required Diagnostic; recheck explicitly selects Diagnostic.
- `python scripts/verify.py pre-push`, pre-push.log.
- `python -c 'from scripts.verify import run_code_health; run_code_health("origin/master")'`, code-health.log (committed HEAD against fresh fetched master).

Statistics and numerical references unchanged. No golden presentation references require updates. Before-fix native screenshots, light-large and dark-default profiles were not captured; captures cover light/default and dark/large. Full statistical authority/platform matrix remains CI scope.

Review qualification: strict Ty (win32) passed; `python scripts/verify_rcms.py sheets` recheck evidence is `artifacts/verification/rcms/20261105T054138Z-af3430b0-sheets`. The helper asserts focus and full selection, enters names with key clicks, and asserts the exact tab name. Initial show-event focus assertion failed; deferring selection until Qt completes page focus setup fixes it. Failed evidence retained.
