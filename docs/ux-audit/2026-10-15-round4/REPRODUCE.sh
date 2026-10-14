#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
export RCMS_AUDIT_DIR="$PWD/docs/ux-audit/2026-10-15-round4"
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
uv run python docs/ux-audit/2026-10-14-round3/run.py reproduce-install uv run python docs/ux-audit/2026-10-14-round3/install_source.py
for family in generic-effect reg-coef diagnostic onearm-proportion twoarm-proportion twoarm-mean twoarm-smd sequential; do
  uv run python docs/ux-audit/2026-10-14-round3/run.py "reproduce-native-$family" uv run python scripts/verify_rcms.py "audit-round3-presentation-$family" --native
done
for scenario in audit-round3-precision audit-round3-hr audit-round3-irr calculator-binary calculator-continuous calculator-mode-pre-post calculator-mode-entered-binary calculator-mode-entered-continuous ux-improvements review-workflows project-table-covariates small-study-diagnostic plot-workflow-regression amino; do
  uv run python docs/ux-audit/2026-10-14-round3/run.py "reproduce-native-$scenario" uv run python scripts/verify_rcms.py "$scenario" --native
done
uv run python docs/ux-audit/2026-10-14-round3/run.py reproduce-full uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh
uv run python docs/ux-audit/2026-10-14-round3/run.py reproduce-numerical uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-r-stack-v2
uv run python docs/ux-audit/2026-10-14-round3/collect_runs.py --since 7938292
