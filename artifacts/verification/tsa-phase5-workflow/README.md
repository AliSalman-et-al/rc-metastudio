# TSA workflow verification

## Spec disposition

| Item | Status | Result |
| --- | --- | --- |
| 1. Change settings | Done | BCG reran in the same window. Changing power alone raised RIS from 117,364 to 157,117. An entered OR survived reopening. A later live-sheet edit did not affect the original study snapshot. The unchanged rerun left the saved project clean. |
| 2. Fixed-effect comparison | Done | Peto reported D² of 95% and a calculated comparison size of 109,848 participants. This uses the Peto default OR of 0.6738 with the REML D², as required by the same-input rule. The REML primary BCG analysis uses a different default OR of 0.6835 and gives 117,364. MD exercised the zero-D² notice. |
| 3a. Grouping | Done | Design assumptions and Monitoring use bold headings. Advanced opens from its existing collapsed control. |
| 3b. Effect equivalents | Done | The measure is in the row label. The relative change or percentage-point equivalent follows the source where applicable. |
| 3c. Inflation | Done | D² or I² shows the corresponding size multiplier. None omits the multiplier. |
| 3d. Tooltips | Done | The specified text is on labels and editors. For checkboxes, the control also serves as the label. |
| 3e. Percent precision | Deviated for hundredths | Whole and tenth-percent values display one decimal, including 5.0% and 80.0%. Values that require hundredths, including the original range endpoints, keep two decimals. Qt rounds range endpoints to the control's numeric precision, so enforcing one decimal everywhere would alter the valid range and some saved settings. |
| 3f. Preview outcome | Done | The 120 ms RIS debounce and the 600 ms background conclusion debounce run independently. The BCG drive clicked Run while the separate local R worker was active. |
| 4. Numerical table | Done | Signed monitoring boundaries, measure-and-level CI headers, optional columns and the dash note are reflected in the report and exports. BCG verified that a dashed limit still exports its exact numeric value. The frozen numerical baseline changed only in its column labels. |
| 5. Report prose | Done | Ordered-study and anticipated-effect wording, conclusion sentences and the figure caption note are in the manuscript. The decoded PDF and DOCX contain the marker-area note. |
| 6. Sensitivity | Done | Table 2 uses the same fitted looks. BCG verifies identical primary summary and final look, and the standalone 10% RRR RIS. The desktop cases cover report navigation and clipboard, PDF, DOCX and both CSV exports. Manual RIS omits the table and methods sentence. Alternative effects that imply infeasible event risks are labelled “Not estimable.” |
| 7. Low-risk default | Conditional item satisfied | RC MetaStudio does not store the required judgements. See the data check below. |

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
Poppler's `pdftotext` on PATH. Set `RCMS_R_HOME` to the packaged R 4.6.2 runtime
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

## Results

Product code was qualified at `2689d88a6108657520c254a4c80a02e92b8c2e13`.
The direct drives used the Windows Qt plugin with Qt/PyQt 6.12.0, Python
3.14.10, R 4.6.2, installed RCMetaR 0.5.6 built from the checkout, metafor
5.2-1 and gsDesign 3.11.0. The library selection is in each `runtime.json`.

| Command | Observed result | Local transcript |
| --- | --- | --- |
| `& $replay typing -Run delivery` | Repository-wide strict Ty passed, target `win32`. The log contains the full executable command and generated-form search paths. | `delivery/typing/typing.log` |
| `& $replay r -Run delivery` | Five R suites passed, including all TSA numerical expectations and the new BCG sensitivity test. RCMetaR installed into the test-owned library. | `delivery/r/r-tests.log`, `delivery/r/install.log` |
| `& $replay python` | 869 passed, one skipped and one failed. The same failure reproduces at base `4151624c` in `test_result_owner_exception_still_deletes_real_specs_and_progress`, where the test's model double has no `is_diagnostic` method. | `qualification/python/python-tests.log`, `final/python/baseline-failure.log` |
| `uv run python -m pytest -q tests/python/gui/test_results_workspace_layout.py --basetemp .tmp/tsa-phase5-results-final` | All 61 affected Results tests passed on the delivery source. | `delivery/python/results-workspace.log` |
| `& $replay native100 -Run delivery` and `& $replay native150 -Run delivery` | Runtime doctor and six native cases passed at both scales. The cases were BCG, HR, MD, RR/MH, SMD eligibility and the 36-look stress case. All 14 manifests and their artifact hashes were audited. | `delivery/native100/`, `delivery/native150/`, `delivery/audit.log` |
| `& $replay full -Run candidate` | R CMD check passed with 2,612 test assertions, zero failures and 15 test warnings. The 103 authority comparisons, 21 deterministic Reitsma visual cases and nine bridge tests passed. The supplemental all-app offscreen matrix was still running at delivery. | `candidate/full/`, `delivery/full/`, `../rcms/20261119T003500Z-7a0ef587-complete/` |

For native replay, each case uses `uv run python scripts/verify_rcms.py
<scenario> --native` with `QT_SCALE_FACTOR` from its lane's
`environment.log`. Both native lanes keep these captures under the scenario
directories.

| Capture | Case | File |
| --- | --- | --- |
| Regrouped binary dialog | `plot-workflow-trial-sequential` | `04-0-tsa-dialog-default.png` |
| Regrouped HR dialog | `tsa-hr` | `02-0-tsa-configured.png` |
| Regrouped MD dialog | `tsa-md` | `02-0-tsa-md-calculated-preview.png` |
| Peto comparison notice | `plot-workflow-trial-sequential` | `02-0-tsa-peto-fixed-effect-notice.png` |
| Report at Table 2 | `plot-workflow-trial-sequential` | `14-0-tsa-sensitivity-report.png` |
| Change settings and its result | `plot-workflow-trial-sequential` | `15-0-tsa-change-settings-dialog.png` through `18-0-tsa-change-settings-result.png` |

## Preview latency

The synchronous implementation took a median 227.03 ms on an early BCG run,
439.00 ms on BCG during the concurrent R stack build, and 1,854.30 ms on
Pignon HR. Those timings triggered the separate R worker. The delivery RIS
figures are seven warm computation samples and exclude the 120 ms debounce.
The conclusion column is the observed elapsed time from rescheduling a
preview to the conclusion appearing, including its 600 ms debounce and fresh
R process startup.

| Fixture | Device scale | RIS median | Conclusion elapsed |
| --- | ---: | ---: | ---: |
| BCG REML | 100% | 31.20 ms | 3,903.46 ms |
| Pignon HR | 100% | 51.86 ms | 5,501.58 ms |
| BCG REML | 150% | 38.53 ms | 4,155.74 ms |
| Pignon HR | 150% | 33.77 ms | 5,089.48 ms |

The native `tsa-preview-timings` steps retain the individual values.
