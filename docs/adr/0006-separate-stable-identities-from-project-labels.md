# Separate stable identities from project labels

Sheets, study rows, arms and covariates have stable internal identities distinct
from editable names. Renaming a label must preserve semantic relationships.
Use the vocabulary in [CONTEXT.md](../../CONTEXT.md).

The original decision preserved version 1 persistence. The implemented sheet
migration uses version 3: sheets own independent study rows, and state stores
the selected sheet. The reader retains version 1/2 schemas and migrates their
structured content at the read boundary. This changes the persistence format
without changing the stable-identity decision. See the
[project-format reference](../project-format.md) for the supported contract.
