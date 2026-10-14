# Round 4 — test attempts and unfinished qualification

Stopped at required push after `ca6815c`: `git push origin ux/audit-improvements` exited **143**, with empty stdout and stderr. Branch remains ahead one. No retry. [STOP](STOP.json) records this exact observation.

The 64 completed recorded attempts comprise 45 exit-zero and 19 nonzero exits. Exact argv, environment, revision, timestamps, raw-log SHA and verbatim failure lines are in [TEST-RUNS](TEST-RUNS.json). Raw logs are ignored under `raw/`. The final native invocation has no completed runner receipt or helper manifest; it is not counted as a passing run.

Established before the last BMJ fix: all original 415 fields matched exactly (max absolute difference 0) in `numerical-before-refresh`. Only three reviewed null-description texts were refreshed using the sanctioned presentation tool. The 157 retained UI checks passed in `retained-ui-final`. The passing targeted native commands are bound in [OBSERVATIONS](OBSERVATIONS.json), with public-package weights, raw-column geometry and decoded export observations. These do not substitute for final current-head qualification.

`full-final` exited 1: 23 retained R presentation assertions expected old Weight/axis/null strings or obsolete fixed coordinates. They were reviewed and updated in `58fa037`. `full-qualification` exited 130 after a deliberate SIGINT to own PID 761953: native inspection discovered BMJ pooled-label/totals and footer/tick collisions. That run reached package Status OK and both 21-case Reitsma visual lanes, but its full profile is incomplete. `ca6815c` repairs the two BMJ causes; current source needs native recapture, full fresh qualification, numerical equivalence and strict goldens.

## Exact recorded commands and exits

