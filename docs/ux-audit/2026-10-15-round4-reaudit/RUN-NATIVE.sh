#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
export DISPLAY=:0
uv run python docs/ux-audit/2026-10-15-round4-reaudit/run.py native-design uv run python scripts/run_with_timeout.py --timeout-seconds 600 --label 'native design' -- uv run python docs/ux-audit/2026-10-15-round4-reaudit/native_design.py
for scenario in $(uv run python -c 'import runpy; print(" ".join(runpy.run_path("scripts/verify_rcms.py")["SCENARIOS"]))'); do
 uv run python docs/ux-audit/2026-10-15-round4-reaudit/run.py "helper-$scenario" uv run python scripts/verify_rcms.py "$scenario" --native
done
