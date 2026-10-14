#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
uv run python docs/ux-audit/2026-10-14-round3/install_source.py
uv run python scripts/verify_rcms.py doctor --native
uv run python docs/ux-audit/2026-10-14-round3/run.py full-reproduce uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh
uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-r-stack-v2
export RCMETASTUDIO_QA_ROOT="$PWD/artifacts/verification/rcms/forest-visual-round3-$(date -u +%Y%m%dT%H%M%SZ)"
uv run python docs/ux-audit/2026-10-14-round3/run.py forest-visual-reproduce "$RCMS_R_HOME/bin/Rscript" r/RCMetaR/inst/qa/render_forest_visual_qa.R
uv run python docs/ux-audit/2026-10-14-round3/validate_forest.py "$RCMETASTUDIO_QA_ROOT"
bash docs/ux-audit/2026-10-14-round3/NATIVE.sh
uv run python docs/ux-audit/2026-10-14-round3/curate.py
