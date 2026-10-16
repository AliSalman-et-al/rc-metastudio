# Round 4 / Opus review 1 — verification

Final current-source qualification passed. The full fresh profile covers 108 desktop scenarios, doctor, the R package gates, strict golden compatibility, live bridge and independent authority comparisons. All 415 original numerical fields are exactly unchanged; maximum difference 0. See [FULL-PROFILE](FULL-PROFILE.json), [NUMERICAL-EQUIVALENCE](NUMERICAL-EQUIVALENCE.json), [installed source](INSTALLED-SOURCE.json), and [native receipts](REVIEW1-NATIVE.json).

The retained GUI boundary selection passed 186 checks with one Linux platform skip; the changed production Python files passed the configured type check. The full fresh profile is the final aggregate gate. Native drives use pinned R 4.6.1 and the test-owned library; every R source revision was reinstalled before driving. No numerical oracle or tolerance was refreshed. Only reviewed presentation text was refreshed with the sanctioned tool; see REVIEW1-GOLDEN-TEXT.md.

Failures and interruptions below are retained development observations, not passing evidence. The first continuation full run was deliberately stopped after visual inspection found the wrong transformed-null variable. Its exact package-check failure remains in the recorded log; REVIEW1-FULL-INTERRUPTION.json names the owned process and signal. Two outer wrappers exited 143 with no sealed desktop manifest; REVIEW1-INTERRUPTIONS.json retains the cleanup/provenance. The earlier push exit 143 had empty stdout and stderr (STOP.json); the user recovered it before this continuation. Every continuation source/evidence commit was fast-forward pushed successfully.

The unconfigured whole-repository type invocation reported `Found 178 diagnostics`; a scoped configured check identified six new errors, which were fixed before the changed-file check passed. The unavailable `ruff` executable and the initial unavailable bare `python` command are tool availability failures, not passing checks. No claim is made for whole-repository typing or linting.

The documentation whitespace check exited 2 only for trailing spaces in the verbatim failed-child transcript. Those bytes are deliberately retained; the same check excluding that transcript passed.

## Exact recorded commands and exits

