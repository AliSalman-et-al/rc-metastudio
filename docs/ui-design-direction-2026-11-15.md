# RC MetaStudio whole-app design directions (Fable 5.2, design lead)

Date: 15 November 2026. Branch `ui/desktop-polish-and-icons`. Source read at HEAD
`58ba8fe9` plus the parent's in-flight label sweep (now `2378636a`, labels,
terminology and placeholders only). Read-only: no launches, no edits, no tests.
This document is the authoritative design brief for the app. It supersedes the
stylistic parts of [fable-review.md](../artifacts/verification/ui-fable-2026-11-15/fable-review.md) and
[fable-polished-experience.md](../artifacts/verification/ui-fable-2026-11-15/fable-polished-experience.md) where they differ;
their defect tables stay valid except where "Corrections" below says otherwise.

Line numbers refer to HEAD `58ba8fe9`; re-locate before editing.

---

## 0. Creative direction in one page

**RC MetaStudio is a quiet instrument.** It is a desktop tool a researcher uses
for an hour at a time, between a spreadsheet and a manuscript. The design goal is
not to look like a web product; it is to look like the best native Windows and
macOS research software looks: calm chrome, dense but legible data, one
typographic voice from the grid to the Word export, and a results window that
feels like the centre of gravity rather than a debug console.

Three words the parent can test every change against:

- **Paper.** Data surfaces (grid, tables, plots, manuscript) read like a printed
  page: horizontal rules, bold aligned headers, upright numerals, generous row
  rhythm, no vertical grid lines except in the editable spreadsheet. In dark
  theme a plot stays a white sheet on a dark desk; we do not recolour science.
- **Native.** Palette roles, system font, system accent for focus and selection,
  Qt widgets. We never fight the OS; we only remove inconsistencies the app
  itself introduced (mixed label grammar, cavernous or clipped dialogs, text-only
  toolbars beside iconised ones, a status message that never expires).
- **One voice.** Project / Outcome / Arm / Study vocabulary everywhere, sentence
  case everywhere, one number formatter, one identity line per result, one
  toolbar grammar in both windows, one size policy for dialogs.

What this direction deliberately rejects: a theme engine, custom-painted
controls, accent gradients, card-heavy "dashboard" layouts, rounded coloured
chips, a web rewrite, a journal selector, and any change to statistical output.

### Non-negotiable design rules (apply to every change)

1. **Sentence case, no trailing colon** on form labels and group titles.
   Proper nouns and acronyms keep their case (Reitsma, DerSimonian-Laird, OR,
   SMD, SROC).
2. **One field column per form.** Labels left-aligned, vertically centred with
   their control; controls start on one shared x in a QFormLayout.
3. **Dialogs size to content.** No internal scroll area while the dialog is
   below its policy maximum (`WINDOW_POLICIES` 0.90 of the screen); re-run the
   content fit when content changes (error panel, mode change, Advanced toggle).
   No arbitrary minimum heights; a two-field dialog may be 160 px tall.
4. **Numbers keep their producer's precision.** Source inputs echo verbatim;
   derived values use one formatter with constant significant digits per column;
   conversions never overwrite typed text.
5. **Red means wrong.** The app's error palette (`#b00020` / `#ff9ca8`) is used
   for messages about a failure only. Focus and selection use the OS accent and
   the app never imitates it.
6. **Transient status expires in 4 s.** Durable facts are widgets, not
   messages.
7. **One toolbar grammar.** Family B icons, text beside icon, 28 px artwork in a
   36 px target, separators between verb groups, every primary verb with a
   shortcut shown in its menu and tooltip.
8. **One identity per result,** printed once in chrome, never scaled with zoom.
9. **Plots are paper.** On screen a plot's first zoom is never above 100 %
   unless the user asks for Fit width; a portrait plot fits the page.
10. **Vocabulary from CONTEXT.md.** Project, Sheet/Outcome, Arm, Study, Group
    (subgroups only), Small-study effects.

---

## 1. Shared design grammar (tokens in Qt terms)

All values derive from the application font so they scale with system text
size. `em` means `widget.fontMetrics().height()` (about 15–16 px at Segoe UI
9 pt, 100 % scale). Where a pixel value is given it is the 100 % rendering of
the em rule, for acceptance checks only.

### Spacing

| Token | Rule | Use |
|---|---|---|
| `page-margin` | 1.5 em (24) | Home, wizard page content, results content area |
| `dialog-margin` | 0.75 em (12) | QDialog content margins (transactional dialogs) |
| `section-gap` | 1.25 em (20) | Between vertical sections (Home title → intro → cards → recents) |
| `group-gap` | 0.75 em (12) | Between QGroupBoxes / disclosure groups inside a dialog |
| `form-vgap` | 0.5 em (8) | QFormLayout vertical spacing |
| `form-hgap` | 0.75 em (12) | Label-to-field horizontal spacing |
| `inline-gap` | 0.5 em (8) | Between sibling controls on one row (Lower / Upper, button rows) |
| `card-gap` | 1 em (16) | Between Home cards and recents columns |

`start_page.py` already uses 24/20/16/12/8; keep. Results content uses 6/4
(`results_window.py:409-411`): raise content margins to 0.75 em; leave the
splitter alone.

