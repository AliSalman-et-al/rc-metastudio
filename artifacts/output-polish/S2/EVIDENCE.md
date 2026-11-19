# Risk-difference display precision

With BCG and DerSimonian–Laird, six study annotations had identical printed CI bounds at the requested two decimals. All 13 studies and the pooled row now have distinct bounds in Default and BMJ, with three decimals throughout. The pooled estimate is −0.007 (−0.010 to −0.004), and the prediction interval is −0.016 to 0.002. A four-digit request still uses four decimals. The RR, OR and MD effect annotations and their matching two-decimal report tables are identical before and after.

| Check | Evidence |
| --- | --- |
| BCG RD, Default | [Before](before/04-0-RD-default-2.png), [after](after/04-0-RD-default-2.png), [SVG](after/04-0-RD-default-2.svg) |
| BCG RD, BMJ | [Before](before/07-0-RD-bmj-2.png), [after](after/07-0-RD-bmj-2.png), [SVG](after/07-0-RD-bmj-2.svg), [four digits](after/10-0-RD-bmj-4.png) |
| Matching intervals and Model configuration disclosure | [DOCX](after/RD-bmj-2.docx), [PDF](after/RD-bmj-2.pdf), [HTML](after/RD-bmj-2.html), [Word Results](after/word-results.jpg), [Word configuration](after/word-configuration.jpg) |
| Exact before/after values for RR, OR, MD, RD and I² | [Before values](before/precision.json), [after values](after/precision.json), [comparison transcript](qualification/compare-receipts.log) |
| Automatic four-decimal cap | [R transcript](qualification/cap.log) |

The native app ran on Windows x64 with Qt/qwindows, R 4.6.2 and metafor 5.2-1. The before run used the R library from `e0d7919f` with the S1 Python checkout. S1 changed R presentation and test expectations. The accepted R3 and R6 captures independently show the same two-decimal RD and I² behavior. The after run used RCMetaR reinstalled from the edited worktree. The native [before manifest](before/manifest.json) and [after manifest](after/manifest.json) record the actual commands, source status and file hashes. Word continued the configuration note on the following page in the captured BMJ export.

Replay from the repository root. The app drive includes the strict Windows typing gate before it opens Qt. It uses the committed BCG sample, the maintained two-arm MD fixture and the phase 1 Aspirin project recorded in the driver.

```powershell
. ./artifacts/output-polish/runtime.ps1
$env:PATH = 'C:/Users/Ali-Salman/Documents/Code/rc-metastudio/.tmp/poppler-tsa/poppler-26.09.0/Library/bin;' + $env:PATH
& (Join-Path $env:RCMS_R_HOME 'bin/R.exe') CMD INSTALL "--library=$env:RCMS_R_LIBS" r/RCMetaR
uv run python artifacts/output-polish/S2/drive.py
uv run python artifacts/output-polish/S2/compare_receipts.py
```

For the before run, select a warm library with RCMetaR installed from `e0d7919f`, then use the previous native command with the before flag.

```powershell
$env:RCMS_PRECISION_BEFORE = '1'
uv run python artifacts/output-polish/S2/drive.py
Remove-Item Env:RCMS_PRECISION_BEFORE
```

To reproduce the Word captures, open a copy of `after/RD-bmj-2.docx`. Inspect the pooled row and prediction sentence under Results. Press Ctrl+End and scroll up slightly to see the configuration heading and note across the page break.

The formatter stress check covers positive-width sub-resolution intervals, equal and missing bounds, and a request already above four decimals.

```powershell
& (Join-Path $env:RCMS_R_HOME 'bin/Rscript.exe') --vanilla -e 'library(RCMetaR); precision <- RCMetaR:::rcmetar.effect.digits; note <- RCMetaR:::rcmetar.effect.precision.note; lo <- c(0.000001, NA, 0); hi <- c(0.000002, NA, 0); stopifnot(precision(list(digits=2), lo, hi) == 4L, precision(list(digits=5), lo, hi) == 5L, precision(list(digits=2), lo[-1], hi[-1]) == 2L, grepl("still round to the same value", note(list(digits=2), 4, lo, hi))); cat("Four-decimal cap, higher explicit digits, missing and exact bounds passed.\n")'
```
