# RC MetaStudio UI refinement, pass 2 (Fable 5.2, design lead)

Date: 16 November 2026. Branch `ui/desktop-polish-and-icons`, HEAD `c93e6670`
(application frozen at `6b57b6dd`, version 0.5.5). Read-only: no launches, edits,
tests or delegates. Line numbers are at `c93e6670`; re-locate before editing.

Evidence: the final native tour `artifacts/verification/rcms/20261115T201609Z-096f8b58-ui-crawl/`
(312 steps, both themes; capture numbers below refer to its `ui-crawl-index.md`),
the gallery `artifacts/verification/ui-fable-2026-11-15/final-ui-preview.html`, the
resolved review `fable-final-implementation-review.md`, the batch log
[ui-fable-polish-2026-11-15.md](ui-fable-polish-2026-11-15.md) and the brief
[ui-design-direction-2026-11-15.md](ui-design-direction-2026-11-15.md), which stays
authoritative. Where this document and the brief differ, this document wins only
for the items it names.

Preserved without question (user decisions): family B icons; plus/minus cumulative
and leave-one-out; upright numerals; producer precision; coloured About logo in
both themes; confidence control bottom-right in the status bar; native Qt palette;
forest landing and quiet-instrument direction; no statistical change; no new
dependency. E1–E7 stay gated; nothing below depends on them.

## 0. Verdict

The first pass landed. Every committed direction is visible in the final tour and no
capture shows a blocker. What remains is the layer under "correct": places where
the app still speaks with two voices (group/arm, headings/labels, three calculator
archetypes), where one dialog family breaks the one-field-column rule (all plot
editors), where the Results window repeats itself (identity three times per figure
page, a navigation pane whose current item is invisible), and where the Word export
undoes the on-screen typography. All are small. The whole list below is roughly
three days of implementation plus qualification.

Class key: **defect** = observed on screen and source-traced; **design** = brief
deviation or a cleaner reading of the same rule; **creative** = not a defect, a
deliberate improvement with a concrete shape. Effort S/M/L. Items marked
**Hypothesis** need a trace before implementation.

## 1. P1: observed defects, fix in the first batch

### R1 · Plot editors use three field columns — defect (rule 2), S–M

- Evidence: `180-0-H-forest-top-light.png` (Plot style fields at x≈295, Appearance
  at x≈520, Column labels at x≈160); `220-0-H-funnel-top-light.png` (Presentation
  fields at x≈730, geometry at x≈275, Axes at x≈140 in `222`); `242-0-H-sroc-top-light.png`
  (x≈305 / 550 / 130). Dark pairs match.
- Cause: each group box owns its own `QGridLayout`
  (`forms/edit_plot_dialog.ui:36,71,138,245,291,330`;
  `forms/funnel_plot_editor_dialog.ui:16,44,56`), so every group sizes its own label
  column. The setup dialog already solved the same problem for Method/Advanced
  (batch log, T5/T6). **Hypothesis** for the funnel Presentation column at 730 px:
  the colour rows' `QHBoxLayout` (hex field + button) lets column 1 take the
  remaining width while column 0 has no cap.
- Change: after `setupUi`, measure the widest label across all groups, cap it at
  18 em, and call `grid.setColumnMinimumWidth(0, width)` on every group grid
  (plus `setColumnStretch(1, 1)`), in `plot_editor_dialog.py` and
  `funnel_plot_editor_dialog.py`. Replace `Choose color…` with `Choose…` in
  `funnel_plot_editor_dialog.ui:26-32` (the forest editor already did).
- Accept: in each editor every control starts on one x in both themes; the
  widest label ("Reference/regression color") does not push its field past
  18 em + form gap; `test_funnel_plot_editor.py` passes.

### R2 · "Group" still used for an arm in nine places — defect (rule 10), S

- Evidence and source:
  - Data type page cards: "One group per study", "Two or more groups per study"
    (`260-0-B-data-type-light.png`; `forms/data_type_page.ui:48,197`).
  - Continuous calculator input mode "Group summaries" (`84`;
    `continuous_data_dialog.py:178`).
  - "Reconstruct group data" in all three calculators (`80`, `84`, `94`;
    `forms/binary_data_dialog.ui:85`, `continuous_data_dialog.ui:75`,
    `diagnostic_data_dialog.ui:42`).
  - Forest setup tab and forest editor: "First group heading", "Second group
    heading", "Show first/second group data", "Show group data columns"
    (`120`, `180`, `182`; `forms/analysis_setup_dialog.ui:296-358`,
    `forms/edit_plot_dialog.ui:190-249`).
  - Arm rename window title "Edit Group Name" (`forms/edit_name_dialog.ui:6`;
    `EditArmNameDialog` never overrides it, `edit_name_dialogs.py:12-19`;
    `EditCovariateNameDialog` does at `:28`).
  - Accessible descriptions "each treatment group" / "each group"
    (`binary_data_dialog.ui:32`, `continuous_data_dialog.ui:27`).
