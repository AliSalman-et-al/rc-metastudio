UI=/home/ali/.t3/qa-env/tools/ui.py
PY=/home/ali/.t3/qa-env/tools/venv/bin/python
u() { "$PY" "$UI" --session batch5 "$@"; }
u type abc
u key Tab Tab
u shot "$PWD/artifacts/qa-r1/batch5/dark-invalid.png"
u click 488 380 --double
u key ctrl+a
u type -1
u key Tab Tab
u shot "$PWD/artifacts/qa-r1/batch5/dark-negative.png"
u click 488 380 --double
u key ctrl+a
u type 60
u key Tab
u shot "$PWD/artifacts/qa-r1/batch5/dark-corrected.png"
u key Escape
u click 215 58
u shot /tmp/menu.png
