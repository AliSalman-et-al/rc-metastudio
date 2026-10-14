#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
label_prefix="${1:-native-final}"
for family in onearm-proportion onearm-mean reg-coef generic-effect twoarm-proportion twoarm-mean twoarm-smd diagnostic hr irr references precision; do
  uv run python docs/ux-audit/2026-10-14-round3/run.py "$label_prefix-$family" uv run python scripts/verify_rcms.py "audit-round3-$family" --native
done
