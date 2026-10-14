param([switch]$FullBootstrap)
$ErrorActionPreference = 'Stop'
. ./docs/ux-audit/2026-10-14-round2/ENV.ps1
function Invoke-Review2([string]$Label, [string[]]$Command) {
    uv run python docs/ux-audit/2026-10-14-round2/run.py "review2-reproduce-$Label" @Command
    if ($LASTEXITCODE) { throw "$Label failed with exit $LASTEXITCODE" }
}
Invoke-Review2 'sync' @('uv', 'sync', '--locked')
Invoke-Review2 'forms' @('uv', 'run', 'python', 'scripts/build_qt6.py', 'generate', '--build-root', 'build/qt6-verification')
Invoke-Review2 'install' @("$env:RCMS_R_HOME/bin/R.exe", 'CMD', 'INSTALL', "--library=$env:RCMS_R_LIBS", 'r/RCMetaR')
Invoke-Review2 'doctor' @('uv', 'run', 'python', 'scripts/verify_rcms.py', 'doctor')
$review2Capture = 'build/qt6-verification/golden-compatibility-review2-reproduce'
Invoke-Review2 'golden' @('uv', 'run', 'python', 'scripts/verify_golden_compatibility.py', '--output', $review2Capture)
Invoke-Review2 'python' @('uv', 'run', 'python', 'scripts/run_with_timeout.py', '--timeout-seconds', '600', '--label', 'review2-python', '--', 'uv', 'run', 'python', '-m', 'pytest', 'tests', '--ignore=tests/r_stack', '--ignore=tests/e2e', '-q', '-ra', '--durations=10')
Invoke-Review2 'typing' @('uv', 'run', 'ty', 'check', '--extra-search-path', 'build/qt6-verification/generated/rc_metastudio', '--extra-search-path', 'build/qt6-verification/generated/rc_metastudio/forms', '--extra-search-path', '.', '--extra-search-path', 'src/rc_metastudio', '--extra-search-path', 'src', '--extra-search-path', 'scripts', '--extra-search-path', 'tests/python/gui', 'src/rc_metastudio', 'scripts', 'tests', 'r/RCMetaR/inst/qa')
Invoke-Review2 'package' @('uv', 'run', 'python', 'docs/ux-audit/2026-10-14-round2/package_check.py')
if ($FullBootstrap) {
    Invoke-Review2 'full' @('uv', 'run', 'python', '.agents/skills/verify-rcms/scripts/verify_all.py', '--full')
} else {
    Invoke-Review2 'versions' @('uv', 'run', 'python', 'scripts/validate_rcmetar_r_manifests.py', '--root', '.', '--report-installed-versions', '--rscript', "$env:RCMS_R_HOME/bin/Rscript.exe")
    Invoke-Review2 'bridge' @('uv', 'run', 'python', '-m', 'pytest', 'tests/r_stack', '-q', '-ra', '--durations=10')
    Invoke-Review2 'desktop' @('uv', 'run', 'python', '-m', 'pytest', 'tests/e2e', '-q', '-ra', '--durations=10', '--dist', 'loadfile', '-n', '2')
    Invoke-Review2 'reitsma' @('uv', 'run', 'python', 'docs/ux-audit/2026-10-14-round2/reitsma_check.py')
}
Invoke-Review2 'authorities' @("$env:RCMS_R_HOME/bin/Rscript.exe", '.agents/skills/verify-rcms/scripts/analysis_authorities.R', 'docs/ux-audit/2026-10-14-round2/raw/review2-reproduce-authorities-results.json')
Invoke-Review2 'equivalence' @('uv', 'run', 'python', 'docs/ux-audit/2026-10-14-round2/numerical_equivalence.py', '--capture', $review2Capture, '--authorities', 'docs/ux-audit/2026-10-14-round2/raw/review2-reproduce-authorities-results.json')
$env:RCMETASTUDIO_QA_ROOT = (Join-Path (Get-Location) 'artifacts/verification/rcms/forest-review2-reproduce')
Invoke-Review2 'forest-matrix' @("$env:RCMS_R_HOME/bin/Rscript.exe", 'r/RCMetaR/inst/qa/render_forest_visual_qa.R')
Invoke-Review2 'forest-validation' @('uv', 'run', 'python', 'docs/ux-audit/2026-10-14-round2/validate_forest.py', $env:RCMETASTUDIO_QA_ROOT, 'docs/ux-audit/2026-10-14-round2/raw/review2-reproduce-forest-validation.json')
$review2Scenarios = @('amino', 'continuous', 'analysis-amino-binary-subgroup', 'analysis-amino-binary-cumulative', 'analysis-amino-binary-leave-one-out', 'review-workflows', 'plot-workflow-forest', 'lymph', 'analysis-data-onearm-proportion', 'analysis-data-twoarm-mean')
foreach ($review2Scenario in $review2Scenarios) {
    Invoke-Review2 "native-$review2Scenario" @('uv', 'run', 'python', 'scripts/verify_rcms.py', $review2Scenario, '--native')
}
uv run python docs/ux-audit/2026-10-14-round2/review_screenshots.py review2-reproduce-native --review review2 --scenarios amino continuous analysis-amino-binary-subgroup analysis-amino-binary-cumulative analysis-amino-binary-leave-one-out review-workflows plot-workflow-forest analysis-data-onearm-proportion analysis-data-twoarm-mean
if ($LASTEXITCODE) { throw 'Native screenshot curation failed' }
