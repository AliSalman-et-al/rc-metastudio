# Run from C:\Users\Ali-Salman\Documents\Code\rc-metastudio.
# These are the successful runtime configuration and finishing commands.
# Log files preserve individual unsuccessful attempts and their diagnostics.
# Use a fresh log destination when replaying so historical failed attempts remain.
$evidence = 'docs/ux-audit/2026-10-13-implementation'
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
$env:RCMS_R_HOME = (Resolve-Path 'build/windows-package/dist/RCMetaStudio/R').Path
$env:RCMS_R_LIBS = (Resolve-Path 'docs/ux-audit/2026-10-13-native/runtime-library').Path
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path 'build/qt6-verification').Path
$env:R_HOME = $env:RCMS_R_HOME
$env:R_LIBS = $env:RCMS_R_LIBS
$env:R_LIBS_USER = $env:RCMS_R_LIBS
$env:PATH = "$env:RCMS_R_HOME/bin;$env:PATH"
$env:RCMS_R_STACK_REQUIRED = '1'

uv run python scripts/verify_rcms.py doctor *> "$evidence/finish-doctor.log"

# Together these two selections cover every node under tests/. R bridge drivers
# remain serial; desktop children use offscreen and retain their own evidence.
uv run python -m pytest tests --ignore=tests/r_stack -q -ra -n 2 --dist loadfile --durations=10 *> "$evidence/finish-full-suite.log"
# After the sole failure was traced to an incomplete parser-error fixture,
# 3cacb3d corrected that fixture and every non-desktop node was run again.
uv run python -m pytest tests --ignore=tests/r_stack --ignore=tests/e2e -q -ra -n 2 --dist loadfile --durations=10 *> "$evidence/finish-non-desktop-recheck.log"
uv run python -m pytest tests/r_stack -q -ra --durations=10 *> "$evidence/finish-r-stack.log"

uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path . --extra-search-path src/rc_metastudio --extra-search-path src --extra-search-path scripts --extra-search-path tests/python/gui src/rc_metastudio scripts tests r/RCMetaR/inst/qa *> "$evidence/finish-typing-final.log"

# Native runs must be serial on the shared display. File picker return paths in
# the desktop driver are test-owned substitutions, not native picker proof.
uv run python scripts/verify_rcms.py ux-improvements --native *> "$evidence/finish-native-ux.log"
# Repeated on the committed implementation after the import/type/comment cleanup.
uv run python scripts/verify_rcms.py ux-improvements --native *> "$evidence/finish-native-ux-committed.log"
$env:QT_SCALE_FACTOR = '2'
uv run python scripts/verify_rcms.py ux-improvements --native *> "$evidence/finish-native-ux-200.log"
Remove-Item Env:QT_SCALE_FACTOR
uv run python scripts/verify_rcms.py project-table-covariates --native *> "$evidence/finish-native-grid-copy.log"
uv run python scripts/verify_rcms.py analysis-data-onearm-proportion --native *> "$evidence/finish-native-onearm-proportion.log"

# The supplemental evidence script needs the repository on sys.path and the same
# real-runtime load flag as verify_rcms.py. Its run is routing/rendering proof,
# not an independent numerical oracle. An absolute executable is needed on Windows.
$env:QT_QPA_PLATFORM = 'windows'
$env:PYTHONPATH = (Get-Location).Path
$env:RCMS_REQUIRE_IN_PROCESS_RPY2 = '1'
$probePython = (Resolve-Path .venv/Scripts/python.exe).Path
uv run python scripts/run_with_timeout.py --timeout-seconds 120 --label 'UX mean regression' -- $probePython "$evidence/supplemental-drive.py" onearm-mean meta-regression *> "$evidence/finish-native-mean-regression-recheck.log"
uv run python "$evidence/clipboard-probe.py" *> "$evidence/finish-clipboard-probe.log"
Remove-Item Env:QT_QPA_PLATFORM

# Run after the desktop suite ends. Fixed original run IDs document this session;
# the collector checks their original manifest hashes before retaining bundles.
uv run python "$evidence/collect-finish-evidence.py"
