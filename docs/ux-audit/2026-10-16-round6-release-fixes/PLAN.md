# v0.5.0 release fixes — plan before implementation

## Windows golden classification and release completion (9caf474)

Reviewer decision permits only reviewed rounds 3–6 presentation changes to be
refreshed with `scripts/regenerate_golden_presentation.py`, using actual Windows
run 38843274727 outputs. Download and hash the original evidence; retain its
failure. Before changing the archive, classify all fourteen drifts in
WINDOWS-GOLDENS.md. For every plot, cite the corresponding Linux refresh commit,
render old Windows and new Windows bytes, personally inspect both and their diff,
and reject unexplained glyph, font, clipping or layout changes. Compare all three
report sections with the refreshed Linux text; Windows-only differences require
a product root-cause fix unless the new text is identical to the intended Linux
text. Numerical rows, tolerances, skips and exceptions remain frozen.

Proof decided before implementation: preserve the failing Windows capture,
commands and hashes; inspect all eleven image pairs; verify archive changes are
limited to classified presentation and SHA bindings; run strict goldens and the
415-field exact numerical comparison after any product change (and after refresh
as a consistency check). Record final state in HANDOFF before merging. Commit and
push small coherent changes immediately, fast-forward only; on failure wait 30
seconds and retry once, then stop. Require every final-head PR check before the
authorised squash merge. Fetch/prune afterward, prove origin/master and the final
branch head have identical trees and all three version sources say 0.5.0, leaving
the local branch checked out and clean. No tags, releases or settings changes.

Evidence prerequisite found before any refresh: the Windows workflow uploads
only desktop evidence, not the strict capture directory produced by the R-stack
runner. Add a separate always-upload artifact for that existing directory; retain
the desktop artifact layout and every verification command unchanged. Prove the
missing original paths with the downloaded inventory, validate the workflow, then
push and inspect the next actual Windows capture. No presentation classification
or refresh can be completed from comparison-log descriptions alone.

### Report character-loss proof before product changes

The original Windows desktop subgroup reports provide supplementary raw text:
each differs from the archive only by tau-squared becoming Latin t-squared. This
does not substitute for the pending strict capture. The shared report path uses
R `format()` and then `capture.output(print(...))`, both native-locale boundaries.
Before changing it, extend the existing installed-real-R/production-bridge summary
driver. Failure modes: Unicode titles, column headers, row labels and notes are
transliterated/escaped; native `format()` expands characters and breaks measured
column widths; whitespace, numbers or report block order changes; temporary
locale changes leak into later analyses. Under a deliberately non-Unicode C
locale, require exact text equality with the ordinary UTF-8 locale, Unicode
preservation and unchanged locale after rendering. Keep the existing print/S3
and actual-model summary assertions. Avoid a console roundtrip in application
text and keep the existing Linux report byte layout. Run the failing driver
before implementation, then re-drive it, strict goldens and all 415 exact fields.

### Diagnostic PNG missing-glyph defect, proof before repair

Actual strict capture from run 38848117604 (same production as 9caf474) confirms
the diagnostic DOR PNG renders U+2080 in H-subscript-zero as a missing-glyph box.
The full-resolution crop is retained; this plot must not be refreshed as-is.
The Windows SVG still contains the correct Unicode caption, but svglite declares
only the primary Arial family. The SVG-to-raster boundary needs an explicit usable
Unicode fallback, preserving ordinary font choice and caption text.

Before implementing, extend the existing real SVG normalization/export contract
to cover a Unicode null caption with a primary family, unchanged text and geometry,
explicit usable fallback and repeated normalization. Failure modes: no fallback
leaves the glyph missing; replacing the primary font changes ordinary typography;
duplicate fallbacks grow on repeat; Unicode/numbers or existing glyph paths are
altered; an unavailable Windows fallback silently passes qualification. Verify
the actual fallback's U+2080 coverage on Windows. Keep existing SVG caption
identity assertions. After repair, run the device contracts, strict goldens,
415-field equivalence, compare all eleven Linux PNGs before/after, native
diagnostic rendering/exports, and personally inspect the new actual Windows PNG.
Do not mutate the executable source during the in-progress fresh report-fix
profile; qualify this subsequent graphics boundary change separately and through
the final Windows full-R matrix.

Starting point: c37e427, ux/audit-improvements. Presentation only; pinned test-owned R 4.6.1. No numerical contract, statistical procedure, tolerance or exception changes. Each commit is pushed immediately, fast-forward only; a failed push waits 30 seconds and retries once, then work stops.

