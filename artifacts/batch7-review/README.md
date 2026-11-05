# Review corrections for PR #575

This evidence supersedes Batch 7's original formatting policy. Ordinary values
retain fixed decimals. Only adaptive values below the configured decimal
threshold gain extra digits, with redundant trailing zeros removed from that
adaptive result. Thus 0.770 / 0.783 and 1.200 / 1.285 remain aligned, while an
adaptive 0.0040 becomes 0.004 and 0.0088 remains 0.0088.

## Results and retained proof

- `formatting-proof.json` checks the reviewed normal/adaptive examples against
  both Python and the installed R package. Both agree exactly, including
  0.770, 1.200, 0.240 and 0.580 at three digits.
- `golden-vs-master.diff` compares the final golden report captures with the
  original pre-PR master a1ae1b49. Only label/casing changes remain: **every
  numeric token spelling matches master**, including fixed trailing zeros.
  `golden-numeric-spelling-proof.json` lists every compared section. Both
  leave-one-out report captures are retained as readable text.
- All **416** numerical golden fields and the existing tolerances pass.
  Public heading keys in the frozen numeric metadata were renamed to sentence
  case; their numerical values were not regenerated. PNG oracle bytes and all
  frozen parameters remain unchanged. `numeric-oracle-proof.json` records this.
- `golden-plot-labels.diff` shows the corresponding artifact/display labels:
  Forest plot, Cumulative forest plot, Leave-one-out forest plot, consistent
  singular Subgroup forest plot, and Diagnostic odds ratio forest plot.
  Production coefficient forests use Forest plot of coefficients. Generated
  metric labels share the sentence-case metric dictionary, preserving acronyms
  and proper nouns. Investigator-supplied text is left intact.
- `authorities-final.json` / `.log`: **103** independent authority cases pass.
- `r-contracts-final.log`: forest renderer and summary-display R contracts pass.
- E2E receipts retain commands, runtime, assertions and screenshot evidence for
  amino, continuous, plot-edit, results-window, cumulative, leave-one-out,
  subgroup, regression, combined and cumulative diagnostics, manuscript export,
  and both ratio families. Native ratios use independent 1600×1000 X displays.
- `pre-push-final.log` retains strict **win32** typing, fresh-master code health,
  fast/golden, GUI and packaging qualification. Earlier failed attempts are
  retained; they exposed stale exact-casing assertions, which were updated
  without changing numeric assertions or tolerances.

## Commands

Source `/home/ali/.t3/qa-env/ENV.sh`; set `PYTHONPATH=$PWD/src:$PWD` and
`UV_PROJECT_ENVIRONMENT=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/.venv`.
Install the current source using `$RCMS_R_HOME/bin/R CMD INSTALL -l
$PWD/build/rcmetar-review-lib r/RCMetaR`; prepend that library to RCMS_R_LIBS,
R_LIBS and R_LIBS_USER. The install log and package source hashes are retained.
Use the existing QA generated forms; no forms changed.

```
uv run --no-sync python artifacts/batch7-review/prove-formatting.py
R_HOME=$RCMS_R_HOME uv run --no-sync python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-batch7-review2-qualified
$RCMS_R_HOME/bin/Rscript .agents/skills/verify-rcms/scripts/analysis_authorities.R artifacts/batch7-review/authorities-final.json --installed
$RCMS_R_HOME/bin/Rscript -e 'testthat::test_local("r/RCMetaR", filter="forest-metafor-renderer|summary-display", reporter="summary")'
uv run --no-sync python scripts/verify_rcms.py SCENARIO
xvfb-run -a -s '-screen 0 1600x1000x24' uv run --no-sync python scripts/verify_rcms.py ratios-hr --native
xvfb-run -a -s '-screen 0 1600x1000x24' uv run --no-sync python scripts/verify_rcms.py ratios-irr --native
git fetch origin master
uv run --no-sync python scripts/verify.py pre-push
```

Scenario names: `amino`, `continuous`, `plot-edit`, `results-window`,
`analysis-amino-binary-cumulative`, `analysis-amino-binary-leave-one-out`,
`analysis-continuous-subgroup`, `analysis-amino-binary-meta-regression`,
`analysis-diagnostic-combined`, `analysis-diagnostic-cumulative`,
`manuscript-export`. Their log files identify the complete original evidence
folders; receipts preserve manifests, transcripts, steps and final screenshots.

Not requalified: Windows/macOS native or release packages; the excluded
1024×700/large-font subgroup first view. The body-text floor and #574 fit
settling remain untouched.

Final pre-push result: **413 fast/golden passed, 6 skipped; 364 GUI passed,
1 skipped; 73 packaging passed, 8 skipped**, plus strict win32 typing and the
fresh-master code-health gate. `golden-report.json` passes all 416 numeric metrics;
all ten sample/plot/report/analysis scenarios and manuscript export passed.

Both complete native ratio workflows end in `workflow-passed`, including long
labels, plot editors, decoded exports and their independent numerical checks.
All **13** affected E2E scenarios passed. See also
`leave-one-out-correction.diff` for the direct correction from the reviewed PR
capture: 0.77 → 0.770, 1.2 → 1.200 and 0.24 → 0.240, without value changes.
