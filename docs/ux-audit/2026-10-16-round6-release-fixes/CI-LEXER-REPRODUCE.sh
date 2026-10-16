#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
export RCMS_AUDIT_DIR="$PWD/docs/ux-audit/2026-10-16-round6-release-fixes/raw/lexer-replay-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RCMS_AUDIT_DIR/raw"
record() { uv run python docs/ux-audit/2026-10-14-round3/run.py "$@"; }
record lexer uv run pytest tests/python/fast/test_code_health.py -q
record baseline uv run --no-sync python scripts/code_health.py --base 8b7796bcc840c3505c5fb0a1328cdd7682880e48 --head 8b7796bcc840c3505c5fb0a1328cdd7682880e48 --allow-fail --output artifacts/code-health/baseline.json --report artifacts/code-health/baseline.txt
record code-health uv run --no-sync python scripts/code_health.py --base e64695b04b4772617a966c1c2d3d63507dff61a7 --head HEAD --baseline artifacts/code-health/baseline.json --output artifacts/code-health/lexer-replay.json --report artifacts/code-health/lexer-replay.txt
record typing uv run ty check --python-platform win32 --extra-search-path build/qt6-verification/generated/rc_metastudio --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path . --extra-search-path src/rc_metastudio --extra-search-path src --extra-search-path scripts --extra-search-path tests/python/gui src/rc_metastudio scripts tests r/RCMetaR/inst/qa
record source-tests env QT_QPA_PLATFORM=offscreen uv run pytest -W error tests/python/fast tests/python/gui tests/analysis_regression/golden/test_analysis_regression_compare.py tests/packaging/contract --dist loadfile -n 2 -q
record axis-text-render "$RCMS_R_HOME/bin/Rscript" docs/ux-audit/2026-10-16-round6-release-fixes/axis_text_probe.R "$RCMS_AUDIT_DIR/axis-text"
record axis-parser uv run python docs/ux-audit/2026-10-16-round6-release-fixes/axis_text_probe.py "$RCMS_AUDIT_DIR/axis-text"
record install uv run python docs/ux-audit/2026-10-14-round3/install_source.py
capture="build/qt6-verification/golden-compatibility-lexer-replay-$(date -u +%Y%m%dT%H%M%SZ)"
record golden uv run python scripts/verify_golden_compatibility.py --output-root "$capture"
record numerical uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture "$capture"
for scenario in doctor project-axis-sequential project-reviewer-predictions analysis-diagnostic-joint project-release-coefficients plot-workflow-funnel plot-workflow-regression review1-design audit-round3-arm-names audit-round3-generic-effect; do
  record "native-$scenario" uv run python scripts/verify_rcms.py "$scenario" --native
done
record full uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh
record numerical-full uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-r-stack-v2
