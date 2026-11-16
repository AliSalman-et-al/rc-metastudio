I reviewed the full uncommitted diff (R, Python and `.ui` copy) against the earlier findings, read-only: no edits, agents or tests. I also read the newest rendered subgroup report, [docx.txt](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261116T135429Z-a971ddbd-audit-round3-twoarm-mean/workflow/report-retention/4ee78d8307c71adb-93892afe/docx.txt), from the current code. All the earlier blockers you listed are fixed correctly, but the latest fixes introduce three new blockers.

## Blockers

1. **Subgroup reports call the pooled total a subgroup.** The rendered report says:
   - "Heterogeneity in Overall: Q = …" ([manuscript_report.py:283](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/src/rc_metastudio/manuscript_report.py:283))
   - "Studies in Overall (k)" ([manuscript_report.py:266](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/src/rc_metastudio/manuscript_report.py:266)). It also repeats the "Studies (k)" row.
   - "Subgroup B: The 95% prediction interval was …" ([manuscript_report.py:212](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/src/rc_metastudio/manuscript_report.py:212)). This has a capital after the colon and doesn't match "In Subgroup B, the pooled …".

   The cause is that R names the last row "Overall" ([results_display.R:693](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/r/RCMetaR/R/results_display.R:693), [repeated_analyses.R:808](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/r/RCMetaR/R/repeated_analyses.R:808)). One small context rule fixes all three:
   - For "Overall": "Overall heterogeneity: …" and "Overall, the 95% prediction interval was …". Drop the Overall k row, because it equals "Studies (k)".
   - For a subgroup: "In Subgroup B, the 95% prediction interval was …".
2. **The metric submenu tooltip is broken.** It reads "Choose a two-arm metrics effect measure." because the menu names are "Two-arm metrics" and "One-arm metrics" ([main_window.py:1071](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/src/rc_metastudio/main_window.py:1071)). Strip " metrics" before formatting.
3. **A window title uses mixed case.** It shows "Change Covariate type" ([covariate_type_dialog.ui:7](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/src/rc_metastudio/forms/covariate_type_dialog.ui:7)). Change it to "Change covariate type".

## Should fix (small, and fits your stated rules)

4. **One repeated supplementary table survives.** "Subgroup summary — Test of subgroup differences" is still in Supplementary details, although Model fit's Between-group rows hold all of its values. It also uses a "p-value" header where everything else says "P". It's a known summary table and every quantity is represented, so add 'Test of subgroup differences' to the `transferred` set ([manuscript_report.py:387](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/src/rc_metastudio/manuscript_report.py:387)). That doesn't loosen the conservative rule.
5. **"could not update Open recent."** reads like a typo ([main_window.py:472](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/src/rc_metastudio/main_window.py:472)). Use "could not update the Open recent list."
6. **The R text pane still writes "Zhou-Dendukuri" with a hyphen** ([r_bridge.py:2484](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/src/rc_metastudio/r_bridge.py:2484)). The table label uses an en dash.
7. **R tests now out of date:** [test-reitsma.R:57–58](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/r/RCMetaR/tests/testthat/test-reitsma.R:57) expects "equivalent parameterizations" in the SROC AUC `note`, which was deleted, and expects the hyphenated "Zhou-Dendukuri". This isn't a copy problem, but it adds to the 5 Python failures and will block a green matrix.

## Optional editorial pass (not blocking)

- "95% confidence intervals used …" starts a sentence with a numeral. AMA/APA style would write "Confidence intervals (95%) …" or "All 95% confidence intervals …".
- "Unavailable: τ² (REML, log odds ratio) is unavailable" says "unavailable" twice ([small_study_effects.R:121](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/r/RCMetaR/R/small_study_effects.R:121)). "could not be estimated" would avoid it.
- In Supplementary details, the R model title still reads "Continuous Random-Effects Model" (and "Binary Fixed-Effect Model - Mantel-Haenszel"). Every other method label is now sentence case.
- "Subgroups by Group." in Model configuration is a fragment ([analysis_identity.py:36](/C:/Users/Ali-Salman/Documents/Code/rc-metastudio/src/rc_metastudio/analysis_identity.py:36)). "Subgroups defined by Group." would fix it.
- "Publication bias — RC MetaStudio" is the only dialog title that adds the app name.
- The `drop00` tooltip just repeats its label.
- The Delete outcome prompt says "and its rows"; "and its studies" is clearer.
- The prose prints "Q = 2.164253e-31". That comes from the fixture's digits setting, but scientific notation in prose is worth formatting later.
- The open-project error no longer names the file. The title still says what failed, so this is fine unless people open from Open recent often.
- The RCMS title has a lowercase word after the colon, unlike APA. Keep it, because it must match the Zenodo record.
- Leftover reference items: Lau 1992 is in a different citation style; *meta* has no reference (wait for an authoritative citation); the R `to` description is stale, but Python overrides it everywhere it's shown.

## Checked and fine

- **Captions, filters and prompts:**
  - File-picker captions and filters are correct.
  - The unsaved-changes prompt is neutral and has a "Don't save" button.
  - The error-message trailing space is gone.
- **Startup error:** the technical R startup cause now walks `__cause__`, and the dialog no longer repeats itself.
- **References:**
  - The six `repeated_analyses.R` sites are fixed and the definitions are deleted.
  - The label-stripping regex only removes the "Label:" prefix. It doesn't touch author names, including "Doebler, P. (2025). mada: …".
- **Parameters and method labels:**
  - Parameter descriptions are centralized and override R everywhere they're displayed.
  - Python estimator labels take priority over R's title-case names, so "restricted maximum likelihood (REML)" comes out correctly.
  - The new method labels don't collide, because R filters methods by data type.
- **Report prose:**
  - The package marker now catches "mada:".
  - The Pooled lowercasing is constrained.
  - Heterogeneity and subgroup-test sentences are generated once.
  - The F/Q wording is correct.
  - The singular and plural forms in the included/excluded sentence, the continuity-correction sentence and the small-study counts are correct.
- **Cite and APA:**
  - Italics skip the RC MetaStudio clause.
  - The APA author list is right for the current five authors.
  - The BibTeX title protects "RC MetaStudio".
- **Bibliography:** Rücker, Diseases, Harbord 2007 with its DOI, and the corrected Deeks DOI are all in place.
- **Export dialog:** the plot export dialog copy is fine.

I didn't run anything or look at screenshots. The matrices are still running, so none of this is a green result. The blocker 1 output is from a 13:54 audit run, which uses the current code. Risk: blocker 1 shows up in every subgroup report you export (PDF, DOCX and the text report).