| Label | Exit | Exact command |
| --- | ---: | --- |
| baseline-precision | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-precision --native</code> |
| baseline-presentation | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation --native</code> |
| before-design-amino | 0 | <code>uv run python scripts/verify_rcms.py amino --native</code> |
| bmj-observed-collision-checked | 1 | <code>uv run python -c 'import sys,json; from pathlib import Path; from types import SimpleNamespace; sys.path.insert(0,"tests/e2e"); from audit_round3 import check_annotation_spacing; r=json.loads(Path("docs/ux-audit/2026-10-15-round4/OBSERVATIONS.json").read_text()); d=next(x for x in r if x["family"]=="twoarm-proportion"); f=Path(d["evidence"]); s=[json.loads(x) for x in (f/"steps.jsonl").read_text().splitlines()]; o=next(x for x in s if x["action"]=="round4-annotations" and x["style"]=="bmj" and x["digits"]==6); check_annotation_spacing(SimpleNamespace(report_text=SimpleNamespace(toPlainText=lambda:"Overall-effect null:"),results=SimpleNamespace(display_images={k:str(f/v) for k,v in o["artifacts"].items()})))'</code> |
| bmj-observed-collision | 1 | <code>uv run python -c 'import sys,json; from pathlib import Path; from types import SimpleNamespace; sys.path.insert(0,"tests/e2e"); from audit_round3 import check_annotation_spacing; r=json.loads(Path("docs/ux-audit/2026-10-15-round4/OBSERVATIONS.json").read_text()); d=next(x for x in r if x["family"]=="twoarm-proportion"); f=Path(d["evidence"]); s=[json.loads(x) for x in (f/"steps.jsonl").read_text().splitlines()]; o=next(x for x in s if x["action"]=="round4-annotations" and x["style"]=="bmj" and x["digits"]==6); check_annotation_spacing(SimpleNamespace(report_text=SimpleNamespace(toPlainText=lambda:"Overall-effect null:"),results=SimpleNamespace(display_images={k:str(f/v) for k,v in o["artifacts"].items()})))'</code> |
| calculators-offscreen-1 | 1 | <code>uv run python -m pytest tests/e2e -n auto -k calculator --fresh -q</code> |
| calculators-offscreen-2 | 2 | <code>uv run python -m pytest tests/e2e -n auto -k calculator --fresh -q</code> |
| full-final | 1 | <code>uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh</code> |
| full-qualification | 130 | <code>uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh</code> |
| golden-before-refresh | 1 | <code>uv run python scripts/verify_golden_compatibility.py --output build/qt6-verification/golden-compatibility-round4-review</code> |
| golden-presentation-refresh | 0 | <code>uv run python scripts/regenerate_golden_presentation.py build/qt6-verification/golden-compatibility-round4-review</code> |
| install-bmj-clearance | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| install-bubble-padding | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| install-design | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| install-final-renderers | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| install-null | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| install-publication-final | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| install-rendering | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| install-sequential-fix | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| native-amino-ready | 0 | <code>uv run python scripts/verify_rcms.py amino --native</code> |
| native-audit-round3-hr-final | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-hr --native</code> |
| native-audit-round3-irr-final | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-irr --native</code> |
| native-audit-round3-presentation-reg-coef-ready | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-reg-coef --native</code> |
| native-calculator-binary-final | 0 | <code>uv run python scripts/verify_rcms.py calculator-binary --native</code> |
| native-calculator-continuous-final | 0 | <code>uv run python scripts/verify_rcms.py calculator-continuous --native</code> |
| native-calculator-mode-entered-binary-ready | 0 | <code>uv run python scripts/verify_rcms.py calculator-mode-entered-binary --native</code> |
| native-calculator-mode-entered-binary-verified | 0 | <code>uv run python scripts/verify_rcms.py calculator-mode-entered-binary --native</code> |
| native-calculator-mode-entered-continuous-ready | 0 | <code>uv run python scripts/verify_rcms.py calculator-mode-entered-continuous --native</code> |
| native-calculator-mode-entered-continuous-verified | 0 | <code>uv run python scripts/verify_rcms.py calculator-mode-entered-continuous --native</code> |
| native-calculator-mode-pre-post-complete | 1 | <code>uv run python scripts/verify_rcms.py calculator-mode-pre-post --native</code> |
| native-calculator-mode-pre-post-final | 1 | <code>uv run python scripts/verify_rcms.py calculator-mode-pre-post --native</code> |
| native-calculator-mode-pre-post-ready | 0 | <code>uv run python scripts/verify_rcms.py calculator-mode-pre-post --native</code> |
| native-calculator-mode-pre-post-verified | 0 | <code>uv run python scripts/verify_rcms.py calculator-mode-pre-post --native</code> |
| native-final-diagnostic | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-diagnostic --native</code> |
| native-final-generic-effect | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-generic-effect --native</code> |
| native-final-onearm-proportion | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-onearm-proportion --native</code> |
| native-final-reg-coef | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-reg-coef --native</code> |
| native-final-sequential | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-sequential --native</code> |
| native-final-twoarm-mean | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-mean --native</code> |
| native-final-twoarm-proportion | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-proportion --native</code> |
| native-final-twoarm-smd | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-smd --native</code> |
| native-plot-workflow-regression-ready | 0 | <code>uv run python scripts/verify_rcms.py plot-workflow-regression --native</code> |
| native-precision-1 | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-precision --native</code> |
| native-precision-final | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-precision --native</code> |
| native-presentation-1 | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation --native</code> |
| native-presentation-2 | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation --native</code> |
| native-presentation-3 | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation --native</code> |
| native-project-table-covariates-ready | 0 | <code>uv run python scripts/verify_rcms.py project-table-covariates --native</code> |
| native-project-table-covariates-verified | 1 | <code>uv run python scripts/verify_rcms.py project-table-covariates --native</code> |
| native-publication-diagnostic | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-diagnostic --native</code> |
| native-publication-generic-effect | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-generic-effect --native</code> |
| native-publication-onearm-proportion | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-onearm-proportion --native</code> |
| native-publication-twoarm-mean | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-mean --native</code> |
| native-publication-twoarm-proportion | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-proportion --native</code> |
| native-publication-twoarm-smd | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-smd --native</code> |
| native-review-workflows-verified | 0 | <code>uv run python scripts/verify_rcms.py review-workflows --native</code> |
| native-sequential-final | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-sequential --native</code> |
| native-small-study-diagnostic-ready | 0 | <code>uv run python scripts/verify_rcms.py small-study-diagnostic --native</code> |
| native-ux-improvements-verified | 0 | <code>uv run python scripts/verify_rcms.py ux-improvements --native</code> |
| numerical-before-refresh | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-round4-review</code> |
| r-presentation-current | 1 | <code>/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript -e 'testthat::test_local("r/RCMetaR", filter="forest&#124;bubble&#124;summary", reporter=testthat::SummaryReporter$new(max_reports=Inf), stop_on_failure=TRUE)'</code> |
| resume-bmj-binary | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-proportion --native</code> |
| resume-install | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| retained-ui-checks-final | 0 | <code>uv run python -m pytest tests/python/gui/test_funnel_plot_editor.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_automation_launch.py -q</code> |
| retained-ui-checks | 1 | <code>uv run python -m pytest tests/python/gui/test_funnel_plot_editor.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_automation_launch.py -q</code> |
| retained-ui-final | 0 | <code>uv run python -m pytest tests/python/gui/test_funnel_plot_editor.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_automation_launch.py -q</code> |
| review1-bounded-calculator-binary | 0 | <code>uv run python scripts/verify_rcms.py calculator-binary --native</code> |
| review1-bounded-calculator-continuous | 0 | <code>uv run python scripts/verify_rcms.py calculator-continuous --native</code> |
| review1-bounded-calculator-diagnostic | 0 | <code>uv run python scripts/verify_rcms.py calculator-diagnostic --native</code> |
| review1-bounded-calculator-mode-entered-continuous | 0 | <code>uv run python scripts/verify_rcms.py calculator-mode-entered-continuous --native</code> |
| review1-bounded-calculator-mode-pre-post | 0 | <code>uv run python scripts/verify_rcms.py calculator-mode-pre-post --native</code> |
| review1-bounded-generic-effect | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-generic-effect --native</code> |
| review1-bounded-project-shell | 1 | <code>uv run python scripts/verify_rcms.py project-shell --native</code> |
| review1-bounded-review-workflows | 0 | <code>uv run python scripts/verify_rcms.py review-workflows --native</code> |
| review1-bounded-subgroup | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-twoarm-proportion --native</code> |
| review1-bounded-transforms | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-transforms --native</code> |
| review1-bounded-ux-improvements | 0 | <code>uv run python scripts/verify_rcms.py ux-improvements --native</code> |
| review1-captions-before | 1 | <code>uv run python scripts/verify_rcms.py analysis-diagnostic-regression-multiple</code> |
| review1-clinical-audit-round3-presentation-transforms | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-transforms --native</code> |
| review1-clinical-complete-analysis-diagnostic-combined | 0 | <code>uv run python scripts/verify_rcms.py analysis-diagnostic-combined --native</code> |
| review1-clinical-complete-analysis-diagnostic-joint | 0 | <code>uv run python scripts/verify_rcms.py analysis-diagnostic-joint --native</code> |
| review1-clinical-complete-analysis-diagnostic-regression-multiple | 0 | <code>uv run python scripts/verify_rcms.py analysis-diagnostic-regression-multiple --native</code> |
| review1-clinical-complete-review1-design | 0 | <code>uv run python scripts/verify_rcms.py review1-design --native</code> |
| review1-clinical-order-before | 1 | <code>uv run python scripts/verify_rcms.py analysis-diagnostic-joint</code> |
| review1-clinical-qualified-analysis-diagnostic-combined | 1 | <code>uv run python scripts/verify_rcms.py analysis-diagnostic-combined --native</code> |
| review1-clinical-qualified-analysis-diagnostic-joint | 0 | <code>uv run python scripts/verify_rcms.py analysis-diagnostic-joint --native</code> |
| review1-clinical-sidebar-before | 1 | <code>uv run python scripts/verify_rcms.py analysis-diagnostic-joint</code> |
| review1-coefficient-editor-after | 0 | <code>uv run python scripts/verify_rcms.py plot-workflow-coefficient --native</code> |
| review1-coefficient-editor-before | 1 | <code>uv run python scripts/verify_rcms.py plot-workflow-coefficient --native</code> |
| review1-coefficient-qualified | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-reg-coef --native</code> |
| review1-complete-project-shell | 1 | <code>uv run python scripts/verify_rcms.py project-shell --native</code> |
| review1-design-before | 1 | <code>uv run python scripts/verify_rcms.py review1-design --native</code> |
| review1-design-reading | 0 | <code>uv run python scripts/verify_rcms.py review1-design --native</code> |
| review1-diagnostic-axis | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-diagnostic --native</code> |
| review1-diagnostic-before | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-diagnostic --native</code> |
| review1-doc-final | 0 | <code>git diff --cached --check -- . ':(exclude)docs/ux-audit/2026-10-15-round4/TESTS.md' ':(exclude)docs/ux-audit/2026-10-15-round4/*-FAILURES.txt'</code> |
| review1-evidence-complete | 0 | <code>uv run python docs/ux-audit/2026-10-15-round4/verify_evidence.py</code> |
| review1-evidence-final | 0 | <code>uv run python docs/ux-audit/2026-10-15-round4/verify_evidence.py</code> |
| review1-evidence-finished | 0 | <code>uv run python docs/ux-audit/2026-10-15-round4/verify_evidence.py</code> |
| review1-evidence-integrity | 0 | <code>uv run python docs/ux-audit/2026-10-15-round4/verify_evidence.py</code> |
| review1-final-generic-effect | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-generic-effect --native</code> |
| review1-final-twoarm-mean | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-mean --native</code> |
| review1-final-twoarm-smd | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-smd --native</code> |
| review1-full-complete | 1 | <code>uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh</code> |
| review1-full-current | 1 | <code>uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh</code> |
| review1-full-final | 1 | <code>uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh</code> |
| review1-full-finished | 0 | <code>uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh</code> |
| review1-full-fresh | 1 | <code>uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh</code> |
| review1-full-gates | 1 | <code>uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh</code> |
| review1-full-qualified | 1 | <code>uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full --fresh</code> |
| review1-golden-refresh | 0 | <code>uv run python scripts/regenerate_golden_presentation.py build/qt6-verification/golden-compatibility-review1</code> |
| review1-golden-review | 1 | <code>uv run python scripts/verify_golden_compatibility.py --output build/qt6-verification/golden-compatibility-review1</code> |
| review1-golden-strict | 0 | <code>uv run python scripts/verify_golden_compatibility.py --output build/qt6-verification/golden-compatibility-review1-strict</code> |
| review1-install-axis | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| review1-install-bounded-reference | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| review1-install-clinical-clearance | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| review1-install-clinical-labels | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| review1-install-committed | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| review1-install-figures | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| review1-install-final-source | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| review1-install-frozen-source | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| review1-install-pft | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| review1-install-portable-source | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| review1-install-qualified-head | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| review1-install-sparse-clearance | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/install_source.py</code> |
| review1-native-design-final | 0 | <code>uv run python scripts/verify_rcms.py review1-design --native</code> |
| review1-native-diagnostic-complete | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-diagnostic --native</code> |
| review1-native-figures-binary | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-proportion --native</code> |
| review1-native-figures-diagnostic | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-diagnostic --native</code> |
| review1-native-figures-transforms | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-transforms --native</code> |
| review1-native-subgroup-complete | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-twoarm-proportion --native</code> |
| review1-native-transforms-qualified | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-transforms --native</code> |
| review1-null-footer-before-contract | 1 | <code>uv run python -c 'import sys,json; from pathlib import Path; from types import SimpleNamespace; sys.path.insert(0,"tests/e2e"); from audit_round3 import check_annotation_spacing; r=json.loads(Path("docs/ux-audit/2026-10-15-round4/REVIEW1-NATIVE.json").read_text())["review1-verified-generic-effect"]; f=Path(r["evidence"]); s=next(x for x in r["observed"] if x["action"]=="round4-annotations" and x["style"]=="default" and x["digits"]==3); check_annotation_spacing(SimpleNamespace(report_text=SimpleNamespace(toPlainText=lambda:"report"),results=SimpleNamespace(display_images={k:str(f/v) for k,v in s["artifacts"].items()})))'</code> |
| review1-numerical-before-refresh | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-review1</code> |
| review1-numerical-finished | 0 | <code>uv run python docs/ux-audit/2026-10-14-round3/numerical_equivalence.py --capture build/qt6-verification/golden-compatibility-r-stack-v2</code> |
| review1-preflight-calculator-mode-onearm-mean | 0 | <code>uv run python scripts/verify_rcms.py calculator-mode-onearm-mean</code> |
| review1-preflight-calculator-mode-onearm-proportion | 0 | <code>uv run python scripts/verify_rcms.py calculator-mode-onearm-proportion</code> |
| review1-preflight-plot-workflow-coefficient | 0 | <code>uv run python scripts/verify_rcms.py plot-workflow-coefficient</code> |
| review1-publication-audit-round3-presentation-diagnostic | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-diagnostic --native</code> |
| review1-publication-audit-round3-presentation-reg-coef | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-reg-coef --native</code> |
| review1-publication-audit-round3-presentation-twoarm-proportion | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-proportion --native</code> |
| review1-publication-review1-design | 0 | <code>uv run python scripts/verify_rcms.py review1-design --native</code> |
| review1-publication-ux-improvements | 0 | <code>uv run python scripts/verify_rcms.py ux-improvements --native</code> |
| review1-qualified-audit-round3-precision | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-precision --native</code> |
| review1-qualified-audit-round3-presentation-onearm-proportion | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-onearm-proportion --native</code> |
| review1-qualified-audit-round3-presentation-transforms | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-transforms --native</code> |
| review1-qualified-plot-workflow-forest | 0 | <code>uv run python scripts/verify_rcms.py plot-workflow-forest --native</code> |
| review1-qualified-project-shell | 0 | <code>uv run python scripts/verify_rcms.py project-shell --native</code> |
| review1-qualified-project-structure | 0 | <code>uv run python scripts/verify_rcms.py project-structure --native</code> |
| review1-r-forest-retained | 0 | <code>/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript -e 'pkgload::load_all("r/RCMetaR", quiet=TRUE); testthat::test_file("r/RCMetaR/tests/testthat/test-forest-metafor-renderer.R", reporter="summary", stop_on_failure=TRUE)'</code> |
| review1-reading-finished-analysis-diagnostic-joint | 0 | <code>uv run python scripts/verify_rcms.py analysis-diagnostic-joint --native</code> |
| review1-reading-finished-analysis-diagnostic-regression-multiple | 0 | <code>uv run python scripts/verify_rcms.py analysis-diagnostic-regression-multiple --native</code> |
| review1-reading-finished-review1-design | 0 | <code>uv run python scripts/verify_rcms.py review1-design --native</code> |
| review1-reading-qualified | 0 | <code>uv run python scripts/verify_rcms.py review1-design --native</code> |
| review1-references-complete | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-references</code> |
| review1-references-qualified | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-references</code> |
| review1-sidebar-after | 0 | <code>uv run python scripts/verify_rcms.py review1-design</code> |
| review1-sidebar-before | 1 | <code>uv run python scripts/verify_rcms.py review1-design</code> |
| review1-singlearm-onearm-mean | 0 | <code>uv run python scripts/verify_rcms.py calculator-mode-onearm-mean --native</code> |
| review1-singlearm-onearm-proportion | 0 | <code>uv run python scripts/verify_rcms.py calculator-mode-onearm-proportion --native</code> |
| review1-static-check | 1 | <code>uv run ty check</code> |
| review1-transformed-axis | 1 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-transforms --native</code> |
| review1-transformed-null-before | 1 | <code>uv run python -c 'import json; from pathlib import Path; from xml.etree import ElementTree as ET; r=json.loads(Path("docs/ux-audit/2026-10-15-round4/REVIEW1-NATIVE.json").read_text())["review1-bounded-transforms"]; s=next(x for x in r["observed"] if x["action"]=="round4-annotations" and x["style"]=="default" and x["metric"]=="PLO"); p=Path(r["evidence"])/next(iter(s["artifacts"].values())); captions=["".join(n.itertext()) for n in ET.parse(p).iter("{http://www.w3.org/2000/svg}text")]; assert any("H₀: proportion = 0.5" in c for c in captions), captions'</code> |
| review1-types-clinical | 0 | <code>uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path build/qt6-verification/generated/rc_metastudio src/rc_metastudio/results_window.py</code> |
| review1-types-controls | 0 | <code>uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path build/qt6-verification/generated/rc_metastudio src/rc_metastudio/start_page.py src/rc_metastudio/main_window.py src/rc_metastudio/results_window.py src/rc_metastudio/qt_layout.py src/rc_metastudio/analysis_identity.py src/rc_metastudio/r_bridge.py src/rc_metastudio/settings.py src/rc_metastudio/binary_data_dialog.py src/rc_metastudio/continuous_data_dialog.py src/rc_metastudio/diagnostic_data_dialog.py</code> |
| review1-types-final | 0 | <code>uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path build/qt6-verification/generated/rc_metastudio src/rc_metastudio/start_page.py src/rc_metastudio/main_window.py src/rc_metastudio/results_window.py src/rc_metastudio/qt_layout.py src/rc_metastudio/analysis_identity.py src/rc_metastudio/r_bridge.py src/rc_metastudio/binary_data_dialog.py src/rc_metastudio/continuous_data_dialog.py src/rc_metastudio/diagnostic_data_dialog.py</code> |
| review1-types-finished | 0 | <code>uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path build/qt6-verification/generated/rc_metastudio src/rc_metastudio/results_window.py</code> |
| review1-types-reading | 0 | <code>uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path build/qt6-verification/generated/rc_metastudio src/rc_metastudio/results_window.py</code> |
| review1-types-renderer | 0 | <code>uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path build/qt6-verification/generated/rc_metastudio src/rc_metastudio/r_bridge.py</code> |
| review1-types-scoped | 1 | <code>uv run ty check --extra-search-path build/qt6-verification/generated/rc_metastudio/forms --extra-search-path build/qt6-verification/generated/rc_metastudio src/rc_metastudio/start_page.py src/rc_metastudio/main_window.py src/rc_metastudio/results_window.py src/rc_metastudio/qt_layout.py src/rc_metastudio/analysis_identity.py src/rc_metastudio/r_bridge.py src/rc_metastudio/binary_data_dialog.py src/rc_metastudio/continuous_data_dialog.py src/rc_metastudio/diagnostic_data_dialog.py</code> |
| review1-ui-boundaries-final | 1 | <code>uv run python -m pytest tests/python/gui/test_main_workspace_window.py tests/python/gui/test_main_window_automation_launch.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_data_workflows.py tests/python/gui/test_user_facing_text_regressions.py -q</code> |
| review1-ui-boundaries | 1 | <code>uv run python -m pytest tests/python/gui/test_main_workspace_window.py tests/python/gui/test_main_window_automation_launch.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_data_workflows.py tests/python/gui/test_user_facing_text_regressions.py -q</code> |
| review1-ui-clinical | 0 | <code>uv run python -m pytest tests/python/gui/test_main_workspace_window.py tests/python/gui/test_main_window_automation_launch.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_data_workflows.py tests/python/gui/test_user_facing_text_regressions.py -q</code> |
| review1-ui-final-current | 0 | <code>uv run python -m pytest tests/python/gui/test_main_workspace_window.py tests/python/gui/test_main_window_automation_launch.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_data_workflows.py tests/python/gui/test_user_facing_text_regressions.py -q</code> |
| review1-ui-finished | 0 | <code>uv run python -m pytest tests/python/gui/test_main_workspace_window.py tests/python/gui/test_main_window_automation_launch.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_data_workflows.py tests/python/gui/test_user_facing_text_regressions.py -q</code> |
| review1-ui-qualified | 0 | <code>uv run python -m pytest tests/python/gui/test_main_workspace_window.py tests/python/gui/test_main_window_automation_launch.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_data_workflows.py tests/python/gui/test_user_facing_text_regressions.py -q</code> |
| review1-ui-reading | 0 | <code>uv run python -m pytest tests/python/gui/test_main_workspace_window.py tests/python/gui/test_main_window_automation_launch.py tests/python/gui/test_results_workspace_layout.py tests/python/gui/test_main_window_data_workflows.py tests/python/gui/test_user_facing_text_regressions.py -q</code> |
| review1-ux-gestures-offscreen | 0 | <code>uv run python scripts/verify_rcms.py ux-improvements</code> |
| review1-ux-gestures | 0 | <code>uv run python scripts/verify_rcms.py ux-improvements --native</code> |
| review1-verbatim-whitespace | 2 | <code>git diff --cached --check</code> |
| review1-verified-generic-effect | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-generic-effect --native</code> |
| review1-verified-onearm-proportion | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-onearm-proportion --native</code> |
| review1-verified-reg-coef | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-reg-coef --native</code> |
| review1-verified-twoarm-proportion | 0 | <code>uv run python scripts/verify_rcms.py audit-round3-presentation-twoarm-proportion --native</code> |

