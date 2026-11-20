# Positive ratio bound evidence

The owner selected scientific notation with two significant figures and a true minus for positive ratio CI and PI bounds that round to zero. In the six-decimal HR and IRR drive, the independently fitted lower bound near 1.69943 × 10⁻¹³ displayed as `1.7e−13` in both journal forest presets, the study table, plain text, HTML and exported DOCX. True zeros and bounds already distinguishable at fixed precision keep their existing format.

The native Windows drive also checked live study quantities, save/reopen and annotation spacing. The former 18-inch cap caused a large fixed-decimal annotation to cross another column, so Default and RevMan can now reserve the measured width. The complete native renders and DOCX are local evidence, regenerable with `uv run python scripts/verify_rcms.py calculator-ratio-precision --native`. The [receipt](receipts.json) identifies the native captures and the corresponding SVG and report outputs.

The Windows package inspector's amino digest predated the approved presentation. The matching macOS inspector also had the old BCG digest. The [summary diff](packaged-summaries.diff) shows the sign and SE changes, and both original digests were reproduced from master. The [digest receipt](packaged-summary-digests.json) records the old and new values. The inspector retains its exact-match rule.

```powershell
. ./artifacts/output-polish/runtime.ps1
uv run python -c "from pathlib import Path; from scripts.verify import run_typing; run_typing(Path('build/qt6-verification').resolve())"
& "$env:RCMS_R_HOME/bin/Rscript.exe" --vanilla -e "install.packages('r/RCMetaR', repos=NULL, type='source', lib=Sys.getenv('RCMS_R_LIBS'))"
uv run python scripts/verify_rcms.py calculator-ratio-precision --native
$env:R_HOME = $env:RCMS_R_HOME
$env:PATH = "$env:R_HOME/bin/x64;$env:R_HOME/bin;$env:PATH"
uv run python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-ratio-two-significant
```

The package source observations are local evidence, regenerable with the installed RCMetaR from each revision and the app automation entry point below. Output paths should be absolute because application startup sets its working directory.

```powershell
$root = (Get-Location).Path
foreach ($sample in @('amino', 'BCG')) {
    uv run python -m rc_metastudio --automation-package-analyze "$root/build/output-polish/$sample-analysis.json" "$root/sample_projects/$sample.rcms" binary.random DL
}
```

Windows strict typing and 235 focused tests passed. The frozen gate passed all 416 numerical comparisons. Both the fitted-report and BMJ prediction scenarios passed with the original value checks, along with both manuscript export scenarios. The fitted-report check now takes subgroup names from the source table's designated label column. The BMJ check compares each printed prediction bound against metafor and verifies all six study-line colors at the study row positions.

[Typing](../qualification/ratio-precision-typing.log), [focused tests](../qualification/ratio-precision-focused.log), [frozen comparison](../qualification/ratio-precision-frozen.log), [report and manuscript scenarios](../qualification/ratio-precision-report-checks.log).

```powershell
uv run python -m pytest -W error tests/python/fast/test_plot_service.py tests/python/fast/test_plot_capabilities.py tests/python/fast/test_result_formatting_audit.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_funnel_plot_editor.py tests/python/gui/test_main_window_automation_launch.py tests/analysis_regression/golden/test_analysis_regression_compare.py -q --tb=short
uv run python -m pytest tests/e2e -n 3 -q -k 'results-values or reviewer-predictions or (manuscript-export and not split)'
```

The hosted Windows R-stack checks on `e2d669bd` passed R CMD check, all 103 independent authority cases, 21 Reitsma visual cases, nine bridge tests and the frozen comparison. [Hosted R-stack transcript](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/44574508738/job/135738528061).

The follow-up report check distinguishes the overall t-test heading, which includes its reported degrees of freedom, from the subgroup t heading. All seven affected desktop scenarios passed after strict typing. [Inference and report checks](../qualification/ratio-precision-inference-checks.log).

```powershell
uv run python -m pytest tests/e2e -n 3 -q -k 'options-binary or options-continuous or options-diagnostic or results-values or reviewer-predictions or (manuscript-export and not split)'
```
