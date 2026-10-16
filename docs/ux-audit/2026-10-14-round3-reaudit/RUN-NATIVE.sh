#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
export DISPLAY=:0
uv run python docs/ux-audit/2026-10-14-round3-reaudit/run_all.py