Each runner receipt in [TEST-RUNS](TEST-RUNS.json) binds the exact argv, environment, revision, times and raw-log SHA. The full profile has its own three command receipts and hash-bound per-scenario manifests. Raw transcripts stay under ignored raw/ and artifacts/verification; curated failure lines are below.

## Verbatim failed-attempt output

### baseline-precision (exit 1)

```text
    assert action.isEnabled(), (scenario, workflow)
AssertionError: ('analysis-data-generic-effect', 'meta-regression')
    assert action.isEnabled(), (scenario, workflow)
AssertionError: ('analysis-data-generic-effect', 'meta-regression')
```

### baseline-presentation (exit 1)

```text
    assert b[0]-a[1] >= 4, ("weight/estimate gap", b[0]-a[1], weight.attrib, estimate.attrib)
AssertionError: ('weight/estimate gap', 3.824999999999932, {'x': '423.08', 'y': '173.31', 'text-anchor': 'middle', 'style': 'font-size: 11.76px; font-family: "Liberation Sans";', 'textLength': '33.31px', 'lengthAdjust': 'spacingAndGlyphs'}, {'x': '546.06', 'y': '171.90', 'text-anchor': 'end', 'style': 'font-size: 11.52px; font-family: "Liberation Sans";', 'textLength': '102.50px', 'lengthAdjust': 'spacingAndGlyphs'})
    assert b[0]-a[1] >= 4, ("weight/estimate gap", b[0]-a[1], weight.attrib, estimate.attrib)
AssertionError: ('weight/estimate gap', 3.824999999999932, {'x': '423.08', 'y': '173.31', 'text-anchor': 'middle', 'style': 'font-size: 11.76px; font-family: "Liberation Sans";', 'textLength': '33.31px', 'lengthAdjust': 'spacingAndGlyphs'}, {'x': '546.06', 'y': '171.90', 'text-anchor': 'end', 'style': 'font-size: 11.52px; font-family: "Liberation Sans";', 'textLength': '102.50px', 'lengthAdjust': 'spacingAndGlyphs'})
```

### bmj-observed-collision-checked (exit 1)

```text
    assert b[0]-a[1] >= 4 or a[0]-b[1] >= 4, ("model/footer collision", text, "".join(other.itertext()), a, b)
AssertionError: ('model/footer collision', '(DerSimonian–Laird)', '39 / 135', (46.8, 169.55, 262.43, 274.91), (158.765, 203.855, 259.03, 271.51))
```

### bmj-observed-collision (exit 1)

```text
    assert any("[0.000000, 0.400000]" in caption for caption in captions), captions
IndentationError: unexpected indent
```

### calculators-offscreen-1 (exit 1)

```text
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
E       AssertionError: Traceback (most recent call last):
E         RuntimeError: Verification inputs changed after desktop collection; restart the run
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-diagnostic]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-binary-metrics]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-continuous-metrics]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-diagnostic-metrics]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-onearm-proportion]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-onearm-mean]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-entered-binary]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-entered-continuous]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-entered-diagnostic]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-pre-post]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-back-binary]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-back-continuous]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-back-diagnostic]
```

### calculators-offscreen-2 (exit 2)

```text
        assert len(evidence_lines) == 1, result.stdout + result.stderr
E       AssertionError: Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261014T194327Z-ddf42c0f-calculator-diagnostic
E         RCMS calculator-diagnostic timed out after 120 seconds: /home/ali/Documents/Code/rc-metastudio/.venv/bin/python -X faulthandler /home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py calculator-diagnostic /home/ali/Documents/Code/rc-metastudio/build/verification/rcms/desktop-08aldv3o
        assert len(evidence_lines) == 1, result.stdout + result.stderr
E       AssertionError: Evidence: /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261014T194537Z-bfe912ab-calculator-mode-binary-metrics
E         RCMS calculator-mode-binary-metrics timed out after 120 seconds: /home/ali/Documents/Code/rc-metastudio/.venv/bin/python -X faulthandler /home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py calculator-mode-binary-metrics /home/ali/Documents/Code/rc-metastudio/build/verification/rcms/desktop-uxf4lbpv
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-diagnostic]
FAILED tests/e2e/test_desktop_workflows.py::test_desktop_workflow[calculator-mode-binary-metrics]
```

### full-final (exit 1)

```text
Failed; inspect /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261014T205345Z-d34ae089-complete/00.log
```

### full-qualification (exit 130)

```text
KeyboardInterrupt
```

### golden-before-refresh (exit 1)