- Change: "One arm per study", "Two arms per study" (the page never offers more
  than two), "Arm summaries", "Reconstruct arm data" ("Reconstruct counts" in the
  diagnostic dialog, which has no arms), "Intervention heading" / "Control
  heading" are wrong because arms are renamable, so use "First arm heading",
  "Second arm heading", "Show first/second arm data", "Show arm data columns";
  `self.setWindowTitle("Edit arm name")` in `EditArmNameDialog.__init__`. Stored
  parameter keys and R-side names stay.
- Accept: `grep -rn "group" src/rc_metastudio/forms/*.ui src/rc_metastudio/*_dialog.py`
  returns only subgroup, button-group and object-name hits. Grep `tests/` for the
  old literals first (none matched a broad grep on 16 Nov, but e2e drives may use
  accessible names).

### R3 · Add study dialog: label "Study", title "Add Study" — defect (rules 1, 10), S

- Evidence: `76-0-D-add-study-light.png` shows a lone field labelled "Study".
- Source: `forms/new_study_dialog.ui:6` ("Add Study"), `:9` ("Study", and the
  form uses `WrapAllRows`, so the label sits above the field unlike every other
  small dialog, `78`, `306`).
- Change: title "Add study", label "Study name", `rowWrapPolicy` →
  `DontWrapRows` so it matches Rename (`78`); OK → "Add study" default.
- Accept: capture matches `78-0-D-rename-light.png` in shape with the new text.

### R4 · Results navigation: current item is invisible when the tree is unfocused — defect (state grammar), S

- Evidence: `174-0-G-binary-forest-default-fit-light.png`, `162`, `166`: the
  selected row is painted `#f5f5f5` on `#ffffff` (sampled at 150,98 vs 150,116);
  in dark (`175`) the difference is similarly faint. The brief required the native
  selection bar; on Windows 11 the inactive-group highlight is nearly white, and
  the tree never has focus after a click lands in the figure.
- Source: `results_window.py:376-398` configures the tree; no palette is set.
- Change: give `nav_tree` a palette whose Inactive `Highlight` and
  `HighlightedText` equal the Active ones (three lines; refresh on
  `PaletteChange` like `SheetTabBar._apply_tab_palette`, `main_window.py:186`).
  Keep the native focus look otherwise.
- Accept: in both themes the current nav item has the accent fill whether or not
  the tree has focus; `J-forest-dark` and `G-*-fit-light` show it.

### R5 · Small-study and Deeks identity strips lose k and the test — defect (rule 8), S–M

- Evidence: `218-0-G-funnel-fit-light.png` strip reads
  `Clinical failure · Binary · Odds ratio · Intervention / Control` with no k, model
  or CI, while every other family ends with `k = 19 · <model> · 95% CI` (`174`,
  `198`, `212`). `252-0-G-deeks-fit-light.png` likewise.
- Cause: `small_study_effects_dialog.py:493` builds `identity` from
  `dataset_identity` only, and the result has no `Model:` / `Confidence level:`
  detail lines for `_setup_identity` to read (`results_window.py:425-441`).
- Change: the dialog already composes the producer facts for its own header
  (`small_study_effects_dialog.py:62-71, 310-326`: "19 included · 17 eligible",
  "Primary test Rücker AS+RE"). Append those strings to the identity's second
  line in `_with_report_identity`, e.g.
  `… · k = 19 · 17 eligible · Primary test Rücker AS+RE · 95% CI`, from the same
  report object; no selection logic is added. For Deeks: `k = 17 · Primary test
  Deeks (meta 8.5-0)` using the package fact the report already discloses.
- Accept: funnel and Deeks strips carry k, the primary test and the CI level; the
  tooltip still shows the full details; `report_retention` e2e unchanged.

### R6 · Setup Plots tab and plot editor disagree on their own labels — defect (one voice), S

