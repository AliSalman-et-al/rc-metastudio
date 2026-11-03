# Slice 9: Summary of findings

Analysis > Summary of findings recalculates each sheet through the ordinary
analysis setup and service, preserving saved model, parameters and sheet
confidence level. Cells use held structured result tables rather than manuscript
sentences: estimate and confidence interval, followed by the method; diagnostic
rows contain only sensitivity and specificity confidence intervals. Participants
are summed from included raw data (including all four diagnostic cells); k uses
the included studies, retaining double-zero rows as Run does. Empty sheets show
en dashes and a short reason. Analysis failures also log their traceback through
the application error handler.

The table gives Comments useful width, narrows Certainty, and uses compact rows
without horizontal scrolling at its default size. Both screenshots are refreshed
from the real offscreen Qt dialog using light and dark palettes.

The precision discrepancy was configuration, not numerical rounding corruption:
the existing ordinary-Run driver explicitly sets Decimal Places to 3, while a
fresh setup defaults to 2. Running does not persist that choice in sheet analysis
settings. The scenario now supplies saved three-decimal settings and compares
every non-diagnostic row with ordinary Run, including fixed-effect
Mantel–Haenszel. Saved settings were already restored by AnalysisSetupDialog.
The summary consumes the exact formatted result fields, preserving their digits.
Both amino rows also compare against direct metafor fits at display precision.
No statistical methods or frozen oracles changed.

The real-menu scenario retains inputs, commands and evidence through verify-rcms.
It proves participant totals, concise cells, empty data, diagnostic rendering,
ordinary Run agreement, direct metafor agreement, clipboard HTML and tab-separated
text, both export buttons through non-native save dialogs, DOCX cells, extracted
PDF text, judgement undo, saved judgement reopen, and recalculation after a study
edit. Screenshots demonstrate offscreen Qt, not native window-manager behavior.

Verification commands source `build/sheets-baseline/ENV.sh` and use
`uv run --no-sync`; no environment synchronization or oracle regeneration.
The initial concise-cell assertion failed on the old p-value prose, with evidence
in `artifacts/verification/rcms/20261101T055736Z-aa6df40d-summary-of-findings`.
The final summary drive passed at
`artifacts/verification/rcms/20261101T060049Z-06bdd88c-summary-of-findings`.

Final ordered verification: summary-of-findings, sheets-persist,
manuscript-export, and amino all passed. The following uninterrupted command
passed **7 tests in 247.26 seconds**:

```
uv run --no-sync python -m pytest tests/e2e -n 2 -q -k "summary or manuscript or sheets"
```

The targeted runs retain manifests under `artifacts/verification/rcms/`:
`20261101T060137Z-2fce642a-sheets-persist`,
`20261101T060147Z-df209d9e-manuscript-export`, and
`20261101T060300Z-37ef321d-amino`.
