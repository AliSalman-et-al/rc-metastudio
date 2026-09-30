# Capability and released-journey baseline

This is a bounded inventory for issue #465. It records the analysis facade, input families, desktop routes, and evidence already checked into this checkout. It does not change statistical settings or claim that every listed capability has a current-release parity fixture.

## Scope and provenance

[ADR 0008, “Use the current release as the rewrite oracle”](adr/0008-use-the-current-release-as-the-rewrite-oracle.md) and parent issue [#464](https://github.com/AliSalman-et-al/rc-metastudio/issues/464) name RC MetaStudio 0.3.1 as the behavior oracle. The inspected source checkout identifies both RC MetaStudio and RCMetaR as 0.4.1. The checked-in golden captures identify themselves as RC MetaStudio/RCMetaR 0.3.0 and `authority: local-debug`, with `authoritative: false`; their observed Windows/PyQt 6.11/R 4.6.1 environment also differs from the declared PyQt 5.15.11/R 4.6.0 baseline environment. The frozen captures are useful pinned historical evidence, but they do not establish behavior of release 0.3.1.

The published [v0.3.1 stable release](https://github.com/AliSalman-et-al/rc-metastudio/releases/tag/v0.3.1) is bound by its release set to source commit `f488ba0c01ec458b5e99fa2b5fc9b539872ae1ec`. Its Windows archive SHA-256 is `aeb6c9fdcbf00d8762284260ce3cdd7ffa722207d29599d1a428fa00ef30f7bd`. No result from that packaged artifact has been recaptured here. The tag's golden capture metadata still expects Windows/PyQt 5.15.11/R 4.6.0, while its own dependency pins use PyQt6 6.11.0/R 4.6.1; its compatibility script forces `local-debug` capture mode. Correct that provenance before treating a new source capture as release authority. The existing 0.3.0 numeric contract matches the contract committed at the v0.3.1 tag, which narrows the numeric gap but does not establish packaged application parity.

The structured inventory lives in [released-capability-inventory.json](../tests/analysis_regression/baseline/released-capability-inventory.json). It records the inspected revision, hashes the three sample projects used by the golden route, records their included study order, and gives each RCMetaR family/workflow/method combination either a fixture reference or an explicit gap. The gap between the requested 0.3.1 oracle and this 0.4.1 source snapshot needs resolution before claiming release parity.

The statistical authority matrix below comes from `rcmetar.analysis.methods()` and `rcmetar.available.methods()` in `r/RCMetaR/R/rcmetar-core.R`. Metric names come from `src/rc_metastudio/meta_globals.py` and the typed request family contract in `src/rc_metastudio/analysis_adapter.py`. Method feasibility is data-dependent: the authority filters methods against the selected data and metric, so the family metric list is not a guarantee that every method accepts every measure or input shape.

## Input families and measures

The desktop creation page has eight choices mapped to three statistical families:

| Family | Reachable representations | Measures offered by the desktop |
| --- | --- | --- |
| Binary | One-arm proportions; two-arm proportions | One arm: PR, PLN, PLO, PAS, PFT. Two arms: OR, RD, RR, AS, YUQ, YUY. |
| Continuous | One-arm mean; single regression coefficient; generic entered effect; two-arm means; two-arm SMD | One arm: TX Mean. Two arms: MD, SMD. |
| Diagnostic | TP/FN/FP/TN counts; entered effect and confidence interval by metric | Sens, Spec, PLR, NLR, DOR. Reitsma requires raw counts and jointly models Sens/Spec. |

These are user-visible storage/input representations, not evidence that each representation has a pinned analysis output. The existing numerical projects exercise two-arm binary OR, two-arm continuous SMD, and raw-count diagnostic DOR. One-arm data, entered effect inputs, alternative binary and continuous measures, and diagnostic analyses from entered effects remain explicit gaps.

## Statistical authority combinations

The current RCMetaR facade declares the following methods. Every supported family/workflow/method combination is represented in the JSON inventory. “Historical fixture” means the named request has a pinned input and output in the existing 0.3.0 local-debug bundle. “Authority fixture” means an adapter test compares a pinned input against a public authority-package call. Neither label means that the current 0.3.1 release was captured.

| Family | Workflow | Methods | Desktop route |
| --- | --- | --- | --- |
| Binary | Standard, cumulative, leave-one-out, subgroup, bootstrap | `binary.fixed.inv.var`, `binary.fixed.mh`, `binary.fixed.peto`, `binary.random` | First four routes are desktop; bootstrap is authority-only. |
| Binary | Meta-regression | `meta.regression` | Desktop. |
| Continuous | Standard, cumulative, leave-one-out, subgroup, bootstrap | `continuous.fixed`, `continuous.random` | First four routes are desktop; bootstrap is authority-only. |
| Continuous | Meta-regression | `meta.regression` | Desktop. |
| Diagnostic | Standard | `diagnostic.fixed.inv.var`, `diagnostic.fixed.mh`, `diagnostic.fixed.peto`, `diagnostic.random`, `diagnostic.reitsma` | Desktop. Reitsma is count-based and joint. |
| Diagnostic | Cumulative, leave-one-out, subgroup | `diagnostic.fixed.inv.var`, `diagnostic.fixed.mh`, `diagnostic.fixed.peto`, `diagnostic.random` | Desktop. |
| Diagnostic | Meta-regression | `diagnostic.reitsma` | Desktop; additive joint Sens/Spec model. |

The authority exposes joint Reitsma only for standard analysis and meta-regression. Joint cumulative, leave-one-out, and subgroup Reitsma are not in the supported method matrix. The removed `diagnostic.hsroc` and `diagnostic.bivariate.ml` identifiers are rejected; [ADR 0005, “Use mada Reitsma for joint diagnostic models”](adr/0005-use-mada-reitsma-for-joint-diagnostic-models.md) names Reitsma as the supported joint count-based model.

`bootstrap` remains present in the authority method matrix for binary and continuous data but has no main-window action and is not among the desktop workflows advertised in `README.md`. `rcmetar.run.permutation()` is also exported by RCMetaR, but it is not part of the analysis method matrix and has no desktop route. Both are listed separately in the JSON because parent issue #464 requires an explicit inventory of non-primary APIs before changing scope.

## Existing pinned analysis evidence

The frozen analysis bundle contains 11 historical captures: binary random OR, cumulative OR, leave-one-out OR, subgroup OR, and meta-regression OR; continuous random/cumulative/leave-one-out/subgroup SMD and meta-regression SMD; and diagnostic random DOR. The bundle includes request parameters, text outputs, plot descriptors, and rendered artifacts. The companion numeric contract pins 415 expected numeric values with tolerance `max(0.001, 1e-9 * abs(expected))`; `plot-descriptors.json` pins 11 plot capability descriptors. Two accepted output exceptions are recorded in `exceptions.json`: the inference-method output section and reviewed meta-regression summary/reference text.

The sample projects are input fixtures too. `released-capability-inventory.json` records their SHA-256 hashes and source-order included study names. The cumulative implementation consumes the input order. The golden cases add deterministic `golden_group` or `golden_year` covariates for subgroup and meta-regression cases and record those definitions with the fixture entries. This pins the evidence used by those historical runs without inventing an ordering policy for other projects.

The two Reitsma tests in `tests/r_stack/test_reitsma_golden.py` compare standard output and meta-regression coefficients to public `mada::reitsma()` behavior using `mada` 0.5.12. They pin the input data and tolerances but compute reference outputs through the public package at test time; they are authority comparisons, not frozen 0.3.1 reports.

## Reachable journeys and secondary actions

The inspected desktop source and existing Qt tests cover these reachable routes. Evidence is mostly source-level or automated UI behavior; it is not a packaged current-release journey capture.

| Journey or action | Evidence and current boundary |
| --- | --- |
| Start, create a dataset, open an `.rcms` project, choose a recent project, open a packaged example, or import CSV | `main_wizard.py`; wizard and CSV journeys in `tests/python/gui/test_main_wizard_workflow_layout.py` and `test_csv_import_wizard.py`. The welcome page exposes an example-project choice when samples are installed. |
| Choose an input representation, edit study data, add variables, use copy/paste/undo/redo, and calculate or back-calculate effects | `main_wizard.py`, `main_window.py`, `calculator_service.py`, and `calculator_routines.py`; Qt and fast coverage includes main-window data workflows and `test_calculator_qt6.py`. Only three input shapes are in the pinned analysis bundle. |
| Run standard, cumulative, leave-one-out, subgroup, or meta-regression analysis | `main_window.py` actions and `analysis_setup_dialog.py`; configuration and diagnostic workflow tests exist. The method/measure coverage is the matrix above. |
| Run small-study effects analysis through the “Publication Bias” action | `publication_bias.py`, `publication_bias_dialog.py`, and `r/RCMetaR/R/publication_bias.R`; the README documents eligibility-gated tests, funnel types, trim-and-fill, and exploratory infinite-precision estimates. Tests cover request contracts and UI behavior, but there is no complete pinned release fixture for eligibility decisions and outputs. |
| Inspect results; regenerate/edit supported plots; export figures | `analysis_results.py`, `plot_capabilities.py`, `plot_service.py`, and `results_window.py`. The README advertises PDF, PNG, SVG, and TIFF. The golden bundle pins plot metadata/artifacts for its 11 analysis captures; packaged edit/export qualification is tracked separately in [the qualification record](qualification-evidence-2026-09-29.md). |
| Save or reopen a project | `project_format.py`, `project_adapter.py`, and `saved_analysis.py` implement version 2 project history with portable figures. Project format/adapter tests and selected package journeys cover saved records; the 0.3.1 release-parity and full capability matrix remain open. |

Other exported RCMetaR helpers cover data preparation, study-effect calculations, imputation/back-calculation, plot serialization/rendering, and permutation analysis. The JSON inventory separates these public APIs from desktop journeys so their compatibility scope can be reviewed explicitly.

## Verification gaps

The current baseline is useful as a migration starting point, but it does not yet satisfy the release-parity target:

- Capture the named 0.3.1 release authoritatively and reconcile it with the checked-out 0.4.1 source version and 0.3.0 historical captures.
- Add release-pinned input/output fixtures for the method/workflow cells marked `gap` in the JSON matrix. Existing golden fixtures cover only one measure per family/workflow and one selected method per cell.
- Add representative numerical or semantic evidence for one-arm binary/continuous data, entered effect representations, alternative measures, fixed/Mantel-Haenszel/Peto methods, and diagnostic entered-effect eligibility.
- Pin eligibility and output behavior for the small-study effects procedures, including why methods are unavailable, and cover the separate Deeks geometry.
- Decide and document the migration target for authority-only bootstrap and permutation routes.
- Pin complete released user journeys for import, calculator application, project/result persistence, figure edit/export, and platform-qualified application behavior. Current source/Qt tests do not certify packaged Windows, macOS, or Linux journeys.

## Verification performed

- `python3 -m json.tool tests/analysis_regression/baseline/released-capability-inventory.json >/dev/null` passed.
- A standard-library integrity check passed for the three outer manifest hashes/sizes, the 11 matching case IDs across the archive/numeric contract/inventory, all 415 numeric contract values, the three sample-project hashes, and all 50 method/workflow combinations (11 historical fixtures, 2 authority comparisons, 37 explicit gaps).
- The system R 4.3.3 could not load the pinned `rpy2` API. With the bundled R 4.6.1 from the repository's Linux integration artifact in API mode, `uv run --no-sync pytest -q tests/analysis_regression/golden/test_analysis_regression_compare.py` passed (43 tests).
- In that bundled runtime, `scripts/verify_golden_compatibility.py` passed all 11 live captures against the committed golden bundle: 461 comparison rows passed and 13 matched documented exceptions. The capture requires its normal `r_tmp` output directory. This is source and frozen-contract evidence; it does not qualify a packaged platform.
- The `cases` values in the committed numeric contract equal the numeric contract at the `v0.3.1` Git tag. Their file hashes and capture provenance differ, so this narrows the numerical gap without turning the local-debug bundle into an authoritative 0.3.1 desktop capture.

These checks validate the inventory, existing frozen artifacts, and live source behavior against that bundle. They do not recapture the 0.3.1 packaged application or qualify a packaged platform.