- Evidence: setup tab (`120`) says "Column headings", "Show headers" with
  "Show annotation"; the editor (`180`, `182`) says "Column labels", "Show" with
  "Annotation". Same controls, two vocabularies, seen minutes apart.
- Source: `forms/analysis_setup_dialog.ui:229-358` vs `forms/edit_plot_dialog.ui:132-249`.
- Change: one wording in both: group "Column headings"; row label "Show";
  checkboxes "Arm data columns", "Column headings", "Annotation" (drop the
  repeated "Show" verb once the row label carries it).
- Accept: the two captures differ only in the setup tab's extra Style/Study order
  rows.

### R7 · "Heterogeneity (τ²) estimator" is the only wrapped label in setup — defect (layout), S

- Evidence: `116`, `117`, `122`, `128`, `134`, `140`: the label wraps to two lines
  and makes that row 1.6× taller than its neighbours.
- Source: `analysis_method_labels.py:122`.
- Change: label "τ² estimator"; tooltip "Between-study variance (heterogeneity)
  estimator". Keep the long form in the Settings page and manuscript.
- Accept: no wrapped label in any Method tab at the default dialog width.

### R8 · Results menu is a flat list and cannot reach the Manuscript — defect (keys), S

- Evidence: `158-0-F-results-menu-light.png`: ten entries, one separator, no
  Manuscript or figure entry; the only way to the manuscript is the mouse.
- Source: `results_window.py:860-864`.
- Change: menu order and separators
  `Figures · Manuscript (Ctrl+M) · Text report (Ctrl+T) · Tables (Ctrl+Shift+T) | Copy report · Export report… · Export plot… | Edit plot… · Change settings… | Fit page · Fit width · Zoom in · Zoom out`.
  "Figures" selects the first plot item (the landing page); "Manuscript" selects
  its nav item. Both are two-line `QAction`s calling `nav_tree.setCurrentItem`.
  Ctrl+M is free in this window.
- Accept: the menu capture shows four groups; a key-only drive reaches Manuscript
  and back to the figure.

### R9 · Word export: headings in a different face, double-spaced table rows — defect (export), S

- Evidence: `172-0-I-docx-page-1.png`: the title and headings render in a light
  sans (Calibri Light look) while the body is Arial; Model fit rows are nearly
  twice the height of the on-screen rows (`170`).
- Cause: `manuscript_report.py:589-591` sets `styles[name].font.name`, but the
  default template's `Title` and `Heading 1` keep `w:asciiTheme`/`w:hAnsiTheme`
  attributes, which Word prefers over the explicit name. Table cell paragraphs
  inherit `Normal` paragraph spacing (space after 8 pt, 1.08 line spacing).
- Change: for each heading style strip the four theme attributes from
  `style.element.rPr.rFonts` (`asciiTheme`, `hAnsiTheme`, `eastAsiaTheme`,
  `cstheme`); in `_docx_table` set `paragraph.paragraph_format.space_after = Pt(2)`
  and `space_before = Pt(2)` for every cell paragraph (`:555-563`). Numbers and
  text untouched.
- Accept: a rendered page shows one family throughout and the Model fit table
  reads as the on-screen table does; `manuscript_export` e2e values unchanged.

### R10 · RevMan review table draws a full grid — defect (paper), S

- Evidence: `290`, `292`: vertical cell borders and boxed headers, unlike every
  Results table.
- Source: `rm5_import.py:248-265`.
- Change: `table.setShowGrid(False)`, `setAlternatingRowColors(True)`, the same
  header rule as `results_window.py:564`.
- Accept: the dialog's table reads like `166-0-F-amino-tables-light.png`.

### R11 · IRR raw-data labels carry a mid-label colon — defect (rule 1), S

- Evidence: `100-0-D-calculator-irr-raw-ratio-light.png`: "Anti-infective
  catheter: Events", "Standard catheter: Person-time".
- Source: `ratio_data_dialog.py:76-78` (`f"{arm_name}: {label}"`).
- Change: `f"{arm_name} {label.lower()}"` → "Anti-infective catheter events",
  "Standard catheter person-time". Keep accessible names explicit.
- Accept: no colon in any calculator label.

### R12 · Menus: duplicate "New project…" and no grouping in Analysis — defect (menubar), S

- Evidence: `14-0-A-menu-project-light.png` lists "New project… Ctrl+N" again
  (already first in File, `06`); `12-0-A-menu-analysis-light.png` has seven
  entries and no separators.
