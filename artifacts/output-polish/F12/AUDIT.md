# Plot editor fidelity audit

Status refers to source changes and existing renderer paths. Native verification receipts are listed in the summary.

| Option | Plot kinds | Result |
| --- | --- | --- |
| Preset and accent | Forest, bubble, funnel, SROC, TSA | Honored. Presets select defaults; explicit colors control the corresponding marks. |
| Point size | Forest, bubble, funnel, SROC, TSA | Forest Default now applies the multiplier to fitted-weight marks. Other renderers already consume a size value. |
| Figure title | All editable kinds | Honored in preview and in opt-in standalone exports. SROC uses its captured style caption. |
| Row order | Ordinary, leave-one-out, subgroup | Honored. Cumulative ordering requires a rerun of the statistical sequence. |
| I² column | Cumulative and leave-one-out | Honored. Hidden in the other editors. |
| Study column and heading | Ordinary, sequential and subgroup forests | Honored. Hide unsupported arm controls on sequential fits. |
| Estimate column and heading | Ordinary, sequential and subgroup forests | Fixed heading propagation. The duplicate Annotation switch is hidden in the editor. |
| Arm headings, arm switches, total count switch | Ordinary and subgroup forest | Honored where the data provide original arm columns. Hidden for sequential and coefficient figures. |
| Weight switch | Ordinary and subgroup forest | Honored across presets. Sequential estimates represent different fits, so no shared weight is implied. |
| Header visibility | Ordinary, sequential and subgroup forests | Honored. |
| Arm direction labels | Ordinary, sequential and subgroup forests | Honored when a comparative direction is defined. |
| Pooled vertical guide | Ordinary BMJ forest | Fixed. Hidden in other forest layouts. |
| X axis label, limits and ticks | Forest, coefficient, funnel, SROC and bubble | Honored where displayed. Bounds/ticks are hidden for TSA, which has a dedicated axis mode. |
| Axis transformation | Ratio/proportion forest and coefficient plots | Honored. Absent where the effect has no alternate axis. |
| Information units | TSA | Honored. |
| Fit, confidence and prediction lines/bands; legend | Bubble | Honored. |
| Y axis label | Funnel and SROC | Honored. |
| Y limits and ticks | SROC | Honored. |
| Label policy, point symbol and colors | Funnel | Honored for applicable paths. Deeks shows None/All. |
| Null and pooled guides | Ordinary, contour and trim-and-fill funnels | Fixed as independent controls. Hidden on Deeks. |
| Regression guide | Deeks | Honored. Hidden in the other funnel variants. |
| Sampling confidence, region and τ² | Ordinary and trim-fill funnels | Honored. Region switch hidden in contour funnels. Sampling level selects the outside-label policy there; the contour geometry uses contour levels. |
| Contour levels | Contour funnel | Honored. Hidden elsewhere. |
| Curve styles/colors, confidence and prediction regions, summary point, AUC, legends, marker area and study labels | SROC | Honored against stored fitted geometry. |
| Extrapolate fit | SROC | Hidden. The editor uses the saved curve geometry; extrapolation is a fit-production option. |
| Reset to defaults | All editable kinds | Loads the initial values of the current analysis into the draft. Apply or OK commits. |
