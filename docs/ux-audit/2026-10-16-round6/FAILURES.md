# Failed attempts (verbatim)

## axes-native-after

Command: `bash -c for scenario in project-axis-proportions project-axis-others; do uv run python scripts/verify_rcms.py "$scenario" --native || exit; done`

```text
["bash", "-c", "for scenario in project-axis-proportions project-axis-others; do uv run python scripts/verify_rcms.py \"$scenario\" --native || exit; done"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T114207Z-1bfc02df-project-axis-proportions
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
R callback write-console: Error in exp(x) : non-numeric argument to mathematical function
  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1832, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 74, in run
    view = matrix(app, window, scenario, record, keep_results=True,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 642, in run
    view = observe()
           ^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 175, in observe
    view = visible(results_window.ResultsWindow)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 171, in visible
    assert len(found) == 1, (kind, found)
           ^^^^^^^^^^^^^^^
AssertionError: (<class 'rc_metastudio.results_window.ResultsWindow'>, [])
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1832, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 74, in run
    view = matrix(app, window, scenario, record, keep_results=True,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 642, in run
    view = observe()
           ^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 175, in observe
    view = visible(results_window.ResultsWindow)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 171, in visible
    assert len(found) == 1, (kind, found)
           ^^^^^^^^^^^^^^^
AssertionError: (<class 'rc_metastudio.results_window.ResultsWindow'>, [])


```

## axes-native-before

Command: `bash -c for scenario in project-axis-proportions project-axis-others; do uv run python scripts/verify_rcms.py "$scenario" --native || exit; done`

```text
["bash", "-c", "for scenario in project-axis-proportions project-axis-others; do uv run python scripts/verify_rcms.py \"$scenario\" --native || exit; done"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T113424Z-9957cdcb-project-axis-proportions
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
R callback write-console: Error in (function (expr, envir = parent.frame(), enclos = if (is.list(envir) ||  : 
  object 'plot.data' not found
  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1832, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 66, in run
    fit = str(r_bridge.execute_r_string('paste(as.integer(serialize(plot.data$res, NULL)), collapse=",")')[0])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_call_serialization.py", line 63, in _serialized_r_call
    return function(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 173, in execute_r_string
    return _r_eval(r_str)
           ^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 143, in _r_eval
    return evaluator(expression)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.venv/lib/python3.11/site-packages/rpy2/robjects/__init__.py", line 552, in __call__
    res, visible = rinterface.evalr_expr_with_visible(   # type: ignore
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.venv/lib/python3.11/site-packages/rpy2/rinterface/__init__.py", line 204, in evalr_expr_with_visible
    raise embedded.RRuntimeError(_rinterface._geterrmessage())
rpy2.rinterface_lib.embedded.RRuntimeError: Error in (function (expr, envir = parent.frame(), enclos = if (is.list(envir) ||  : 
  object 'plot.data' not found

Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1832, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 66, in run
    fit = str(r_bridge.execute_r_string('paste(as.integer(serialize(plot.data$res, NULL)), collapse=",")')[0])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_call_serialization.py", line 63, in _serialized_r_call
    return function(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 173, in execute_r_string
    return _r_eval(r_str)
           ^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 143, in _r_eval
    return evaluator(expression)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.venv/lib/python3.11/site-packages/rpy2/robjects/__init__.py", line 552, in __call__
    res, visible = rinterface.evalr_expr_with_visible(   # type: ignore
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.venv/lib/python3.11/site-packages/rpy2/rinterface/__init__.py", line 204, in evalr_expr_with_visible
    raise embedded.RRuntimeError(_rinterface._geterrmessage())
rpy2.rinterface_lib.embedded.RRuntimeError: Error in (function (expr, envir = parent.frame(), enclos = if (is.list(envir) ||  : 
  object 'plot.data' not found



```

## axis-before-after-numeric-diagnosis

Command: `/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript docs/ux-audit/2026-10-16-round6/axis_numeric_equivalence.R /home/ali/Documents/Code/rc-metastudio`

```text
["/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript", "docs/ux-audit/2026-10-16-round6/axis_numeric_equivalence.R", "/home/ali/Documents/Code/rc-metastudio"]
MD:bmj : differing fields  time 
Error in FUN(X[[i]], ...) : 
  identical(a$numeric, b$numeric, num.eq = FALSE) is not TRUE
Calls: lapply -> FUN -> stopifnot
Execution halted

```

## axis-before-after-numerics

Command: `/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript docs/ux-audit/2026-10-16-round6/axis_numeric_equivalence.R /home/ali/Documents/Code/rc-metastudio`

```text
["/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript", "docs/ux-audit/2026-10-16-round6/axis_numeric_equivalence.R", "/home/ali/Documents/Code/rc-metastudio"]
Error in FUN(X[[i]], ...) : 
  identical(a$numeric, b$numeric, num.eq = FALSE) is not TRUE
Calls: lapply -> FUN -> stopifnot
Execution halted

```

## axis-exact-value-replay

Command: `uv run python scripts/verify_rcms.py project-axis-proportions`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-axis-proportions"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T114542Z-442b6b33-project-axis-proportions
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1832, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 142, in run
    check_endpoints(path, observed, geometry, other == 'natural', ratio)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 70, in check_endpoints
    assert matched == len(expected['lower']), ('interval endpoint projection', path, matched, expected, lines)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ('interval endpoint projection', PosixPath('/home/ali/Documents/Code/rc-metastudio/build/verification/rcms/desktop-ov0eksa7/analysis/forest-bbdee9bd994f.display.svg'), 0, {'lower': [-2.481947536840617, -2.1673335324374774, -1.9190905775241123, -1.714862680124642, -1.541836481117074, -1.392015805128584], 'upper': [-0.2906411853991637, -0.15896808717388433, -0.042567928499340546, 0.06150553375570633, 0.15554211999718315, 0.24128751532146053], 'pooled': [-0.8846784667245323, -1.25954799667614, -0.5098089367729246]}, [(807.98, 809.75), (806.91, 809.75), (805.67, 809.75), (804.21, 809.75), (802.43, 809.75), (800.17, 809.75), (567.21, 782.13), (0.0, 1000.3)])
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1832, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 142, in run
    check_endpoints(path, observed, geometry, other == 'natural', ratio)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 70, in check_endpoints
    assert matched == len(expected['lower']), ('interval endpoint projection', path, matched, expected, lines)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ('interval endpoint projection', PosixPath('/home/ali/Documents/Code/rc-metastudio/build/verification/rcms/desktop-ov0eksa7/analysis/forest-bbdee9bd994f.display.svg'), 0, {'lower': [-2.481947536840617, -2.1673335324374774, -1.9190905775241123, -1.714862680124642, -1.541836481117074, -1.392015805128584], 'upper': [-0.2906411853991637, -0.15896808717388433, -0.042567928499340546, 0.06150553375570633, 0.15554211999718315, 0.24128751532146053], 'pooled': [-0.8846784667245323, -1.25954799667614, -0.5098089367729246]}, [(807.98, 809.75), (806.91, 809.75), (805.67, 809.75), (804.21, 809.75), (802.43, 809.75), (800.17, 809.75), (567.21, 782.13), (0.0, 1000.3)])


```

## axis-first-replay

Command: `uv run python scripts/verify_rcms.py project-axis-proportions`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-axis-proportions"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T114335Z-1c872de6-project-axis-proportions
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1832, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 113, in run
    assert str(r_bridge.execute_r_string('paste(as.integer(serialize(plot.data$res, NULL)), collapse=",")')[0]) == fit
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1832, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 113, in run
    assert str(r_bridge.execute_r_string('paste(as.integer(serialize(plot.data$res, NULL)), collapse=",")')[0]) == fit
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError


```

## axis-numeric-fields-replay

Command: `uv run python scripts/verify_rcms.py project-axis-proportions`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-axis-proportions"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T114432Z-9510a28e-project-axis-proportions
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1832, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 113, in run
    assert str(r_bridge.execute_r_string('paste(as.integer(serialize(c(plot.data$res[vapply(plot.data$res, is.numeric, logical(1))], list(weights=as.numeric(weights(plot.data$res)))), NULL)), collapse=",")')[0]) == fit
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1832, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 113, in run
    assert str(r_bridge.execute_r_string('paste(as.integer(serialize(c(plot.data$res[vapply(plot.data$res, is.numeric, logical(1))], list(weights=as.numeric(weights(plot.data$res)))), NULL)), collapse=",")')[0]) == fit
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError


```

## axis-pft-subset-baseline

Command: `uv run python scripts/verify_rcms.py project-axis-sequential`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-axis-sequential"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T115317Z-2a9292af-project-axis-sequential
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
R callback write-console: Error: Must specify the sample sizes via the 'targs' argument.
  
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 775, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1833, in run
    run_sequential(app, window, Path(sys.argv[2]), record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 172, in run_sequential
    view = matrix(app, window, 'analysis-data-onearm-proportion', record, keep_results=True,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 642, in run
    view = observe()
           ^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 175, in observe
    view = visible(results_window.ResultsWindow)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 171, in visible
    assert len(found) == 1, (kind, found)
           ^^^^^^^^^^^^^^^
AssertionError: (<class 'rc_metastudio.results_window.ResultsWindow'>, [])
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 775, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1833, in run
    run_sequential(app, window, Path(sys.argv[2]), record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 172, in run_sequential
    view = matrix(app, window, 'analysis-data-onearm-proportion', record, keep_results=True,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 642, in run
    view = observe()
           ^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 175, in observe
    view = visible(results_window.ResultsWindow)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 171, in visible
    assert len(found) == 1, (kind, found)
           ^^^^^^^^^^^^^^^
AssertionError: (<class 'rc_metastudio.results_window.ResultsWindow'>, [])


```

## axis-renderer-replay

Command: `/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript -e testthat::test_local("r/RCMetaR", filter="forest-metafor-renderer|bubble-metafor-renderer|summary-display|forest-subgroup-range", stop_on_failure=TRUE)`

```text
["/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript", "-e", "testthat::test_local(\"r/RCMetaR\", filter=\"forest-metafor-renderer|bubble-metafor-renderer|summary-display|forest-subgroup-range\", stop_on_failure=TRUE)"]
✔ | F W  S  OK | Context

⠏ |          0 | bubble-metafor-renderer                                        
⠋ |          1 | bubble-metafor-renderer                                        
⠙ |          2 | bubble-metafor-renderer                                        
⠸ |          4 | bubble-metafor-renderer                                        
⠏ |         10 | bubble-metafor-renderer                                        
⠴ |         16 | bubble-metafor-renderer                                        
✔ |         27 | bubble-metafor-renderer [3.2s]

⠏ |          0 | forest-metafor-renderer                                        
⠋ |          1 | forest-metafor-renderer                                        
⠋ |         11 | forest-metafor-renderer                                        
⠹ |         33 | forest-metafor-renderer                                        
⠙ |         42 | forest-metafor-renderer                                        
⠧ |         48 | forest-metafor-renderer                                        
⠙ |         52 | forest-metafor-renderer                                        
⠦ |         67 | forest-metafor-renderer                                        
⠴ |         76 | forest-metafor-renderer                                        
⠙ |         82 | forest-metafor-renderer                                        
⠇ |         89 | forest-metafor-renderer                                        
⠸ |        104 | forest-metafor-renderer                                        
⠴ |        116 | forest-metafor-renderer                                        
⠙ |        122 | forest-metafor-renderer                                        
⠦ |        137 | forest-metafor-renderer                                        
⠴ |        146 | forest-metafor-renderer                                        
⠇ |        149 | forest-metafor-renderer                                        
⠸ |        154 | forest-metafor-renderer                                        
⠙ |        172 | forest-metafor-renderer                                        
⠧ |        178 | forest-metafor-renderer                                        
⠙ |        192 | forest-metafor-renderer                                        
⠧ |        198 | forest-metafor-renderer                                        
⠼ |        205 | forest-metafor-renderer                                        
⠦ |        207 | forest-metafor-renderer                                        
⠼ |        215 | forest-metafor-renderer                                        
⠹ |        223 | forest-metafor-renderer                                        
⠼ |        235 | forest-metafor-renderer                                        
⠧ |        248 | forest-metafor-renderer                                        
⠏ |        260 | forest-metafor-renderer                                        
⠋ |        271 | forest-metafor-renderer                                        
⠇ |        289 | forest-metafor-renderer                                        
⠙ |        292 | forest-metafor-renderer                                        
⠦ |        297 | forest-metafor-renderer                                        
⠙ |        302 | forest-metafor-renderer                                        
⠦ |        307 | forest-metafor-renderer                                        
⠼ |        315 | forest-metafor-renderer                                        
⠹ |        323 | forest-metafor-renderer                                        
⠋ |        331 | forest-metafor-renderer                                        
⠧ |        338 | forest-metafor-renderer                                        
⠼ |        345 | forest-metafor-renderer                                        
⠙ |        352 | forest-metafor-renderer                                        
⠇ |        359 | forest-metafor-renderer                                        
⠴ |        366 | forest-metafor-renderer                                        
⠹ |        373 | forest-metafor-renderer                                        
⠹ |        383 | forest-metafor-renderer                                        
⠴ |        386 | forest-metafor-renderer                                        
⠴ |        396 | forest-metafor-renderer                                        
⠏ |        400 | forest-metafor-renderer                                        
⠦ |        407 | forest-metafor-renderer                                        
⠹ |        413 | forest-metafor-renderer                                        
⠏ |        420 | forest-metafor-renderer                                        
⠇ |        429 | forest-metafor-renderer                                        
⠧ |        438 | forest-metafor-renderer                                        
⠏ |        440 | forest-metafor-renderer                                        
⠋ |        451 | forest-metafor-renderer                                        
⠙ |        462 | forest-metafor-renderer                                        
⠹ |        473 | forest-metafor-renderer                                        
⠹ |        483 | forest-metafor-renderer                                        
⠙ |        492 | forest-metafor-renderer                                        
⠏ |        500 | forest-metafor-renderer                                        
⠇ |        509 | forest-metafor-renderer                                        
⠴ |        516 | forest-metafor-renderer                                        
⠹ |        523 | forest-metafor-renderer                                        
⠴ |        526 | forest-metafor-renderer                                        
⠙ |        532 | forest-metafor-renderer                                        
⠏ |        540 | forest-metafor-renderer                                        
⠴ |        556 | forest-metafor-renderer                                        
⠴ |        566 | forest-metafor-renderer                                        
⠙ |        572 | forest-metafor-renderer                                        
⠸ |        584 | forest-metafor-renderer                                        
⠴ |        586 | forest-metafor-renderer                                        
⠙ |        592 | forest-metafor-renderer                                        
⠸ | 1      593 | forest-metafor-renderer                                        
⠴ | 2      594 | forest-metafor-renderer                                        
⠹ | 3      600 | forest-metafor-renderer                                        
⠼ | 4      601 | forest-metafor-renderer                                        
⠏ | 5      605 | forest-metafor-renderer                                        
⠙ | 6      606 | forest-metafor-renderer                                        
⠦ | 6      621 | forest-metafor-renderer                                        
⠙ | 6      626 | forest-metafor-renderer                                        
⠦ | 6      631 | forest-metafor-renderer                                        
⠙ | 6      636 | forest-metafor-renderer                                        
⠦ | 6      641 | forest-metafor-renderer                                        
⠙ | 6      646 | forest-metafor-renderer                                        
⠦ | 6      651 | forest-metafor-renderer                                        
⠙ | 6      656 | forest-metafor-renderer                                        
⠦ | 6      661 | forest-metafor-renderer                                        
⠙ | 6      666 | forest-metafor-renderer                                        
⠇ | 6      673 | forest-metafor-renderer                                        
⠼ | 6      679 | forest-metafor-renderer                                        
⠋ | 6      685 | forest-metafor-renderer                                        
⠦ | 6      691 | forest-metafor-renderer                                        
⠹ | 6      697 | forest-metafor-renderer                                        
⠇ | 6      703 | forest-metafor-renderer                                        
⠼ | 6      709 | forest-metafor-renderer                                        
⠋ | 6      715 | forest-metafor-renderer                                        
⠦ | 6      721 | forest-metafor-renderer                                        
⠹ | 6      727 | forest-metafor-renderer                                        
⠇ | 6      743 | forest-metafor-renderer                                        
⠏ | 6      754 | forest-metafor-renderer                                        
✖ | 6      764 | forest-metafor-renderer [240.8s]
────────────────────────────────────────────────────────────────────────────────
Failure ('test-forest-metafor-renderer.R:1777:5'): workflow forest artifacts regenerate through their saved public contract
Expected `identical(params$fp_plot_lb, "[default]")` to be FALSE.
Differences:
`actual`:   TRUE 
`expected`: FALSE


Failure ('test-forest-metafor-renderer.R:1778:5'): workflow forest artifacts regenerate through their saved public contract
Expected `identical(params$fp_plot_ub, "[default]")` to be FALSE.
Differences:
`actual`:   TRUE 
`expected`: FALSE


Failure ('test-forest-metafor-renderer.R:1777:5'): workflow forest artifacts regenerate through their saved public contract
Expected `identical(params$fp_plot_lb, "[default]")` to be FALSE.
Differences:
`actual`:   TRUE 
`expected`: FALSE


Failure ('test-forest-metafor-renderer.R:1778:5'): workflow forest artifacts regenerate through their saved public contract
Expected `identical(params$fp_plot_ub, "[default]")` to be FALSE.
Differences:
`actual`:   TRUE 
`expected`: FALSE


Failure ('test-forest-metafor-renderer.R:1777:5'): workflow forest artifacts regenerate through their saved public contract
Expected `identical(params$fp_plot_lb, "[default]")` to be FALSE.
Differences:
`actual`:   TRUE 
`expected`: FALSE


Failure ('test-forest-metafor-renderer.R:1778:5'): workflow forest artifacts regenerate through their saved public contract
Expected `identical(params$fp_plot_ub, "[default]")` to be FALSE.
Differences:
`actual`:   TRUE 
`expected`: FALSE

────────────────────────────────────────────────────────────────────────────────

⠏ |          0 | forest-subgroup-range                                          
✔ |          4 | forest-subgroup-range

⠏ |          0 | summary-display                                                
⠧ |          8 | summary-display                                                
⠏ |         20 | summary-display                                                
⠸ |         44 | summary-display                                                
⠙ |         62 | summary-display                                                
⠦ |         67 | summary-display                                                
⠙ |         72 | summary-display                                                
⠧ |         78 | summary-display                                                
⠧ |         88 | summary-display                                                
⠙ |         92 | summary-display                                                
⠴ |         96 | summary-display                                                
✔ |        105 | summary-display [1.3s]

══ Results ═════════════════════════════════════════════════════════════════════
Duration: 245.5 s

── Failed tests ────────────────────────────────────────────────────────────────
Failure ('test-forest-metafor-renderer.R:1777:5'): workflow forest artifacts regenerate through their saved public contract
Expected `identical(params$fp_plot_lb, "[default]")` to be FALSE.
Differences:
`actual`:   TRUE 
`expected`: FALSE


Failure ('test-forest-metafor-renderer.R:1778:5'): workflow forest artifacts regenerate through their saved public contract
Expected `identical(params$fp_plot_ub, "[default]")` to be FALSE.
Differences:
`actual`:   TRUE 
`expected`: FALSE


Failure ('test-forest-metafor-renderer.R:1777:5'): workflow forest artifacts regenerate through their saved public contract
Expected `identical(params$fp_plot_lb, "[default]")` to be FALSE.
Differences:
`actual`:   TRUE 
`expected`: FALSE


Failure ('test-forest-metafor-renderer.R:1778:5'): workflow forest artifacts regenerate through their saved public contract
Expected `identical(params$fp_plot_ub, "[default]")` to be FALSE.
Differences:
`actual`:   TRUE 
`expected`: FALSE


Failure ('test-forest-metafor-renderer.R:1777:5'): workflow forest artifacts regenerate through their saved public contract
Expected `identical(params$fp_plot_lb, "[default]")` to be FALSE.
Differences:
`actual`:   TRUE 
`expected`: FALSE


Failure ('test-forest-metafor-renderer.R:1778:5'): workflow forest artifacts regenerate through their saved public contract
Expected `identical(params$fp_plot_ub, "[default]")` to be FALSE.
Differences:
`actual`:   TRUE 
`expected`: FALSE


[ FAIL 6 | WARN 0 | SKIP 0 | PASS 900 ]
Error:
! Test failures.
Execution halted

```

## axis-renderer-tests

Command: `/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript -e testthat::test_local("r/RCMetaR", filter="forest-metafor-renderer|bubble-metafor-renderer|summary-display|forest-subgroup-range", stop_on_failure=TRUE)`

