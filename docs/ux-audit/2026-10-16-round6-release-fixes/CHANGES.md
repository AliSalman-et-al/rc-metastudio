# v0.5.0 release fixes — complete

All eight re-audit findings are fixed on the requested Linux source/native paths. The original release-fix qualification is **07c4f4a**. Subsequent PR #537 CI repairs and their final qualification are recorded below; the original evidence remains historical. Presentation only; no new statistical procedure or numerical contract changes.

| Item | Implementation commits | Accepted proof / evidence |
| --- | --- | --- |
| R6-01 | 443fdec; b069cc3 removes obsolete blank-header assumptions | presentation-1: six-study PFT BMJ, Group/Participants × standard/subgroup, semantic Events / Total plus custom spanner. Actual SVG/report/export checks and four inspected after frames. |
| R6-02 | 50afaa5 | presentation-1, back-continuous-1, back-binary-1: complete ordinary-screen About and decision content; small-screen-3: explicit synthetic 360×240 bounds and native scrolling/reachability. Nine inspected before/ordinary frames and six small-screen frames. |
| R6-03 | 443fdec | Stronger assertions failed before implementation. headers-fixed-3: measured physical header reservation, complete device/caption/rule checks in all styles. Six long-name native after frames and all 24 actual export renderings personally inspected. |
| R6-04 | 50afaa5 | pln-axes-1: round exact fitted PLN ticks in RevMan/BMJ, edit/reopen/Cancel, SVG positions and unchanged fitted fields/weights. All proportion transformations/styles also pass; two inspected after frames. |
| R6-05 | aba1f60 | stress-2: real keyboard source entry, undo/redo, save/reopen, public conversion/fit, journal column spacing and nonzero tiny fitted bound. Four inspected IRR after frames. Ordinary strict goldens unchanged. Raw matrices keep full precision for totals; only final presentation strings compact. |
| R6-06 | 443fdec, af9aa87 | Both Qt and R forest-label truncation removed. headers-fixed-3: complete 89-character name plus two names differing after character 80, Default/RevMan/BMJ and all exports. Caption excluded from heading word-identity assertion. |
| R6-07 | 1578d75, b069cc3 | coefficient-4: exact six-study Reitsma Dose input saved/reopened; both dedicated OR components, log default, visible scale chooser, linear/reopen/Cancel, exact unchanged arrays and eight decoded exports. Four inspected bottom frames show actual ticks. Beta/logit renderers remain linear. |
| R6-08 | 50afaa5 | presentation-1: bundled HR/IRR six-digit REML Dose regression, Intercept in Text/Tables/copy/CSV; exact shared surface rows and report export equality. Both after reports inspected. Secondary-table source sweep found no other intrcpt presentation branch. |

## Release gates

- Single `verify_all.py --full --fresh`: **PASS**, 2,978.019 seconds, 123 desktop scenarios plus doctor; current-source R package Status OK; nine live bridge checks; 91/91 independent authorities; strict goldens. FULL-PROFILE.json binds every child manifest and artifact.
- **415 original fields exactly identical, maximum difference zero**, checked again against this full run's capture. No golden presentation refresh, numerical contract, tolerance, exception or fixture change.
- Retained GUI checks: **90 passed, one platform skip**. Earlier stale assertions and all failed/incomplete attempts remain explicit in TESTS.md/OUTCOMES.json.
- **65 selected image frames personally inspected**; 24 actual long-header exports retained. CURATED.json and INSPECTIONS.md bind selection, bytes and acceptance. Raw logs stay ignored.

All changes are immediately fast-forward pushed. No PR, merge, tag, force push or history rewrite. Round six + independent re-audit + release fixes are complete; ready for the separate squash merge to master as v0.5.0.

No requested Linux repro remains unproved. This source/native qualification does not establish packaged Windows/macOS targets, actual OS DPI, screen readers, every native picker or an arbitrary name/value/parameter Cartesian product. Small-screen proof uses explicit synthetic available geometry, not an OS display-mode change.

## CI fixes

