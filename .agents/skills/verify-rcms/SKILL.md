---
name: verify-rcms
description: Verify RC MetaStudio desktop workflows with real Qt and R, capture action and result evidence, and select the necessary native, statistical, or package checks after changes.
---

# Verify RC MetaStudio

Prove the changed user behavior with the real application. Read the [feature index](features/README.md), the [coverage checklist](references/coverage.md), then the affected feature. Use [CONTEXT.md](../../../CONTEXT.md) for domain terms, the relevant [architecture decisions](../../../docs/adr/README.md), and the [test policy](../../../docs/maintaining.md#test-suite-organization-and-policy). A green basic analysis is insufficient after a shared analysis change.

## Launch

Follow [source setup](../../../docs/maintaining.md#set-up-the-development-environment) for generated forms and a pinned R runtime. Use a persistent test library for targeted drives. Reinstall changed RCMetaR source before driving it and record installed-source provenance. If startup fails, inspect the helper's `stderr.log` and `runtime.json`.

The verification helper owns and closes its own windows. Do not attach it to the user's running application. Native driving is opt-in with `--native`; on Windows this uses qwindows, on macOS cocoa, and on Linux a working native display is required. The default uses Qt offscreen.

## Doctor

Run `uv run python scripts/verify_rcms.py doctor` before driving a newly configured runtime or whenever readiness is uncertain. This reads runtime identity and opens an empty application in isolated settings; it does not edit projects. Each proof run repeats the same check before its feature.

Inspect the printed evidence directory. `runtime.json` records the actual R home and libraries, authority versions, RCMetaR/rpy2/Qt versions, platform plugin, and Qt build root. Missing dependencies, version mismatches, startup errors, or a nonzero process exit fail the check. An absent `runtime.json` means startup failed before identity could be recorded.

## Drive

Use the existing `tests/e2e/desktop_driver.py` through the evidence helper:

```powershell
uv run python scripts/verify_rcms.py amino
uv run python scripts/verify_rcms.py editing
```

Choose the scenario from the feature map. See [verification lanes](../../../docs/maintaining.md#verification-lanes-and-test-suites) for warm and full matrix commands, reuse rules and the R-change gate. The desktop registry lists its scenarios. An exact artifact or numerical claim needs the corresponding evidence.

The matrix includes all eight original New Dataset paths plus the HR/IRR metric variants, fixed estimator selection, binary/continuous cumulative/leave-one-out/subgroup/regression with frozen contracts, diagnostic sequential/subgroup/joint/combined metrics and three moderator shapes, extended binary/continuous small-study procedures, and diagnostic Deeks. The feature maps state each drive's proof strength and remaining checks.

The advanced workflows in `scripts/advanced_workflows.py` add nondefault inference, heterogeneity and confidence-interval choices with public numerical references, zero cells and inclusion changes, calculator modes with persistence and independent post-reopen analysis, plot editors with decoded exports, and workspace transactions. The scenario registry in `tests/e2e/desktop_scenarios.py` lists the current drives. Examples include `options-binary`, `calculator-mode-back-continuous`, `plot-workflow-sroc`, `plot-workflow-trial-sequential`, and `project-table-covariates`. Numerical claims require numerical comparisons.

See the [desktop selection policy](../../../docs/maintaining.md#desktop-selection) for producer deduplication. Individual CLI scenarios remain available for debugging.

The driver uses QAction handles, Qt widgets, editors, modal buttons, and the production storage and analysis path. Each child owns its application-data and analysis-scratch subdirectories. `runtime.json` records those paths and confirms that Python and embedded R retain the caller's working directory. File pickers return test-owned paths, and the intentional corrupt-project error is observed without a blocking box. Native application-data creation and OS file-picker gestures require separate checks. The `csv` scenario starts at the CSV page. Use `xlsx-import` for the unified Import data action and Welcome wizard entry with controlled picker results, and `rm5-import` for RevMan entry and review.

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

Normal completion and assertion failure close/dispose owned Qt windows and quit the application. `tests/e2e/desktop_scenarios.py` owns the process limits. Most scenarios use 120 seconds, the four-format plot workflows use 240 seconds, `ratios-hr` uses 600 seconds, and `ratios-irr` uses 1,200 seconds. `scripts/run_with_timeout.py` terminates only the child process tree it launched. The helper copies settings and R artifacts from its temporary directories under `build/verification/rcms/` into evidence before cleanup, including after a failure.

After a proof, confirm the printed directory still contains `manifest.json`, transcripts, and the expected screenshots and side-effect artifacts. Cleanup must preserve failed evidence too. If the outer shell itself is forcibly terminated, inspect its recorded command/PID before cleaning an orphan; never kill by process name or recursively delete a shared artifact directory. Do not clean the user's project files, runtime libraries, or application preferences.

## Helpers

`uv run python scripts/verify_rcms.py --help` lists the supported scenarios and `--native`. It wraps the shared E2E driver; it is not a second implementation of the workflows. The existing `scripts/verify.py` and native/package scripts remain the authority for their lanes.

The skill owns `scripts/analysis_matrix.py`, `scripts/analysis_authorities.R`, and `scripts/verify_all.py` here, and uses the shared verification harness `scripts/verify_rcms.py`, `tests/e2e/desktop_driver.py`, its pytest selection, and the golden comparison harness under `tests/analysis_regression/golden/`. Maintenance may repair these harnesses; keep product changes and frozen oracle changes out of a skill maintenance pass. Invoke Python scripts with `uv run python`; the analysis feature documents the pinned Rscript invocation and report argument.

Update this feature map when a demonstrated path changes or new behavior is added.
