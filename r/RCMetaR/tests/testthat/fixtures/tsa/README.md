# Trial sequential analysis reference fixtures

## Observed CTU TSA 0.9.5.10 Beta results

Run on Windows with Java 25 using `java -jar TSA.jar` from the installed CTU
directory. Open the input with Ctrl+O, select **TSA → Perform calculations**,
then **Graphs → Adjusted Boundaries**. **Generate TSA Report → Create** exports
HTML settings, trial estimates and the graph. This export does not tabulate
exact per-look boundaries or cumulative Z. The following are the values
legible in the report and graph.

| Input | Settings | Observed |
| --- | --- | --- |
| Installed sample `samples/High perioperative oxygen SSI.TSA` (inputs transcribed in `oxygen.csv`) | RR, random DL, harmful outcome, empirical 0.01 zero-event setting with double zeros excluded, two-sided α = .05, β = .20, user-defined intervention 13.09%, control 16.36% and heterogeneity factor input .67, OBF alpha and beta, configured looks Greif/Belda/ENIGMA/PROXI | RIS 11172, RR 0.89 (95% CI 0.65–1.23), P = 0.4824, Q = 18.42, I² = .67, D² = .79. CTU's Z is positive in the direction favouring intervention for this harmful outcome. The [exported plot](ctu-oxygen.png) shows both wedges. |
| `cabg-mi-settings.TSA` (synthetic trials) | RR, random DL, two-sided α = .05, β = .20, control 3.9%, intervention 2.613% (33% RRR), user-defined heterogeneity 0, OBF alpha and beta, four selected looks | RIS **5972**. CTU displayed “Trials ignored in Interim Looks due to too low information use (<1.0%)” for Early (50/5972). Its Z point remained visible. The efficacy and futility curves ended at RIS. The Z-curve continued at N = 8050 and 10050. See the [window capture](ctu-cabg.png). |

The CABG probe reproduces the independently calculated 5971.500 rounded to
5972, so the manual's 5942 does not follow from the printed settings in this
version. An unrounded control proportion near 3.9187% at 33% RRR could yield
5942. The original CABG trial file and unrounded inputs are unavailable.

The oxygen sample used a user-supplied heterogeneity adjustment of .67 (67%,
despite the report's percent label). The printed incidences give an unadjusted
RIS of 3686.797 and 11172.111 with that factor. With the same incidences and its
default fitted D² of .788590, RCMetaR reports 17440 (17439.05 before rounding).
The pooled RR, conventional interval, two-sided P and reported heterogeneity
agree at CTU's printed precision. The earlier graph points are not an exact
per-look oracle. RCMetaR uses the fitted sheet model at every look, spends at
every estimable fraction, and holds the final threshold for display after the
first RIS-reaching look.

## Manual capture checklist for the remaining comparisons

Use the installed sample for the four binary variants and the supplied
`mean-difference.csv` input rows for MD. Keep each report in a new directory.
Capture the entire application window including the graph axes and RIS label.

1. Open the sample. On **Meta-analysis**, set **Effect Measure** and **Model**.
   Repeat with RR/random DL, RR/fixed MH, RD/fixed MH and OR/fixed MH. Preserve
   the sample zero-event settings. On **TSA**, select the sequential boundary
   and **Edit selected**. Set two-sided 5%, power 80%, intervention 13.09% and
   control 16.36%, OBF alpha and beta. Use model variance-based heterogeneity
   for random DL and 0% for fixed. Record the effective heterogeneity shown.
   Select all eligible interim looks in the right pane and **Perform calculations**.
2. Open **Graphs → Adjusted Boundaries** and export the report. Use graph point
   labels where available. Record the cumulative N, Z, efficacy pair and
   futility pair for each look, with graph estimates labelled as estimates.
   On **Meta-analysis → Set Confidence Intervals**, choose **α spending
   adjusted CI → Select** and select the sequential boundary. Export again
   to retain the final CI. For an earlier CI, repeat on a saved prefix of the
   input and retain the same heterogeneity and anticipated-risk assumptions.
3. For LIL, reopen the sample, set RR/fixed, then **TSA → Law of the Iterated
   Logarithm**. Set two-sided α = .05 and adjustment factor 2. Calculate and
   capture **Graphs → Penalized Tests**. Record Z and penalised Z at matching N.
4. For MD, use **File → New Meta analysis** for a two-arm continuous outcome,
   then **Trials** to enter the three rows from `mean-difference.csv`. Use
   Mean Difference/fixed, then **TSA → Alpha Spending Boundaries**, two-sided
   5%, power 80%, anticipated difference 1, variance 4, heterogeneity 0% and
   OBF alpha and beta. Save the native input and capture the same fields as
   for binary.
5. For the early and overrun behaviour, reopen `cabg-mi-settings.TSA` and
   perform calculations. Record the warning, RIS, N at each Z point and
   boundary endpoint. Try selecting the adjusted CI and record whether CTU
   returns one after the RIS. This CI check is still open.

The R numeric oracles for the remaining cases are the public method references
in `docs/research/trial-sequential-analysis-methods.md`. CTU screenshots are
retained as observations and are not digitized into exact numeric fixtures.
