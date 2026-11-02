#!/bin/bash
set -eu
repo=$(pwd)
evidence="$repo/artifacts/verification/rscript-launcher"
packaged=/home/ali/Documents/Code/rc-metastudio/build/linux-package/work/qualification/extracted/RCMetaStudio-linux-x64/R
original=/home/ali/Documents/Code/rc-metastudio/build/linux-package/work/r-extract/opt/R/4.6.1/lib/R
scratch=$(mktemp -d /tmp/rcms-rscript-proof.XXXXXX)
echo "Scratch: $scratch"
cp -a "$packaged" "$scratch/R"
# Restore the two upstream launchers consumed by the relocation build step.
cp "$original/bin/R" "$original/bin/Rscript" "$scratch/R/bin/"
python3 scripts/configure_linux_r_launchers.py "$scratch/R"
"$scratch/R/bin/Rscript" -e 'cat(commandArgs(TRUE))' a b
echo
"$scratch/R/bin/Rscript" -e 'stopifnot(identical(commandArgs(TRUE), c("a b", "", "--flag"))); cat(R.home(), "quoted arguments OK\n")' 'a b' '' --flag
"$scratch/R/bin/Rscript" tests/e2e/rm5_reference.R tests/fixtures/rm5/Fleiss1993.rm5 "$evidence/data.csv" "$evidence/results.csv"
cat "$evidence/results.csv"
sha256sum "$packaged/bin/Rscript" "$original/bin/Rscript" "$scratch/R/bin/Rscript.real"
