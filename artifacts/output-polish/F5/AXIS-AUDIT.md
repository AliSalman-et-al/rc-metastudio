# Axis label audit

In R, assigning NULL removes the exact bp_xlabel key. Reading with $ then partially matches bp_xlabel_literal, which is FALSE for an automatic label. Exact lookup allows the moderator-name fallback. Forest and SROC read labels through rcmetar.plot.axis.label, which uses exact keys. Funnels use exact lookup in their settings resolver. TSA selects its axis label from the information scale.
