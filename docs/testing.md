# Test coverage decisions

The desktop E2E suite uses a fresh Python process, the normal application
composition, generated Qt forms, the production rpy2 bridge, and an installed
RCMetaR package. It runs in the required Full R Stack Evidence lane. Missing
dependencies, unexpected error dialogs, hangs, and crashes fail the suite.

| Workflow | Observable result |
| --- | --- |
| Binary, continuous, diagnostic projects | Correct studies and inclusion; selected method runs; displayed estimates and intervals match the frozen numerical oracle; Qt renders the SVG; PDF export succeeds |
| Table editing | Unicode editor commits; Return advances; undo/redo restores values and dirty state; saved edits survive reopening; corrupt open preserves the document and destination |
| CSV import | Quoted Unicode study names, numeric and factor covariates, and raw counts reach the workspace, analysis, and saved project |
| Plot editing | Apply changes a real R plot and persisted parameters; Cancel discards the subsequent draft |
| Small-study effects | The application action opens configuration, runs the authority package, displays the automatic test, and renders a real funnel plot |
| Three calculator families | Comma-decimal input reaches R; accepted changes survive undo/redo and save/reopen; cancelled changes disappear; edited data remain analyzable |

Native file pickers return test-owned paths. The corrupt-project scenario observes
the error message without opening a blocking message box. Calculations, storage,
analysis dispatch, result presentation, and rendering use production code.
Settings and analysis artifacts are isolated. The default Qt offscreen platform
allows CI execution; the suite does not establish native DPI or window-manager
behavior.

Removed checks include copied label and registry tables, source-string and XML
inventories, workflow topology snapshots, retired implementation-name assertions,
mock-only delegation tests, and happy paths now exercised through the desktop.
Unused imports, helpers, and inventories were removed with them. Existing native
package qualification and live golden analyses remain responsible for deployment
and the broader statistical workflow matrix.

The remaining smaller tests need a concrete failure the desktop scenarios miss:

| Coverage retained | Why E2E does not replace it |
| --- | --- |
| Project parsing and atomic persistence | Malformed ZIP/JSON, duplicate members, resource limits, unsupported versions, failed replacement, and post-replacement durability failures require hostile inputs or controlled I/O failures |
| Analysis boundaries and R transactions | Invalid requests/results, partial diagnostic success, Unicode/NULL/typed-NA conversion (including literal "NA" labels), nested transactions, and concurrent calls are outside ordinary sequential desktop workflows |
| Statistical calculations and golden comparison | Zero cells, partial raw data, entered effect estimates, unavailable statistics, unusual measures, Reitsma variants, and oracle tampering require independent numerical and rejection checks |
| Workspace and plot rollback | Failed calculations, partially promoted plot files, and failed saves must preserve the previous usable state |
| GUI edge cases | Invalid inputs, partial diagnostic failure, long labels, fractional scale factors, narrow viewports, keyboard focus, remaining calculator alternatives, and failure recovery exceed the 75 desktop workflows |
| Packaging and evidence validators | Wrong architectures, unresolved imports, forged hashes, symlink escapes, absent provenance, and relocation failures require deliberately invalid artifacts |
| Verification tools | Revision-bound Git metrics, unsafe output directories, installer failure handling, and timeout cleanup have their own observable failure modes |

When adding coverage, extend a workflow if the bug can be demonstrated there.
Otherwise identify the missed failure and assert its externally meaningful
result. Returning a mock's own value or checking that source contains a chosen
spelling is insufficient.

The extended suite runs all eight New Dataset paths (single and double arm,
entered estimates, and diagnostic counts), fixed estimators, cumulative and
leave-one-out analyses, subgroup analysis, meta-regression, joint and combined
diagnostic analysis, and extended small-study procedures. Binary and continuous
extended analyses compare the frozen numerical contracts. Independent current-source
R comparisons cover 19 metric families, ten heterogeneity estimators, four inference
choices, and zero-cell correction policies. The verification skill records the
remaining combinations and UI entry points that need a targeted drive.

The 31 advanced desktop cases cover alternate estimator/inference/CI choices,
excluded studies and zero-cell policies; twelve calculator modes with independent
preview and post-reopen pooled results; eleven editors with decoded PDF/PNG/TIFF/SVG
exports; and structure, covariate clipboard/sorting, recent-file and dirty-open
transactions. Source-owned feature recipes identify combinations still requiring
a targeted drive. TIFF alpha compositing retains a smaller numerical pixel test:
the desktop white-margin check would miss incorrectly blended colored pixels.

The second cleanup removes 65 Python test functions overall and three R blocks: duplicated
desktop happy paths, serialization and preset inventories, immutable-object checks,
Qt role boilerplate, and comparisons that construct their expected effects with
the same preparation function under test. Independent package calculations replace
those R checks. Rejection, partial-success, atomic-write, rollback, unusual-data,
native-layout and artifact-tampering cases remain when they expose a distinct
failure outside the desktop matrix.

Two removed functions represented nine permanently skipped cases for a retired
calculator history contract. They supplied no verification. Frozen sample-project
semantics and custom small-study settings remain because default desktop paths
do not establish those contracts.

`coverage` is a locked uv development dependency. The repository configuration
measures branches and desktop child processes, omitting generated forms. After
configuring the real Qt/R runtime, measure E2E separately from the smaller checks:

```powershell
uv run python -m coverage run -m pytest tests/e2e -q
uv run python -m coverage combine
uv run python -m coverage json -o artifacts/verification/rcms/e2e-coverage.json
uv run python -m coverage report
```

Use `tests/python` instead of `tests/e2e` for smaller checks. Preserve separate
reports to distinguish real desktop coverage from mocked failure injection.
Coverage identifies unexercised code; it does not justify keeping a duplicate
assertion. It measures Python execution, not the R calculations or native usability.

The R-stack cleanup removes 17 duplicated testthat blocks, the 83-case standalone
nonempty-result smoke matrix, and two Python drivers that checked legacy API smoke
paths or repeated joint-result formatting. The real joint diagnostic window now
checks all four ratio rows and interval columns; the regression editor applies,
reopens, cancels and exports BMJ style. Existing desktop workflows exercise the
deleted standard, sequential, subgroup, combined-metric and moderator happy paths.
This does not establish every fixed-estimator/sequential/metric combination.
Independent public-package oracles and distinct rejection, partial-result,
geometry, encoding, missing-value and alpha-blending checks remain. Explicit axis
bounds use numerical expectations rather than another internal layout helper.
Desktop child processes run in fresh working directories with owned scratch files;
diagnostic CSV output must use that scratch directory, never a repository `r_tmp`.
