#!/usr/bin/env bash
set -euo pipefail
source artifacts/statistical-mutants/env.sh
proof=$PWD/artifacts/statistical-mutants/ci-integration
(set -x; git apply tests/mutants/ci-z-instead-of-t.patch) > "$proof/mutant-apply.log" 2>&1
trap 'git apply -R tests/mutants/ci-z-instead-of-t.patch' EXIT
mkdir -p "$proof/mutant-library"
(set -x; R CMD INSTALL -l "$proof/mutant-library" r/RCMetaR) > "$proof/mutant-install.log" 2>&1
export R_LIBS="$proof/mutant-library:$R_LIBS"
set +e
(set -x; python "$proof/prove.py") > "$proof/mutant.log" 2>&1
status=$?
set -e
echo "Installed mutant authority step exit=$status" | tee "$proof/mutant-status.txt"
test "$status" -ne 0