The Native Qt6 Vertical Slice stopped before native execution: its repository-wide
Windows typing gate found 44 diagnostics in recently added evidence drivers.
Use the existing typed QtTest seams (plus mouse-release), explicitly require XML
matches/table items and the concrete CSV page, and establish plot collections
before reading loop-derived values. No assertion is removed. Results smoke now
reads References from the result contract and validates the current Text report /
Tables / Forest Plot navigation rather than removed legacy scene text entries.

Changed-code complexity: split configuration context/restoration, diagnostic
request preparation and result identity; separate report section/table shaping
and numeric-cell formatting; isolate plot-axis setup; separate runtime/cgroup
collection and scenario timeout/reuse policy. The same operations remain in the
same order. Existing focused Qt checks: 131 passed, one Linux platform skip.

R presentation refactors separate manual bubble ticks, regeneration override
validation, continuous arm labels, forest marks/annotations/headers, Reitsma
appearance/axis/visibility settings, summary prediction intervals and subgroup
rows. Fit calls, transformations, operation order, output values and style-field
order are preserved. Strict goldens pass without refresh.

Remaining Surfaces now first requires blank-covariate acceptance to be disabled,
then enters a valid name before testing default-button acceptance. Local real-Qt
reproduction changed from `(false, false)` to `(true, true)` for enabled/accepted;
no validator was loosened. Git source/metadata decoding is explicitly UTF-8 in
code-health (no metric or policy change), resolving the reproduced cp1252 byte
0x9d decode error. The existing process contract now displays stderr on failure.

Core GUI qualification also retained stale pre-polish assumptions. The project
selection fixture now reverses the bundled Intervention/Control names, preserving
both save/reopen assertions; the small-study fake supplies the required subtype
accessor and expects the current expanded metric label; the second-count candidate
uses the radio indicator's real hit target and verifies selection before comparing
all six exact cells. Synthetic binary bounds use the existing explicit geometry
provider seam, while fractional-scale table proof opens the actual sample before
measuring its visible viewport. All visibility, DPR and geometry checks remain.
The code-health process test uses matching locale decoding for its child stdout;
UTF-8 is required at the Git-source boundary, not imposed on a locale-written pipe.

Implementation/merge stopped under the explicit mis-measurement rule: the R lexer
counts `||` inside `%||%` as a boolean branch. An equivalent operator alias changes
the metric, and the approved Reitsma function contains 29 affected operators.
The gate policy/measurement remains unchanged. Earlier R splits are pushed but
require reassessment; [CI-STOP](CI-STOP.md) supersedes any merge-readiness claim.

## CI fixes — lexer and reassessment

The R lexer now consumes a closed, same-line `%...%` operator before looking for
real boolean pairs. Strings, backticks and comments still take precedence. Four
lexer lines change; no policy/configuration/threshold/weight/exemption changes.
Twelve pre-implementation cases cover custom boolean-named infixes, modulo,
ordinary custom operators, quoted/comment contexts and adjacent real branches.

Baseline inspection: `.github/workflows/code-health.yml` regenerates the ignored
artifact with the measuring script at the fixed source head `8b7796b`; the stored
functions/derived totals contain inflated counts. Baseline comparison reports
stored aggregates; gate policy uses stored cycles/forbidden imports, while changed
function thresholds are independently computed. Re-ran the exact existing command
with both revisions fixed to `8b7796b`. [CI-BASELINE-AUDIT.json](CI-BASELINE-AUDIT.json)
and [baseline_audit.py](baseline_audit.py) prove 30 functions containing `%||%`
lose exactly 200 false branches, with only corresponding derived file
complexity/density/hotspot order and cognitive aggregates changing. All other
values are identical. Baseline remains generated evidence, not hand-edited source.

Read all 23 CI splits: [CI-REASSESSMENT](CI-REASSESSMENT.md) records each decision.
Keep 22 useful resource/configuration/presentation seams. Undo Reitsma's three
single-use style mappings: original corrected CC=8, not 37; the restored flat list
is easier to follow and that file is byte-identical to c62df31. Also remove extra
blank lines and correct extracted header-helper indentation. These are ordinary
new changes, not history rewriting. Reinstalled current RCMetaR into the pinned
private library; source/install hashes are in `raw/lexer/INSTALLED-SOURCE.json`.