- Source: `forms/main_window.ui` (Project menu action list), `main_window.py:356-368`
  (Project additions), `276` (Analysis menu).
- Change: remove `action_new_dataset` from the Project menu. Analysis separators:
  `Effect-size tools | Meta-analysis… · Cumulative… · Leave-one-out… | Subgroup… · Meta-regression… | Small-study effects… | Change confidence level…`.
  The toolbar dropdown shares `menuAnalysis`, so it follows.
- Accept: both menu captures show the groups; `verify-rcms` menu scripts still
  find entries by text.

## 2. P2: polish that changes how the app reads

### R13 · Tables page: a full-width frame around a half-width table — design, S

- Evidence: `166`, `167`, `196`: columns end at x≈885 while the table frame runs
  to x≈1250, so a third of the frame is empty paper.
- Source: `results_window.py:540-566` (`setStretchLastSection(False)` is
  deliberate; the compact-table check proves columns do not stretch).
- Change: let the table take its content width:
  `result_table.setSizeAdjustPolicy(AdjustToContents)`, horizontal size policy
  `Maximum`, left-aligned in its layout with a stretch after it, max width the
  pane. Alternating rows then end where the data ends, like the manuscript's
  tables. Keep the selector and the two export buttons on the header row.
- Accept: the table frame hugs its last column; a very wide table still gets a
  horizontal scrollbar; `test_results_workspace_layout.py` compact-table case
  passes.

### R14 · Calculators: one archetype instead of three — design, M

- Evidence: binary (`80`) uses two titled groups with the action row and
  read-out at the bottom; continuous summary (`84`) has no titles and a bare
  table; diagnostic (`94`) places Clear / Reconstruct *above* Prevalence and
  Metric and prints the read-out *inside* the "Entered effect estimate" group.
