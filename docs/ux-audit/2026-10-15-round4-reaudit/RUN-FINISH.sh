#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
export DISPLAY=:0
for scenario in review-workflows ux-improvements editing csv project-structure project-table-covariates calculator-binary calculator-continuous calculator-diagnostic calculator-mode-binary-metrics calculator-mode-continuous-metrics calculator-mode-diagnostic-metrics calculator-mode-onearm-proportion calculator-mode-onearm-mean calculator-mode-entered-binary calculator-mode-entered-continuous calculator-mode-entered-diagnostic calculator-mode-pre-post calculator-mode-back-binary calculator-mode-back-continuous calculator-mode-back-diagnostic plot-workflow-forest plot-workflow-cumulative plot-workflow-leave-one-out plot-workflow-subgroup plot-workflow-regression plot-workflow-sroc plot-workflow-coefficient plot-workflow-funnel plot-workflow-contour plot-workflow-trimfill plot-workflow-deeks audit-round3-presentation-sequential audit-round3-presentation-transforms; do
 if uv run python -c 'import json,sys; from pathlib import Path; p=Path(sys.argv[1]); sys.exit(0 if p.exists() and json.loads(p.read_text())["exit_code"]==0 else 1)' "docs/ux-audit/2026-10-15-round4-reaudit/raw/helper-$scenario.json"; then continue; fi
 uv run python docs/ux-audit/2026-10-15-round4-reaudit/run.py "helper-$scenario" uv run python scripts/verify_rcms.py "$scenario" --native
done
