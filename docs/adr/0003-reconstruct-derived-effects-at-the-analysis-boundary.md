# Reconstruct derived effects at the analysis boundary

Analyses with complete compatible raw data reconstruct study effects and standard errors once at the R analysis boundary using the request's measure and preprocessing parameters. Every standard and wrapped method then consumes those same derived values. When raw data are unavailable, RCMetaR preserves entered effects and standard errors exactly and the interface disables raw-data-only controls. This removes competing edit-time and run-time effect sources while retaining intentional entered-effect analyses.

ADR-0015 qualifies source precedence for the new HR/IRR contract: IRR studies explicitly select raw data or a reported estimate when both are supplied. Existing binary, continuous, and diagnostic precedence remains as described above.
