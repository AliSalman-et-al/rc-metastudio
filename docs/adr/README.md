# Architecture decisions

These records state active constraints and their reasons. Update a decision when
the design changes, preserving the distinction between current policy and
historical evidence. Use [CONTEXT.md](../../CONTEXT.md) for domain terms.

| Decision | Responsibility |
| --- | --- |
| [0001: Statistical authority](0001-delegate-statistical-decisions-to-authority-packages.md) | Package calculations and small-study effects eligibility |
| [0002: Small-study effects](0002-use-a-dedicated-small-study-effects-boundary.md) | Dedicated request, package ownership and result integration |
| [0003: Effect reconstruction](0003-reconstruct-derived-effects-at-the-analysis-boundary.md) | Raw versus entered study effects |
| [0004: Joint diagnostic models](0004-use-mada-reitsma-for-joint-diagnostic-models.md) | Reitsma fitting, summaries, prediction and AUC |
| [0005: Rewrite oracle](0005-use-the-current-release-as-the-rewrite-oracle.md) | Historical rewrite baseline. Superseded by the current golden-oracle policy. |
| [0006: Stable identity](0006-separate-stable-identities-from-project-labels.md) | Renaming and project persistence |
| [0007: Real R runtime](0007-require-an-explicit-r-runtime.md) | Explicit production startup and failure |
| [0008: Analysis boundary](0008-use-a-versioned-analysis-boundary.md) | Typed requests/results and exact numerical quantities |
| [0009: Release platforms](0009-support-qualified-release-platforms.md) | Supported targets, private runtime and trust profiles |
| [0010: HR and IRR](0010-distinguish-hazard-and-incidence-rate-ratios.md) | Measures, selected sources, confidence and zero handling |
| [0011: Trial sequential analysis](0011-implement-trial-sequential-analysis-over-metafor-and-gsdesign.md) | Authority exception, owned formulas, defaults and references |
| [0012: Persistent R worker](0012-supervise-a-persistent-r-worker.md) | Process isolation, job protocol, cancellation and publication |

The documentation cleanup consolidated sixteen earlier records into the first ten. The eleventh records trial sequential analysis.
Git retains their original text and numbering; historical audit/oracle records
continue to use the identifiers they recorded at the time.