```text
["/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript", "-e", "testthat::test_local(\"r/RCMetaR\", filter=\"forest-metafor-renderer|bubble-metafor-renderer|summary-display|forest-subgroup-range\", stop_on_failure=TRUE)"]
✔ | F W  S  OK | Context

⠏ |          0 | bubble-metafor-renderer                                        
⠋ |          1 | bubble-metafor-renderer                                        
⠙ |          2 | bubble-metafor-renderer                                        
⠸ |          4 | bubble-metafor-renderer                                        
⠏ |         10 | bubble-metafor-renderer                                        
⠴ |         16 | bubble-metafor-renderer                                        
✔ |         27 | bubble-metafor-renderer [3.1s]

⠏ |          0 | forest-metafor-renderer                                        
⠋ |          1 | forest-metafor-renderer                                        
⠋ |         11 | forest-metafor-renderer                                        
⠹ |         33 | forest-metafor-renderer                                        
⠙ |         42 | forest-metafor-renderer                                        
⠧ |         48 | forest-metafor-renderer                                        
⠙ |         52 | forest-metafor-renderer                                        
⠦ |         67 | forest-metafor-renderer                                        
⠴ |         76 | forest-metafor-renderer                                        
⠙ |         82 | forest-metafor-renderer                                        
⠇ |         89 | forest-metafor-renderer                                        
⠙ |        112 | forest-metafor-renderer                                        
⠏ |        120 | forest-metafor-renderer                                        
⠇ |        129 | forest-metafor-renderer                                        
⠴ |        146 | forest-metafor-renderer                                        
⠋ |        151 | forest-metafor-renderer                                        
⠋ |        161 | forest-metafor-renderer                                        
⠼ |        175 | forest-metafor-renderer                                        
⠧ |        188 | forest-metafor-renderer                                        
⠦ |        197 | forest-metafor-renderer                                        
⠼ |        205 | forest-metafor-renderer                                        
⠦ |        207 | forest-metafor-renderer                                        
⠼ |        215 | forest-metafor-renderer                                        
⠧ | 1      227 | forest-metafor-renderer                                        
⠼ | 1      234 | forest-metafor-renderer                                        
⠧ | 1      247 | forest-metafor-renderer                                        
⠏ | 1      259 | forest-metafor-renderer                                        
⠹ | 1      272 | forest-metafor-renderer                                        
⠋ | 1      290 | forest-metafor-renderer                                        
⠙ | 1      291 | forest-metafor-renderer                                        
⠦ | 1      296 | forest-metafor-renderer                                        
⠙ | 1      301 | forest-metafor-renderer                                        
⠸ | 2      312 | forest-metafor-renderer                                        
⠙ | 2      320 | forest-metafor-renderer                                        
⠏ | 2      328 | forest-metafor-renderer                                        
⠦ | 2      335 | forest-metafor-renderer                                        
⠸ | 2      342 | forest-metafor-renderer                                        
⠋ | 2      349 | forest-metafor-renderer                                        
⠧ | 2      356 | forest-metafor-renderer                                        
⠼ | 2      363 | forest-metafor-renderer                                        
⠙ | 2      370 | forest-metafor-renderer                                        
⠙ | 2      380 | forest-metafor-renderer                                        
⠼ | 2      383 | forest-metafor-renderer                                        
⠼ | 2      393 | forest-metafor-renderer                                        
⠇ | 2      397 | forest-metafor-renderer                                        
⠴ | 2      404 | forest-metafor-renderer                                        
⠸ | 2      412 | forest-metafor-renderer                                        
⠧ | 3      425 | forest-metafor-renderer                                        
⠦ | 3      434 | forest-metafor-renderer                                        
⠴ | 3      443 | forest-metafor-renderer                                        
⠸ | 3      451 | forest-metafor-renderer                                        
⠹ | 3      460 | forest-metafor-renderer                                        
⠏ | 3      467 | forest-metafor-renderer                                        
⠦ | 3      474 | forest-metafor-renderer                                        
⠦ | 5      482 | forest-metafor-renderer                                        
⠙ | 6      486 | forest-metafor-renderer                                        
⠧ | 6      492 | forest-metafor-renderer                                        
⠏ | 6      504 | forest-metafor-renderer                                        
⠙ | 6      506 | forest-metafor-renderer                                        
⠧ | 6      512 | forest-metafor-renderer                                        
⠇ | 6      523 | forest-metafor-renderer                                        
⠴ | 6      530 | forest-metafor-renderer                                        
⠸ | 6      538 | forest-metafor-renderer                                        
⠹ | 6      547 | forest-metafor-renderer                                        
⠧ | 6      552 | forest-metafor-renderer                                        
⠹ | 6      557 | forest-metafor-renderer                                        
⠧ | 6      562 | forest-metafor-renderer                                        
⠹ | 6      567 | forest-metafor-renderer                                        
⠧ | 6      572 | forest-metafor-renderer                                        
⠹ | 6      577 | forest-metafor-renderer                                        
⠧ | 6      582 | forest-metafor-renderer                                        
⠹ | 6      587 | forest-metafor-renderer                                        
⠧ | 6      592 | forest-metafor-renderer                                        
⠼ | 6      599 | forest-metafor-renderer                                        
⠋ | 6      605 | forest-metafor-renderer                                        
⠦ | 6      611 | forest-metafor-renderer                                        
⠹ | 6      617 | forest-metafor-renderer                                        
⠇ | 6      623 | forest-metafor-renderer                                        
⠼ | 6      629 | forest-metafor-renderer                                        
⠋ | 6      635 | forest-metafor-renderer                                        
⠦ | 6      641 | forest-metafor-renderer                                        
⠹ | 6      647 | forest-metafor-renderer                                        
⠇ | 6      653 | forest-metafor-renderer                                        
⠼ | 6      669 | forest-metafor-renderer                                        
⠴ | 6      680 | forest-metafor-renderer                                        
✖ | 6      690 | forest-metafor-renderer [170.2s]
────────────────────────────────────────────────────────────────────────────────
Failure ('test-forest-metafor-renderer.R:889:5'): BMJ Forest Style builds faithful family columns and renders smoke cases
Expected `bundle$style_blocks$axis_label` to equal `case$axis_label`.
Differences:
`actual`:   "Odds ratio"
`expected`: "Odds Ratio"


Error ('test-forest-metafor-renderer.R:1055:5'): entered-effect-only standard plots render without raw arm columns
Error in `exp(x)`: non-numeric argument to mathematical function
Backtrace:
     ▆
  1. └─RCMetaR::rcmetar.draw.forest.plot(bundle, png_path) at test-forest-metafor-renderer.R:1055:5
  2.   └─RCMetaR:::rcmetar.draw.metafor.forest(plot.data, outpath) at RCMetaR/R/rcmetar-core.R:518:9
  3.     └─RCMetaR (local) renderer(bundle, outpath) at RCMetaR/R/forest_metafor.R:905:9
  4.       └─RCMetaR:::rcmetar.render.plot_file(...) at RCMetaR/R/forest_style_default.R:233:5
  5.         └─RCMetaR:::rcmetar.render.plot_svg(svg.path, size, draw) at RCMetaR/R/plot_devices.R:289:5
  6.           └─RCMetaR (local) draw() at RCMetaR/R/plot_devices.R:198:5
  7.             └─RCMetaR:::rcmetar.forest.axis.effect(bundle, bundle$effect) at RCMetaR/R/forest_style_default.R:284:9
  8.               └─RCMetaR:::rcmetar.forest.axis.values(bundle, effect[[field]]) at RCMetaR/R/forest_axis.R:23:9
  9.                 └─rcmetar.bundle.transform(bundle)$display.scale(values, ni = bundle$sample_sizes) at RCMetaR/R/forest_axis.R:18:5
 10.                   └─RCMetaR:::invlogit(x) at RCMetaR/R/diagnostic_methods.R:113:13

Error ('test-forest-metafor-renderer.R:1402:5'): single-arm binary metrics build and render Default metafor bundles
Error in `(function (x, vi, sei, ci.lb, ci.ub, annotate = TRUE, showweights = FALSE, header = TRUE, xlim, alim, olim, ylim, at, steps = 5, level = 95, refline = 0, digits = 2L, width, xlab, slab, ilab, ilab.lab, ilab.xpos, ilab.pos, order, subset, transf, atransf, targs, rows, efac = 1, pch, psize, plim = c(0.5, 1.5), col, shade, colshade, lty, fonts, cex, cex.lab, cex.axis, ...)  {     mstyle <- .get.mstyle()     na.act <- getOption("na.action")     if (!is.element(na.act, c("na.omit", "na.exclude", "na.fail", "na.pass")))          stop(mstyle$stop("Unknown 'na.action' specified under options()."))     if (missing(transf))          transf <- FALSE     if (missing(atransf))          atransf <- FALSE     transf.char <- deparse(transf)     atransf.char <- deparse(atransf)     if (is.function(transf) && is.function(atransf))          stop(mstyle$stop("Use either 'transf' or 'atransf' to specify a transformation (not both)."))     .start.plot()     yi <- x     if (missing(targs))          targs <- NULL     if (missing(at))          at <- NULL     if (missing(ilab))          ilab <- NULL     if (missing(ilab.lab))          ilab.lab <- NULL     if (missing(ilab.xpos))          ilab.xpos <- NULL     if (missing(ilab.pos))          ilab.pos <- NULL     if (missing(subset))          subset <- NULL     if (missing(order))          order <- NULL     if (missing(pch))          pch <- 15     if (missing(psize))          psize <- NULL     if (missing(col))          col <- NULL     if (missing(shade))          shade <- NULL     if (missing(colshade))          colshade <- .coladj(par("bg", "fg"), dark = 0.1, light = -0.1)     if (missing(cex))          cex <- NULL     if (missing(cex.lab))          cex.lab <- NULL     if (missing(cex.axis))          cex.axis <- NULL     level <- .level(level)     if (length(digits) == 1L)          digits <- c(digits, digits, digits)     if (length(digits) == 2L)          digits <- c(digits, digits[[1]])     ddd <- list(...)     if (missing(lty)) {         lty <- c("solid", "solid")     }     else {         if (length(lty) == 1L)              lty <- c(lty, "solid")     }     efac <- .expand1(efac, 4L)     if (length(efac) == 2L)          efac <- c(efac, 1, 1)     if (length(efac) == 3L)          efac <- efac[c(1:3, 3)]     efac[efac == 0] <- NA     if (is.null(ddd$annosym)) {         annosym <- c(" [", ", ", "]", "-", " ")     }     else {         annosym <- ddd$annosym         if (length(annosym) == 3L)              annosym <- c(annosym, "-", " ")         if (length(annosym) == 4L)              annosym <- c(annosym, " ")         if (length(annosym) != 5L)              stop(mstyle$stop("Argument 'annosym' must be a vector of length 3 (or 4 or 5)."))     }     if (isTRUE(ddd$tabfig == 1))          annosym <- c(" [", ", ", "]", "−", " ")     if (isTRUE(ddd$tabfig == 2))          annosym <- c(" [", ", ", "]", "–", " ")     if (isTRUE(ddd$tabfig == 3))          annosym <- c(" [", ", ", "]", "−", " ")     if (is.null(attr(yi, "measure"))) {         measure <- "GEN"     }     else {         measure <- attr(yi, "measure")     }     estlab <- .setlab(measure, transf.char, atransf.char, gentype = 3, short = TRUE)     if (is.expression(estlab)) {         header.right <- str2lang(paste0("bold(", estlab, " * '", annosym[1], "' * '", round(100 * (1 - level), digits[[1]]), "% CI'", " * '", annosym[3], "')"))     }     else {         header.right <- paste0(estlab, annosym[1], round(100 * (1 - level), digits[[1]]), "% CI", annosym[3])     }     if (is.logical(header)) {         if (header) {             header.left <- "Study"         }         else {             header.left <- NULL             header.right <- NULL         }     }     else {         if (!is.character(header))              stop(mstyle$stop("Argument 'header' must either be a logical or character vector."))         if (length(header) == 1L) {             header.left <- header         }         else {             header.left <- header[1]             header.right <- header[2]         }     }     if (!annotate)          header.right <- NULL     decreasing <- .chkddd(ddd$decreasing, FALSE)     if (is.null(ddd$clim)) {         if (missing(olim))              olim <- NULL     }     else {         olim <- ddd$clim     }     if (!is.null(olim)) {         if (length(olim) != 2L)              stop(mstyle$stop("Argument 'olim' must be of length 2."))         if (anyNA(olim))              stop(mstyle$stop("Argument 'olim' cannot contain NAs."))         olim <- sort(olim)     }     if (is.null(ddd$rowadj)) {         rowadj <- rep(0, 3)     }     else {         rowadj <- ddd$rowadj         if (length(rowadj) == 1L)              rowadj <- c(rowadj, rowadj, 0)         if (length(rowadj) == 2L)              rowadj <- c(rowadj, 0)     }     top <- .chkddd(ddd$top, 3)     if (is.null(ddd$xlabadj)) {         xlabadj <- c(NA, NA)     }     else {         xlabadj <- ddd$xlabadj         if (length(xlabadj) == 1L)              xlabadj <- c(xlabadj, 1 - xlabadj)     }     xlabfont <- .chkddd(ddd$xlabfont, 1)     if (!is.null(ddd$mlab))          warning("The forest.default() function does not have an 'mlab' argument.", call. = FALSE, immediate. = TRUE)     if (!is.null(ddd$addfit))          warning("The forest.default() function does not have an 'addfit' argument.", call. = FALSE, immediate. = TRUE)     if (!is.null(ddd$addpred))          warning("The forest.default() function does not have an 'addpred' argument.", call. = FALSE, immediate. = TRUE)     if (!is.null(ddd$predstyle))          warning("The forest.default() function does not have a 'predstyle' argument.", call. = FALSE, immediate. = TRUE)     if (!is.null(ddd$predlim))          warning("The forest.default() function does not have a 'predlim' argument.", call. = FALSE, immediate. = TRUE)     if (!is.null(ddd$colout))          warning("The forest.default() function does not have a 'colout' argument.", call. = FALSE, immediate. = TRUE)     if (!is.null(ddd$border))          warning("The forest.default() function does not have a 'border' argument.", call. = FALSE, immediate. = TRUE)     lplot <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) plot(...)     labline <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) abline(...)     lsegments <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) segments(...)     laxis <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) axis(...)     lmtext <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) mtext(...)     lpolygon <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) polygon(...)     ltext <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) text(...)     lpoints <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) points(...)     if (!missing(vi) && is.function(vi))          stop(mstyle$stop("Cannot find variable specified for the 'vi' argument."))     if (hasArg(ci.lb) && hasArg(ci.ub) && !is.null(ci.lb) && !is.null(ci.ub)) {         if (length(ci.lb) != length(ci.ub))              stop(mstyle$stop("Length of 'ci.lb' and 'ci.ub' are not the same."))         if (missing(vi) && missing(sei)) {             vi <- ((ci.ub - ci.lb)/(2 * qnorm(level/2, lower.tail = FALSE)))^2         }         else {             if (missing(vi))                  vi <- sei^2         }         if (length(ci.lb) != length(vi))              stop(mstyle$stop("Length of 'vi' (or 'sei') does not match the length of ('ci.lb','ci.ub')."))     }     else {         if (missing(vi)) {             if (missing(sei)) {                 stop(mstyle$stop("Must specify either 'vi', 'sei', or ('ci.lb','ci.ub')."))             }             else {                 vi <- sei^2             }         }         if (length(yi) != length(vi))              stop(mstyle$stop("Length of 'vi' (or 'sei') does not match the length of 'yi'."))         ci.lb <- yi - qnorm(level/2, lower.tail = FALSE) * sqrt(vi)         ci.ub <- yi + qnorm(level/2, lower.tail = FALSE) * sqrt(vi)     }     k <- length(yi)     if (length(vi) != k)          stop(mstyle$stop("Length of 'yi' does not match the length of 'vi', 'sei', or the ('ci.lb','ci.ub')."))     slab.null <- FALSE     if (missing(slab)) {         slab <- attr(yi, "slab")         if (is.null(slab) || length(slab) != k) {             slab <- paste("Study", seq_len(k))             slab.null <- TRUE         }     }     else {         if (length(slab) == 1L && is.na(slab)) {             slab <- rep("", k)             slab.null <- TRUE         }     }     if (length(slab) != k)          stop(mstyle$stop(paste0("Length of the 'slab' argument (", length(slab), ") does not correspond to the number of outcomes (", k, ").")))     if (!is.null(ilab)) {         if (is.null(dim(ilab)))              ilab <- cbind(ilab)         if (nrow(ilab) != k)              stop(mstyle$stop(paste0("Length of the 'ilab' argument (", nrow(ilab), ") does not correspond to the number of outcomes (", k, ").")))     }     pch <- .expand1(pch, k)     if (length(pch) != k)          stop(mstyle$stop(paste0("Length of the 'pch' argument (", length(pch), ") does not correspond to the number of outcomes (", k, ").")))     if (!is.null(psize)) {         if (length(psize) == 1L)              psize <- .expand1(psize, k)         if (length(psize) != k)              stop(mstyle$stop(paste0("Length of the 'psize' argument (", length(psize), ") does not correspond to the number of outcomes (", k, ").")))     }     if (!is.null(col)) {         col <- .expand1(col, k)         if (length(col) != k)              stop(mstyle$stop(paste0("Length of the 'col' argument (", length(col), ") does not correspond to the number of outcomes (", k, ").")))     }     else {         col <- rep(par("fg"), k)     }     shade.type <- "none"     if (is.character(shade)) {         shade.type <- "character"         shade <- shade[1]         if (!is.element(shade, c("zebra", "zebra1", "zebra2", "all")))              stop(mstyle$stop("Unknown option specified for 'shade' argument."))     }     if (is.logical(shade)) {         if (length(shade) == 1L) {             shade <- "zebra"             shade.type <- "character"         }         else {             shade.type <- "logical"             shade <- .chksubset(shade, k, stoponk0 = FALSE)         }     }     if (is.numeric(shade))          shade.type <- "numeric"     subset <- .chksubset(subset, k)     if (!is.null(order)) {         if (length(order) == 1L) {             order <- match.arg(order, c("obs", "yi", "prec", "vi"))             if (order == "obs" || order == "yi")                  sort.vec <- order(yi)             if (order == "prec" || order == "vi")                  sort.vec <- order(vi, yi)         }         else {             if (length(order) != k)                  stop(mstyle$stop(paste0("Length of the 'order' argument (", length(order), ") does not correspond to the number of outcomes (", k, ").")))             if (grepl("^order\\(", deparse1(substitute(order)))) {                 sort.vec <- order             }             else {                 sort.vec <- order(order, decreasing = decreasing)             }         }         yi <- yi[sort.vec]         vi <- vi[sort.vec]         ci.lb <- ci.lb[sort.vec]         ci.ub <- ci.ub[sort.vec]         slab <- slab[sort.vec]         ilab <- ilab[sort.vec, , drop = FALSE]         pch <- pch[sort.vec]         psize <- psize[sort.vec]         col <- col[sort.vec]         subset <- subset[sort.vec]         if (shade.type == "logical")              shade <- shade[sort.vec]     }     if (!is.null(subset)) {         yi <- .getsubset(yi, subset)         vi <- .getsubset(vi, subset)         ci.lb <- .getsubset(ci.lb, subset)         ci.ub <- .getsubset(ci.ub, subset)         slab <- .getsubset(slab, subset)         ilab <- .getsubset(ilab, subset)         pch <- .getsubset(pch, subset)         psize <- .getsubset(psize, subset)         col <- .getsubset(col, subset)         if (shade.type == "logical")              shade <- .getsubset(shade, subset)     }     k <- length(yi)     if (missing(rows)) {         rows <- k:1     }     else {         if (length(rows) == 1L)              rows <- rows:(rows - k + 1)     }     if (length(rows) != k)          stop(mstyle$stop(paste0("Length of the 'rows' argument (", length(rows), ") does not correspond to the number of outcomes (", k, ")", ifelse(is.null(subset), ".", " after subsetting."))))     yi <- yi[k:1]     vi <- vi[k:1]     ci.lb <- ci.lb[k:1]     ci.ub <- ci.ub[k:1]     slab <- slab[k:1]     ilab <- ilab[k:1, , drop = FALSE]     pch <- pch[k:1]     psize <- psize[k:1]     col <- col[k:1]     rows <- rows[k:1]     if (shade.type == "logical")          shade <- shade[k:1]     yivi.na <- is.na(yi) | is.na(vi)     if (any(yivi.na)) {         not.na <- !yivi.na         if (na.act == "na.omit") {             yi <- yi[not.na]             vi <- vi[not.na]             ci.lb <- ci.lb[not.na]             ci.ub <- ci.ub[not.na]             slab <- slab[not.na]             ilab <- ilab[not.na, , drop = FALSE]             pch <- pch[not.na]             psize <- psize[not.na]             col <- col[not.na]             if (shade.type == "logical")                  shade <- shade[not.na]             rows.new <- rows             rows.na <- rows[!not.na]             for (j in seq_along(rows.na)) {                 rows.new[rows >= rows.na[j]] <- rows.new[rows >= rows.na[j]] - 1             }             rows <- rows.new[not.na]         }         if (na.act == "na.fail")              stop(mstyle$stop("Missing values in results."))     }     k <- length(yi)     if (is.function(transf)) {         if (is.null(targs)) {             yi <- sapply(yi, transf)             ci.lb <- sapply(ci.lb, transf)             ci.ub <- sapply(ci.ub, transf)         }         else {             if (!is.primitive(transf) && !is.null(targs) && length(formals(transf)) == 1L)                  stop(mstyle$stop("Function specified via 'transf' does not appear to have an argument for 'targs'."))             yi <- sapply(yi, transf, targs)             ci.lb <- sapply(ci.lb, transf, targs)             ci.ub <- sapply(ci.ub, transf, targs)         }     }     tmp <- .psort(ci.lb, ci.ub)     ci.lb <- tmp[, 1]     ci.ub <- tmp[, 2]     if (!is.null(olim)) {         yi <- .applyolim(yi, olim)         ci.lb <- .applyolim(ci.lb, olim)         ci.ub <- .applyolim(ci.ub, olim)     }     if (showweights) {         weights <- 1/vi         weights <- 100 * weights/sum(weights, na.rm = TRUE)     }     if (is.null(psize)) {         if (any(vi <= 0, na.rm = TRUE)) {             psize <- rep(1, k)         }         else {             if (length(plim) < 2L)                  stop(mstyle$stop("Argument 'plim' must be of length 2 or 3."))             wi <- 1/sqrt(vi)             if (!is.na(plim[1]) && !is.na(plim[2])) {                 rng <- max(wi, na.rm = TRUE) - min(wi, na.rm = TRUE)                 if (rng <= .Machine$double.eps^0.5) {                   psize <- rep(1, k)                 }                 else {                   psize <- (wi - min(wi, na.rm = TRUE))/rng                   psize <- (psize * (plim[2] - plim[1])) + plim[1]                 }             }             if (is.na(plim[1]) && !is.na(plim[2])) {                 psize <- wi/max(wi, na.rm = TRUE) * plim[2]                 if (length(plim) == 3L)                    psize[psize <= plim[3]] <- plim[3]             }             if (!is.na(plim[1]) && is.na(plim[2])) {                 psize <- wi/min(wi, na.rm = TRUE) * plim[1]                 if (length(plim) == 3L)                    psize[psize >= plim[3]] <- plim[3]             }             if (all(is.na(psize)))                  psize <- rep(1, k)         }     }     if (!is.null(at)) {         if (anyNA(at))              stop(mstyle$stop("Argument 'at' cannot contain NAs."))         if (any(is.infinite(at)))              stop(mstyle$stop("Argument 'at' cannot contain +-Inf values."))     }     alim.spec <- TRUE     if (missing(alim)) {         if (is.null(at)) {             alim <- range(pretty(x = c(min(ci.lb, na.rm = TRUE), max(ci.ub, na.rm = TRUE)), n = steps - 1))             alim.spec <- FALSE         }         else {             alim <- range(at)         }     }     alim <- sort(alim)[1:2]     if (anyNA(alim))          stop(mstyle$stop("Argument 'alim' cannot contain NAs."))     if (is.null(at)) {         if (alim.spec) {             at <- seq(from = alim[1], to = alim[2], length.out = steps)         }         else {             at <- pretty(x = c(min(ci.lb, na.rm = TRUE), max(ci.ub, na.rm = TRUE)), n = steps - 1)         }     }     else {         at[at < alim[1]] <- alim[1]         at[at > alim[2]] <- alim[2]         at <- unique(at)     }     if (is.null(ddd$at.lab)) {         at.lab <- at         if (is.function(atransf)) {             if (is.null(targs)) {                 at.lab <- fmtx(sapply(at.lab, atransf), digits[[2]], drop0ifint = TRUE)             }             else {                 at.lab <- fmtx(sapply(at.lab, atransf, targs), digits[[2]], drop0ifint = TRUE)             }         }         else {             at.lab <- fmtx(at.lab, digits[[2]], drop0ifint = TRUE)         }     }     else {         at.lab <- ddd$at.lab     }     ncol.ilab <- ifelse(is.null(ilab), 0, ncol(ilab))     if (slab.null) {         area.slab <- 25     }     else {         area.slab <- 40     }     if (annotate) {         if (showweights) {             area.anno <- 30         }         else {             area.anno <- 25         }     }     else {         area.anno <- 10     }     iadd <- 5     area.slab <- area.slab + iadd * ncol.ilab     area.forest <- 100 + iadd * ncol.ilab - area.slab - area.anno     area.slab <- area.slab/(100 + iadd * ncol.ilab)     area.anno <- area.anno/(100 + iadd * ncol.ilab)     area.forest <- area.forest/(100 + iadd * ncol.ilab)     plot.multp.l <- area.slab/area.forest     plot.multp.r <- area.anno/area.forest     if (missing(xlim)) {         if (min(ci.lb, na.rm = TRUE) < alim[1]) {             f.1 <- alim[1]         }         else {             f.1 <- min(ci.lb, na.rm = TRUE)         }         if (max(ci.ub, na.rm = TRUE) > alim[2]) {             f.2 <- alim[2]         }         else {             f.2 <- max(ci.ub, na.rm = TRUE)         }         rng <- f.2 - f.1         xlim <- c(f.1 - rng * plot.multp.l, f.2 + rng * plot.multp.r)         xlim <- round(xlim, digits[[2]])     }     else {         if (length(xlim) != 2L)              stop(mstyle$stop("Argument 'xlim' must be of length 2."))     }     xlim <- sort(xlim)     textpos <- .chkddd(ddd$textpos, xlim)     if (length(textpos) != 2L)          stop(mstyle$stop("Argument 'textpos' must be of length 2."))     if (is.na(textpos[1]))          textpos[1] <- xlim[1]     if (is.na(textpos[2]))          textpos[2] <- xlim[2]     if (missing(ylim)) {         ylim <- c(0, max(rows, na.rm = TRUE) + top)     }     else {         if (length(ylim) == 1L) {             ylim <- c(ylim, max(rows, na.rm = TRUE) + top)         }         else {             ylim <- sort(ylim)         }     }     if (missing(fonts)) {         fonts <- rep(par("family"), 3L)     }     else {         if (length(fonts) == 1L)              fonts <- rep(fonts, 3L)         if (length(fonts) == 2L)              fonts <- c(fonts, fonts[1])     }     if (is.null(names(fonts)))          fonts <- setNames(c(1L, 1L, 1L), nm = fonts)     par(family = names(fonts)[1], font = fonts[1])     par.mar <- par("mar")     par.mar.adj <- par.mar - c(0, 3, 1, 1)     par.mar.adj[par.mar.adj < 0] <- 0     par(mar = par.mar.adj)     on.exit(par(mar = par.mar), add = TRUE)     lplot(NA, NA, xlim = xlim, ylim = ylim, xlab = "", ylab = "", yaxt = "n", xaxt = "n", xaxs = "i", yaxs = "i", bty = "n", ...)     if (shade.type == "character") {         if (shade == "zebra" || shade == "zebra1")              tmp <- rep_len(c(TRUE, FALSE), k)         if (shade == "zebra2")              tmp <- rep_len(c(FALSE, TRUE), k)         if (shade == "all")              tmp <- rep_len(TRUE, k)         shade <- tmp     }     if (shade.type %in% c("character", "logical")) {         for (i in seq_len(k)) {             if (shade[i])                  rect(xlim[1], rows[i] - 0.5, xlim[2], rows[i] + 0.5, border = colshade, col = colshade)         }     }     if (shade.type == "numeric") {         for (i in seq_along(shade)) {             rect(xlim[1], shade[i] - 0.5, xlim[2], shade[i] + 0.5, border = colshade, col = colshade)         }     }     labline(h = ylim[2] - (top - 1), lty = lty[2], ...)     par.usr <- par("usr")     if (is.numeric(refline))          lsegments(refline, par.usr[3], refline, ylim[2] - (top - 1), lty = "dotted", ...)     height <- par.usr[4] - par.usr[3]     if (is.null(cex)) {         lheight <- strheight("O")         cex.adj <- ifelse(k * lheight > height * 0.8, height/(1.25 * k * lheight), 1)     }     if (is.null(cex)) {         cex <- par("cex") * cex.adj     }     else {         if (is.null(cex.lab))              cex.lab <- par("cex") * cex         if (is.null(cex.axis))              cex.axis <- cex     }     if (is.null(cex.lab))          cex.lab <- par("cex") * cex.adj     if (is.null(cex.axis))          cex.axis <- par("cex") * cex.adj     laxis(side = 1, at = at, labels = at.lab, cex.axis = cex.axis, ...)     if (missing(xlab))          xlab <- .setlab(measure, transf.char, atransf.char, gentype = 1)     if (!is.element(length(xlab), 1:3))          stop(mstyle$stop("Argument 'xlab' argument must be of length 1, 2, or 3."))     if (length(xlab) == 1L)          lmtext(xlab, side = 1, at = min(at) + (max(at) - min(at))/2, line = par("mgp")[1] - 0.5, cex = cex.lab, font = xlabfont[1], ...)     if (length(xlab) == 2L) {         lmtext(xlab[1], side = 1, at = min(at), line = par("mgp")[1] - 0.5, cex = cex.lab, adj = xlabadj[1], font = xlabfont[1], ...)         lmtext(xlab[2], side = 1, at = max(at), line = par("mgp")[1] - 0.5, cex = cex.lab, adj = xlabadj[2], font = xlabfont[1], ...)     }     if (length(xlab) == 3L) {         lmtext(xlab[1], side = 1, at = min(at), line = par("mgp")[1] - 0.5, cex = cex.lab, adj = xlabadj[1], font = xlabfont[1], ...)         lmtext(xlab[2], side = 1, at = min(at) + (max(at) - min(at))/2, line = par("mgp")[1] - 0.5, cex = cex.lab, font = xlabfont[2], ...)         lmtext(xlab[3], side = 1, at = max(at), line = par("mgp")[1] - 0.5, cex = cex.lab, adj = xlabadj[2], font = xlabfont[1], ...)     }     ciendheight <- height/150 * cex * efac[1]     arrowwidth <- 1.4/100 * cex * (xlim[2] - xlim[1])     arrowheight <- height/150 * cex * efac[2]     for (i in seq_len(k)) {         if (is.na(yi[i]) || is.na(ci.lb[i]) || is.na(ci.ub[i]))              next         if (ci.lb[i] >= alim[2]) {             lpolygon(x = c(alim[2], alim[2] - arrowwidth, alim[2] - arrowwidth, alim[2]), y = c(rows[i], rows[i] + arrowheight, rows[i] - arrowheight, rows[i]), col = col[i], border = col[i], ...)             next         }         if (ci.ub[i] <= alim[1]) {             lpolygon(x = c(alim[1], alim[1] + arrowwidth, alim[1] + arrowwidth, alim[1]), y = c(rows[i], rows[i] + arrowheight, rows[i] - arrowheight, rows[i]), col = col[i], border = col[i], ...)             next         }         lsegments(max(ci.lb[i], alim[1]), rows[i], min(ci.ub[i], alim[2]), rows[i], lty = lty[1], col = col[i], ...)         if (ci.lb[i] >= alim[1]) {             lsegments(ci.lb[i], rows[i] - ciendheight, ci.lb[i], rows[i] + ciendheight, col = col[i], ...)         }         else {             lpolygon(x = c(alim[1], alim[1] + arrowwidth, alim[1] + arrowwidth, alim[1]), y = c(rows[i], rows[i] + arrowheight, rows[i] - arrowheight, rows[i]), col = col[i], border = col[i], ...)         }         if (ci.ub[i] <= alim[2]) {             lsegments(ci.ub[i], rows[i] - ciendheight, ci.ub[i], rows[i] + ciendheight, col = col[i], ...)         }         else {             lpolygon(x = c(alim[2], alim[2] - arrowwidth, alim[2] - arrowwidth, alim[2]), y = c(rows[i], rows[i] + arrowheight, rows[i] - arrowheight, rows[i]), col = col[i], border = col[i], ...)         }     }     ltext(textpos[1], rows + rowadj[1], slab, pos = 4, cex = cex, col = col, ...)     if (!is.null(ilab)) {         if (is.null(ilab.xpos)) {             dist <- min(ci.lb, na.rm = TRUE) - xlim[1]             if (ncol.ilab == 1L)                  ilab.xpos <- xlim[1] + dist * 0.75             if (ncol.ilab == 2L)                  ilab.xpos <- xlim[1] + dist * c(0.65, 0.85)             if (ncol.ilab == 3L)                  ilab.xpos <- xlim[1] + dist * c(0.6, 0.75, 0.9)             if (ncol.ilab >= 4L)                  ilab.xpos <- seq(xlim[1] + dist * 0.5, xlim[1] + dist * 0.9, length.out = ncol.ilab)         }         if (length(ilab.xpos) != ncol.ilab)              stop(mstyle$stop(paste0("Number of 'ilab' columns (", ncol.ilab, ") does not match the length of the 'ilab.xpos' argument (", length(ilab.xpos), ").")))         if (!is.null(ilab.pos) && length(ilab.pos) == 1L)              ilab.pos <- rep(ilab.pos, ncol.ilab)         if (!is.null(ilab.lab) && length(ilab.lab) != ncol.ilab)              stop(mstyle$stop(paste0("Number of 'ilab' columns (", ncol.ilab, ") does not match the length of the 'ilab.lab' argument (", length(ilab.lab), ").")))         par(family = names(fonts)[3], font = fonts[3])         for (l in seq_len(ncol.ilab)) {             ltext(ilab.xpos[l], rows + rowadj[3], ilab[, l], pos = ilab.pos[l], cex = cex, ...)             if (!is.null(ilab.lab))                  ltext(ilab.xpos[l], ylim[2] - (top - 1) + 1 + rowadj[3], ilab.lab[l], pos = ilab.pos[l], font = 2, cex = cex, ...)         }         par(family = names(fonts)[1], font = fonts[1])     }     if (annotate) {         if (is.function(atransf)) {             if (is.null(targs)) {                 annotext <- cbind(sapply(yi, atransf), sapply(ci.lb, atransf), sapply(ci.ub, atransf))             }             else {                 annotext <- cbind(sapply(yi, atransf, targs), sapply(ci.lb, atransf, targs), sapply(ci.ub, atransf, targs))             }             tmp <- .psort(annotext[, 2:3])             annotext[, 2:3] <- tmp         }         else {             annotext <- cbind(yi, ci.lb, ci.ub)         }         if (showweights) {             annotext <- cbind(weights, annotext)             annotext <- fmtx(annotext, c(digits[[3]], digits[[1]], digits[[1]], digits[[1]]))         }         else {             annotext <- fmtx(annotext, digits[[1]])         }         if (missing(width)) {             width <- apply(annotext, 2, function(x) max(nchar(x)))         }         else {             width <- .expand1(width, ncol(annotext))             if (length(width) != ncol(annotext))                  stop(mstyle$stop(paste0("Length of the 'width' argument (", length(width), ") does not match the number of annotation columns (", ncol(annotext), ").")))         }         for (j in seq_len(ncol(annotext))) {             annotext[, j] <- formatC(annotext[, j], width = width[j])         }         if (showweights) {             annotext <- cbind(annotext[, 1], paste0("%", paste0(rep(substr(annosym[1], 1, 1), 3), collapse = "")), annotext[, 2], annosym[1], annotext[, 3], annosym[2], annotext[, 4], annosym[3])         }         else {             annotext <- cbind(annotext[, 1], annosym[1], annotext[, 2], annosym[2], annotext[, 3], annosym[3])         }         annotext <- apply(annotext, 1, paste, collapse = "")         annotext[grepl("NA", annotext, fixed = TRUE)] <- ""         annotext <- gsub("-", annosym[4], annotext, fixed = TRUE)         annotext <- gsub(" ", annosym[5], annotext, fixed = TRUE)         par(family = names(fonts)[2], font = fonts[2])         ltext(textpos[2], rows + rowadj[2], labels = annotext, pos = 2, cex = cex, col = col, ...)         par(family = names(fonts)[1], font = fonts[1])     }     else {         width <- NULL     }     for (i in seq_len(k)) {         if (is.na(yi[i]))              next         if (yi[i] >= alim[1] && yi[i] <= alim[2])              lpoints(x = yi[i], y = rows[i], pch = pch[i], cex = cex * psize[i], col = col[i], ...)     }     ltext(textpos[1], ylim[2] - (top - 1) + 1 + rowadj[1], header.left, pos = 4, font = 2, cex = cex, ...)     ltext(textpos[2], ylim[2] - (top - 1) + 1 + rowadj[2], header.right, pos = 2, font = 2, cex = cex, ...)     res <- list(xlim = par("usr")[1:2], alim = alim, at = at, ylim = ylim, rows = rows, cex = cex, cex.lab = cex.lab, cex.axis = cex.axis, ilab.xpos = ilab.xpos, ilab.pos = ilab.pos, textpos = textpos)     sav <- c(res, list(level = level, annotate = annotate, digits = digits[[1]], width = width, transf = transf, atransf = atransf, targs = targs, alim = alim, olim = olim, rowadj = rowadj, fonts = fonts[1:2], annosym = annosym))     try(assign("forest", sav, envir = .metafor), silent = TRUE)     invisible(res) })(x = NULL, ci.lb = NULL, ci.ub = NULL, sei = NULL, slab = c("Ames, 2001", "Benton, 2002", "Cruz, 2003", "Dover, 2004", "Elia, 2005"), ilab = structure(c("4", "8", "10", "15", "18", "96", "92", "90", "85", "82"), dim = c(5L, 2L), dimnames = list(NULL, c("Events", "Non-events"))), ilab.xpos = c(-0.682103174603174, -0.362738095238095), textpos = c(-2.05873015873016, 1.58214285714286), xlim = c(-2.23873015873016, 1.76214285714286), alim = c(0, 1), at = c(0, 0.2, 0.4, 0.6, 0.8, 1), refline = NA, xlab = "Proportion",      cex = 1.08, cex.lab = 1.08, cex.axis = 1.08, header = FALSE, rows = 5:1, ylim = c(-5, 8), annotate = FALSE, xaxt = "n", col = "black", colshade = "#eeeeee", shade = "zebra", lty = c("solid", "blank", "blank"), pch = 15, lwd = 1.35, efac = 0, digits = 3L, psize = c(1.5, 1.11832919797895, 0.962718637119288, 0.648550131541075, 0.5))`: Length of the 'slab' argument (5) does not correspond to the number of outcomes (0).
Backtrace:
    ▆
 1. └─RCMetaR::rcmetar.draw.forest.plot(bundle, png_path) at test-forest-metafor-renderer.R:1402:5
 2.   └─RCMetaR:::rcmetar.draw.metafor.forest(plot.data, outpath) at RCMetaR/R/rcmetar-core.R:518:9
 3.     └─RCMetaR (local) renderer(bundle, outpath) at RCMetaR/R/forest_metafor.R:905:9
 4.       └─RCMetaR:::rcmetar.render.plot_file(...) at RCMetaR/R/forest_style_default.R:233:5
 5.         └─RCMetaR:::rcmetar.render.plot_svg(svg.path, size, draw) at RCMetaR/R/plot_devices.R:289:5
 6.           └─RCMetaR (local) draw() at RCMetaR/R/plot_devices.R:198:5
 7.             ├─base::do.call(...) at RCMetaR/R/forest_style_default.R:290:9
 8.             └─metafor (local) `<fn>`(...)

Failure ('test-forest-metafor-renderer.R:1554:3'): diagnostic Default Forest Style builds and renders count columns on transformed axes
Expected `rcmetar.metafor.atransf(bundle)` to be identical to `invlogit`.
Differences:
`actual` is NULL
`expected` is a function


Error ('test-forest-metafor-renderer.R:1570:3'): diagnostic Default Forest Style builds and renders count columns on transformed axes
Error in `exp(x)`: non-numeric argument to mathematical function
Backtrace:
     ▆
  1. └─RCMetaR::rcmetar.draw.forest.plot(bundle, png_path) at test-forest-metafor-renderer.R:1570:3
  2.   └─RCMetaR:::rcmetar.draw.metafor.forest(plot.data, outpath) at RCMetaR/R/rcmetar-core.R:518:9
  3.     └─RCMetaR (local) renderer(bundle, outpath) at RCMetaR/R/forest_metafor.R:905:9
  4.       └─RCMetaR:::rcmetar.render.plot_file(...) at RCMetaR/R/forest_style_default.R:233:5
  5.         └─RCMetaR:::rcmetar.render.plot_svg(svg.path, size, draw) at RCMetaR/R/plot_devices.R:289:5
  6.           └─RCMetaR (local) draw() at RCMetaR/R/plot_devices.R:198:5
  7.             └─RCMetaR:::rcmetar.forest.axis.effect(bundle, bundle$effect) at RCMetaR/R/forest_style_default.R:284:9
  8.               └─RCMetaR:::rcmetar.forest.axis.values(bundle, effect[[field]]) at RCMetaR/R/forest_axis.R:23:9
  9.                 └─rcmetar.bundle.transform(bundle)$display.scale(values, ni = bundle$sample_sizes) at RCMetaR/R/forest_axis.R:18:5
 10.                   └─RCMetaR:::invlogit(x) at RCMetaR/R/diagnostic_methods.R:113:13

Error ('test-forest-metafor-renderer.R:1603:5'): diagnostic multi-metric workflows save independent metafor forest plots
Error in `exp(x)`: non-numeric argument to mathematical function
Backtrace:
     ▆
  1. └─RCMetaR (local) run_metrics(c("Sens", "Spec", "NLR", "PLR")) at test-forest-metafor-renderer.R:1645:3
  2.   └─RCMetaR::rcmetar.run.diagnostic.analyses(...) at test-forest-metafor-renderer.R:1603:5
  3.     └─RCMetaR:::multiple.diagnostic(methods, params.list, diagnostic.data) at RCMetaR/R/rcmetar-core.R:688:5
  4.       └─RCMetaR:::rcmetar.diagnostic.fit(...) at RCMetaR/R/diagnostic_methods.R:247:13
  5.         └─RCMetaR:::.rcmetar.call.method(method, prepared.data, params) at RCMetaR/R/diagnostic_methods.R:155:5
  6.           └─RCMetaR:::diagnostic.random(om.data, params) at RCMetaR/R/rcmetar-core.R:826:5
  7.             └─RCMetaR::rcmetar.draw.forest.plot(plot.data, forest.path) at RCMetaR/R/diagnostic_methods.R:628:13
  8.               └─RCMetaR:::rcmetar.draw.metafor.forest(plot.data, outpath) at RCMetaR/R/rcmetar-core.R:518:9
  9.                 └─RCMetaR (local) renderer(bundle, outpath) at RCMetaR/R/forest_metafor.R:905:9
 10.                   └─RCMetaR:::rcmetar.render.plot_file(...) at RCMetaR/R/forest_style_default.R:233:5
 11.                     └─RCMetaR:::rcmetar.render.plot_svg(svg.path, size, draw) at RCMetaR/R/plot_devices.R:289:5
 12.                       └─RCMetaR (local) draw() at RCMetaR/R/plot_devices.R:198:5
 13.                         └─RCMetaR:::rcmetar.forest.axis.effect(bundle, bundle$effect) at RCMetaR/R/forest_style_default.R:284:9
 14.                           └─RCMetaR:::rcmetar.forest.axis.values(bundle, effect[[field]]) at RCMetaR/R/forest_axis.R:23:9
 15.                             └─rcmetar.bundle.transform(bundle)$display.scale(values, ni = bundle$sample_sizes) at RCMetaR/R/forest_axis.R:18:5
 16.                               └─RCMetaR:::invlogit(x) at RCMetaR/R/diagnostic_methods.R:113:13
────────────────────────────────────────────────────────────────────────────────

⠏ |          0 | forest-subgroup-range                                          
✔ |          4 | forest-subgroup-range

⠏ |          0 | summary-display                                                
⠦ |          7 | summary-display                                                
⠴ |         16 | summary-display                                                
⠼ |         35 | summary-display                                                
⠙ |         62 | summary-display                                                
⠴ |         76 | summary-display                                                
⠧ |         88 | summary-display                                                
⠴ |         96 | summary-display                                                
✔ |        105 | summary-display

══ Results ═════════════════════════════════════════════════════════════════════
Duration: 174.4 s

── Failed tests ────────────────────────────────────────────────────────────────
Failure ('test-forest-metafor-renderer.R:889:5'): BMJ Forest Style builds faithful family columns and renders smoke cases
Expected `bundle$style_blocks$axis_label` to equal `case$axis_label`.
Differences:
`actual`:   "Odds ratio"
`expected`: "Odds Ratio"


Error ('test-forest-metafor-renderer.R:1055:5'): entered-effect-only standard plots render without raw arm columns
Error in `exp(x)`: non-numeric argument to mathematical function
Backtrace:
     ▆
  1. └─RCMetaR::rcmetar.draw.forest.plot(bundle, png_path) at test-forest-metafor-renderer.R:1055:5
  2.   └─RCMetaR:::rcmetar.draw.metafor.forest(plot.data, outpath) at RCMetaR/R/rcmetar-core.R:518:9
  3.     └─RCMetaR (local) renderer(bundle, outpath) at RCMetaR/R/forest_metafor.R:905:9
  4.       └─RCMetaR:::rcmetar.render.plot_file(...) at RCMetaR/R/forest_style_default.R:233:5
  5.         └─RCMetaR:::rcmetar.render.plot_svg(svg.path, size, draw) at RCMetaR/R/plot_devices.R:289:5
  6.           └─RCMetaR (local) draw() at RCMetaR/R/plot_devices.R:198:5
  7.             └─RCMetaR:::rcmetar.forest.axis.effect(bundle, bundle$effect) at RCMetaR/R/forest_style_default.R:284:9
  8.               └─RCMetaR:::rcmetar.forest.axis.values(bundle, effect[[field]]) at RCMetaR/R/forest_axis.R:23:9
  9.                 └─rcmetar.bundle.transform(bundle)$display.scale(values, ni = bundle$sample_sizes) at RCMetaR/R/forest_axis.R:18:5
 10.                   └─RCMetaR:::invlogit(x) at RCMetaR/R/diagnostic_methods.R:113:13

Error ('test-forest-metafor-renderer.R:1402:5'): single-arm binary metrics build and render Default metafor bundles
Error in `(function (x, vi, sei, ci.lb, ci.ub, annotate = TRUE, showweights = FALSE, header = TRUE, xlim, alim, olim, ylim, at, steps = 5, level = 95, refline = 0, digits = 2L, width, xlab, slab, ilab, ilab.lab, ilab.xpos, ilab.pos, order, subset, transf, atransf, targs, rows, efac = 1, pch, psize, plim = c(0.5, 1.5), col, shade, colshade, lty, fonts, cex, cex.lab, cex.axis, ...)  {     mstyle <- .get.mstyle()     na.act <- getOption("na.action")     if (!is.element(na.act, c("na.omit", "na.exclude", "na.fail", "na.pass")))          stop(mstyle$stop("Unknown 'na.action' specified under options()."))     if (missing(transf))          transf <- FALSE     if (missing(atransf))          atransf <- FALSE     transf.char <- deparse(transf)     atransf.char <- deparse(atransf)     if (is.function(transf) && is.function(atransf))          stop(mstyle$stop("Use either 'transf' or 'atransf' to specify a transformation (not both)."))     .start.plot()     yi <- x     if (missing(targs))          targs <- NULL     if (missing(at))          at <- NULL     if (missing(ilab))          ilab <- NULL     if (missing(ilab.lab))          ilab.lab <- NULL     if (missing(ilab.xpos))          ilab.xpos <- NULL     if (missing(ilab.pos))          ilab.pos <- NULL     if (missing(subset))          subset <- NULL     if (missing(order))          order <- NULL     if (missing(pch))          pch <- 15     if (missing(psize))          psize <- NULL     if (missing(col))          col <- NULL     if (missing(shade))          shade <- NULL     if (missing(colshade))          colshade <- .coladj(par("bg", "fg"), dark = 0.1, light = -0.1)     if (missing(cex))          cex <- NULL     if (missing(cex.lab))          cex.lab <- NULL     if (missing(cex.axis))          cex.axis <- NULL     level <- .level(level)     if (length(digits) == 1L)          digits <- c(digits, digits, digits)     if (length(digits) == 2L)          digits <- c(digits, digits[[1]])     ddd <- list(...)     if (missing(lty)) {         lty <- c("solid", "solid")     }     else {         if (length(lty) == 1L)              lty <- c(lty, "solid")     }     efac <- .expand1(efac, 4L)     if (length(efac) == 2L)          efac <- c(efac, 1, 1)     if (length(efac) == 3L)          efac <- efac[c(1:3, 3)]     efac[efac == 0] <- NA     if (is.null(ddd$annosym)) {         annosym <- c(" [", ", ", "]", "-", " ")     }     else {         annosym <- ddd$annosym         if (length(annosym) == 3L)              annosym <- c(annosym, "-", " ")         if (length(annosym) == 4L)              annosym <- c(annosym, " ")         if (length(annosym) != 5L)              stop(mstyle$stop("Argument 'annosym' must be a vector of length 3 (or 4 or 5)."))     }     if (isTRUE(ddd$tabfig == 1))          annosym <- c(" [", ", ", "]", "−", " ")     if (isTRUE(ddd$tabfig == 2))          annosym <- c(" [", ", ", "]", "–", " ")     if (isTRUE(ddd$tabfig == 3))          annosym <- c(" [", ", ", "]", "−", " ")     if (is.null(attr(yi, "measure"))) {         measure <- "GEN"     }     else {         measure <- attr(yi, "measure")     }     estlab <- .setlab(measure, transf.char, atransf.char, gentype = 3, short = TRUE)     if (is.expression(estlab)) {         header.right <- str2lang(paste0("bold(", estlab, " * '", annosym[1], "' * '", round(100 * (1 - level), digits[[1]]), "% CI'", " * '", annosym[3], "')"))     }     else {         header.right <- paste0(estlab, annosym[1], round(100 * (1 - level), digits[[1]]), "% CI", annosym[3])     }     if (is.logical(header)) {         if (header) {             header.left <- "Study"         }         else {             header.left <- NULL             header.right <- NULL         }     }     else {         if (!is.character(header))              stop(mstyle$stop("Argument 'header' must either be a logical or character vector."))         if (length(header) == 1L) {             header.left <- header         }         else {             header.left <- header[1]             header.right <- header[2]         }     }     if (!annotate)          header.right <- NULL     decreasing <- .chkddd(ddd$decreasing, FALSE)     if (is.null(ddd$clim)) {         if (missing(olim))              olim <- NULL     }     else {         olim <- ddd$clim     }     if (!is.null(olim)) {         if (length(olim) != 2L)              stop(mstyle$stop("Argument 'olim' must be of length 2."))         if (anyNA(olim))              stop(mstyle$stop("Argument 'olim' cannot contain NAs."))         olim <- sort(olim)     }     if (is.null(ddd$rowadj)) {         rowadj <- rep(0, 3)     }     else {         rowadj <- ddd$rowadj         if (length(rowadj) == 1L)              rowadj <- c(rowadj, rowadj, 0)         if (length(rowadj) == 2L)              rowadj <- c(rowadj, 0)     }     top <- .chkddd(ddd$top, 3)     if (is.null(ddd$xlabadj)) {         xlabadj <- c(NA, NA)     }     else {         xlabadj <- ddd$xlabadj         if (length(xlabadj) == 1L)              xlabadj <- c(xlabadj, 1 - xlabadj)     }     xlabfont <- .chkddd(ddd$xlabfont, 1)     if (!is.null(ddd$mlab))          warning("The forest.default() function does not have an 'mlab' argument.", call. = FALSE, immediate. = TRUE)     if (!is.null(ddd$addfit))          warning("The forest.default() function does not have an 'addfit' argument.", call. = FALSE, immediate. = TRUE)     if (!is.null(ddd$addpred))          warning("The forest.default() function does not have an 'addpred' argument.", call. = FALSE, immediate. = TRUE)     if (!is.null(ddd$predstyle))          warning("The forest.default() function does not have a 'predstyle' argument.", call. = FALSE, immediate. = TRUE)     if (!is.null(ddd$predlim))          warning("The forest.default() function does not have a 'predlim' argument.", call. = FALSE, immediate. = TRUE)     if (!is.null(ddd$colout))          warning("The forest.default() function does not have a 'colout' argument.", call. = FALSE, immediate. = TRUE)     if (!is.null(ddd$border))          warning("The forest.default() function does not have a 'border' argument.", call. = FALSE, immediate. = TRUE)     lplot <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) plot(...)     labline <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) abline(...)     lsegments <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) segments(...)     laxis <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) axis(...)     lmtext <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) mtext(...)     lpolygon <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) polygon(...)     ltext <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) text(...)     lpoints <- function(..., textpos, decreasing, clim, rowadj, annosym, tabfig, top, xlabadj, xlabfont, at.lab, mlab, addfit, addpred, predstyle, predlim, colout, border) points(...)     if (!missing(vi) && is.function(vi))          stop(mstyle$stop("Cannot find variable specified for the 'vi' argument."))     if (hasArg(ci.lb) && hasArg(ci.ub) && !is.null(ci.lb) && !is.null(ci.ub)) {         if (length(ci.lb) != length(ci.ub))              stop(mstyle$stop("Length of 'ci.lb' and 'ci.ub' are not the same."))         if (missing(vi) && missing(sei)) {             vi <- ((ci.ub - ci.lb)/(2 * qnorm(level/2, lower.tail = FALSE)))^2         }         else {             if (missing(vi))                  vi <- sei^2         }         if (length(ci.lb) != length(vi))              stop(mstyle$stop("Length of 'vi' (or 'sei') does not match the length of ('ci.lb','ci.ub')."))     }     else {         if (missing(vi)) {             if (missing(sei)) {                 stop(mstyle$stop("Must specify either 'vi', 'sei', or ('ci.lb','ci.ub')."))             }             else {                 vi <- sei^2             }         }         if (length(yi) != length(vi))              stop(mstyle$stop("Length of 'vi' (or 'sei') does not match the length of 'yi'."))         ci.lb <- yi - qnorm(level/2, lower.tail = FALSE) * sqrt(vi)         ci.ub <- yi + qnorm(level/2, lower.tail = FALSE) * sqrt(vi)     }     k <- length(yi)     if (length(vi) != k)          stop(mstyle$stop("Length of 'yi' does not match the length of 'vi', 'sei', or the ('ci.lb','ci.ub')."))     slab.null <- FALSE     if (missing(slab)) {         slab <- attr(yi, "slab")         if (is.null(slab) || length(slab) != k) {             slab <- paste("Study", seq_len(k))             slab.null <- TRUE         }     }     else {         if (length(slab) == 1L && is.na(slab)) {             slab <- rep("", k)             slab.null <- TRUE         }     }     if (length(slab) != k)          stop(mstyle$stop(paste0("Length of the 'slab' argument (", length(slab), ") does not correspond to the number of outcomes (", k, ").")))     if (!is.null(ilab)) {         if (is.null(dim(ilab)))              ilab <- cbind(ilab)         if (nrow(ilab) != k)              stop(mstyle$stop(paste0("Length of the 'ilab' argument (", nrow(ilab), ") does not correspond to the number of outcomes (", k, ").")))     }     pch <- .expand1(pch, k)     if (length(pch) != k)          stop(mstyle$stop(paste0("Length of the 'pch' argument (", length(pch), ") does not correspond to the number of outcomes (", k, ").")))     if (!is.null(psize)) {         if (length(psize) == 1L)              psize <- .expand1(psize, k)         if (length(psize) != k)              stop(mstyle$stop(paste0("Length of the 'psize' argument (", length(psize), ") does not correspond to the number of outcomes (", k, ").")))     }     if (!is.null(col)) {         col <- .expand1(col, k)         if (length(col) != k)              stop(mstyle$stop(paste0("Length of the 'col' argument (", length(col), ") does not correspond to the number of outcomes (", k, ").")))     }     else {         col <- rep(par("fg"), k)     }     shade.type <- "none"     if (is.character(shade)) {         shade.type <- "character"         shade <- shade[1]         if (!is.element(shade, c("zebra", "zebra1", "zebra2", "all")))              stop(mstyle$stop("Unknown option specified for 'shade' argument."))     }     if (is.logical(shade)) {         if (length(shade) == 1L) {             shade <- "zebra"             shade.type <- "character"         }         else {             shade.type <- "logical"             shade <- .chksubset(shade, k, stoponk0 = FALSE)         }     }     if (is.numeric(shade))          shade.type <- "numeric"     subset <- .chksubset(subset, k)     if (!is.null(order)) {         if (length(order) == 1L) {             order <- match.arg(order, c("obs", "yi", "prec", "vi"))             if (order == "obs" || order == "yi")                  sort.vec <- order(yi)             if (order == "prec" || order == "vi")                  sort.vec <- order(vi, yi)         }         else {             if (length(order) != k)                  stop(mstyle$stop(paste0("Length of the 'order' argument (", length(order), ") does not correspond to the number of outcomes (", k, ").")))             if (grepl("^order\\(", deparse1(substitute(order)))) {                 sort.vec <- order             }             else {                 sort.vec <- order(order, decreasing = decreasing)             }         }         yi <- yi[sort.vec]         vi <- vi[sort.vec]         ci.lb <- ci.lb[sort.vec]         ci.ub <- ci.ub[sort.vec]         slab <- slab[sort.vec]         ilab <- ilab[sort.vec, , drop = FALSE]         pch <- pch[sort.vec]         psize <- psize[sort.vec]         col <- col[sort.vec]         subset <- subset[sort.vec]         if (shade.type == "logical")              shade <- shade[sort.vec]     }     if (!is.null(subset)) {         yi <- .getsubset(yi, subset)         vi <- .getsubset(vi, subset)         ci.lb <- .getsubset(ci.lb, subset)         ci.ub <- .getsubset(ci.ub, subset)         slab <- .getsubset(slab, subset)         ilab <- .getsubset(ilab, subset)         pch <- .getsubset(pch, subset)         psize <- .getsubset(psize, subset)         col <- .getsubset(col, subset)         if (shade.type == "logical")              shade <- .getsubset(shade, subset)     }     k <- length(yi)     if (missing(rows)) {         rows <- k:1     }     else {         if (length(rows) == 1L)              rows <- rows:(rows - k + 1)     }     if (length(rows) != k)          stop(mstyle$stop(paste0("Length of the 'rows' argument (", length(rows), ") does not correspond to the number of outcomes (", k, ")", ifelse(is.null(subset), ".", " after subsetting."))))     yi <- yi[k:1]     vi <- vi[k:1]     ci.lb <- ci.lb[k:1]     ci.ub <- ci.ub[k:1]     slab <- slab[k:1]     ilab <- ilab[k:1, , drop = FALSE]     pch <- pch[k:1]     psize <- psize[k:1]     col <- col[k:1]     rows <- rows[k:1]     if (shade.type == "logical")          shade <- shade[k:1]     yivi.na <- is.na(yi) | is.na(vi)     if (any(yivi.na)) {         not.na <- !yivi.na         if (na.act == "na.omit") {             yi <- yi[not.na]             vi <- vi[not.na]             ci.lb <- ci.lb[not.na]             ci.ub <- ci.ub[not.na]             slab <- slab[not.na]             ilab <- ilab[not.na, , drop = FALSE]             pch <- pch[not.na]             psize <- psize[not.na]             col <- col[not.na]             if (shade.type == "logical")                  shade <- shade[not.na]             rows.new <- rows             rows.na <- rows[!not.na]             for (j in seq_along(rows.na)) {                 rows.new[rows >= rows.na[j]] <- rows.new[rows >= rows.na[j]] - 1             }             rows <- rows.new[not.na]         }         if (na.act == "na.fail")              stop(mstyle$stop("Missing values in results."))     }     k <- length(yi)     if (is.function(transf)) {         if (is.null(targs)) {             yi <- sapply(yi, transf)             ci.lb <- sapply(ci.lb, transf)             ci.ub <- sapply(ci.ub, transf)         }         else {             if (!is.primitive(transf) && !is.null(targs) && length(formals(transf)) == 1L)                  stop(mstyle$stop("Function specified via 'transf' does not appear to have an argument for 'targs'."))             yi <- sapply(yi, transf, targs)             ci.lb <- sapply(ci.lb, transf, targs)             ci.ub <- sapply(ci.ub, transf, targs)         }     }     tmp <- .psort(ci.lb, ci.ub)     ci.lb <- tmp[, 1]     ci.ub <- tmp[, 2]     if (!is.null(olim)) {         yi <- .applyolim(yi, olim)         ci.lb <- .applyolim(ci.lb, olim)         ci.ub <- .applyolim(ci.ub, olim)     }     if (showweights) {         weights <- 1/vi         weights <- 100 * weights/sum(weights, na.rm = TRUE)     }     if (is.null(psize)) {         if (any(vi <= 0, na.rm = TRUE)) {             psize <- rep(1, k)         }         else {             if (length(plim) < 2L)                  stop(mstyle$stop("Argument 'plim' must be of length 2 or 3."))             wi <- 1/sqrt(vi)             if (!is.na(plim[1]) && !is.na(plim[2])) {                 rng <- max(wi, na.rm = TRUE) - min(wi, na.rm = TRUE)                 if (rng <= .Machine$double.eps^0.5) {                   psize <- rep(1, k)                 }                 else {                   psize <- (wi - min(wi, na.rm = TRUE))/rng                   psize <- (psize * (plim[2] - plim[1])) + plim[1]                 }             }             if (is.na(plim[1]) && !is.na(plim[2])) {                 psize <- wi/max(wi, na.rm = TRUE) * plim[2]                 if (length(plim) == 3L)                    psize[psize <= plim[3]] <- plim[3]             }             if (!is.na(plim[1]) && is.na(plim[2])) {                 psize <- wi/min(wi, na.rm = TRUE) * plim[1]                 if (length(plim) == 3L)                    psize[psize >= plim[3]] <- plim[3]             }             if (all(is.na(psize)))                  psize <- rep(1, k)         }     }     if (!is.null(at)) {         if (anyNA(at))              stop(mstyle$stop("Argument 'at' cannot contain NAs."))         if (any(is.infinite(at)))              stop(mstyle$stop("Argument 'at' cannot contain +-Inf values."))     }     alim.spec <- TRUE     if (missing(alim)) {         if (is.null(at)) {             alim <- range(pretty(x = c(min(ci.lb, na.rm = TRUE), max(ci.ub, na.rm = TRUE)), n = steps - 1))             alim.spec <- FALSE         }         else {             alim <- range(at)         }     }     alim <- sort(alim)[1:2]     if (anyNA(alim))          stop(mstyle$stop("Argument 'alim' cannot contain NAs."))     if (is.null(at)) {         if (alim.spec) {             at <- seq(from = alim[1], to = alim[2], length.out = steps)         }         else {             at <- pretty(x = c(min(ci.lb, na.rm = TRUE), max(ci.ub, na.rm = TRUE)), n = steps - 1)         }     }     else {         at[at < alim[1]] <- alim[1]         at[at > alim[2]] <- alim[2]         at <- unique(at)     }     if (is.null(ddd$at.lab)) {         at.lab <- at         if (is.function(atransf)) {             if (is.null(targs)) {                 at.lab <- fmtx(sapply(at.lab, atransf), digits[[2]], drop0ifint = TRUE)             }             else {                 at.lab <- fmtx(sapply(at.lab, atransf, targs), digits[[2]], drop0ifint = TRUE)             }         }         else {             at.lab <- fmtx(at.lab, digits[[2]], drop0ifint = TRUE)         }     }     else {         at.lab <- ddd$at.lab     }     ncol.ilab <- ifelse(is.null(ilab), 0, ncol(ilab))     if (slab.null) {         area.slab <- 25     }     else {         area.slab <- 40     }     if (annotate) {         if (showweights) {             area.anno <- 30         }         else {             area.anno <- 25         }     }     else {         area.anno <- 10     }     iadd <- 5     area.slab <- area.slab + iadd * ncol.ilab     area.forest <- 100 + iadd * ncol.ilab - area.slab - area.anno     area.slab <- area.slab/(100 + iadd * ncol.ilab)     area.anno <- area.anno/(100 + iadd * ncol.ilab)     area.forest <- area.forest/(100 + iadd * ncol.ilab)     plot.multp.l <- area.slab/area.forest     plot.multp.r <- area.anno/area.forest     if (missing(xlim)) {         if (min(ci.lb, na.rm = TRUE) < alim[1]) {             f.1 <- alim[1]         }         else {             f.1 <- min(ci.lb, na.rm = TRUE)         }         if (max(ci.ub, na.rm = TRUE) > alim[2]) {             f.2 <- alim[2]         }         else {             f.2 <- max(ci.ub, na.rm = TRUE)         }         rng <- f.2 - f.1         xlim <- c(f.1 - rng * plot.multp.l, f.2 + rng * plot.multp.r)         xlim <- round(xlim, digits[[2]])     }     else {         if (length(xlim) != 2L)              stop(mstyle$stop("Argument 'xlim' must be of length 2."))     }     xlim <- sort(xlim)     textpos <- .chkddd(ddd$textpos, xlim)     if (length(textpos) != 2L)          stop(mstyle$stop("Argument 'textpos' must be of length 2."))     if (is.na(textpos[1]))          textpos[1] <- xlim[1]     if (is.na(textpos[2]))          textpos[2] <- xlim[2]     if (missing(ylim)) {         ylim <- c(0, max(rows, na.rm = TRUE) + top)     }     else {         if (length(ylim) == 1L) {             ylim <- c(ylim, max(rows, na.rm = TRUE) + top)         }         else {             ylim <- sort(ylim)         }     }     if (missing(fonts)) {         fonts <- rep(par("family"), 3L)     }     else {         if (length(fonts) == 1L)              fonts <- rep(fonts, 3L)         if (length(fonts) == 2L)              fonts <- c(fonts, fonts[1])     }     if (is.null(names(fonts)))          fonts <- setNames(c(1L, 1L, 1L), nm = fonts)     par(family = names(fonts)[1], font = fonts[1])     par.mar <- par("mar")     par.mar.adj <- par.mar - c(0, 3, 1, 1)     par.mar.adj[par.mar.adj < 0] <- 0     par(mar = par.mar.adj)     on.exit(par(mar = par.mar), add = TRUE)     lplot(NA, NA, xlim = xlim, ylim = ylim, xlab = "", ylab = "", yaxt = "n", xaxt = "n", xaxs = "i", yaxs = "i", bty = "n", ...)     if (shade.type == "character") {         if (shade == "zebra" || shade == "zebra1")              tmp <- rep_len(c(TRUE, FALSE), k)         if (shade == "zebra2")              tmp <- rep_len(c(FALSE, TRUE), k)         if (shade == "all")              tmp <- rep_len(TRUE, k)         shade <- tmp     }     if (shade.type %in% c("character", "logical")) {         for (i in seq_len(k)) {             if (shade[i])                  rect(xlim[1], rows[i] - 0.5, xlim[2], rows[i] + 0.5, border = colshade, col = colshade)         }     }     if (shade.type == "numeric") {         for (i in seq_along(shade)) {             rect(xlim[1], shade[i] - 0.5, xlim[2], shade[i] + 0.5, border = colshade, col = colshade)         }     }     labline(h = ylim[2] - (top - 1), lty = lty[2], ...)     par.usr <- par("usr")     if (is.numeric(refline))          lsegments(refline, par.usr[3], refline, ylim[2] - (top - 1), lty = "dotted", ...)     height <- par.usr[4] - par.usr[3]     if (is.null(cex)) {         lheight <- strheight("O")         cex.adj <- ifelse(k * lheight > height * 0.8, height/(1.25 * k * lheight), 1)     }     if (is.null(cex)) {         cex <- par("cex") * cex.adj     }     else {         if (is.null(cex.lab))              cex.lab <- par("cex") * cex         if (is.null(cex.axis))              cex.axis <- cex     }     if (is.null(cex.lab))          cex.lab <- par("cex") * cex.adj     if (is.null(cex.axis))          cex.axis <- par("cex") * cex.adj     laxis(side = 1, at = at, labels = at.lab, cex.axis = cex.axis, ...)     if (missing(xlab))          xlab <- .setlab(measure, transf.char, atransf.char, gentype = 1)     if (!is.element(length(xlab), 1:3))          stop(mstyle$stop("Argument 'xlab' argument must be of length 1, 2, or 3."))     if (length(xlab) == 1L)          lmtext(xlab, side = 1, at = min(at) + (max(at) - min(at))/2, line = par("mgp")[1] - 0.5, cex = cex.lab, font = xlabfont[1], ...)     if (length(xlab) == 2L) {         lmtext(xlab[1], side = 1, at = min(at), line = par("mgp")[1] - 0.5, cex = cex.lab, adj = xlabadj[1], font = xlabfont[1], ...)         lmtext(xlab[2], side = 1, at = max(at), line = par("mgp")[1] - 0.5, cex = cex.lab, adj = xlabadj[2], font = xlabfont[1], ...)     }     if (length(xlab) == 3L) {         lmtext(xlab[1], side = 1, at = min(at), line = par("mgp")[1] - 0.5, cex = cex.lab, adj = xlabadj[1], font = xlabfont[1], ...)         lmtext(xlab[2], side = 1, at = min(at) + (max(at) - min(at))/2, line = par("mgp")[1] - 0.5, cex = cex.lab, font = xlabfont[2], ...)         lmtext(xlab[3], side = 1, at = max(at), line = par("mgp")[1] - 0.5, cex = cex.lab, adj = xlabadj[2], font = xlabfont[1], ...)     }     ciendheight <- height/150 * cex * efac[1]     arrowwidth <- 1.4/100 * cex * (xlim[2] - xlim[1])     arrowheight <- height/150 * cex * efac[2]     for (i in seq_len(k)) {         if (is.na(yi[i]) || is.na(ci.lb[i]) || is.na(ci.ub[i]))              next         if (ci.lb[i] >= alim[2]) {             lpolygon(x = c(alim[2], alim[2] - arrowwidth, alim[2] - arrowwidth, alim[2]), y = c(rows[i], rows[i] + arrowheight, rows[i] - arrowheight, rows[i]), col = col[i], border = col[i], ...)             next         }         if (ci.ub[i] <= alim[1]) {             lpolygon(x = c(alim[1], alim[1] + arrowwidth, alim[1] + arrowwidth, alim[1]), y = c(rows[i], rows[i] + arrowheight, rows[i] - arrowheight, rows[i]), col = col[i], border = col[i], ...)             next         }         lsegments(max(ci.lb[i], alim[1]), rows[i], min(ci.ub[i], alim[2]), rows[i], lty = lty[1], col = col[i], ...)         if (ci.lb[i] >= alim[1]) {             lsegments(ci.lb[i], rows[i] - ciendheight, ci.lb[i], rows[i] + ciendheight, col = col[i], ...)         }         else {             lpolygon(x = c(alim[1], alim[1] + arrowwidth, alim[1] + arrowwidth, alim[1]), y = c(rows[i], rows[i] + arrowheight, rows[i] - arrowheight, rows[i]), col = col[i], border = col[i], ...)         }         if (ci.ub[i] <= alim[2]) {             lsegments(ci.ub[i], rows[i] - ciendheight, ci.ub[i], rows[i] + ciendheight, col = col[i], ...)         }         else {             lpolygon(x = c(alim[2], alim[2] - arrowwidth, alim[2] - arrowwidth, alim[2]), y = c(rows[i], rows[i] + arrowheight, rows[i] - arrowheight, rows[i]), col = col[i], border = col[i], ...)         }     }     ltext(textpos[1], rows + rowadj[1], slab, pos = 4, cex = cex, col = col, ...)     if (!is.null(ilab)) {         if (is.null(ilab.xpos)) {             dist <- min(ci.lb, na.rm = TRUE) - xlim[1]             if (ncol.ilab == 1L)                  ilab.xpos <- xlim[1] + dist * 0.75             if (ncol.ilab == 2L)                  ilab.xpos <- xlim[1] + dist * c(0.65, 0.85)             if (ncol.ilab == 3L)                  ilab.xpos <- xlim[1] + dist * c(0.6, 0.75, 0.9)             if (ncol.ilab >= 4L)                  ilab.xpos <- seq(xlim[1] + dist * 0.5, xlim[1] + dist * 0.9, length.out = ncol.ilab)         }         if (length(ilab.xpos) != ncol.ilab)              stop(mstyle$stop(paste0("Number of 'ilab' columns (", ncol.ilab, ") does not match the length of the 'ilab.xpos' argument (", length(ilab.xpos), ").")))         if (!is.null(ilab.pos) && length(ilab.pos) == 1L)              ilab.pos <- rep(ilab.pos, ncol.ilab)         if (!is.null(ilab.lab) && length(ilab.lab) != ncol.ilab)              stop(mstyle$stop(paste0("Number of 'ilab' columns (", ncol.ilab, ") does not match the length of the 'ilab.lab' argument (", length(ilab.lab), ").")))         par(family = names(fonts)[3], font = fonts[3])         for (l in seq_len(ncol.ilab)) {             ltext(ilab.xpos[l], rows + rowadj[3], ilab[, l], pos = ilab.pos[l], cex = cex, ...)             if (!is.null(ilab.lab))                  ltext(ilab.xpos[l], ylim[2] - (top - 1) + 1 + rowadj[3], ilab.lab[l], pos = ilab.pos[l], font = 2, cex = cex, ...)         }         par(family = names(fonts)[1], font = fonts[1])     }     if (annotate) {         if (is.function(atransf)) {             if (is.null(targs)) {                 annotext <- cbind(sapply(yi, atransf), sapply(ci.lb, atransf), sapply(ci.ub, atransf))             }             else {                 annotext <- cbind(sapply(yi, atransf, targs), sapply(ci.lb, atransf, targs), sapply(ci.ub, atransf, targs))             }             tmp <- .psort(annotext[, 2:3])             annotext[, 2:3] <- tmp         }         else {             annotext <- cbind(yi, ci.lb, ci.ub)         }         if (showweights) {             annotext <- cbind(weights, annotext)             annotext <- fmtx(annotext, c(digits[[3]], digits[[1]], digits[[1]], digits[[1]]))         }         else {             annotext <- fmtx(annotext, digits[[1]])         }         if (missing(width)) {             width <- apply(annotext, 2, function(x) max(nchar(x)))         }         else {             width <- .expand1(width, ncol(annotext))             if (length(width) != ncol(annotext))                  stop(mstyle$stop(paste0("Length of the 'width' argument (", length(width), ") does not match the number of annotation columns (", ncol(annotext), ").")))         }         for (j in seq_len(ncol(annotext))) {             annotext[, j] <- formatC(annotext[, j], width = width[j])         }         if (showweights) {             annotext <- cbind(annotext[, 1], paste0("%", paste0(rep(substr(annosym[1], 1, 1), 3), collapse = "")), annotext[, 2], annosym[1], annotext[, 3], annosym[2], annotext[, 4], annosym[3])         }         else {             annotext <- cbind(annotext[, 1], annosym[1], annotext[, 2], annosym[2], annotext[, 3], annosym[3])         }         annotext <- apply(annotext, 1, paste, collapse = "")         annotext[grepl("NA", annotext, fixed = TRUE)] <- ""         annotext <- gsub("-", annosym[4], annotext, fixed = TRUE)         annotext <- gsub(" ", annosym[5], annotext, fixed = TRUE)         par(family = names(fonts)[2], font = fonts[2])         ltext(textpos[2], rows + rowadj[2], labels = annotext, pos = 2, cex = cex, col = col, ...)         par(family = names(fonts)[1], font = fonts[1])     }     else {         width <- NULL     }     for (i in seq_len(k)) {         if (is.na(yi[i]))              next         if (yi[i] >= alim[1] && yi[i] <= alim[2])              lpoints(x = yi[i], y = rows[i], pch = pch[i], cex = cex * psize[i], col = col[i], ...)     }     ltext(textpos[1], ylim[2] - (top - 1) + 1 + rowadj[1], header.left, pos = 4, font = 2, cex = cex, ...)     ltext(textpos[2], ylim[2] - (top - 1) + 1 + rowadj[2], header.right, pos = 2, font = 2, cex = cex, ...)     res <- list(xlim = par("usr")[1:2], alim = alim, at = at, ylim = ylim, rows = rows, cex = cex, cex.lab = cex.lab, cex.axis = cex.axis, ilab.xpos = ilab.xpos, ilab.pos = ilab.pos, textpos = textpos)     sav <- c(res, list(level = level, annotate = annotate, digits = digits[[1]], width = width, transf = transf, atransf = atransf, targs = targs, alim = alim, olim = olim, rowadj = rowadj, fonts = fonts[1:2], annosym = annosym))     try(assign("forest", sav, envir = .metafor), silent = TRUE)     invisible(res) })(x = NULL, ci.lb = NULL, ci.ub = NULL, sei = NULL, slab = c("Ames, 2001", "Benton, 2002", "Cruz, 2003", "Dover, 2004", "Elia, 2005"), ilab = structure(c("4", "8", "10", "15", "18", "96", "92", "90", "85", "82"), dim = c(5L, 2L), dimnames = list(NULL, c("Events", "Non-events"))), ilab.xpos = c(-0.682103174603174, -0.362738095238095), textpos = c(-2.05873015873016, 1.58214285714286), xlim = c(-2.23873015873016, 1.76214285714286), alim = c(0, 1), at = c(0, 0.2, 0.4, 0.6, 0.8, 1), refline = NA, xlab = "Proportion",      cex = 1.08, cex.lab = 1.08, cex.axis = 1.08, header = FALSE, rows = 5:1, ylim = c(-5, 8), annotate = FALSE, xaxt = "n", col = "black", colshade = "#eeeeee", shade = "zebra", lty = c("solid", "blank", "blank"), pch = 15, lwd = 1.35, efac = 0, digits = 3L, psize = c(1.5, 1.11832919797895, 0.962718637119288, 0.648550131541075, 0.5))`: Length of the 'slab' argument (5) does not correspond to the number of outcomes (0).
Backtrace:
    ▆
 1. └─RCMetaR::rcmetar.draw.forest.plot(bundle, png_path) at test-forest-metafor-renderer.R:1402:5
 2.   └─RCMetaR:::rcmetar.draw.metafor.forest(plot.data, outpath) at RCMetaR/R/rcmetar-core.R:518:9
 3.     └─RCMetaR (local) renderer(bundle, outpath) at RCMetaR/R/forest_metafor.R:905:9
 4.       └─RCMetaR:::rcmetar.render.plot_file(...) at RCMetaR/R/forest_style_default.R:233:5
 5.         └─RCMetaR:::rcmetar.render.plot_svg(svg.path, size, draw) at RCMetaR/R/plot_devices.R:289:5
 6.           └─RCMetaR (local) draw() at RCMetaR/R/plot_devices.R:198:5
 7.             ├─base::do.call(...) at RCMetaR/R/forest_style_default.R:290:9
 8.             └─metafor (local) `<fn>`(...)

Failure ('test-forest-metafor-renderer.R:1554:3'): diagnostic Default Forest Style builds and renders count columns on transformed axes
Expected `rcmetar.metafor.atransf(bundle)` to be identical to `invlogit`.
Differences:
`actual` is NULL
`expected` is a function


Error ('test-forest-metafor-renderer.R:1570:3'): diagnostic Default Forest Style builds and renders count columns on transformed axes
Error in `exp(x)`: non-numeric argument to mathematical function
Backtrace:
     ▆
  1. └─RCMetaR::rcmetar.draw.forest.plot(bundle, png_path) at test-forest-metafor-renderer.R:1570:3
  2.   └─RCMetaR:::rcmetar.draw.metafor.forest(plot.data, outpath) at RCMetaR/R/rcmetar-core.R:518:9
  3.     └─RCMetaR (local) renderer(bundle, outpath) at RCMetaR/R/forest_metafor.R:905:9
  4.       └─RCMetaR:::rcmetar.render.plot_file(...) at RCMetaR/R/forest_style_default.R:233:5
  5.         └─RCMetaR:::rcmetar.render.plot_svg(svg.path, size, draw) at RCMetaR/R/plot_devices.R:289:5
  6.           └─RCMetaR (local) draw() at RCMetaR/R/plot_devices.R:198:5
  7.             └─RCMetaR:::rcmetar.forest.axis.effect(bundle, bundle$effect) at RCMetaR/R/forest_style_default.R:284:9
  8.               └─RCMetaR:::rcmetar.forest.axis.values(bundle, effect[[field]]) at RCMetaR/R/forest_axis.R:23:9
  9.                 └─rcmetar.bundle.transform(bundle)$display.scale(values, ni = bundle$sample_sizes) at RCMetaR/R/forest_axis.R:18:5
 10.                   └─RCMetaR:::invlogit(x) at RCMetaR/R/diagnostic_methods.R:113:13

Error ('test-forest-metafor-renderer.R:1603:5'): diagnostic multi-metric workflows save independent metafor forest plots
Error in `exp(x)`: non-numeric argument to mathematical function
Backtrace:
     ▆
  1. └─RCMetaR (local) run_metrics(c("Sens", "Spec", "NLR", "PLR")) at test-forest-metafor-renderer.R:1645:3
  2.   └─RCMetaR::rcmetar.run.diagnostic.analyses(...) at test-forest-metafor-renderer.R:1603:5
  3.     └─RCMetaR:::multiple.diagnostic(methods, params.list, diagnostic.data) at RCMetaR/R/rcmetar-core.R:688:5
  4.       └─RCMetaR:::rcmetar.diagnostic.fit(...) at RCMetaR/R/diagnostic_methods.R:247:13
  5.         └─RCMetaR:::.rcmetar.call.method(method, prepared.data, params) at RCMetaR/R/diagnostic_methods.R:155:5
  6.           └─RCMetaR:::diagnostic.random(om.data, params) at RCMetaR/R/rcmetar-core.R:826:5
  7.             └─RCMetaR::rcmetar.draw.forest.plot(plot.data, forest.path) at RCMetaR/R/diagnostic_methods.R:628:13
  8.               └─RCMetaR:::rcmetar.draw.metafor.forest(plot.data, outpath) at RCMetaR/R/rcmetar-core.R:518:9
  9.                 └─RCMetaR (local) renderer(bundle, outpath) at RCMetaR/R/forest_metafor.R:905:9
 10.                   └─RCMetaR:::rcmetar.render.plot_file(...) at RCMetaR/R/forest_style_default.R:233:5
 11.                     └─RCMetaR:::rcmetar.render.plot_svg(svg.path, size, draw) at RCMetaR/R/plot_devices.R:289:5
 12.                       └─RCMetaR (local) draw() at RCMetaR/R/plot_devices.R:198:5
 13.                         └─RCMetaR:::rcmetar.forest.axis.effect(bundle, bundle$effect) at RCMetaR/R/forest_style_default.R:284:9
 14.                           └─RCMetaR:::rcmetar.forest.axis.values(bundle, effect[[field]]) at RCMetaR/R/forest_axis.R:23:9
 15.                             └─rcmetar.bundle.transform(bundle)$display.scale(values, ni = bundle$sample_sizes) at RCMetaR/R/forest_axis.R:18:5
 16.                               └─RCMetaR:::invlogit(x) at RCMetaR/R/diagnostic_methods.R:113:13

[ FAIL 6 | WARN 0 | SKIP 0 | PASS 826 ]
Error:
! Test failures.
Execution halted

```

