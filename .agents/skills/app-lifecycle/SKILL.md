---
name: app-lifecycle
description: Check RC MetaStudio's app lifecycle statecharts and project-save invariants when changing project actions, saving, analysis/result ownership, or plot workflows; replay persistence failures and keep models aligned with code.
---

# App lifecycle and data safety

Read `docs/formal-verification.md` for the app charts, code correspondence, evidence,
scope and known abstractions. This is the single project-local formal verification
skill. `verify-rcms` remains the desktop/real-R driver; do not duplicate its workflow
matrix or introduce another formal skill for an already covered lifecycle boundary.

## Acceptance check for a candidate change

This skill evaluates modeled behavior; it does not choose or iterate improvements.
The promises below constrain saving and project-action consent, not layout or implementation. Review the diff
from the sync commit and confirm the model describes the candidate before trusting
a pass. If the invariant, verifier or code/model mapping changed, the corresponding
scratch mutation must still fail for the expected reason.

Use `verify-rcms` for the affected real-app and numerical checks and its broader
handoff gates. Report formal passes, failures and unexamined behavior separately,
with evidence for the candidate source/runtime. A missing prerequisite is a gap,
not regression clearance. Do not change a rule, test or oracle merely to accept a
candidate; changed expectations need an intended requirement change and a reason.

## Run

From the repository root, with the locked Python environment and Java 11+ on PATH:

```powershell
uv run python .agents/skills/app-lifecycle/check.py
```

The command prints a new scratch evidence folder outside the repository. It checks
`App.tla`, `ProjectSave.tla` and `UnsavedActions.tla`, then runs eight existing persistence failure tests
against a retained scratch copy of production source. It downloads TLC release
1.7.4 once, verifies its SHA-256, and records Java/Python versions, exact child
commands, input/output hashes, source revision, JUnit, logs and disposable project
files. Exit zero requires all three models and all eight named real-code checks to
execute and pass; missing or skipped checks cannot produce a pass. The manifest
records `outcome` and `replay_coverage`. Exit 1 means a modeled invariant or real
assertion failed; exit 2 means a tool/collection/report problem or incomplete
coverage. Inspect every model log and the replay log, not just the exit status. A tool/parse error is
not a finding.
An early setup failure may leave partial evidence; inspect stderr for the missing
prerequisite rather than treating the absent reports as completed checks.
Use `--out` with a new absolute directory to choose where evidence lives.

Formalize domain promises and user decisions, not the current screens, widget
classes, wording or click sequence. A redesigned UI may implement the same
transition differently; review its code/model mapping and update the driver
without weakening data/scientific/cancellation invariants. `CONTEXT.md` and active
ADRs define the app's intended direction; a statechart is not a frozen UI design.

Read **every TLA+ result with pstack `/statechart`**, using the copied inputs in that
run's evidence folder. Use `app.view.ts` and `analysis.view.ts` for the two app
projections, `save.view.ts` for save safety and `unsaved.view.ts` for user consent. Follow the installed `/statechart`
skill for its current execution/render commands; no launcher paths are embedded
here. Keep its report and shortest bug paths with the run evidence. See the report's
Windows note if the installed launcher/parser cannot process native TLC output.

## Properties and harm

| Invariant | Promise | Harm if broken |
| --- | --- | --- |
| `PreservePrevious` | Until replacement succeeds, the previous destination remains intact. | A failed save destroys the last usable project. |
| `InstallOnlyValidated` | Replacement installs only a reopened, validated temporary archive. | Unchecked or unreadable data replaces usable research. |
| `ReportInstalled` | An installed replacement is never reported as an ordinary failed save. | The workspace/UI can retain the wrong save identity or mislead the user about which project is installed. |
| `AuthorizeOnlyWithConsent` | Unsaved work can be replaced or closed only after explicit discard or an installed save. | Cancelled/failed saves can let a destructive action discard work. |

`App.tla` is an app-wide **overview**, with deadlock checking only. It does not
prove result snapshots, statistics or plot rollback.
Its phases are user-visible operation boundaries, not atomic Qt/R instructions.
`ProjectSave.tla` checks a single save, previous/new file identities and failures at
each pre-replacement phase and after replacement. Input preparation and temporary
file construction hide internal steps that do not modify the destination. A save
call is synchronous; this model does not introduce a background save race.
`UnsavedActions.tla` checks one clean/dirty project-action decision with Cancel,
Discard or Save and each save outcome. It maps `None`/`False`/`True` to cancelled,
failed and installed; durability uncertainty counts as installed per `MainWindow.save`.
The real Qt/R companion drives are `project-unsaved-actions` and
`project-unsaved-discard` through `scripts/verify_rcms.py`. Run them when changing
the guards; the default formal command alone does not exercise those GUI paths.

