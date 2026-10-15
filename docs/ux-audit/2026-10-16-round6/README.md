# Round six — accepted reviewer fixes and 0.5.0

The six requested reviewer fixes are implemented on `ux/audit-improvements`.
Executable/test source is frozen at **06df415**; later commits retain evidence and
documentation. Every commit was immediately pushed fast-forward; no PR, force push
or history rewrite. [COMMITS](COMMITS.md) lists the implementation and proof work.

PFT prediction intervals now use proportions through the same harmonic-mean inverse
as the pooled estimate, including subgroup-specific inference. Missing/invalid-size
contexts retain an explicit transformed-scale explanation. Six independent public
meta/metafor comparisons agree to less than 1e-12:
[REVIEWER-PFT-AUTHORITIES](REVIEWER-PFT-AUTHORITIES.json). The FT-zero test remains
explicitly transformed; it is not described as a test of proportion zero.

Unnamed single-arm Group spanners are hidden and meaningful names remain.
Diagnostic coefficients distinguish logit estimates/intervals from odds ratios.
Default forest marks/intervals/caps/arrows use the shared blue accent with black
study text; journal colours remain unchanged. The visible style name is Default,
while the persisted `default` key remains compatible. Python/R/package metadata,
About and newly saved project manifests report **0.5.0**; the changelog is dated
**2026-10-15**. A native legacy 0.4.2 project/paired settings load, new project save
and reopen are retained. The installed-source proof is refreshed for RCMetaR 0.5.0.

Actual screenshot inspection also exposed a Tables-to-figure navigation defect.
It was reproduced with a failing native assertion before 06df415 fixed the page
selection; the complete 18-case prediction replay then passed. Earlier exit-zero
runs with the wrong content page or a hidden picker remain visually rejected.

The final **`verify_all.py --full --fresh` passed**, exit 0 in **3,484.665 seconds**:
**122 desktop scenarios plus doctor**, R CMD check **1,825 passes**, zero failures/
warnings and one opt-in gallery skip, both **21-case Reitsma lanes**, **nine live
bridge checks**, strict goldens and **91 independent authorities**. The original
**415 fields are exact, maximum difference 0**, including the final full-profile
capture. No baseline refresh was needed for the reviewer fixes.

[FULL-PROFILE](FULL-PROFILE.json) binds **123 receipts / 9,224 artifacts** to the
final executable source. [EVIDENCE-INTEGRITY](EVIDENCE-INTEGRITY.json) verifies
source/install bytes, profile logs, helper/curated hashes, the original numerical
contracts and the actual [saved 0.5.0 project](release-0.5.0.rcms), bound to the
fresh save/reopen step by [RELEASE-PROJECT](RELEASE-PROJECT.json).

[PLAN](PLAN.md) records failure modes/proof before implementation.
[CHANGES](CHANGES.md) maps the fixes; [TESTS](TESTS.md) and
[REVIEWER-TEST-RUNS](REVIEWER-TEST-RUNS.json) retain commands/exits.
[REVIEWER-FAILURES](REVIEWER-FAILURES.md) preserves nonzero attempts verbatim;
[REVIEWER-VISUAL-REJECTIONS](REVIEWER-VISUAL-REJECTIONS.json) separately records
visually rejected exit-zero evidence. Reproduce with
[REVIEWER-REPRODUCE.sh](REVIEWER-REPRODUCE.sh). Earlier round-six qualification is
preserved historically through [REVIEWER-BEFORE](REVIEWER-BEFORE.json), not promoted
to proof of the reviewer changes.

The [reviewer contact sheet](reviewer-contact-sheet.html) has **35 entries / 51
original native PNGs**, appended to the existing [contact sheet](contact-sheet.html).
[REVIEWER-VISUAL](REVIEWER-VISUAL.md) states the images personally inspected and the
scope of the 28 additional QtSvg lower-device crops. There are **35 selected passing
native workflows**; each retains its actual revision/runtime. Targeted native checks
cover all three PFT/logit/arcsine styles, sequential/subgroup PIs, single-arm
proportion/mean, both diagnostic coefficient tables and precision levels, Default
colour families/clipped arrows, 40 decoded four-format exports, and release surfaces.

The original 70 curated frames, commands and failed/interrupted attempts remain
historical evidence. Raw/helper files are ignored but retained locally with paths
and hashes. Original numerical contracts/tolerances/fixtures remain unchanged.
Seven earlier-round reviewed text headings were refreshed only through the
sanctioned presentation tool; reviewer fixes required no further refresh.

Linux source/native Qt and the pinned test-owned **R 4.6.1** runtime are exercised.
Windows/macOS installers/packages, actual OS DPI, screen readers, native OS file
pickers and every possible parameter/value combination remain unqualified. The
single-arm rate family is not offered; the supported two-arm IRR path was checked.
Mean entered-effect forests do not expose raw-data spanners, so custom mean identity
is proved in the caption. No cross-platform release build is claimed.
