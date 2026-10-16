# Opus review 1 — implementation and proof map

Source commits are fast-forward pushed; no PR. Final aggregate qualification passed: 108 fresh desktop scenarios, doctor, current-source R gates, independent authorities and strict goldens. All 415 original numerical fields remain exact. Earlier round-four
receipts and interrupted drafts remain historical evidence, including the user's
successful recovery push of `ca6815c`.

| Finding / design item | Change and commits | Native / independent proof |
| --- | --- | --- |
| 1: BMJ binary collisions | `ca6815c` measured pooled-label and footer clearance; `2e645c5` shortens conventional overall tests. All three reported collisions clear at 3/6 digits. | `REVIEW1-RESUME.json`, `review1-publication-audit-round3-presentation-twoarm-proportion` and final binary receipt in `REVIEW1-NATIVE.json`; SVG geometry and PDF/PNG/TIFF/SVG decode at both precisions. |
| 2: Diagnostic header/ticks | `2e645c5` uses measured header baselines and top clearance, suppresses the duplicate metafor separator, and separates tick/title baselines. Round display ticks are transformed to plot coordinates in all styles. | `review1-publication-audit-round3-presentation-diagnostic`; three styles, Sens/Spec, 3/6 digits and four exports. PLN/PLO/PAS/PFT receive separate native/public-package proof. |
| 3: Heavy F05 wording | `2e645c5` uses the conventional overall-test heading for OR/RR/RD/HR/IRR/MD/SMD and other comparative binary measures. Ambiguous single-arm, diagnostic, entered-effect and coefficient tests name a concise H₀; the same producer heading serves figures and report tables. Removed the duplicate null note and bridge append. | Native binary/MD/SMD/diagnostic/proportion/entered/coefficient families; three reviewed golden text changes in `REVIEW1-GOLDEN-TEXT.md`. |
| 4: Confidence/inference polish | `8f48f47` prints `95% confidence interval` / `Confidence level: 95%`, retaining fractional levels. Actual inference appears in Model configuration; the duplicate legacy section is removed. | Native calculators, start page/status and result reports; report copy/export and native GUI boundary checks. |
| D4-04: Main start page | `8f48f47` replaces the blank grid and action strip with a scrollable native page, Create / Import CSV / Open, full-path recents with disabled missing files, and a short three-step orientation. No welcome modal. | `review1-reading-qualified`: pristine and normal-size startup, full/missing paths, wizard/picker Cancel, recent opening, and native light/dark palettes. Dataset matrix plus shell/structure/CSV supply successful create/save/reopen/undo. |
| D4-05: Results reading/export | `8f48f47` leads with result/heterogeneity/test/PI, moves configuration/calculation details later, moderates heading size, and preserves numeric table alignment. Sidebar opens report, tables and configuration directly. Existing settings remember the export format across navigation and a fresh analysis. | `review1-reading-qualified`, `review1-ux-gestures` and `review1-bounded-review-workflows`: report/table copy and export, zoom, setup Cancel, rerun from the captured dataset, and remembered SVG. |
| D4-06: Native controls/navigation | `8f48f47` adds one small native proxy style for button height and consistent stock dialog icons. Primary toolbar actions have text beside icons; other actions retain tooltips. A labeled outcome/follow-up/group selector with Previous / Next / Add replaces the compass. | Main/start light and dark captures; native calculator/setup/structure drives and actual dimension switching, undo/save/reopen. No theme or navigation framework. |
| D4-07: Publication finishing | `2e645c5` covers shared leading, round transformed ticks, concise tests and heterogeneity → overall test → subgroup differences → PI footer order. PFT journal displays now receive actual sample sizes. `bc1e057` preserves sparse pooled-label/weight padding; `cab0d7a` bounds default null guides to study rows. `4eb4217` names the clinical Proportion beside back-transformed values, preserves the actual fitted null, adds PLN public-reference proof and clears its wider endpoint tick. Three effect decimals remain the default; existing direction fields persist. `46c2364` records the visible subgroup footer as well as its SVG order. | PLN/PLO/PAS/PFT study and pooled intervals independently match public metafor fits/conversions at three decimals in all three styles; all affected native families at 3/6 digits and four exports; real forest editor applies/reopens direction labels. |

