# Peto null / omitted-study presentation proof

Environment: source `/home/ali/.t3/qa-env/ENV.sh`, then `PYTHONPATH=$PWD/src:$PWD`; installed current R source with `$RCMS_R_HOME/bin/R CMD INSTALL -l $PWD/build/rcmetar-lib r/RCMetaR`. For E2E prepend that library to RCMS_R_LIBS and R_LIBS. Linux xcb native screenshots; automated Qt/R drives use offscreen.

Commands and results:
- Strict typing: exact win32 command and generated-module paths in typing-before.log and typing-after.log; both pass.
- `python scripts/verify.py pre-push`: pre-push.log, passed.
- `$RCMS_R_HOME/bin/Rscript -e 'library(RCMetaR); testthat::test_dir("r/RCMetaR/tests/testthat", package="RCMetaR", stop_on_failure=TRUE)'`: r-tests.log; 1830 pass, zero failures/warnings, one existing opt-in visual skip.
- `python scripts/verify_rcms.py analysis-binary.fixed.mh` and `analysis-binary.fixed.peto`: e2e-*-final.log point to durable manifests, inputs, screenshots, exact commands and assertion receipts. Both passed. Initial failed attempts are retained in the verification tree: an overbroad assertion matched a valid p-value, fixed to inspect the heading.

## Mechanical numbers proof

Run `Rscript numbers.R <library> <output.rds>` from repository root using the paths in this directory's script; baseline library is `/home/ali/.t3/qa-env/rcmetar-lib`, changed library is `build/rcmetar-lib`. Then `Rscript artifacts/qa-r1/peto-null/compare.R`. The fixture is the existing six-study R renderer fixture with the first study set to double zero. before.rds/after.rds retain inputs' fits and presentation fields; comparison.log records exact equality of **every fit field**, excluding only elapsed runtime (`time`) and captured execution environment (`data`, containing presentation and timing). No tolerance or rounding comparison is used.

Presentation changes:
- Peto forest footer and Summary overall-test table title: `Test for overall effect (H₀: odds Ratio = 0)` -> `Test for overall effect`, exactly like IV OR and MH. Statistic and p-value unchanged.
- MH standard forest held `effect_display.{y.disp,lb.disp,ub.disp}` for fit-omitted studies: corrected finite estimate/CI -> NA. This now agrees with its already-rendered Not estimable forest row. Plot range can shrink when it no longer includes the omitted corrected interval. Report shows Not estimable / em-dash bounds with the original zero weight.
- Peto study estimate/CI remains finite with zero weight because RCMS explicitly calls rma.peto with drop00=FALSE; no fitting policy changes.

No frozen golden reference or numerical contract was edited. The eleven frozen golden cases do not include MH/Peto fixed standard analysis. No affected frozen golden presentation field is expected; the added MH/Peto E2E assertions and paired RDS proof cover those cases directly. If CI detects another presentation reference affected by omitted-study alignment, review that exact field rather than regenerating numerical references.

Audit: `rg 'res\$measure' r/RCMetaR/R` finds only rcmetar.overall.null.label in forest_summary.R; no other fitted-measure presentation read shares the PETO trap.

Native session `peto-null` used ui.py with the QA review project (`/home/ali/.t3/qa-round2/j1/review project.rcms`): Open, Analysis > Meta-analysis, select Peto, Run; Change settings > MH, Run; Text report. Baseline library: QA library; changed: RCMS_QA_R_LIB=$PWD/build/rcmetar-lib. Light/default baseline and dark/large-font changed captures prove the triggers. The complete crossed before/after theme/font matrix was not completed. Session stopped.