Latest-head CI exposed two further stale qualification-driver contracts. Native
analysis smoke now constructs a real DatasetTableModel from bundled amino.rcms,
using the existing project adapter; it no longer invents a partial model missing
identity/state. Its owner accepts the actual typed-result callback keyword. On
backend failure it records the visible inline error, live configuration and
disposed progress, then cancels and retains every final teardown/leak assertion.
The validator now requires that recoverable state in addition to the original
Windows QPA, request, confidence, screenshot hash and four lifecycle checks.

The packaged analysis hook's result-capture lambda accepts `change_settings`,
matching actual delivery. The previous TypeError reached the global modal error
handler and explained Windows qualification's 300-second timeout. The capture now
completes through real Qt/R; timeout bounds and all package comparisons remain.


## Final release-completion qualification

The frozen 035ebd3 fresh profile passed, exit 0 in **3,164.487 seconds**: all
123 desktop scenarios, doctor, current-source R package Status OK, nine live
bridge checks, both 21-case Reitsma visual runs, strict goldens and 91 independent
authorities. The full capture preserves all 415 original numerical fields exactly.
The collector verified **124 child manifests / 9,469 retained artifacts**.
[CI-QUALIFICATION](CI-QUALIFICATION.json) indexes that original proof and every
retained command receipt without replacing the earlier FULL-PROFILE history.

Final qualification-only repairs address genuine Windows failures: observe the
proxy's actual native base style; recognize the established tau-glyph equivalence
in the release's reordered heterogeneity header; bind package presentation hashes
to exact approved c62df31 reports; write/read arm evidence as UTF-8; use a valid
long fixture path; wait for the actual queued Qt header refit under the same height
bound; group real SVG baselines directly within the original 0.1-point precision.
All endpoint, spacing, interval-projection, persistence and numerical assertions
remain. Full-R CI now uploads its original evidence on success or failure. See
[CI-PACKAGE](CI-PACKAGE.md) and [CI-WINDOWS](CI-WINDOWS.md) for pre-fix failures.

These changes alter qualification observation/identity and driver boundaries,
not fits, generated reports, figures, UI defaults or R source. Strict goldens and
all 415 exact fields were rerun afterward and pass. Source/GUI/packaging contracts
pass **891 tests**, with 16 existing opt-in/platform skips; Windows-target typing,
44 real SVG parser cases, three offscreen scaled source hooks and native xcb UX
pass. The original failed package/Windows runs remain failed. Actual final-head
GitHub qualification is required before the authorised squash merge. Automatic
remote head deletion is accepted; repository settings and local checkout stay.


### Windows offscreen font follow-up after 19b5fd9

The next Windows full-R run passed 122 cases and exposed missing Qt fonts in its
original PNGs; those images are rejected, not visual qualification. CI-FONTS.json
and CI-WINDOWS.md bind the actual artifact/transcript and personally inspected
frame. The recent-path ellipsis assertion stays; no speculative wait remains.
Verification children on Windows offscreen select existing WINDIR/Fonts, and every
doctor requires an actual font database plus Latin/tau/ellipsis glyphs, recording
resolved font identity. Font-directory selection/bytes enter the evidence context.
Child environment preparation is separated from process lifecycle. Failure
transcripts use UTF-8 child output and console-safe escaping; two failing console
cases were written before repair and pass afterward without changing log bytes.

Local follow-up: **893 passed / 16 existing skips**, strict Windows typing, strict
goldens and **415 exact fields, max difference zero**. The font-aware doctor and
original review1 workflow pass; the real-R fontless negative doctor fails at the
intended readiness assertion. Production UI, R source, fits, report/figure
production, numerical oracles, thresholds and bounds are unchanged. Every actual
final-head GitHub check is still required before squash merge.
