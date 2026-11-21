# Sample projects

Open a bundled example from **File > Open sample project** or from the Welcome page. You can edit and analyze the sample. Save opens Save As so you can keep your own copy.

| Project | Analysis suggestion |
| --- | --- |
| [Binary - BCG vaccine and tuberculosis, Colditz 1994](<Binary - BCG vaccine and tuberculosis, Colditz 1994.rcms>) | Use this for two-arm event counts, latitude meta-regression and trial sequential analysis. |
| [Binary - Aminoglycoside dosing, Barza 1996](<Binary - Aminoglycoside dosing, Barza 1996.rcms>) | Use this for Mantel–Haenszel and Peto with studies that have zero events in both arms. |
| [Continuous - Monthly respiratory exacerbations, Poole 2003](<Continuous - Monthly respiratory exacerbations, Poole 2003.rcms>) | Use this for mean differences, trial-duration subgroups, meta-regression and small-study effects. |
| [Diagnostic accuracy - Ultrasound for deep vein thrombosis, Kearon 1998](<Diagnostic accuracy - Ultrasound for deep vein thrombosis, Kearon 1998.rcms>) | Use this for paired sensitivity and specificity, SROC, patient-group regression and Deeks’ test. |
| [Event rates (IRR) - Catheter infections, Niel-Weise 2008](<Event rates (IRR) - Catheter infections, Niel-Weise 2008.rcms>) | Use this for events per catheter-day, raw Mantel–Haenszel and reported incidence rate ratios. |
| [Reported effects - Alcohol intake and breast cancer, Greenland 1992](<Reported effects - Alcohol intake and breast cancer, Greenland 1992.rcms>) | Use this for pooling published coefficients with a confidence interval or a standard error. |
| [Single-arm mean - Handgrip strength in young adults, Abe 2025](<Single-arm mean - Handgrip strength in young adults, Abe 2025.rcms>) | Use this for pooling measured grip strength in kilograms from one cohort per study. |
| [Single-arm proportion - Depression after myocardial infarction, Feng 2019](<Single-arm proportion - Depression after myocardial infarction, Feng 2019.rcms>) | Use this for pooling a prevalence from cases and totals and comparing proportion transformations. |
| [Time-to-event (HR) - Head and neck cancer, Pignon 2000](<Time-to-event (HR) - Head and neck cancer, Pignon 2000.rcms>) | Use this for pooling hazard ratios, chemotherapy-timing subgroups and trial sequential analysis. |

See the [coverage table](COVERAGE-PLAN.md) for the analyses by project and [retained source records](sources/README.md) for the row checks and exclusions.

In the Abe handgrip project, dynamometers, measurement protocols and cohorts differ. The pooled mean is an instructional example only. One cohort consists of trained male basketball players.

The existing desktop calculator fixture exercises pre/post inputs with a paired correlation.

## Sources

- Colditz GA, Brewer TF, Berkey CS, Wilson ME, Burdick E, Fineberg HV, Mosteller F. Efficacy of BCG vaccine in the prevention of tuberculosis: meta-analysis of the published literature. JAMA. 1994;271:698–702. [Source paper](https://doi.org/10.1001/jama.1994.03510330076038) · [metadat::dat.bcg](https://wviechtb.github.io/metadat/reference/dat.bcg.html)
- Barza M, Ioannidis JP, Cappelleri JC, Lau J. Single or multiple daily doses of aminoglycosides: a meta-analysis. BMJ. 1996;312:338–345. [Source paper](https://doi.org/10.1136/bmj.312.7027.338)
- Poole PJ, Black PN. Mucolytic agents for chronic bronchitis or chronic obstructive pulmonary disease. Cochrane Database Syst Rev. 2003;1:CD001287. [Source paper](https://doi.org/10.1002/14651858.CD001287) · [metadat::dat.poole2003](https://wviechtb.github.io/metadat/reference/dat.poole2003.html)
- Kearon C, Julian JA, Newman TE, Ginsberg JS. Noninvasive diagnosis of deep venous thrombosis. Ann Intern Med. 1998;128:663–677. [Source paper](https://doi.org/10.7326/0003-4819-128-8-199804150-00011) · [metadat::dat.kearon1998](https://wviechtb.github.io/metadat/reference/dat.kearon1998.html)
- Niel-Weise BS, Stijnen T, van den Broek PJ. Anti-infective-treated central venous catheters for total parenteral nutrition or chemotherapy: a systematic review. J Hosp Infect. 2008;69:114–123. [Source paper](https://doi.org/10.1016/j.jhin.2008.02.020) · [metadat::dat.nielweise2008](https://wviechtb.github.io/metadat/reference/dat.nielweise2008.html)
- Greenland S, Longnecker MP. Methods for trend estimation from summarized dose-response data, with applications to meta-analysis. Am J Epidemiol. 1992;135:1301–1309. [Source paper](https://doi.org/10.1093/oxfordjournals.aje.a116237) · [metadat::dat.greenland1992](https://wviechtb.github.io/metadat/reference/dat.greenland1992.html)
- Abe T, Song JS, Dankel SJ, Viana RB, Abe A, Loenneke JP. Impact of potential moderating factors on absolute test-retest reliability of grip strength measurements in healthy populations: a systematic review with meta-analysis. J Sports Sci Med. 2025;24:543–554. [Source paper](https://doi.org/10.52082/jssm.2025.543)
- Feng L, Li L, Liu W, Yang J, Wang Q, Shi L, Luo M. Prevalence of depression in myocardial infarction: A PRISMA-compliant meta-analysis. Medicine. 2019;98:e14596. [Source paper](https://doi.org/10.1097/MD.0000000000014596) · [metadat::dat.feng2019](https://wviechtb.github.io/metadat/reference/dat.feng2019.html)
- Pignon JP, Bourhis J, Domenge C, Designe L. Chemotherapy added to locoregional treatment for head and neck squamous-cell carcinoma: three meta-analyses of updated individual data. Lancet. 2000;355:949–955. [Source paper](https://doi.org/10.1016/S0140-6736(00)90011-4) · [metadat::dat.pignon2000](https://wviechtb.github.io/metadat/reference/dat.pignon2000.html)
- Viechtbauer W, White T, Noble D, Senior A, Hamilton W. metadat: Meta-Analysis Datasets. R package version 1.6-0. [Package repository](https://github.com/wviechtb/metadat)

## Rebuild

From the repository root, run the builders to refresh the archives and their manifest hashes.

```powershell
uv run python scripts/build_clinical_samples.py
uv run python scripts/build_mean_sample.py
uv run python scripts/build_metafor_ratio_samples.py
```

To verify the retained R-package data, run the two source exporters with the pinned R library selected. The manual Barza and Abe extractions record the exact publication tables in their JSON files.

```powershell
& "$env:RCMS_R_HOME/bin/Rscript.exe" --vanilla scripts/export_metadat_clinical_samples.R sample_projects/sources/metadat-clinical.json
& "$env:RCMS_R_HOME/bin/Rscript.exe" --vanilla scripts/export_metafor_ratio_samples.R sample_projects/sources/metadat-ratios.json
```