| Label | Exit | Exact argv |
| --- | ---: | --- |
| baseline-precision | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| baseline-presentation | 1 | `uv run python scripts/verify_rcms.py audit-round3-presentation --native` |
| before-design-amino | 0 | `uv run python scripts/verify_rcms.py amino --native` |
| bmj-observed-collision-checked | 1 | `uv run python -c 'import sys,json; from pathlib import Path; from types import SimpleNamespace; sys.path.insert(0,"tests/e2e"); from audit_round3 import check_annotation_spacing; r=json.loads(Path("docs/ux-audit/2026-10-15-round4/OBSERVATIONS.json").read_text()); d=next(x for x in r if x["family"]=="twoarm-proportion"); f=Path(d["evidence"]); s=[json.loads(x) for x in (f/"steps.jsonl").read_text().splitlines()]; o=next(x for x in s if x["action"]=="round4-annotations" and x["style"]=="bmj" and x["digits"]==6); check_annotation_spacing(SimpleNamespace(report_text=SimpleNamespace(toPlainText=lambda:"Overall-effect null:"),results=SimpleNamespace(display_images={k:str(f/v) for k,v in o["artifacts"].items()})))'` |
| bmj-observed-collision | 1 | `uv run python -c 'import sys,json; from pathlib import Path; from types import SimpleNamespace; sys.path.insert(0,"tests/e2e"); from audit_round3 import check_annotation_spacing; r=json.loads(Path("docs/ux-audit/2026-10-15-round4/OBSERVATIONS.json").read_text()); d=next(x for x in r if x["family"]=="twoarm-proportion"); f=Path(d["evidence"]); s=[json.loads(x) for x in (f/"steps.jsonl").read_text().splitlines()]; o=next(x for x in s if x["action"]=="round4-annotations" and x["style"]=="bmj" and x["digits"]==6); check_annotation_spacing(SimpleNamespace(report_text=SimpleNamespace(toPlainText=lambda:"Overall-effect null:"),results=SimpleNamespace(display_images={k:str(f/v) for k,v in o["artifacts"].items()})))'` |
| calculators-offscreen-1 | 1 | `uv run python -m pytest tests/e2e -n auto -k calculator --fresh -q` |
| calculators-offscreen-2 | 2 | `uv run python -m pytest tests/e2e -n auto -k calculator --fresh -q` |
| full-final | 1 | `uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh` |
| full-qualification | 130 | `uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh` |
| golden-before-refresh | 1 | `uv run python scripts/verify_golden_compatibility.py --output build/qt6-verification/golden-compatibility-round4-review` |
| golden-presentation-refresh | 0 | `uv run python scripts/regenerate_golden_presentation.py build/qt6-verification/golden-compatibility-round4-review` |
| install-bmj-clearance | 0 | `uv run python docs/ux-audit/2026-10-14-round3/install_source.py` |
| install-bubble-padding | 0 | `uv run python docs/ux-audit/2026-10-14-round3/install_source.py` |
| install-design | 0 | `uv run python docs/ux-audit/2026-10-14-round3/install_source.py` |
| install-final-renderers | 0 | `uv run python docs/ux-audit/2026-10-14-round3/install_source.py` |
| install-null | 0 | `uv run python docs/ux-audit/2026-10-14-round3/install_source.py` |
| install-publication-final | 0 | `uv run python docs/ux-audit/2026-10-14-round3/install_source.py` |
| install-rendering | 0 | `uv run python docs/ux-audit/2026-10-14-round3/install_source.py` |
| install-sequential-fix | 0 | `uv run python docs/ux-audit/2026-10-14-round3/install_source.py` |
| native-amino-ready | 0 | `uv run python scripts/verify_rcms.py amino --native` |
| native-audit-round3-hr-final | 0 | `uv run python scripts/verify_rcms.py audit-round3-hr --native` |
| native-audit-round3-irr-final | 0 | `uv run python scripts/verify_rcms.py audit-round3-irr --native` |
| native-audit-round3-presentation-reg-coef-ready | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-reg-coef --native` |
| native-calculator-binary-final | 0 | `uv run python scripts/verify_rcms.py calculator-binary --native` |
| native-calculator-continuous-final | 0 | `uv run python scripts/verify_rcms.py calculator-continuous --native` |
| native-calculator-mode-entered-binary-ready | 0 | `uv run python scripts/verify_rcms.py calculator-mode-entered-binary --native` |
| native-calculator-mode-entered-binary-verified | 0 | `uv run python scripts/verify_rcms.py calculator-mode-entered-binary --native` |
| native-calculator-mode-entered-continuous-ready | 0 | `uv run python scripts/verify_rcms.py calculator-mode-entered-continuous --native` |
| native-calculator-mode-entered-continuous-verified | 0 | `uv run python scripts/verify_rcms.py calculator-mode-entered-continuous --native` |
| native-calculator-mode-pre-post-complete | 1 | `uv run python scripts/verify_rcms.py calculator-mode-pre-post --native` |
| native-calculator-mode-pre-post-final | 1 | `uv run python scripts/verify_rcms.py calculator-mode-pre-post --native` |
| native-calculator-mode-pre-post-ready | 0 | `uv run python scripts/verify_rcms.py calculator-mode-pre-post --native` |
| native-calculator-mode-pre-post-verified | 0 | `uv run python scripts/verify_rcms.py calculator-mode-pre-post --native` |
| native-final-diagnostic | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-diagnostic --native` |
| native-final-generic-effect | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-generic-effect --native` |
| native-final-onearm-proportion | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-onearm-proportion --native` |
| native-final-reg-coef | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-reg-coef --native` |
| native-final-sequential | 1 | `uv run python scripts/verify_rcms.py audit-round3-presentation-sequential --native` |
| native-final-twoarm-mean | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-mean --native` |
| native-final-twoarm-proportion | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-proportion --native` |
| native-final-twoarm-smd | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-smd --native` |
| native-plot-workflow-regression-ready | 0 | `uv run python scripts/verify_rcms.py plot-workflow-regression --native` |
| native-precision-1 | 1 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| native-precision-final | 0 | `uv run python scripts/verify_rcms.py audit-round3-precision --native` |
| native-presentation-1 | 1 | `uv run python scripts/verify_rcms.py audit-round3-presentation --native` |
| native-presentation-2 | 1 | `uv run python scripts/verify_rcms.py audit-round3-presentation --native` |
| native-presentation-3 | 1 | `uv run python scripts/verify_rcms.py audit-round3-presentation --native` |
| native-project-table-covariates-ready | 0 | `uv run python scripts/verify_rcms.py project-table-covariates --native` |
| native-project-table-covariates-verified | 1 | `uv run python scripts/verify_rcms.py project-table-covariates --native` |
| native-publication-diagnostic | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-diagnostic --native` |
| native-publication-generic-effect | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-generic-effect --native` |
| native-publication-onearm-proportion | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-onearm-proportion --native` |
| native-publication-twoarm-mean | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-mean --native` |
| native-publication-twoarm-proportion | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-proportion --native` |
| native-publication-twoarm-smd | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-smd --native` |
| native-review-workflows-verified | 0 | `uv run python scripts/verify_rcms.py review-workflows --native` |
| native-sequential-final | 0 | `uv run python scripts/verify_rcms.py audit-round3-presentation-sequential --native` |
| native-small-study-diagnostic-ready | 0 | `uv run python scripts/verify_rcms.py small-study-diagnostic --native` |
| native-ux-improvements-verified | 0 | `uv run python scripts/verify_rcms.py ux-improvements --native` |
| numerical-before-refresh | 0 | `uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-round4-review` |
| r-presentation-current | 1 | `/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript -e 'testthat::test_local("r/RCMetaR", filter="forest\|bubble\|summary", reporter=testthat::SummaryReporter$new(max_reports=Inf), stop_on_failure=TRUE)'` |
| retained-ui-checks-final | 0 | `uv run python -m pytest tests/python/gui/test_funnel_plot_editor.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_automation_launch.py -q` |
| retained-ui-checks | 1 | `uv run python -m pytest tests/python/gui/test_funnel_plot_editor.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_automation_launch.py -q` |
| retained-ui-final | 0 | `uv run python -m pytest tests/python/gui/test_funnel_plot_editor.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_automation_launch.py -q` |

