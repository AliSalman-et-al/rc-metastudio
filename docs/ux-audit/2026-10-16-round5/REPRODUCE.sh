#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
export RCMS_AUDIT_DIR="$PWD/docs/ux-audit/2026-10-16-round5"
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
uv run python docs/ux-audit/2026-10-14-round3/run.py replay-install uv run python docs/ux-audit/2026-10-14-round3/install_source.py
for scenario in doctor audit-round3-round5 audit-round3-bubble-metrics audit-round3-irr-context audit-round3-precision review1-design audit-round3-hr audit-round3-irr audit-round3-presentation-twoarm-mean audit-round3-presentation-diagnostic plot-workflow-forest plot-workflow-regression plot-workflow-coefficient plot-workflow-funnel plot-workflow-deeks; do
  uv run python docs/ux-audit/2026-10-14-round3/run.py "replay-$scenario" uv run python scripts/verify_rcms.py "$scenario" --native
done
for factor in 1.25 1.5 2; do
  QT_SCALE_FACTOR="$factor" uv run python docs/ux-audit/2026-10-14-round3/run.py "replay-scale-$factor" uv run python scripts/verify_rcms.py review1-design --native
done
for scenario in calculator-mode-entered-binary calculator-mode-pre-post calculator-mode-back-diagnostic; do
  QT_SCALE_FACTOR=1.5 uv run python docs/ux-audit/2026-10-14-round3/run.py "replay-$scenario" uv run python scripts/verify_rcms.py "$scenario" --native
done
uv run python docs/ux-audit/2026-10-14-round3/run.py replay-full uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh
uv run python docs/ux-audit/2026-10-14-round3/run.py replay-numerical uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-r-stack-v2
uv run python docs/ux-audit/2026-10-14-round3/collect_runs.py --since df71e82
