# Verification lanes

Choose checks that can detect the changed failure. Preserve transcripts and distinguish source behavior, numerical evidence, native fixture checks, and exact-package qualification.

| Change | Required useful evidence |
| --- | --- |
| Ordinary workflow/edit/save/import/calculator/plot | Mapped real Qt/R scenario with action and side-effect evidence; affected retained edge/failure tests |
| R estimator, eligibility, effect reconstruction, boundary, or dependency | `uv run python scripts/verify.py r-stack`: current installed RCMetaR, live bridge, golden/statistical and Reitsma visual evidence, plus desktop E2E; inspect all produced reports |
| Shared Python storage or workspace boundary | Relevant files in `tests/python/fast`; mapped persistence/rollback drive; `uv run python scripts/verify.py fast` when the scope is broad |
| Qt form, sizing, focus, accessibility, resources | Generate forms; strict Ty; affected GUI tests; matching native lane on the changed target; real E2E when business behavior also changes |
| Packager, relocation, installer, trust, release artifact | Affected `tests/packaging/contract` plus actual target package qualification; source E2E is supplemental |
| Test-suite structure/configuration | `uv run pytest --strict-markers tests --collect-only -q` after generating forms; run affected selections |

## Native and typing commands

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

Read `docs/maintaining.md` for runner options and `docs/release.md` for package qualification. R dependency identity comes from `config/r-dependencies.json`, not remembered latest versions. ADR-0007 delegates statistical decisions to the authority packages. Golden tolerance changes require justification independent of current output.

Release targets are Windows x64, Apple silicon macOS, and Ubuntu 24.04 x86_64 (ADR-0013 supersedes ADR-0012). A local Windows proof cannot qualify the other targets. Exact artifact hashes, relocatability, runtime provenance, platform trust and release-set evidence come from package qualification. This skill does not authorize publishing, promotion, signing, workflow dispatch, or messaging others.

## Reporting

State the behavior proved and link its evidence directory. Include commands, runtime/platform, pass/fail and material skip reasons. If a path was unavailable, name the attempted action and missing precondition. Do not report a release qualified from source tests, a skipped path as passed, or a success marker from a process that crashed afterward.