```text
      {
        "classification": "text_artifact_drift",
        "dataset": "amino.rcms",
        "detail": "Text section Summary changed.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "continuous.rcms",
        "detail": "Text section Summary changed.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "lymph.rcms",
        "detail": "Text section Odds Ratio Summary changed.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
```

### native-calculator-mode-pre-post-complete (exit 1)

```text
    assert dialog.content_scroll.verticalScrollBar().maximum() == 0, (mode, dialog.size())
AssertionError: ('pre-post', PyQt6.QtCore.QSize(356, 388))
    assert not errors, errors
AssertionError: [AssertionError(('pre-post', PyQt6.QtCore.QSize(356, 388)))]
    assert not errors, errors
AssertionError: [AssertionError(('pre-post', PyQt6.QtCore.QSize(356, 388)))]
```

### native-calculator-mode-pre-post-final (exit 1)

```text
    assert dialog.content_scroll.verticalScrollBar().maximum() == 0, (mode, dialog.size())
AssertionError: ('pre-post', PyQt6.QtCore.QSize(356, 388))
    assert not errors, errors
AssertionError: [AssertionError(('pre-post', PyQt6.QtCore.QSize(356, 388)))]
    assert not errors, errors
AssertionError: [AssertionError(('pre-post', PyQt6.QtCore.QSize(356, 388)))]
```

### native-final-sequential (exit 1)

```text
    assert ticks and any(abs(float(line["x1"]) - float(line["x2"])) < .01
AssertionError: ('analysis.cumulative.cumulative forest_plot.1', 0, [234.51], [{'x1': '202.56', 'y1': '45.85', 'x2': '442.14', 'y2': '45.85', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '224.66', 'y1': '72.82', 'x2': '420.04', 'y2': '72.82', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '233.36', 'y1': '99.79', 'x2': '411.35', 'y2': '99.79', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '238.12', 'y1': '126.76', 'x2': '406.58', 'y2': '126.76', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '241.17', 'y1': '153.73', 'x2': '403.53', 'y2': '153.73', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '243.32', 'y1': '180.70', 'x2': '401.39', 'y2': '180.70', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '202.56', 'y1': '47.33', 'x2': '202.56', 'y2': '44.36', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '224.66', 'y1': '74.30', 'x2': '224.66', 'y2': '71.33', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '233.36', 'y1': '101.27', 'x2': '233.36', 'y2': '98.30', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '238.12', 'y1': '128.24', 'x2': '238.12', 'y2': '125.27', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '241.17', 'y1': '155.21', 'x2': '241.17', 'y2': '152.24', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '243.32', 'y1': '182.18', 'x2': '243.32', 'y2': '179.21', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '442.14', 'y1': '47.33', 'x2': '442.14', 'y2': '44.36', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '420.04', 'y1': '74.30', 'x2': '420.04', 'y2': '71.33', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '411.35', 'y1': '101.27', 'x2': '411.35', 'y2': '98.30', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '406.58', 'y1': '128.24', 'x2': '406.58', 'y2': '125.27', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '403.53', 'y1': '155.21', 'x2': '403.53', 'y2': '152.24', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '401.39', 'y1': '182.18', 'x2': '401.39', 'y2': '179.21', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '146.66', 'y1': '318.24', 'x2': '498.04', 'y2': '318.24', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '146.66', 'y1': '318.24', 'x2': '146.66', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '234.51', 'y1': '318.24', 'x2': '234.51', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '322.35', 'y1': '318.24', 'x2': '322.35', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '410.20', 'y1': '318.24', 'x2': '410.20', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '498.04', 'y1': '318.24', 'x2': '498.04', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '44.85', 'y1': '26.97', 'x2': '651.31', 'y2': '26.97', 'style': 'stroke-width: 0.60;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}])
    assert ticks and any(abs(float(line["x1"]) - float(line["x2"])) < .01
AssertionError: ('analysis.cumulative.cumulative forest_plot.1', 0, [234.51], [{'x1': '202.56', 'y1': '45.85', 'x2': '442.14', 'y2': '45.85', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '224.66', 'y1': '72.82', 'x2': '420.04', 'y2': '72.82', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '233.36', 'y1': '99.79', 'x2': '411.35', 'y2': '99.79', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '238.12', 'y1': '126.76', 'x2': '406.58', 'y2': '126.76', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '241.17', 'y1': '153.73', 'x2': '403.53', 'y2': '153.73', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '243.32', 'y1': '180.70', 'x2': '401.39', 'y2': '180.70', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '202.56', 'y1': '47.33', 'x2': '202.56', 'y2': '44.36', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '224.66', 'y1': '74.30', 'x2': '224.66', 'y2': '71.33', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '233.36', 'y1': '101.27', 'x2': '233.36', 'y2': '98.30', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '238.12', 'y1': '128.24', 'x2': '238.12', 'y2': '125.27', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '241.17', 'y1': '155.21', 'x2': '241.17', 'y2': '152.24', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '243.32', 'y1': '182.18', 'x2': '243.32', 'y2': '179.21', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '442.14', 'y1': '47.33', 'x2': '442.14', 'y2': '44.36', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '420.04', 'y1': '74.30', 'x2': '420.04', 'y2': '71.33', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '411.35', 'y1': '101.27', 'x2': '411.35', 'y2': '98.30', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '406.58', 'y1': '128.24', 'x2': '406.58', 'y2': '125.27', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '403.53', 'y1': '155.21', 'x2': '403.53', 'y2': '152.24', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '401.39', 'y1': '182.18', 'x2': '401.39', 'y2': '179.21', 'style': 'stroke-width: 1.01;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '146.66', 'y1': '318.24', 'x2': '498.04', 'y2': '318.24', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '146.66', 'y1': '318.24', 'x2': '146.66', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '234.51', 'y1': '318.24', 'x2': '234.51', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '322.35', 'y1': '318.24', 'x2': '322.35', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '410.20', 'y1': '318.24', 'x2': '410.20', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '498.04', 'y1': '318.24', 'x2': '498.04', 'y2': '321.84', 'style': 'stroke-width: 0.75;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}, {'x1': '44.85', 'y1': '26.97', 'x2': '651.31', 'y2': '26.97', 'style': 'stroke-width: 0.60;', 'fill': 'none', 'stroke': '#000000', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-miterlimit': '10.00'}])
```

### native-precision-1 (exit 1)

```text
    assert tick_left - title_right >= 4, ("tick/title gap", tick_left, title.attrib)
AssertionError: ('tick/title gap', 46.04, {'transform': 'translate(32.76,154.80) rotate(-90)', 'text-anchor': 'middle', 'style': 'font-size: 12.00px; font-family: "Liberation Sans";', 'textLength': '74.45px', 'lengthAdjust': 'spacingAndGlyphs'})
    assert tick_left - title_right >= 4, ("tick/title gap", tick_left, title.attrib)
AssertionError: ('tick/title gap', 46.04, {'transform': 'translate(32.76,154.80) rotate(-90)', 'text-anchor': 'middle', 'style': 'font-size: 12.00px; font-family: "Liberation Sans";', 'textLength': '74.45px', 'lengthAdjust': 'spacingAndGlyphs'})
```

### native-presentation-1 (exit 1)

```text
    assert headers == ["Mean", "SD", "Total", "Mean", "SD", "Total", "Weight"], headers
AssertionError: ['Mean', 'SD', 'N', 'Mean', 'SD', 'N']
    assert headers == ["Mean", "SD", "Total", "Mean", "SD", "Total", "Weight"], headers
AssertionError: ['Mean', 'SD', 'N', 'Mean', 'SD', 'N']
```

### native-presentation-2 (exit 1)

```text
    assert headers == expected_headers, headers
AssertionError: ['Total', 'Mean', 'SD', 'Total', 'Mean', 'SD', 'Weight']
    assert headers == expected_headers, headers
AssertionError: ['Total', 'Mean', 'SD', 'Total', 'Mean', 'SD', 'Weight']
```

### native-presentation-3 (exit 1)

```text
RCMS audit-round3-presentation timed out after 600 seconds: /home/ali/Documents/Code/rc-metastudio/.venv/bin/python -X faulthandler /home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py audit-round3-presentation /home/ali/Documents/Code/rc-metastudio/build/verification/rcms/desktop-_ahj17ab
```

### native-project-table-covariates-verified (exit 1)

```text
StopIteration
```

### r-presentation-current (exit 1)

```text
Error:
```

### retained-ui-checks (exit 1)

```text
            assert window.open(_sample_project_path("amino.rcms")) is True
            assert (
            assert (
            assert cov_model.headerData(
            assert display_value not in (None, "")
            assert not hasattr(display_value, "value")
            assert cov_model.setData(cov_model.index(0, cov_model.NEW_VAL), "High") is True
            assert (
            assert (
E           AssertionError: assert ['Numeric cov...ire numbers.'] == ['Covariate v... be numeric.']
                assert field.maxLength() == PLOT_TEXT_INPUT_LIMIT
E               AssertionError: assert 'publication readability' in 'Automatic: determined by the plotted data'
E           AssertionError: assert 'About and licenses…' == 'About/Legal'
E           RuntimeError: RC MetaStudio wizard pages require MainWizard ownership
FAILED tests/python/gui/test_main_window_automation_launch.py::test_change_covariate_type_model_returns_native_values_and_accepts_native_edits
FAILED tests/python/gui/test_main_window_automation_launch.py::test_plot_text_inputs_enforce_publication_readability_limit
FAILED tests/python/gui/test_main_window_automation_launch.py::test_about_legal_and_welcome_links_show_current_project_information
FAILED tests/python/gui/test_main_window_automation_launch.py::test_csv_required_format_table_expands_and_shows_all_rows
```

### review1-bounded-project-shell (exit 1)

```text
    assert window.size() == remembered_size, (window.size(), remembered_size)
AssertionError: (PyQt6.QtCore.QSize(1600, 828), PyQt6.QtCore.QSize(700, 500))
    assert window.size() == remembered_size, (window.size(), remembered_size)
AssertionError: (PyQt6.QtCore.QSize(1600, 828), PyQt6.QtCore.QSize(700, 500))
```

### review1-captions-before (exit 1)

