# Batch 6 evidence (Linux xcb, Qt/R)

**Read [body-fit/README.md](body-fit/README.md) for the corrected forest rule and current native evidence.** The screen-width exception described in the initial evidence below was rejected by CI and removed. The corrected rule preserves the 9pt study/body floor on all screens and fixes the annotation-size overshoot.

Base: origin/master 7ce97279b711232f01839acecbb0b4db513abb4c.

## Inputs and commands

Source `/home/ali/.t3/qa-env/ENV.sh`; override `PYTHONPATH=$PWD/src:$PWD`, `UV_PROJECT_ENVIRONMENT=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/.venv`, and `RCMS_QT6_BUILD_ROOT=$PWD/build/qt6-verification`.

- Generate: `uv run --no-sync python scripts/build_qt6.py generate --build-root $PWD/build/qt6-verification`.
- Install current R: `$RCMS_R_HOME/bin/R CMD INSTALL -l $PWD/build/rcmetar-lib r/RCMetaR`; prepend this library to RCMS_R_LIBS and R_LIBS.
- Typing: `uv run --no-sync python -c 'from scripts.verify import run_typing; from pathlib import Path; run_typing(Path("build/qt6-verification"))'`. Transcript includes full source selection, generated paths and win32 target.
- Qualification: `git fetch origin master`, then `uv run --no-sync python scripts/verify.py pre-push` (pre-push-pr-head.log).
- Desktop: `uv run --no-sync python scripts/verify_rcms.py SCENARIO`, for calculator-binary, plot-edit, analysis-diagnostic-joint and results-window. Each log identifies the full durable evidence directory with commands, inputs, runtime identity, screenshots and assertions.
- Independent participant proof: `python3 artifacts/qa-batch6/prove-participants.py`. Reads the sample ZIP/JSON directly, sums all four cells for 17 included studies, and compares complete baseline/current clinical reports and model-result text. See participants-proof.txt. Original run manifests retained. No numerical references changed.

## Native driver

Start using `RCMS_QA_APP_SRC=$PWD RCMS_QA_BUILD_ROOT=$PWD/build/qt6-verification RCMS_QA_R_LIB=$PWD/build/rcmetar-lib /home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session NAME start FLAGS`.

Sessions: batch6light with `--size 1600x1000`; batch6dark with `--dark --large-font --size 1024x700`. `drive.sh NAME COMMAND` wraps the exact ui.py invocation; outputs retained in commands.log. Both sessions stopped after capture.

Repeatable gestures:

1. Ctrl+O, type absolute `sample_projects/amino.rcms`, Return (click Open if native picker remains). Click first row calculator icon. Double-click Event 6, Ctrl+A, type abc, Tab. Capture `light-invalid.png` / `dark-invalid.png`: abc and other input counts retained, totals and effects blank, metric/Wald previews hidden, OK disabled. Valid calculator screenshots also show the metric grid without an internal vertical scrollbar.
2. Cancel calculator; Ctrl+O `sample_projects/continuous.rcms`. Analyses dropdown → Meta-analysis → Run analysis. Capture `light-forest.png` (previous 221% retained) and `dark-forest.png` (63%, names AND estimate/CI visible). Compact screens below 1280 logical pixels use width fit instead of the 9pt automatic floor; larger screens retain the prior rule. The boundary separates the observed 1024px failure from the unchanged 1600px default. Explicit Fit width remains available at every size.
3. Edit plot. Capture editor heading and estimate heading (`*-editor.png`); scroll to Forest options (`*-axis.png`): group-data wording. Enter abc in X-axis ticks and capture `*-tick-invalid.png`: immediate contrasting validation error. P-value notation unchanged.

Before evidence supplied with task: `/home/ali/.t3/qa-round4/council/shots/{09-invalid,48-cont-results,50-fit,51-editor,52-editor-axis,54-tick-invalid-typed}.png`.

Error foreground contrast (WCAG sRGB relative luminance): #b00020 on white 7.325:1, on #efefef 6.370:1; #ff9ca8 on #202020 8.203:1, on #2b2b2b 7.129:1. All exceed 4.5:1.

This proves Linux source behavior, not Windows/macOS native or installed-package qualification. Full R-stack/authority CI remains required. Existing frozen numerical references and tolerances are untouched.

Final qualification: pre-push-pr-head.log completed successfully. code-health-head.txt separately confirms the final product-source head against fresh origin/master. Artifact-only commits after qualification retain transcripts without changing executable source. Four final E2E receipts are committed under receipts/; their full hashed screenshot/export payloads remain in the original local evidence directories recorded in each manifest.
