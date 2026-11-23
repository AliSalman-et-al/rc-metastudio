# Reconstruct derived effects at the analysis boundary

Analyses with complete compatible raw data reconstruct study effects and standard errors once at the R analysis boundary using the request's measure and preprocessing parameters. Every standard and wrapped method then consumes those same derived values. When raw data are unavailable, RCMetaR preserves entered effects and standard errors exactly and the interface disables raw-data-only controls. This removes competing edit-time and run-time effect sources while retaining intentional entered-effect analyses.

ADR-0010 qualifies source precedence for the HR/IRR contract: IRR studies explicitly select raw data or a reported estimate when both are supplied. Existing binary, continuous, and diagnostic precedence remains as described above.

## Individual and pooled values

Study-level corrections follow the analysis request. Mantel–Haenszel pooling
uses the uncorrected counts, and Peto and Reitsma delegate any count
transformation to their fit authority. Display eligibility can differ from
pooling eligibility. Prefer the fitted individual effect where present. Use
the prepared display effect as a fallback for rows that contributed to the fit.

Raw-data calculations in the study editor are previews. They preserve
explicitly entered effects and results already published by a meta-analysis.
Incomplete raw rows can still carry authoritative entered effects.
