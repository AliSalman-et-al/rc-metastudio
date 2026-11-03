# Verification lanes

Choose checks that can detect the changed failure. Preserve transcripts and distinguish source behavior, numerical evidence, native fixture checks, and exact-package qualification.

| Change | Required useful evidence |
| --- | --- |
| Ordinary workflow/edit/save/import/calculator/plot | Mapped real Qt/R scenario with action and side-effect evidence; affected retained edge/failure tests |
| R estimator, eligibility, effect reconstruction, boundary, or dependency | `verify_all.py --full`: current-source R-stack, independent public-package authority matrix and complete desktop matrix; inspect all reports and complete affected targeted coverage rows |
| Shared Python storage or workspace boundary | Relevant files in `tests/python/fast`; mapped persistence/rollback drive; `uv run python scripts/verify.py fast` when the scope is broad |
| Qt form, sizing, focus, accessibility, resources | Generate forms; strict Ty; affected GUI tests; matching native lane on the changed target; real E2E when business behavior also changes |
| Packager, relocation, installer, trust, release artifact | Affected `tests/packaging/contract` plus actual target package qualification; source E2E is supplemental |
| Test-suite structure/configuration | `uv run python -m pytest --strict-markers tests --collect-only -q` after generating forms; run affected selections |

## Native and typing commands

Every qualification runs the repository-wide strict Ty invocation in `scripts/verify-qt6.ps1` before GUI tests. On POSIX, preserve its generated-module search paths and full source selection, using the configured `RCMS_QT6_BUILD_ROOT`.

For Windows-target qualification on another host, add `--python-platform win32` so platform-specific APIs such as `winreg` resolve against Windows. Keep that target on subsequent qualification runs. Retain the exact command and transcript. Record typing and GUI results separately: a failed typing gate means the following GUI phase has not run.

On Windows the repository owns the complete Qt lane:

```powershell
.\scripts\verify-qt6.ps1 -Section Core
.\scripts\verify-qt6.ps1 -Section RemainingSurfaces
```

Core performs strict Ty with generated-module search paths, the core GUI selection, native shell/calculator/analysis/Results probes, and R-load teardown. RemainingSurfaces owns the other five GUI layout modules and corresponding native probes. These commands intentionally unset the offscreen platform for native smoke. Inspect each probe's backend: fixture-based Results/layout evidence does not establish real R analysis.

Focused source behavior with native rendering can use:

```powershell
uv run python scripts/verify_rcms.py amino --native
```

For specific native evidence, the maintained scripts include:

```powershell
uv run python scripts/native_calculator_smoke.py
uv run python scripts/native_calculator_smoke.py --validate-only
uv run python scripts/native_results_smoke.py
uv run python scripts/native_results_smoke.py --validate-only
uv run python scripts/native_remaining_surfaces_smoke.py
uv run python scripts/native_remaining_surfaces_smoke.py --validate-only
```

Calculator and Results evidence defaults to `build/qt6-verification/native-calculators` and `native-results`; these are shared output directories. Do not run overlapping native probes concurrently in one checkout. Preserve their output under the current proof directory before cleaning build outputs. Native RemainingSurfaces supports `--evidence-root`; use a unique destination when invoking it directly.

## Numerical and release scope

The R-stack pytest selection includes all 98 desktop workflows through the shared scenario list. The skill's complete runner stops at the first failure and retains its logs; later commands are unexercised, not passed. After fixing a harness failure, doctor a fresh session and re-drive that path before shipping. For product failures, retain evidence and report the regression. During skill-only maintenance do not expand scope to product changes; when the user authorizes fixes, reproduce, fix and re-drive the failed behavior and its relevant boundaries.

Frozen comparison covers 11 cases (three basic plus eight binary/continuous extended). The authority script supplies 91 independent public-`metafor` model comparisons plus effect reconstruction assertions, including single/double-zero correction policies. Current-source R-stack supplies joint Reitsma public-`mada` comparisons and 21-case visual QA. These complement one another; none alone proves all UI modes. Small-study numerical gaps and mandatory targeted recipes are in its feature map.

After a golden-comparator-only correction, preserve the original failed report and re-run that gate without repeating already-passed unchanged package/bridge tests. For a configured warm Windows runtime:

```powershell
$env:R_HOME = $env:RCMS_R_HOME
$env:R_LIBS = $env:RCMS_R_LIBS
$env:R_LIBS_USER = $env:RCMS_R_LIBS
$env:PATH = "$env:R_HOME/bin/x64;$env:R_HOME/bin;$env:PATH"
uv run python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-targeted
```

The golden CLI needs that R environment explicitly; the desktop helper configures its bootstrap itself. Verify the saved `compatibility-report.json`, all 415 numerical fields and plot contracts, and identify the selected library/source provenance. Text comparison canonicalizes only a line-leading heterogeneity `t²`/`τ²` header before Q: runtime encoding can change that spelling within the same OS. Changed numbers, narrative and other text still fail. Frozen contracts and tolerances remain unchanged. A focused recovery pass does not retroactively make the original failed full-run command successful; report its failed stage and the corrected gate's evidence.

Read `docs/maintaining.md` for runner options and `docs/release.md` for package qualification. R dependency identity comes from `config/r-dependencies.json`, not remembered latest versions. ADR-0007 delegates statistical decisions to the authority packages. Golden tolerance changes require justification independent of current output.

Release targets are Windows x64, Apple silicon macOS, and Ubuntu 24.04 x86_64 (ADR-0013 supersedes ADR-0012). A local Windows proof cannot qualify the other targets. Exact artifact hashes, relocatability, runtime provenance, platform trust and release-set evidence come from package qualification. This skill does not authorize publishing, promotion, signing, workflow dispatch, or messaging others.

## Reporting

State the behavior proved and link its evidence directory. Include commands, runtime/platform, pass/fail and material skip reasons. If a path was unavailable, name the attempted action and missing precondition. Do not report a release qualified from source tests, a skipped path as passed, or a success marker from a process that crashed afterward.
