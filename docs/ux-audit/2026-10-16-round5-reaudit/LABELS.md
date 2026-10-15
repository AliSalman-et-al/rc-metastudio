# Independent leftover-label review

The broad source sweep covers Python UI code, Qt forms, R render/display code, project schemas and sample manifest/archive contents. [LABEL-INVENTORY](LABEL-INVENTORY.json) classifies every one of the 137 `tx` / `[default]` / `group1` / `group2` source hits individually. All are justified internal keys, normalized form seeds, historical input aliases or sample-rename provenance; none establishes a current built-in Tx/Group1/Group2 label leak. [FORM-STRING-CANDIDATES](FORM-STRING-CANDIDATES.json) disposes of five additional None/URL candidates. This is not a guarantee about every investigator-authored title.

The current seven sample archives have a separate [content inventory](SAMPLE-INVENTORY.json) and [native open/analyze/save/reopen proof](SAMPLE-NATIVE.json). Their current clinical arm names are readable; old labels in `manifest.json` record the rename rather than define current names. Legacy user projects intentionally keep their actual stored `tx A`/`tx B` names, verified in the fresh dedicated arm-name scenario. Current and historical CSV headers both map to readable current required fields. Changing a user's stored clinical names without consent would violate the preservation requirement.

Representative reproducible searches, from the repository root:

```bash
rg -n -i '\btx\b|\btx[ab]\b|\[default\]|group[12]' src/rc_metastudio r/RCMetaR/R sample_projects
rg -n 'intrcpt|moderator|statistic|Std Error|p-value|Sens Forest|Spec Forest|DTA|fp_[a-z_]+|bp_[a-z_]+' src/rc_metastudio r/RCMetaR/R
```

The second search intentionally includes internal parameter names; its hits require tracing to a display surface. Actual native reports establish the surviving visible vocabulary in **R5-05** (`intrcpt`, diagnostic table/navigation/count headings), while R5-03 establishes the mixed numeric formatting. The 171 actual option/menu states also retain method-family terminology (“Binary” for single-arm proportion, “Continuous” for coefficient/entered effect) and an overly generic IRR Mantel–Haenszel description. These are copy/context improvements in REPORT §5. Do not globally replace internal keys or researcher covariate names to fix display text.

The human inspection and live method/editor inventories matter more than a grep count: source form seeds can be normalized before display, while raw R table headings can be generated dynamically and evade a simple literal-string filter. No source or sample data was changed by this audit.
