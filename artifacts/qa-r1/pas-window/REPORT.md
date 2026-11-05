# PAS display and main-window minimum

Base merge-base with origin/master: e7d7389c (contains 07b28316). Linux xcb real-display captures; strict Ty target win32. Worktree Python source and locally installed current RCMetaR (`build/rcmetar-lib`, install.log); shared pinned R runtime/forms from qa-env/ENV.sh.

Changes: all PAS display conversions now call metafor::transf.iarcsin. PFT already calls metafor::transf.ipft / transf.ipft.hm; raw proportions (PR, metafor PRAW) use identity. PLO now calls transf.ilogit to avoid overflow. No fit/effect/variance construction changed. Main adaptive policy reserves max(640,40 font heights) by max(400,24 font heights), bounded to screen size.

Tiny nonzero PAS lower 6.71052e-06 is deliberately retained: #554 F7 requires six significant digits when fixed decimals would round a nonzero number to zero. Ratio-only <0.01 handling does not apply to PAS.

## Repeatable commands and results

Source `/home/ali/.t3/qa-env/ENV.sh`, export `PYTHONPATH=$PWD/src:$PWD`, prepend `$PWD/build/rcmetar-lib` to RCMS_R_LIBS and R_LIBS after `R CMD INSTALL -l $PWD/build/rcmetar-lib r/RCMetaR`.

- `python -c 'from scripts.verify import run_typing; from pathlib import Path; import os; run_typing(Path(os.environ["RCMS_QT6_BUILD_ROOT"]))'`: passed (typing.log includes complete command and win32 target).
- `python scripts/verify_rcms.py amino`: before failed main minimum assertion; after passed direct metafor PAS row comparisons for 0/30, 1/74 and 0/19 plus original frozen OR analysis. Evidence path is retained in after-e2e.log.
- `$RCMS_R_HOME/bin/Rscript artifacts/qa-r1/pas-window/authority.R`: passed (authority.log); requested PAS bounds compared directly with metafor, PFT/PLO/PR extreme inputs too. Three-study PAS REML fit before/after: identical b, SE, z, p, CI, tau², Q, I², H². Full values printed twice. This is a three-study PAS analysis, not the full amino fit.
- `python scripts/verify.py pre-push`: passed. Full R/authority/desktop matrix and other-platform native qualification remain CI-only.

## Native actions

`RCMS_QA_APP_SRC=$PWD [RCMS_QA_R_LIB=$PWD/build/rcmetar-lib] /home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session pas-window start [--dark --large-font]`; Ctrl+O amino.rcms; Analysis > Effect-size tools > One-arm metrics > PAS. Screenshots before-pas-light.png and after-pas-light.png show lower bounds corrected from positive to zero. after-pas-dark-large.png shows the same corrected rows at dark/large font. Double-click title to restore; drag lower-right inward; after-minimum-light.png retains menu, toolbar, grid and tabs. after-minimum-dark-large.png is the restored large-font window, not a verified minimum-size drag (that drag missed the border). Session stopped.

Limitations: full before/after light/dark × default/large capture matrix not completed; dark/large capture is after only. No numerical golden references regenerated. Please review any strict presentation golden mismatch rather than regenerate numerical references. Expected presentation changes are PAS back-transformed out-of-domain bounds and main-window minimum geometry; no known frozen numerical case should change.