```text
    assert view.report_text.toPlainText().count("Overall ML likelihood-ratio test") == 1
AssertionError
    assert view.report_text.toPlainText().count("Overall ML likelihood-ratio test") == 1
AssertionError
```

### review1-clinical-audit-round3-presentation-transforms (exit 1)

```text
    assert b[0]-a[1] >= 4 or a[0]-b[1] >= 4, ("model/footer collision", text, "".join(other.itertext()), a, b)
AssertionError: ('model/footer collision', 'Test for overall effect (H₀: proportion = 1): Z = -9.052 (P < 0.001)', '0.05', (46.35, 401.1, 313.60999999999996, 326.09), (404.01, 428.28999999999996, 320.09999999999997, 332.58))
    assert b[0]-a[1] >= 4 or a[0]-b[1] >= 4, ("model/footer collision", text, "".join(other.itertext()), a, b)
AssertionError: ('model/footer collision', 'Test for overall effect (H₀: proportion = 1): Z = -9.052 (P < 0.001)', '0.05', (46.35, 401.1, 313.60999999999996, 326.09), (404.01, 428.28999999999996, 320.09999999999997, 332.58))
```

### review1-clinical-order-before (exit 1)

```text
    assert report.startswith("Model configuration\n"), report
AssertionError: Clinical interpretation
    assert report.startswith("Model configuration\n"), report
AssertionError: Clinical interpretation
```

### review1-clinical-qualified-analysis-diagnostic-combined (exit 1)

```text
    assert properties.lr_dor_panel.method == dialog.lr_dor_panel.method
RuntimeError: wrapped C/C++ object of type AdaptiveComboBox has been deleted
    assert properties.lr_dor_panel.method == dialog.lr_dor_panel.method
RuntimeError: wrapped C/C++ object of type AdaptiveComboBox has been deleted
```

### review1-clinical-sidebar-before (exit 1)

```text
    assert view.nav_tree.currentItem().text(0) == "Text report"
AssertionError
    assert view.nav_tree.currentItem().text(0) == "Text report"
AssertionError
```

### review1-coefficient-editor-before (exit 1)

```text
rpy2.rinterface_lib.embedded.RRuntimeError: Error in if (ncol(bundle$ilab$matrix) > 0) { : argument is of length zero
rpy2.rinterface_lib.embedded.RRuntimeError: Error in if (ncol(bundle$ilab$matrix) > 0) { : argument is of length zero
```

### review1-complete-project-shell (exit 1)

```text
    assert not errors, errors
AssertionError: ["You've made unsaved changes to your data. Do you want to save your changes?"]
    assert not errors, errors
AssertionError: ["You've made unsaved changes to your data. Do you want to save your changes?"]
```

### review1-design-before (exit 1)

```text
    assert window.cl_label.text() == 'Confidence level: 95%'
AssertionError
    assert window.cl_label.text() == 'Confidence level: 95%'
AssertionError
```

### review1-diagnostic-before (exit 1)

```text
    assert box[2]-other_box[3] >= 2 or other_box[2]-box[3] >= 2, ("header leading", "".join(other.itertext()), box, other_box)
AssertionError: ('header leading', 'Sensitivity', (687.18, 760.8, 10.879999999999999, 23.84), (696.03, 760.8, 1.5299999999999994, 14.49))
    assert box[2]-other_box[3] >= 2 or other_box[2]-box[3] >= 2, ("header leading", "".join(other.itertext()), box, other_box)
AssertionError: ('header leading', 'Sensitivity', (687.18, 760.8, 10.879999999999999, 23.84), (696.03, 760.8, 1.5299999999999994, 14.49))
```

### review1-final-generic-effect (exit 1)

```text
    assert b[0]-a[1] >= 4 or a[0]-b[1] >= 4, ("model/footer collision", text, "".join(other.itertext()), a, b)
AssertionError: ('model/footer collision', 'Random-effects model (DerSimonian–Laird)', '100.0%', (45.03, 337.29999999999995, 216.46, 230.46), (340.315, 387.765, 218.07, 232.07))
    assert b[0]-a[1] >= 4 or a[0]-b[1] >= 4, ("model/footer collision", text, "".join(other.itertext()), a, b)
AssertionError: ('model/footer collision', 'Random-effects model (DerSimonian–Laird)', '100.0%', (45.03, 337.29999999999995, 216.46, 230.46), (340.315, 387.765, 218.07, 232.07))
```

### review1-full-complete (exit 1)

```text
Failed; inspect /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261014T223321Z-9644f637-complete/00.log
```

### review1-full-current (exit 1)

```text
Failed; inspect /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261014T224356Z-34556ec1-complete/00.log
```

### review1-full-final (exit 1)

```text
Failed; inspect /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261014T221926Z-4187a690-complete/00.log
{
  "reason": "Visual inspection found an incorrect single-arm logit null variable name; invalidate in-flight source qualification before fixing it.",
  "owned_root_pid": 806028,
  "signalled_r_test_pid": 807807,
  "signal": "SIGINT",
  "command": [
    "/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/exec/R",
    "-f",
    "testthat.R",
    "--restore",
    "--save",
    "--no-readline",
    "--vanilla"
  ],
  "evidence": "artifacts/verification/rcms/20261014T221926Z-4187a690-complete",
  "qualification": "Deliberately interrupted; not current-source qualification.",
  "bounded_cleanup": "R test did not exit on SIGINT; sent SIGTERM to the same verified test PID."
}
```

### review1-full-fresh (exit 1)

```text
Failed; inspect /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261014T231308Z-cbfa6af0-complete/00.log
```

### review1-full-gates (exit 1)

```text
Failed; inspect /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261014T233457Z-111de8a6-complete/00.log
```

### review1-full-qualified (exit 1)

```text
Failed; inspect /home/ali/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261014T224015Z-d4817349-complete/00.log
{
  "utc": "2026-10-14T22:42:46.307594+00:00",
  "pid": 821462,
  "command": "/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/exec/R --no-restore --no-echo --args nextArg--no-manualnextArg--no-build-vignettesnextArg--library=/tmp/RCMetaR-r-stack-6jlsiekq/librarynextArg/tmp/RCMetaR-r-stack-6jlsiekq/RCMetaR_0.4.2.tar.gz ",
  "signal": "SIGTERM",
  "reason": "Previous completed R check disclosed non-ASCII source warning; this same-source repeat cannot qualify Status: OK. Stop owned check before its retained tests; escape the literal en dash without changing output, then restart fresh."
}
```

### review1-golden-review (exit 1)

```text
      {
        "classification": "text_artifact_drift",
        "dataset": "amino.rcms",
        "detail": "Text section Summary changed.",
        "id": "amino-binary-random",
        "method": "binary.random",
        "metric": "OR"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "continuous.rcms",
        "detail": "Text section Summary changed.",
        "id": "continuous-random",
        "method": "continuous.random",
        "metric": "SMD"
      },
      {
        "classification": "text_artifact_drift",
        "dataset": "lymph.rcms",
        "detail": "Text section Odds Ratio Summary changed.",
        "id": "lymph-diagnostic-random-dor",
        "method": [
          "diagnostic.random"
        ],
        "metric": "DOR"
      },
```

### review1-native-figures-transforms (exit 1)

```text
R callback write-console: Error: Must specify the sample sizes via the 'targs' argument.
    assert len(found) == 1, (kind, found)
AssertionError: (<class 'rc_metastudio.results_window.ResultsWindow'>, [])
    assert len(found) == 1, (kind, found)
AssertionError: (<class 'rc_metastudio.results_window.ResultsWindow'>, [])
```

### review1-null-footer-before-contract (exit 1)

```text
    assert min(points[1],points[3]) >= box[3]+2 or max(points[1],points[3]) <= box[2]-2, ('reference over footer', ''.join(footer.itertext()), points, box)
AssertionError: ('reference over footer', 'Heterogeneity: τ² = 0.019; Q = 11.455, df = 5 (P = 0.043); I² = 56.4%', [371.82, 469.44, 371.82, 72.0], (52.13, 441.46999999999997, 360.09000000000003, 373.05))
```

### review1-references-qualified (exit 1)

```text
    assert report.startswith("Model configuration\n"), report
AssertionError: Sensitivity Summary
    assert report.startswith("Model configuration\n"), report
AssertionError: Sensitivity Summary
```

### review1-sidebar-before (exit 1)

```text
    assert view.nav_tree.currentItem().text(0) == 'Text report'
AssertionError
    assert view.nav_tree.currentItem().text(0) == 'Text report'
AssertionError
```

### review1-static-check (exit 1)

