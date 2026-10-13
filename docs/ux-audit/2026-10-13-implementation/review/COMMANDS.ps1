# Run from the repository root. ENV.ps1 selects test-owned runtime/library paths.
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
. ./docs/ux-audit/2026-10-13-implementation/review/ENV.ps1
Get-ChildItem -LiteralPath docs/ux-audit/2026-10-13-native/runtime-library -Directory |
    Where-Object Name -ne 'RCMetaR' | Copy-Item -Destination $reviewLibrary -Recurse -Force
& (Join-Path $env:RCMS_R_HOME 'bin/R.exe') CMD INSTALL --library=$reviewLibrary r/RCMetaR
uv run python scripts/verify_rcms.py doctor

# The initial full selection and the final disjoint selections cover tests/.
uv run python -m pytest tests --ignore=tests/r_stack -q -ra -n 2 --dist loadfile --durations=10
uv run python -m pytest tests --ignore=tests/r_stack --ignore=tests/e2e -q -ra -n 2 --dist loadfile --durations=10
uv run python scripts/verify.py r-stack --r-runtime-root $env:RCMS_R_HOME
& (Join-Path $env:RCMS_R_HOME 'bin/Rscript.exe') .agents/skills/verify-rcms/scripts/analysis_authorities.R "$reviewEvidence/authorities.json"
$env:RCMETASTUDIO_QA_ROOT = Join-Path (Get-Location) "$reviewEvidence/forest-visual"
& (Join-Path $env:RCMS_R_HOME 'bin/Rscript.exe') r/RCMetaR/inst/qa/render_forest_visual_qa.R

$reviewScenarios = @('amino', 'analysis-amino-binary-cumulative',
    'analysis-amino-binary-leave-one-out', 'analysis-amino-binary-subgroup',
    'analysis-amino-binary-meta-regression', 'analysis-data-onearm-proportion',
    'continuous', 'analysis-diagnostic-joint', 'analysis-data-onearm-mean',
    'analysis-data-reg-coef', 'analysis-data-generic-effect',
    'analysis-diagnostic-regression-multiple')
foreach ($reviewScenario in $reviewScenarios) {
    uv run python scripts/verify_rcms.py $reviewScenario --native
}
$env:QT_SCALE_FACTOR = '1.25'
uv run python scripts/verify_rcms.py ux-improvements --native
Remove-Item Env:QT_SCALE_FACTOR

uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path . --extra-search-path src/rc_metastudio --extra-search-path src --extra-search-path scripts --extra-search-path tests/python/gui src/rc_metastudio scripts tests r/RCMetaR/inst/qa
# Native logs supply the original proof paths to this hash-checking collector.
uv run python docs/ux-audit/2026-10-13-implementation/review/collect.py
