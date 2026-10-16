#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
export DISPLAY=:0
for family in onearm-proportion onearm-mean reg-coef generic-effect twoarm-proportion; do
 uv run python docs/ux-audit/2026-10-14-round3-reaudit/run.py "matrix-retry-$family" uv run python scripts/run_with_timeout.py --timeout-seconds 600 --label "native matrix retry $family" -- uv run python docs/ux-audit/2026-10-14-round3-reaudit/native_matrix.py "$family"
done
uv run python docs/ux-audit/2026-10-14-round3-reaudit/run.py shell-retry uv run python scripts/run_with_timeout.py --timeout-seconds 120 --label 'native shell retry' -- uv run python docs/ux-audit/2026-10-14-round3-reaudit/native_shell.py
uv run python docs/ux-audit/2026-10-14-round3-reaudit/run.py native-extra-retry uv run python scripts/run_with_timeout.py --timeout-seconds 600 --label 'native variant retry' -- uv run python docs/ux-audit/2026-10-14-round3-reaudit/native_extra.py
