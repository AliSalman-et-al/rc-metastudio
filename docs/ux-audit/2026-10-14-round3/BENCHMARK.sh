#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source docs/ux-audit/2026-10-14-round3/ENV.sh
evidence=docs/ux-audit/2026-10-14-round3
for iteration in 1 2 3 4 5; do
  for mode in before after; do
    label="tiff-reproduce-$mode-$iteration"
    uv run python "$evidence/run.py" "$label" /usr/bin/time -v -o "$evidence/raw/$label-time.txt" \
      "$RCMS_R_HOME/bin/Rscript" "$evidence/benchmark_tiff.R" "$evidence/TIFF-input.svg" \
      "$evidence/raw/$label.tiff" "$mode" "$evidence/raw/$label-result.json"
  done
done
uv run python "$evidence/compare_tiff.py" "$evidence/raw/tiff-reproduce-before-1.tiff" "$evidence/raw/tiff-reproduce-after-1.tiff"
