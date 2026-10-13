# Meta-analysis

Users select included studies, choose a statistical method and parameters, run the analysis, and read package-authoritative numerical results and plots.

## Sub-features

- `analysis-binary`: amino project, binary random-effects analysis.
- `analysis-continuous`: continuous project, continuous random-effects analysis.
- `analysis-diagnostic`: lymph project, univariate diagnostic odds ratio.
- `analysis-extended`: cumulative, leave-one-out, subgroup, meta-regression, joint/combined diagnostics, moderator shapes, fixed estimators, and all dataset creation types.

## How to get to it (user POV)

- Open a project, then Analysis > Meta-Analysis or the matching toolbar button.
- Diagnostic projects first show the metric selection dialog.
- Analysis menu/toolbar also provides Cumulative Meta-Analysis, Leave-One-Out Meta-Analysis, Subgroup Analysis and Meta-Regression.

## Driving it with Qt E2E

Preconditions: doctor passes; committed samples and the frozen numerical contract are present.

- **Binary.** Run `uv run python scripts/verify_rcms.py amino`. The workspace shows Gonzalez and 19 included studies. `action_go` opens `AnalysisSetupDialog`; `method_cbo_box` selects `binary.random`; the Decimal places spinbox is set to three; the dialog OK button runs R. Displayed estimate/intervals match `amino-binary-random` within `0.001`.
- **Continuous.** Run `uv run python scripts/verify_rcms.py continuous`. Carroll and six included studies reach `continuous.random`; compare with `continuous-random`.
- **Diagnostic.** Run `uv run python scripts/verify_rcms.py lymph`. Kinderman and 17 included studies reach metric DOR, then `diagnostic.random`; compare with `lymph-diagnostic-random-dor`. The public heading is Odds Ratio Summary; use typed section identity rather than assuming it is the internal text key.
- **Proof.** Each run records `analysis-action`, `analysis-configured`, `analysis-results`, and `numerical-oracle`. The results scene must display the actual summary and render valid SVG. `workflow/forest.pdf` must be a PDF export, not a renamed image.

## Gotchas

- Dataset length includes excluded studies; count inclusion, not rows alone.
- The selected model matters: a fixed-effects result can look plausible and still be wrong. Require the independent numerical contract.
- These three paths alone do not establish the extended workflows below. Run their real action drives and the corresponding numerical lane.
- Statistical authority packages own estimates; entered effect estimates and reconstructed analysis effect estimates are distinct from transient derived effect previews.

## Extended analysis action matrix

Invoke each scenario with `uv run python scripts/verify_rcms.py <scenario>`. `analysis_matrix.py` is the skill-owned extension of the shared desktop driver. Each invocation repeats doctor and records `matrix-action`, `matrix-configured`, displayed results, retained plots, and oracle/routing observations.

| Scenarios | User action/configuration | Numerical proof |
| --- | --- | --- |
| `analysis-amino-binary-cumulative`, `analysis-continuous-cumulative` | `action_cum_ma`, random-effects DL, three digits | All frozen cumulative numerical fields, not only final pooled estimate |
| `analysis-amino-binary-leave-one-out`, `analysis-continuous-leave-one-out` | `action_loo_ma`, random-effects DL | All frozen omission results |
| `analysis-amino-binary-subgroup`, `analysis-continuous-subgroup` | Factor fixture `golden_group`; `action_subgroup_ma`, `covariate_combo_box`, then setup | Frozen per-group and overall results |
| `analysis-amino-binary-meta-regression`, `analysis-continuous-meta-regression` | Continuous fixture `golden_year`; `action_meta_regression`, covariate checkboxes | Frozen coefficients, uncertainty and model results |
| `analysis-diagnostic-joint` | `action_go`, Sens/Spec, `diagnostic.reitsma` | Actual clinical interval columns, four complete ratio rows and I-squared text; valid SROC; pinned `mada` numerical tests and visual QA supplement |
| `analysis-diagnostic-combined` | Select Sens/Spec/LR/DOR through metric checkboxes; combined method panels | UI result/report presence for five metrics; univariate authorities and joint R lane supplement |
| `analysis-diagnostic-cumulative`, `analysis-diagnostic-leave-one-out`, `analysis-diagnostic-subgroup` | Corresponding action, DOR univariate random; factor for subgroup | UI execution/plot; R sequential/subgroup tests supplement |
| `analysis-diagnostic-regression-continuous`, `analysis-diagnostic-regression-factor`, `analysis-diagnostic-regression-multiple` | Joint Reitsma regression; one numeric, one factor, both | UI model execution; R `mada` regression/21-case visual lane supplement |
| `analysis-binary.fixed.inv.var`, `analysis-binary.fixed.mh`, `analysis-binary.fixed.peto`, `analysis-continuous.fixed`, `analysis-diagnostic.fixed.inv.var`, `analysis-diagnostic.fixed.mh`, `analysis-diagnostic.fixed.peto` | Actual method selector, OR/SMD/DOR compatible sample | UI selection/execution; independent public-package matrix below supplements |

