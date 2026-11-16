# Desktop UI refresh

Agreed with the user on 2026-11-16:

- Keep one manuscript-formatted Text report with section navigation and model configuration; omit repeated supplementary tables.
- Remove Copy report and hover status hints; retain save confirmations and confidence-level control.
- Share one Export plot dialog between toolbar and context menu, with proportional dimensions, cm/in units and raster DPI.
- Use File, Edit, View and Analysis menus in Results.
- Add About RCMS with website, authors, license, versions and copyable debug information; remove Project site from Help.
- Cite uses the project's Zenodo citation, with copy and BibTeX, RIS and EndNote exports.
- Add project action icons and persistent System/Light/Dark appearance. Retain outcome keyboard shortcuts.

## Behavior to prove before implementation

Drive the real Qt/R application on Windows. Retain exact commands and artifacts.
Check report navigation, selection/copy, methods/results/configuration and retained unique tables;
both export entry points, cancellation, proportional sizing, decoded PDF/SVG and raster dimensions/DPI;
theme persistence and palette changes; citation clipboard and all three exported formats;
About links and debug clipboard; Help/Project menu alignment and keyboard outcome navigation.
Check small-window layout and record native screenshots. Run strict typing before all GUI qualification.

## Report wording and citations

The user requested the Statistical analyses were performed using RC MetaStudio
(version …; Research Consultancy) template on 2026-11-16. Versions and package
names come from the executed analysis; package names are italic in formatted
reports. RC MetaStudio's Zenodo citation is reference 1, including when a producer
has no method references. The software sentence leads Methods; package references
precede method references, with matching numbered markers in the text.
The application citation uses the existing all-versions DOI 10.5281/zenodo.23118556.
Zenodo metadata checked on 2026-11-16 identifies v0.5.5, published 2026-11-16,
with version DOI 10.5281/zenodo.24271687; the project DOI remains selected here.

## Copy review decisions

Opus reviewed the application copy and subsequent fixes; the findings are retained
in `ui-copy-audit-2026-11-16.md`, `ui-copy-review-2026-11-16.md`, and
`ui-copy-final-review-2026-11-16.md`. The approved product description is
“RC MetaStudio is open-source software for advanced meta-analysis.” Published
Zenodo titles and historical documentation retain their original wording.

Applied consistent validation, sentence-case titles, readable tooltips, native
file filters, singular/plural forms, CI notation, P headings, and scale-preserving
SE headings. Model configuration and report exports use the same content.
Subgroup wording follows the executed F or Q test; Overall is not called a
subgroup. Explanatory subgroup/leave-one-out strings are no longer citations.

The report suppresses a known supplementary summary table only when all its
quantities appear in the primary tables. Arbitrary tables remain because equal
numbers can describe distinct comparisons. Existing project arm names and
internal R result keys are preserved. Broad renaming of R result identities is
outside this editorial pass.