## axis-rerun-baseline

Command: `uv run python scripts/verify_rcms.py project-axis-proportions`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-axis-proportions"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T115725Z-2aeea289-project-axis-proportions
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 775, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1837, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 162, in run
    assert setup.current_param_vals.get('fp_axis_scale') == other, ('axis lost on analysis rerun', measure, style)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ('axis lost on analysis rerun', 'PLO', 'default')
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 775, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1837, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 162, in run
    assert setup.current_param_vals.get('fp_axis_scale') == other, ('axis lost on analysis rerun', measure, style)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ('axis lost on analysis rerun', 'PLO', 'default')


```

## axis-rerun-others

Command: `uv run python scripts/verify_rcms.py project-axis-others`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-axis-others"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T115816Z-c2e5630a-project-axis-others
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 775, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1837, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 163, in run
    click(app, setup.btn_ok)
               ^^^^^^^^^^^^
AttributeError: 'AnalysisSetupDialog' object has no attribute 'btn_ok'
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 775, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1837, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 163, in run
    click(app, setup.btn_ok)
               ^^^^^^^^^^^^
AttributeError: 'AnalysisSetupDialog' object has no attribute 'btn_ok'


```

## axis-rerun-proportions

Command: `uv run python scripts/verify_rcms.py project-axis-proportions`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-axis-proportions"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T115814Z-593586a1-project-axis-proportions
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 775, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1837, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 163, in run
    click(app, setup.btn_ok)
               ^^^^^^^^^^^^
