#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
export DISPLAY="${DISPLAY:-:0}"
replay_id="$(date -u +%Y%m%dT%H%M%SZ)"
export RCMS_AUDIT_DIR="$PWD/docs/ux-audit/2026-10-16-round6-release-fixes/raw/replay-$replay_id"
mkdir -p "$RCMS_AUDIT_DIR/raw"
record() { uv run python docs/ux-audit/2026-10-14-round3/run.py "$@"; }
record reinstall uv run python docs/ux-audit/2026-10-14-round3/install_source.py
record doctor uv run python scripts/verify_rcms.py doctor --native
record headers uv run python scripts/run_with_timeout.py --timeout-seconds 900 --label headers -- uv run python docs/ux-audit/2026-10-16-round6-release-fixes/native.py "headers-replay-$replay_id"
record presentation uv run python scripts/run_with_timeout.py --timeout-seconds 600 --label presentation -- uv run python docs/ux-audit/2026-10-16-round6-release-fixes/native.py "presentation-replay-$replay_id"
record small-screen uv run python docs/ux-audit/2026-10-16-round6-release-fixes/native.py "small-screen-replay-$replay_id"
for scenario in project-release-coefficients calculator-mode-back-continuous calculator-mode-back-binary project-axis-proportions calculator-ratio-precision; do
    record "$scenario" uv run python scripts/verify_rcms.py "$scenario" --native
done
capture="build/qt6-verification/golden-compatibility-release-$replay_id"
record golden uv run python scripts/verify_golden_compatibility.py --output-root "$capture"
record numerical uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture "$capture"
record full uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh
printf 'Replay receipts: %s\n' "$RCMS_AUDIT_DIR"
