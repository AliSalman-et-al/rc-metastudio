# Separate stable identities from project labels

Studies, outcomes, follow-ups, groups, and covariates have stable internal identities distinct from their editable names, while the rewrite continues to read and write `.rcms` v1 through the project boundary. This prevents renames from changing semantic relationships without introducing a new project format solely to persist implementation identities.

Planning clarification (2026-10-31): the opening paragraph describes the existing
v1 format, using its historical labels. Current domain vocabulary is defined in
[CONTEXT.md](../../CONTEXT.md): sheets own study rows, outcomes are endpoints,
and intervention/control columns are arms. The proposed sheet migration in
[PLAN.md](../ux-hill-climb/PLAN.md) reopens the v1 persistence choice; it has not
yet changed the format or the stable-identity requirement.