AttributeError: 'AnalysisSetupDialog' object has no attribute 'btn_ok'
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 775, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1837, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 163, in run
    click(app, setup.btn_ok)
               ^^^^^^^^^^^^
AttributeError: 'AnalysisSetupDialog' object has no attribute 'btn_ok'


```

## axis-rerun-report-others

Command: `uv run python scripts/verify_rcms.py project-axis-others`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-axis-others"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T115913Z-8bda0c8b-project-axis-others
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
RCMS project-axis-others timed out after 600 seconds: /home/ali/Documents/Code/rc-metastudio/.venv/bin/python -X faulthandler /home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py project-axis-others /home/ali/Documents/Code/rc-metastudio/build/verification/rcms/desktop-7kufiteo


```

## axis-rerun-report-proportions

Command: `uv run python scripts/verify_rcms.py project-axis-proportions`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-axis-proportions"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T115912Z-0d4cfe45-project-axis-proportions
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
RCMS project-axis-proportions timed out after 600 seconds: /home/ali/Documents/Code/rc-metastudio/.venv/bin/python -X faulthandler /home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py project-axis-proportions /home/ali/Documents/Code/rc-metastudio/build/verification/rcms/desktop-39dzm186


```

## baseline-tiny-sd-focused

Command: `uv run python scripts/verify_rcms.py calculator-mode-continuous-metrics --native`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-mode-continuous-metrics", "--native"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110013Z-6a0c0649-calculator-mode-continuous-metrics
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 83, in ready
    drive(dialog)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1115, in drive
    assert actual == expected, ("raw precision lost", mode, value, actual)
           ^^^^^^^^^^^^^^^^^^
AssertionError: ('raw precision lost', 'continuous-metrics', '0.00001', 0.0)
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 769, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1776, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1180, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 97, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError(('raw precision lost', 'continuous-metrics', '0.00001', 0.0))]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 769, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1776, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1180, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 97, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError(('raw precision lost', 'continuous-metrics', '0.00001', 0.0))]


```

