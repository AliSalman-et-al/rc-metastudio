# RC MetaStudio 0.6.0 local verification

## Runtime and replay

Windows x64, Python 3.14.10, Qt and PyQt 6.12.0, R 4.6.2, rpy2 3.6.9 and
Poppler 26.09.0. The [doctor transcript](doctor.log) links the runtime record,
installed statistical package versions and startup captures. RCMetaR was
installed from this checkout into a test-owned library. See the
[R source tree](r-source.txt) and [install transcript](install-fixes.log).

From the repository root, before GUI tests:

```powershell
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path build/qt6-verification).Path
uv run python -c "from scripts.verify import run_typing; from pathlib import Path; print(run_typing(Path('build/qt6-verification').resolve()))"
```

Use the pinned R 4.6.2 runtime and a test-owned library of the pinned
dependencies. For these runs, the runtime came from the installed 0.5.6
bundle and the seed library from the merged TSA qualification.

```powershell
$env:RCMS_R_HOME = "$env:USERPROFILE/Downloads/RCMetaStudio-0.5.6-windows-x64/R"
$env:RCMS_R_LIBS = (New-Item -ItemType Directory -Force .tmp/v060-r-library).FullName
Copy-Item .tmp/tsa-phase6-library/* -Exclude RCMetaR -Destination $env:RCMS_R_LIBS -Recurse -Force
$env:R_HOME = $env:RCMS_R_HOME
$env:R_LIBS = $env:R_LIBS_USER = $env:RCMS_R_LIBS
$env:Path = "$env:R_HOME/bin/x64;$env:R_HOME/bin;$(Resolve-Path .tmp/poppler-tsa/poppler-26.09.0/Library/bin);$env:Path"
$env:LC_ALL = '.UTF-8'
$env:QT_QPA_PLATFORM = 'offscreen'
$env:RCMS_R_STACK_REQUIRED = '1'
$env:PYTHONUNBUFFERED = '1'
$rscript = "$env:R_HOME/bin/Rscript.exe"
& $rscript --vanilla -e 'stopifnot(nzchar(Sys.setlocale("LC_CTYPE", ".UTF-8"))); install.packages("r/RCMetaR", repos=NULL, type="source"); cat(find.package("RCMetaR"), as.character(packageVersion("RCMetaR")), "\n")'
```

## Reproductions

- [Sheet strip before the fix](sheets-before.log) reproduced the width
  assertion with the pinned runtime. The original
  [attempt](../rcms/20261119T014408Z-3016382e-sheets/manifest.json) used system
  R 4.6.1 and timed out loading Matrix. The 0.5.5 polish in `88ccaf2e` made
  overflow tabs font-relative. The updated scenario checks widths from four to
  twelve font heights and still checks tab visibility and the complete tooltip.
- The [native resize reproduction](resize-before.log) failed all three plot
  tests with `QT_QPA_PLATFORM=windows` and `QT_SCALE_FACTOR=0.8`. Set
  test window geometry after Qt applies first-show sizing. The assertions
  respect the existing plot magnification and viewport constraints.
- The [native Python reproduction](python-native-before.log) recorded an access
  violation while opening the continuous calculator combo box. The binary
  [focused run](popup-binary-before.log) also reproduced a popup that never
  appeared. A stock Qt drop-down reproduced the invisibility across Windows
  styles in the [style matrix](popup-style-matrix.log). Disabling Qt's combo
  animation made it visible with both the stock style and the application proxy
  [in the same probe](popup-no-animation.log). Application startup now disables
  this effect on Windows. The native right-edge layout test checks popup
  visibility as well as bounds, scrolling and the complete tooltip.
- The [Results cleanup test failure](../tsa-phase6-merged/final/baseline/result-owner-exception.log)
  came from a test double missing the binary table model's
  `is_diagnostic()` method. The test now reaches the intended callback failure.
- The [initial R test run](r-before.log) inherited `C.UTF-8`, which this
  Windows R runtime rejected. Unicode assertions passed under test setup
  using the Windows `.UTF-8` locale.

## Qualification

All suite commands ran from the repository root. Test results record the
fixes applied to `9c1b695b42edd59bea2af41a69ad9fb3ad67e891`, before the
release metadata update. Commit `078d995d` records the tested fixes.

