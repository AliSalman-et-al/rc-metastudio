#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
export DISPLAY=:0
for family in twoarm-proportion onearm-proportion onearm-mean reg-coef generic-effect twoarm-mean twoarm-smd diagnostic hr irr; do
 uv run python docs/ux-audit/2026-10-15-round4-reaudit/run.py "matrix-$family" uv run python scripts/run_with_timeout.py --timeout-seconds 600 --label "native matrix $family" -- uv run python docs/ux-audit/2026-10-15-round4-reaudit/native_matrix.py "$family"
done
