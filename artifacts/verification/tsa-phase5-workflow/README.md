# TSA workflow verification

## Risk-of-bias data check

Searched `CONTEXT.md`, the project/domain model (`analysis_dataset.py`,
`project_format.py`, and `project_adapter.py`), the RevMan importer and review
dialog (`rm5_import.py`, `rm5_review_dialog.py`, and `docs/rm5-import.md`), and
the covariate creation, storage and selection paths (`dataset_table_model.py`
and `covariate_type_dialog.py`). Study rows have notes and generic covariate
values with no overall risk-of-bias judgement or standard covariate identity
for that purpose. RevMan import explicitly excludes risk-of-bias assessments.
The low-risk default and sensitivity row wait on study-level risk-of-bias
data.

## Replay

Use Windows x64 with the locked Python environment, generated Qt forms and
Poppler's `pdftotext` on PATH. Set `RCMS_R_HOME` to the packaged R 4.6.1 runtime
and `RCMS_R_LIBS` to a test-owned library seeded with the manifest-pinned
packages. The `r` lane builds and installs the checkout's RCMetaR into that
library. For a host at 125% OS scaling, the native lanes set Qt scale factors
0.8 and 1.2 for observed device scales 1.0 and 1.5. Override
`-SystemScale` to match a different host.

```powershell
uv sync --locked
uv run python scripts/build_qt6.py generate --build-root build/qt6-verification
$replay = "artifacts/verification/tsa-phase5-workflow/replay.ps1"
& $replay typing
& $replay r
& $replay python
& $replay native100
& $replay native150
& $replay full
```

The replay retains the native helper's manifests, commands, screenshots,
exported reports and project fixtures. Those files stay in the local evidence
directory because their paths and runtime metadata identify the host.
