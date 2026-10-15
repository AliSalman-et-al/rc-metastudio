#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
export RCMS_AUDIT_DIR="$PWD/docs/ux-audit/2026-10-16-round6"
export DISPLAY="${DISPLAY:-:0}"
record() { uv run python docs/ux-audit/2026-10-14-round3/run.py "$@"; }
record reviewer-install-current uv run python docs/ux-audit/2026-10-14-round3/install_source.py
record reviewer-pft-authorities-current "$RCMS_R_HOME/bin/Rscript" docs/ux-audit/2026-10-16-round6/reviewer_authorities.R docs/ux-audit/2026-10-16-round6/REVIEWER-PFT-AUTHORITIES.json
record reviewer-predictions-visible-page uv run python scripts/verify_rcms.py project-reviewer-predictions --native
record reviewer-groups-plots-tab uv run python scripts/verify_rcms.py project-reviewer-groups --native
record reviewer-colours-current uv run python scripts/verify_rcms.py project-reviewer-colours --native
record reviewer-diagnostic-current uv run python scripts/verify_rcms.py project-round6-polish --native
record reviewer-funnel-current uv run python scripts/verify_rcms.py plot-workflow-funnel --native
record reviewer-bubble-current uv run python scripts/verify_rcms.py plot-workflow-regression --native
record reviewer-golden-current uv run python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-reviewer-current
record reviewer-numerical-current uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-reviewer-current
# Retain the owned temporary check and saved project before cleanup.
record reviewer-full-final env PYTEST_ADDOPTS=-x uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh &
profile_pid=$!
record reviewer-retain-r-check uv run python docs/ux-audit/2026-10-16-round6/reviewer_retain_check.py &
check_pid=$!
record reviewer-retain-project uv run python docs/ux-audit/2026-10-16-round6/reviewer_retain_project.py &
project_pid=$!
wait "$profile_pid"
wait "$check_pid"
wait "$project_pid"
record reviewer-numerical-full-profile uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-r-stack-v2
record reviewer-vector-footer-runtime env QT_QPA_PLATFORM=offscreen uv run python docs/ux-audit/2026-10-16-round6/reviewer_render_footers.py
uv run python docs/ux-audit/2026-10-14-round3/collect_full_profile.py reviewer-full-final
uv run python docs/ux-audit/2026-10-16-round6/reviewer_collect.py
uv run python docs/ux-audit/2026-10-16-round6/select_native.py
uv run python docs/ux-audit/2026-10-16-round6/reviewer_curate.py
uv run python docs/ux-audit/2026-10-16-round6/integrity.py