## baseline-tiny-sd

Command: `uv run python scripts/verify_rcms.py calculator-mode-continuous-metrics --native`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-mode-continuous-metrics", "--native"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T105938Z-0f4888f8-calculator-mode-continuous-metrics
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 83, in ready
    drive(dialog)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1115, in drive
    assert actual == expected, ("raw precision lost", mode, value, actual)
           ^^^^^^^^^^^^^^^^^^
AssertionError: ('raw precision lost', 'continuous-metrics', '0.00001', 22.0)
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 769, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1776, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1180, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 97, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError(('raw precision lost', 'continuous-metrics', '0.00001', 22.0))]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 769, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1776, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1180, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 97, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError(('raw precision lost', 'continuous-metrics', '0.00001', 22.0))]


```

## calculator-boundary-replay

Command: `uv run python -m pytest tests/python/fast/test_calculator_qt6.py -q`

```text
["uv", "run", "python", "-m", "pytest", "tests/python/fast/test_calculator_qt6.py", "-q"]
............................F                                            [100%]
=================================== FAILURES ===================================
________ test_continuous_calculator_grid_columns_keep_internal_overflow ________

qapp = <PyQt6.QtWidgets.QApplication object at 0x7263a3154670>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7263a0a408d0>

    def test_continuous_calculator_grid_columns_keep_internal_overflow(qapp, monkeypatch):
        from rc_metastudio import continuous_data_dialog
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "continuous_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_continuous_data",
            lambda data, alpha: {"succeeded": False, "comment": "stub"},
        )
    
        form = continuous_data_dialog.ContinuousDataDialog(
            FakeContinuousAnalysisUnit(),
            ["Group 1", "Group 2"],
            "Group 1-Group 2",
            "ROM",
            confidence_level=95.0,
        )
    
        form.resize(360, form.height())
        form.show()
        qapp.processEvents()
        table = _required(form.simple_table)
        header = _required(table.horizontalHeader())
        assert header.sectionResizeMode(0) == QHeaderView.ResizeMode.Interactive
        assert not header.stretchLastSection()
        assert (
            table.horizontalScrollBarPolicy() == QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
>       assert (
            sum(header.sectionSize(column) for column in range(table.columnCount()))
            > table.viewport().width()
        )
E       assert 342 > 375
E        +  where 342 = sum(<generator object test_continuous_calculator_grid_columns_keep_internal_overflow.<locals>.<genexpr> at 0x7263a0c5c4a0>)
E        +  and   375 = <built-in method width of QWidget object at 0x7263a0a2d3f0>()
E        +    where <built-in method width of QWidget object at 0x7263a0a2d3f0> = <PyQt6.QtWidgets.QWidget object at 0x7263a0a2d3f0>.width
E        +      where <PyQt6.QtWidgets.QWidget object at 0x7263a0a2d3f0> = <built-in method viewport of QTableWidget object at 0x7263a0a2eef0>()
E        +        where <built-in method viewport of QTableWidget object at 0x7263a0a2eef0> = <PyQt6.QtWidgets.QTableWidget object at 0x7263a0a2eef0>.viewport

tests/python/fast/test_calculator_qt6.py:1308: AssertionError
----------------------------- Captured stderr call -----------------------------
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
=========================== short test summary info ============================
FAILED tests/python/fast/test_calculator_qt6.py::test_continuous_calculator_grid_columns_keep_internal_overflow
1 failed, 28 passed in 1.18s

```

## calculator-existing-boundary-tests

Command: `uv run python -m pytest tests/python/fast/test_calculator_qt6.py -q`

```text
["uv", "run", "python", "-m", "pytest", "tests/python/fast/test_calculator_qt6.py", "-q"]
.............F..F...FF......FF                                           [100%]
=================================== FAILURES ===================================
__________ test_continuous_imputation_uses_r_keys_not_visible_headers __________

qapp = <PyQt6.QtWidgets.QApplication object at 0x7fc181d385e0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fc17f9c2d10>

    def test_continuous_imputation_uses_r_keys_not_visible_headers(qapp, monkeypatch):
        from rc_metastudio import continuous_data_dialog
    
        captured = []
    
        def fake_impute_continuous_data(params, alpha):
            captured.append(params.copy())
            return {"succeeded": False}
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_continuous_data",
            fake_impute_continuous_data,
        )
    
        form = continuous_data_dialog.ContinuousDataDialog.__new__(
            continuous_data_dialog.ContinuousDataDialog
        )
        form.simple_table = QTableWidget(2, 8)
        form.simple_table.setHorizontalHeaderLabels(
            ["N", "Mean", "SD", "SE", "Variance", "Lower", "Upper", "P-Value"]
        )
        form.current_groups = ["Group 1", "Group 2"]
        form.confidence_level = 95.0
        form.analysis_unit = object()
        from rc_metastudio.calculator_service import CalculatorService
    
        form.calculator = CalculatorService()
    
        form.simple_table.setItem(0, 0, QTableWidgetItem("10"))
        form.simple_table.setItem(0, 1, QTableWidgetItem("94"))
        form.simple_table.setItem(0, 4, QTableWidgetItem("2.5"))
        form.simple_table.setItem(0, 5, QTableWidgetItem("90"))
        form.simple_table.setItem(0, 6, QTableWidgetItem("98"))
    
        form.impute_data()
    
>       assert captured[0] == {
            "n": 10.0,
            "mean": 94.0,
            "var": 2.5,
            "low": 90.0,
            "high": 98.0,
        }
E       AssertionError: assert {} == {'n': 10.0, '...w': 90.0, ...}
E         
E         Right contains 5 more items:
E         {'high': 98.0, 'low': 90.0, 'mean': 94.0, 'n': 10.0, 'var': 2.5}
E         Use -v to get more diff

tests/python/fast/test_calculator_qt6.py:484: AssertionError
_________ test_continuous_prepost_only_publishes_complete_differences __________

qapp = <PyQt6.QtWidgets.QApplication object at 0x7fc181d385e0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fc17f6c9050>

    def test_continuous_prepost_only_publishes_complete_differences(qapp, monkeypatch):
        from rc_metastudio import analysis_dataset, continuous_data_dialog, meta_globals
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda _confidence_level: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "continuous_convert_scale",
            lambda value, *_args, **_kwargs: value,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_continuous_data",
            lambda _data, _alpha: {"succeeded": False, "comment": "stub"},
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "back_calculate_continuous_data",
            lambda *_args, **_kwargs: {"FAIL": True},
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "continuous_effect_for_study",
            lambda *_args, **_kwargs: {"calc_scale": (-0.5, -1.0, 0.0)},
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "effect_triplet",
            lambda result, scale, metric=None: result[scale],
        )
    
        def values(n=None, mean=None, sd=None):
            return {
                "n": n,
                "mean": mean,
                "sd": sd,
                "se": None,
                "var": None,
                "low": None,
                "high": None,
                "pval": None,
            }
    
        def prepost(data, _correlation, _alpha):
            complete = all(
                data.get(field) is not None
                for field in ("n.A", "mean.A", "sd.A", "n.B", "mean.B", "sd.B")
            )
            if not complete:
                return {
                    "succeeded": True,
                    "output": values(),
                    "pre": values(),
                    "post": values(),
                }
            return {
                "succeeded": True,
                "output": values(60, -2, 29.7321),
                "pre": values(60, 94, 22),
                "post": values(60, 92, 20),
            }
    
        monkeypatch.setattr(
            calculator_service.r_bridge, "impute_pre_post_continuous_data", prepost
        )
        unit = analysis_dataset.AnalysisUnit(
            analysis_dataset.Outcome("Outcome", meta_globals.CONTINUOUS),
            raw_data=[[None, None, None], [60, 92, 20]],
            group_names=["Group 1", "Group 2"],
        )
        unit.set_effect_for_source(
            "entered", "SMD", "Group 1-Group 2", 0.0945, -0.1, 0.29
        )
        dialog = continuous_data_dialog.ContinuousDataDialog(
            unit,
            ["Group 1", "Group 2"],
            "Group 1-Group 2",
            "SMD",
            confidence_level=95.0,
        )
        for row, values_for_row in enumerate(((60, 94, 22), (60, 92, 20))):
            for column, value in enumerate(values_for_row):
                dialog._set_val(row, column, value, dialog.g1_pre_post_table)
    
        dialog.impute_pre_post_data(dialog.g1_pre_post_table, 0)
    
>       assert unit.get_raw_data_for_group("Group 1") == [60, -2, 29.7321]
E       assert [None, None, None] == [60, -2, 29.7321]
E         
E         At index 0 diff: None != 60
E         Use -v to get more diff

tests/python/fast/test_calculator_qt6.py:760: AssertionError
_ test_binary_calculator_table_layout_uses_real_headers_and_visible_total_row __

qapp = <PyQt6.QtWidgets.QApplication object at 0x7fc181d385e0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fc17f73c410>

    def test_binary_calculator_table_layout_uses_real_headers_and_visible_total_row(
        qapp, monkeypatch
    ):
        from rc_metastudio import binary_data_dialog
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "binary_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_binary_data",
            lambda data: {"FAIL": True},
        )
    
        form = binary_data_dialog.BinaryDataDialog(
            FakeAnalysisUnit(),
            ["Group 1", "Group 2"],
            "Group 1-Group 2",
            "OR",
            confidence_level=95.0,
        )
    
        table = _required(form.raw_data_table)
    
>       assert form.event_lbl_3.isHidden()
               ^^^^^^^^^^^^^^^^
E       AttributeError: 'BinaryDataDialog' object has no attribute 'event_lbl_3'

tests/python/fast/test_calculator_qt6.py:889: AttributeError
__________ test_calculator_effect_ci_fields_fit_valid_domain_samples ___________

qapp = <PyQt6.QtWidgets.QApplication object at 0x7fc181d385e0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fc17f44c5d0>

    def test_calculator_effect_ci_fields_fit_valid_domain_samples(qapp, monkeypatch):
        from rc_metastudio import binary_data_dialog
        from rc_metastudio import continuous_data_dialog
        from rc_metastudio import diagnostic_data_dialog
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "binary_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_binary_data",
            lambda data: {"FAIL": True},
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "continuous_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_continuous_data",
            lambda data, alpha: {"succeeded": False, "comment": "stub"},
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "diagnostic_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_diagnostic_data",
            lambda data: {"TP": None, "FP": None, "FN": None, "TN": None},
        )
    
        forms_and_representatives = [
            (
                binary_data_dialog.BinaryDataDialog(
                    FakeAnalysisUnit(),
                    ["Group 1", "Group 2"],
                    "Group 1-Group 2",
                    "OR",
                    confidence_level=95.0,
                ),
                "-0.8888",
            ),
            (
>               continuous_data_dialog.ContinuousDataDialog(
                    FakeContinuousAnalysisUnit(),
                    ["Group 1", "Group 2"],
                    "Group 1-Group 2",
                    "ROM",
                    confidence_level=95.0,
                ),
                "-0.8888",
            ),
            (
                diagnostic_data_dialog.DiagnosticDataDialog(
                    FakeDiagnosticAnalysisUnit(),
                    ["Group 1", "Group 2"],
                    "Group 1-Group 2",
                    confidence_level=95.0,
                ),
                "1.0000",
            ),
        ]

tests/python/fast/test_calculator_qt6.py:965: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <rc_metastudio.continuous_data_dialog.ContinuousDataDialog object at 0x7fc17f6bfe20>
analysis_unit = <test_calculator_qt6.FakeContinuousAnalysisUnit object at 0x7fc17f44c490>
current_groups = ['Group 1', 'Group 2'], group_comparison = 'Group 1-Group 2'
current_effect = 'ROM', confidence_level = 95.0, calculator = None
parent = None

    def __init__(
        self,
        analysis_unit,
        current_groups,
        group_comparison,
        current_effect,
        confidence_level=None,
        calculator: CalculatorService | None = None,
        parent=None,
    ):
        super(ContinuousDataDialog, self).__init__(parent)
        self.setupUi(self)
        self._configure_tables()
        self._configure_semantic_fields()
        self._configure_focus_revelation()
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self.setup_signals_and_slots()
    
        if confidence_level is None:
            QMessageBox.critical(
                self, "Insufficient Arguments", "Confidence interval must be specified"
            )
            raise ValueError("Confidence interval must be specified")
        self.confidence_level = confidence_level
        self.calculator = calculator or CalculatorService()
        self.confidence_multiplier = self.calculator.get_confidence_multiplier(
            self.confidence_level
        )
    
        self.analysis_unit = analysis_unit
        self.current_groups = current_groups
        self.current_effect = current_effect
        self.group_comparison = group_comparison
        self.metric_parameter = None
        self.entry_widgets = [
            self.simple_table,
            self.g1_pre_post_table,
            self.g2_pre_post_table,
            self.effect_text_box,
            self.lower_text_box,
            self.upper_text_box,
            self.correlation_pre_post,
        ]
        self.text_boxes = [
            self.lower_text_box,
            self.upper_text_box,
            self.effect_text_box,
            self.correlation_pre_post,
        ]
        self.ci_label.setText(
            f"{self.confidence_level:g}% confidence interval"
        )
        self._configure_readable_ci_label()
        self.current_item_data = {}
    
        groups_names = [str(group_name) for group_name in self.current_groups]
        self.simple_table.setVerticalHeaderLabels(groups_names)
    
        self.tables = [
            self.simple_table,
            self.g1_pre_post_table,
            self.g2_pre_post_table,
        ]
        self.group_one_label.setText(str(self.current_groups[0]))
        self.group_two_label.setText(str(self.current_groups[1]))
        for table, group in zip((self.g1_pre_post_table, self.g2_pre_post_table), self.current_groups):
            table.setAccessibleName(f"{group} pre/post summaries")
            table.setAccessibleDescription(f"Pre-treatment and post-treatment summary values for {group}.")
    
        self.setup_clear_button_palettes()  # Color for clear_button_pallette
        self.initialize_form()  # initialize cells to empty items
        self._field_history = calc_fncs.TransientEditHistory()
    
        self.update_raw_data()
        self._populate_effect_data()
        self.set_current_effect()
        self.impute_data()
        self.update_effect_from_raw_data()
        self.update_back_calculation_button()
    
>       if self.analysis_unit.outcome.sub_type not in {"reg_coef", "generic_effect"}:
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'FakeContinuousAnalysisUnit' object has no attribute 'outcome'

src/rc_metastudio/continuous_data_dialog.py:181: AttributeError
________ test_continuous_calculator_grid_columns_keep_internal_overflow ________

qapp = <PyQt6.QtWidgets.QApplication object at 0x7fc181d385e0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fc17f9b9750>

    def test_continuous_calculator_grid_columns_keep_internal_overflow(qapp, monkeypatch):
        from rc_metastudio import continuous_data_dialog
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "continuous_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_continuous_data",
            lambda data, alpha: {"succeeded": False, "comment": "stub"},
        )
    
>       form = continuous_data_dialog.ContinuousDataDialog(
            FakeContinuousAnalysisUnit(),
            ["Group 1", "Group 2"],
            "Group 1-Group 2",
            "ROM",
            confidence_level=95.0,
        )

tests/python/fast/test_calculator_qt6.py:1287: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <rc_metastudio.continuous_data_dialog.ContinuousDataDialog object at 0x7fc17f762b00>
analysis_unit = <test_calculator_qt6.FakeContinuousAnalysisUnit object at 0x7fc17f9b9690>
current_groups = ['Group 1', 'Group 2'], group_comparison = 'Group 1-Group 2'
current_effect = 'ROM', confidence_level = 95.0, calculator = None
parent = None

    def __init__(
        self,
        analysis_unit,
        current_groups,
        group_comparison,
        current_effect,
        confidence_level=None,
        calculator: CalculatorService | None = None,
        parent=None,
    ):
        super(ContinuousDataDialog, self).__init__(parent)
        self.setupUi(self)
        self._configure_tables()
        self._configure_semantic_fields()
        self._configure_focus_revelation()
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self.setup_signals_and_slots()
    
        if confidence_level is None:
            QMessageBox.critical(
                self, "Insufficient Arguments", "Confidence interval must be specified"
            )
            raise ValueError("Confidence interval must be specified")
        self.confidence_level = confidence_level
        self.calculator = calculator or CalculatorService()
        self.confidence_multiplier = self.calculator.get_confidence_multiplier(
            self.confidence_level
        )
    
        self.analysis_unit = analysis_unit
        self.current_groups = current_groups
        self.current_effect = current_effect
        self.group_comparison = group_comparison
        self.metric_parameter = None
        self.entry_widgets = [
            self.simple_table,
            self.g1_pre_post_table,
            self.g2_pre_post_table,
            self.effect_text_box,
            self.lower_text_box,
            self.upper_text_box,
            self.correlation_pre_post,
        ]
        self.text_boxes = [
            self.lower_text_box,
            self.upper_text_box,
            self.effect_text_box,
            self.correlation_pre_post,
        ]
        self.ci_label.setText(
            f"{self.confidence_level:g}% confidence interval"
        )
        self._configure_readable_ci_label()
        self.current_item_data = {}
    
        groups_names = [str(group_name) for group_name in self.current_groups]
        self.simple_table.setVerticalHeaderLabels(groups_names)
    
        self.tables = [
            self.simple_table,
            self.g1_pre_post_table,
            self.g2_pre_post_table,
        ]
        self.group_one_label.setText(str(self.current_groups[0]))
        self.group_two_label.setText(str(self.current_groups[1]))
        for table, group in zip((self.g1_pre_post_table, self.g2_pre_post_table), self.current_groups):
            table.setAccessibleName(f"{group} pre/post summaries")
            table.setAccessibleDescription(f"Pre-treatment and post-treatment summary values for {group}.")
    
        self.setup_clear_button_palettes()  # Color for clear_button_pallette
        self.initialize_form()  # initialize cells to empty items
        self._field_history = calc_fncs.TransientEditHistory()
    
        self.update_raw_data()
        self._populate_effect_data()
        self.set_current_effect()
        self.impute_data()
        self.update_effect_from_raw_data()
        self.update_back_calculation_button()
    
>       if self.analysis_unit.outcome.sub_type not in {"reg_coef", "generic_effect"}:
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'FakeContinuousAnalysisUnit' object has no attribute 'outcome'

src/rc_metastudio/continuous_data_dialog.py:181: AttributeError
_________ test_continuous_calculator_keeps_long_imputed_values_compact _________

qapp = <PyQt6.QtWidgets.QApplication object at 0x7fc181d385e0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fc17f7690d0>

    def test_continuous_calculator_keeps_long_imputed_values_compact(qapp, monkeypatch):
        from rc_metastudio import continuous_data_dialog
    
        long_imputed = {
            "n": 10,
            "mean": 92.89482413483651,
            "sd": 2.604729426373378,
            "se": 8.75360686626884e-310,
            "var": 3.4972319657703745e-249,
            "pval": 0.12345678912345678,
            "low": 91.11111111111111,
            "high": 94.99999999999999,
        }
    
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "get_confidence_multiplier_from_r",
            lambda conf: 1.96,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "continuous_convert_scale",
            lambda x, *args, **kwargs: x,
        )
        monkeypatch.setattr(
            calculator_service.r_bridge,
            "impute_continuous_data",
            lambda data, alpha: {"succeeded": True, "output": long_imputed},
        )
    
>       form = continuous_data_dialog.ContinuousDataDialog(
            FakeContinuousAnalysisUnit(),
            ["Group 1", "Group 2"],
            "Group 1-Group 2",
            "ROM",
            confidence_level=95.0,
        )

tests/python/fast/test_calculator_qt6.py:1341: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <rc_metastudio.continuous_data_dialog.ContinuousDataDialog object at 0x7fc17f7629e0>
analysis_unit = <test_calculator_qt6.FakeContinuousAnalysisUnit object at 0x7fc17f768890>
current_groups = ['Group 1', 'Group 2'], group_comparison = 'Group 1-Group 2'
current_effect = 'ROM', confidence_level = 95.0, calculator = None
parent = None

    def __init__(
        self,
        analysis_unit,
        current_groups,
        group_comparison,
        current_effect,
        confidence_level=None,
        calculator: CalculatorService | None = None,
        parent=None,
    ):
        super(ContinuousDataDialog, self).__init__(parent)
        self.setupUi(self)
        self._configure_tables()
        self._configure_semantic_fields()
        self._configure_focus_revelation()
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self.setup_signals_and_slots()
    
        if confidence_level is None:
            QMessageBox.critical(
                self, "Insufficient Arguments", "Confidence interval must be specified"
            )
            raise ValueError("Confidence interval must be specified")
        self.confidence_level = confidence_level
        self.calculator = calculator or CalculatorService()
        self.confidence_multiplier = self.calculator.get_confidence_multiplier(
            self.confidence_level
        )
    
        self.analysis_unit = analysis_unit
        self.current_groups = current_groups
        self.current_effect = current_effect
        self.group_comparison = group_comparison
        self.metric_parameter = None
        self.entry_widgets = [
            self.simple_table,
            self.g1_pre_post_table,
            self.g2_pre_post_table,
            self.effect_text_box,
            self.lower_text_box,
            self.upper_text_box,
            self.correlation_pre_post,
        ]
        self.text_boxes = [
            self.lower_text_box,
            self.upper_text_box,
            self.effect_text_box,
            self.correlation_pre_post,
        ]
        self.ci_label.setText(
            f"{self.confidence_level:g}% confidence interval"
        )
        self._configure_readable_ci_label()
        self.current_item_data = {}
    
        groups_names = [str(group_name) for group_name in self.current_groups]
        self.simple_table.setVerticalHeaderLabels(groups_names)
    
        self.tables = [
            self.simple_table,
            self.g1_pre_post_table,
            self.g2_pre_post_table,
        ]
        self.group_one_label.setText(str(self.current_groups[0]))
        self.group_two_label.setText(str(self.current_groups[1]))
        for table, group in zip((self.g1_pre_post_table, self.g2_pre_post_table), self.current_groups):
            table.setAccessibleName(f"{group} pre/post summaries")
            table.setAccessibleDescription(f"Pre-treatment and post-treatment summary values for {group}.")
    
        self.setup_clear_button_palettes()  # Color for clear_button_pallette
        self.initialize_form()  # initialize cells to empty items
        self._field_history = calc_fncs.TransientEditHistory()
    
        self.update_raw_data()
        self._populate_effect_data()
        self.set_current_effect()
        self.impute_data()
        self.update_effect_from_raw_data()
        self.update_back_calculation_button()
    
>       if self.analysis_unit.outcome.sub_type not in {"reg_coef", "generic_effect"}:
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'FakeContinuousAnalysisUnit' object has no attribute 'outcome'

src/rc_metastudio/continuous_data_dialog.py:181: AttributeError
=========================== short test summary info ============================
FAILED tests/python/fast/test_calculator_qt6.py::test_continuous_imputation_uses_r_keys_not_visible_headers
FAILED tests/python/fast/test_calculator_qt6.py::test_continuous_prepost_only_publishes_complete_differences
FAILED tests/python/fast/test_calculator_qt6.py::test_binary_calculator_table_layout_uses_real_headers_and_visible_total_row
FAILED tests/python/fast/test_calculator_qt6.py::test_calculator_effect_ci_fields_fit_valid_domain_samples
FAILED tests/python/fast/test_calculator_qt6.py::test_continuous_calculator_grid_columns_keep_internal_overflow
FAILED tests/python/fast/test_calculator_qt6.py::test_continuous_calculator_keeps_long_imputed_values_compact
6 failed, 24 passed in 1.17s