### Control sizes and minimum widths

| Token | Rule |
|---|---|
| Control height | `fm.height() + 12` (already enforced by `_ControlStyle.sizeFromContents`) |
| Primary action button | 36 px high, 24 px icon (`configure_primary_action_buttons`) |
| Toolbar button | 36 px target, 28 px artwork (`configure_main_toolbar`) |
| Numeric line edit minimum | 10 em |
| Name / path line edit minimum | 20 em |
| Combo minimum | contents + arrow; never full dialog width unless it is the only control on the row |
| Dialog minimum | none global; `set_content_preferred_width(minimum=measured label column + 10 em field)` |
| Dialog maximum | 0.90 screen (policy), already |

### Type roles (use `qt_layout.configure_heading`; add nothing new)

| Role | Font | Where |
|---|---|---|
| App title | bold, 1.8× | Home "RC MetaStudio" only |
| Page title | bold, 1.15× | Wizard page titles, Results identity strip name |
| Section heading | bold, 1.0× | Results section headers ("Forest plot"), Home "Recent projects", calculator sub-tables ("Intervention") |
| Body | 1.0× | Everything else |
| Caption / muted | 1.0×, `PlaceholderText` role or 0.8 opacity | Paths, derived read-outs ("SE (log scale) 0.6172"), status |
| Manuscript body | max(11 pt, app) serif-free, as now | Manuscript page |
| Tabular numerals | upright, right-aligned | Grid, Results tables, plot annotation |

Headings are never italic except the existing sub-table arm titles in the
continuous calculator, which become **bold section heading** (rule 7 of the
grammar: one heading style).

### Palette roles (no literal colours beyond these)

| Purpose | Role / value |
|---|---|
| Window, text, buttons | system palette |
| Selection / focus | `Highlight` (OS accent); grid keeps its deliberate `#245a81` so a selected cell cannot be confused with a red accent |
| Links | `QPalette.Link` set once in `configure_application_controls`: light `#1a5fb4`, dark keep default |
| Error text | `#b00020` light / `#ff9ca8` dark (`qt_layout._set_error_palette`) |
| Derived column tint | gold `QColor(214,169,58,80)` as now |
| Disabled text (dark) | `#999999` as now |
| Plot paper | white, R-side default; unchanged |

### Icons

| Context | Size | Set |
|---|---|---|
| Main / Results toolbar | 28 in 36 | `icons/actions/*` family B |
| Analysis menu | 18 | `icons/analyses/compact/*` |
| Home cards | 24 in 36 | `icons/actions/*` |
| Grid row header | 16 | `icons/table/calculator.svg` |
| Data-type cards | as now | `icons/dataset-types/{light,dark}` |

New assets required by this brief (draw in family B, 28 px master + 18 px
compact not needed): `export.svg` (arrow out of tray), `edit-plot.svg` (pen on
chart), `fit-page.svg`, `fit-width.svg`, `settings.svg` (sliders; reuse the
`meta-analysis` sliders glyph if a distinct one is not wanted). Five SVGs, no
dependency.

### State grammar

| State | Rule |
|---|---|
| Hover | native |
| Focus | native accent ring; never a custom border |
| Selected (lists, nav tree) | native `Highlight`; nav tree current item shows the native selection bar, not only a left tick |
| Disabled | native; **every disabled primary action has a tooltip and status tip saying why** (already done for analyses in `main_window.py:504-544`; extend to Results `Export plot`, `Edit plot`, `Change settings`, Tables) |
| Error | message in a dedicated `QLabel` with `style_inline_error`, first word a plain verb phrase ("Cannot import: …", "No studies are included.") placed directly above the controls it refers to; never a red border on a field |
| Empty | one sentence + one action link (Home recents, Tables page without tables) |
| Busy | `AnalysisProgressDialog` as now; title = owning window title |

---

## 2. Screen-by-screen directions

Each item: **what** (hierarchy, wording, size), **where** (file:line), **state**,
**keys**, **accept** (visual + interaction acceptance). Priority P1 (ship in the
first batch), P2 (second), P3 (nice). Effort S/M/L. "Source-backed" unless
marked **Hypothesis** (needs a prototype or a trace first).

### 2.1 Shell: menubar, toolbar, status bar, sheet strip

**Menubar** (`forms/main_window.ui`, `main_window.py:302-311`). Order stays
File, Edit, View, Analysis, Project, Help. P1, S:

- Project menu (renamed by the sweep) holds New project…, Add covariate…, Swap
  intervention and control. Add "Rename outcome…" (F2) and "Add outcome…" here so
  the menu covers the sheet strip's context menu; both actions exist as slots
  (`_rename_sheet`, `_add_sheet`).
- View menu: add "Previous outcome" Ctrl+PgUp and "Next outcome" Ctrl+PgDown as
  visible entries bound to the existing hidden QActions (`main_window.py:336-340`).
  Justification: the bindings exist but nothing in the UI reveals them.
- Analysis menu already has icons and tooltips; add accelerators (below).
- Help: About… stays; add "Project site" and "How to cite" (the two links already
  on the wizard welcome page) so help is reachable after the wizard is gone.