| Suite | Command | Result |
| --- | --- | --- |
| Strict typing | `run_typing` as shown above | Passed, [Win32 command and transcript](../typing/20261119T095155-8ffed73a/command.json) and [console output](typing-fixes.log) |
| Python, packaging, golden comparator tests and live R bridge | `uv run python -m pytest --strict-markers tests/python tests/analysis_regression tests/packaging tests/r_stack -q -ra --basetemp .tmp/v060-python-tests --junitxml=artifacts/verification/v0.6.0-local/python.xml` | [1,094 passed, 3 platform skips](python.log). Python 870 passed and 1 POSIX skip, comparator 68 passed, packaging 147 passed and 2 macOS skips, R bridge 9 passed. [JUnit report](python.xml) |
| Native GUI at Qt scale factor 0.8 | `uv run python -X faulthandler -m pytest --strict-markers tests/python/gui -q -ra --tb=short --basetemp .tmp/v060-native-tests --junitxml=artifacts/verification/v0.6.0-local/native-gui.xml` | [385 passed, 1 existing offscreen-only clipboard skip](native-gui.log) |
| R package | `Rscript --vanilla -e '<expression below>'` | [214 test blocks, 2,614 passed assertions, 15 warnings, zero failures, errors or skips](r-tests.log) |
| Qt Core | `./scripts/verify-qt6.ps1 -Section Core` | [322 passed, nine native probe and validation commands completed](qt-core-serial.log) |
| Qt RemainingSurfaces | `./scripts/verify-qt6.ps1 -Section RemainingSurfaces` | [64 passed, 10 native surfaces validated at 100% and 150%](qt-remaining.log) |
| Complete desktop matrix | `uv run python -m pytest --strict-markers tests/e2e -n auto --fresh -q -ra --durations=10 --junitxml=artifacts/verification/v0.6.0-local/desktop.xml` | [146 passed in 35:41](desktop.log) across 143 desktop scenarios and 3 geometry controls. [JUnit report](desktop.xml), [scenario manifests](desktop-manifests.md), [19,995 artifact hashes verified](desktop-audit.log) |
| Golden compatibility | `uv run python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-v060-local` | [11 cases, 476 comparisons passed, including 416 numeric fields](../../../build/qt6-verification/golden-compatibility-v060-local/capture/compatibility-report.json). [Command and exit](../../../build/qt6-verification/golden-compatibility-v060-local/command.json) |
| Targeted sheet scenarios | `uv run python -m pytest --strict-markers tests/e2e/test_desktop_workflows.py --fresh -q -ra -k 'sheets and not legacy and not persist and not swap'` | [2 passed](sheets-focused.log). [sheets](../rcms/20261119T045729Z-4c038fef-sheets/manifest.json), [sheets-edges](../rcms/20261119T045838Z-c5a6356d-sheets-edges/manifest.json) |

The R package expression selects the installed current-source package and
reports assertion counts from every testthat block:

```r
stopifnot(nzchar(Sys.setlocale("LC_CTYPE", ".UTF-8")))
x <- testthat::test_local("r/RCMetaR", load_package="installed", reporter="summary", stop_on_failure=FALSE)
d <- as.data.frame(x)
print(colSums(d[c("passed", "failed", "error", "skipped", "warning")]))
cat("Test blocks:", nrow(d), "\n")
stopifnot(!any(d$failed > 0 | d$error))
```

The [first Core attempt](qt-core.log) overlapped the supplemental native
GUI run and failed on popup visibility. The full serial Core run passed.
The native lanes retain [calculator](../../../build/qt6-verification/native-calculators/evidence.json),
[analysis](../../../build/qt6-verification/native-analysis/evidence.json),
[Results](../../../build/qt6-verification/native-results/scale-1_5.json) and
[remaining surface](../../../build/qt6-verification/native-remaining-surfaces/scale-1_5.json)
evidence. The desktop matrix uses the production R backend and offscreen Qt.

The two pytest selections cover all 1,243 tests collected by
`uv run python -m pytest --strict-markers tests --collect-only -q`. Across
those selections, 1,240 tests passed and three existing platform skips were
reported.

## Release metadata

The `v0.5.6` tag includes the REML and Peto corrections cited by `paper.md`.
The 0.6.0 bump sets the package date in `DESCRIPTION` to the changelog's
release date and regenerates the lockfile with [`uv lock`](uv-lock.log).
The resolver also recorded six additional wheels for the existing
`pyqt6-pdf-qt6` 6.140.0 pin. The [locked sync](release-sync.log) rebuilt
the Python application and retained the installed dependencies.

- [Strict Win32 typing](typing-release.log) passed with the bumped metadata.
- The same source-install command rebuilt [RCMetaR 0.6.0](install-release.log).
  The [Python version check](python-version.log) matched the module and
  installed distribution at 0.6.0.
- `uv run python -m pytest --strict-markers tests/packaging/contract/test_release_version_bump.py -q`
  returned [one pass](release-contract.log).
- `uv run python scripts/verify_rcms.py doctor` verified the
  [0.6.0 runtime](../rcms/20261119T053127Z-843bd38b-doctor/manifest.json).
