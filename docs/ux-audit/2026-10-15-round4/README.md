# Round 4 / Opus review 1 — implementation and proof

Implementation and qualification are complete on `ux/audit-improvements`, with
application source through `ff03295`. Every continuation commit was fast-forward
pushed; no PR or history rewrite. The user recovered the earlier `ca6815c` push.
STOP/INTERRUPTION receipts preserve that history.

Start with the [native before/after contact sheet](contact-sheet.html), then
[CHANGES](CHANGES.md) for each finding/design item and commit, [PLAN](PLAN.md) for
the pre-implementation choices, and [TESTS](TESTS.md) for exact commands, exits
and failures verbatim. [COMMITS](COMMITS.md) lists source and evidence commits.

The four review findings and D4-04..07 cover a native main-window start page,
clear dataset navigation, consistent native controls, a result-first report with
coherent sidebar/export behavior, and publication figure headers/ticks/footers.
There are no new statistical features.

Qualification: **108 fresh desktop scenarios plus doctor**;
R package `Status: OK`, retained statistical/rendering checks, independent
public-package authorities, live bridge and strict golden gates. **415 original
numerical fields exactly unchanged**, maximum difference 0. Only reviewed
presentation text was refreshed through the sanctioned tool; see
[the text review](REVIEW1-GOLDEN-TEXT.md). Original numerical fields, tolerances and
exceptions remain fixed. The retained GUI selection passed 186 checks with one
Linux platform skip; changed production Python files passed configured typing.

[FULL-PROFILE](FULL-PROFILE.json) verifies each expected scenario and every retained
artifact hash. [NUMERICAL-EQUIVALENCE](NUMERICAL-EQUIVALENCE.json) contains every
original field. [REVIEW1-NATIVE](REVIEW1-NATIVE.json) binds fresh xcb commands,
R 4.6.1 identities, manifest hashes, inputs, observations and unmodified captures.
[INSTALLED-SOURCE](INSTALLED-SOURCE.json) binds the exact source and test-owned R
library. Authority packages and system libraries were not modified.
[REVIEW1-EXPORTS](REVIEW1-EXPORTS.json) binds actual four-format publication bytes
and clearly marked derived previews. [VISUAL-REVIEW](VISUAL-REVIEW.md) identifies
frames actually inspected, including rejected development frames.

[REPRODUCE](REPRODUCE.sh) uses the pinned runtime, owned-library installer, actual
Qt/R driver and existing numerical oracle. Raw logs and complete desktop outputs
remain ignored under raw/ and artifacts/verification; curated receipts and
screenshots are committed.

Opus acceptance and the independent native re-audit are subsequent review steps.
Linux source/controlled-fixture proof does not qualify native OS pickers,
keyboard-only/screen-reader access, OS DPI, other platforms or release packaging.
Historical development screenshots are retained without claiming blanket visual
approval; final representative native inspection is recorded separately.
