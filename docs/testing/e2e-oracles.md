# E2E oracle qualification

The bounded e2e-oracles-01 batch strengthens evidence, without changing product or R behavior or frozen numerical references.

| ID | Observable contract | Mapped drive |
| --- | --- | --- |
| G6B-001 | Configured precision equals the request; receipt records the observed spinbox | amino |
| G6B-002 | Required screenshot saves return success | sheets; calculator and XLSX paths retain the same assertion |
| G6B-003 | Default/RevMan require at least three capped interval rows; caps cannot cross row bands. BMJ deliberately draws uncapped intervals and uses its other plot geometry checks. | audit-round3-twoarm-proportion; audit-round3-round5 |
| G6B-007 | Entire mapped project, including stable identities, labels, raw data and covariates, survives reopening | ux-improvements |
| G6B-008 | Every imported study year matches the XML fixture, including empty/non-digit years | rm5-import |
| G6B-009 | Generic IV study counts, identities, years and numerical inputs match independent meta read.rm5 output | rm5-import |
| G6B-010 | Each expected interval consumes one line at its named study row | project-axis-others |
| G6B-011 | Header boxes stay inside SVG horizontal viewBox bounds | project-round6-polish |
| G6B-012 | Orders equal independent stable sorts of fixture years, fitted effects and weights; ties retain table order and missing years go last | review-workflows |

G6B-013 is separate maintenance: current `advanced_workflows.py` calls `round6_polish.run`, contrary to the historical no-caller claim. Preserve that entry point and `run_headers`; remove only the misleading sequential precision block that treated rounded display values as its own authority. This removal adds no numerical coverage claim.

Start with generated forms and the strict win32 typing gate, then use `uv run --locked python scripts/verify_rcms.py SCENARIO`. The helper retains exact commands, runtime, plots, persisted projects, steps, screenshots and hashed manifests. Select runtime-04 read-only as instructed by the parent batch; never install into it. Geometry controls are `uv run --locked python -m pytest tests/e2e/test_oracle_geometry_controls.py -q --basetemp artifacts/fixes/e2e-oracles-01/geometry-work-UNIQUE`.

Synthetic SVG controls isolate the rendered-output boundary; they do not establish statistical accuracy. Live drives use real Qt/R. The batch's ignored `artifacts/fixes/e2e-oracles-01/` contains malformed-output controls, baseline rejection failures, fault driver, exact environment/replay commands, failed attempts and final handoff. Faults modify owned child observations immediately before the real oracle: exported effect, reopened label, imported year/identity, ordering, precision or screenshot write status. Count a control only when its defect marker and specific assertion are both present; startup/typing/wrapper failures are not proof. PDF text inclusion supplements exact DOCX cell comparisons and does not prove PDF cell geometry. Offscreen Windows source qualification does not qualify native shell, other platforms or release packages. Parent owns the aggregate full profile.