Covariate injection constructs a controlled fixture; these drives do not establish covariate CRUD UI. Regression explicitly unchecks every covariate to require disabled OK, then checks the intended covariates. Subgroup requires a complete factor covariate. Shared diagnostic confidence/digits/correction and the LR/DOR panel must not silently override each other.

## Dataset/metric matrix

`analysis-data-*` starts **Dataset > New Dataset** through `action_new_dataset`, clicks the real data-type button, advances the metric/name pages, finishes, populates study cells through validated table edits, saves/reopens `typed.rcms`, then analyzes. It does not bypass wizard type selection.

| Scenario suffix | Arms/type | Default metric | Supported metric domain to verify after shared reconstruction changes |
| --- | --- | --- | --- |
| `onearm-proportion` | One arm binary proportion | PR | PR, PLN, PLO, PAS, PFT |
| `onearm-mean` | One arm continuous mean | TX Mean | Mean with N/Mean/SD |
| `reg-coef` | One arm regression coefficient | TX Mean | Entered coefficient and lower/upper confidence bounds |
| `generic-effect` | One arm generic effect | TX Mean | Entered estimate and standard error; distinct from raw reconstructed effects |
| `twoarm-proportion` | Two arms binary | OR | OR, RR, RD, AS, YUQ, YUY |
| `twoarm-mean` | Two arms continuous | MD | MD, SMD |
| `twoarm-smd` | Two arms standardized mean difference | SMD | SMD, MD; calculator pre/post modes need their own drives |
| `diagnostic` | TP/FN/FP/TN | Diagnostic metric dialog | Sens, Spec, PLR, NLR, DOR; joint Sens/Spec Reitsma |

The independent matrix constructs effects for all binary metrics, MD/SMD/one-arm mean/entered estimates and five diagnostic measures, then compares supported fixed/random fits with public `metafor` calls. It also checks all HE/DL/HS/HSk/SJ/ML/REML/EB/PM/PMM × z/t/knha/adhoc combinations at a nondefault 90% confidence level on a binary fit. This is numerical backend proof; the eight wizard scenarios establish default type routing, not every metric-menu choice or every parameter UI combination.

```powershell
$taskRscript = Join-Path $env:RCMS_R_HOME 'bin/Rscript.exe' # Windows; POSIX uses bin/Rscript
$env:R_LIBS = $env:RCMS_R_LIBS
& $taskRscript .agents/skills/verify-rcms/scripts/analysis_authorities.R artifacts/verification/rcms/authorities.json
```

The R script loads current `r/RCMetaR` source with pkgload, validates six pinned authorities, and writes actual/expected values plus fields compared at `1e-8 * max(1, abs(expected))`. Fixed MH supports OR/RR/RD; Peto is OR-only. Diagnostic MH supports DOR/PLR/NLR. Reitsma requires complete counts and joint Sens/Spec; it is unavailable for sequential/subgroup workflows. Do not force an unsupported method×metric Cartesian product.

## Required targeted cases after analysis changes

`analysis-sequential-fixed-{cumulative,leave-one-out,subgroup}` drives all three
workflows with binary MH, binary Peto and continuous fixed inverse variance.
`analysis-sequential-diagnostic-{cumulative,leave-one-out,subgroup}` selects Sens
and Spec together with both fixed inverse variance and random effects. Every
displayed study-prefix, omission, subgroup and overall estimate, lower/upper CI
and standard error matches independent public `metafor` fits within `1e-6`.
These replace the fixed and multimetric route checks in the removed standalone
smoke matrix. Subgroup fixtures inject a factor; `project-table-covariates` proves
the actual covariate creation path. Single-study rows use the public study effect
and normal interval, reflecting the application's single-study result contract.