**Shortcuts** (collision-checked against `main_window.ui`, `main_window.py:311,336,451-456`
and `results_window.py:695-711`). P1, S:

| Action | Key | Where | Collision |
|---|---|---|---|
| Meta-analysis… | Ctrl+R | main | none |
| Rename outcome | F2 (when sheet strip or grid has focus) | main | grid F2 edits cell; bind on the tab bar only |
| Previous / next outcome | Ctrl+PgUp / Ctrl+PgDown | main (exists) | none |
| Fit page | Ctrl+0 | Results | none |
| Fit width | Ctrl+Shift+0 | Results | none |
| Zoom in / out | Ctrl+= / Ctrl+- | Results | none |
| Edit plot… | Ctrl+E | Results | none |
| Change settings… | Ctrl+Shift+R | Results | none |
| Text report / Tables / Copy / Export | existing Ctrl+T, Ctrl+Shift+T/C/S/E | Results | keep |

Accept: every Analysis and Results menu capture shows an accelerator column; a
key-only drive runs New project → Create → Ctrl+R → Run → Ctrl+0 → Ctrl+E.

**Toolbar Analyses control** (`main_window.py:284-297`). P1, S. Decision: make
it a split button. `setPopupMode(MenuButtonPopup)`, `setDefaultAction(action_go)`
so the main part reads "Meta-analysis" with the meta-analysis glyph and runs the
most frequent analysis in one click; the arrow opens `menuAnalysis` (all seven
entries, disabled ones explaining themselves as now). Keep
`setAccessibleName("Analyses")` on the button so the drive scripts keep working;
verify `.agents/skills/verify-rcms/scripts/click` targets by accessible name, not
visible text, before merging. Accept: `02-0-A-home` shows a two-segment button,
no detached indicator under the label; main part disabled on Home with the
existing tooltip.

**Status bar** (`main_window.py:319-327, 494`). P1, S:

- Every `showMessage` in both windows passes `4000`. Results currently has
  none (`results_window.py:642, 650, 669, 848, 861, 1692`).
- Move the "95% CI…" button out of the status bar into the sheet strip, right
  end, after the "+" tab, separated by `inline-gap` (`_setup_sheet_strip`,
  `:1349`). Text "95% CI", no ellipsis (it opens a tiny dialog; the ellipsis is
  correct by convention but the strip is cramped; keep the ellipsis if the parent
  prefers strict convention). Tooltip unchanged. Status bar then carries only
  messages. P2, M (layout of the strip). Accept: button sits on the same baseline
  as the tabs, within 1 em of "+" when few tabs, pinned right when many.

**Sheet strip** (`SheetTabBar`, `main_window.py:1349-1364`). P2, S:

- Tabs elide at ~180 px even on an empty strip (`106-0-J-grid-tabs-dark`,
  "Catheter-related bloodstream i…"). Cap per-tab width at 28 em when the strip
  has spare room, 12 em minimum when it overflows; locate the cap in
  `SheetTabBar.tabSizeHint` (not read; verify).
- Keep scroll buttons off; keep the inline rename on double-click; add F2.
- Context menu order: Rename, Add outcome, separator, Move left, Move right,
  separator, Delete (destructive last, with the outcome name quoted: "Delete
  'nephrotoxic'…").

### 2.2 Home (`start_page.py`)

P1, S:

- Cards: `card.setFlat(True)` removes the bordered-button-inside-a-bordered-box
  look; keep the 36 px button with icon and description below. Three equal
  columns, `card-gap` 16, max content width 1000 as now.
- Button captions stay "New project", "Import data", "Open project".
- Recent projects: keep the heading. Row = name button (min 14 em) · muted
  elided path (opacity 0.8 as now) · nothing when available (drop the "Available"
  label; show only "Missing file" + "Locate…" / "Remove from list" for missing
  rows). Rows separated by `form-vgap`.
- Empty state: "Projects you open or save will appear here." plus a second line
  with a link button "Open the sample project" **Hypothesis**: only if the
  bundled sample (`scripts/verify_bundled_sample` suggests one ships) is
  installed with the app; otherwise point to "Import data".
- Intro sentence stays. Title 1.8×.

Accept: `02-0-A-home` shows three flat cards, no double frame; empty recents
reads as two lines, not a void. Dark parity unchanged.

### 2.3 Workspace grid (`dataset_table_model.py`, `dataset_table_view.py`)

P1, S:

- Header "Study Name" → "Study name" (sentence case). The model header list is
  lowercase (`dataset_table_model.py:138`); the capitalisation happens in
  `_horizontal_header_display` (not read). Change it to capitalise only the
  first character. Import mapper's "Field" column must follow (it shows the same
  label, `30-0-C-map-columns`); file-column names stay as the file wrote them.
- Derived-column precision: `format_effect_number` small-value branch strips
  trailing zeros (`result_formatting.py:148`), so the Lower column shows
  `0.004`, `0.0088`, `0.0086`, `0.17`. Keep zeros in the fixed branch (strip
  only in the exponent branch) so two significant digits are constant:
  `0.0040`, `0.0088`, `0.0086`, `0.17`. Accept: `04-0-A-amino-grid` Lower column
  scans with equal significant digits; Results tables unaffected (they use
  `digits` from the analysis).
