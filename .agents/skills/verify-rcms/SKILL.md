---
name: verify-rcms
description: Verify RC MetaStudio desktop workflows with real Qt and R, capture action and result evidence, and select the necessary native, statistical, or package checks after changes.
---

# Verify RC MetaStudio

Prove the changed user behavior with the real application. Read the [feature index](features/README.md), the [coverage checklist](references/coverage.md), then the affected feature. Use `CONTEXT.md` for domain terms, `docs/testing.md` for retained failure tests, and the relevant `docs/adr/` decisions. ADR-0008 owns the release oracle; ADR-0010 requires a real R runtime. A green basic analysis is insufficient after a shared analysis change.

## Launch

Run from the repository root using its locked Python 3.11 environment:

```powershell
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path build/qt6-verification).Path
uv run python scripts/verify_rcms.py doctor
```

The helper starts a fresh ordinary Qt/R composition for each invocation. `doctor` requires a visible main window, generated forms, working embedded R, the manifest-pinned statistical authority packages, and the current RCMetaR version. Exit zero plus `WORKFLOW PASSED` in the saved transcript establishes readiness. It does not establish that installed RCMetaR code matches a dirty source tree.

For a warm run, `RCMS_R_HOME` and `RCMS_R_LIBS` must select an existing pinned runtime and library containing installed RCMetaR. The helper inherits these variables and `RCMS_QT6_BUILD_ROOT`; it does not install packages or silently substitute an R fake. If startup fails, inspect `stderr.log` and `runtime.json` if present. Use the repository's full setup/verification lane:

```powershell
uv run python scripts/verify.py r-stack
```

That lane installs dependencies and the current RCMetaR source into a temporary library and runs the live bridge and complete desktop matrix. Its temporary library disappears at completion; the dependency cache alone is not an installed RCMetaR development library. Configure a persistent test-owned library for later screenshot captures. Do not install into a system library or alter a qualified package to repair source verification.

For interactive source execution, after configuring that runtime and generating forms:

```powershell
uv run python -m rc_metastudio
```

Keep `RCMS_QT6_BUILD_ROOT` set for interactive execution; without it the application
defaults to `build/qt6`. On a POSIX shell use
`export RCMS_QT6_BUILD_ROOT="$PWD/build/qt6-verification"` instead of the PowerShell assignment.

The verification helper owns and closes its own windows. Do not attach it to the user's running application. Native driving is opt-in with `--native`; on Windows this uses qwindows, on macOS cocoa, and on Linux a working native display is required. The default uses Qt offscreen.

The full R-stack lane runs bridge drivers and desktop scenarios serially on every platform to bound publication-raster memory and give native driving one display owner. It binds `RCMS_R_LIBS`, `R_LIBS` and `R_LIBS_USER` to its owned library so an ambient interactive-library override cannot replace the installed current source. Inspect desktop `runtime.json` library paths to confirm that selection. Each desktop child owns its settings, working directory and analysis scratch directory. CI caches only dependency libraries, verifies their manifest versions, and rebuilds RCMetaR from the current source on every run. `--durations=10` reports the slowest desktop cases.

## Doctor

Run `uv run python scripts/verify_rcms.py doctor` before driving a newly configured runtime or whenever readiness is uncertain. This reads runtime identity and opens an empty application in isolated settings; it does not edit projects. Each proof run repeats the same check before its feature.

Inspect the printed evidence directory. `runtime.json` records the actual R home and libraries, authority versions, RCMetaR/rpy2/Qt versions, platform plugin, and Qt build root. Missing dependencies, version mismatches, startup errors, or a nonzero process exit fail the check. An absent `runtime.json` means startup failed before identity could be recorded.

## Drive

Use the existing `tests/e2e/desktop_driver.py` through the evidence helper:

```powershell
uv run python scripts/verify_rcms.py amino
uv run python scripts/verify_rcms.py editing
```

Choose the scenario from the feature map. For the complete desktop matrix with durable evidence:

```powershell
uv run python .agents/skills/verify-rcms/scripts/verify_all.py
```

For a shared analysis, data-type, inference, or R dependency change, run the full profile:

```powershell
uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full
```

This runs the current-source R-stack lane (including every desktop scenario once), independent authority comparisons and doctor. It requires `RCMS_R_HOME` and `RCMS_R_LIBS` from Launch. The R lane installs a temporary library; doctor and later targeted drives still use the configured warm library. After changing RCMetaR, install the changed source into a persistent test-owned library and select it before desktop driving; version equality alone is insufficient. Record installed-source provenance. The full profile does not repeat the desktop registry after pytest has already proved it.

The matrix includes all eight original New Dataset paths plus the HR/IRR metric variants, fixed estimator selection, binary/continuous cumulative/leave-one-out/subgroup/regression with frozen contracts, diagnostic sequential/subgroup/joint/combined metrics and three moderator shapes, extended binary/continuous small-study procedures, and diagnostic Deeks. The feature maps state each drive's proof strength and remaining checks.

The 37 advanced workflows in `scripts/advanced_workflows.py` add nondefault inference/heterogeneity/CI choices with public numerical references, zero cells and inclusion changes, twelve calculator modes with persistence and independent post-reopen analysis, eleven plot editors with four decoded exports each, and structure/covariate/shell transactions. Run these through the same evidence helper, for example `options-binary`, `calculator-mode-back-continuous`, `plot-workflow-sroc`, and `project-table-covariates`. Never replace numerical comparisons with nonempty text or a render-only check.

The same scenarios are part of the R-stack CI E2E selection. Pytest calls the evidence helper too, so every run retains its inputs, transcript and manifest:

