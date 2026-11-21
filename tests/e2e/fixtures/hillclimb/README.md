# Hill climb inputs

binary.tsv is a headerless clipboard rectangle: study, year, intervention events,
intervention total, control events, control total. Twelve complete studies support
both subgroup/regression and the default small-study test. covariates.json gives
one Category (Region) and one Numeric (Dose) value per row, entered through the
real cell editors. T4 reuses tests/fixtures/desktop-projects/lymph.rcms (17 diagnostic studies).

Proof obligations: clipboard column order and row count; every covariate value;
actual result sections; preserved numerical output across repetitions; valid
text and plot-PDF exports; explicit noncompletion of manuscript PDF/DOCX.
Do not regenerate expected results to accept statistical drift.

## Compare workflow effort

The `hillclimb` scenario measures five fixed tasks through the shared real Qt/R
driver: create/paste/analyze binary data; add categorical/numeric moderators and
run subgroup/regression; run small-study effects; analyze the diagnostic sample;
and export the report and figures. Each run records its actual starting state,
performed gestures, completion status, numerical/text receipts and outputs.

After the strict typing gate and runtime setup in the
[verification skill](../../../../.agents/skills/verify-rcms/SKILL.md):

```powershell
uv run python scripts/verify_rcms.py hillclimb
uv run python scripts/verify_rcms.py hillclimb --compare-measures <first-evidence-directory>/measures.json
```

The comparison requires equal gesture counts, completion flags, parsed numerical
sections and result text, excluding wall time. It compares repetitions of one
UI version. For changed UI, inspect effort separately while keeping statistical
references fixed. These receipts are not independent estimator oracles.

Clicks include direct QAction activations; they do not measure menu-opening
pointer travel. Non-text key/chord gestures count as shortcuts, entered text as
characters, and observed dialogs separately from results windows. Clipboard
contents are preloaded inputs. Time is a monotonic interval from first gesture
through the final assertion, including analysis waits and capture overhead but
excluding task-independent setup and final screenshots. It is scripted wall
time, not human reading or pointing time.

Retain `measures.json`, `steps.jsonl`, runtime/command manifests, screenshots and
exported files. Record incomplete tasks as incomplete. Offscreen results do not
qualify native focus, OS pickers, accessibility, release startup or a comparison
with RevMan.
