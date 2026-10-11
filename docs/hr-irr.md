# Hazard ratios and incidence rate ratios

Choose **Time-to-event and event rates** under studies with two or more groups in New Dataset, then select **HR** or **IRR** on the existing metric page. HR, IRR, and binary risk ratios are distinct measures; keep one outcome family per project.

Ready-to-open [metafor example projects](../sample_projects/README.md) are bundled in `sample_projects/`: Pignon 2000 (HR, 65 trial results) and Niel-Weise 2008 (IRR, 9 studies), with original inputs and source citations.

## Enter study data

The usual table shows **HR, Lower, Upper**, or the two groups' **Events, Person-time** followed by **IRR, Lower, Upper**. Enter reported ratios and their original interval bounds directly. The default original confidence level is 95%. Click the study row number to edit its input details.

For a reported result, choose **Ratio and confidence interval** and enter the confidence level used in the publication. Choose **Log ratio and standard error** when a log effect and its positive standard error are available. Changing the input format converts the point estimate; enter the uncertainty in the selected format. Log-input rows display as ratios in the table and are edited through the study dialog.

For raw IRR, select **Events and person-time**. Events are nonnegative integers and may include recurrent events. Person-time must be positive and use the same unit for both groups of a study. Declare that unit in the dialog; the default is person-years. Studies may use different units because each ratio compares rates within its study. RCMS does not convert units automatically.

Raw and reported IRR studies can be combined. When both inputs exist for a study, select the intended source in its dialog. Inactive inputs survive saving and reopening. An incomplete selected source never falls back to the other source.

Raw IRR rows show a transient preview using the default 0.5 correction for zero-event studies and the workspace confidence level. Studies with zero events in both groups show **Not estimable**, with dashes for interval bounds; their tooltip explains that the individual rate ratio is 0/0. Hover over a ratio cell for its source and interval details. Analysis options control the actual fit separately.

## Import CSV

Use the required columns shown by the import wizard. HR needs `Study Name,Year,HR,Lower,Upper`. IRR also needs the two groups' Events and Person-time columns before `IRR,Lower,Upper`; leave the ratio cells empty for raw studies, or the raw cells empty for reported studies.

Synthetic examples are provided for [HR](examples/hr.csv), [raw IRR](examples/irr-raw.csv), and [mixed-source IRR](examples/irr-mixed.csv). They are demonstration data, not clinical evidence. The simple examples use the default 95% source confidence; the full mixed example declares 90%.

The following named input columns are optional and can appear after the required columns, alongside covariates:

| Column | Default | Purpose |
| --- | --- | --- |
| SE of log effect | Empty | Standard error for log input |
| Input scale (ratio/log) | ratio | Original reported scale |
| Source CI (%) | 95 | Confidence of the original interval |
| Effect source (raw/reported) | Empty | IRR source; required when both inputs exist |
| Person-time unit | person-years | Shared unit for the study's two groups |

HR uses only the first three optional fields. Headerless imports use the defaults; include headers for advanced input fields. CSV values in the HR/IRR columns are original inputs on the declared scale, while copied table cells contain the displayed ratios. Save an `.rcms` project to preserve the complete original input record.

## Analyses and interpretation

Fixed and random inverse-variance meta-analysis, cumulative analysis, leave-one-out, subgroup analysis, and meta-regression use log effects and log-scale uncertainty. Reported CI conversion uses the full log interval width at the original source confidence. Selecting another analysis confidence level changes output intervals, without changing those study standard errors. Rounded/asymmetric Wald interval warnings remain in the results. Use a supplied log-effect SE for a known non-Wald interval.

Raw IRR also offers Mantel–Haenszel when every included study selects complete raw input. Pooling uses original counts and person-time. The individual displayed effects and the package's MH tests have separate zero-event handling. A subset with zero total events in either arm remains labelled non-estimable; RCMS does not substitute another estimator. MH supports fixed pooling and sequential/subgroup summaries, without a moderator model.

Forests use ratio labels and logarithmic geometry, with null ratio 1. Meta-regression reports log coefficients and SEs, plus exponentiated coefficient intervals as multiplicative changes in HR/IRR per moderator unit. Standard errors remain on the log scale.

Publication bias offers the generic eligible-study procedures: primary classical Egger, exploratory mixed-effects Egger/Begg, ordinary and contour funnels, and optional trim-and-fill sensitivity. It discloses omitted studies and requires sufficient eligible studies and precision variation. Funnels and contours are calculated on the log scale. Asymmetry is evidence of small-study effects and does not by itself establish publication bias.

HR reconstruction from log-rank/Kaplan–Meier/IPD, Poisson GLMM, and new estimators are outside this feature. See the [metafor documentation review](hr-irr-metafor-review.md) and [verification report](hr-irr-verification.md).