## Verbatim failures

Every retained nonzero attempt is below; paths and numerical arrays are preserved verbatim. The longer retained R diagnostic block is in [R-PRESENTATION-FAILURES](R-PRESENTATION-FAILURES.txt).

### baseline-precision (exit 1)

```text
AssertionError: ('analysis-data-generic-effect', 'meta-regression')
AssertionError: ('analysis-data-generic-effect', 'meta-regression')
```

### baseline-presentation (exit 1)

```text
AssertionError: ('weight/estimate gap', 3.824999999999932, {'x': '423.08', 'y': '173.31', 'text-anchor': 'middle', 'style': 'font-size: 11.76px; font-family: "Liberation Sans";', 'textLength': '33.31px', 'lengthAdjust': 'spacingAndGlyphs'}, {'x': '546.06', 'y': '171.90', 'text-anchor': 'end', 'style': 'font-size: 11.52px; font-family: "Liberation Sans";', 'textLength': '102.50px', 'lengthAdjust': 'spacingAndGlyphs'})
AssertionError: ('weight/estimate gap', 3.824999999999932, {'x': '423.08', 'y': '173.31', 'text-anchor': 'middle', 'style': 'font-size: 11.76px; font-family: "Liberation Sans";', 'textLength': '33.31px', 'lengthAdjust': 'spacingAndGlyphs'}, {'x': '546.06', 'y': '171.90', 'text-anchor': 'end', 'style': 'font-size: 11.52px; font-family: "Liberation Sans";', 'textLength': '102.50px', 'lengthAdjust': 'spacingAndGlyphs'})
```

### bmj-observed-collision-checked (exit 1)

```text
AssertionError: ('model/footer collision', '(DerSimonian–Laird)', '39 / 135', (46.8, 169.55, 262.43, 274.91), (158.765, 203.855, 259.03, 271.51))
```

### bmj-observed-collision (exit 1)

```text
IndentationError: unexpected indent
```

### calculators-offscreen-1 (exit 1)

```text
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-diagnostic]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-binary-metrics]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-continuous-metrics]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-diagnostic-metrics]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-onearm-proportion]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-onearm-mean]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-entered-binary]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-entered-continuous]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-entered-diagnostic]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-pre-post]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-back-binary]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-back-continuous]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-back-diagnostic]
```

### calculators-offscreen-2 (exit 2)

```text
E       AssertionError: Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261014T194327Z-ddf42c0f-calculator-diagnostic
E         RCMS calculator-diagnostic timed out after 120 seconds: /home/ali/Documents/Code/rc-metastudio/.venv/bin/python -X faulthandler /home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py calculator-diagnostic /home/ali/Documents/Code/rc-metastudio/build/verification/rcms/desktop-08aldv3o
E       AssertionError: Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261014T194537Z-bfe912ab-calculator-mode-binary-metrics
E         RCMS calculator-mode-binary-metrics timed out after 120 seconds: /home/ali/Documents/Code/rc-metastudio/.venv/bin/python -X faulthandler /home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py calculator-mode-binary-metrics /home/ali/Documents/Code/rc-metastudio/build/verification/rcms/desktop-uxf4lbpv
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-diagnostic]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-binary-metrics]
```