Automated `options-binary`, `options-continuous`, and `options-diagnostic` drive REML/Knapp-Hartung, PM/t, and ML/modified Knapp-Hartung through actual parameter controls at 90% CI and six digits. All eight pooled/inference/heterogeneity fields match independent public `metafor` fits. `options-confidence-inclusion` changes global CI, undoes/redoes it, excludes Gonzalez using the inclusion cell, saves/reopens, and verifies the inherited 90% CI, 18-study weights and independent subset fit. `options-zero-cells` enters single- and double-zero binary rows and drives both UI-supported policies (`only0`, `all`), checking the independent fit and all 19 weights. The backend-only `if0all` policy remains in the public-package matrix; it is not claimed as binary selector coverage.

`project-table-covariates` creates/pastes numeric Dose and factor Region through the UI, saves/reopens and uses them in regression/subgroup analysis. Independent public fits check the Dose coefficient/SE/interval/p-value and North/South estimates. Fixture injection in the older analysis matrix does not establish these CRUD paths.

- Change global CI through `action_change_confidence_level`, `ConfidenceLevelDialog.confidence_level_spinbox` and `button_box` OK. Require inherited analysis CI, changed interval, undo/redo, persistence, and independent nondefault-CI reference. Exercise precision and confidence boundaries without accepting invalid values.
- Select an alternate heterogeneity/inference pair through generated QLabel buddies and enum item data; require the report and numerical result to reflect the choice. Test correction policies on zero-cell data, including double-zero studies, and compare the exact included study set and effects.
- Exclude/reinclude a study through the inclusion checkbox; require study count, estimates and weights to change and restore. Use an entered-estimate fixture separately from raw data, and verify only supported diagnostic metrics/methods remain selectable.
- Regression: no covariate disables OK; missing moderator values show the exact excluded names. Click No and preserve the setup/project; click Yes and require exactly the complete-case subset. Exercise numeric/factor/multiple moderators, reference levels, fixed/random selection for binary/continuous, insufficient residual degrees of freedom and rank-deficient input with actionable recovery. Diagnostic regression offers a joint model, not a fixed-effects toggle.
- Subgroup: numeric and incomplete factor covariates must not be selectable. Require group membership, order, per-group results and overall result, including an excluded study and a small group.
- Diagnostic metric selection: none disables OK; Sens/Spec joint and optional LR/DOR requests yield the intended semantic sections. Combined Peto is deliberately unavailable. Counts, entered estimates and missing counts must not silently select a different model.

Run `uv run python scripts/verify.py r-stack` after shared statistical changes: current installed RCMetaR, retained numerical/eligibility/plot tests, 11 frozen golden cases, 21 Reitsma visual cases and all desktop E2E scenarios. Require no missing-runtime skips. R routines with no reachable current UI (e.g. legacy bootstrap/permutation helpers) are not advertised app functions; add coverage when a reachable surface is introduced rather than restoring removed workflows.


## Reported inference

Standard univariate results include the package-owned Z/t overall-effect statistic
and, for random models with more than two studies, `predict.rma` prediction limits.
PFT prediction limits explicitly retain calculation scale because a new study's
sample size is unspecified. Subgroup reports include the package's QM/F, degrees of
freedom and P beside within-group estimates. `output-authorities.R` in the
round-two evidence checks 84 metric/inference combinations against independent
public metafor fits. Keep that check separate from the unchanged frozen contract;
newly reported quantities must not replace or rewrite existing numerical oracles.

## HR and IRR

`options-zero-cells` verifies the shared Not estimable/dashes convention for complete, undefined effect previews. It contrasts SMD with no residual degrees of freedom against numeric MD, proves save/reopen and correction recovery, and keeps incomplete input blank. Finite previews keep their existing precision and zero-event policy.

See [ratios.md](ratios.md) for the compact input, original-source persistence, analysis, plot and small-study workflows. Run `ratios-hr` and `ratios-irr` after changes affecting these families; the broader shared-change lane remains required.
