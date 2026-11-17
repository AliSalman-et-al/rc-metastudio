# Use the domain documentation

Before exploring or changing a domain boundary, read [CONTEXT.md](../../CONTEXT.md)
and the relevant [architecture decisions](../adr/README.md). The glossary names
projects, independent sheets, study rows, arms, outcomes and analysis quantities.
Use its terms in code, issues, proposed changes and reports.

If a needed concept is absent, check whether the existing vocabulary already
expresses it before introducing a new term. Keep resolved definitions in
`CONTEXT.md` and significant design choices in `docs/adr/`; do not create a
parallel glossary in a plan or audit report.

When proposing a change that contradicts an active ADR, identify the decision
and explain why it should be reopened. Update the decision and its callers as
part of an accepted behavior change. Historical records describe their original
revision and are not additional compatibility requirements.

[Maintaining RC MetaStudio](../maintaining.md) maps responsibilities to source
owners. [AGENTS.md](../../AGENTS.md) supplies the shared engineering rules.
