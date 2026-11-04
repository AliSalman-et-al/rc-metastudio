#!/usr/bin/env bash
set -euo pipefail
source artifacts/statistical-mutants/env.sh
proof=$PWD/artifacts/statistical-mutants/ci-integration
export R_LIBS="$proof/base-library:$R_LIBS"
(set -x; python "$proof/prove.py") > "$proof/restored.log" 2>&1
cp artifacts/verification/rcms/authorities.json "$proof/restored.json"