## Coverage and synchronization

Last code correspondence review: `f79aee5fe43fd7021f0e014955f533586136756e`.
Read the diff from that commit before trusting the models. Move this sync commit
forward **only after confirming that the model still describes the covered code**,
updating the mapping and rerunning both baseline and relevant mutations.

| Model/check | Covered code |
| --- | --- |
| App project flow | `main_window.py`: `start`, `_authorize_destructive_project_action`, `closeEvent`, `create_new_dataset`, `_import_csv`, `open`, `save`, `_handle_wizard_results`; `main_wizard.py`: page routing and `get_results` |
| App editing/analysis/results overview | `main_window.py`: `data_dirtied`, `undo`, `redo`, `go`, `cum_ma`, `loo_ma`, `meta_subgroup`, `meta_reg`, `publication_bias`, `analysis`; `analysis_setup_dialog.py`: `run_ma`; `results_window.py`: `ResultsWindow`, plot edit/export routes; `plot_editor_dialog.py`: `_commit`, `mark_commit_succeeded`, `mark_commit_failed`; `plot_service.py`: `apply_edits`, `export` |
| Save invariants | `project_format.py`: `save_project`, `_write_container`, `load_project`, `_fsync_parent_directory`, `_cleanup_temporary` |
| Unsaved-work consent | `main_window.py`: `_authorize_destructive_project_action`, `closeEvent`, `save`; `tests/e2e/unsaved_actions.py` drives New/Open shortcuts, Import/Quit menu entries and Close with real prompts and storage |
| Real-code replay | Eight named existing tests listed in `check.py`, from `tests/python/fast/test_project_format.py`; fault injection uses real ZIP/filesystem save/load, with synthetic I/O errors and simulated directory handles |
| Consumers reviewed, not formally checked | `workspace_session.py:WorkspaceSession.save`, `main_window.py:MainWindow.save` durability-error handling |

For the consent property's broken-code demonstration, a scratch change from
`self.save() is True` to `self.save() is not False` in the shared guard admits a
cancelled Save As. Run `project-unsaved-actions` through `scripts/verify_rcms.py`
in that scratch checkout: it must reject the unauthorized New wizard. In the
matching model variant, set `Mutation = "allow-cancelled-save"` in a scratch
`UnsavedActions.cfg` and read its violation with `/statechart`. Restore the code
and configuration and require both checks to pass. No GUI layout is part of this
property; the protected behavior is consent before losing unsaved work.

## Demonstrate that checks can fail

The failure list is deliberate: damage before replacement; install without
temporary validation; confuse post-replacement uncertainty with ordinary failure.
The runner applies each scratch change to production `project_format.py` and the
matching model variant. It never edits the working source tree.

```powershell
uv run python .agents/skills/app-lifecycle/check.py --mutation truncate
uv run python .agents/skills/app-lifecycle/check.py --mutation skip-validation
uv run python .agents/skills/app-lifecycle/check.py --mutation misclassify
```

Each must return exit 1 with a named invariant violation **and** the corresponding
real-code assertion failure, not a syntax/import/tool failure. Read those results
with `/statechart` too. `truncate` fails preservation on a failed `os.replace`;
`skip-validation` fails installation validation; `misclassify` fails the installed
error classification. Then run the baseline command again. No product-source
restoration is needed because mutations live only in their evidence folders.

## When a change is intentional

Replay any counterexample against real code in exactly its action order. Treat a
non-reproducing counterexample as a modeling error until shown otherwise. Preserve
real findings; do not weaken an invariant to get green. In a verification-only
task, report product defects without changing product code. During an authorized
improvement task, fix defects within that scope. Update intended flow changes in the model, source mapping and views,
then rerun the baseline/mutations and the affected `verify-rcms` workflow.

This check assumes same-directory atomic `os.replace` semantics, one writer, no
external destination modification and ordinary caught exceptions. It does not
prove power-loss/reboot durability, filesystem implementation, process termination,
multiple writers, arbitrary archive/parser inputs, numerical correctness, R
serialization, every wizard/control combination, multiple result windows, native
UI or packaging. Consult `/maintain-formal-verification-skill` after changes that
did not recheck this skill. Keep new formal checks here when adding another app
invariant; extend the coverage table rather than creating overlapping skills.