```powershell
uv run python -m pytest tests/e2e -q
```

The driver uses QAction handles, Qt widgets, actual editors, modal buttons, and the production storage/analysis path. The managed application base is redirected to each child's owned working directory and recorded in `runtime.json`; Qt test mode alone still shares a base directory across workers. File pickers return test-owned paths, and the intentional corrupt-project error is observed without a blocking box. These substitutions do not verify native application-data directory creation or OS file-picker behavior. CSV driving currently starts the import wizard at its CSV page; it does not prove the File menu or the earlier wizard pages. Record these entry-point limits rather than treating nearby coverage as proof.

When a changed path is absent from the map or uses an unexercised entry point, extend the real driver or perform a targeted native drive. Assert observable data, numerical results, rendered output, saved state, and rollback as applicable. Exercise the failing trigger first and the recovered state afterward. Do not replace an unavailable production dependency with a mock or add source-string/constant inventories as evidence.

Select additional checks by the actual change; see [verification lanes](references/lanes.md). The complete matrix does not establish every supported parameter/data combination, calculator mode, native entry gesture, or release package. Complete the affected rows of the coverage checklist; record attempted paths, observed results and missing proof. Broaden when changed behavior or an unresolved failure justifies it.

## Evidence

Each desktop child runs in a fresh owned working directory. Its diagnostic CSVs
and plot state must stay under `RCMS_ANALYSIS_SCRATCH_DIR`; a repository `r_tmp`
directory must not be a prerequisite. The joint diagnostic drive checks clinical
interval columns and all four ratio rows in the actual result window. Regression
plot editing also proves BMJ style persistence, Cancel rollback and decoded exports.
The R lane uses independent numerical and distinct failure/geometry checks plus
desktop E2E; the removed standalone nonempty-result smoke matrix is not evidence.

Each helper invocation prints a unique `artifacts/verification/rcms/<UTC>-<id>-<scenario>/` directory containing:

- `manifest.json`: exact command, process exit, pass status, timestamps, Git revision and dirty state, tracked-diff, driver and skill-file digests (including untracked harness changes), and SHA-256 for captured files.
- `stdout.log` and `stderr.log`: startup, assertions, exceptions, crashes, and timeout diagnostics.
- `runtime.json`: observed production runtime identity.
- `steps.jsonl` and numbered PNGs: the action, selected method/configuration, before/after views, and observed state while each window is alive.
- Numbered plot files: copies taken while R is alive, including funnels created outside the analysis scratch directory. Each step's `artifacts` maps titles to retained paths; its `plots` records the original transient paths.
- `workflow/`: saved projects, CSV, exported PDF, isolated settings, and R plot/parameter artifacts copied before scratch cleanup.

Read the assertions and the action/result pair; a screenshot or success marker alone is insufficient. Frozen desktop cases compare displayed numerical sections with `tests/analysis_regression/baseline/numeric-contract.json`. Additional estimator/data-type drives establish UI execution and rendering, supplemented by public-package comparisons; do not call these frozen numerical UI proof. `analysis_authorities.R` independently constructs effects and compares coefficients, standard errors, tests, intervals, heterogeneity and study counts with public `metafor` calls. The R-stack supplies Reitsma `mada` comparisons and visual evidence. Small-study identity tests are not independent numerical oracles for every asymmetry method; statistical changes require the feature's direct-package comparisons. Never regenerate an oracle to make a failure pass. A `.rcms` file alone is insufficient persistence proof: reopen it and observe the saved values.

The manifest binds evidence to an observed dirty worktree, not a release build. Installed package version equality is not source-code provenance. State exactly which feature, scenario, entry point, runtime, and platform passed; name any skipped or unexercised paths. Offscreen screenshots demonstrate Qt rendering and interaction, not native window-manager, DPI, accessibility, or package qualification. Native result smoke also uses controlled fixtures; read the lane's scope before claiming live statistical proof.

## Cleanup

Normal completion and assertion failure close/dispose owned Qt windows and quit the owned application. The helper delegates a 120-second bound (240 seconds for four-format plot workflows; 600 seconds for the full HR/IRR drives, each with six editors and 24 exports including 600-DPI rasters) to `scripts/run_with_timeout.py`, which terminates only the child process tree it launched. Scratch directories under `build/verification/rcms/` are owned `TemporaryDirectory` instances; their settings and R artifacts are copied into evidence before removal, including after failure.

After a proof, confirm the printed directory still contains `manifest.json`, transcripts, and the expected screenshots and side-effect artifacts. Cleanup must preserve failed evidence too. If the outer shell itself is forcibly terminated, inspect its recorded command/PID before cleaning an orphan; never kill by process name or recursively delete a shared artifact directory. Do not clean the user's project files, runtime libraries, or application preferences.

## Helpers

`uv run python scripts/verify_rcms.py --help` lists the supported scenarios and `--native`. It wraps the shared E2E driver; it is not a second implementation of the workflows. The existing `scripts/verify.py` and native/package scripts remain the authority for their lanes.

The skill owns `scripts/analysis_matrix.py`, `scripts/analysis_authorities.R`, and `scripts/verify_all.py` here, and uses the shared verification harness `scripts/verify_rcms.py`, `tests/e2e/desktop_driver.py`, its pytest selection, and the golden comparison harness under `tests/analysis_regression/golden/`. Maintenance may repair these harnesses; keep product changes and frozen oracle changes out of a skill maintenance pass. Invoke Python scripts with `uv run python`; the analysis feature documents the pinned Rscript invocation and report argument.

Update this feature map when a demonstrated path changes or new behavior is added. Use `pstack:maintain-verification-skill` for a later maintenance pass.