```text
error[no-matching-overload]: No overload of function `mouseClick` matches arguments
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[no-matching-overload]: No overload of function `keyClick` matches arguments
error[invalid-argument-type]: Argument to bound method `__init__` is incorrect
error[no-matching-overload]: No overload of function `mouseClick` matches arguments
error[no-matching-overload]: No overload of function `mouseClick` matches arguments
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[no-matching-overload]: No overload of function `mouseClick` matches arguments
error[not-subscriptable]: Cannot subscript object of type `int` with no `__getitem__` method
error[not-subscriptable]: Cannot subscript object of type `float` with no `__getitem__` method
error[possibly-unresolved-reference]: Name `rendered` used when possibly not defined
error[no-matching-overload]: No overload of function `keyClick` matches arguments
error[possibly-unresolved-reference]: Name `diagnostic_interval` used when possibly not defined
error[no-matching-overload]: No overload of function `mouseClick` matches arguments
error[no-matching-overload]: No overload of function `keyClick` matches arguments
error[no-matching-overload]: No overload of function `mouseClick` matches arguments
error[no-matching-overload]: No overload of function `mouseClick` matches arguments
error[no-matching-overload]: No overload of function `mouseClick` matches arguments
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[possibly-unresolved-reference]: Name `case` used when possibly not defined
error[invalid-argument-type]: Argument to function `__new__` is incorrect
error[not-subscriptable]: Cannot subscript object of type `object` with no `__getitem__` method
error[call-non-callable]: Object of type `str` is not callable
error[unresolved-attribute]: Attribute `start_automation` is not defined on `str` in union `Unknown | str`
error[call-non-callable]: Object of type `str` is not callable
error[unresolved-attribute]: Attribute `topLevelWidgets` is not defined on `None` in union `None | Unknown`
error[unresolved-attribute]: Attribute `QMessageBox` is not defined on `str` in union `Unknown | str`
error[call-non-callable]: Object of type `str` is not callable
error[unresolved-attribute]: Attribute `QTimer` is not defined on `str` in union `Unknown | str`
error[call-non-callable]: Object of type `str` is not callable
error[unresolved-attribute]: Attribute `dispose_qobjects` is not defined on `str` in union `Unknown | str`
error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
error[call-non-callable]: Object of type `str` is not callable
error[call-non-callable]: Object of type `str` is not callable
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[call-non-callable]: Object of type `str` is not callable
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[no-matching-overload]: No overload of function `mouseClick` matches arguments
error[call-non-callable]: Object of type `str` is not callable
error[call-non-callable]: Object of type `str` is not callable
error[call-non-callable]: Object of type `str` is not callable
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[call-non-callable]: Object of type `str` is not callable
error[no-matching-overload]: No overload of function `mouseClick` matches arguments
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[no-matching-overload]: No overload of function `mouseClick` matches arguments
error[call-non-callable]: Object of type `str` is not callable
error[call-non-callable]: Object of type `str` is not callable
error[call-non-callable]: Object of type `str` is not callable
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[call-non-callable]: Object of type `str` is not callable
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[call-non-callable]: Object of type `str` is not callable
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[no-matching-overload]: No overload of function `mouseClick` matches arguments
error[missing-argument]: No argument provided for required parameter `ms` of function `qWait`
error[invalid-argument-type]: Argument to function `qWait` is incorrect
error[call-non-callable]: Object of type `str` is not callable
error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
error[unsupported-operator]: Unsupported `/` operation
error[not-iterable]: Object of type `int` is not iterable
error[not-iterable]: Object of type `float` is not iterable
error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
error[not-iterable]: Object of type `int` is not iterable
error[not-iterable]: Object of type `float` is not iterable
error[invalid-argument-type]: Argument to function `module_from_spec` is incorrect
error[unresolved-attribute]: Attribute `loader` is not defined on `None` in union `ModuleSpec | None`
error[unresolved-attribute]: Attribute `exec_module` is not defined on `None` in union `Loader | None`
error[possibly-unresolved-reference]: Name `evidence` used when possibly not defined
error[possibly-unresolved-reference]: Name `evidence` used when possibly not defined
error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
error[unresolved-import]: Cannot resolve imported module `qt_window_ownership`
error[unresolved-import]: Cannot resolve imported module `inspect_macos_deployment`
error[unresolved-import]: Cannot resolve imported module `pefile`
error[unresolved-import]: Cannot resolve imported module `local_r_test_backend`
error[unresolved-import]: Cannot resolve imported module `local_r_test_backend`
error[unresolved-import]: Cannot resolve imported module `local_r_test_backend`
error[unresolved-import]: Cannot resolve imported module `local_r_test_backend`
error[unresolved-import]: Cannot resolve imported module `pefile`
error[unresolved-attribute]: Module `winreg` has no member `HKEY_CURRENT_USER`
error[unresolved-attribute]: Module `winreg` has no member `HKEY_LOCAL_MACHINE`
error[unresolved-attribute]: Module `winreg` has no member `OpenKey`
error[unresolved-attribute]: Module `winreg` has no member `QueryValueEx`
77 |                     except OSError:
error[unresolved-attribute]: Module `winreg` has no member `QueryValueEx`
83 |                     except OSError:
error[unresolved-attribute]: Module `winreg` has no member `OpenKey`
error[unresolved-attribute]: Module `winreg` has no member `QueryValueEx`
error[unresolved-attribute]: Module `winreg` has no member `EnumKey`
 99 |                         except OSError:
error[unresolved-attribute]: Module `winreg` has no member `OpenKey`
error[unresolved-attribute]: Module `winreg` has no member `QueryValueEx`
error[unresolved-import]: Cannot resolve imported module `r_verification_support`
error[unresolved-import]: Cannot resolve imported module `r_verification_support`
error[unresolved-import]: Cannot resolve imported module `r_verification_support`
error[unresolved-import]: Cannot resolve imported module `ui_about_legal`
error[unresolved-import]: Cannot resolve imported module `ui_new_covariate_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_new_follow_up_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_new_group_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_new_outcome_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_new_study_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_analysis_setup_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_binary_back_calculation_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_binary_data_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_confidence_level_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_continuous_back_calculation_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_continuous_data_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_covariate_type_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_diagnostic_data_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_diagnostic_metrics_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_edit_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_edit_name_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_funnel_plot_editor_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_main_window`
error[unresolved-import]: Cannot resolve imported module `ui_choose_metric_page`
error[unresolved-import]: Cannot resolve imported module `ui_csv_import_page`
error[unresolved-import]: Cannot resolve imported module `ui_data_type_page`
error[unresolved-import]: Cannot resolve imported module `ui_outcome_name_page`
error[unresolved-import]: Cannot resolve imported module `ui_welcome_page`
error[unresolved-import]: Cannot resolve imported module `ui_edit_plot_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_progress_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_publication_bias_dialog`
error[invalid-method-override]: Invalid override of method `sizeFromContents`
error[unresolved-import]: Cannot resolve imported module `ui_results_window`
error[unresolved-attribute]: Attribute `setDocumentMargin` is not defined on `None` in union `QTextDocument | None`
error[unresolved-attribute]: Attribute `widget` is not defined on `None` in union `Unknown | QLayoutItem | None`
error[unresolved-import]: Cannot resolve imported module `ui_subgroup_analysis_dialog`
error[unresolved-import]: Cannot resolve imported module `verify_golden_compatibility`
error[unresolved-import]: Cannot resolve imported module `verify_rcmetar_r_stack`
error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
error[possibly-unresolved-reference]: Name `lines` used when possibly not defined
error[possibly-unresolved-reference]: Name `ticks` used when possibly not defined
error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
error[not-subscriptable]: Cannot subscript object of type `None` with no `__getitem__` method
error[invalid-argument-type]: Argument to bound method `__init__` is incorrect
error[possibly-unresolved-reference]: Name `bounds` used when possibly not defined
error[possibly-unresolved-reference]: Name `ticks` used when possibly not defined
error[possibly-unresolved-reference]: Name `bounds` used when possibly not defined
error[unresolved-import]: Cannot resolve imported module `audit_qt_layout_contracts`
error[unresolved-import]: Cannot resolve imported module `ui_analysis_setup_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_analysis_setup_dialog`
error[unresolved-import]: Cannot resolve imported module `ui_main_window`
Found 178 diagnostics
```

### review1-transformed-axis (exit 1)

```text
AssertionError: {'metric': 'PFT', 'ticks': [], 'labels': []}
AssertionError: {'metric': 'PFT', 'ticks': [], 'labels': []}
```

### review1-transformed-null-before (exit 1)

```text
AssertionError: ['Logit transformed Proportion (probability scale)', 'Fixture 6', 'Fixture 5', 'Fixture 4', 'Fixture 3', 'Fixture 2', 'Fixture 1', '9', '8', '7', '6', '5', '4', 'Events', '16', '16', '16', '16', '16', '16', 'Non-events', 'Study', ' 0.1', ' 0.2', ' 0.3', ' 0.4', ' 0.5', '0.200 [0.077, 0.428]', '0.238 [0.103, 0.460]', '0.273 [0.128, 0.489]', '0.304 [0.153, 0.515]', '0.333 [0.176, 0.539]', '0.360 [0.199, 0.560]', '0.292 [0.221, 0.375]', 'Logit transformed Proportion [95% CI]', 'tx A', 'Random-effects model (DerSimonian–Laird)', 'Heterogeneity: τ² = 0.000; Q = 1.904, df = 5 (P = 0.862); I² = 0.0%', 'Test for overall effect (H₀: logit transformed Proportion = 0.5): Z = -4.625 (P < 0.001)', '95% prediction interval: [0.221, 0.375]']
```

### review1-types-scoped (exit 1)

```text
error[invalid-method-override]: Invalid override of method `sizeFromContents`
error[unresolved-attribute]: Attribute `value` is not defined on `None` in union `Unknown | QScrollBar | None`
error[unresolved-attribute]: Attribute `maximum` is not defined on `None` in union `Unknown | QScrollBar | None`
error[unresolved-attribute]: Attribute `setValue` is not defined on `None` in union `Unknown | QScrollBar | None`
error[unresolved-attribute]: Attribute `maximum` is not defined on `None` in union `Unknown | QScrollBar | None`
error[unresolved-attribute]: Attribute `setValue` is not defined on `None` in union `Unknown | QScrollBar | None`
Found 6 diagnostics
```

### review1-ui-boundaries-final (exit 1)

```text
FAILED tests/python/gui/test_main_window_data_workflows.py::test_main_window_dialog_text_slots_accept_native_pyqt6_line_edit_strings
```

### review1-ui-boundaries (exit 1)

```text
            assert state.policy.archetype is adaptive_window.WindowArchetype.WORKSPACE
            assert state.role is adaptive_window.WindowRole.MAIN
            assert (
            assert (
            assert (
                assert window.navigationLayout.indexOf(control) >= 0
E           AssertionError: assert 'Fit columns' == 'Auto-Fit Columns'
        assert image.save(str(plot_path), "PNG")
E           AssertionError: assert ['Text report... 'References'] == ['Summary', '... 'References']
        assert form.plot_tab.isEnabled()
        assert not form.plot_tab.isEnabled()
E       AssertionError: assert 'exactly one continuous covariate' in 'Bubble plot options require exactly one Numeric covariate.'
E           AssertionError: assert ['Text report...onfiguration'] == ['Summary']
FAILED tests/python/gui/test_main_workspace_window.py::test_main_is_a_managed_workspace_with_expanding_table_and_layouted_navigation
FAILED tests/python/gui/test_main_window_automation_launch.py::test_results_window_places_references_after_images_and_wraps_them
FAILED tests/python/gui/test_main_window_automation_launch.py::test_meta_regression_enables_plots_only_for_one_continuous_covariate
FAILED tests/python/gui/test_main_window_automation_launch.py::test_results_window_ignores_missing_image_order_entries
FAILED tests/python/gui/test_main_window_data_workflows.py::test_main_window_dialog_text_slots_accept_native_pyqt6_line_edit_strings
```

