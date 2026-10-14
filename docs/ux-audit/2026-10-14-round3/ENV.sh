#!/usr/bin/env bash
# Source from the repository root after establishing the test-owned runtime.
export RCMS_R_HOME="$PWD/build/ux-round3/r-home"
if [[ -d "$PWD/build/ux-round3/r-stack-retained-273bd6a" ]]; then
  export RCMS_R_LIBS="$PWD/build/ux-round3/r-stack-retained-273bd6a"
else
  export RCMS_R_LIBS="$PWD/build/ux-round3/r-library"
fi
export RCMS_QT6_BUILD_ROOT="$PWD/build/qt6-verification"
export R_HOME="$RCMS_R_HOME"
export R_LIBS="$RCMS_R_LIBS"
export R_LIBS_USER="$RCMS_R_LIBS"
export LD_LIBRARY_PATH="$RCMS_R_HOME/lib:$PWD/build/ux-round3/xcb/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PATH="$HOME/.local/bin:$RCMS_R_HOME/bin:$PATH"
