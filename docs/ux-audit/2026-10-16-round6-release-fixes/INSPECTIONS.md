# Personal visual inspection journal

The implementation agent opened each image listed below using view_image. Selection/decoding did not count as inspection. No caption/device/column overlap was accepted on the long-name path.

## Header blockers

- `screenshots/R6-03-R6-06-before-revman.png`: inspected the re-audit original. First arm crosses above the device and through the caption; follow-up is absent from its heading.
- `screenshots/R6-03-R6-06-after-{default,revman,bmj}-long.png`: all three native frames inspected individually. Complete follow-up is visible, caption and top clear, raw headings/rule/data separated. Type retained. Default figure is taller and uses the existing scroll viewport; complete exports inspected separately.
- `screenshots/R6-03-R6-06-after-{default,revman,bmj}-twins.png`: all three native frames inspected individually. Both full names retain their distinct follow-up/follow-through ending. Caption wraps independently and stays above both arms.
- `export-previews/{default,revman,bmj}-{long,twins}.{svg,pdf,png,tiff}.png`: **all 24 renderings opened and inspected individually**, at 1800px width (raster TIFF may retain its aspect dimensions). Full device/caption, complete arm words, raw headings, rule/data clearance, totals, interval marks and axes inspected. All pass the required clearance/identity checks visually. PDF/raster glyph appearance differs slightly from the native SVG renderer, but names remain complete and separated. Actual original exports are retained under exports/; CURATED.json binds their bytes and the preview bytes.

The full native header drive also exercises Drug/Control and unequal medium names, with assertions on display and exported SVGs. Those incidental frames remain raw, without claiming individual visual review of every incidental capture.

The 24 export checks above were performed on the rendered whole device, not just header crops. In particular the RevMan caption is above the full eight-line heading; the two-line twins caption stays above both blocks. The BMJ pooled model name wraps separately and does not cross the last study row or count total. Natural-scale ratios/intervals remain in their original rows.

## Other native paths inspected

All nine selected re-audit before frames for R6-01/02/04/05/07/08 were opened individually. They show the blank BMJ raw header, small dialog viewports, irrational fitted ticks, extreme-column overflow, linear diagnostic OR ticks and intrcpt tokens described by the re-audit.

The four R6-01 after frames (Group/Participants × standard/subgroup), ordinary About, both reconstruction decisions, both HR/IRR exponentiated reports and both fitted PLN after frames were each opened individually. Semantic raw header/custom spanner, full ordinary-screen questions/options, readable Intercept and round exact fitted ticks are visible without the reported collisions. Subgroup total/footer content below the native viewport is backed by actual export assertions, not claimed visible in these top frames.

The first four coefficient after frames were opened: their ticks are below the native viewport. They establish the selected component and mark but are **rejected as visible-axis proof**. A targeted fresh replay records the bottom of each selected component; only those bottom frames replace the curated coefficient after views. Actual SVG coordinate checks already passed on both scales with unchanged coefficient arrays.

Final coefficient-4 bottom frames (both sensitivity/specificity × log/linear) were each opened and inspected: 0.5/1/2 have log spacing, while the linear alternatives have equal natural increments. Ticks, axis title, marks and plot title are visible without overlap. Exact fitted arrays/report text and persisted choices/Cancel are checked by the driver.

All four final IRR stress frames (raw/reported ratio × RevMan/BMJ) were opened individually. Raw time/events, estimate/CI and totals fit their columns; the tiny positive fitted bound is scientific and nonzero. Ordinary rows retain their previous fixed decimals. Compact notation is intentionally approximate presentation; stored/editable source values are checked exactly after save/reopen.

All six small-screen-3 frames were opened individually. Under explicit synthetic 360×240 available geometry, About and the binary prompt scroll to their lower content with footer controls reachable; the short continuous question and both choices fit without scrolling. These are native xcb captures under synthetic bounds, not actual OS-DPI/small-monitor qualification.
