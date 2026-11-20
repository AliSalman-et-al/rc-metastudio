# BMJ forest reference audit

Reference: [metafor recreation and R code](https://www.metafor-project.org/doku.php/plots:forest_plot_bmj). The audited reference is an ordinary two-arm binary forest with inverse-variance random effects (DL) and an RD axis.

| Reference | Before | Action |
| --- | --- | --- |
| Paired event/total columns with a spanner and rule | Arm headings with an Events / Total label in each column | One count spanner and rule for a pair of binary arms. Keep the non-event column scheme for non-binary datasets. |
| Arm names below the spanner | Names printed above counts labels | Draw project arm names directly under the spanner, with wrapping for long names. |
| Same measure and method label above panel and estimate column | Separate lines with title-case method | Use the fit-derived method, sentence case and shared CI level in both positions. |
| Weight (%) and 100.0 | Already present | Preserve both. Respect the independent Weight switch. |
| Total (95% CI) and summed events / totals | Model name with bold totals | Print Total and the actual confidence level, with plain body values. The fit remains unchanged. |
| χ², df, P, I² and τ² | Shared generic heterogeneity footer | Use the BMJ footer with actual fitted statistics and a dash when heterogeneity is unavailable. |
| Overall Z and P | Shared generic footer | Use compact BMJ punctuation. Retain t/df when the model uses a t test. |
| Purple #5f4c9a and grey #a7a9ac | Different accent and grey, generic pooled dash | Use the reference palette and pooled line; explicit custom accents still work. |
| Bold heading and direction type, plain data and totals | Bold summary/total row | Draw data and totals in plain text with common row baselines. |
| Weighted purple diamonds with a 1.15× white backing | Already present in ordinary BMJ | Preserve in ordinary BMJ. Use BMJ marks in its fallback forest layouts. |
| Study or subgroup | Hard-coded for ordinary BMJ | Keep the reference heading and allow an explicit custom heading. |
| Favours labels anchored at opposite axis ends | Anchored to the null | Anchor at axis ends and wrap long labels to keep separation. Preserve user direction wording. |
| Parentheses with “to” intervals | Bracketed prediction interval | Use parentheses with “to” for BMJ intervals. |
| White ordinary plot without bands | Ordinary plot already unshaded | Preserve white background. The reference has no subgroup plot. Keep F1's bands and subtotal structure in the subgroup fallback. |
| Linear RD axis | RCMS supports RD and ratio measures | Retain the actual effect scale, including ratio log spacing with natural labels. |
