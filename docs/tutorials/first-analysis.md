# Your first meta-analysis

This walkthrough opens the bundled BCG vaccine trial dataset, fits a random-effects risk-ratio model, edits and exports the forest plot and written report, and optionally checks the exact numbers against a direct R script.

Use RC MetaStudio 0.7.0 or later. See [source setup](../maintaining.md#set-up-the-development-environment) to run the current checkout.

## 1. Open the bundled BCG sample

1. Launch RC MetaStudio.
2. Choose **File > Open sample project > Binary - BCG vaccine and tuberculosis, Colditz 1994** (if your Recent projects list is empty, you can also click **Open a sample project** on the Welcome page).
3. Confirm the **Tuberculosis** sheet is active. It holds **13 included trials** comparing **BCG vaccine** (first arm) with **Unvaccinated control** (second arm), recording tuberculosis events and total participants in each arm, plus latitude and allocation covariates.
4. Set the effect measure to Risk ratio via **Analysis > Effect-size tools > Two-arm metrics > Risk ratio (RR)**. Changing the effect measure updates the displayed study estimates without modifying the underlying event counts.

These counts match `metadat::dat.bcg` from Colditz et al. (1994), [doi:10.1001/jama.1994.03510330076038](https://doi.org/10.1001/jama.1994.03510330076038). See [Sample projects and sources](../../sample_projects/README.md) for all nine bundled examples and provenance.

## 2. Configure and run the analysis

Choose **Analysis > Meta-analysis…** (`Ctrl+R`). On the **Method** tab, verify or select:

| Setting | Value |
| --- | --- |
| Analysis method | Random-effects |
| Effect measure | Risk ratio |
| τ² estimator | Restricted maximum likelihood (REML) |
| Confidence level | 95% |
| Inference method (under **Advanced**) | Normal approximation |

Leave the default continuity correction (`0.5` for studies with a zero cell). All 13 BCG trials have positive counts in every cell, so no continuity correction is applied. Click **Run analysis**.

## 3. Read the forest plot and report

Select the **Forest plot** in Results. Switch to **Text report** in the left navigation tree to read the Methods, Results, numerical tables, references, and model configuration.

- **Expected pooled estimate:** **RR 0.49 (95% CI 0.34 to 0.70)** across all 13 trials, comparing tuberculosis risk in the **BCG vaccine** arm with **Unvaccinated control** (values below 1 favor vaccination).
- Read the heterogeneity statistics (`I²`, `τ²`, `Q`) alongside the pooled interval. Explore the relationship with `Absolute latitude` under **Analysis > Meta-regression…**.

## 4. Edit and export

1. Select the forest plot in the left sidebar and click **Edit plot…** (`Ctrl+E`).
2. Change the plot style (for example **Default**, **BMJ**, or **RevMan**) or figure caption, then click **Apply** to redraw the figure through R without refitting the model. Click **Cancel** to discard unapplied edits.
3. Click **Export plot…** (`Ctrl+Shift+E`) to save **PDF** or **SVG** (vector) or **PNG** or **TIFF** (raster).
4. Click **Export report…** (`Ctrl+Shift+S`) to save the full written report as **PDF** or **Word (`.docx`)**.
5. Open **Data tables (CSV)** in the sidebar to copy table cells or export exact unrounded numbers via **Export values CSV…**.

Remember that an `.rcms` project stores study data and settings, not open Results windows. If you edit the sample and save, RC MetaStudio opens **Save as…** to preserve the bundled original. Keep exported plots and reports as the record of a run, along with the application version from **Help > About RCMS…**.

## 5. Optional: verify the exact numbers in R

Readers and reviewers who want to check RC MetaStudio's output directly against `metafor` can run the companion script [`bcg-reference.R`](bcg-reference.R) from a repository checkout.

**Prerequisites:** R (`4.6.2`) with `metafor` (from [`config/r-dependencies.json`](../../config/r-dependencies.json)) plus the CRAN packages `metadat` and `jsonlite` (used only by this script to read the `.rcms` JSON and compare against `metadat::dat.bcg`).

```shell
Rscript --vanilla docs/tutorials/bcg-reference.R artifacts/bcg-reference
```

The script extracts the 13 included rows from `sample_projects/Binary - BCG vaccine and tuberculosis, Colditz 1994.rcms`, verifies every count against `metadat::dat.bcg`, fits `metafor::escalc(measure = "RR", ...)` and `metafor::rma.uni(..., method = "REML", test = "z", level = 95)`, and writes `counts.csv`, `reference.csv`, `session.txt`, and `command-and-input.txt` to a new output directory.

Expected full-precision output:

- **Risk ratio:** `0.4894209368`
- **95% CI:** `0.3440742934` to `0.6961660838`

Check `session.txt` if comparing against a different R or `metafor` version.
