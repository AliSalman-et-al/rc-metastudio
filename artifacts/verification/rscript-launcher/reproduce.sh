#!/bin/bash
set -eu
packaged=/home/ali/Documents/Code/rc-metastudio/build/linux-package/work/qualification/extracted/RCMetaStudio-linux-x64/R
unreduced=/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home
for home in "$packaged" "$unreduced"; do
  echo "Runtime: $home"
  "$home/bin/Rscript" -e 'cat(commandArgs(TRUE))' a b
  echo
 done
file "$packaged/bin/Rscript"
cat "$packaged/bin/Rscript"
printf 'cat(commandArgs(TRUE))\n' > /tmp/rcms-rscript-before.R
"$packaged/bin/R" --vanilla --slave -f /tmp/rcms-rscript-before.R --args a b
echo