- Change (order for all three): Input mode → data group (titled: "Study counts",
  "Arm summaries", "Test counts") → derived rows if any → effect group ("Effect
  estimate and confidence interval") → Clear / Reconstruct row → read-out →
  buttons. Diagnostic: move Prevalence and Metric into the data group under the
  2×2 table; move the read-out out of the group. Continuous: title the table
  group; keep the pre/post bold arm headings.
- Accept: three captures scan top-to-bottom in the same order; the read-out is
  always the last line above OK/Cancel; the 146-check dialog suite passes with
  the geometry assertions updated only where the order changed.

### R15 · Import page: a frame inside a frame — design, S

- Evidence: `280`, `284`, `286`: the preview tab widget sits inside a second
  rounded frame (the untitled group box), x≈5–785, which makes the page look
  like a form inside a form.
- Source: `forms/csv_import_page.ui:183` (`preview_grp_box`, title blanked at
  `main_wizard.py:581`).
- Change: `preview_grp_box.setFlat(True)` and zero its margins, or replace it
  with a plain `QWidget` in the .ui. The tab widget then provides the only frame.
- Accept: one frame around Preview / Map columns; the error line and
  "CSV options" disclosure keep their positions.

### R16 · Wizard header band appears on one page only — design, S

- Evidence: `260` (Data type) and `264` (Metric) have a bare bold title;
  `262`/`310` (Outcome) has a title plus the breadcrumb subtitle "New project ·
  Single-arm proportion · Proportion" in a white band, so the layout jumps on the
  last step.
- Source: `main_wizard.py:1017-1018` sets the subtitle only in `OutcomeNamePage`;
  `DataTypePage.initializePage` (`:263`) and `ChooseMetricPage.initializePage`
  (`:440`) set none.
- Change: set the same subtitle grammar on every page: Data type → "New project"
  (or "Add outcome"); Metric → "New project · Two-arm binary"; Outcome as now.
  Rename "Choose a metric" → "Effect measure" and its field label "Metric" →
  "Effect measure" so the wizard, the setup dialog ("Effect measure", `116`) and
  the strip use one noun. Keep "What type of data do you have?".
- Accept: the white header band is present and the same height on all three
  pages; no page title changes height between steps.

### R17 · Home cards: a full-width button with a centred caption and a far-left icon — design, S

- Evidence: `02`, `03`: in each card the icon sits at the left edge and the
  caption is centred 140 px away, which reads as a form button, not a card
  action.
- Source: `start_page.py:66-70` (`Expanding` policy, `AlignTop`).
- Change: size the button to its content (`Preferred` horizontally) and add it
  with `AlignLeft | AlignTop`; the description stays below. Three compact
  icon+caption buttons over three descriptions reads as three choices.
- Accept: icon and caption are adjacent; the card rule line above each card
  stays (flat group box).

### R18 · Colour rows: a swatch, not a painted button — design (resolves O3), S

- Evidence: `120`, `180`, `220`, `242`: the "Choose…" button is filled with the
  chosen colour across 12 em and is the loudest element in each dialog.
- Source: `plot_editor_dialog.py:566`, `analysis_setup_dialog.py:935`
  (stylesheet on the button).
- Change: a 1.5 em square `QLabel` (`autoFillBackground`, palette `Window` =
  colour, 1 px `Mid` outline) between the hex field and a native "Choose…"
  button; drop the button stylesheet. Accessible name "Accent colour swatch"
  with the hex as its text for screen readers.
- Accept: colour rows read `[#2f5597] [■] [Choose…]`; buttons are native in
  both themes.

### R19 · Regression strip omits the moderator — design, S

- Evidence: `212-0-G-regression-fit-light.png`: the strip names the model but
  not "golden_year"; the plot's x-axis is the only place the moderator appears.
- Source: `analysis_identity.py:38` already writes "Moderators: …" into
  `details`; `results_window.py:430-438` ignores that line.
- Change: read the `Moderators: ` line like `Model: ` and append
  `Moderators: golden_year` before the CI level.
- Accept: regression and Reitsma meta-regression strips show their moderators.

### R20 · Export plot format as part of the verb — design, M

- Evidence: `174`: "Export report" and "Export plot" share one glyph, and the
  bare "PDF ▾" combo after them explains itself only on hover.
- Source: `results_window.py:779-790`; a per-format action list already exists
  for the plot context menu (`:1547-1593`).
- Change: make "Export plot…" a `MenuButtonPopup` whose arrow lists the formats
  (checked = remembered format, same `save_plot_export_format`); the main part
  exports in the remembered format. Remove the combo. Keep the accessible name
  "Plot export format" on the menu for the drive scripts.
- Objection to weigh: e2e drives set the format through the combo by accessible
  name; retargeting them is a day of harness work. If that cost is not wanted,
  the smaller fix is a muted "as" label before the combo and a tooltip on
  "Export report" naming its destination (DOCX). Parent's call.

## 3. Creative refinements (P3, each with a concrete shape)

### C1 · Empty sheet guidance — S

A new outcome opens on twenty blank rows (`18-0-A-one-sheet-light.png`,
`dataset_table_model.py:35`) with nothing to say what to do. Paint one muted
sentence in the viewport when the sheet has no studies, in
`DatasetTableView.paintEvent` (`dataset_table_view.py:83`): "Type a study name in
row 1, paste rows from a spreadsheet, or use Import data." (`PlaceholderText`
role, centred, page-margin from the top). It disappears with the first study.
This is the brief's empty-state rule applied to the one empty surface that lacks it.

### C2 · Jump keys for Results navigation — S

Bind Ctrl+1 … Ctrl+9 to the nav items in order (figures first, so Ctrl+1 is
always the first plot). Build the actions in `_setup_report_controls` after the
tree is filled; show them in the Results menu's navigation group (R8). Readers
who switch between a forest and its tables many times a session get a browser
habit for free.

### C3 · Derived cells in the calculators wear the grid's gold — S (Hypothesis on exposure)

The workspace grid tints derived OR/Lower/Upper cells gold (`04`); the continuous
calculator shows SE, Variance, p, Lower, Upper computed from N/Mean/SD in the same
white cells as the inputs (`84`), and the binary dialog's OR/RR/RD table is
untinted (`80`). Tint derived cells with `QColor(214,169,58,80)` and a tooltip
"Computed from the entered values". Needs the calculator models to say which
cells are derived; `calculator_controls.py` likely knows (not read).

### C4 · Recent projects show when they were last saved — S

Rows are name + elided path (`start_page.py:125-132`). Add a muted
"Modified 12 Nov 2026" column from `Path.stat().st_mtime` for existing files;
missing files keep "Missing file". A researcher with six `.rcms` files picks by
date more often than by path.

### C5 · Small-study tests sentence as context, not a group box — S

`152`: "Small-study effects tests" is a group box around one sentence. Render
that sentence with `configure_context_label` directly under the header line
"Binary · Odds ratio · 19 included · 17 eligible", and start the first group at
"Funnel plot methods". One fewer frame, the fact reads as a fact.

## 4. Checked and fine (do not reopen)

