# Maintaining RC MetaStudio

This guide is the single operational reference for building, configuring, testing, and maintaining RC MetaStudio from source. Track active plans and unresolved work in [GitHub Issues](https://github.com/AliSalman-et-al/rc-metastudio/issues); release candidate building and promotion live in [Releasing RC MetaStudio](release.md).

## Set up the development environment

### Python and Qt 6 forms

RC MetaStudio uses **Python 3.14** and [uv](https://docs.astral.sh/uv/) (`pyproject.toml` and `uv.lock` are authoritative. Change dependencies in `pyproject.toml`, update `uv.lock`, and commit both together).

From the repository root:

```powershell
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
```

Point the runtime and test tools at the generated Qt modules:

```powershell
# PowerShell
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path build/qt6-verification).Path
```

```bash
# POSIX shell (macOS / Linux)
export RCMS_QT6_BUILD_ROOT="$PWD/build/qt6-verification"
```

Editable form sources live in `src/rc_metastudio/forms/*.ui`. Generated `ui_*.py` modules and compiled `.rcc` resources belong only under the selected build directory and must never be committed.

### Real R runtime and library (`4.6.2`)

Running the application or real-R verification requires **R 4.6.2** and the manifest-pinned packages in [`config/r-dependencies.json`](../config/r-dependencies.json) (`metafor 5.2-1`, `meta 8.5-0`, `mada 0.5.12`, `gsDesign 3.11.0`, and rendering/support packages). Production startup fails closed if R cannot start (see [ADR-0007](adr/0007-require-an-explicit-r-runtime.md)).

To create a persistent local development R library (do not install into your system R library):

```powershell
# PowerShell (adjust RCMS_R_HOME to your R 4.6.2 installation)
$env:RCMS_R_HOME = "C:\Program Files\R\R-4.6.2"
$env:RCMS_R_LIBS = (New-Item -ItemType Directory -Force "build/dev-r-lib").FullName
$env:R_LIBS_USER = $env:RCMS_R_LIBS

& "$env:RCMS_R_HOME\bin\Rscript.exe" --vanilla scripts/install-r-deps.R
& "$env:RCMS_R_HOME\bin\Rscript.exe" --vanilla scripts/install-rcmetar-source.R r/RCMetaR $env:RCMS_R_LIBS
```

```bash
# POSIX shell (macOS / Linux; adjust RCMS_R_HOME to your R 4.6.2 home)
export RCMS_R_HOME="$(R RHOME)"
export RCMS_R_LIBS="$PWD/build/dev-r-lib"
mkdir -p "$RCMS_R_LIBS"
export R_LIBS_USER="$RCMS_R_LIBS"

"$RCMS_R_HOME/bin/Rscript" --vanilla scripts/install-r-deps.R
"$RCMS_R_HOME/bin/Rscript" --vanilla scripts/install-rcmetar-source.R r/RCMetaR "$RCMS_R_LIBS"
```

Verify the installed package versions and runtime readiness:

```powershell
uv run python scripts/validate_rcmetar_r_manifests.py --report-installed-versions --rscript "$env:RCMS_R_HOME/bin/Rscript.exe"
uv run python scripts/verify_rcms.py doctor
```

Whenever you edit code under `r/RCMetaR`, reinstall it into `$RCMS_R_LIBS` with `scripts/install-rcmetar-source.R` before running warm desktop checks (`doctor` checks version equality, not whether installed files match dirty source).

### Launch from source

With `RCMS_QT6_BUILD_ROOT`, `RCMS_R_HOME`, and `RCMS_R_LIBS` set:

```powershell
uv run python -m rc_metastudio
```

Without `RCMS_QT6_BUILD_ROOT`, the application looks for generated forms under `build/qt6`.

## Pre-push gate

Set up the tracked hook in your checkout:

```powershell
git config core.hooksPath .githooks
```

Use Windows with a native Qt desktop, Node.js (`node` on PATH), Poppler (`pdftotext` on PATH), and the locked Python environment above. Set `RCMS_R_HOME` if the default R selection differs from [the runtime pin](../config/r-dependencies.json). The gate checks the actual R version before using it and builds RCMetaR in its own temporary library for the full stack and doctor.

Fetch the default branch for code health, commit your changes and run the gate from a clean tree:

```powershell
git fetch origin
uv run --locked python scripts/verify.py pre-push
```

The gate fails fast. It generates Qt forms and runs strict win32 typing before any GUI tests. It checks the pinned R runtime, committed code health, strict pytest collection, fast/golden Python tests, GUI tests, packaging contracts and JavaScript release tests. It runs both native Qt sections and the full R check set with a fresh run of every desktop scenario across the three CI shards, followed by doctor in the same owned R library.

The timing table is printed and saved to `artifacts/verification/pre-push.json` with the tested HEAD and clean-tree status. The hook checks that every local lane passed for the exact object being pushed and that the tree is still clean. It only checks the local receipt. Run the gate again after any new commit. The repository's macOS and Linux lanes still run in CI. The release pipeline separately qualifies the exact Windows package on its Windows Server 2025 runner.

## Verification lanes and test suites

### Unified runner (`scripts/verify.py`)

```powershell
# Representative fast/format/Qt resource smoke
uv run python scripts/verify.py smoke

# Fast Python tests, golden analysis tests, and default R evidence
uv run python scripts/verify.py fast

# Full RCMetaR check, Python–R bridge, golden compatibility, and desktop E2E
uv run python scripts/verify.py r-stack
```

Useful flags: `--sync` (re-sync `uv.lock`), `--require-r-evidence` / `--skip-r-evidence`, `--rscript <path>`, `--desktop-shard {1,2,3}`, `--skip-desktop`. Note that `verify.py r-stack` installs dependencies and current `r/RCMetaR` source into a temporary owned library that is cleaned up on exit; keep a persistent `RCMS_R_LIBS` for warm local `verify_rcms.py` drives.

### Required gate after `r/RCMetaR` changes

Any change under `r/RCMetaR` (including plot layout and rendering) requires running the full R-stack verifier against the pinned R `4.6.2` runtime and retaining its transcript:

```powershell
uv run --no-sync python scripts/verify_rcmetar_r_stack.py `
  --rscript "$env:RCMS_R_HOME/bin/Rscript.exe" `
  --r-library-cache-root artifacts/r-library-cache `
  --desktop-workers 1
```

(On POSIX, use `"$RCMS_R_HOME/bin/Rscript"`.) Afterwards, reinstall `r/RCMetaR` into your persistent `$RCMS_R_LIBS`.

### Native and typing commands

`ty` uses Astral's default rules with warnings treated as errors (`pyproject.toml`: `error-on-warning = true`; do not enable `all = "error"`). It checks `src/rc_metastudio`, `scripts`, `tests`, `.agents/skills/verify-rcms/scripts`, and `r/RCMetaR/inst/qa` against the generated Qt build root and `--python-platform win32`. Run the repository-wide check before GUI qualification. Each invocation retains its command, win32 target, exit code and transcripts under `artifacts/verification/typing/`. On other hosts keep the generated-module paths and win32 target for Windows qualification. Record typing and GUI results separately.

On Windows, run the native Qt 6 lane (form generation, strict `ty`, GUI tests, and native `qwindows` shell/calculator/analysis/Results/remaining-surfaces smoke):

```powershell
.\scripts\verify-qt6.ps1
# Or individual CI sections:
.\scripts\verify-qt6.ps1 -Section Core
.\scripts\verify-qt6.ps1 -Section RemainingSurfaces
```

### Real Qt/R desktop workflows and evidence (`verify_rcms.py`)

For targeted real-application proofs with retained screenshots, transcripts, manifests, and exported files under `artifacts/verification/rcms/`:

```powershell
uv run python scripts/verify_rcms.py doctor
uv run python scripts/verify_rcms.py amino          # offscreen Qt
uv run python scripts/verify_rcms.py amino --native # host-platform Qt
uv run python -m pytest tests/e2e -n auto -k '<selection>'
```

- The scenario registry and `PLOT_PRODUCERS` / `QUALIFICATION_SCENARIOS` deduplication live in [`tests/e2e/desktop_scenarios.py`](../tests/e2e/desktop_scenarios.py).
- For the complete warm desktop matrix or full qualification pass, use `uv run python .agents/skills/verify-rcms/scripts/verify_all.py` (add `--full --fresh` for uncached R-stack + authority comparisons). See [Verify RCMS](../.agents/skills/verify-rcms/SKILL.md) for scenario maps and evidence rules.
- **CI sharding:** CI runs three parallel desktop shards plus a checks job. Shards are balanced by `config/desktop-durations.json` (unmeasured cases default to 60 s). Inspect a shard with `uv run python -m pytest --strict-markers tests/e2e --collect-only -q --desktop-shard 1 --shard-report artifacts/verification/desktop-partition.json`.
- **Strict collection check** after test configuration edits: `uv run pytest --strict-markers tests --collect-only -q`.

### Test suite organization and policy

| Suite | Scope |
| --- | --- |
| `tests/e2e` | Real Qt 6 and embedded R desktop workflows with numerical, geometry and persistence checks |
| `tests/python/fast` | Archive corruption, atomic durability, rollback, concurrency, boundary validation |
| `tests/python/gui` | Layout, keyboard focus, dialog edge cases, and failure recovery outside E2E |
| `tests/analysis_regression/golden` | Frozen numerical and presentation regression contracts (see [baseline provenance](../tests/analysis_regression/baseline/presentation-review/README.md)) |
| `tests/r_stack` | Python–R bridge serialization, Unicode/NA handling, and `mada` Reitsma authority |
| `tests/packaging/contract` | Frozen bundle integrity, relocation, tampering, and release-set validation |
| `r/RCMetaR/tests/testthat` | R package statistical and rendering unit/authority checks |

**Coverage rules:** Prefer real desktop E2E assertions over mocks. Keep smaller tests only for concrete failures that ordinary E2E workflows cannot easily trigger (malformed archives, I/O durability errors, invalid inputs, rollback, concurrency, pixel-level alpha compositing, or package tampering). Never assert against a mock's own return value, check source-code strings as proof, or refresh a golden oracle to make a failure pass.

### Desktop selection

Qualification omits ten standalone producer runs already executed in full by
the plot workflows below. Their CLI commands remain available for targeted
debugging. `PLOT_PRODUCERS` owns both the actual producer used by each plot drive
and the qualification selection, so the two cannot drift independently.

| Standalone producer | Qualification workflow |
| --- | --- |
| `analysis-binary.fixed.inv.var` | `plot-workflow-forest` |
| `analysis-amino-binary-cumulative` | `plot-workflow-cumulative` |
| `analysis-amino-binary-leave-one-out` | `plot-workflow-leave-one-out` |
| `analysis-amino-binary-subgroup` | `plot-workflow-subgroup` |
| `analysis-amino-binary-meta-regression` | `plot-workflow-regression` |
| `analysis-diagnostic-joint` | `plot-workflow-sroc` |
| `analysis-diagnostic-regression-continuous` | `plot-workflow-coefficient` |
| `small-study-binary-extended` | `plot-workflow-funnel`, `plot-workflow-contour`, `plot-workflow-trimfill` |
| `small-study-diagnostic` | `plot-workflow-deeks` |
| `tsa-bcg` | `plot-workflow-trial-sequential` |

The exact CLI aliases `results-window` and `project-structure` are qualified
through `ux-improvements` and `sheets`, respectively. Each pair dispatches the
same function with the same inputs. Targeted CLI names remain available.
The sorted-name edit explicitly sorts the restored model after undo/redo:
presentation sorting is transient and is reset when history rebuilds the model.

Workspace-safety helper cases remain in the GUI suite: that helper has no
registered desktop caller. CSV dialect changes, failed plot commits, native
geometry, hostile archives and independent numerical oracles also remain when
their exact failures are absent from desktop coverage. Consolidating setup does
not justify deleting a distinct failure merely because a nearby happy path runs.

### Independent expectations

The November 2026 audit treats a check as circular when its expected answer comes
from the same implementation, a configured mock return, or a declaration that
the test merely repeats. A mock is still useful for injecting failure or observing
a boundary request. Round trips remain useful when they verify persisted data,
ownership, or regenerated artifacts against the original inputs.

The audit retained these independent checks.

| Failure to detect | Independent proof |
| --- | --- |
| Wrong zero-cell DOR reconstruction or correction-label mapping | Corrected-count arithmetic and public `metafor::escalc` on original counts |
| Peto accidentally consumes stale entered effects | Public `metafor::rma.peto` on original counts |
| Wrong small-study routing heterogeneity | Public `meta::metagen` on count-derived log odds ratios and standard errors |
| Wrong Reitsma moderator formula | Public `mada::reitsma` with an explicit two-moderator formula |
| Wrong packaged-summary normalization or digest | Literal normalized text hashed independently with the standard library |
| Policy evidence changed after stages were recorded | Reject a modified policy digest in the completed release chain |
| Wrong revision complexity | Literal cognitive counts for a straight return and two nested conditions |
| Incorrect plot labels | Literal fixture labels, independent of production formatters |
| Ratio reversal silently becomes a no-op | Reciprocal bounds on the ratio scale and negated, swapped bounds on the log scale |
| Apple Silicon launcher accepts Intel linker flags | Execute the generated shell adapter with supported and Intel upstream metadata |
| Calculator grid displays a different estimate or interval | Compare numeric cells with the entered interval at the configured precision; small values must also retain their sign and relative accuracy, without calling the grid formatter |

Keep frozen numerical release oracles independent of current output. Baseline provenance and replay instructions live with the [golden records](../tests/analysis_regression/baseline/presentation-review/README.md).
Sequential plot alignment compares SVG row positions with the observed report
cells, without asking the renderer's own label formatter for an expected answer.
Numerical correctness remains covered by frozen/public-package comparisons.

See the [desktop oracle reference](../tests/e2e/ORACLES.md) for scenario inputs and evidence.

**Python branch coverage** (measure E2E and smaller checks separately):

```powershell
uv run python -m coverage run -m pytest tests/e2e -q
uv run python -m coverage combine
uv run python -m coverage json -o artifacts/verification/rcms/e2e-coverage.json
uv run python -m coverage report
```

## Code health and unused code

### Complexity, coupling, and churn (`scripts/code_health.py`)

```powershell
uv run python scripts/code_health.py --base 8b7796b --head HEAD `
  --baseline artifacts/code-health/baseline.json `
  --output artifacts/code-health/final.json `
  --report artifacts/code-health/final.txt
```

Measurements always inspect the named Git revisions (not dirty worktree files). `--base` governs pass/fail gates (new cycles, forbidden imports, changed-function complexity); `--baseline` supplies trend context only.

### Unused Python code (`vulture`)

```powershell
uv run vulture
```

Review every finding against callers before deleting: Qt overrides, Designer custom widgets, pytest hooks/fixtures, schema declarations, and subprocess entry points may be invoked implicitly. Exit code `3` means findings remain. Re-run after removing confirmed dead code to catch newly orphaned helpers; avoid blanket whitelists.

## Repository layout and module ownership

| Path | Role |
| --- | --- |
| `src/rc_metastudio/` | Application source, `.ui` forms, icons, and bundled `.rcms` JSON schemas |
| `r/RCMetaR/` | Bundled R statistical and plotting package |
| `sample_projects/` | Nine bundled published `.rcms` examples, manifest, and source provenance |
| `scripts/` | Build, verification, R-dependency, version-bump, and packaging scripts |
| `packaging/` | PyInstaller specs and platform packaging definitions |
| `config/` | Machine-readable policies (`r-dependencies.json`, `desktop-durations.json`, etc.) |
| `tests/` | Executable test suites, frozen desktop/legacy fixtures, and golden baselines |
| `artifacts/` *(gitignored)* | Local verification evidence, caches, and built packages |

<a id="where-a-change-belongs"></a>

### Module ownership under `src/rc_metastudio/`

Start at the boundary responsible for the behavior and follow its callers. File length alone is not a reason to split a file.

| Owner | Responsibility | Contract to preserve |
| --- | --- | --- |
| `application_metadata.py` | App identity and version (imported from package `__version__`) | Single version source of truth |
| `project/` | `.rcms` archive, v1/v2→v3 migration, semantic validation, pure data model | Loads without Qt or R; safe archives and atomic durability |
| `workspace/` | Session undo/redo (100 steps), sheet editing, column rules, Qt table | Stable IDs, atomic edits and rollback |
| `importing/` | CSV, `.xlsx`, and RevMan `.rm5` ingestion | Validated previews and atomic sheet publication |
| `analysis/` | Catalog (`catalog.py`), validation (`validation.py`), requests (`requests.py`), setup, small-study effects, TSA | Catalog/validation stay Qt-free; real R authority; never move statistical policy into widgets |
| `r_runtime.py`, `r_bridge.py` | Explicit R startup and versioned Python–R boundary | Fail-closed startup; exact producer quantities |
| `results/` | Result contract, formatting (`formatting.py`), report (`report.py`), plot editors/export, SVG adapter | Exact numerical quantities (never parse formatted text); preserve prior plot on edit failure |
| `calculators/` | Controls (`controls.py`), effect readout (`effect_readout.py`), dialog-local history (`edit_history.py`), four dialogs | Controls do not depend on readouts/history; history is Qt/R-free |
| `forms/*.ui`, `qt_layout.py` | Editable Qt Designer forms and adaptive layout helpers | Generated modules stay out of source; preserve form manifest and keyboard/DPI behavior |

**Relocation rules:** When moving a module, update imports, dynamic symbol references, Qt Designer custom-widget headers, form manifests, `code_health.py` boundary rules, tests, and docs in the same change. Preserve data-family IDs, metric strings, statistical method IDs, settings keys, and `.rcms` format contracts. Before changing cross-boundary assumptions, read [CONTEXT.md](../CONTEXT.md) and the active [architecture decisions](adr/README.md).

## Platform and rendering invariants

- **Qt SVG `clipPath` adaptation:** Qt 6's `QtSvg` omits `clipPath`. `src/rc_metastudio/results/svg_rendering.py` (`svg_bytes_for_qt`) converts `svglite`'s rectangular, untransformed clip groups into in-memory symbol viewports for on-screen display and intersects each group with the visible page slice during multi-page PDF report pagination. Saved `.svg` files keep R's original `clipPath` markup; PNG/TIFF/PDF plot exports render through R/`rsvg`. Verify multi-page forests when modifying SVG rendering or caption clearance.
- **Frozen Linux startup and `HOME` ordering:** In frozen builds, `r_runtime.configure_bundled_r_environment()` must run **before** `settings.setup_directories()`. It redirects `HOME` and temp paths to a private runtime directory outside the bundle; creating Qt's application-data paths first leaves R's working-directory reset pointing at a missing directory. Keep R loading deferred until after the window shell is visible.

## Build the Linux package

For bootstrap changes, verify the packaged Linux executable with a fresh HOME, no XDG_DATA_HOME, German locale and native xcb at 1.25, 1.50 and 1.75 scale. Retain the commands, environment, surface records and bounded exit.

Release packages target **Ubuntu 24.04 x86_64** (see [ADR-0009](adr/0009-support-qualified-release-platforms.md)):

```bash
sudo apt-get update
sudo apt-get install -y xvfb libegl1 libx11-xcb1 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-randr0 libxcb-shape0 libxcb-util1 libxcb-xkb1 libxkbcommon-x11-0 librsvg2-2 libdeflate-dev libzstd-dev libtirpc-dev liblzma-dev libbz2-dev libblas-dev liblapack-dev libgfortran5 libgomp1 libtk8.6
bash scripts/package-linux.sh
```

This writes `artifacts/RCMetaStudio-linux-x64.tar.gz` (application, private R runtime, and `LaunchRCMetaStudio.sh`) and its qualification evidence. For version bumping (`scripts/bump_version.py`), hosted Windows/macOS/Linux candidate builds, signing/notarization, and promotion, see [Releasing RC MetaStudio](release.md).

## License headers

New maintained source files use:

```text
SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
SPDX-License-Identifier: GPL-3.0-or-later
```

Preserve original copyright notices in derived files and never label third-party code or assets as RC MetaStudio-owned. Before releasing, verify bundled components and add `THIRD_PARTY_NOTICES.md` only if required beyond included package metadata.