```

## calculator-native-all

Command: `bash -c for mode in continuous-metrics onearm-mean pre-post back-continuous entered-continuous binary-metrics diagnostic-metrics onearm-proportion entered-binary entered-diagnostic back-binary back-diagnostic; do uv run python scripts/verify_rcms.py "calculator-mode-$mode" --native || exit; done`

```text
["bash", "-c", "for mode in continuous-metrics onearm-mean pre-post back-continuous entered-continuous binary-metrics diagnostic-metrics onearm-proportion entered-binary entered-diagnostic back-binary back-diagnostic; do uv run python scripts/verify_rcms.py \"calculator-mode-$mode\" --native || exit; done"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110156Z-829d7b2a-calculator-mode-continuous-metrics
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110214Z-fa64e8bc-calculator-mode-onearm-mean
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110240Z-46be4972-calculator-mode-pre-post
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110301Z-80aba4ef-calculator-mode-back-continuous
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110320Z-66493949-calculator-mode-entered-continuous
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110336Z-8b35f8ff-calculator-mode-binary-metrics
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110358Z-46ece6a5-calculator-mode-diagnostic-metrics
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110432Z-a993ed9b-calculator-mode-onearm-proportion
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 84, in ready
    drive(dialog)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1102, in drive
    cell(table, 0, column, float(table.item(0, column).text()) + 1)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 806, in cell
    assert editor is not None, (mode, row, column)
           ^^^^^^^^^^^^^^^^^^
AssertionError: ('onearm-proportion', 0, 0)
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1786, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1186, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 98, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError(('onearm-proportion', 0, 0))]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1786, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1186, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 98, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError(('onearm-proportion', 0, 0))]


```

## changed-code-types

Command: `uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path . --extra-search-path src/rc_metastudio --extra-search-path src --extra-search-path scripts --extra-search-path tests/python/gui src/rc_metastudio tests/e2e/precision_inputs.py tests/e2e/display_labels.py tests/e2e/ratio_precision.py tests/e2e/round6_polish.py`

```text
["uv", "run", "ty", "check", "--extra-search-path", "build/qt6-verification/generated/rc_metastudio", "--extra-search-path", "build/qt6-verification/generated/rc_metastudio/forms", "--extra-search-path", ".", "--extra-search-path", "src/rc_metastudio", "--extra-search-path", "src", "--extra-search-path", "scripts", "--extra-search-path", "tests/python/gui", "src/rc_metastudio", "tests/e2e/precision_inputs.py", "tests/e2e/display_labels.py", "tests/e2e/ratio_precision.py", "tests/e2e/round6_polish.py"]
error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
  --> tests/e2e/round6_polish.py:90:34
   |
88 |                     if y >= first-5:
89 |                         continue
90 |                     size = float(re.search(r'font-size:\s*([\d.]+)px', node.attrib['style'])[1])
   |                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
91 |                     width = float(node.attrib.get('textLength', '0').removesuffix('px'))
92 |                     anchor = node.attrib.get('text-anchor')
   |
info: rule `not-subscriptable` was selected in the configuration file

Found 1 diagnostic

```

## closed-results-baseline

Command: `uv run python scripts/verify_rcms.py project-axis-proportions`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-axis-proportions"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T121435Z-aff660c3-project-axis-proportions
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 775, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1840, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 176, in run
    assert sip.isdeleted(rerun), "closed result keeps its SVG scene alive"
           ^^^^^^^^^^^^^^^^^^^^
AssertionError: closed result keeps its SVG scene alive
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 775, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1840, in run
    axes(app, window, Path(sys.argv[2]), record, scenario.removeprefix("project-axis-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/axis_conventions.py", line 176, in run
    assert sip.isdeleted(rerun), "closed result keeps its SVG scene alive"
           ^^^^^^^^^^^^^^^^^^^^
AssertionError: closed result keeps its SVG scene alive


```

## final-source-types

Command: `uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path . --extra-search-path src/rc_metastudio --extra-search-path src --extra-search-path scripts --extra-search-path tests/python/gui src/rc_metastudio tests/e2e/axis_conventions.py tests/e2e/display_labels.py tests/e2e/precision_inputs.py tests/e2e/ratio_precision.py tests/e2e/round6_polish.py`

```text
["uv", "run", "ty", "check", "--extra-search-path", "build/qt6-verification/generated/rc_metastudio", "--extra-search-path", "build/qt6-verification/generated/rc_metastudio/forms", "--extra-search-path", ".", "--extra-search-path", "src/rc_metastudio", "--extra-search-path", "src", "--extra-search-path", "scripts", "--extra-search-path", "tests/python/gui", "src/rc_metastudio", "tests/e2e/axis_conventions.py", "tests/e2e/display_labels.py", "tests/e2e/precision_inputs.py", "tests/e2e/ratio_precision.py", "tests/e2e/round6_polish.py"]
error[invalid-assignment]: Cannot assign to a subscript on an object of type `str`
   --> src/rc_metastudio/analysis_setup_dialog.py:382:17
    |
380 |             restored = copy.deepcopy(saved)
381 |             if axis_scale is not None:
382 |                 restored["parameters"]["fp_axis_scale"] = axis_scale
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
383 |             form = AnalysisSetupDialog(model, parent=owner, analysis_type=workflow,
384 |                 external_params=restored["parameters"], diagnostic_metrics=metrics,
    |
info: The full type of the subscripted object is `Unknown | str | dict[str, object] | list[Unknown] | bool`
info: `str` does not have a `__setitem__` method.
info: rule `invalid-assignment` was selected in the configuration file

error[invalid-assignment]: Invalid subscript assignment with key of type `Literal["fp_axis_scale"]` and value of type `Unknown & ~None` on object of type `list[Unknown]`
   --> src/rc_metastudio/analysis_setup_dialog.py:382:17
    |
380 |             restored = copy.deepcopy(saved)
381 |             if axis_scale is not None:
382 |                 restored["parameters"]["fp_axis_scale"] = axis_scale
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
383 |             form = AnalysisSetupDialog(model, parent=owner, analysis_type=workflow,
384 |                 external_params=restored["parameters"], diagnostic_metrics=metrics,
    |
info: The full type of the subscripted object is `Unknown | str | dict[str, object] | list[Unknown] | bool`
info: rule `invalid-assignment` was selected in the configuration file

error[invalid-assignment]: Cannot assign to a subscript on an object of type `bool`
   --> src/rc_metastudio/analysis_setup_dialog.py:382:17
    |
380 |             restored = copy.deepcopy(saved)
381 |             if axis_scale is not None:
382 |                 restored["parameters"]["fp_axis_scale"] = axis_scale
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
383 |             form = AnalysisSetupDialog(model, parent=owner, analysis_type=workflow,
384 |                 external_params=restored["parameters"], diagnostic_metrics=metrics,
    |
info: The full type of the subscripted object is `Unknown | str | dict[str, object] | list[Unknown] | bool`
info: `bool` does not have a `__setitem__` method.
info: rule `invalid-assignment` was selected in the configuration file

Found 3 diagnostics

```

## full-final

Command: `uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh`

```text
["uv", "run", "python", ".agents/skills/verify-rcms/scripts/verify_all.py", "--full", "--fresh"]
Complete-run evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T121950Z-69157af3-complete
Running /home/ali/Documents/Code/rc-metastudio/.venv/bin/python scripts/verify.py r-stack --rscript /home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript
Failed; inspect /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T121950Z-69157af3-complete/00.log

```

## funnel-se-and-label-replay

Command: `bash -c for scenario in plot-workflow-funnel plot-workflow-contour plot-workflow-trimfill project-round6-polish; do uv run python scripts/verify_rcms.py "$scenario" || exit; done`

```text
["bash", "-c", "for scenario in plot-workflow-funnel plot-workflow-contour plot-workflow-trimfill project-round6-polish; do uv run python scripts/verify_rcms.py \"$scenario\" || exit; done"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T122957Z-0bae0679-plot-workflow-funnel
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
R callback write-console: Error in .small.study.metric.label(metric) : 
  argument "params" is missing, with no default
  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
UNEXPECTED DIALOG: Sorry, an unexpected error occurred. RC MetaStudio is still running, but the action could not be completed.

Details: Error in .small.study.metric.label(metric) : 
  argument "params" is missing, with no default


A diagnostic trace was written to:
/home/ali/Documents/Code/rc-metastudio/build/verification/rcms/desktop-z9g042su/rc-metastudio-error.log
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 785, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1881, in run
    plots(app, window, scenario.removeprefix("plot-workflow-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 368, in plots
    view = matrix(app, window, producer, record, keep_results=True)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 477, in run
    assert not callback_errors, callback_errors
           ^^^^^^^^^^^^^^^^^^^
AssertionError: [AssertionError('Error in .small.study.metric.label(metric) : \n  argument "params" is missing, with no default\n')]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 785, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1881, in run
    plots(app, window, scenario.removeprefix("plot-workflow-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 368, in plots
    view = matrix(app, window, producer, record, keep_results=True)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 477, in run
    assert not callback_errors, callback_errors
           ^^^^^^^^^^^^^^^^^^^
AssertionError: [AssertionError('Error in .small.study.metric.label(metric) : \n  argument "params" is missing, with no default\n')]


```

## funnel-se-axis-baseline

