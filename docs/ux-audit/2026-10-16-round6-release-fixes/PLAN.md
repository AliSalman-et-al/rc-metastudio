# v0.5.0 release fixes — plan before implementation

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