- Row-header calculator glyph is a real affordance (shown only when the study
  has entered data, `dataset_table_model.py:879-884`, with tooltip). Keep it.
  Prior P14 is withdrawn.
- Selection colour stays the grid's own blue; everything else native.
- Context menus (`38`–`49` captures) are correct and minimal; keep. Row menu:
  Copy, Paste, separator, "Delete study 'Gonzalez'…" already quotes; good.
- Two trailing blank rows for entry stay; no "Add study" shortcut needed.

### 2.4 Wizard: New project / Add outcome (`main_wizard.py`, `forms/*_page.ui`)

**Welcome page** (`WelcomePage`, `main_wizard.py:103`, start id at `:1069`).
P2, S + a trace: the page duplicates Home. Trace every `MainWizard(path=None)`
caller. If all UI entry points pass `"new_dataset"` or `"csv_import"`, the page
is dead: delete it and move its three links to Help. If one entry passes `None`,
route that caller to `Page_DataType` and still delete the page. Until then the
sweep's labels ("Start a project", "Open project…") stand. Accept: no capture
shows a wizard page offering the same three actions as Home.

**Data type page** (`04-0-B`): keep as is. It is the clearest page in the app.

**Choose a metric page** (`08-0-B` … `22-0-B`): one combo in 800×640. P2, M:

