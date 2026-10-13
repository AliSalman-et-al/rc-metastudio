param([string]$LabelPrefix = 'review1-final-native')
$ErrorActionPreference = 'Stop'
. ./docs/ux-audit/2026-10-14-round2/ENV.ps1
$reviewNativeScenarios = @('amino', 'continuous', 'analysis-data-onearm-proportion',
    'analysis-amino-binary-subgroup', 'analysis-amino-binary-cumulative',
    'analysis-amino-binary-leave-one-out', 'analysis-amino-binary-meta-regression',
    'analysis-continuous-cumulative', 'analysis-continuous-leave-one-out',
    'analysis-continuous-subgroup', 'lymph', 'analysis-diagnostic-joint',
    'review-workflows', 'plot-workflow-forest')
foreach ($reviewNativeScenario in $reviewNativeScenarios) {
    uv run python docs/ux-audit/2026-10-14-round2/run.py "$LabelPrefix-$reviewNativeScenario" uv run python scripts/verify_rcms.py $reviewNativeScenario --native
    if ($LASTEXITCODE) { throw "$reviewNativeScenario failed" }
}
uv run python docs/ux-audit/2026-10-14-round2/run.py "$LabelPrefix-raw" uv run python scripts/verify_rcms.py analysis-data-twoarm-mean --native
if ($LASTEXITCODE) { throw 'Raw continuous native scenario failed' }
uv run python docs/ux-audit/2026-10-14-round2/review_screenshots.py $LabelPrefix
if ($LASTEXITCODE) { throw 'Native curation failed' }
