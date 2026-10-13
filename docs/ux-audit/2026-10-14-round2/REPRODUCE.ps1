$ErrorActionPreference = 'Stop'
. ./docs/ux-audit/2026-10-14-round2/ENV.ps1
uv sync --locked
if ($LASTEXITCODE) { throw 'Environment sync failed' }
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
if ($LASTEXITCODE) { throw 'Qt form generation failed' }
$reviewRunner = 'docs/ux-audit/2026-10-14-round2/run.py'
function Invoke-ReviewCheck([string]$Label, [string[]]$Command) {
    uv run python $reviewRunner $Label @Command
    if ($LASTEXITCODE) { throw "$Label failed with exit $LASTEXITCODE" }
}
Invoke-ReviewCheck 'install' @("$env:RCMS_R_HOME/bin/R.exe", 'CMD', 'INSTALL', "--library=$env:RCMS_R_LIBS", 'r/RCMetaR')
Invoke-ReviewCheck 'doctor' @('uv', 'run', 'python', 'scripts/verify_rcms.py', 'doctor')
Invoke-ReviewCheck 'python' @('uv', 'run', 'python', '-m', 'pytest', 'tests', '--ignore=tests/r_stack', '--ignore=tests/e2e', '-q', '-ra', '--durations=10')
Invoke-ReviewCheck 'golden' @('uv', 'run', 'python', 'scripts/verify_golden_compatibility.py', '--output', 'build/qt6-verification/golden-compatibility-review1-reproduce')
Invoke-ReviewCheck 'desktop' @('uv', 'run', 'python', '-m', 'pytest', 'tests/e2e', '-q', '-ra', '--durations=10', '--dist', 'loadfile', '-n', '2')
Invoke-ReviewCheck 'r-stack' @('uv', 'run', 'python', 'scripts/verify.py', 'r-stack')
Invoke-ReviewCheck 'package' @('uv', 'run', 'python', 'docs/ux-audit/2026-10-14-round2/package_check.py')
Invoke-ReviewCheck 'authorities' @("$env:RCMS_R_HOME/bin/Rscript.exe", '.agents/skills/verify-rcms/scripts/analysis_authorities.R', 'docs/ux-audit/2026-10-14-round2/raw/authorities-results.json')
Invoke-ReviewCheck 'new-quantities' @("$env:RCMS_R_HOME/bin/Rscript.exe", 'docs/ux-audit/2026-10-14-round2/output-authorities.R', 'docs/ux-audit/2026-10-14-round2/raw/new-quantities-results.json')
Invoke-ReviewCheck 'equivalence' @('uv', 'run', 'python', 'docs/ux-audit/2026-10-14-round2/numerical_equivalence.py', '--capture', 'build/qt6-verification/golden-compatibility-review1-reproduce')
$env:RCMETASTUDIO_QA_ROOT = (Join-Path (Get-Location) 'artifacts/verification/rcms/forest-review1-reproduce')
Invoke-ReviewCheck 'forest-matrix' @("$env:RCMS_R_HOME/bin/Rscript.exe", 'r/RCMetaR/inst/qa/render_forest_visual_qa.R')
Invoke-ReviewCheck 'forest-validation' @('uv', 'run', 'python', 'docs/ux-audit/2026-10-14-round2/validate_forest.py', $env:RCMETASTUDIO_QA_ROOT, 'docs/ux-audit/2026-10-14-round2/raw/forest-validation-reproduce.json')
