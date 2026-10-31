# Slice 5 — initial RM5 import (incomplete)

This is an implementation checkpoint, not acceptance of PLAN row 13/j.
No numerical oracle was changed. No statistical method was added.

| RevMan | Current RCMS mapping |
| --- | --- |
| COMPARISON / DICH_OUTCOME | One binary Sheet; OR/RR/RD retained |
| CONT_OUTCOME | One continuous Sheet; MD/SMD retained |
| GROUP_LABEL_1/2 | Ordered arms; group 1 remains intervention |
| DICH_DATA EVENTS_1/2, TOTAL_1/2 | Events/total per arm |
| CONT_DATA TOTAL_1/2, MEAN_1/2, SD_1/2 | N/mean/SD per arm (RCMS storage order) |
| STUDY_ID | Reference to STUDY NAME and YEAR |
| CI_TOTAL | Sheet output confidence level |
| SUBGROUP | Categorical covariate; not yet verified with public subgroup fixture |

Multiple comparisons prefix sheet names. Duplicate sheet names, unresolved studies,
invalid counts, non-finite numbers and invalid arm labels reject the candidate.
The File menu opens a review dialog before replacement. Cancel preserves the
existing data. A welcome-wizard button is wired but not yet exercised.

Unsupported outcomes are listed in the review: generic inverse variance,
O−E/variance, other and empty outcomes, diagnostic DATA_TEST and IPD. Binary
SWAP_EVENTS outcomes are skipped with a reason. Review text, references,
risk-of-bias assessments and graphs are not imported. Method settings are
currently left at RCMS defaults and explicitly disclosed, including shared
methods: method-setting mapping remains unfinished. Peto is implemented by RCMS
but its import settings have not been wired. Unsupported source attachment and
per-item inventory need further work.

## Fixture and independent R check

[Fleiss1993.rm5 source](https://raw.githubusercontent.com/guido-s/meta/d100dde2c4aa924cef1399973da72f57904e93dd/inst/extdata/Fleiss1993.rm5),
SHA-256 `af4215ebcb2c186738fb2fb30abb7366de17678d29efba617f0abe9bb96bfaa7`.
Copied unchanged from installed meta extdata. A second public fixture is missing.

The desktop scenario runs `tests/e2e/rm5_reference.R` with installed meta 8.5-0.
All 12 imported labels/years and all 58 raw numeric cells equal `meta::read.rm5`.
Save/reopen compares the complete project object with its pre-save value.

These are `meta::metacr` fixed/common reference results, **not yet compared with
RCMS pooled results**. OR is shown here on its log scale; I² is a fraction.

| Outcome | Estimate | Lower | Upper | I² |
| --- | ---: | ---: | ---: | ---: |
| Aspirin (log OR) | -0.108849304507015 | -0.173741192560105 | -0.0439574164539248 | 0.39674580455584 |
| Mental health (SMD) | -0.343445753457489 | -0.606815161445856 | -0.0800763454691217 | 0 |

## Evidence and commands

All paths below are relative to `artifacts/verification/rcms/`:

- Expected pre-implementation failure (missing menu action): `20261031T175506Z-4096107a-rm5-import`.
- Passing independent row comparison, review/cancel/confirm and save/reopen: `20261031T175814Z-c9c14a39-rm5-import`.
- Sheets: `20261031T175841Z-3493d66e-sheets`.
- Sheets persistence: `20261031T175905Z-27c20a19-sheets-persist`.
- Amino: `20261031T175925Z-e1a639cf-amino`.

Each directory retains manifests, input/runtime identity, transcript, steps,
screenshots and workflow files, including read-rm5.csv and metacr.csv for import.
Offscreen Qt evidence does not prove native file-picker behavior.
Screenshots: `screens/slice5-review.png`, `slice5-binary.png`, `slice5-continuous.png`.

```bash
source build/sheets-baseline/ENV.sh
uv run --no-sync python scripts/verify_rcms.py rm5-import
uv run --no-sync python scripts/verify_rcms.py sheets
uv run --no-sync python scripts/verify_rcms.py sheets-persist
uv run --no-sync python scripts/verify_rcms.py amino
uv run --no-sync python -m pytest tests/e2e -n 2 -q -k "rm5 or sheets or wizard"
```

Remaining acceptance work: GIV and DTA mapping and public fixtures; subgroup
fixture; exact shared-method settings and live pooled comparisons; exhaustive
unsupported-item reporting and preservation; welcome-wizard E2E; malformed-input
rollback and dirty/path/history cancellation proof. Do not ship or push as a
completed RM5 switching path.

The requested pytest selection completed: **6 passed in 145.84 s**. A later
boundary-validation/covariate-key correction was followed by another direct
`rm5-import` run (`20261031T180225Z-04f78b10-rm5-import`); the complete selection
predates that correction.
