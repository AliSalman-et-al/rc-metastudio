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
| Analysis boundaries and R transactions | Invalid requests/results, partial diagnostic success, Unicode/NULL conversion, nested transactions, and concurrent calls are outside ordinary sequential desktop workflows |
| Statistical calculations and golden comparison | Zero cells, partial raw data, entered effect estimates, unavailable statistics, unusual measures, Reitsma variants, and oracle tampering require independent numerical and rejection checks |
| Workspace and plot rollback | Failed calculations, partially promoted plot files, and failed saves must preserve the previous usable state |
| GUI edge cases | Invalid inputs, multi-metric diagnostics, long labels, fractional scale factors, narrow viewports, keyboard focus, cancellation, and failure recovery exceed the ten default workflows |
| Packaging and evidence validators | Wrong architectures, unresolved imports, forged hashes, symlink escapes, absent provenance, and relocation failures require deliberately invalid artifacts |
| Verification tools | Revision-bound Git metrics, unsafe output directories, installer failure handling, and timeout cleanup have their own observable failure modes |

When adding coverage, extend a workflow if the bug can be demonstrated there.
Otherwise identify the missed failure and assert its externally meaningful
result. Returning a mock's own value or checking that source contains a chosen
spelling is insufficient.