- Under the combo add a definition label (`configure_context_label`), one
  sentence per metric, from a dict in `main_wizard.py` keyed by metric id (e.g.
  "Odds ratio: odds of the event in the intervention arm divided by odds in the
  control arm. Default for binary data."). Then a muted line listing the other
  available metrics for this data type.
- Page content top-aligned with `page-margin`; the wizard's shared window size
  is accepted (rule 3 exempts the wizard).
- **Experiment X2** (metric inside the data-type card) stays an experiment.

**Outcome page** (`06-0-B`, `54-0-B`). P1, S:

- The disabled "Next >" beside "Create" is forced visible by
  `_synchronize_default_action` (`main_wizard.py:1151`, visible unless Welcome or
  CsvImport). Change to `next_button.setVisible(self.nextId() != -1)`. Accept:
  the final page shows Back · Create · Cancel only.
- Placeholder per data type (done by the sweep). Validation message already
  stays empty until `_name_attempted` (confirmed). The red underline in captures
  is the OS focus accent; no change.
- Arms section (comparative): two name fields in the same form column as
  Outcome name; labels "Intervention name" / "Control name" (sentence case, as
  now).

**Button row**: Stretch, Back, Next, Finish, Cancel (as now). Default button
follows the visible forward action (as now).

### 2.5 Import: CSV / Excel / RevMan (`CsvImportPage`, `rm5_import` dialog)

P1, S:

- File chooser button: full-width is fine; keep the file name centred with the
  folder glyph. Title "Import data" 1.15×.
- "Data type" / "Worksheet" labels and combos: combos are full width; acceptable
  because they are the only control on the row.
- Error text ("Binary!C2 has a formula with no saved value. Open and save it in
  Excel first.") is the right register; keep. It uses the error palette; good.
- "Save a blank template" link: fixed by the Link palette role (section 1).
- Preview/Map columns tabs: keep. Map columns "Field" column follows the grid
  header rename.
- RevMan confirm dialog (`34`, `36`): table takes dialog width
  (`horizontalHeader().setStretchLastSection(True)`), "Studies" right-aligned,
  the "Differs from RevMan" / "Not imported" leads **bold** on their own line,
  body lines as now; closing sentence unchanged. Buttons Import · Cancel, Import
  default.

### 2.6 Small dialogs (About, Confidence level, Add covariate, Covariate values, Add study, Rename ×3)

P1, S, all in one commit:

- Labels: "Confidence level", "Covariate name", "Type of covariate", "Study
  name", "Covariate name", "Arm name" (the `EditArmNameDialog` says "Group
  name:"; CONTEXT.md forbids Group for an arm). Remove the colons
  (`edit_name_dialogs.py`, `add_new_dialogs.py`, `confidence_level_dialog.ui`).
- Covariate values dialog title "Values for New Covariate" → "Values for new
  covariate" (`covariate_type_dialog.ui`); the table should show at least eight
  rows before scrolling (`setMinimumHeight(8 * rowHeight + header)`) bounded by
  the policy maximum; it is a transactional dialog so this is content, not an
  arbitrary minimum.
- Add covariate: primary button "Add covariate" default; the dialog is 216×170
  and that is correct for two fields. Do not enlarge.
- About: fixed (transparent wordmark). Version line muted. Links already use the
  Link role; the light value changes with section 1.
- Confidence level: the sentence above the spinbox is the right pattern; keep.

### 2.7 Calculators

**Binary (`binary_data_dialog.py`), Diagnostic, Continuous summary**. P1, S–M:

- "95% confidence interval  Lower [ ]  Upper [ ]" row does not share the field
  column with Estimate (`80`, `84`, `94`). Put "Lower" and "Upper" as two
  half-width fields with "to" between them in the same form column: label "95%
  confidence interval", field widget = QHBoxLayout(lower, QLabel("to"), upper).
  The binary dialog's `ci_label.setMinimumWidth` (`:179`) becomes unnecessary.
- Sub-table arm titles ("Intervention", "Control" in pre/post) use the section
  heading role (bold), not italic.
- Derived read-out row ("SE (log scale): 0.6172   Z: -0.9067   Two-sided P:
  0.365") is the right pattern; make the separator a middle dot with 1 em gaps
  and drop the colons: "SE (log scale) 0.6172 · z −0.9067 · two-sided p 0.365".
  Keep producer precision.
- "Reconstruct group data" disabled with no explanation: add tooltip "Enter an
  estimate and interval to reconstruct counts." (state rule).
- Input mode combo first row: fine. Group boxes: keep native titles, sentence
  case ("Study counts", "Effect estimate and confidence interval" already).

**Continuous pre/post**: fixed (refit, scroll 0). Correlation field 10 em.
**Continuous "Entered estimate"** (`92`): half the dialog is empty after the
table group hides; call the same content refit used by the mode change (already
requested for pre/post) so height follows content. P1, S.

**HR / IRR (`ratio_data_dialog.py`)**. P1, M:

- Never rewrite the typed text on a scale change (`_convert_format_fields:94-104`).
  Cache the three field texts per scale (`self._typed = {scale: (est, lo, up)}`)
  when leaving a scale; on entering a scale restore its cache if present and if
  the current texts still equal the last conversion result; otherwise convert.
  Typing in either scale is honoured verbatim; round-tripping restores the
  original digits. Full precision retained; no rounding anywhere.
- Add the calculators' derived read-out row under the fields: ratio mode shows
  "log HR −0.1241 · SE (log scale) 0.2626"; log mode shows "HR 0.883 · 95% CI
  0.528 to 1.478". Display digits for this caption only use the sheet's
  `NUM_DIGITS` + 2; the stored value is the parsed double.
- Fields min width 14 em (currently 230 px literal at `:39`; make it em-based).
- Labels already colon-free; "Original CI (%)" → "Original CI level (%)".

### 2.8 Analysis setup (`analysis_setup_dialog.py`, `forms/analysis_setup_dialog.ui`)

P1, S:

- "Analysis method:" colon comes from code, not the .ui: `:156` and `:1786`
  (`"Analysis method: " + label`). Remove the colon and the centred alignment on
  `method_lbl` (`.ui` has `Qt::AlignCenter`); left-align like the other labels
  so the method combo starts on the shared field x (currently 22 px left of the
  others, `116-0-E`).
- Diagnostic variant (`09-0-analysis-configured`): two method rows with long
  labels; keep, but the "Shared parameters" group box title and "Advanced · 1
  changed" are good patterns; apply "· n changed" to every family's Advanced
  button.
- Advanced disclosure stays a `DisclosureButton`; content appears below with
  `group-gap`.
- Error panel (fixed to refit): cap the Details text box at 8 lines
  (`fontMetrics().lineSpacing() * 8 + frame`) with its own scrollbar, so the
  expanded state (`06-0-fable-analysis-error-True`) does not push Method off
  the first screen. P1, S.
- Plots tab stays (capability guardrail). Two refinements only: tab title
  "Plots" → "Forest plot" when the family produces only forests (binary,
  continuous, HR, IRR), "Plots" otherwise; and all colon labels in the .ui are
  removed by the sweep (confirmed in the diff).
- Buttons: "Run analysis" default · Cancel. Keep.

**Regression setup** (`148-0-E`): 560×620 for ~230 px of content. P1, S + trace:
the Covariates tab is the first tab; `_fit_active_tab_contents` appears to size
from the tallest tab (Plots). Fit to the *active* tab on first show, as the
Method-first families already do. **Hypothesis** until traced.

**Subgroup setup** (`146-0-E`): "Covariate for subgroups:" → "Covariate for
subgroups". OK default. Fine as a two-row dialog.

**Diagnostic metrics** (`150-0-E`): "Select metrics" group; Next · Cancel. Fine.
Disabled Next tooltip "Select at least one metric."

**Small-study effects** (`152`, `153`). P1, S–M:

- Internal scroll at 700×526 while the screen has room: pass a preferred height
  = content `sizeHint().height()` to `set_content_preferred_width`
  (`small_study_effects_dialog.py:239`); the policy clamps to 0.90 screen.
- "Primary: Rücker AS+RE / Additional: Peters" reads as settings. Render as a
  read-only status line in the context header (same register as "Binary · Odds
  ratio · 19 included · 17 eligible"): "Primary test Rücker AS+RE, chosen for odds
  ratios with 17 eligible studies · Exploratory Peters". The rationale string
  comes from `small_study_effects.py` (not read; it must already decide the
  primary test, so it can name the reason).
- Labels "Confidence level:", "Contour levels:" lose colons. "Confidence level"
  combo should be a spinbox like the setup dialog (consistency); low priority.

### 2.9 Results window (`results_window.py`, `forms/results_window.ui`)

This is the centre of the product; four committed changes.

**(a) Toolbar regroup with icons** (`_setup_results_actions:690-754`). P1, M:

Order and groups, separators between groups:

```
[Copy report ▾] [Export report…] [Export plot…] [PDF ▾]  |  [Edit plot…] [Change settings…]  |  Zoom [100% ▴▾] [Fit page] [Fit width]
```

- Apply the same configuration as the main toolbar: 28 px icons in 36 px
  targets, `ToolButtonTextBesideIcon` for Copy report, Export report, Export
  plot, Edit plot; icon-only with tooltip for Fit page / Fit width; `Zoom`
  label stays text.
- Icons: copy.svg (exists), export.svg (new, used twice), edit-plot.svg (new),
  settings.svg (new or reuse meta-analysis sliders), fit-page.svg, fit-width.svg
  (new).
- "Copy report" becomes a `MenuButtonPopup`: main part keeps Ctrl+Shift+C
  behaviour (copies the active report page); the arrow lists "Copy Methods",
  "Copy Results" (from the manuscript mini toolbar) and "Copy table" when the
  Tables page is active. Remove the manuscript mini toolbar (`:418-424`). The
  Tables page keeps "Export formatted CSV…" / "Export values CSV…" as flat tool
  buttons on the table header row, right-aligned, and loses "Copy table" (now in
  the menu). Ctrl+C on the table stays (`:531-533`).
- Keep the export-format combo next to Export plot (exists).
- Disabled verbs get tooltips: "Select a plot to export", "Select a plot to
  edit", "This analysis cannot be re-run from here".

Accept: both-theme captures of Forest, Manuscript, Tables, Settings show one
toolbar with three groups and icons; manuscript page has no second toolbar;
Copy report arrow opens a three-item menu on the Manuscript page.

**(b) Navigation order** (`_setup_report_controls:372-382`). P1, S: insert the
text entries *after* the plot items: Forest plot (and other figures) first, then
Manuscript, Text report, Tables, Settings. Keep every entry and Ctrl+T /
Ctrl+Shift+T. `_show_initial_result` logic unchanged. Nav tree width: keep
`sizeHintForColumn + 12` but make it a splitter minimum, not fixed, so long
plot names ("Deeks Effective-Sample-Size funnel plot") do not force a 270 px
pane; elide middle. Accept: tree reads Forest plot, Manuscript, Text report,
Tables, Settings for a binary run; current item uses native selection fill.

**(c) Identity strip.** P1, M: one fixed `QLabel` row at the top of the content
area (above `content_stack`, inside the right splitter pane), `page-margin`
left, section-heading weight for the outcome name, body weight for the rest:

```
clinical failure   Binary · Odds ratio · Intervention / Control · k = 19 · Random effects (DerSimonian-Laird) · 95% CI
```

Source: `results.identity` (already feeds the window title at `:408`) plus `k`,
model and CI from `results.details` / manuscript model info
(`manuscript_report.py:358`). Capitalise the first character of the outcome name
for display only. The per-section small bold header ("Forest plot") stays; the
in-SVG caption stays for now (export needs it) and is the subject of experiment
E1. Accept: every page shows the strip; it does not scroll or zoom; text report
page no longer opens on "Pooled effect" without context.

**(d) First zoom and fit actions.** P1, S:

- Root cause (traced): `_automatic_plot_scale` (`:1008-1021`) caps non-forest
  plots to the available height, so funnel/SROC/coefficient first display is
  already fit-page; the 176–219 % captures followed an explicit Fit width. Forest
  plots skip the cap and `_fit_size_to_viewport` upscales to the viewport width
  (`MAX_VECTOR_PLOT_SCALE = 4.0`), so narrow forests open at 121–157 %
  (`16`, `26`, `34`, `40`). Fix: in `_automatic_plot_scale`, when not
  `_explicit_fit_width`, `target_scale = min(target_scale, 1.0)` before the
  text floor. Explicit Fit width keeps the unbounded behaviour.
- Add "Fit page" action (Ctrl+0): sets `_explicit_fit_width = False`,
  `_fit_width_active = True`, calls `_apply_fit_width`. "Fit width"
  (Ctrl+Shift+0) sets `_explicit_fit_width = True` as now. Zoom in/out
  Ctrl+= / Ctrl+- step the spinbox by 25.
- Zoom spinbox range 10–400 stays.

Accept: first-display captures (no prior Fit width) for cumulative,
leave-one-out, HR forest show ≤ 100 %; funnel and SROC show the whole plot;
after Fit width the funnel reaches 176 % as today; Ctrl+0 returns it.

**Manuscript page** (`_setup_manuscript_page`, `manuscript_report.py`). P1, S:

- H1: capitalise the first character of the outcome name (display only; the
  stored name is untouched).
- Sentences never start with a numeral: "In total, 19 studies were included …";
  "The 2 studies with no events in either arm were retained with this
  correction." (`manuscript_report.py` Methods/Results builders; the Results
  sentence starts at the k clause).
- Tables: already horizontal rules only. Keep the nbsp "to" join.
- Zoom applies to font size as now.

**Text report page**: keep. Same identity strip gives it context. Heading sizes
as now.

**Tables page** (`_setup_result_tables:498-576`). P1, S:

- `table_selector.setSizeAdjustPolicy(AdjustToContents)`, left-aligned with the
  table; no full-width flat combo.
- `result_table.setShowGrid(False)`; keep alternating rows and bold header; add a
  1 px bottom border on the header via the palette `Mid` colour (stylesheet on
  the header only). This makes the three Results surfaces one family.
- Export buttons as in (a).

**Settings page**: fine. Heading "Model configuration" and references are
readable; keep.

### 2.10 Plot editors (`plot_editor_dialog.py`, `funnel_plot_editor_dialog.py`)

P2, S:

- Label grammar done by the sweep for SROC; verify forest/funnel editors have
  none left (`72-0-H` showed colons; the diff removes them).
- Colour rows: hex field + "Choose color…" is fine; make the button text "Choose…"
  and give the field a 6 em maximum so the hex does not stretch across the
  dialog (`48-0-H-funnel-top`).
- "Rerun the analysis to change statistical settings." line at the top of the
  funnel editor is the right pattern; keep.
- Button row OK · Cancel · Apply (Windows convention) stays.
- Disabled rows (Regression line, Null contour levels) already grey; add
  tooltips saying which style enables them.

### 2.11 Plot rendering on screen

- Plots stay white paper in dark theme; the scene background is the window
  palette (already), so the sheet reads as a document. Give the SVG item a 1 px
  `Mid` outline (a `QGraphicsRectItem` behind each plot item) so the paper edge
  is deliberate rather than a cut-off. P3, S.
- Coefficient plot height proportional to coefficient count: R-side
  (`r/RCMetaR`), presentation only. P3, M. **Hypothesis** for the exact row
  height; prototype with 1, 3 and 8 coefficients.

### 2.12 Exports (DOCX / PDF)

P1, S (`manuscript_report.py:528-550`):

- Per-cell alignment: compute `numeric` per cell with the same regex, not per
  column; header alignment follows the majority of its column. This fixes the
  Model fit "Value" column (text rows for estimator/inference force the whole
  column left). Apply the same rule in `table_html` (`result_formatting.py:24-43`)
  so screen and Word agree.
- Replace `' to '` with `' to '` in DOCX cell text (the screen
  manuscript already does) so intervals do not wrap.
- `table.autofit = True` and set column widths from the longest cell per column
  (character count × 0.11 inch, clamped) so "SE scale" stops hoarding width.
- Numeral-initial sentences as in 2.9.

### 2.13 Progress, errors, empty and disabled states

- `AnalysisProgressDialog`: title = owning window title (as now); label two
  lines (operation, context); add an indeterminate `QProgressBar` if the .ui
  lacks one (not read). P3.
- Error register: a plain sentence first, "Details" disclosure second, capped at
  8 lines (2.8). Import errors inline above the buttons (as now).
- Empty Tables page: "This analysis produced no tables." with the Tables nav
  item disabled (already) and a tooltip.
- Disabled analyses: keep the explanatory tooltips; mirror them as status tips.

---

## 3. Corrections to earlier reviews (do not implement these)

- Pre/post initial scroll: fixed; the earlier capture was post-scroll.
- HR/IRR `.6g` rounding: rejected; use the per-scale text cache (2.7).
- Results window title: `_setup_identity` sets "sheet — identity"; the "Results"
  caption in captures is not evidence of a generic title.
- Model fit rows df and I²: present in the complete DOCX
  (`report-observations.json`); the issue is per-column alignment (2.12).
- Required fields red on open: OS accent; `OutcomeNamePage.isComplete` and
  `AddCovariateDialog` already defer messages. No validation logic to add.
- Row-header glyph: real affordance; keep.
- Initial zoom of portrait plots: already fit-page; the real defect is narrow
  forests upscaling past 100 % (2.9 d).
- Sheet navigation keys exist; the fix is discoverability (2.1).
- "Plots tab removal": withdrawn under the capability guardrail; renamed only.

---

## 4. Experiments (prototype first, then decide)

| # | Experiment | Smallest prototype | Decide by |
|---|---|---|---|
| E1 | Remove the in-SVG caption from the *display* render (keep in export) once the identity strip exists | One R flag on `fp_display_path` for the binary forest only; capture at 100 % and after Fit width | Keep if no reviewer misses the caption in a two-plot results window (funnel + contour) |
| E2 | Welcome page removal | Trace `MainWizard(path=None)` callers; if none, delete | Delete if no UI caller passes `None` |
| E3 | Metric choice inside the data-type card | One card (Proportions) expanding to a 2-item radio list; keep the combo page for the rest | Keep if the wizard drops to three pages without losing the default marker |
| E4 | Default forest label colour (accent vs black) | Show `02-0-G` vs `06-0-G` to five users | Change default only on a 4/5 preference |
| E5 | Docked Results pane in the main window | A `QDockWidget` wrapping the existing `ResultsWindow` central widget, one week of dogfood | Adopt if alt-tab loss of context is reported as the main pain |
| E6 | "Data changed since this analysis" banner with Re-run | A dirty flag set by the model on edit, read by Results on focus | Adopt if false positives are zero in the dialog suite |
| E7 | Coefficient plot height rule | Render 1/3/8 coefficients at 0.5 em per row + 6 em | Adopt if all three read without empty frame |

---

## 5. Ordered commits

Each commit is self-contained, passes strict typing and the 66-check GUI suite,
and leaves one capture pair (light/dark) per touched surface.

1. **Grammar and copy sweep (finish).** Code-side colons (`analysis_setup_dialog.py:156,1786`, subgroup, small-study, small dialogs), "Group name" → "Arm name", "Study name" header, covariate values title, numeral-initial sentences, H1 capital, derived read-out separators, Link palette light value, status message timeouts in Results. (P1, S)
2. **Wizard.** Hide Next on the final page; metric definition line; dead-welcome trace (E2 decision recorded). (P1, S–M)
3. **Shell.** Split Analyses button; shortcut set with menu accelerators; View menu outcome navigation entries; Project/Help menu additions; flat Home cards and recents rows. (P1, S–M)
4. **Numbers.** `format_effect_number` zeros; per-cell alignment in HTML and DOCX; DOCX nbsp and widths; ratio-dialog scale cache and read-out. (P1, M)
5. **Results toolbar, nav order, identity strip.** (P1, M)
6. **Zoom.** Automatic scale cap at 1.0, Fit page / Fit width / zoom keys. (P1, S)
7. **Dialog fit.** Error details cap; small-study preferred height; regression first-tab fit; continuous estimate-mode refit; calculator CI row; covariate values rows. (P1–P2, M)
8. **Strip and tables.** CI button into the sheet strip; tab width cap; Tables page grid and selector; plot editor colour fields; paper outline. (P2, M)
9. **Experiments** E1–E7 as separate branches with the stated prototype and decision.

---

## 6. Inspected coverage (candid)

Opened in full this pass (≈118 captures from the 268 indexed, plus 8 from the
two native polish runs):

- A: home (both), amino grid (both), all six menus (light), Analyses dropdown,
  tab context menu, inline rename, 20-tab overflow, 1024 grid, grid context
  menus (study, effect, row), J grid tabs (dark).
- B: welcome (both), data type (both), outcome (light), add-outcome name,
  metric binary proportion (light).
- C: CSV preview, CSV options, XLSX two sheets, map columns (both), XLSX error,
  both RevMan dialogs, J import (dark).
- D: About (light + fixed dark), confidence level, add covariate, covariate
  type, add study, rename, rename arm, binary counts (both), binary estimate,
  continuous summary, pre/post (light + fixed before-scroll both runs),
  continuous estimate, diagnostic counts, HR ratio, HR log, IRR raw, IRR
  reported ratio.
- E: binary method (both), advanced, plots; continuous method; diagnostic
  method, advanced, plots; HR method; IRR method, advanced; subgroup;
  regression; diagnostic metrics; small-study (both); error collapsed and
  expanded (light + fixed dark pair); J setup advanced dark; native diagnostic
  configured.
- F: manuscript (light + J dark), text report, tables, settings, subgroup
  tables; native diagnostic text report and tables (dark).
- G: every family listed in the index in light (binary default/RevMan/BMJ,
  continuous, diagnostic, HR, subgroup, cumulative top+bottom, leave-one-out,
  regression, funnel (both), contour, trim-and-fill left and right (176 %),
  SROC, coefficient, Deeks); J forest dark; native SROC figure.
- H: forest top+bottom, subgroup top, funnel top+bottom, SROC top+bottom,
  coefficient top, regression top, Deeks top; J plot editor dark.
- I: all four rendered pages.

Not opened: dark variants of B metric pages, C CSV/XLSX, D small dialogs other
than those named, most E dark pairs, F text/tables/settings dark, most G and H
dark pairs, H bottoms for cumulative/leave-one-out/regression/contour/trim-fill/
coefficient/Deeks, the 188-step tour at `20261115T164415Z-69e6d2de-ui-crawl`
(completed after my inspection), `report-observations.json` (facts taken from
the parent's summary).

Source read: `adaptive_window.py`, `qt_layout.py`, `start_page.py`,
`result_formatting.py`, `progress_dialog.py`, `ratio_data_dialog.py:60-130`,
`results_window.py` (init, identity, toolbar, fit/zoom/refit paths, tables
setup), `main_window.py:270-350` and shortcut lines, `main_wizard.py` (outcome
page, wizard init, default-action sync), `manuscript_report.py` (primary
sections, docx table), `dataset_table_model.py` (header/decoration), the three
form diffs, and the icon asset list.

Not traced (marked Hypothesis above): `_horizontal_header_display`,
`SheetTabBar.tabSizeHint`, regression tab first fit, small-study primary-test
rationale string, `MainWizard(path=None)` callers, bundled sample availability,
progress dialog .ui contents.

---

## 7. Unresolved risks

- Split Analyses button: automation that clicks by visible text "Analyses" will
  break; by accessible name it will not. Check `verify-rcms` scripts first.
- Removing the manuscript mini toolbar changes where "Copy Methods" lives; the
  dialog suite may assert on it.
- Automatic scale cap at 1.0 changes first-display geometry for every forest;
  the goldens under `docs/ci/2026-11-03-windows-goldens` will need regeneration.
- Per-cell alignment changes the HTML of every table copied to the clipboard;
  tests comparing clipboard HTML will need updating.
- Identity strip reduces vertical space for plots by about 2 em; on 800 px
  screens the forest loses one row before scrolling.