| Item | Failure modes to prevent | Proof decided before implementation |
| --- | --- | --- |
| R6-03 / R6-06 | Generated names lose characters after 80; distinct names collapse; measured wrapped text crosses device top, caption, rules or data; exports differ from display. | Extend existing real SVG header geometry checks with device-top/caption clearance and complete word identity. Run on current code and retain the failing assertion before implementation. Native long-name two-arm Default/RevMan/BMJ, including names differing after 80; inspect complete display and SVG/PDF/PNG/TIFF exports. Measure actual block height at rendered type size and reserve it. |
| R6-01 | Hidden unnamed arm removes the semantic raw-data header; custom name replaces rather than supplements it. | Native six-study PFT BMJ standard/subgroup, unnamed and custom arm; SVG Events / Total and correct counts/totals. |
| R6-02 | Short informational/decision dialogs open with hidden content despite available space; large minimums break small screens. | Native About and continuous/binary reconstruction prompts at ordinary scaling, inspect visible full question/options; bounded sizing and scrolling on smaller available geometry. |
| R6-04 | Fitted PLN journal ticks inherit logarithms of natural ticks or labels disagree with positions. | Native PLN RevMan/BMJ fitted-axis Edit/OK/reopen, SVG exact round displayed-scale values and positions; retain natural-axis behavior. Reuse existing round-tick helper. |
| R6-08 | Secondary exponentiated tables leak intrcpt while primary table says Intercept; copy/export differ. | Native bundled HR/IRR Dose regressions, six digits, Text/Tables/copy/export identity. Sweep secondary table naming; numerical equivalence unchanged. |
| R6-07 | Dedicated exponentiated diagnostic coefficient axes stay linear, lack the existing scale editor, or changing scale changes coefficients; beta/logit axes become logarithmic. | Native six-study Reitsma Dose regression: OR default log spacing with natural round labels, Edit linear/OK/reopen and rollback, beta/logit linear. Compare values and exports. |
| R6-05 | Extreme fixed-point raw data/estimates/intervals/totals/ticks collide or round a positive bound to zero; formatting changes editable data or ordinary output. | Native exact IRR stress calculator entry, Accept/save/reopen and analysis in journal styles; inspect scientific text and measured clearance, compare persisted inputs/public fit. Ordinary strict golden/numerical gates unchanged except reviewed report wording. |

## Sequence and acceptance

1. Commit/push this plan; retain baseline evidence and failing stronger assertions.
2. Small coherent implementation/proof commits, reinstalling current RCMetaR into the test-owned library before native driving. Delete obsolete assertions/assumptions.
3. Retain curated, personally inspected before/after screenshots and a contact sheet; logs in ignored raw/. CHANGES maps item → commits → evidence; TESTS records exact commands/exits and verbatim failures; COMMITS records pushes; REPRODUCE.sh runs the retained proofs.
4. Run exact 415-field numerical equivalence and strict golden gates. Use only the sanctioned presentation-refresh tool for reviewed report text if needed, never numerical contracts.
5. Once fixes and targeted drives pass, execute `.agents/skills/verify-rcms/scripts/verify_all.py --full --fresh`. Record evidence and any unproved scope honestly.
6. Correct CHANGELOG wording if needed; update HANDOFF with round six, re-audit and release-fix state only after proof. Finish clean and pushed; no PR or merge.

## CI fixes

PR #537 is the branch's first GitHub qualification. Starting at c62df31,
reproduce the changed-code gate against e64695b04b4772617a966c1c2d3d63507dff61a7
using the CI-owned stable baseline at 8b7796bcc840c3505c5fb0a1328cdd7682880e48.
Read all offending functions, simplify production code along existing seams,
and preserve behavior, numerical values, thresholds, baseline and exemptions.
A demonstrably incorrect measurement must be reported rather than worked around.

The Native Qt6 Vertical Slice fails during repository-wide strict typing, before
native execution. Retain its complete job log, reproduce all diagnostics locally,
and repair their causes without suppressions or excluding files. Inspect every
other check for additional actionable failures. Retry infrastructure-only failures
once; a repeated external failure blocks merge.

Proof decided before implementation: unchanged numerical outputs (all 415 original
fields exactly), strict golden gates, affected real native scenarios, strict typing,
unchanged code-health gate, and one final full fresh profile if production changes.
Retain commands, inputs, logs and results in CI evidence and append CHANGES, TESTS,
COMMITS and HANDOFF. Commit small changes and push every commit fast-forward;
a push failure waits 30 seconds and retries once, then stops. Squash merge only
when every required check passes on the latest head; preserve the branch and verify
identical remote trees and all three 0.5.0 version sources after fetch.

Additional completed CI jobs exposed two more causes before their repair:
- Remaining Surfaces clicked Add covariate with an empty required name. Retained
  Windows JSON proves accepted/default-enabled are false while Cancel passes.
  Prove empty input blocks acceptance, then enter a valid name and observe actual
  acceptance; retain all existing action/focus/geometry checks.