Bibliographic corrections were checked against the publisher's
[Harbord record](https://academic.oup.com/biostatistics/issue/8/2?browseBy=volume),
[Yusuf record](https://www.sciencedirect.com/science/article/abs/pii/S0033062085800037),
and [Deeks record](https://pubmed.ncbi.nlm.nih.gov/16085191/).
The installed `meta` citation was retained in verification artifacts; adding or
reorganizing the remaining methodological bibliography needs a separate accuracy
pass rather than speculative replacements.

## Dead-code cleanup

Removed the unreachable Add Study dialog and its form, manifest entry, native
inventory, and screenshot probes. Study creation remains in the table's blank
row. Removed the hidden main footer, unused import file label, and hidden plot
path/Browse controls; plot paths are plain internal state and export remains in
Results. Deleted the obsolete Results HTML formatter, hard-coded module demos,
unused edit/reorder helpers and workspace mutation helper, unused imports, and
20 unexported R wrappers/helpers with no production or registry caller.

Tests now exercise table paste and the current renderer functions. Qt virtual
methods, form-promoted widgets, explicit public re-exports, platform scripts,
project migration readers, and tested domain operations remain; a single textual
reference count is not proof that those are dead.

Verification artifacts live under `artifacts/verification/ui-refresh`. Strict Ty
uses the win32 target. The affected GUI rerun passed 110 checks and the affected
fast rerun passed 44; earlier full runs and interrupted matrices are retained
as failed/incomplete evidence, not qualification. Final native, R, and complete
desktop results will be recorded after they finish against stable inputs.

The full R testthat suite passed with `LC_ALL=English_United States.utf8`;
the earlier C-locale run failed on Unicode rendering and is retained separately.
The native UI refresh passed in
`artifacts/verification/rcms/20261116T141418Z-d61253c3-ui-refresh`.
The remaining native surface probe validated all ten live surfaces at 1.0 and
1.5 scale. The unreachable Add Study removal is commit `0b22d10e`; the R
wrapper cleanup is `6705aa67`. Opus's cleanup review is retained in
`dead-code-review-2026-11-16.md`; its stale driver reference and scalar path
normalization findings were fixed before the final desktop run.

The earlier complete run in
`artifacts/verification/rcms/20261116T141831Z-99e5633f-complete`
finished with 123 passed and 17 failed. Its display expectations and export-driver
selection issues were corrected without changing numerical oracles.

## Version 0.5.6 qualification

All transcripts below are under `artifacts/verification/ui-refresh/` on Windows,
using R 4.6.2 and the current-source, test-owned RCMetaR 0.5.6 installation.

- `typing-056.log`: repository-wide strict Ty, win32 target, passed; subsequent
  native and desktop launches also retained their own passing typing gates.
- `056-collection.log`: all 1,253 Python tests collected.
- `056-gui.log`: 399 passed.
- `056-fast-packaging.log`: 701 passed, 3 platform skips. The explicit reasons
  in `056-platform-skips.log` are POSIX process-group teardown, native macOS
  PyInstaller BUNDLE, and the staged macOS R runtime without X11.
- `056-r-bridge-complete-library.log`: all 10 real-R bridge tests passed with
  required-stack mode enabled. The combined test-owned library adds pkgload
  and its development dependencies without modifying the desktop runtime.
- `056-analysis-authorities-pinned.log` and `056-analysis-authorities.json`:
  103 independent public-package numerical comparisons passed. Both R_LIBS
  and R_LIBS_USER were pinned to prevent ambient user-package substitution.
- `056-native-ui.log`: the real native UI refresh passed in
  `artifacts/verification/rcms/20261116T145749Z-82f71e8b-ui-refresh`.
- `056-native-results.log`: native Results fixture/export checks passed.
- `056-native-surfaces.log`: all 10 remaining surfaces passed at 1.0 and 1.5 scale.

The stable-source complete desktop matrix is retained in
`artifacts/verification/rcms/20261116T145337Z-230c2d25-complete`.
The full R testthat rerun passed with visual QA enabled and no skipped tests
(`056-r-all-pinned-visual.log`). Four expected complete-case warnings report a
fixture's omitted study. The library search order selects current RCMetaR, then
the bundled pinned statistical packages, then user development tools only.
The 300-case visual manifest and all 300 PNG/SVG pairs are retained in
`artifacts/verification/ui-refresh/056-forest-visual-qa/rcmetar-forest-visual-qa-test`.

The first 0.5.6 desktop matrix finished with 138 passed and two stale
verification assumptions: About still expected its old title/menu label, and the
retained-table helper duplicated identical section/table titles. These checks
were updated to match the approved UI without changing numerical comparisons.
The final complete rerun is
`artifacts/verification/rcms/20261116T153227Z-5a72c28b-complete`;
it passed all 140 desktop scenarios in 2,208.91 seconds. The subsequent doctor
passed in `artifacts/verification/rcms/20261116T160925Z-03852dda-doctor`,
after another passing repository-wide win32 typing gate. The complete runner
exited zero. Across Python lanes, 1,250 tests passed and three platform-only
tests were skipped; all 1,253 collected tests are accounted for. The two repaired
scenarios, project-shell and project-round6-polish, passed in this final run. This is source qualification on Windows, not
qualification of a packaged release or other operating systems.