Home link colour `#1a5fb4` light (sampled). Meta-analysis and Save disabled on
Home (`02`). Grid Lower column constant digits (`04`). Sheet strip, overflow and
1024 grid (`64`, `66`). Context menus and quoted deletes (`22`, `304`). Error
register and Details cap (`154`, `156`). Regression first-tab fit (`148`).
Small-study no inner scroll (`152`). RevMan bold leads (`290`). Manuscript H1,
"In total", "The 2 studies" (`162`). Text report headings (`164`). Settings page
(`168`). First zoom ≤ 100 % where text allows; at 900 px the readable-text floor
wins and the forest scrolls horizontally (`160`), which is the intended trade.
Toolbar fits at 900 px with whole captions. About coloured logo both themes
(`68`, `69`). Red underline on focused fields is the OS accent, not an error.

## 5. Objections and trade-offs, candidly

- **In-scene section heading on single-plot pages.** Figure pages print the
  identity three times (strip, bold "Forest plot" heading in the scene, SVG
  caption; `174`). The caption is E1 and stays gated. The heading duplicates the
  nav item exactly when a result has one plot, but it anchors scrolling and
  automatic scaling for multi-plot scenes (`results_window.py:889-897, 1129-1139`),
  so hiding it for single-plot results touches both paths. I recommend leaving it
  this pass and folding it into the E1 decision.
- **R20** trades a tidier toolbar for harness work; see the objection in the item.
- **R14** is the only M-sized layout change; the dialog suite's geometry
  assertions for the diagnostic dialog will need updating. Do it as its own
  commit with before/after captures of all three calculators.
- **R16 "Effect measure"** changes a wizard title that drive scripts may match by
  text; grep `tests/e2e/ui_crawl.py` and `test_main_wizard_workflow_layout.py`
  first.
- Nothing here changes statistics, goldens, tolerances or exported numbers. R9
  changes DOCX styling bytes only.

## 6. Suggested commit order

1. Copy and vocabulary: R2, R3, R6, R7, R11, R12 (one commit, strict typing + 66
   wizard/setup/editor checks + menu captures).
2. Plot editors one column: R1, R18 (editor captures light/dark, all five kinds).
3. Results: R4, R5, R8, R19, C2 (figure, manuscript, tables captures; menu
   capture; keyboard drive extended by Ctrl+M and Ctrl+1).
4. Export and import surfaces: R9, R10, R15 (rendered Word page; RevMan and
   CSV captures).
5. Tables and Home: R13, R17, C4 (tables light/dark; Home with and without
   recents).
6. Wizard band: R16.
7. Calculators: R14, C3 (three calculator captures each mode).
8. C1, C5 last; both are isolated.

Each commit: strict Windows typing first, the focused GUI suite, one native
capture pair per touched surface, retained under `artifacts/verification/`.

## 7. Coverage limits

Opened in full from the final tour: A 02–24, 64–66, 304; B 258–264, 278, 310;
C 280–292; D 68–102 light, 69 dark; E 116–120, 128, 130, 146–156 light, 112/117
dark; F 158–168 light, 163/167 dark, 196; G 174, 175, 190, 198, 206, 212, 218,
230, 240, 246, 252; H 180, 182, 220, 222, 242; I 170, 172; J 109.

Not opened: most dark pairs in B/C/D/E/G/H, the inline-rename and 20-tab dark
frames, H bottoms other than forest and funnel, `steps.jsonl`, `qt-messages.log`.
Pixel colours were sampled only on `02` and `174`.

Source read: `results_window.py` (nav, identity, actions, fit/zoom, scene
titles), `main_window.py:130-375, 500-530, 1335-1365, 1391-1430, 1600-1640`,
`start_page.py`, `qt_layout.py:38-243`, `main_wizard.py:81-150, 423-512,
988-1030`, `edit_name_dialogs.py`, `progress_dialog.py`, `ratio_data_dialog.py`
(grep), `analysis_identity.py:59-96`, `small_study_effects_dialog.py` (grep,
480-500), `manuscript_report.py:528-610`, `rm5_import.py:200-270`,
`dataset_table_view.py:560-600`, the calculator, wizard, editor, progress and
results `.ui` files (grep), and the test file listing. Not traced: the funnel
Presentation column width cause (R1), calculator derived-cell exposure (C3),
`row_padding.py`, the theme-attribute fix against the exact python-docx version
pinned here (R9: verify `rFonts` element access on the installed version).
