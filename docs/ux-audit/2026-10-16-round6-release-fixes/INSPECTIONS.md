# Personal visual inspection journal

The implementation agent opened each image listed below using view_image. Selection/decoding did not count as inspection. No caption/device/column overlap was accepted on the long-name path.

## Header blockers

- `screenshots/R6-03-R6-06-before-revman.png`: inspected the re-audit original. First arm crosses above the device and through the caption; follow-up is absent from its heading.
- `screenshots/R6-03-R6-06-after-{default,revman,bmj}-long.png`: all three native frames inspected individually. Complete follow-up is visible, caption and top clear, raw headings/rule/data separated. Type retained. Default figure is taller and uses the existing scroll viewport; complete exports inspected separately.
- `screenshots/R6-03-R6-06-after-{default,revman,bmj}-twins.png`: all three native frames inspected individually. Both full names retain their distinct follow-up/follow-through ending. Caption wraps independently and stays above both arms.
- `export-previews/{default,revman,bmj}-{long,twins}.{svg,pdf,png,tiff}.png`: **all 24 renderings opened and inspected individually**, at 1800px width (raster TIFF may retain its aspect dimensions). Full device/caption, complete arm words, raw headings, rule/data clearance, totals, interval marks and axes inspected. All pass the required clearance/identity checks visually. PDF/raster glyph appearance differs slightly from the native SVG renderer, but names remain complete and separated. Actual original exports are retained under exports/; CURATED.json binds their bytes and the preview bytes.

The full native header drive also exercises Drug/Control and unequal medium names, with assertions on display and exported SVGs. Those incidental frames remain raw, without claiming individual visual review of every incidental capture.

The 24 export checks above were performed on the rendered whole device, not just header crops. In particular the RevMan caption is above the full eight-line heading; the two-line twins caption stays above both blocks. The BMJ pooled model name wraps separately and does not cross the last study row or count total. Natural-scale ratios/intervals remain in their original rows.