### full-final (exit 1)

```text
```

### full-qualification (exit 130)

```text
```

### golden-before-refresh (exit 1)

```text
```

### native-calculator-mode-pre-post-complete (exit 1)

```text
AssertionError: ('pre-post', PyQt6.QtCore.QSize(356, 388))
AssertionError: [AssertionError(('pre-post', PyQt6.QtCore.QSize(356, 388)))]
AssertionError: [AssertionError(('pre-post', PyQt6.QtCore.QSize(356, 388)))]
```

### native-calculator-mode-pre-post-final (exit 1)

```text
AssertionError: ('pre-post', PyQt6.QtCore.QSize(356, 388))
AssertionError: [AssertionError(('pre-post', PyQt6.QtCore.QSize(356, 388)))]
AssertionError: [AssertionError(('pre-post', PyQt6.QtCore.QSize(356, 388)))]
```

### native-final-sequential (exit 1)

```text
AssertionError: ('analysis.cumulative.cumulative forest_plot.1', 0, [234.51], [{'x1': '202.56', 'y1': '45.85', 'x2': '442.14', 'y2': '45.85', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '224.66', 'y1': '72.82', 'x2': '420.04', 'y2': '72.82', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '233.36', 'y1': '99.79', 'x2': '411.35', 'y2': '99.79', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '238.12', 'y1': '126.76', 'x2': '406.58', 'y2': '126.76', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '241.17', 'y1': '153.73', 'x2': '403.53', 'y2': '153.73', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '243.32', 'y1': '180.70', 'x2': '401.39', 'y2': '180.70', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '202.56', 'y1': '47.33', 'x2': '202.56', 'y2': '44.36', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '224.66', 'y1': '74.30', 'x2': '224.66', 'y2': '71.33', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '233.36', 'y1': '101.27', 'x2': '233.36', 'y2': '98.30', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '238.12', 'y1': '128.24', 'x2': '238.12', 'y2': '125.27', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '241.17', 'y1': '155.21', 'x2': '241.17', 'y2': '152.24', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '243.32', 'y1': '182.18', 'x2': '243.32', 'y2': '179.21', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '442.14', 'y1': '47.33', 'x2': '442.14', 'y2': '44.36', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '420.04', 'y1': '74.30', 'x2': '420.04', 'y2': '71.33', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '411.35', 'y1': '101.27', 'x2': '411.35', 'y2': '98.30', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '406.58', 'y1': '128.24', 'x2': '406.58', 'y2': '125.27', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '403.53', 'y1': '155.21', 'x2': '403.53', 'y2': '152.24', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '401.39', 'y1': '182.18', 'x2': '401.39', 'y2': '179.21', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '146.66', 'y1': '318.24', 'x2': '498.04', 'y2': '318.24', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '146.66', 'y1': '318.24', 'x2': '146.66', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '234.51', 'y1': '318.24', 'x2': '234.51', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '322.35', 'y1': '318.24', 'x2': '322.35', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '410.20', 'y1': '318.24', 'x2': '410.20', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '498.04', 'y1': '318.24', 'x2': '498.04', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '44.85', 'y1': '26.97', 'x2': '651.31', 'y2': '26.97', 'style': 'stroke-width: 0.60;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}])
AssertionError: ('analysis.cumulative.cumulative forest_plot.1', 0, [234.51], [{'x1': '202.56', 'y1': '45.85', 'x2': '442.14', 'y2': '45.85', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '224.66', 'y1': '72.82', 'x2': '420.04', 'y2': '72.82', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '233.36', 'y1': '99.79', 'x2': '411.35', 'y2': '99.79', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '238.12', 'y1': '126.76', 'x2': '406.58', 'y2': '126.76', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '241.17', 'y1': '153.73', 'x2': '403.53', 'y2': '153.73', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '243.32', 'y1': '180.70', 'x2': '401.39', 'y2': '180.70', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '202.56', 'y1': '47.33', 'x2': '202.56', 'y2': '44.36', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '224.66', 'y1': '74.30', 'x2': '224.66', 'y2': '71.33', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '233.36', 'y1': '101.27', 'x2': '233.36', 'y2': '98.30', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '238.12', 'y1': '128.24', 'x2': '238.12', 'y2': '125.27', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '241.17', 'y1': '155.21', 'x2': '241.17', 'y2': '152.24', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '243.32', 'y1': '182.18', 'x2': '243.32', 'y2': '179.21', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '442.14', 'y1': '47.33', 'x2': '442.14', 'y2': '44.36', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '420.04', 'y1': '74.30', 'x2': '420.04', 'y2': '71.33', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '411.35', 'y1': '101.27', 'x2': '411.35', 'y2': '98.30', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '406.58', 'y1': '128.24', 'x2': '406.58', 'y2': '125.27', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '403.53', 'y1': '155.21', 'x2': '403.53', 'y2': '152.24', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '401.39', 'y1': '182.18', 'x2': '401.39', 'y2': '179.21', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '146.66', 'y1': '318.24', 'x2': '498.04', 'y2': '318.24', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '146.66', 'y1': '318.24', 'x2': '146.66', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '234.51', 'y1': '318.24', 'x2': '234.51', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '322.35', 'y1': '318.24', 'x2': '322.35', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '410.20', 'y1': '318.24', 'x2': '410.20', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '498.04', 'y1': '318.24', 'x2': '498.04', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '44.85', 'y1': '26.97', 'x2': '651.31', 'y2': '26.97', 'style': 'stroke-width: 0.60;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}])
```

