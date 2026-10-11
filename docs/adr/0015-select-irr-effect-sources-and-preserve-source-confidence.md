# Select IRR effect sources and preserve source confidence

An IRR analysis may mix studies with raw events/person-time and studies with reported estimates. When both forms are supplied for a comparison, the user must explicitly select the statistical source; otherwise an adjusted reported effect could silently become an unadjusted ratio reconstructed from counts. This qualifies ADR-0003 for the new HR/IRR contract while preserving existing binary, continuous, and diagnostic source precedence.

Reported HR/IRR intervals retain their source confidence level, defaulting to 95%, separately from output confidence. RCMS uses metafor's log-scale Wald conversion and surfaces its warnings; changing output confidence must not change reconstructed study uncertainty or weights.

CI conversion retains the original point estimate and bounds and does not reject ordinary rounded intervals solely for a package asymmetry warning; known non-Wald intervals require a supplied log-effect SE. Each raw IRR comparison retains a declared person-time unit shared by its two groups; studies may use different units without automatic conversion. Existing study-level covariates provide optional adjustment annotations, and reversing the same group pair reciprocates an entered ratio and interval exactly while preserving SE and selected source.
