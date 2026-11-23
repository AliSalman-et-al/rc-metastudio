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

## Workspace identity and persistence

The active sheet is persisted navigation, separate from the document's
dirty state. Imported templates and persisted column widths retain the
physical slots for both arms. Keep all arms in imported data so a later
comparison can choose any eligible pair. Publish durable undo history before
notifying visual observers, which can reenter the editing model.

Commit project data before updating machine-local recent-project metadata.
Failure of that bookkeeping cannot turn a completed save into a failed
document transaction.