### review1-verbatim-whitespace (exit 2)

```text
["git", "diff", "--cached", "--check"]
docs/ux-audit/2026-10-15-round4/REVIEW1-UX-DRIVER-FAILURES.txt:2: trailing whitespace.
+  
docs/ux-audit/2026-10-15-round4/REVIEW1-UX-DRIVER-FAILURES.txt:4: trailing whitespace.
+  
docs/ux-audit/2026-10-15-round4/REVIEW1-UX-DRIVER-FAILURES.txt:6: trailing whitespace.
+  
docs/ux-audit/2026-10-15-round4/REVIEW1-UX-DRIVER-FAILURES.txt:7: trailing whitespace.
+R callback write-console: 
docs/ux-audit/2026-10-15-round4/REVIEW1-UX-DRIVER-FAILURES.txt:14: trailing whitespace.
+  
docs/ux-audit/2026-10-15-round4/REVIEW1-UX-DRIVER-FAILURES.txt:18: trailing whitespace.
+R callback write-console: Error in rma.uni(yi = binary.data@y, sei = binary.data@SE, slab = binary.data@study.names,  : 
docs/ux-audit/2026-10-15-round4/REVIEW1-UX-DRIVER-FAILURES.txt:20: trailing whitespace.
+  
```

## Fresh qualification failures (verbatim)

The completed fresh matrix reported `3 failed, 105 passed in 1531.21s (0:25:31)`. The three failed children and native coefficient reproduction are hash-bound by REVIEW1-QUALIFICATION-FAILURES.json. The production repair dispatches Reitsma coefficient defaults by its existing renderer predicate; the calculator driver separately verifies unsupported back-calculation is hidden.

```text
artifacts/verification/rcms/20261015T000417Z-7ca2a20d-calculator-mode-onearm-proportion
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 83, in ready
    drive(dialog)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1074, in drive
    assert all(widget.isVisible() and widget.visibleRegion().boundingRect().contains(widget.rect()) for widget in primary)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 761, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1687, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1091, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 97, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError()]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 761, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1687, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1091, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 97, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError()]

artifacts/verification/rcms/20261015T000425Z-4c43f66e-plot-workflow-coefficient
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
R callback write-console: Error in if (ncol(bundle$ilab$matrix) > 0) { : argument is of length zero
  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 761, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1685, in run
    plots(app, window, scenario.removeprefix("plot-workflow-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 377, in plots
    artifact = next(
               ^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 384, in <genexpr>
    or view.plot_service.load_params(a.params_path).get(
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/plot_service.py", line 66, in load_params
    params = self.bridge.load_vars_for_plot(params_path, return_params_dict=True)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_call_serialization.py", line 63, in _serialized_r_call
    return function(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 1190, in load_vars_for_plot
    defaults = r_object_to_python(execute_r_string("""local({
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_call_serialization.py", line 63, in _serialized_r_call
    return function(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 172, in execute_r_string
    return _r_eval(r_str)
           ^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 142, in _r_eval
    return evaluator(expression)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.venv/lib/python3.11/site-packages/rpy2/robjects/__init__.py", line 552, in __call__
    res, visible = rinterface.evalr_expr_with_visible(   # type: ignore
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.venv/lib/python3.11/site-packages/rpy2/rinterface/__init__.py", line 204, in evalr_expr_with_visible
    raise embedded.RRuntimeError(_rinterface._geterrmessage())
rpy2.rinterface_lib.embedded.RRuntimeError: Error in if (ncol(bundle$ilab$matrix) > 0) { : argument is of length zero

Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 761, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1685, in run
    plots(app, window, scenario.removeprefix("plot-workflow-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 377, in plots
    artifact = next(
               ^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 384, in <genexpr>
    or view.plot_service.load_params(a.params_path).get(
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/plot_service.py", line 66, in load_params
    params = self.bridge.load_vars_for_plot(params_path, return_params_dict=True)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_call_serialization.py", line 63, in _serialized_r_call
    return function(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 1190, in load_vars_for_plot
    defaults = r_object_to_python(execute_r_string("""local({
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_call_serialization.py", line 63, in _serialized_r_call
    return function(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 172, in execute_r_string
    return _r_eval(r_str)
           ^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 142, in _r_eval
    return evaluator(expression)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.venv/lib/python3.11/site-packages/rpy2/robjects/__init__.py", line 552, in __call__
    res, visible = rinterface.evalr_expr_with_visible(   # type: ignore
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.venv/lib/python3.11/site-packages/rpy2/rinterface/__init__.py", line 204, in evalr_expr_with_visible
    raise embedded.RRuntimeError(_rinterface._geterrmessage())
rpy2.rinterface_lib.embedded.RRuntimeError: Error in if (ncol(bundle$ilab$matrix) > 0) { : argument is of length zero


artifacts/verification/rcms/20261015T000431Z-16f5c4cd-calculator-mode-onearm-mean
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 83, in ready
    drive(dialog)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1074, in drive
    assert all(widget.isVisible() and widget.visibleRegion().boundingRect().contains(widget.rect()) for widget in primary)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 761, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1687, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1091, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 97, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError()]
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 761, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1687, in run
    calculators(app, window, scenario.removeprefix("calculator-mode-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1091, in calculators
    modal(app, kind, drive, launch)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 97, in modal
    assert not errors, errors
           ^^^^^^^^^^
AssertionError: [AssertionError()]

artifacts/verification/rcms/20261015T000750Z-34499469-plot-workflow-coefficient
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
R callback write-console: Error in if (ncol(bundle$ilab$matrix) > 0) { : argument is of length zero
  
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 761, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1685, in run
    plots(app, window, scenario.removeprefix("plot-workflow-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 377, in plots
    artifact = next(
               ^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 384, in <genexpr>
    or view.plot_service.load_params(a.params_path).get(
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/plot_service.py", line 66, in load_params
    params = self.bridge.load_vars_for_plot(params_path, return_params_dict=True)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_call_serialization.py", line 63, in _serialized_r_call
    return function(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 1190, in load_vars_for_plot
    defaults = r_object_to_python(execute_r_string("""local({
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_call_serialization.py", line 63, in _serialized_r_call
    return function(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 172, in execute_r_string
    return _r_eval(r_str)
           ^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 142, in _r_eval
    return evaluator(expression)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.venv/lib/python3.11/site-packages/rpy2/robjects/__init__.py", line 552, in __call__
    res, visible = rinterface.evalr_expr_with_visible(   # type: ignore
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.venv/lib/python3.11/site-packages/rpy2/rinterface/__init__.py", line 204, in evalr_expr_with_visible
    raise embedded.RRuntimeError(_rinterface._geterrmessage())
rpy2.rinterface_lib.embedded.RRuntimeError: Error in if (ncol(bundle$ilab$matrix) > 0) { : argument is of length zero

Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 761, in <module>
    run(app, window, scenario, record_step)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 1685, in run
    plots(app, window, scenario.removeprefix("plot-workflow-"), record)
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 377, in plots
    artifact = next(
               ^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.agents/skills/verify-rcms/scripts/advanced_workflows.py", line 384, in <genexpr>
    or view.plot_service.load_params(a.params_path).get(
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/plot_service.py", line 66, in load_params
    params = self.bridge.load_vars_for_plot(params_path, return_params_dict=True)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_call_serialization.py", line 63, in _serialized_r_call
    return function(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 1190, in load_vars_for_plot
    defaults = r_object_to_python(execute_r_string("""local({
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_call_serialization.py", line 63, in _serialized_r_call
    return function(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 172, in execute_r_string
    return _r_eval(r_str)
           ^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py", line 142, in _r_eval
    return evaluator(expression)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.venv/lib/python3.11/site-packages/rpy2/robjects/__init__.py", line 552, in __call__
    res, visible = rinterface.evalr_expr_with_visible(   # type: ignore
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ali/Documents/Code/rc-metastudio/.venv/lib/python3.11/site-packages/rpy2/rinterface/__init__.py", line 204, in evalr_expr_with_visible
    raise embedded.RRuntimeError(_rinterface._geterrmessage())
rpy2.rinterface_lib.embedded.RRuntimeError: Error in if (ncol(bundle$ilab$matrix) > 0) { : argument is of length zero


```

## Failed UX driver child (verbatim)

Maintained entry point: `uv run python scripts/verify_rcms.py ux-improvements` (offscreen within review1-full-fresh). The corrected native and offscreen gesture drives are recorded separately.

```text
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
R callback write-console: Error in rma.uni(yi = binary.data@y, sei = binary.data@SE, slab = binary.data@study.names,  : 
  Unknown 'method' specified.
  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 740, in <module>
    run(app, window, WORK, ROOT, record_step, analyze)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/ux_workflows.py", line 146, in run
    artifact = view._selected_plot()[0]
               ~~~~~~~~~~~~~~~~~~~~~^^^
TypeError: 'NoneType' object is not subscriptable
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 740, in <module>
    run(app, window, WORK, ROOT, record_step, analyze)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/ux_workflows.py", line 146, in run
    artifact = view._selected_plot()[0]
               ~~~~~~~~~~~~~~~~~~~~~^^^
TypeError: 'NoneType' object is not subscriptable

```

## Failed reference child (verbatim)

Exact maintained entry point: `uv run python scripts/verify_rcms.py audit-round3-references` (offscreen, within review1-full-current). The failed child manifest is bound by REVIEW1-MATRIX-FAILURE.json.

