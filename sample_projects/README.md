# Sample projects

Open these `.rcms` files through RCMS **File > Open**. The original binary, continuous and diagnostic examples remain unchanged.

## Metafor HR and IRR examples

These datasets are distributed in `metadat`, the companion dataset package used by metafor. The source tables are retained in [sources/metadat-ratios.json](sources/metadat-ratios.json), exported from **metadat 1.6-0** (GPL ≥ 2). The projects use RCMS format 2; the older samples retain format 1.

| Project | Data | Preserved inputs |
| --- | --- | --- |
| [Pignon2000-HR.rcms](Pignon2000-HR.rcms) | 65 trial results on mortality with chemotherapy added to locoregional treatment for head and neck cancer | `log(HR) = OmE / V`, `SE = sqrt(1 / V)`; original observed-minus-expected deaths, variance, study IDs and chemotherapy timing |
| [NielWeise2008-IRR.rcms](NielWeise2008-IRR.rcms) | 9 studies of catheter-related bloodstream infections | Original event counts and catheter-days for anti-infective versus standard catheters |

For HR, the comparison is **locoregional treatment plus chemotherapy / locoregional treatment alone**. Study years are absent in the source and remain blank. The original order is retained; a cumulative analysis in that order is not a chronological analysis. The **Chemotherapy timing** factor supports subgroup analysis (adjuvant, neoadjuvant, concomitant). RCMS uses sequential internal study IDs while retaining the original IDs, including `26.1` and `26.2`, as a covariate and in study notes. Original numeric inputs remain available through the study dialog; the table displays HR and its calculated interval.

For IRR, the comparison is **anti-infective catheter / standard catheter** and the exposure unit is **catheter-days**. Inverse-variance fixed/random analyses and raw-data Mantel–Haenszel are available. This example has nine eligible studies, below RCMS's ten-study threshold for asymmetry tests. The upstream help page's opening description says 18 studies, but its displayed table, detailed description and installed dataset contain nine; the bundled project uses those nine rows without additions. Neither source example contains a double-zero IRR row; they should not be modified to manufacture a “Not estimable” demonstration.

## Sources and citation

- Pignon, J. P., Bourhis, J., Domenge, C., & Designe, L. (2000). *Chemotherapy added to locoregional treatment for head and neck squamous-cell carcinoma: Three meta-analyses of updated individual data.* Lancet, 355(9208), 949–955. [Original publication](https://doi.org/10.1016/S0140-6736(00)90011-4); [dataset documentation and metafor analysis](https://wviechtb.github.io/metadat/reference/dat.pignon2000.html).
- Niel-Weise, B. S., Stijnen, T., & van den Broek, P. J. (2008). *Anti-infective-treated central venous catheters for total parenteral nutrition or chemotherapy: A systematic review.* Journal of Hospital Infection, 69(2), 114–123. [Original publication](https://doi.org/10.1016/j.jhin.2008.02.020); [dataset documentation and metafor analysis](https://wviechtb.github.io/metadat/reference/dat.nielweise2008.html).
- Viechtbauer, W., White, T., Noble, D., Senior, A., & Hamilton, W. (2026). *metadat: Meta-Analysis Datasets.* R package version 1.6-0. [Package repository](https://github.com/wviechtb/metadat). The complete package citation is also retained with the source tables.

## Rebuild and verification

From the repository root, `uv run python scripts/build_metafor_ratio_samples.py` rebuilds both projects deterministically from the retained source tables and updates their archive/semantic hashes in `manifest.json`. It preserves the existing samples. To re-export the source tables, select the verified R library with `RCMS_R_LIBS`, then run:

```powershell
& 'C:/Program Files/R/R-4.6.1/bin/Rscript.exe' --vanilla scripts/export_metafor_ratio_samples.R sample_projects/sources/metadat-ratios.json
uv run python scripts/build_metafor_ratio_samples.py
```

Run `uv run python scripts/verify_rcms.py ratios-samples` through the [verification skill](../.agents/skills/verify-rcms/SKILL.md). This dedicated desktop drive opens both bundled samples, checks every original input and displayed estimate, compares fixed/random pooling with direct metafor calls (plus IRR Mantel–Haenszel), compares HR chemotherapy-timing subgroups with metafor, observes IRR asymmetry ineligibility and descriptive funnels, saves separate copies, and reopens them. Commands, runtime identity, screenshots, numerical results and saved copies are retained.
