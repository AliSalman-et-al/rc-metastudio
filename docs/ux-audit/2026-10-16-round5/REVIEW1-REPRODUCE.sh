#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
export RCMS_AUDIT_DIR="$PWD/docs/ux-audit/2026-10-16-round5"
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
uv run python docs/ux-audit/2026-10-14-round3/run.py review1-replay-install uv run python docs/ux-audit/2026-10-14-round3/install_source.py
for scenario in review1-design audit-round3-arm-names audit-round3-round5 audit-round3-irr-context plot-workflow-forest plot-workflow-cumulative plot-workflow-leave-one-out plot-workflow-subgroup plot-workflow-regression plot-workflow-sroc plot-workflow-coefficient plot-workflow-funnel plot-workflow-contour plot-workflow-trimfill plot-workflow-deeks; do
  uv run python docs/ux-audit/2026-10-14-round3/run.py "review1-replay-$scenario" uv run python scripts/verify_rcms.py "$scenario" --native
done
uv run python docs/ux-audit/2026-10-14-round3/run.py review1-replay-full uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh
uv run python docs/ux-audit/2026-10-14-round3/run.py review1-replay-numerical uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-r-stack-v2
uv run python docs/ux-audit/2026-10-14-round3/collect_full_profile.py review1-replay-full
uv run python docs/ux-audit/2026-10-16-round5/review1_collect.py
