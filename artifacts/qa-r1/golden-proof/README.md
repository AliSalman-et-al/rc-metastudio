# Final reduced-scope golden proof for PR #556

The later scope decision supersedes the earlier F14 notation approval. Master notation and selected decimal places are restored. The only updated golden fields are:

- amino-binary-leave-one-out / texts.Leave-one-out Summary: repeated `Study omitted: ` removed from 19 study rows; the column header remains `Study omitted`.
- continuous-leave-one-out / texts.Leave-one-out Summary: the same prefix removed from 6 study rows; the header remains.

`check.py` is a throwaway approval check stored as evidence, not a test and not part of any test suite. It ran BEFORE the reference update. `output.json` contains each complete old/new string, all 164 paired numeric tokens, the selected new decimal quantum and old-value rounding result (ROUND_HALF_EVEN). All tokens pass; in fact all numeric values are exactly equal. No number appeared or disappeared and no removal exception was needed. There are no separate plot-text fields in this frozen archive, and no PNG was updated.

Current-only Inference Method fields and two pre-existing meta-regression text differences are deliberately NOT reference updates: their existing compatibility exceptions remain. The check rejects other unexpected changed fields. `apply.py` permits only the two proved text projections, retaining all other JSON fields and binary member payloads.

`structural-proof.json` proves that all non-text archive fields and all 11 PNGs are identical, every numeric case and tolerance is identical, and all plot descriptor rows are identical. The only numeric-contract and plot-descriptor file change is `/oracle_sha256`, required to bind their unchanged content to the text-only ZIP update. `manifest.json` changes only the archive/contract binding hashes and ZIP size. `reference-diff-stat.txt` is `git diff origin/master --stat -- tests/analysis_regression/baseline`.

Reproduce using the original references at master d0ad121d (the references are also identical to d63e7c1eb5959d44e209c16bf81b81aec65b72f5). Reconstruct `old/` from `tests/analysis_regression/baseline/` at that revision; it is retained locally but not duplicated as a large committed ZIP.

```bash
python3 artifacts/qa-r1/golden-proof/check.py artifacts/qa-r1/golden-proof/current --baseline artifacts/qa-r1/golden-proof/old
```

`current/manifest.json` is retained to reproduce the text/number proof without running R. Capture command (source qa-env ENV.sh; set PYTHONPATH=$PWD/src:$PWD; prepend $PWD/build/rcmetar-lib to RCMS_R_LIBS/R_LIBS/R_LIBS_USER; set R_HOME=$RCMS_R_HOME and add its bin to PATH):

```bash
python scripts/verify_golden_compatibility.py --root "$PWD" --output-root build/qt6-verification/golden-compatibility-qa-r1-reduced
python artifacts/qa-r1/golden-proof/recompare.py
```

The initial comparison correctly reports the two old prefix fields as changed. After the proved projection, `recompare.log` passes all 475 rows. All 416 numerical fields retain their values and original tolerance policy. No authority files or tolerance definitions were changed.

The optional near-zero Q presentation rule applies only to Python report projection of Q columns and explicitly identified subgroup-Q tests (`0 < abs(Q) < 1e-10`), so it requires no golden R-text update. Other numbers, notation and selected decimal places retain master behavior.

`superseded-unification/` and earlier local capture logs are historical attempts, NOT evidence for the final scope. They are not included in the PR's final proof artifacts.
