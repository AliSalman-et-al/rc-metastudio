# Windows report verification failures

Artifact: GitHub run 41448144714, `full-r-stack-windows-evidence`, downloaded
with `gh run download 41448144714 --repo AliSalman-et-al/rc-metastudio -n full-r-stack-windows-evidence -D /tmp/ci-ev2`.

Grouping by the first failure in each scenario: 47 encoding, 35 PDF-table,
6 PDF-caption, 9 Model fit, 3 pooled-row failures (100 total).

The encoding failure is the observer's `copy.html` write using cp1252; its
other text files also used the locale encoding. Poppler emits UTF-8, but the
observer decoded it as cp1252, producing `â€”` for an em dash and corrupting
non-ASCII table captions. All evidence text boundaries now explicitly use
UTF-8. Driver transcript streams also explicitly match the UTF-8 reader.
A search of Python text opens/writes in `src/` found explicit encodings;
remaining matches were binary I/O, Qt buffers, or application open methods.

Re-extracting the actual Windows PDFs exposed decimal wrapping in narrow
supplementary cells: `-0.395506` becomes `-0.39550` then `6`. Extraction joins
only a decimal and its digit continuation at the same left edge on adjacent
lines with overlapping glyph boxes. Every digit, sign, punctuation mark and
ordered table token remains checked. Replay of all 41 retained reports passed
all 351 complete tables. Exact initial replay script and result:
`build/pr539-check-artifact-pdfs.py`, `build/pr539-artifact-pdfs.log` (the initial
run documents the eight wrapped-table differences; subsequent production-helper
replay printed `WINDOWS PDF REPLAY PASSED 351 tables in 41 reports`).

The Windows small-study `failure.txt` preserves `Rücker` in UTF-8; replacement
characters occur in the decoded transcript. That failure precedes report
capture, so this scenario retained no PDF/DOCX to inspect. No product string
replacement is justified by the artifact.

Model fit differences include display precision (`0.000000%` versus held
`0.0%`), not different underlying values. Pooled regression differences are
the premature rounding of coefficient p-values, fixed in the product.

Local reproduction commands use `source build/sheets-baseline/ENV.sh`, then
`LC_ALL=C LANG=C PYTHONCOERCECLOCALE=0 PYTHONUTF8=0 PYTHONIOENCODING=cp1252 uv run --no-sync python scripts/verify_rcms.py` with `manuscript-export` and
`audit-round3-precision`. Both passed; logs are `build/pr539-cp1252-*.log`.
Linux's C locale is an encoding stress test, not exact Windows qualification.

A subsequent full local matrix reached 135 passed and two PDF comparison
failures, both the same diagnostic coefficient table. Qt split a row label
(`Group = A` / `vs B`) across pages, and a six-digit variant split centered
`(logit)` header units across pages. Extraction now restores logical cell order
only using the clipped duplicate's exact text and horizontal coordinates, or a
unique matching column center for a parenthesized unit near the page boundary.
It neither removes nor invents tokens. Both formerly failing scenarios passed
fresh targeted drives. The extended replay passed all 3,282 ordered tables in
323 retained reports: `uv run --no-sync python build/pr539-replay-retained-reports.py`,
with observed output in `build/pr539-replay-retained-reports.log`.