The before/after contact sheet is `contact-sheet.html`, self-contained with the
original native PNG bytes. `make_contact_sheet.py` reproduces it from bound
receipts. `collect_review1.py` checks the native platform, sealed manifest and
all artifact hashes before adding a receipt. Individual captures and exact
commands are indexed in `REVIEW1-NATIVE.json`; visual inspection is recorded in
VISUAL-REVIEW, separately from automated geometry checks.

References compared: RevMan's [analysis reporting](https://documentation.cochrane.org/revman-kb/report-analysis-results-142314014.html)
and [DTA graph settings](https://documentation.cochrane.org/revman-kb/analysis-graphs-in-dta-reviews-236847627.html),
and metafor's [forest API and examples](https://wviechtb.github.io/metafor/reference/forest.rma.html).
Adopted aligned study/estimate columns, an explicit pooled diamond, compact
conventional test wording, deliberate header leading and separated direction
labels. Retained calculation-scale geometry with display-scale labels and the
same publication layout in the app and exports. This is a reference comparison,
not qualification of a separate RevMan installation.

No new statistical feature or fitted quantity was introduced. The PFT repair is
an existing display conversion through the pinned public package; its pooled
conversion uses the harmonic sample size and its PI retains the explicit
Freeman–Tukey scale because no new-study sample size is specified.

Unfinished by scope: independent Opus acceptance and the final low-effort native
re-audit; native OS file-picker operation, keyboard-only/screen-reader and OS-DPI
qualification; other platforms and release packaging. No claim is made for all
option combinations or filesystem failures. No new persistence framework,
clinical verdict, inferred favours direction or statistical capability was added.

`c043296` repairs native verification timing: wait up to five seconds for the exact restored size, mark the deliberately opened unsaved prompt as expected before taking its screenshot, and let wizard compositor transitions settle. The data-retention and geometry assertions remain.

`8ef7468` synchronizes actual Text report / Tables toolbar gestures with the sidebar, restores the selected plot on return, and disables plot actions while reading Tables. The extended real Qt/R drive reproduces the stale selection before the repair and proves report → tables → plot → report → same plot afterward. `8c8e8a3` changes only the R source encoding of the Freeman–Tukey dash, preserving rendered text while clearing the package portability check. `87724ef` aligns the last old BMJ probability-axis assertion and asserts fully visible validation actions after the native resize.

The fresh reference sweep exposed an overbroad new table assertion: the diagnostic producer does not publish the top-level weight vector used by the binary/continuous Study weights table. The corrected driver limits that table contract to those two producers, retaining all independent diagnostic heterogeneity comparisons. No diagnostic report quantity or fitted calculation was added. REVIEW1-MATRIX-FAILURE.json and REVIEW1-MATRIX-FAILURES.txt retain the exact failing trigger and scoped cleanup; final TESTS records the corrected sweep and fresh aggregate.

`febd7d6` completes clinical startup navigation and suppresses a table caption when its section already supplies the same heading, consistently in HTML, copied/exported text and the table selector. The real driver now asserts result-first ordering for joint/combined diagnostic reports, snapshots LR/DOR settings before the setup dialog is deleted, and restores sidebar selection after native screenshot instrumentation. `8151a7b` scopes the existing study-weights table contract to binary/continuous producers. Corrected reference sweep and native joint/combined/multiple-moderator/report workflows pass; no fitted quantities or package algorithms changed.

`370a3ac` corrects the UX driver to use actual Text report toolbar gestures and select the plot before reading its artifact. Both native and offscreen runs pass; this changes verification only. The failed full-matrix child and owned cleanup are retained in REVIEW1-UX-DRIVER-FAILURE.json / REVIEW1-UX-DRIVER-FAILURES.txt.

`ff03295` fixes a real coefficient-editor regression found by the final fresh
matrix: automatic-tooltip lookup now respects the existing Reitsma coefficient
renderer instead of invoking the ordinary metafor forest planner on its saved
bundle. Both native and offscreen coefficient editing, Cancel/reopen and four
exports pass. The same matrix exposed an overbroad calculator assertion; the
driver now proves single-arm Back-calculate is intentionally hidden while all
applicable controls remain fully visible at both scroll extremes. Both one-arm
calculator modes pass natively/offscreen with independent preview, persistence
and post-reopen analysis. The completed `3 failed, 105 passed` attempt, native
reproduction and corrected preflights are bound by REVIEW1-QUALIFICATION-FAILURES.
