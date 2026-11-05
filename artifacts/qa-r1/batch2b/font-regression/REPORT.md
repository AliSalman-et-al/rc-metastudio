# SVG readability regression in #566

CI run 41961316301, jobs 127028722277 and 127028722270 measured the Gonzalez study name inside the real forest SVG, not a QLabel. The measurement includes SVG coordinate conversion, item scale and view scale. No pixel-sized QFont or pointSizeF=-1 caused this failure.

Before: `python scripts/verify_rcms.py results-window` reproduced 5.296294787 pt locally (before.log; raw evidence 20261105T034140Z-f4c0a7a3-results-window). Manual zoom multiplied the displayed absolute percentage by the existing fitted SVG item scale, effectively applying a ~59% fit twice. The new analyze helper's zoom-in/back check exposed that existing product bug and left subsequent scenarios in manual mode.

Fix: manual zoom normalizes SVG/raster item scale before applying the chosen view percentage, and resize preserves it. The zoom E2E now checks effective zoom against the displayed percentage and restores automatic mode afterward. Automatic SVG sizing clamps the smallest declared text to 9 pt and permits horizontal scrolling. Explicit Fit width opts out of that floor. This is a display-only scale; R source, SVG bytes, statistics, exports and numerical references are unchanged.

The unchanged `assert label_pt >= 9, label_pt` remains. The common UX/results scenario also checks study readability after increasing the application font by +6 pt. A retained font runner launches the entire real desktop/R scenario at explicit 9 or 15 pt; it only configures QApplication before the ordinary driver. Thus the 15 pt run exercises a fresh Results navigation layout, not just an enlarged existing widget.

Observed initial values: default app 9 pt -> study 9.340182688 pt; app 15 pt -> study 9.191489362 pt with horizontal scrolling (24 logical pixels in the retained large-font observation). The plot deliberately preserves a 9 pt floor, not the full app font size, per review direction.

The plot-toolbar scenario now explicitly invokes Fit width before asserting fitted plot width; manual 125% intentionally overflows. No readability assertion was relaxed.

Master including #568 (8d3609d2) was merged in b03f3b5b. No push occurs without that ancestry.

## Commands / environment

`source /home/ali/.t3/qa-env/ENV.sh && export PYTHONPATH=$PWD/src:$PWD`.
Strict typing: typing-final.log (win32 target, before GUI qualification).
Scenario commands: `python scripts/verify_rcms.py ux-improvements`; `python artifacts/qa-r1/batch2b/font-regression/drive_font.py results-window 9`; `python artifacts/qa-r1/batch2b/font-regression/drive_font.py ux-improvements 15`.
Each helper retains commands, runtime, inputs, screenshots and assertions under artifacts/verification/rcms; selected proof is copied beneath proof/. Intermediate failed runs are retained in this directory and raw evidence.

The 15 pt launch also checks +6 pt (21 pt) without matching that full size in SVG; study text remains above 9 pt. Full raw runs retain all other workflow screenshots and exported files.

## Qualification follow-through

The initial full pre-push found two existing no-text SVG resize checks restoring a width one scrollbar narrower than before. Both unchanged checks pass in resize-checks.log after preserving the width-only sizing path for plots without declared text. Text-size metadata is computed when the SVG renderer loads, so it refreshes after plot edits instead of retaining an old item's font measurement.

Merged master changed R plotting sources. To qualify the same source, installed current R with `"$RCMS_R_HOME/bin/R" CMD INSTALL -l "$PWD/build/rcmetar-lib" r/RCMetaR` (r-install.log), then ran final scenarios with `export RCMS_R_LIBS=$PWD/build/rcmetar-lib:$RCMS_R_LIBS; export R_LIBS=$RCMS_R_LIBS R_LIBS_USER=$RCMS_R_LIBS`. Final runtime.json records this test-owned library first. Source provenance is the merged HEAD r/RCMetaR Git tree; the Python follow-up does not edit R files.

Native dark/large real-display drive: `RCMS_QA_APP_SRC=$PWD .../ui.py --session b2b-font start --dark --large-font --size 1280x800`; Ctrl+O amino.rcms; Analysis > Meta-analysis > Run analysis. native-auto-floor.png shows automatic sizing with horizontal scrolling; native-explicit-fit.png follows a click on Fit width. The session was stopped. These captures preceded the renderer metadata/no-text cleanup; final-source E2E captures beneath proof/ establish the final measured state. No Windows execution or package qualification is claimed locally; those remain CI-owned.

Final-source qualification after renderer/no-text cleanup is in proof/final-ux, proof/final-results and proof/final-large. All passed against installed R source tree `2fc16662208bd4a7caa5ed702ff6b1b78c84804c`, with that test-owned library first in runtime.json. Final pre-push transcript is pre-push-final.log; original failed GUI transcript is pre-push.log. No assertions or numerical references were relaxed.

All final pre-push stages passed: strict typing, code health, fast/golden, GUI (364 passed, 1 skipped), packaging contracts (73 passed, 8 skipped). A later fetch found unrelated #569 on master; the requested #568 merge remains present. fresh-health.* records a final code-health comparison against that freshly fetched master without folding another unrelated feature PR into this fix. Local scenario/source proof remains bound to the branch containing #568.