### native-precision-1 (exit 1)

```text
AssertionError: ('tick/title gap', 46.04, {'transform': 'translate(32.76,154.80) rotate(-90)', 'text-anchor': 'middle', 'style': 'font-size: 12.00px; font-family: "Liberation Sans";', 'textLength': '74.45px', 'lengthAdjust': 'spacingAndGlyphs'})
AssertionError: ('tick/title gap', 46.04, {'transform': 'translate(32.76,154.80) rotate(-90)', 'text-anchor': 'middle', 'style': 'font-size: 12.00px; font-family: "Liberation Sans";', 'textLength': '74.45px', 'lengthAdjust': 'spacingAndGlyphs'})
```

### native-presentation-1 (exit 1)

```text
AssertionError: ['Mean', 'SD', 'N', 'Mean', 'SD', 'N']
AssertionError: ['Mean', 'SD', 'N', 'Mean', 'SD', 'N']
```

### native-presentation-2 (exit 1)

```text
AssertionError: ['Total', 'Mean', 'SD', 'Total', 'Mean', 'SD', 'Weight']
AssertionError: ['Total', 'Mean', 'SD', 'Total', 'Mean', 'SD', 'Weight']
```

### native-presentation-3 (exit 1)

```text
RCMS audit-round3-presentation timed out after 600 seconds: /home/ali/Documents/Code/rc-metastudio/.venv/bin/python -X faulthandler /home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py audit-round3-presentation /home/ali/Documents/Code/rc-metastudio/build/verification/rcms/desktop-_ahj17ab
```

### native-project-table-covariates-verified (exit 1)

```text
```

### r-presentation-current (exit 1)

```text
Error:
```

### retained-ui-checks (exit 1)

```text
E           AssertionError: assert ['Numeric cov...ire numbers.'] == ['Covariate v... be numeric.']
E               AssertionError: assert 'publication readability' in 'Automatic: determined by the plotted data'
E           AssertionError: assert 'About and licenses…' == 'About/Legal'
E           RuntimeError: RC MetaStudio wizard pages require MainWizard ownership
FAILED tests/python/gui/test_main_window_automation_launch.py::test_change_covariate_type_model_returns_native_values_and_accepts_native_edits
FAILED tests/python/gui/test_main_window_automation_launch.py::test_plot_text_inputs_enforce_publication_readability_limit
FAILED tests/python/gui/test_main_window_automation_launch.py::test_about_legal_and_welcome_links_show_current_project_information
FAILED tests/python/gui/test_main_window_automation_launch.py::test_csv_required_format_table_expands_and_shows_all_rows
```

The final push returned no text; its tool result reported `exit_code: 143`. The concurrently running native shell also returned `exit_code: 143`; no manifest was sealed, although the action stream reached workflow-passed. This cannot be represented as a complete pass. No owned verification process remained when reporting.
