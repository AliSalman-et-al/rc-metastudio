#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
export RCMS_AUDIT_DIR="$PWD/docs/ux-audit/2026-10-16-round6"
export DISPLAY="${DISPLAY:-:0}"
record() { uv run python docs/ux-audit/2026-10-14-round3/run.py "$@"; }
record reinstall uv run python docs/ux-audit/2026-10-14-round3/install_source.py
for mode in binary-metrics continuous-metrics diagnostic-metrics onearm-proportion onearm-mean entered-binary entered-continuous entered-diagnostic pre-post back-binary back-continuous back-diagnostic; do
    record "native-$mode" uv run python scripts/verify_rcms.py "calculator-mode-$mode" --native
done
for scenario in calculator-grid-precision calculator-ratio-precision project-display-labels project-round6-polish project-axis-proportions project-axis-others project-axis-sequential audit-round3-round5 audit-round3-arm-names plot-workflow-regression plot-workflow-funnel plot-workflow-contour plot-workflow-trimfill audit-round3-presentation-transforms audit-round3-presentation-diagnostic project-shell; do
    record "native-$scenario" uv run python scripts/verify_rcms.py "$scenario" --native
done
for scale in 1.5 2; do
    record "native-design-$scale" env QT_SCALE_FACTOR="$scale" uv run python scripts/verify_rcms.py review1-design --native
done
record full-qualified-5 uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh
uv run python docs/ux-audit/2026-10-14-round3/collect_full_profile.py full-qualified-5
record numeric-qualified uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-r-stack-v2
uv run python docs/ux-audit/2026-10-16-round6/select_native.py
uv run python docs/ux-audit/2026-10-16-round6/curate.py
uv run python docs/ux-audit/2026-10-16-round6/collect.py
uv run python docs/ux-audit/2026-10-16-round6/axis_title_geometry.py
uv run python docs/ux-audit/2026-10-16-round6/integrity.py
