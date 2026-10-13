param([ValidateSet('before','after','after-final')][string]$Phase = 'before')
. ./docs/ux-audit/2026-10-14-round2/ENV.ps1
$round2Scenarios = @('ux-improvements', 'amino', 'continuous',
    'analysis-data-onearm-proportion', 'analysis-data-onearm-mean', 'analysis-data-twoarm-mean',
    'analysis-data-reg-coef', 'analysis-data-generic-effect',
    'analysis-amino-binary-cumulative', 'analysis-amino-binary-leave-one-out',
    'analysis-amino-binary-subgroup', 'analysis-amino-binary-meta-regression',
    'analysis-diagnostic-joint', 'analysis-diagnostic-combined',
    'analysis-diagnostic-regression-multiple', 'calculator-diagnostic',
    'calculator-continuous', 'small-study-effects', 'project-structure',
    'plot-workflow-forest', 'plot-workflow-regression', 'plot-workflow-sroc')
foreach ($round2Scenario in $round2Scenarios) {
    uv run python docs/ux-audit/2026-10-14-round2/run.py "$Phase-native-$round2Scenario" uv run python scripts/verify_rcms.py $round2Scenario --native
}
