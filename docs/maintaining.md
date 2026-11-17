# Maintaining RC MetaStudio

Use this guide to set up, change, and verify the application. Keep temporary plans, investigation notes, and work status in GitHub Issues.

## Set up the repository

RC MetaStudio uses Python 3.14 and [uv](https://docs.astral.sh/uv/). Use uv 0.13.8 or newer so its runtime catalog includes Python 3.14.10. From the repository root:

```powershell
uv sync --locked
```

Ty uses Astral’s default rules with warnings treated as failures. Avoid `all = "error"`, which enables optional, opinionated rules automatically.

The lockfile is authoritative. Change dependencies in `pyproject.toml`, update `uv.lock`, and commit both files together.

## Run verification

Use the unified runner for normal source work:

```powershell
# Representative Python, project-format, and Qt resource checks
uv run python scripts/verify.py smoke

# Fast Python tests, golden analysis tests, and default R evidence
uv run python scripts/verify.py fast

# Full RCMetaR and R integration evidence
uv run python scripts/verify.py r-stack
```

Run the affected local checks before committing. Before pushing, run
`uv run python scripts/verify.py pre-push` after committing so its code-health
check measures the committed revision. Analysis and R-boundary changes also
need the [full real-R and desktop qualification](../.agents/skills/verify-rcms/SKILL.md).
The pre-push gate does not replace that lane.

Use the pinned development tool to review unused Python code:

```powershell
uv run vulture
```

The configured scan includes product code, scripts, tests and verification
helpers. Review findings against callers before deleting code. Qt overrides,
Designer custom widgets, pytest hooks and fixtures, schema declarations and
subprocess entry points may be invoked implicitly. Fixture arguments can be
required for setup and teardown even when their values are unused. Vulture's
confidence is not a deletion decision. Exit code 3 means findings remain; see
the [Vulture documentation](https://pypi.org/project/vulture/).

After removing a confirmed unused owner, rerun the scan to find newly orphaned
helpers and imports. Preserve meaningful tests and durable settings migrations.
Avoid blanket suppressions or generating a whitelist from every finding.

For deterministic complexity, dependency, churn, and hotspot evidence, run the
locked code-health command against a comparison commit. Both snapshots are
measured from their named revisions: history is bounded at the measured head,
and Radon, Complexipy, and Grimp analyze that revision's source. The command
writes machine-readable JSON and a short text report; the exit status enforces
only new cycles, forbidden boundary imports, and changed-function thresholds.

```powershell
uv run python scripts/code_health.py --base 8b7796b --head HEAD `
  --baseline artifacts/code-health/baseline.json `
  --output artifacts/code-health/final.json `
  --report artifacts/code-health/final.txt
```

Use the stable rewrite baseline `8b7796b` for trend snapshots (as the CI
workflow does) and use the PR or push base separately for changed-code gates.
`--base` alone governs new cycles, forbidden imports and changed-function gates;
`--baseline` never changes their pass/fail decision.
CI passes the recorded baseline artifact with `--baseline`; this makes the
final report compare directly with the evidence that was emitted for that
baseline, rather than relying on a branch name or an implicit merge base.
The evidence records the requested names and their resolved commit SHAs; all
snapshot measurements use those SHAs, so a dirty worktree cannot alter them.
Use the same commit for `--base` and `--head` to capture a baseline snapshot.
The report records rename-aware 30-, 90-, and 180-day line churn. Hotspots are
ranked as normalized 180-day churn multiplied by cyclomatic complexity density;
coupling, cycles, cognitive complexity, maintainability, defect history, and
revision-bound typing indicators are reported independently. The typing
indicators report annotated-parameter and annotated-return coverage plus
`Any` annotations, `type: ignore` directives, and casts to `Any`; repository-wide strict `ty`
verification remains part of the Qt6 verification lane.

Add `--sync` when the environment may be stale. Add `--require-r-evidence` when R is required, or `--skip-r-evidence` when a separate full R run owns that evidence.

During development, run the narrowest relevant test file first. The maintained suites are grouped by execution needs:

- `tests/e2e`: complete desktop workflows using the production Qt/R stack
- `tests/python/fast`: boundary, corruption, concurrency, and failure tests
- `tests/python/gui`: interaction, layout, and failure cases outside the E2E scenarios
- `tests/analysis_regression/golden`: statistical regression tests
- `tests/r_stack`: Python-to-R integration tests
- `tests/packaging/contract`: package validation, relocation, and tampering tests

The required `r-stack` lane runs the desktop E2E suite after installing the pinned
R dependencies and the current RCMetaR source. For a warm local run, generate the
Qt forms with `python scripts/build_qt6.py generate --build-root build/qt6-verification`,
set `RCMS_R_HOME` and `RCMS_R_LIBS` to that installed runtime and library, and run
`uv run pytest tests/e2e -q`. Missing R dependencies fail the suite; they never skip it.

Prefer a complete workflow assertion about saved data, numerical results, displayed
content, or exported plots. Keep a smaller test only when it exercises a meaningful
case the desktop scenarios miss, such as malformed archives, failed atomic saves,
partial calculations, rollback, concurrency, or a platform-specific validator.
Source-string assertions, declaration inventories, and tests that merely return
their own mock's expected value do not qualify. See [the coverage decisions](testing.md).

For a workflow proof with persistent screenshots, action records, runtime identity,
and saved artifacts, use the project [Verify RCMS skill](../.agents/skills/verify-rcms/SKILL.md).
`uv run python scripts/verify_rcms.py doctor` checks a configured development runtime;
`uv run python scripts/verify_rcms.py amino` captures a binary analysis in a unique
`artifacts/verification/rcms/` directory. Add `--native` for host-platform rendering.
The helper uses the same real Qt/R driver as the E2E suite and preserves evidence
after cleaning its isolated settings and analysis scratch directory.

Run strict collection after changing test configuration or suite structure:

```powershell
uv run pytest --strict-markers tests --collect-only -q
```

For Qt source or GUI changes, generate the forms and run the relevant native lane:

```powershell
.\scripts\verify-qt6.ps1
```

This command generates Qt6 modules, runs Ty, and then runs the GUI and native smoke stages. CI can select one lane:

```powershell
.\scripts\verify-qt6.ps1 -Section Core
.\scripts\verify-qt6.ps1 -Section RemainingSurfaces
```

Ty checks `src/rc_metastudio`, `scripts`, `tests`, and `r/RCMetaR/inst/qa`. Generated Qt modules take precedence over the editable `.ui` sources during the check.

## Build the Linux package

The release package is qualified on Ubuntu 24.04 x86_64. Run the package command
on that platform to create the portable archive and its qualification evidence:

```bash
sudo apt-get update
sudo apt-get install -y xvfb libegl1 libx11-xcb1 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-randr0 libxcb-shape0 libxcb-util1 libxcb-xkb1 libxkbcommon-x11-0 librsvg2-2 libdeflate-dev libzstd-dev libtirpc-dev liblzma-dev libbz2-dev libblas-dev liblapack-dev libgfortran5 libgomp1 libtk8.6
bash scripts/package-linux.sh
```

The command writes `artifacts/RCMetaStudio-linux-x64.tar.gz`. The archive
contains the application, private R runtime, and `LaunchRCMetaStudio.sh`.
Other Linux distributions are not part of the release qualification baseline.
The [packaged smoke requirements](verification/linux-packaged-smoke-fix.md)
describe the native startup and bundled-runtime checks.

## Workspace and import limits

Workspace history retains the latest 100 committed edits. An operation that raises
restores its pre-operation snapshot; selecting a sheet does not create an edit or
change the sheet restored by Redo. History stores one snapshot per step.

XLSX import accepts worksheet extents up to 100,000 rows, 512 columns and
1,000,000 cells. This includes distant formatted cells in the workbook's declared
extent. Trim unused worksheet rows/columns before importing a file above those
limits. Formula imports use saved values and still require saving in Excel first.

## Work with generated Qt code

Files under `src/rc_metastudio/forms/*.ui` are the editable form sources. Generated Python modules belong under the selected build directory and must not be committed. `scripts/build_qt6.py generate` compiles forms and resources before tests, typing, or packaging.

## Repository layout

See [file names and ownership](file-ownership.md) for detailed module
responsibilities, relocation rules and public contracts.

- `src/rc_metastudio`: application code and packaged resources
- `r/RCMetaR`: bundled statistical package
- `sample_projects`: user-facing example projects
- `scripts`: build, verification, and release commands
- `packaging`: PyInstaller and platform packaging definitions
- `config`: machine-readable policy used by builds and tests
- `tests`: executable behavior and distribution contracts

Keep machine-readable contracts beside their consumer. Keep frozen test data under `tests`, not under `docs`.

## Where a change belongs

Use the same map for human and agent work. Start at the boundary responsible for the behavior, then follow its callers. A large file is not by itself a reason to split it.

| Responsibility | Main owners | Contract to preserve |
| --- | --- | --- |
| Workspace changes and undo/redo | `workspace_session.py`, `workspace_editing.py`, `dataset_table_model.py` | Stable sheet and row identities, atomic edits and rollback. |
| Project persistence | `project_format.py`, `project_adapter.py`, project schemas | Safe archives, durable saves and supported older-project migration. |
| Analysis configuration and execution | `analysis_setup_dialog.py`, `analysis_adapter.py`, `r_bridge.py`, `r/RCMetaR` | Included data, selected inputs and methods, real R execution and package authority. |
| Results and written output | `analysis_results.py`, `result_formatting.py`, `manuscript_report.py` | Exact numerical quantities, interval levels, interpretation and complete report content. |
| Plot editing and export | `plot_service.py`, plot editor dialogs and RCMetaR plot producers | Saved plot parameters, original output preservation on failure, readable decoded exports. |
| Qt forms and shared behavior | `forms/*.ui`, `qt_layout.py`, form manifest and generator | Editable Designer sources, generated files outside source, keyboard and native layout behavior. |
| Verification and releases | `scripts/verify.py`, verification feature maps, `packaging/`, workflows | Repeatable inputs and commands, pinned runtime identity and platform-specific qualification. |

Python filenames above are under `src/rc_metastudio/`. Read [CONTEXT.md](../CONTEXT.md) and the relevant [architecture decisions](adr/) before changing a cross-boundary assumption. The [project-format reference](project-format.md), [testing guide](testing.md) and [verification feature map](../.agents/skills/verify-rcms/features/README.md) hold the detailed contracts.

Do not move statistical policy into a widget or reconstruct exact numbers from displayed text. Before a behavior change, identify a real workflow or failure case that can distinguish the old and intended behavior. Migrate callers to the new owner and remove the superseded route in the same change.

## Change versions

Use the version command so Python, RCMetaR, the lockfile, and changelog stay aligned:

```powershell
uv run python scripts/bump_version.py VERSION
```

Replace `VERSION` with the intended release version. Review the generated changelog heading and complete its release notes before publishing. See [Releasing RC MetaStudio](release.md) for the hosted build and promotion steps.

## License notices

New maintained source files use:

```text
SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
SPDX-License-Identifier: GPL-3.0-or-later
```

Preserve accurate original authorship in derived files. Do not label third-party code or assets as RC MetaStudio-owned. Before a release, review the components actually bundled into each artifact and add `THIRD_PARTY_NOTICES.md` if their licenses require notices beyond the included package metadata. Do not add an empty placeholder.
