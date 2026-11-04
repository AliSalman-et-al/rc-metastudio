---
name: project-round-trip
description: Check generated project persistence after any change to project_format.py, project_adapter.py, project_domain.py, project_schemas/, or saved analysis_dataset.py/analysis_unit.py fields.
---

The property is: for every valid v3 project P (passes save_project's schema + validate_project_semantics), `dataset_to_project(project_to_dataset(load_project(save_project(P)).project)) == P` and `load_project(...).state == state`.
Losing any saved field silently changes a user's research when they reopen it.

Exception: P must contain no row for which
`src/rc_metastudio/project_format.py:is_empty_entry_row` returns true:
`src/rc_metastudio/project_adapter.py:project_to_dataset` intentionally drops those grid entry rows.
This seeded test samples the property; it is not an exhaustive proof over all valid JSON.

## Run

From the repository root, use the existing shared environment; do not run bare uv sync (it breaks the local rpy2 runtime):

```bash
source /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/build/sheets-baseline/ENV.sh
export RCMS_R_LIBS=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/build/sheets-r-library
export R_LIBS=$RCMS_R_LIBS R_LIBS_USER=$RCMS_R_LIBS
export RCMS_QT6_BUILD_ROOT=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/build/qt6-verification
export PYTHONPATH="$PWD/src:$PWD"
export PATH=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/.venv/bin:$PATH
python -c 'from scripts.verify import run_typing; from pathlib import Path; import os; run_typing(Path(os.environ["RCMS_QT6_BUILD_ROOT"]))'
python -m pytest -q -s tests/python/fast/test_project_round_trip_property.py
RCMS_ROUND_TRIP_CASES=20000 RCMS_ROUND_TRIP_SEED=20261104 python -m pytest -q -s tests/python/fast/test_project_round_trip_property.py
python scripts/verify.py pre-push
```

Retain the exact commands, seed, platform, logs and counterexamples in an evidence directory.
The default is 20 candidates; the test reports rejected candidates and elapsed seconds.
Over 20% rejection means fix the generator, never relax the validators.

## Diagnose

The failure prints a seed, zero-based candidate index, first differing path and a greedy
counterexample with sheets, rows and optional fields deleted while preserving validation
and the failure. This shrink is deletion-minimal for its traversal, not a globally smallest
document. Reproduce using the same seed and at least index + 1 candidates.

A generated P that save_project accepts but the app could never create is a generator
error. Trace the disputed field through AnalysisUnit, StudyRow, Sheet and their editing
callers; compare a real saved sample and the v3 schema. For example, duplicate comparison
records cannot be represented by the runtime's keyed effect dictionary. Do not dismiss
an ordinary missing raw arm, empty covariate, Unicode string or multi-group sheet merely
because a sample lacks it. If reachable accepted input loses data, report a product finding
with the field and counterexample and stop; do not fix product code or weaken the property
without authorization.

## Coverage and maintenance

Generator and shrinker: tests/python/fast/test_project_round_trip_property.py.
Structured construction covers all five families/data types, permitted subtypes, raw-data
arities and missing cells/arms, multi-group arms, multiple sheets/rows, nullable and edge
years, sample sizes, inclusion flags, Unicode/whitespace/quoted/long text, sheet covariate
definitions and empty/missing/populated row values, settings, entered effects and ratio inputs.
It also perturbs projects loaded from sample_projects/*.rcms. Arbitrary settings and effect
objects are sampled, not exhaustively enumerated.

Covered code:
- src/rc_metastudio/project_format.py: save_project, load_project, _canonical_json,
  migrate_to_latest (current v3 path), is_empty_entry_row.
- src/rc_metastudio/project_adapter.py: project_to_dataset, dataset_to_project.
- src/rc_metastudio/project_domain.py: validate_project_semantics and sheet validators.
- src/rc_metastudio/project_schemas/v3/project.schema.json and state.schema.json;
  manifest.schema.json through the real archive boundary.
- src/rc_metastudio/analysis_dataset.py: Dataset, Sheet, StudyRow, Arm saved fields.
- src/rc_metastudio/analysis_unit.py: AnalysisUnit raw arms and entered_effects/ratio_inputs.
- src/rc_metastudio/ratio_data.py: RatioInput saved fields.

Not covered: archive hardening/adversarial ZIPs, legacy v1/v2 migration guarantees,
UI model state beyond current_sheet_id, R analysis, crash durability, or all possible
field combinations. Keep the existing focused tests for these contracts.

Last confirmed in sync at commit 90aa3247e889b718664d954cd835a42fc0f719c7.
Move this SHA forward only after comparing every saved field against the v3 schema and
confirming the generator still covers it at the new commit. Use
/maintain-formal-verification-skill for re-syncing. Repeat the four mutation demonstrations
(year loss, row notes loss, Unicode corruption, fabricated missing raw arms) after changing
the oracle or shrinker.
