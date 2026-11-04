#!/bin/bash
set -e
cd /home/ali/.t3/worktrees/rc-metastudio/t3-8c6f70fc
source /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/build/sheets-baseline/ENV.sh
export RCMS_R_LIBS=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/build/sheets-r-library
export R_LIBS=$RCMS_R_LIBS R_LIBS_USER=$RCMS_R_LIBS RCMS_QT6_BUILD_ROOT=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/build/qt6-verification PYTHONPATH=$PWD/src:$PWD
/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/.venv/bin/python scripts/verify.py pre-push
