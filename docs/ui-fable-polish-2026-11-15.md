# Fable UI/UX refinement

The authoritative whole-app brief is
[Fable's design direction](ui-design-direction-2026-11-15.md): a quiet instrument,
with paper-like data surfaces, native controls and one vocabulary. Its committed
directions are being implemented in batches; its seven experiments remain gated
by their stated prototype/observation criteria.

The aim is a coherent, polished and easy-to-use research application, with the
existing features exposed clearly. Fable's screenshot review is input to this
work, not proof that every suspected defect exists. Larger interaction changes
need a concrete proposal before implementation.

## Proof obligations before changes

- A real failed analysis must leave its error and Method controls readable.
  Revealing error details may grow the dialog within the owning screen; it must
  not cover or cut off Advanced. Retain collapsed and expanded captures.
- Switching continuous calculator input modes must size visible content to the
  available screen and start pre/post inputs at the first arm. Capture before
  the driver scrolls, then prove both arms remain reachable on smaller screens.
- About must keep the wordmark readable without a white panel in dark mode,
  including a live theme change. Retain both themes.
- An executed Reitsma result must preserve the proper name in its title.
  Continuity-correction prose must use sentence-ready policy descriptions and
  retain the actual correction meaning.
- HR/IRR editable source values must retain their full accepted precision.
  Do not round source fields merely to make them shorter. Existing precision,
  save/reopen and public-reference comparisons remain authoritative.
- Report table layout must retain every row and quantity. Verify suspected
  regression omissions and alignment against executed objects before changing
  them. Check editable Word and rendered paper, not XML alone.

Use real Qt/R E2E observations and retained before/after evidence. Run strict
Windows typing before GUI qualification. Stop editing executable inputs before
the final matrix. Interrupted earlier matrices do not qualify v0.5.5.

## First concrete corrections

The native `ui-fable-polish` drive reproduced About's white panel, both pre/post
arm visibility failures, clipped Method controls with collapsed/expanded errors,
and the Reitsma title/correction wording. Failed evidence is retained at
`artifacts/verification/rcms/20261115T163307Z-b3e7eb35-ui-fable-polish/`.

The corrected drive passed at
`artifacts/verification/rcms/20261115T163524Z-24505332-ui-fable-polish/`:
pre/post opens at scroll position zero with both tables visible; error disclosure
grows within the screen; About renders a transparent monochrome wordmark on dark
backgrounds; executed titles retain Reitsma and policy text fits a sentence.
Strict win32 typing preceded each run. The installed test-owned RCMetaR library
was rebuilt at 0.5.5. These are Windows native source checks, not release-package
or other-platform qualification.

The existing dialog behavior suite passed 88 checks after updating its obsolete
assumption that an explicit pre/post mode change must retain summary-mode height.
Edits after the mode change still preserve settled geometry. Both transcripts
are retained under `artifacts/verification/ui-fable-2026-11-15/`.

HR/IRR source-field precision remains unchanged: the proposed six-significant-
digit rounding would lose original scientific input. The pre/post screenshot's
intentional scroll did not prove an initial defect, but a fresh native run did
confirm that mode changes were not requesting a content refit.

## Consistency sweep

Project terminology now follows the domain glossary in the menu and welcome
page. Outcome placeholders use concrete examples for each data family. Setup
and SROC labels use the same no-trailing-colon convention.

The native A/B/D/E/S tour passed with 188 recorded steps in
`artifacts/verification/rcms/20261115T164415Z-69e6d2de-ui-crawl/`, covering the
shell, outcome wizard/management, all calculator families and analysis/error
dialogs in both themes. The earlier attempt exposed a native focus-settling
race in the capture driver; it now waits for native activation before checking
the focused outcome editor. The original focus assertions remain intact.
The corrected wizard/setup/editor suite passed all 66 existing checks.

### Review findings requiring qualification

- `report-observations.json` under the Fable artifact directory confirms that
  regression df and residual I² are present in the complete editable DOCX.
  They continue beyond the first page. Mixed text/numeric Value-column
  alignment is a separate confirmed presentation issue.
- Whole-chart fitting and result-specific titles already exist. Earlier
  post-Fit-width captures and missing window decorations do not prove broken
  defaults. Verify initial-state behavior before changing it.
- Empty outcome validation is already quiet before an attempted submission;
  focus colouring from the operating system must not be treated as an error.
- Keep the Text report, full plot settings, source-input precision and current
  dialog archetypes. Larger reorganisations remain design proposals.

## Whole-app direction implementation

The new `ui-design-direction` drive was written before these changes. The native
baseline at `20261115T170614Z-2dc58343-ui-design-direction` reproduced thirteen
interaction/presentation failures, including an accepted-double change after a
ratio/log round trip. Earlier attempts retained their typing/utility failures;
none is a qualification pass.

### Copy and wizard guidance

Finished the remaining code-side labels, small-dialog arm terminology, Study name
display header, calculator readout separators, manuscript capitalisation and
numeral-initial sentences. Copy/save messages now expire after four seconds.
Links use a readable light-theme blue and retain the existing readable dark blue
while following live theme changes. No scientific values were reformatted.

Metric pages explain the selected measure and list alternatives. The final
outcome page shows only its applicable forward action. The importer still
constructs `MainWizard(path=None)` and dispatches the selected file before
showing it; welcome-page removal remains a separately gated simplification.

Strict win32 typing and 66 existing wizard/setup/editor checks passed. Native
B/D/E captures passed 104 steps in
`artifacts/verification/rcms/20261115T171146Z-a0ba6fa5-ui-crawl/`, including both
themes, all calculator families, setup and error states.

### Shell and Home

The analysis button is now a split control: one-click meta-analysis, with other
analyses in its menu. Ctrl+R, visible previous/next outcome commands and scoped
F2 outcome renaming improve keyboard discoverability without taking F2 from
spreadsheet cell editing. Project and Help expose outcome management and the
repository's actual citation file. Home uses flat card frames, removes redundant
Available labels, and offers an import action in the empty recent-project list.

The first native menu capture caught a delayed application-palette update closing
menus. Link-colour refresh now stays on the relevant controls after initial app
configuration. Its failed evidence remains retained. The corrected native shell
tour passed at `20261115T171929Z-1e33c90c-ui-crawl`; strict typing and 73 existing
GUI checks passed. Final frozen qualification remains pending.

### Numbers and report layout

HR/IRR scale switching caches exact field text, invalidates a stale opposite-scale
draft after an edit, and provides a separate conversion preview. Full source
precision remains authoritative. Small table effects retain significant trailing
zeroes instead of stripping them from the fixed-format branch.

HTML, Word and the Results table now share numeric-cell detection and header
alignment. Detection matches the whole value, so labels beginning with `95%`
stay left-aligned. Mixed numeric/text columns align each cell appropriately.
Word uses measured content proportions, nonbreaking interval spaces, the PDF's
Arial family and headers kept with their first data row. A retained first Word
render exposed the previous serif fallback and orphan header; corrected page
renders are `number-layout-word-final-1.png` and `-2.png` in the Fable bundle.

The focused real Qt/R numeric phase passed at
`20261115T173053Z-4ea2a50a-ui-design-direction`, including exact input round trips,
the accepted double, subgroup output and complete report retention. An earlier
observer rejected intentional nonbreaking whitespace; it now normalizes only
that layout character, preserving all digits and punctuation. The original
failed output is retained. The existing GUI/quantity suite passed 78 checks.
No statistical oracle or tolerance changed.

### Results workspace and zoom

Results now has one icon toolbar with grouped copy/export, edit/settings and zoom
actions. Figures lead the resizable navigation pane. The executed analysis
identity stays above the content stack when scrolling or zooming. Fit page
(Ctrl+0), Fit width (Ctrl+Shift+0), edit and zoom keys are discoverable; automatic
forest scaling caps at 100% before the existing readable-text floor.

Strict win32 typing passed (`typing/20261115T224359-e64e8d74`). The focused GUI
suite passed 134 checks. The complete native `ui-design-direction` drive passed
at `rcms/20261115T174400Z-2f93304b-ui-design-direction`, including actual keyboard
analysis, Fit page and plot editing, ratio round trips, status expiry and report
number retention. Visually inspected `12-0-direction-results-first-display.png`: 
all plot labels fit at 100%, with fixed context and the grouped toolbar visible.
Final frozen qualification remains pending.

### Dialog content sizing and calculator fields

Interval edits now share the Estimate field column with equally sized lower and
upper fields separated by “to”. Accessible limit names remain explicit.
Continuous arm headings are bold and upright; correlation is ten em wide.
Diagnostic reconstruction has an explanatory tooltip. Error details own an
eight-line viewport. Forest-only setup names its plot tab “Forest plot”.

Regression's initial empty space was reproduced in the native C/D/E tour
`20261115T175650Z-ec7b70e4-ui-crawl`. QTabWidget includes hidden-page hints despite
Ignored policies. The existing fit path now measures the active layout and
permits explicit refits to shrink. Method and parameter rows share label widths
and insets. Small-study setup accounts for scroll-content height and describes
automatically selected tests using the producer's eligibility/input metadata;
it adds no statistical selection rules. Covariate conversion prefers eight
rows within the screen policy. RevMan review right-aligns study counts and
separates bold headings from unchanged explanatory text.

The preimplementation native baseline reproduced six presentation failures.
Intermediate runs retained a diagnostic-layout call-site failure and a
preinitialisation timer failure; both were fixed and re-driven. Final strict
win32 typing and native `ui-fable-polish` passed at
`20261115T180331Z-b8cb6f35-ui-fable-polish`, including compact regression, exact
field alignment, error disclosure and actual Reitsma output. The focused GUI
suite passed 146 checks (`direction-dialogs-columns-gui.log`). The earlier C/D/E
tour proves both-theme import, calculator and small-study rendering; its old
regression capture is superseded by the compact regression drive.

### Outcome strip, Results tables and plot editors

Sheet confidence now sits beside Add outcome. Outcome tabs allow up to 28 em
when space permits and use a 12 em cap during overflow; custom tab navigation
and the grid's shared horizontal scrollbar remain separate controls. Results
tables retain aligned bold headings and alternating rows, with cell boxes
removed and a palette-based header rule. The selector keeps its content width.
Colour fields in forest, funnel and SROC editors are bounded to six em and
picker buttons use “Choose…”. Existing disabled funnel-setting explanations
already name the enabling plot kind. A cosmetic palette-Mid outline marks
preview paper without changing exported artifacts. The progress dialog already
has an indeterminate bar; no duplicate progress control was added.

The preimplementation drive reproduced four failures. Strict win32 typing,
146 focused GUI checks and native `ui-design-direction` now pass at
`20261115T180649Z-f1818136-ui-design-direction`. The long outcome label, confidence
control, Results table and compact plot-editor controls are captured there.
Native overflow/grid-scroll behavior remains part of final shell qualification.

All eight committed design batches are implemented. E1–E7 remain explicitly
gated experiments; no opinion-only change to forest label colours, docking,
statistical output, caption removal or coefficient height was adopted.
Final qualification and external design review are pending.

### User feedback: logo clarity and confidence placement

The user overrode the brief's proposed CI placement after seeing it: the control
is restored to the far right of the status bar, with its visible button styling
and explanation retained. The outcome strip keeps its independent grid scrollbar
and adaptive tab widths. Native `ui-design-direction` passed at
`20261115T182810Z-fa591119-ui-design-direction` with the updated placement check.

The About artwork is a 4096-pixel source with a 3586×418 visible wordmark. Qt's
rich-text fast reduction made its edges jagged. The resource is now smoothly
reduced to the current screen's physical pixel width before text rendering,
records its device-pixel ratio and retains its natural aspect ratio. It refreshes
on pixel-density changes as well as theme changes. No original artwork changed.
Both themes were captured at scale factors 1, 1.25 and 2 (observed physical DPRs
1.25, 1.5625 and 2.5 on this host) under
`artifacts/verification/about-logo-2026-11-15/qualified-before` and
`qualified-after`. The baseline loads the exact ba99c3db About implementation.
The probe retains the command, environment, Qt platform, script hash and resource
sizes. Earlier probe attempts lacked resource registration/application ordering;
only the qualified captures establish the visual comparison. Strict typing and
five compact-dialog layout checks passed. The probe is `build/about_logo_probe.py`.
