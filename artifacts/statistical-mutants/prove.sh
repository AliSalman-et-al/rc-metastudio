#!/usr/bin/env bash
set -eu
source artifacts/statistical-mutants/env.sh
root=artifacts/statistical-mutants
prove() {
  id=$1; shift
  for phase in base mutant restored; do
    set +e
    (set -x; if [ "$phase" = mutant ]; then python "$root/mutate.py" tests/mutants/"$id".patch "$@"; else "$@"; fi) > "$root/$id-$phase.log" 2>&1
    status=$?
    set -e
    echo "$id $phase exit=$status" | tee -a "$root/status.txt"
    if [ "$phase" = mutant ]; then test "$status" -ne 0; else test "$status" -eq 0; fi
  done
}
prove ci-z-instead-of-t Rscript .agents/skills/verify-rcms/scripts/analysis_authorities.R "$root/authority.json"
prove bridge-ci-width python scripts/verify_rcms.py sheets
prove xlsx-year-column python -m pytest tests/python/fast/test_csv_import.py -k unmapped -q
