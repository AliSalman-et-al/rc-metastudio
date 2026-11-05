#!/bin/bash
set -e
cd /home/ali/.t3/worktrees/rc-metastudio/t3-a32e1ada
UI=(/home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session "$1")
shift
"${UI[@]}" "$@" >> artifacts/qa-batch6/commands.log 2>&1
