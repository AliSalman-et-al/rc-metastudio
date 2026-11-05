#!/bin/bash
UI=/home/ali/.t3/qa-env/tools/ui.py
PY=/home/ali/.t3/qa-env/tools/venv/bin/python
u() { "$PY" "$UI" --session batch5 "$@"; }
u key ctrl+o
u type /home/ali/.t3/qa-env/src/sample_projects/continuous.rcms
u key Return Return
u click 20 184
u shot /tmp/b5.png