- Windows source verification's code-health subprocess fails decoding UTF-8 Git
  source through the Windows locale. `dataset_table_view.py` contains bytes
  undefined in cp1252. Reproduce with a cp1252 locale at the real Git boundary,
  then make Git text decoding explicitly UTF-8; preserve gate measurements/policy.
  Preserve subprocess stderr in future evidence-test failures.

The broader local source sweep (752 passed, eight platform skips, twelve failures)
found three stale driver contracts also reachable by Windows Core: active groups
still name tx A/tx B after the bundled sample was deliberately renamed; the
small-study fake model omits the now-required outcome subtype accessor; and the
second-choice radio test clicks the middle of a wide multiline widget instead
of its indicator. Preserve reversed selection/save/reopen, small-study assertions
and exact second-candidate counts; explicitly assert the radio selection before
Accept and drive a real indicator click. Repair these test inputs/gestures only.

Follow-up Windows logs confirm the stale model/arm setups and reveal two further
fixture differences: fractional-scale table geometry probes an empty start page
whose table is intentionally hidden; binary screen-bound testing patches a global
provider which native screen attachment replaces. Load the actual sample before
measuring its table, and pass synthetic geometry through the existing explicit
provider seam so the same bounds remain authoritative. Keep all size/DPR/visibility
assertions. Restore matching parent/child locale decoding in the code-health
process test; the added UTF-8 parent override mismatched Windows stdout (0xd7).

## CI fixes — lexer and reassessment

Reviewer authorisation supersedes the measurement-defect stop at 09c240b. Repair
only R custom-infix tokenisation; thresholds, weights, exemptions and gated metrics
stay fixed. Before editing the lexer, extend the existing code-health tests and
retain the failing run. Failure list: custom infix operators containing `||` or
`&&` must stay whole; `%%` is modulo; percent signs in strings/comments must not
start operators; backtick-quoted operator definitions must preserve real body
branches; a neighbouring real `||` must still count. Also prove `%in%`, `%o%`,
`%>%` and real `&&`, `if`, `for`, `while`, `switch` retain their intended counts.

Inspect baseline production and comparison. If recorded measurements are affected,
rerun the workflow's existing baseline command at exactly
8b7796bcc840c3505c5fb0a1328cdd7682880e48 with the corrected measuring code;
retain old/new evidence and explain every changed function and aggregate. Never
hand-edit baseline values or anchor them to this branch head.

Read all 23 previous refactors against c62df31 and corrected measurements. Keep
useful presentation/configuration/resource seams; undo metric-only R splits that
add indirection, in a new commit. Prove unchanged results with strict goldens,
415-field exact numerical equivalence, unchanged code-health gate, strict typing,
fast/GUI sweep, native arm-names/generic-effect continuations and one final
`verify_all.py --full --fresh`. Compare affected figure/report/setup/editor families
against actual c62df31 renders and personally inspect representative frames.

Record commands, outcomes, failures and artifact hashes; append CHANGES, TESTS,
COMMITS and HANDOFF. Commit small coherent changes and push immediately with the
existing 30-second/one-retry stop rule. Inspect every latest-head PR check, fix
root causes, retry infrastructure flakes once, and stop on external/policy blockers.
Only after all required checks pass, squash PR #537 with the authorised release
subject/body; preserve branch/tags/settings. Fetch and verify equal remote trees
and all three 0.5.0 version sources; leave ux/audit-improvements checked out.

### Additional latest-head CI failures, proof before repair

The 9de179b check snapshot adds two real stale developer-driver contracts. Native
Vertical Slice fails constructing AnalysisSetupDialog because its synthetic Model
lacks outcome identity; the same fixture also cannot supply the real snapshot for
Change settings, and its owner callback lacks the keyword delivered with typed
results. Replace that incomplete model with the actual bundled-project table
model. Keep explicit fake statistical operations and all lifecycle checks. Backend
failure now intentionally preserves configuration with an inline error: assert that
recoverable state and disposed progress, then cancel and prove complete teardown.

The packaged workflow times out capturing binary.random. Reproduce the actual
source hook with real Qt/R and a non-modal exception reporter before repair; inspect
its callback's acceptance of the current `change_settings` keyword. Preserve all
packaged numerical, locale, persistence and output comparisons and the 300-second
bound. No timeout increase, skipped assertion or validator weakening is authorised.

The new full retry is intentionally unqualified and stopped before changing its
input bytes. Run a single new final fresh profile after these genuine repairs;
the earlier terminal-SIGTERM attempt and this planned interruption stay explicit.