Command: `uv run python scripts/verify_rcms.py plot-workflow-funnel`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "plot-workflow-funnel"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T122716Z-9d41f42d-plot-workflow-funnel
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 775, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1881, in run
    plots(app, window, scenario.removeprefix("plot-workflow-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 368, in plots
    view = matrix(app, window, producer, record, keep_results=True)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 477, in run
    assert not callback_errors, callback_errors
           ^^^^^^^^^^^^^^^^^^^
AssertionError: [AssertionError('Contour levels must be numbers between 0 and 100, separated by commas (for example, 90, 95, 99).')]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 775, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1881, in run
    plots(app, window, scenario.removeprefix("plot-workflow-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 368, in plots
    view = matrix(app, window, producer, record, keep_results=True)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 477, in run
    assert not callback_errors, callback_errors
           ^^^^^^^^^^^^^^^^^^^
AssertionError: [AssertionError('Contour levels must be numbers between 0 and 100, separated by commas (for example, 90, 95, 99).')]


```

## golden-axis-capture

Command: `uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-round6-axis`

```text
["uv", "run", "python", "scripts/verify_golden_compatibility.py", "--output-root", "build/qt6-verification/golden-compatibility-round6-axis"]
{
  "baseline": "tests/analysis_regression/baseline/observed-golden-baseline.zip",
  "capture_passed": true,
  "case_count": 11,
  "comparison": {
    "passed": false,
    "rows": [
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.calculation_scale.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.calculation_scale.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.calculation_scale.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.calculation_scale.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.heterogeneity_df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.heterogeneity_p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.tau_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.de_vries matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.giamarellou matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.gonzalez matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.hansen matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.hollender matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.klastersky matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.maller matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.marik matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.mauracher matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.muijsken matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.nordstrom matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.prins matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.rozdzinski matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.sturm matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.ter_braak matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.tulkens matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.van_der_auwera matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.vanhaeverbeek matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.vigano matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section Summary matched.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section Weights matched.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.heterogeneity_df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.heterogeneity_p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.tau_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.carroll matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.donat matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.grant matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.peck matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.stewart matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.young matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "continuous.rcms",
        "detail": "Text section Summary changed.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Weights matched.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.calculation_scale.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.calculation_scale.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.calculation_scale.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.calculation_scale.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.heterogeneity_df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.heterogeneity_p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.study_count matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.tau_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Text section Odds Ratio Summary matched.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Text section References matched.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "lymph.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Artifact Odds Ratio Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.gonzalez.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.gonzalez.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.gonzalez.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.gonzalez.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section Cumulative Summary matched.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Cumulative Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section Leave-one-out Summary matched.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Leave-one-out Forest plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.carroll.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.carroll.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.carroll.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.carroll.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "continuous.rcms",
        "detail": "Text section Cumulative Summary changed.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Cumulative Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "continuous.rcms",
        "detail": "Text section Leave-one-out Summary changed.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Leave-one-out Forest plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.coefficient matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.coefficient matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.omnibus.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.de_vries matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.giamarellou matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.gonzalez matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.hansen matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.hollender matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.klastersky matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.maller matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.marik matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.mauracher matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.muijsken matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.nordstrom matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.prins matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.rozdzinski matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.sturm matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.ter_braak matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.tulkens matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.van_der_auwera matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.vanhaeverbeek matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.vigano matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Text section Summary changed.",
        "exception": "PR #349 intentionally improves meta-regression summary and reference text.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section Weights matched.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Regression Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.coefficient matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.coefficient matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.omnibus.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.carroll matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.donat matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.grant matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.peck matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.stewart matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.young matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Text section Summary changed.",
        "exception": "PR #349 intentionally improves meta-regression summary and reference text.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Weights matched.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Regression Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.overall.df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.overall.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.overall.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_early.df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_early.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_early.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_early.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_late.df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_late.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_late.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_late.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.studies matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.z_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.studies matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.z_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.studies matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.z_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section Subgroup Summary matched.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Subgroup Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "continuous.rcms",
        "detail": "Text section Subgroup Summary changed.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Subgroups Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      }
    ]
  },
  "comparison_count": 474,
  "numeric_contract": {
    "metric_count": 415,
    "path": "tests/analysis_regression/baseline/numeric-contract.json",
    "sha256": "dd309a37dc5d86290497d24b747fca478745b5c4b0cf40b9920b95e828fc594f"
  },
  "passed": false,
  "rpy2_identities": {
    "rpy2": "3.6.7",
    "rpy2-rinterface": "3.6.6",
    "rpy2-robjects": "3.6.5"
  }
}

```

## golden-before-refresh

Command: `uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-round6`

```text
["uv", "run", "python", "scripts/verify_golden_compatibility.py", "--output-root", "build/qt6-verification/golden-round6"]
Golden compatibility verification failed: Golden output must use a dedicated golden-compatibility directory

```

## golden-presentation-capture

Command: `uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-round6`

```text
["uv", "run", "python", "scripts/verify_golden_compatibility.py", "--output-root", "build/qt6-verification/golden-compatibility-round6"]
{
  "baseline": "tests/analysis_regression/baseline/observed-golden-baseline.zip",
  "capture_passed": true,
  "case_count": 11,
  "comparison": {
    "passed": false,
    "rows": [
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.calculation_scale.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.calculation_scale.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.calculation_scale.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.calculation_scale.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.heterogeneity_df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.heterogeneity_p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.tau_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.de_vries matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.giamarellou matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.gonzalez matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.hansen matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.hollender matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.klastersky matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.maller matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.marik matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.mauracher matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.muijsken matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.nordstrom matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.prins matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.rozdzinski matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.sturm matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.ter_braak matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.tulkens matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.van_der_auwera matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.vanhaeverbeek matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.vigano matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section Summary matched.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section Weights matched.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.heterogeneity_df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.heterogeneity_p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.tau_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.carroll matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.donat matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.grant matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.peck matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.stewart matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.young matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Summary matched.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Weights matched.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.calculation_scale.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.calculation_scale.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.calculation_scale.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.calculation_scale.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.heterogeneity_df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.heterogeneity_p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.study_count matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.tau_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Odds Ratio Summary.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Text section Odds Ratio Summary matched.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Text section References matched.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "lymph.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Artifact Odds Ratio Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.gonzalez.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.gonzalez.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.gonzalez.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.gonzalez.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_de_vries.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_giamarellou.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hansen.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_hollender.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_klastersky.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_maller.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_marik.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_mauracher.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_muijsken.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_nordstrom.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_prins.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_rozdzinski.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_sturm.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_ter_braak.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_tulkens.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_van_der_auwera.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vanhaeverbeek.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Cumulative Summary.model.through_vigano.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "amino.rcms",
        "detail": "Text section Cumulative Summary changed.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Cumulative Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.overall.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_de_vries.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_giamarellou.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_gonzalez.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hansen.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_hollender.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_klastersky.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_maller.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_marik.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_mauracher.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_muijsken.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_nordstrom.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_prins.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_rozdzinski.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_sturm.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_ter_braak.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_tulkens.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_van_der_auwera.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vanhaeverbeek.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Leave-one-out Summary.model.without_vigano.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "amino.rcms",
        "detail": "Text section Leave-one-out Summary changed.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Leave-one-out Forest plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.carroll.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.carroll.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.carroll.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.carroll.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_donat.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_grant.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_peck.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_stewart.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Cumulative Summary.model.through_young.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Cumulative Summary matched.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Cumulative Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.overall.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_carroll.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_donat.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_grant.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_peck.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_stewart.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Leave-one-out Summary.model.without_young.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Leave-one-out Summary matched.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Leave-one-out Forest plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.coefficient matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.golden_year.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.coefficient matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.model.intercept.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Summary.omnibus.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.de_vries matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.giamarellou matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.gonzalez matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.hansen matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.hollender matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.klastersky matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.maller matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.marik matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.mauracher matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.muijsken matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.nordstrom matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.prins matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.rozdzinski matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.sturm matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.ter_braak matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.tulkens matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.van_der_auwera matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.vanhaeverbeek matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Weights.weight.vigano matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Text section Summary changed.",
        "exception": "PR #349 intentionally improves meta-regression summary and reference text.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section Weights matched.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Regression Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.coefficient matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.golden_year.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.coefficient matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.model.intercept.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Summary.omnibus.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.carroll matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.donat matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.grant matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.peck matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.stewart matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Weights.weight.young matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Text section Summary changed.",
        "exception": "PR #349 intentionally improves meta-regression summary and reference text.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Weights matched.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Regression Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.overall.df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.overall.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.overall.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_early.df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_early.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_early.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_early.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_late.df matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_late.i_squared matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_late.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.heterogeneity.subgroup_late.q matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.studies matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.overall.z_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.studies matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.z_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.studies matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.z_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Text section References matched.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "amino.rcms",
        "detail": "Text section Subgroup Summary changed.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "accepted_exception",
        "dataset": "amino.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Artifact Subgroup Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.overall.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_early.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.estimate matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.lower_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.p_value matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.standard_error matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Subgroup Summary.model.subgroup_late.upper_bound matched within tolerance abs 0.001 / rel 1e-09.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section References matched.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Text section Subgroup Summary matched.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "accepted_exception",
        "dataset": "continuous.rcms",
        "detail": "Unexpected text section Inference Method was produced.",
        "exception": "PR #349 intentionally exposes the selected inference method in result output.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Artifact Subgroups Forest Plot descriptor matched; content SHA-256 was validated but byte equality was not required by the cross-platform artifact policy (Windows -> Linux).",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "lymph.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-cumulative",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-leave-one-out",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-cumulative",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-leave-one-out",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-meta-regression",
        "method": "meta.regression",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-meta-regression",
        "method": "meta.regression",
        "metric": "SMD"
      },
      {
        "classification": "pass",
        "dataset": "amino.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "amino-binary-subgroup",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "pass",
        "dataset": "continuous.rcms",
        "detail": "Plot descriptor matched the committed oracle-bound contract.",
        "id": "continuous-subgroup",
        "method": "continuous.random",
        "metric": "SMD"
      }
    ]
  },
  "comparison_count": 474,
  "numeric_contract": {
    "metric_count": 415,
    "path": "tests/analysis_regression/baseline/numeric-contract.json",
    "sha256": "5a14768e2cc755b198646897a27efcd13369de08c5f556d9e5d444de98a65e8f"
  },
  "passed": false,
  "rpy2_identities": {
    "rpy2": "3.6.7",
    "rpy2-rinterface": "3.6.6",
    "rpy2-robjects": "3.6.5"
  }
}

```

## grid-precision-editors

Command: `uv run python scripts/verify_rcms.py calculator-grid-precision`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-grid-precision"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110521Z-5138de2a-calculator-grid-precision
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support raise()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
UNEXPECTED DIALOG: The higher CI must be greater than the point estimate!
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1765, in run
    precision(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/precision_inputs.py", line 95, in run
    assert float(edit(row, column)) == expected[row]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1765, in run
    precision(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/precision_inputs.py", line 95, in run
    assert float(edit(row, column)) == expected[row]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError


```

## grid-precision-first

Command: `uv run python scripts/verify_rcms.py calculator-grid-precision`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-grid-precision"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110305Z-4408bc9e-calculator-grid-precision
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    calculator(app, window, scenario.removeprefix("calculator-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 587, in calculator
    sample, dialog_type, table_name, column = {
                                              ^
KeyError: 'grid-precision'
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    calculator(app, window, scenario.removeprefix("calculator-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 587, in calculator
    sample, dialog_type, table_name, column = {
                                              ^
KeyError: 'grid-precision'


```

## grid-precision-routed

Command: `uv run python scripts/verify_rcms.py calculator-grid-precision`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-grid-precision"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110350Z-a3fe3620-calculator-grid-precision
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support raise()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1765, in run
    precision(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/precision_inputs.py", line 94, in run
    edit(row, column, text)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/precision_inputs.py", line 26, in edit
    assert isinstance(editor, QtWidgets.QLineEdit), editor
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1765, in run
    precision(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/precision_inputs.py", line 94, in run
    edit(row, column, text)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/precision_inputs.py", line 26, in edit
    assert isinstance(editor, QtWidgets.QLineEdit), editor
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None


```

## grid-precision-second

Command: `uv run python scripts/verify_rcms.py calculator-grid-precision`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-grid-precision"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110326Z-5737d139-calculator-grid-precision
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    calculator(app, window, scenario.removeprefix("calculator-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 587, in calculator
    sample, dialog_type, table_name, column = {
                                              ^
KeyError: 'grid-precision'
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    calculator(app, window, scenario.removeprefix("calculator-"))
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 587, in calculator
    sample, dialog_type, table_name, column = {
                                              ^
KeyError: 'grid-precision'


```

## grid-precision-third

Command: `uv run python scripts/verify_rcms.py calculator-grid-precision`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "calculator-grid-precision"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T110344Z-8e9899b7-calculator-grid-precision
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    elif scenario.startswith("calculator-"):
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 587, in calculator
    sample, dialog_type, table_name, column = {
                                              ^
KeyError: 'grid-precision'
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 771, in <module>
    elif scenario.startswith("calculator-"):
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 587, in calculator
    sample, dialog_type, table_name, column = {
                                              ^
KeyError: 'grid-precision'


```

## labels-expanded

Command: `uv run python scripts/verify_rcms.py project-display-labels`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-display-labels"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T111320Z-952d9adf-project-display-labels
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support raise()
This plugin does not support propagateSizeHints()
qt.gui.imageio: QImageIOHandler: Rejecting image as it exceeds the current allocation limit of 256 megabytes
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1791, in run
    labels(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/display_labels.py", line 67, in run
    view = analyze_existing(app, window, 'standard', 'time_to_event.random' if family == 'hr' else 'event_rate.random', observe)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 410, in analyze_existing
    dialog.method_cbo_box.setCurrentText(next(label for label, key in dialog.available_method_d.items() if key == method))
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
StopIteration
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1791, in run
    labels(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/display_labels.py", line 67, in run
    view = analyze_existing(app, window, 'standard', 'time_to_event.random' if family == 'hr' else 'event_rate.random', observe)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 410, in analyze_existing
    dialog.method_cbo_box.setCurrentText(next(label for label, key in dialog.available_method_d.items() if key == method))
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
StopIteration


```

## labels-first

Command: `uv run python scripts/verify_rcms.py project-display-labels`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-display-labels"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T111255Z-7916be2f-project-display-labels
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1791, in run
    labels(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/display_labels.py", line 63, in run
    matrix(app, window, 'analysis-data-' + family, observe)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 357, in run
    assert not callback_errors, callback_errors
           ^^^^^^^^^^^^^^^^^^^
AssertionError: [AssertionError(('metric needs a readable name', 'twoarm_smds_Button', 'SMD'))]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1791, in run
    labels(app, window, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/display_labels.py", line 63, in run
    matrix(app, window, 'analysis-data-' + family, observe)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/analysis_matrix.py", line 357, in run
    assert not callback_errors, callback_errors
           ^^^^^^^^^^^^^^^^^^^
AssertionError: [AssertionError(('metric needs a readable name', 'twoarm_smds_Button', 'SMD'))]


```

## native-label-and-legend-frames

Command: `bash -c for scenario in project-display-labels plot-workflow-regression project-axis-sequential audit-round3-presentation-transforms audit-round3-round5; do uv run python scripts/verify_rcms.py "$scenario" --native || exit; done`

```text
["bash", "-c", "for scenario in project-display-labels plot-workflow-regression project-axis-sequential audit-round3-presentation-transforms audit-round3-round5; do uv run python scripts/verify_rcms.py \"$scenario\" --native || exit; done"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T121256Z-5211bc48-project-display-labels
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T121509Z-be2576db-plot-workflow-regression
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T121551Z-f81290e9-project-axis-sequential
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T121638Z-438dee76-audit-round3-presentation-transforms
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 739, in <module>
    run(app, window, WORK, record_step, scenario)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 529, in run
    check_annotation_spacing(view)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 129, in check_annotation_spacing
    assert b[0]-a[1] >= 4 or a[0]-b[1] >= 4, ("model/footer collision", text, "".join(other.itertext()), a, b)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ('model/footer collision', 'Test for overall effect (H₀: Freeman–Tukey transformed proportion = 0): Z = 13.525 (P < 0.001)', '0', (46.88, 587.88, 341.31, 354.27), (588.77, 595.97, 347.52000000000004, 360.48))
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 739, in <module>
    run(app, window, WORK, record_step, scenario)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 529, in run
    check_annotation_spacing(view)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 129, in check_annotation_spacing
    assert b[0]-a[1] >= 4 or a[0]-b[1] >= 4, ("model/footer collision", text, "".join(other.itertext()), a, b)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ('model/footer collision', 'Test for overall effect (H₀: Freeman–Tukey transformed proportion = 0): Z = 13.525 (P < 0.001)', '0', (46.88, 587.88, 341.31, 354.27), (588.77, 595.97, 347.52000000000004, 360.48))


```

## polish-native-first

Command: `bash -c for scenario in audit-round3-round5 audit-round3-arm-names analysis-diagnostic-regression-continuous project-shell; do uv run python scripts/verify_rcms.py "$scenario" --native || exit; done`

```text
["bash", "-c", "for scenario in audit-round3-round5 audit-round3-arm-names analysis-diagnostic-regression-continuous project-shell; do uv run python scripts/verify_rcms.py \"$scenario\" --native || exit; done"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T111318Z-b875900e-audit-round3-round5
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T111552Z-82a55d11-audit-round3-arm-names
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 735, in <module>
    run(app, window, WORK, record_step, scenario)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 508, in run
    return naming(app, window, work, record)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/arm_names.py", line 62, in run
    assert expected[0] in view.identity_label.text(), view.identity_label.text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Meta-analysis — Verification outcome · Single-arm mean · Mean
Follow-up: first
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 735, in <module>
    run(app, window, WORK, record_step, scenario)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 508, in run
    return naming(app, window, work, record)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/arm_names.py", line 62, in run
    assert expected[0] in view.identity_label.text(), view.identity_label.text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Meta-analysis — Verification outcome · Single-arm mean · Mean
Follow-up: first


```

## precision-and-contour-targeted

Command: `uv run python scripts/verify_rcms.py project-round6-polish`

```text
["uv", "run", "python", "scripts/verify_rcms.py", "project-round6-polish"]
Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261015T111906Z-ecb44b94-project-round6-polish
stdout.log (last 20000 characters):

stderr.log (last 20000 characters):
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 86, in ready
    drive(dialog)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/round6_polish.py", line 46, in small_study
    assert '10' in explanation and '9' in explanation, explanation
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: No formal asymmetry test is available.
Disabled by default below 10 usable studies.
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1812, in run
    polish(app, window, Path(sys.argv[2]), record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/round6_polish.py", line 59, in run
    modal(app, PublicationBiasDialog, small_study, window.action_publication_bias.trigger)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 100, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError('No formal asymmetry test is available.\nDisabled by default below 10 usable studies.')]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 770, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1812, in run
    polish(app, window, Path(sys.argv[2]), record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/round6_polish.py", line 59, in run
    modal(app, PublicationBiasDialog, small_study, window.action_publication_bias.trigger)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 100, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError('No formal asymmetry test is available.\nDisabled by default below 10 usable studies.')]


```

## python-affected

Command: `uv run python -m pytest tests/python/fast tests/python/gui/test_diagnostic_transactional_layout.py -q`

```text
["uv", "run", "python", "-m", "pytest", "tests/python/fast", "tests/python/gui/test_diagnostic_transactional_layout.py", "-q"]
....................................................................F... [ 18%]
...................F....F............................................... [ 36%]
........................................................................ [ 55%]
..............................sss.............s.s....................... [ 73%]
....................................................s................... [ 91%]
......................F....FF...                                         [100%]
=================================== FAILURES ===================================
_____ test_rename_group_preserves_effects_when_the_name_contains_a_hyphen ______

    def test_rename_group_preserves_effects_when_the_name_contains_a_hyphen():
        dataset = _dataset(analysis_dataset.BINARY)
        unit = dataset.studies[0].analysis_units_by_outcome["Outcome"]["first"]
        original_groups = unit.get_group_names()
        dataset.change_group_name(original_groups[0], "Usual-care")
        pair_key = "-".join(("Usual-care", original_groups[1]))
        unit.entered_effects["OR"][pair_key]["est"] = 0.75
    
        dataset.change_group_name("Usual-care", "Control")
    
        renamed_key = "-".join(("Control", original_groups[1]))
        assert unit.get_group_names() == ["Control", original_groups[1]]
        assert unit.groups["Control"].name == "Control"
>       assert unit.entered_effects["OR"][renamed_key]["est"] == 0.75
E       assert None == 0.75

tests/python/fast/test_dataset_contracts.py:81: AssertionError
______ test_dataset_group_and_follow_up_order_is_stable_across_hash_seeds ______

    def test_dataset_group_and_follow_up_order_is_stable_across_hash_seeds():
        script = textwrap.dedent(
            """
            import json
            from rc_metastudio import analysis_dataset
            from rc_metastudio import meta_globals
    
            dataset = analysis_dataset.Dataset()
            outcome = analysis_dataset.Outcome("Mortality", meta_globals.BINARY)
            study = analysis_dataset.Study(1, "Alpha")
            dataset.add_study(study)
            dataset.add_outcome(outcome)
            dataset.add_group("tx C", "Mortality")
            dataset.add_group("tx D", "Mortality")
            dataset.change_follow_up_name("Mortality", "first", "baseline")
            dataset.add_follow_up_to_outcome("Mortality", "week 4")
            dataset.add_follow_up_to_outcome("Mortality", "week 8")
    
            print(json.dumps({
                "all_groups": dataset.get_group_names(),
                "fu_groups": dataset.get_group_names_for_outcome_follow_up(
                    "Mortality", "week 4"
                ),
                "follow_ups": dataset.get_follow_up_names(),
            }))
            """
        )
        expected = {
            "all_groups": ["tx A", "tx B", "tx C", "tx D"],
            "fu_groups": ["tx A", "tx B", "tx C", "tx D"],
            "follow_ups": ["baseline", "week 4", "week 8"],
        }
    
        for seed in ("1", "2"):
            env = os.environ.copy()
            env["PYTHONHASHSEED"] = seed
            env["PYTHONPATH"] = os.path.abspath("src")
            result = subprocess.run(
                [sys.executable, "-c", script],
                check=True,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
>           assert json.loads(result.stdout.splitlines()[-1]) == expected
E           AssertionError: assert {'all_groups'...4', 'week 8']} == {'all_groups'...4', 'week 8']}
E             
E             Omitting 1 identical items, use -vv to show
E             Differing items:
E             {'fu_groups': ['Intervention', 'Control', 'tx C', 'tx D']} != {'fu_groups': ['tx A', 'tx B', 'tx C', 'tx D']}
E             {'all_groups': ['Intervention', 'Control', 'tx C', 'tx D']} != {'all_groups': ['tx A', 'tx B', 'tx C', 'tx D']}
E             Use -v to get more diff

tests/python/fast/test_dataset_ordering.py:67: AssertionError
_____________ test_editable_labels_do_not_change_domain_identities _____________

    def test_editable_labels_do_not_change_domain_identities():
        dataset = analysis_dataset.Dataset()
        outcome = analysis_dataset.Outcome("Outcome", meta_globals.CONTINUOUS)
        study = analysis_dataset.Study(0, "Study")
        dataset.add_study(study)
        dataset.add_outcome(outcome)
        dataset.add_follow_up_to_outcome("Outcome", "week 2")
        unit = study.get_analysis_unit("Outcome", "week 2")
>       group_id = unit.groups["tx A"].stable_id
                   ^^^^^^^^^^^^^^^^^^^
E       KeyError: 'tx A'

tests/python/fast/test_domain_identity.py:14: KeyError
_________ test_large_font_count_overflow_and_focus_stay_inside_content _________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7d299c0aeb10>

    def test_large_font_count_overflow_and_focus_stay_inside_content(monkeypatch):
        app = cast(
            QtWidgets.QApplication,
            required(
                QtWidgets.QApplication.instance() or QtWidgets.QApplication([]),
                "application",
            ),
        )
        old_font = app.font()
        enlarged = QtGui.QFont(old_font)
        enlarged.setPointSize(max(16, old_font.pointSize() + 6))
        app.setFont(enlarged)
        app, dialog = _open_data_dialog(monkeypatch)
        try:
            dialog.show()
            dialog.resize(320, 300)
            app.processEvents()
            dialog.current_item_data = 12
            dialog.two_by_two_table.item(0, 0).setText("999999999999999999")
            app.processEvents()
    
            assert AVAILABLE.contains(dialog.frameGeometry())
>           assert dialog.two_by_two_table.horizontalScrollBar().maximum() > 0
E           assert 0 > 0
E            +  where 0 = <built-in method maximum of QScrollBar object at 0x7d299cd8e170>()
E            +    where <built-in method maximum of QScrollBar object at 0x7d299cd8e170> = <PyQt6.QtWidgets.QScrollBar object at 0x7d299cd8e170>.maximum
E            +      where <PyQt6.QtWidgets.QScrollBar object at 0x7d299cd8e170> = <built-in method horizontalScrollBar of QTableWidget object at 0x7d299cd8dcf0>()
E            +        where <built-in method horizontalScrollBar of QTableWidget object at 0x7d299cd8dcf0> = <PyQt6.QtWidgets.QTableWidget object at 0x7d299cd8dcf0>.horizontalScrollBar
E            +          where <PyQt6.QtWidgets.QTableWidget object at 0x7d299cd8dcf0> = <rc_metastudio.diagnostic_data_dialog.DiagnosticDataDialog object at 0x7d299cd8d3f0>.two_by_two_table

tests/python/gui/test_diagnostic_transactional_layout.py:337: AssertionError
----------------------------- Captured stderr call -----------------------------
This plugin does not support propagateSizeHints()
_ test_direct_effect_validation_is_complete_and_reachable_with_large_font[effect] _

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7d299c0b26d0>
field_name = 'effect_text_box', invalid_value = 'not numeric'
guidance = 'must be numeric', restored = '0.75'

    @pytest.mark.parametrize(
        ("field_name", "invalid_value", "guidance", "restored"),
        [
            ("effect_text_box", "not numeric", "must be numeric", "0.75"),
            ("lower_text_box", "0.95", "lower CI must be less", "0.6"),
        ],
        ids=["effect", "interval"],
    )
    def test_direct_effect_validation_is_complete_and_reachable_with_large_font(
        monkeypatch, field_name, invalid_value, guidance, restored
    ):
        from rc_metastudio import diagnostic_data_dialog
    
        app = cast(
            QtWidgets.QApplication,
            required(
                QtWidgets.QApplication.instance() or QtWidgets.QApplication([]),
                "application",
            ),
        )
        old_font = app.font()
        enlarged = QtGui.QFont(old_font)
        enlarged.setPointSize(max(16, old_font.pointSize() + 6))
        app.setFont(enlarged)
        app, dialog = _open_data_dialog(
            monkeypatch,
            raw_data=[None, None, None, None],
            effects={"Sens": (0.75, 0.60, 0.85), "Spec": (0.80, 0.70, 0.90)},
        )
        warnings = []
        monkeypatch.setattr(
            diagnostic_data_dialog.calc_fncs.QMessageBox,
            "warning",
            lambda _parent, _title, message: warnings.append(message),
        )
        try:
            dialog.show()
            dialog.resize(dialog.width(), 280)
            app.processEvents()
            field = getattr(dialog, field_name)
            field.setText(invalid_value)
            field.editingFinished.emit()
            app.processEvents()
    
            assert warnings
            assert guidance in dialog.inconsistencyLabel.text()
            assert dialog.inconsistencyLabel.wordWrap()
>           assert field.text() == restored
E           AssertionError: assert 'not numeric' == '0.75'
E             
E             - 0.75
E             + not numeric

tests/python/gui/test_diagnostic_transactional_layout.py:539: AssertionError
----------------------------- Captured stderr call -----------------------------
This plugin does not support propagateSizeHints()
_ test_direct_effect_validation_is_complete_and_reachable_with_large_font[interval] _

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7d299c0aabd0>
field_name = 'lower_text_box', invalid_value = '0.95'
guidance = 'lower CI must be less', restored = '0.6'

    @pytest.mark.parametrize(
        ("field_name", "invalid_value", "guidance", "restored"),
        [
            ("effect_text_box", "not numeric", "must be numeric", "0.75"),
            ("lower_text_box", "0.95", "lower CI must be less", "0.6"),
        ],
        ids=["effect", "interval"],
    )
    def test_direct_effect_validation_is_complete_and_reachable_with_large_font(
        monkeypatch, field_name, invalid_value, guidance, restored
    ):
        from rc_metastudio import diagnostic_data_dialog
    
        app = cast(
            QtWidgets.QApplication,
            required(
                QtWidgets.QApplication.instance() or QtWidgets.QApplication([]),
                "application",
            ),
        )
        old_font = app.font()
        enlarged = QtGui.QFont(old_font)
        enlarged.setPointSize(max(16, old_font.pointSize() + 6))
        app.setFont(enlarged)
        app, dialog = _open_data_dialog(
            monkeypatch,
            raw_data=[None, None, None, None],
            effects={"Sens": (0.75, 0.60, 0.85), "Spec": (0.80, 0.70, 0.90)},
        )
        warnings = []
        monkeypatch.setattr(
            diagnostic_data_dialog.calc_fncs.QMessageBox,
            "warning",
            lambda _parent, _title, message: warnings.append(message),
        )
        try:
            dialog.show()
            dialog.resize(dialog.width(), 280)
            app.processEvents()
            field = getattr(dialog, field_name)
            field.setText(invalid_value)
            field.editingFinished.emit()
            app.processEvents()
    
            assert warnings
            assert guidance in dialog.inconsistencyLabel.text()
            assert dialog.inconsistencyLabel.wordWrap()
>           assert field.text() == restored
E           AssertionError: assert '0.95' == '0.6'
E             
E             - 0.6
E             + 0.95

tests/python/gui/test_diagnostic_transactional_layout.py:539: AssertionError
----------------------------- Captured stderr call -----------------------------
This plugin does not support propagateSizeHints()
=========================== short test summary info ============================
FAILED tests/python/fast/test_dataset_contracts.py::test_rename_group_preserves_effects_when_the_name_contains_a_hyphen
FAILED tests/python/fast/test_dataset_ordering.py::test_dataset_group_and_follow_up_order_is_stable_across_hash_seeds
FAILED tests/python/fast/test_domain_identity.py::test_editable_labels_do_not_change_domain_identities
FAILED tests/python/gui/test_diagnostic_transactional_layout.py::test_large_font_count_overflow_and_focus_stay_inside_content
FAILED tests/python/gui/test_diagnostic_transactional_layout.py::test_direct_effect_validation_is_complete_and_reachable_with_large_font[effect]
FAILED tests/python/gui/test_diagnostic_transactional_layout.py::test_direct_effect_validation_is_complete_and_reachable_with_large_font[interval]
6 failed, 380 passed, 6 skipped in 93.04s (0:01:33)

```

## strict-types

Command: `uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path . --extra-search-path src/rc_metastudio --extra-search-path src --extra-search-path scripts --extra-search-path tests/python/gui src/rc_metastudio scripts tests r/RCMetaR/inst/qa`

```text
["uv", "run", "ty", "check", "--extra-search-path", "build/qt6-verification/generated/rc_metastudio", "--extra-search-path", "build/qt6-verification/generated/rc_metastudio/forms", "--extra-search-path", ".", "--extra-search-path", "src/rc_metastudio", "--extra-search-path", "src", "--extra-search-path", "scripts", "--extra-search-path", "tests/python/gui", "src/rc_metastudio", "scripts", "tests", "r/RCMetaR/inst/qa"]
error[unresolved-import]: Cannot resolve imported module `pefile`
   --> scripts/inspect_windows_deployment.py:173:12
    |
172 | def _pe_imports(path: Path) -> list[dict[str, str]]:
173 |     import pefile
    |            ^^^^^^
174 |
175 |     try:
    |
info: Searched in the following paths during module resolution:
info:   1. /home/ali/Documents/Code/rc-metastudio/build/qt6-verification/generated/rc_metastudio (extra search path specified on the CLI or in your config file)
info:   2. /home/ali/Documents/Code/rc-metastudio/build/qt6-verification/generated/rc_metastudio/forms (extra search path specified on the CLI or in your config file)
info:   3. /home/ali/Documents/Code/rc-metastudio (extra search path specified on the CLI or in your config file)
info:   4. /home/ali/Documents/Code/rc-metastudio/src/rc_metastudio (extra search path specified on the CLI or in your config file)
info:   5. /home/ali/Documents/Code/rc-metastudio/src (extra search path specified on the CLI or in your config file)
info:   ... and 6 more paths. Run with `-v` to see all paths.
info: make sure your Python environment is properly configured: https://docs.astral.sh/ty/modules/#python-environment
info: rule `unresolved-import` was selected in the configuration file

error[unresolved-attribute]: Object of type `ResultsWindow` has no attribute `references_text`
   --> scripts/native_results_smoke.py:599:31
    |
597 |             "qpa": app.platformName(),
598 |             "result_text": {
599 |                 "references": results.references_text,
    |                               ^^^^^^^^^^^^^^^^^^^^^^^
600 |                 "summary": results.texts.get("Summary"),
601 |             },
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-import]: Cannot resolve imported module `pefile`
   --> scripts/r_integration_kit.py:863:12
    |
862 | def _windows_native_record(path: Path, relative: str) -> dict[str, object]:
863 |     import pefile
    |            ^^^^^^
864 |
865 |     try:
    |
info: Searched in the following paths during module resolution:
info:   1. /home/ali/Documents/Code/rc-metastudio/build/qt6-verification/generated/rc_metastudio (extra search path specified on the CLI or in your config file)
info:   2. /home/ali/Documents/Code/rc-metastudio/build/qt6-verification/generated/rc_metastudio/forms (extra search path specified on the CLI or in your config file)
info:   3. /home/ali/Documents/Code/rc-metastudio (extra search path specified on the CLI or in your config file)
info:   4. /home/ali/Documents/Code/rc-metastudio/src/rc_metastudio (extra search path specified on the CLI or in your config file)
info:   5. /home/ali/Documents/Code/rc-metastudio/src (extra search path specified on the CLI or in your config file)
info:   ... and 6 more paths. Run with `-v` to see all paths.
info: make sure your Python environment is properly configured: https://docs.astral.sh/ty/modules/#python-environment
info: rule `unresolved-import` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `HKEY_CURRENT_USER`
  --> scripts/r_verification_support.py:66:14
   |
65 |     homes: list[Path] = []
66 |     roots = (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
   |              ^^^^^^^^^^^^^^^^^^^^^^^^
67 |     keys = (
68 |         r"Software\R-core\R",
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `HKEY_CURRENT_USER` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `HKEY_LOCAL_MACHINE`
  --> scripts/r_verification_support.py:66:40
   |
65 |     homes: list[Path] = []
66 |     roots = (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
   |                                        ^^^^^^^^^^^^^^^^^^^^^^^^^
67 |     keys = (
68 |         r"Software\R-core\R",
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `HKEY_LOCAL_MACHINE` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `OpenKey`
  --> scripts/r_verification_support.py:74:22
   |
72 |         for key_name in keys:
73 |             try:
74 |                 with winreg.OpenKey(root, key_name) as key:
   |                      ^^^^^^^^^^^^^^
75 |                     try:
76 |                         install_path, _ = winreg.QueryValueEx(key, "InstallPath")
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `OpenKey` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `QueryValueEx`
  --> scripts/r_verification_support.py:76:43
   |
74 |                 with winreg.OpenKey(root, key_name) as key:
75 |                     try:
76 |                         install_path, _ = winreg.QueryValueEx(key, "InstallPath")
   |                                           ^^^^^^^^^^^^^^^^^^^
77 |                     except OSError:
78 |                         install_path = None
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `QueryValueEx` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `QueryValueEx`
  --> scripts/r_verification_support.py:82:46
   |
80 |                         homes.append(Path(install_path))
81 |                     try:
82 |                         current_version, _ = winreg.QueryValueEx(key, "Current Version")
   |                                              ^^^^^^^^^^^^^^^^^^^
83 |                     except OSError:
84 |                         current_version = None
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `QueryValueEx` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `OpenKey`
  --> scripts/r_verification_support.py:87:34
   |
85 |                     if current_version:
86 |                         try:
87 |                             with winreg.OpenKey(key, current_version) as version_key:
   |                                  ^^^^^^^^^^^^^^
88 |                                 version_install_path, _ = winreg.QueryValueEx(
89 |                                     version_key, "InstallPath"
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `OpenKey` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `QueryValueEx`
  --> scripts/r_verification_support.py:88:59
   |
86 |                         try:
87 |                             with winreg.OpenKey(key, current_version) as version_key:
88 |                                 version_install_path, _ = winreg.QueryValueEx(
   |                                                           ^^^^^^^^^^^^^^^^^^^
89 |                                     version_key, "InstallPath"
90 |                                 )
   |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `QueryValueEx` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `EnumKey`
   --> scripts/r_verification_support.py:98:39
    |
 96 |                     while True:
 97 |                         try:
 98 |                             version = winreg.EnumKey(key, index)
    |                                       ^^^^^^^^^^^^^^
 99 |                         except OSError:
100 |                             break
    |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `EnumKey` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `OpenKey`
   --> scripts/r_verification_support.py:103:34
    |
101 |                         index += 1
102 |                         try:
103 |                             with winreg.OpenKey(key, version) as version_key:
    |                                  ^^^^^^^^^^^^^^
104 |                                 version_install_path, _ = winreg.QueryValueEx(
105 |                                     version_key, "InstallPath"
    |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `OpenKey` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Module `winreg` has no member `QueryValueEx`
   --> scripts/r_verification_support.py:104:59
    |
102 |                         try:
103 |                             with winreg.OpenKey(key, version) as version_key:
104 |                                 version_install_path, _ = winreg.QueryValueEx(
    |                                                           ^^^^^^^^^^^^^^^^^^^
105 |                                     version_key, "InstallPath"
106 |                                 )
    |
info: The member may be available on other Python versions or platforms
info: Python 3.11 was assumed when resolving the `QueryValueEx` attribute
  --> pyproject.toml:74:18
   |
73 | [tool.ty.environment]
74 | python-version = "3.11"
   |                  ^^^^^^ Python version configuration
75 | root = ["./src", ".", "./.agents/skills/verify-rcms/scripts"]
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `setData` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> src/rc_metastudio/continuous_data_dialog.py:808:17
    |
806 |                 return
807 |             with QSignalBlocker(self.simple_table):
808 |                 self.simple_table.item(row, col).setData(Qt.ItemDataRole.UserRole, True)
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
809 |             self.impute_data()
810 |         except Exception as e:
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `setToolTip` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> src/rc_metastudio/continuous_data_dialog.py:863:13
    |
861 |                     table.item(row, col), f"continuous table cell ({row}, {col})"
862 |                 ).setText(str_val)
863 |             table.item(row, col).setToolTip(str_val)
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
864 |             if supplied is not None or not str_val:
865 |                 table.item(row, col).setData(Qt.ItemDataRole.UserRole, bool(supplied and str_val))
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `setData` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> src/rc_metastudio/continuous_data_dialog.py:865:17
    |
863 |             table.item(row, col).setToolTip(str_val)
864 |             if supplied is not None or not str_val:
865 |                 table.item(row, col).setData(Qt.ItemDataRole.UserRole, bool(supplied and str_val))
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
866 |
867 |     def _disable_row_if_filled(self, table, row, col):
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `text` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> src/rc_metastudio/continuous_data_dialog.py:938:19
    |
936 |         for table in self.tables:
937 |             old_tables_data.append([
938 |                 [(table.item(row, col).text(), bool(table.item(row, col).data(Qt.ItemDataRole.UserRole)))
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^
939 |                  for col in range(table.columnCount())]
940 |                 for row in range(table.rowCount())
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `data` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> src/rc_metastudio/continuous_data_dialog.py:938:53
    |
936 |         for table in self.tables:
937 |             old_tables_data.append([
938 |                 [(table.item(row, col).text(), bool(table.item(row, col).data(Qt.ItemDataRole.UserRole)))
    |                                                     ^^^^^^^^^^^^^^^^^^^^^^^^^
939 |                  for col in range(table.columnCount())]
940 |                 for row in range(table.rowCount())
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `data` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> src/rc_metastudio/continuous_data_dialog.py:977:46
    |
975 |             for var_index, var_name in enumerate(var_names):
976 |                 var_value = self._get_float(row_index, var_index)
977 |                 if var_value is not None and self.simple_table.item(row_index, var_index).data(Qt.ItemDataRole.UserRole):
    |                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
978 |                     current_values[self._imputation_field_name(var_name)] = var_value
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[index-out-of-bounds]: Index 1 is out of bounds for tuple `tuple[str]` with length 1
  --> tests/e2e/arm_names.py:74:66
   |
72 |                     assert table.horizontalHeaderItem(1).text() == "No event"
73 |                 if len(entered)==2:
74 |                     assert table.verticalHeaderItem(1).text() == expected[1]
   |                                                                  ^^^^^^^^
75 |                 record("round5-arm-calculator", dialog, case=case, groups=expected, capture_surface="desktop-composite")
76 |                 dialog.reject()
   |
info: rule `index-out-of-bounds` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `template_btn`
  --> tests/e2e/arm_names.py:90:28
   |
88 |             template = work / f"arms-{case}-template.csv"
89 |             with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(template), "CSV")):
90 |                 click(app, page.template_btn)
   |                            ^^^^^^^^^^^^^^^^^
91 |             with template.open(encoding="utf-8-sig") as stream:
92 |                 canonical = next(csv.reader(stream))
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `select_file_btn`
   --> tests/e2e/arm_names.py:107:32
    |
105 |                     writer.writerow(values)
106 |                 with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(source), "CSV")):
107 |                     click(app, page.select_file_btn)
    |                                ^^^^^^^^^^^^^^^^^^^^
108 |                 assert page.isComplete(), page.import_status.text()
109 |                 displayed=[page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `isComplete` is not defined on `None` in union `QWizardPage | None`
   --> tests/e2e/arm_names.py:108:24
    |
106 |                 with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(source), "CSV")):
107 |                     click(app, page.select_file_btn)
108 |                 assert page.isComplete(), page.import_status.text()
    |                        ^^^^^^^^^^^^^^^
109 |                 displayed=[page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
110 |                 assert displayed == canonical, (displayed, canonical)
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `import_status`
   --> tests/e2e/arm_names.py:108:43
    |
106 |                 with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(source), "CSV")):
107 |                     click(app, page.select_file_btn)
108 |                 assert page.isComplete(), page.import_status.text()
    |                                           ^^^^^^^^^^^^^^^^^^
109 |                 displayed=[page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
110 |                 assert displayed == canonical, (displayed, canonical)
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `preview_table`
   --> tests/e2e/arm_names.py:109:28
    |
107 |                     click(app, page.select_file_btn)
108 |                 assert page.isComplete(), page.import_status.text()
109 |                 displayed=[page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
    |                            ^^^^^^^^^^^^^^^^^^
110 |                 assert displayed == canonical, (displayed, canonical)
111 |                 if data_type == "binary":
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `preview_table`
   --> tests/e2e/arm_names.py:109:93
    |
107 |                     click(app, page.select_file_btn)
108 |                 assert page.isComplete(), page.import_status.text()
109 |                 displayed=[page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
    |                                                                                             ^^^^^^^^^^^^^^^^^^
110 |                 assert displayed == canonical, (displayed, canonical)
111 |                 if data_type == "binary":
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `preview_table`
   --> tests/e2e/arm_names.py:112:29
    |
110 | …     assert displayed == canonical, (displayed, canonical)
111 | …     if data_type == "binary":
112 | …         assert [page.preview_table.item(0, i).text() for i in range(2, 6)] == ["4", "20", "6", "22"]
    |                   ^^^^^^^^^^^^^^^^^^
113 | …     record("round5-arm-csv-preview", wizard, case=case, spelling=spelling, headers=displayed, exports={"template":str(template),"in…
114 | …     page.import_tabs.setCurrentWidget(page.mapping_table)
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `import_tabs`
   --> tests/e2e/arm_names.py:114:17
    |
112 | …         assert [page.preview_table.item(0, i).text() for i in range(2, 6)] == ["4", "20", "6", "22"]
113 | …     record("round5-arm-csv-preview", wizard, case=case, spelling=spelling, headers=displayed, exports={"template":str(template),"in…
114 | …     page.import_tabs.setCurrentWidget(page.mapping_table)
    |       ^^^^^^^^^^^^^^^^
115 | …     assert not any("tx " in control.itemText(i).casefold() for control in page.mapping_controls for i in range(control.count()))
116 | …     record("round5-arm-csv-mapping", wizard, case=case, spelling=spelling)
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `mapping_table`
   --> tests/e2e/arm_names.py:114:51
    |
112 | …         assert [page.preview_table.item(0, i).text() for i in range(2, 6)] == ["4", "20", "6", "22"]
113 | …     record("round5-arm-csv-preview", wizard, case=case, spelling=spelling, headers=displayed, exports={"template":str(template),"in…
114 | …     page.import_tabs.setCurrentWidget(page.mapping_table)
    |                                         ^^^^^^^^^^^^^^^^^^
115 | …     assert not any("tx " in control.itemText(i).casefold() for control in page.mapping_controls for i in range(control.count()))
116 | …     record("round5-arm-csv-mapping", wizard, case=case, spelling=spelling)
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `mapping_controls`
   --> tests/e2e/arm_names.py:115:87
    |
113 | …         record("round5-arm-csv-preview", wizard, case=case, spelling=spelling, headers=displayed, exports={"template":str(template)…
114 | …         page.import_tabs.setCurrentWidget(page.mapping_table)
115 | …         assert not any("tx " in control.itemText(i).casefold() for control in page.mapping_controls for i in range(control.count()))
    |                                                                                 ^^^^^^^^^^^^^^^^^^^^^
116 | …         record("round5-arm-csv-mapping", wizard, case=case, spelling=spelling)
117 | …     wizard.reject()
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
  --> tests/e2e/audit_round3.py:18:18
   |
16 |     assert expected in " ".join(text.split()), (expected, text)
17 |     caption = nodes[-1]
18 |     size = float(re.search(r"font-size:\s*([\d.]+)px", caption.attrib["style"])[1])
   |                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 |     assert size >= 12.9, ("unreadable caption", caption.attrib)
   |
info: rule `not-subscriptable` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
   --> tests/e2e/audit_round3.py:115:28
    |
113 |             x, y = float(node.attrib["x"]), float(node.attrib["y"])
114 |             width = float(node.attrib["textLength"].removesuffix("px"))
115 |             height = float(re.search(r"font-size: ([\d.]+)px", node.attrib["style"])[1])
    |                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
116 |             anchor = node.attrib.get("text-anchor", "start")
117 |             left = x-width if anchor == "end" else x-width/2 if anchor == "middle" else x
    |
info: rule `not-subscriptable` was selected in the configuration file

error[possibly-unresolved-reference]: Name `lines` used when possibly not defined
   --> tests/e2e/audit_round3.py:254:25
    |
252 | …     if workflow in {"cumulative", "leave-one-out"}:
253 | …         row_y = [y for text, y in nodes if text in data["slab"]]
254 | …         for line in lines if data["measure"] in {"OR", "RR", "HR", "IRR", "MD", "SMD"} and data["range"][0] <= 0 <= data["range"][1…
    |                       ^^^^^
255 | …             if (abs(float(line["x1"]) - float(line["x2"])) < .01
256 | …                 and abs(float(line["y1"]) - float(line["y2"])) > 50
    |
info: rule `possibly-unresolved-reference` was selected in the configuration file

error[possibly-unresolved-reference]: Name `ticks` used when possibly not defined
   --> tests/e2e/audit_round3.py:257:77
    |
255 |                 if (abs(float(line["x1"]) - float(line["x2"])) < .01
256 |                     and abs(float(line["y1"]) - float(line["y2"])) > 50
257 |                     and any(abs(float(line["x1"]) - tick) < .02 for tick in ticks)):
    |                                                                             ^^^^^
258 |                     assert max(float(line["y1"]), float(line["y2"])) <= max(row_y) + 15, ("null reaches footer", line, row_y)
259 |         view.report_action.setChecked(False)
    |
info: rule `possibly-unresolved-reference` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
   --> tests/e2e/audit_round3.py:455:51
    |
453 | …     title = next(node for node in svg.iter("{http://www.w3.org/2000/svg}text")
454 | …                  if "Entered effect" in "".join(node.itertext()))
455 | …     title_x = float(title.attrib.get("x", re.search(r"translate\(([-\d.]+)", title.attrib.get("transform", "translate(0"))[1]))
    |                                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
456 | …     title_right = title_x + float(re.search(r"font-size:\s*([\d.]+)px", title.attrib["style"])[1])
457 | …     tick_left = min(float(node.attrib["x"]) - float(node.attrib["textLength"].removesuffix("px")) for node in tick_nodes)
    |
info: rule `not-subscriptable` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
   --> tests/e2e/audit_round3.py:456:43
    |
454 | …                  if "Entered effect" in "".join(node.itertext()))
455 | …     title_x = float(title.attrib.get("x", re.search(r"translate\(([-\d.]+)", title.attrib.get("transform", "translate(0"))[1]))
456 | …     title_right = title_x + float(re.search(r"font-size:\s*([\d.]+)px", title.attrib["style"])[1])
    |                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
457 | …     tick_left = min(float(node.attrib["x"]) - float(node.attrib["textLength"].removesuffix("px")) for node in tick_nodes)
458 | …     assert tick_left - title_right >= 4, ("tick/title gap", tick_left, title.attrib)
    |
info: rule `not-subscriptable` was selected in the configuration file

error[unresolved-attribute]: Attribute `text` is not defined on `None` in union `Unknown | QTableWidgetItem | None`
   --> tests/e2e/audit_round3.py:627:24
    |
625 |                 click(app, page.select_file_btn)
626 |             assert page.isComplete(), page.import_status.text()
627 |             headers = [page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
628 |             assert "Estimate" in headers and "TX Mean" not in headers, headers
629 |             record("round4-contextual-csv", wizard, headers=headers, input_headers=page.required_header_labels,
    |
info: rule `unresolved-attribute` was selected in the configuration file

error[invalid-argument-type]: Argument to bound method `__init__` is incorrect
   --> tests/e2e/audit_round3.py:713:31
    |
711 |             for title, path in view.results.display_images.items():
712 |                 r_bridge.load_in_r(str(view.params_paths[title]) + ".plotdata")
713 |                 bounds = list(r_bridge.ro.r('RCMetaR:::rcmetar.forest.layout.preflight(plot.data)$x$alim'))
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Expected `Iterable[Unknown]`, found `object`
714 |                 assert all(math.isfinite(x) for x in bounds) and bounds[1] > bounds[0], bounds
715 |                 nodes = list(ET.parse(path).iter("{http://www.w3.org/2000/svg}text"))
    |
info: Matching overload defined here
    --> stdlib/builtins.pyi:2839:9
     |
2837 |     def __init__(self) -> None: ...
2838 |     @overload
2839 |     def __init__(self, iterable: Iterable[_T], /) -> None: ...
     |         ^^^^^^^^       ---------------------- Parameter declared here
2840 |     def copy(self) -> list[_T]:
2841 |         """Return a shallow copy of the list."""
     |
info: Non-matching overloads for bound method `__init__`:
info:   (self) -> None
info: rule `invalid-argument-type` was selected in the configuration file

error[possibly-unresolved-reference]: Name `bounds` used when possibly not defined
   --> tests/e2e/audit_round3.py:723:92
    |
721 |                 assert len(ticks) >= 2, ticks
722 |                 assert len(labels) == len(ticks), ("duplicate collapsed-axis labels", style, labels)
723 |             record("round3-degenerate-axis", view, style=style, entered=[1, 1e-20], bounds=bounds,
    |                                                                                            ^^^^^^
724 |                    ticks=sorted(ticks), plots=dict(view.results.display_images))
725 |             if style == "default":
    |
info: rule `possibly-unresolved-reference` was selected in the configuration file

error[possibly-unresolved-reference]: Name `ticks` used when possibly not defined
   --> tests/e2e/audit_round3.py:724:33
    |
722 |                 assert len(labels) == len(ticks), ("duplicate collapsed-axis labels", style, labels)
723 |             record("round3-degenerate-axis", view, style=style, entered=[1, 1e-20], bounds=bounds,
724 |                    ticks=sorted(ticks), plots=dict(view.results.display_images))
    |                                 ^^^^^
725 |             if style == "default":
726 |                 view.graphics_view.verticalScrollBar().setValue(view.graphics_view.verticalScrollBar().maximum())
    |
info: rule `possibly-unresolved-reference` was selected in the configuration file

error[possibly-unresolved-reference]: Name `bounds` used when possibly not defined
   --> tests/e2e/audit_round3.py:727:83
    |
725 |             if style == "default":
726 |                 view.graphics_view.verticalScrollBar().setValue(view.graphics_view.verticalScrollBar().maximum())
727 |                 record("round3-degenerate-axis-bottom", view, style=style, bounds=bounds)
    |                                                                                   ^^^^^^
728 |             view.close()
729 |             window.workspace.mark_saved()
    |
info: rule `possibly-unresolved-reference` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
   --> tests/e2e/audit_round3.py:924:36
    |
922 | …         continue
923 | …     y = float(node.attrib["y"])
924 | …     height = float(re.search(r"font-size:\s*([\d.]+)px", node.attrib["style"])[1])
    |                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
925 | …     for rule in ET.parse(path).iter("{http://www.w3.org/2000/svg}line"):
926 | …         if abs(float(rule.attrib["x2"]) - float(rule.attrib["x1"])) < 500 or abs(float(rule.attrib["y2"]) - float(rule.attrib["y1"]…
    |
info: rule `not-subscriptable` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
    --> tests/e2e/audit_round3.py:1062:28
     |
1060 |             x, y = float(node.attrib["x"]), float(node.attrib["y"])
1061 |             width = float(node.attrib["textLength"].removesuffix("px"))
1062 |             height = float(re.search(r"font-size:\s*([\d.]+)px", node.attrib["style"])[1]) * .8
     |                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1063 |             anchor = node.attrib.get("text-anchor", "start")
1064 |             left = x - (width if anchor == "end" else width/2 if anchor == "middle" else 0)
     |
info: rule `not-subscriptable` was selected in the configuration file

error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
    --> tests/e2e/audit_round3.py:1079:28
     |
1077 |                 continue
1078 |             x, y = float(node.attrib["x"]), float(node.attrib["y"])
1079 |             height = float(re.search(r"font-size:\s*([\d.]+)px", node.attrib["style"])[1])
     |                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1080 |             for line in svg.iter("{http://www.w3.org/2000/svg}line"):
1081 |                 if abs(float(line.attrib["y1"]) - float(line.attrib["y2"])) < .01:
     |
info: rule `not-subscriptable` was selected in the configuration file

error[no-matching-overload]: No overload of function `keyClick` matches arguments
  --> tests/e2e/precision_inputs.py:29:13
   |
27 |         before = editor.text()
28 |         if text is not None:
29 |             QTest.keyClick(editor, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier)
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
30 |             QTest.keyClicks(editor, text)
31 |         QTest.keyClick(editor, QtCore.Qt.Key.Key_Return)
   |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:149:9
    |
147 | … def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
148 | … @typing.overload
149 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 | … @typing.overload
151 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: str, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `keyClick`:
info:   (self, widget: QWidget | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, widget: QWidget | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[missing-argument]: No argument provided for required parameter `sequence` of function `keyClicks`
  --> tests/e2e/precision_inputs.py:30:13
   |
28 |         if text is not None:
29 |             QTest.keyClick(editor, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier)
30 |             QTest.keyClicks(editor, text)
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
31 |         QTest.keyClick(editor, QtCore.Qt.Key.Key_Return)
32 |         app.processEvents()
   |
info: Parameter declared here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:147:57
    |
145 |     @typing.overload
146 |     def keyEvent(self, action: 'QTest.KeyAction', window: QtGui.QWindow|None, ascii: str, modifier: QtCore.Qt.KeyboardModifier = ...,…
147 |     def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = …
    |                                                         ^^^^^^^^^^^^^^^^^^
148 |     @typing.overload
149 |     def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = .…
    |
info: rule `missing-argument` was selected in the configuration file

error[no-matching-overload]: No overload of function `keyClick` matches arguments
  --> tests/e2e/precision_inputs.py:31:9
   |
29 |             QTest.keyClick(editor, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier)
30 |             QTest.keyClicks(editor, text)
31 |         QTest.keyClick(editor, QtCore.Qt.Key.Key_Return)
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
32 |         app.processEvents()
33 |         return before
   |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:149:9
    |
147 | … def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
148 | … @typing.overload
149 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 | … @typing.overload
151 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: str, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `keyClick`:
info:   (self, widget: QWidget | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, widget: QWidget | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `outcome_name_LineEdit`
  --> tests/e2e/precision_inputs.py:70:5
   |
68 |     wizard = main_wizard.MainWizard(path='csv_import')
69 |     wizard.set_dataset_info(dict(arms='two', data_type='continuous', sub_type='means', effect='SMD', metric_choices=[], name='Precisio…
70 |     wizard.page(main_wizard.Page_OutcomeName).outcome_name_LineEdit.setText('Precision')
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
71 |     wizard.setStartId(main_wizard.Page_CsvImport)
72 |     wizard.restart()
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[no-matching-overload]: No overload of function `mouseClick` matches arguments
  --> tests/e2e/precision_inputs.py:77:9
   |
75 |     page = wizard.currentPage()
76 |     with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(csv), '')):
77 |         QTest.mouseClick(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
78 |     assert page.isComplete(), page.required_header_labels
79 |     record('csv-precision-preview', wizard, inputs=expected)
   |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:111:9
    |
109 | … def mouseDClick(self, window: QtGui.QWindow|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
110 | … @typing.overload
111 | … def mouseClick(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
112 | … @typing.overload
113 | … def mouseClick(self, window: QtGui.QWindow|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `mouseClick`:
info:   (self, widget: QWidget | None, button: MouseButton, modifier: KeyboardModifier = ..., pos: QPoint = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, button: MouseButton, modifier: KeyboardModifier = ..., pos: QPoint = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `select_file_btn`
  --> tests/e2e/precision_inputs.py:77:26
   |
75 |     page = wizard.currentPage()
76 |     with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(csv), '')):
77 |         QTest.mouseClick(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
   |                          ^^^^^^^^^^^^^^^^^^^^
78 |     assert page.isComplete(), page.required_header_labels
79 |     record('csv-precision-preview', wizard, inputs=expected)
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Attribute `isComplete` is not defined on `None` in union `QWizardPage | None`
  --> tests/e2e/precision_inputs.py:78:12
   |
76 |     with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(csv), '')):
77 |         QTest.mouseClick(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
78 |     assert page.isComplete(), page.required_header_labels
   |            ^^^^^^^^^^^^^^^
79 |     record('csv-precision-preview', wizard, inputs=expected)
80 |     window._handle_wizard_results(wizard.get_results())
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[unresolved-attribute]: Object of type `QWizardPage | None` has no attribute `required_header_labels`
  --> tests/e2e/precision_inputs.py:78:31
   |
76 |     with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(csv), '')):
77 |         QTest.mouseClick(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
78 |     assert page.isComplete(), page.required_header_labels
   |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
79 |     record('csv-precision-preview', wizard, inputs=expected)
80 |     window._handle_wizard_results(wizard.get_results())
   |
info: rule `unresolved-attribute` was selected in the configuration file

error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
  --> tests/e2e/review1_design.py:88:17
   |
86 |             assert wizard.get_wizard_path() == expected
87 |             if app.platformName() in {'windows', 'xcb', 'cocoa'}:
88 |                 QTest.qWait(250)
   |                 ^^^^^^^^^^^^^^^^
89 |             record('review1-start-wizard-' + expected, wizard)
90 |             wizard.reject()
   |
info: Parameter declared here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:21
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |                     ^^^^^^^
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `missing-argument` was selected in the configuration file

error[invalid-argument-type]: Argument to function `qWait` is incorrect
  --> tests/e2e/review1_design.py:88:29
   |
86 |             assert wizard.get_wizard_path() == expected
87 |             if app.platformName() in {'windows', 'xcb', 'cocoa'}:
88 |                 QTest.qWait(250)
   |                             ^^^ Expected `QTest`, found `Literal[250]`
89 |             record('review1-start-wizard-' + expected, wizard)
90 |             wizard.reject()
   |
info: Function defined here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:9
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |         ^^^^^ ---- Parameter declared here
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `invalid-argument-type` was selected in the configuration file

error[no-matching-overload]: No overload of function `keyClick` matches arguments
   --> tests/e2e/review1_design.py:131:5
    |
129 |     keyboard_traversal(app, window, [window.analysis_button, window.navigation_dimension, window.tableView], record, "workspace")
130 |     window.tableView.setFocus()
131 |     QTest.keyClick(window.tableView, QtCore.Qt.Key.Key_Tab, QtCore.Qt.KeyboardModifier.ControlModifier)
    |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
132 |     app.processEvents()
133 |     assert app.focusWidget() is not window.tableView, "Ctrl+Tab cannot leave the study grid"
    |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:149:9
    |
147 | … def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
148 | … @typing.overload
149 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 | … @typing.overload
151 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: str, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `keyClick`:
info:   (self, widget: QWidget | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, widget: QWidget | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[no-matching-overload]: No overload of function `mouseRelease` matches arguments
   --> tests/e2e/review1_design.py:149:17
    |
147 |                 prerequisite = window.action_subgroup_ma
148 |                 assert not prerequisite.isEnabled()
149 |                 QTest.mouseRelease(menu, QtCore.Qt.MouseButton.LeftButton, pos=menu.actionGeometry(prerequisite).center())
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 |                 QTest.mouseMove(menu, menu.actionGeometry(window.action_go).center())
151 |                 QTest.mouseMove(menu, menu.actionGeometry(prerequisite).center())
    |
info: First overload defined here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:95:9
   |
93 | … def qWait(self, ms: int) -> None: ...
94 | … @typing.overload
95 | … def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
   |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
96 | … @typing.overload
97 | … def mouseRelease(self, window: QtGui.QWindow|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
   |
info: Possible overloads for function `mouseRelease`:
info:   (self, widget: QWidget | None, button: MouseButton, modifier: KeyboardModifier = ..., pos: QPoint = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, button: MouseButton, modifier: KeyboardModifier = ..., pos: QPoint = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
   --> tests/e2e/review1_design.py:152:17
    |
150 | …     QTest.mouseMove(menu, menu.actionGeometry(window.action_go).center())
151 | …     QTest.mouseMove(menu, menu.actionGeometry(prerequisite).center())
152 | …     QTest.qWait(1200)
    |       ^^^^^^^^^^^^^^^^^
153 | …     assert QtWidgets.QToolTip.isVisible() and QtWidgets.QToolTip.text() == prerequisite.toolTip(), QtWidgets.QToolTip.text()
154 | …     record('round5-analysis-prerequisite-tooltip', window, tooltip=QtWidgets.QToolTip.text(), capture_surface="desktop-composite")
    |
info: Parameter declared here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:21
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |                     ^^^^^^^
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `missing-argument` was selected in the configuration file

error[invalid-argument-type]: Argument to function `qWait` is incorrect
   --> tests/e2e/review1_design.py:152:29
    |
150 | …     QTest.mouseMove(menu, menu.actionGeometry(window.action_go).center())
151 | …     QTest.mouseMove(menu, menu.actionGeometry(prerequisite).center())
152 | …     QTest.qWait(1200)
    |                   ^^^^ Expected `QTest`, found `Literal[1200]`
153 | …     assert QtWidgets.QToolTip.isVisible() and QtWidgets.QToolTip.text() == prerequisite.toolTip(), QtWidgets.QToolTip.text()
154 | …     record('round5-analysis-prerequisite-tooltip', window, tooltip=QtWidgets.QToolTip.text(), capture_surface="desktop-composite")
    |
info: Function defined here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:9
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |         ^^^^^ ---- Parameter declared here
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `invalid-argument-type` was selected in the configuration file

error[no-matching-overload]: No overload of function `mouseClick` matches arguments
   --> tests/e2e/review1_design.py:157:13
    |
155 | …             QtWidgets.QToolTip.hideText()
156 | …         record('round5-analysis-menu', menu, actions=[dict(text=action.text(), enabled=action.isEnabled(), tooltip=action.toolTip()…
157 | …         QTest.mouseClick(menu, QtCore.Qt.MouseButton.LeftButton, pos=menu.actionGeometry(window.action_go).center())
    |           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
158 | …     except Exception as error:
159 | …         menu_errors.append(str(error))
    |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:111:9
    |
109 | … def mouseDClick(self, window: QtGui.QWindow|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
110 | … @typing.overload
111 | … def mouseClick(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
112 | … @typing.overload
113 | … def mouseClick(self, window: QtGui.QWindow|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., pos: QtCore.QPoint = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `mouseClick`:
info:   (self, widget: QWidget | None, button: MouseButton, modifier: KeyboardModifier = ..., pos: QPoint = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, button: MouseButton, modifier: KeyboardModifier = ..., pos: QPoint = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
   --> tests/e2e/review1_design.py:223:5
    |
221 |     window.activateWindow()
222 |     controls[0].setFocus(QtCore.Qt.FocusReason.TabFocusReason)
223 |     QTest.qWait(80)
    |     ^^^^^^^^^^^^^^^
224 |     visited, reached = [], set()
225 |     for _ in range(300):
    |
info: Parameter declared here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:21
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |                     ^^^^^^^
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `missing-argument` was selected in the configuration file

error[invalid-argument-type]: Argument to function `qWait` is incorrect
   --> tests/e2e/review1_design.py:223:17
    |
221 |     window.activateWindow()
222 |     controls[0].setFocus(QtCore.Qt.FocusReason.TabFocusReason)
223 |     QTest.qWait(80)
    |                 ^^ Expected `QTest`, found `Literal[80]`
224 |     visited, reached = [], set()
225 |     for _ in range(300):
    |
info: Function defined here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:9
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |         ^^^^^ ---- Parameter declared here
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `invalid-argument-type` was selected in the configuration file

error[no-matching-overload]: No overload of function `keyClick` matches arguments
   --> tests/e2e/review1_design.py:235:9
    |
233 |             break
234 |         modifier = QtCore.Qt.KeyboardModifier.NoModifier
235 |         QTest.keyClick(focus, QtCore.Qt.Key.Key_Tab, modifier)
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
236 |         app.processEvents()
237 |     assert len(reached) == len(controls), (surface, reached, [c.objectName() for c in controls], visited)
    |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:149:9
    |
147 | … def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
148 | … @typing.overload
149 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 | … @typing.overload
151 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: str, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `keyClick`:
info:   (self, widget: QWidget | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, widget: QWidget | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[no-matching-overload]: No overload of function `keyClick` matches arguments
   --> tests/e2e/review1_design.py:264:17
    |
262 |             for _ in range(len(buttons)):
263 |                 visited.add(app.focusWidget())
264 |                 QTest.keyClick(app.focusWidget(), QtCore.Qt.Key.Key_Right)
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
265 |                 app.processEvents()
266 |             assert visited == set(buttons), ("radio arrow traversal", visited, buttons)
    |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:149:9
    |
147 | … def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
148 | … @typing.overload
149 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 | … @typing.overload
151 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: str, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `keyClick`:
info:   (self, widget: QWidget | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, widget: QWidget | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[no-matching-overload]: No overload of function `keyClick` matches arguments
   --> tests/e2e/review1_design.py:268:13
    |
266 |             assert visited == set(buttons), ("radio arrow traversal", visited, buttons)
267 |             radio.setFocus()
268 |             QTest.keyClick(radio, QtCore.Qt.Key.Key_Space)
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
269 |             app.processEvents()
270 |             assert radio.isChecked(), ("radio selection restoration", radio.text())
    |
info: First overload defined here
   --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:149:9
    |
147 | … def keyClicks(self, widget: QtWidgets.QWidget|None, sequence: str|None, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
148 | … @typing.overload
149 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: QtCore.Qt.Key, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 | … @typing.overload
151 | … def keyClick(self, widget: QtWidgets.QWidget|None, key: str, modifier: QtCore.Qt.KeyboardModifier = ..., delay: int = ...) -> None: ...
    |
info: Possible overloads for function `keyClick`:
info:   (self, widget: QWidget | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, widget: QWidget | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: Key, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info:   (self, window: QWindow | None, key: str, modifier: KeyboardModifier = ..., delay: int = ...) -> None
info: rule `no-matching-overload` was selected in the configuration file

error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
   --> tests/e2e/ux_workflows.py:273:9
    |
271 |     assert form.error_label.text()
272 |     if app.platformName() in {"windows", "xcb", "cocoa"}:
273 |         QtTest.QTest.qWait(250)
    |         ^^^^^^^^^^^^^^^^^^^^^^^
274 |     assert form.rect().contains(button.mapTo(form, button.rect().bottomRight()))
275 |     assert form.rect().contains(form.error_label.mapTo(form, form.error_label.rect().bottomRight()))
    |
info: Parameter declared here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:21
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |                     ^^^^^^^
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `missing-argument` was selected in the configuration file

error[invalid-argument-type]: Argument to function `qWait` is incorrect
   --> tests/e2e/ux_workflows.py:273:28
    |
271 |     assert form.error_label.text()
272 |     if app.platformName() in {"windows", "xcb", "cocoa"}:
273 |         QtTest.QTest.qWait(250)
    |                            ^^^ Expected `QTest`, found `Literal[250]`
274 |     assert form.rect().contains(button.mapTo(form, button.rect().bottomRight()))
275 |     assert form.rect().contains(form.error_label.mapTo(form, form.error_label.rect().bottomRight()))
    |
info: Function defined here
  --> .venv/lib/python3.11/site-packages/PyQt6/QtTest.pyi:93:9
   |
91 |     @typing.overload
92 |     def qWaitForWindowActive(self, widget: QtWidgets.QWidget|None, timeout: int = ...) -> bool: ...
93 |     def qWait(self, ms: int) -> None: ...
   |         ^^^^^ ---- Parameter declared here
94 |     @typing.overload
95 |     def mouseRelease(self, widget: QtWidgets.QWidget|None, button: QtCore.Qt.MouseButton, modifier: QtCore.Qt.KeyboardModifier = ..., …
   |
info: rule `invalid-argument-type` was selected in the configuration file

error[unresolved-attribute]: Attribute `setData` is not defined on `None` in union `QTableWidgetItem | None`
   --> tests/python/fast/test_calculator_qt6.py:483:9
    |
482 |     for column in (0, 1, 4, 5, 6):
483 |         form.simple_table.item(0, column).setData(QtCore.Qt.ItemDataRole.UserRole, True)
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
484 |     form.impute_data()
    |
info: rule `unresolved-attribute` was selected in the configuration file

Found 67 diagnostics

```
