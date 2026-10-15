# Reviewer-fix visual inspection

The implementation agent opened and inspected the images below through the image
viewer. Automated assertions supplement this inspection; an exit-zero helper is
not itself a visual acceptance. `REVIEWER-SCREENSHOTS.json` binds all 51 original
PNG copies and their source hashes; `reviewer-contact-sheet.html` contains 35
entries. The interactive `reviewer-gallery.html` was previewed at 728 pixels with
no browser console messages before publication.

| Inspected set | Retained inspection pages | Observation |
| --- | --- | --- |
| All 51 curated before/after frames | `raw/reviewer-curated-page-00.png` through `12.png` | PFT footer scale, unnamed/custom groups, diagnostic scale headers, Default marks/arrows, About, old-key picker and reopened project are visible. |
| Final prediction drive: 33 primary frames | `raw/reviewer-visible-pi-page-00.png` through `08.png` | Eighteen figures, twelve actual Tables views and three lower subgroup views. Figure navigation really displays the figure after visiting Tables. |
| Group/release drive: 28 primary frames | `raw/reviewer-group-page-00.png` through `06.png` | Unnamed Group removed, Participants retained, all three styles. Mean entered-effect output has no raw-data spanner; its custom identity is in the caption. |
| Final old-key picker | `20261015T170059Z-08042b0e-project-reviewer-groups/146-0-reviewer-legacy-default-setup.png` | Plots tab is open and explicitly shows Default. Also included in curated copies. |
| Default colour drive: 31 primary frames | `raw/reviewer-colour-page-00.png` through `07.png` | Study text stays black; blue markers, intervals, caps, diamonds and actual clipped arrows remain readable on white/zebra rows. Diagnostic, HR/IRR, single-arm and sequential/subgroup paths are represented. |
| Diagnostic drive: 29 primary frames | `raw/reviewer-diagnostic-page-00.png` through `07.png` | Logit/OR bounds fit the actual two/six-digit coefficient tables for continuous, factor and multiple moderators. Multiple-moderator report overview requires scrolling; curated Tables views show all coefficients and headers. |
| Complete SVG lower devices: 28 crops | `raw/reviewer-vector-footer-00.png` through `27.png`; pages `reviewer-footer-page-01.png` through `06.png` | First four crops viewed individually; remaining crops viewed on the six pages. Footer text, pooled/subgroup intervals, axes and lower summaries have no observed collisions. |

The vector crops are derived inspection images rendered with QtSvg 6.11.0 from the
actual native-drive SVG files, not new native screenshots. Their input/output
hashes, device sizes and steps are in `REVIEWER-VECTOR-FOOTERS.json`; exact command
and exit are in the reviewer command ledger. Native long plots legitimately scroll
(notably HR, cumulative, omission and mean outputs). A viewport screenshot alone
does not prove the offscreen footer; the full SVG checks cover that part.

Also inspected the native funnel initial view/editor at steps 4/5 of
`20261015T171752Z-8c231a80-plot-workflow-funnel` and bubble initial view/editor at
steps 7/8 of `20261015T171815Z-450b92ea-plot-workflow-regression`. Their existing
Default study/reference/regression colours already agree, so no extra colour
change was needed. The bubble legend displays blue study/line/CI samples.

Earlier images were rejected despite exit zero: the selected figure still showed
Tables, and one old-key setup frame hid the style picker on the Method tab.
`REVIEWER-VISUAL-REJECTIONS.json` retains those cases and replacements. The real
Tables-to-figure navigation defect was reproduced with a failing native assertion,
fixed in 06df415, then passed in the final prediction drive. Neither hidden-page
frames nor the hidden-picker frame are curated as proof of the missing surface.

No claim is made that every incidental setup PNG, every full-profile screenshot,
every export pixel, actual OS DPI or screen-reader behaviour was visually checked.
Four-format export parsing/sampling and native assertions have their own narrower
proof in the helper manifests. Retained Linux native Qt proof does not qualify
Windows/macOS packaging or native OS file-picker behaviour.
