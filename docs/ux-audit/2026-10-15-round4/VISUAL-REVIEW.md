# Round 4 — actual visual inspection, interrupted

> Historical draft retained from the interrupted session. The user successfully
> pushed `ca6815c`; origin was observed at that exact commit. `resume-bmj-binary`
> now passes natively at 3/6 digits, with 6-digit four-format exports. Fresh
> captures were inspected: pooled-label/totals and footer/tick clearance are
> correct. See REVIEW1-RESUME.json. Remaining review work and final aggregate
> qualification are still open; statements below describe the earlier session.

Curated frames are unmodified QScreen captures. The manifest/action bindings are
in SCREENSHOTS.json. The review is **incomplete**: these frames were inspected in
the current final evidence pass; other curated frames need inspection before
claiming complete visual qualification. Earlier edit-loop native inspections
caught and repaired zero residues, missing journal references, ignored SVG
paper clipping and calculator scroll dependence.

Inspected final-pass frames:

- report-before/report-after: both report and table (four frames). Pooled sentence,
  smaller model configuration heading, named calculation-scale table and explicit
  tested null are clear; displayed model table numbers agree before/after.
- twoarm-proportion: 3-digit RevMan and 6-digit default/RevMan/BMJ (four frames).
  Numeric columns and effect annotations clear; **BMJ wrapped pooled estimator
  touches raw totals and its test line reaches the first tick**. This triggered
  0f21212/ca6815c, a deliberate full-run interruption, and pending new captures.
- twoarm-mean: 6-digit RevMan/BMJ (two frames). Raw Mean/SD/N columns clear; BMJ
  footer reaches its endpoint tick. Same repair, still awaiting final qualification.
- generic-effect: 3-digit RevMan, 6-digit default/RevMan/BMJ (four frames), plus
  contextual calculator and CSV (two frames). Context labels and Estimate preview
  are correct. Pooled RevMan model/weight spacing warrants the extended collision
  check on fresh final source. Default figure needs scrolling for its footer.
- reg-coef: 6-digit RevMan/BMJ and contextual calculator (three frames). Fixture 2
  lower bound is printed 0.000000; correct coefficient axis/result label.
- pre-post, entered-binary, entered-continuous calculator-mode-layout (three
  frames). Primary estimate, CI, clear/accept/cancel actions visible. Inactive
  input layouts removed; arm names used. No scroll-dependent result controls.
- precision: OR/logit/linear bubble frames, tiny-effect frame and degenerate-axis
  footer (five frames). Compact linear ticks 0.2/0.4/0.6/0.8, clear left title gap,
  existing transformed round ticks, tiny scientific estimates and concise extreme
  Z statistic retained.
- historical continuous-calculator before frame (one frame). Demonstrates the
  old stacked/inactive input content and result inside the scroller.

This is 28 inspected curated frames. It does not establish that all 68 curated
frames are visually approved. BMJ fix ca6815c is not visually qualified. The
failed push stopped further curation and inspection. Before/after clinical fixture
pairs are illustrative, not a pixel-level comparison at identical scroll state.
Screen reader, keyboard-only operation, OS scaling, long-figure reading size,
standalone exposure context and release packages remain deferred.
