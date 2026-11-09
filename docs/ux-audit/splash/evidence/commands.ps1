# From repository root; this Windows host uses system scale 125%.
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
uv run python -c "from scripts.verify import run_typing; from pathlib import Path; run_typing(Path('build/qt6-verification'))" 2>&1 | Tee-Object docs/ux-audit/splash/evidence/typing.log
uv run python -m pytest tests/python/gui/test_compact_transient_layout.py tests/python/gui/test_main_window_automation_launch.py -q -W error 2>&1 | Tee-Object artifacts/splash-review-gui.log
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path build/qt6-verification).Path
$env:RCMS_R_HOME = 'C:/Program Files/R/R-4.6.1'
$env:RCMS_R_LIBS = (Resolve-Path build/splash-r-library).Path
$env:QT_SCALE_FACTOR = '0.8'
uv run python scripts/run_with_timeout.py --timeout-seconds 120 --label 'Startup failure review' -- uv run python tests/e2e/startup_splash_driver.py --failure --output artifacts/splash-review-failure 2>&1 | Tee-Object artifacts/splash-review-failure.log
uv run python tests/e2e/startup_splash_driver.py --output artifacts/splash-review-100 2>&1 | Tee-Object artifacts/splash-review-100.log
$env:QT_SCALE_FACTOR = '1.6'
uv run python tests/e2e/startup_splash_driver.py --output artifacts/splash-review-200 2>&1 | Tee-Object artifacts/splash-review-200.log
# Copy only the review captures/observations, leaving runtime output in artifacts/.
Copy-Item artifacts/splash-review-failure/failure-desktop.png,artifacts/splash-review-failure/observations.json docs/ux-audit/splash/evidence/native-failure -Force
Copy-Item artifacts/splash-review-100/r-library-metafor-start.png,artifacts/splash-review-100/observations.json docs/ux-audit/splash/evidence/native-100 -Force
Copy-Item artifacts/splash-review-200/r-library-metafor-start.png,artifacts/splash-review-200/observations.json docs/ux-audit/splash/evidence/native-200 -Force
# Artwork generation and comparison:
# uv run python scripts/build_splash_artwork.py
# uv run python docs/ux-audit/splash/compare_artwork.py