```text
R callback write-console: Loading required package: Matrix
  
R callback write-console: Loading required package: metadat
  
R callback write-console: Loading required package: numDeriv
  
R callback write-console: 
Loading the 'metafor' package (version 5.0-1). For an
introduction to the package please type: help(metafor)

An updated version of the package (version 5.2-1) is available!
To update to this version type: install.packages("metafor")

  
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
qt.gui.imageio: QImageIOHandler: Rejecting image as it exceeds the current allocation limit of 256 megabytes
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
qt.gui.imageio: QImageIOHandler: Rejecting image as it exceeds the current allocation limit of 256 megabytes
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 724, in <module>
    run(app, window, WORK, record_step, scenario)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 804, in run
    check_standard_heterogeneity(view, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 170, in check_standard_heterogeneity
    weights = next(t for section in view.results.sections for t in section.tables if t.title == "Study weights")
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
StopIteration
Traceback (most recent call last):
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/desktop_driver.py", line 724, in <module>
    run(app, window, WORK, record_step, scenario)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 804, in run
    check_standard_heterogeneity(view, record)
  File "/home/ali/Documents/Code/rc-metastudio/tests/e2e/audit_round3.py", line 170, in check_standard_heterogeneity
    weights = next(t for section in view.results.sections for t in section.tables if t.title == "Study weights")
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
StopIteration

```

## Completed R check failure (verbatim)

```text
[03:33:21] Skipping dependency sync for warm local R verification
[03:33:21] $ /home/ali/Documents/Code/rc-metastudio/.venv/bin/python scripts/build_qt6.py generate --build-root /home/ali/Documents/Code/rc-metastudio/build/qt6-verification
{"form": "/home/ali/Documents/Code/rc-metastudio/build/qt6-verification/generated/rc_metastudio/forms/ui_about_legal.py", "resource": "/home/ali/Documents/Code/rc-metastudio/build/qt6-verification/resources/icons.rcc"}
[03:33:24] Delegating Full R Stack Evidence
[03:33:24] $ /home/ali/Documents/Code/rc-metastudio/.venv/bin/python scripts/verify_rcmetar_r_stack.py --rscript /home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript --r-library-cache-root /home/ali/Documents/Code/rc-metastudio/artifacts/r-library-cache
[RCMetaR-r-stack] Locked rpy2 identities verified: {"rpy2": "3.6.7", "rpy2-rinterface": "3.6.6", "rpy2-robjects": "3.6.5"}
[RCMetaR-r-stack] /home/ali/Documents/Code/rc-metastudio/.venv/bin/python scripts/validate_rcmetar_r_manifests.py --root /home/ali/Documents/Code/rc-metastudio
validated RCMetaR R dependency and drift manifests
[RCMetaR-r-stack] /home/ali/Documents/Code/rc-metastudio/.venv/bin/python scripts/validate_rcmetar_r_manifests.py --root /home/ali/Documents/Code/rc-metastudio --report-installed-versions --rscript /home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript
[RCMetaR-r-stack] Manifest dependency versions are installed: {"packages": {"R": "4.6.1", "boot": "1.3-32", "grDevices": "4.6.1", "graphics": "4.6.1", "mada": "0.5.12", "meta": "8.5-0", "metafor": "5.0-1", "methods": "4.6.1", "png": "0.1-9", "roxygen2": "8.0.0", "rsvg": "2.7.0", "stats": "4.6.1", "svglite": "2.2.2", "testthat": "3.3.2", "tiff": "0.1-12", "utils": "4.6.1"}, "r_version": "4.6.1"}
[RCMetaR-r-stack] /home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript -e missing <- commandArgs(trailingOnly=TRUE)[!vapply(commandArgs(trailingOnly=TRUE), requireNamespace, logical(1), quietly=TRUE)]; if (length(missing)) stop(paste(missing, collapse=', ')) CompQuadForm Formula Hmisc MatrixModels RColorBrewer Rcpp RcppEigen S7 SparseM acepack ape cli colorspace data.table ellipse farver ggplot2 glue gridExtra gtable htmlTable htmltools htmlwidgets irlba isoband knitr labeling latticeExtra lifecycle mada magrittr meta metabook metafor mice minqa mixmeta mvmeta mvtnorm nloptr png quantreg rlang rmarkdown roxygen2 rsvg scales stringi stringr svglite testthat tiff vctrs viridis viridisLite withr xml2
Registered S3 method overwritten by 'ape':
  method    from   
  print.ace acepack
[RCMetaR-r-stack] Using cached R dependency library at /home/ali/Documents/Code/rc-metastudio/artifacts/r-library-cache/R-4.6.1-x86_64-source-rdeps-72fc3df2a5ba/library
[RCMetaR-r-stack] Using isolated R verification library at /tmp/RCMetaR-r-stack-zjiy25c2/library
[RCMetaR-r-stack] /home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/R CMD build --no-build-vignettes /home/ali/Documents/Code/rc-metastudio/r/RCMetaR
* checking for file ‘/home/ali/Documents/Code/rc-metastudio/r/RCMetaR/DESCRIPTION’ ... OK
* preparing ‘RCMetaR’:
* checking DESCRIPTION meta-information ... OK
* checking for LF line-endings in source and make files and shell scripts
* checking for empty or unneeded directories
Removed empty directory ‘RCMetaR/tests/testthat/_snaps’
* building ‘RCMetaR_0.4.2.tar.gz’

[RCMetaR-r-stack] /home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/R CMD check --no-manual --no-build-vignettes --library=/tmp/RCMetaR-r-stack-zjiy25c2/library /tmp/RCMetaR-r-stack-zjiy25c2/RCMetaR_0.4.2.tar.gz
* using log directory ‘/tmp/RCMetaR-r-stack-zjiy25c2/RCMetaR.Rcheck’
* using R version 4.6.1 (2026-06-24)
* using platform: x86_64-pc-linux-gnu
* R was compiled by
    gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
    GNU Fortran (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
* running under: Linux Mint 22.3
* using session charset: UTF-8
* current time: 2026-10-14 22:33:32 UTC
* using options ‘--no-manual --no-build-vignettes’
* checking for file ‘RCMetaR/DESCRIPTION’ ... OK
* checking extension type ... Package
* this is package ‘RCMetaR’ version ‘0.4.2’
* package encoding: UTF-8
* checking package namespace information ... OK
* checking package dependencies ... OK
* checking if this is a source package ... OK
* checking if there is a namespace ... OK
* checking for executable files ... OK
* checking for hidden files and directories ... OK
* checking for portable file names ... OK
* checking for sufficient/correct file permissions ... OK
* checking whether package ‘RCMetaR’ can be installed ... OK
* checking installed package size ... OK
* checking package directory ... OK
* checking DESCRIPTION meta-information ... OK
* checking top-level files ... OK
* checking for left-over files ... OK
* checking index information ... OK
* checking package subdirectories ... OK
* checking code files for non-ASCII characters ... WARNING
Found the following file with non-ASCII characters:
  R/forest_summary.R
Portable packages must use only ASCII characters in their R code and
NAMESPACE directives, except perhaps in comments.
Use \uxxxx escapes for other characters.
Function ‘tools::showNonASCIIfile’ can help in finding non-ASCII
characters in files.
* checking R files for syntax errors ... OK
* checking whether the package can be loaded ... OK
* checking whether the package can be loaded with stated dependencies ... OK
* checking whether the package can be unloaded cleanly ... OK
* checking whether the namespace can be loaded with stated dependencies ... OK
* checking whether the namespace can be unloaded cleanly ... OK
* checking loading without being on the library search path ... OK
* checking dependencies in R code ... OK
* checking S3 generic/method consistency ... OK
* checking replacement functions ... OK
* checking foreign function calls ... OK
* checking R code for possible problems ... OK
* checking Rd files ... OK
* checking Rd metadata ... OK
* checking Rd cross-references ... OK
* checking for missing documentation entries ... OK
* checking for code/documentation mismatches ... OK
* checking Rd \usage sections ... OK
* checking Rd contents ... OK
* checking for unstated dependencies in examples ... OK
* checking examples ... NONE
* checking for unstated dependencies in ‘tests’ ... OK
* checking tests ...
  Running ‘testthat.R’
 ERROR
Running the tests in ‘tests/testthat.R’ failed.
Last 13 lines of output:
  • identical(Sys.getenv("RCMETAR_RUN_VISUAL_QA"), "true") is not TRUE (1):
    'test-forest-visual-qa.R:2:3'
  
  ══ Failed tests ════════════════════════════════════════════════════════════════
  ── Failure ('test-forest-metafor-renderer.R:1445:3'): single-arm binary RevMan and BMJ styles use one-arm count columns and plain metric axes ──
  Expected `bmj.bundle$style_blocks$axis_label` to equal "Logit Proportion (probability scale)".
  Differences:
  `actual`:   "Proportion (probability scale)"      
  `expected`: "Logit Proportion (probability scale)"
  
  
  [ FAIL 1 | WARN 0 | SKIP 1 | PASS 1825 ]
  Error:
  ! Test failures.
  Execution halted
* DONE

Status: 1 ERROR, 1 WARNING
See
  ‘/tmp/RCMetaR-r-stack-zjiy25c2/RCMetaR.Rcheck/00check.log’
for details.

error: command failed with exit code 1: /home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/R CMD check --no-manual --no-build-vignettes --library=/tmp/RCMetaR-r-stack-zjiy25c2/library /tmp/RCMetaR-r-stack-zjiy25c2/RCMetaR_0.4.2.tar.gz
verification failed: command failed with exit code 1: /home/ali/Documents/Code/rc-metastudio/.venv/bin/python scripts/verify_rcmetar_r_stack.py --rscript /home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home/bin/Rscript --r-library-cache-root /home/ali/Documents/Code/rc-metastudio/artifacts/r-library-cache

```

The earlier detailed package failure block is retained verbatim in [R-PRESENTATION-FAILURES](R-PRESENTATION-FAILURES.txt).

Qualification limits: Linux source and controlled fixtures only. Native OS picker interaction, keyboard-only/screen-reader coverage, OS DPI, other platforms and release packaging remain unqualified. Opus acceptance and independent native re-audit are separate review steps.
