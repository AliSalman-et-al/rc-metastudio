# RC MetaStudio project format

RC MetaStudio saves projects as `.rcms` files. The current format is version 3.

## Archive contents

An `.rcms` file is a ZIP archive with exactly three UTF-8 JSON members:

- `manifest.json` identifies the format and records hashes for the data members.
- `project.json` stores the analysis dataset and project content.
- `state.json` stores portable application state needed to reopen the project.

The current schemas are packaged under `src/rc_metastudio/project_schemas/v3`. They are the authoritative field-level contract. The version 1 and 2 schemas remain available at the read/migration seam.

## Compatibility

The reader accepts released structured versions for which schemas and migrations exist. It rejects unknown versions before decoding project data. Historical pickle projects are not supported.

The writer always emits the current version. Saving a loaded older structured version therefore upgrades it to the current format.

Version 1 and 2 projects migrate deterministically to version 3. Each sheet owns its study rows, outcome, arms, covariates and analysis settings. Editable names are separate from stable sheet, row, arm and covariate identities. `state.json` records the selected sheet; selecting another sheet is navigation, not an undoable document edit.

Existing binary, continuous and diagnostic inputs retain their meaning. The distinct time-to-event (HR) and event-rate (IRR) families introduced in version 2 remain supported. Each comparison's optional `ratio_inputs` record preserves its original reported scale, estimate, interval, log-SE, source confidence, selected source and shared person-time unit. Raw IRR arm data contain events and person-time. Inactive raw and reported sources survive save/reopen; read-time migration does not invent a source selection.

An originally omitted raw arm remains omitted while it is entirely blank. Measurements subsequently entered into that arm are persisted and participate in dirty tracking and undo history.

## Safety and durability

The reader validates member names, sizes, compression ratios, hashes, JSON structure, schemas, and project semantics. It rejects duplicate properties, non-finite numbers, path traversal, links, extra archive members, and resource use above the configured limits.

Saving is atomic. RC MetaStudio writes and synchronizes a temporary file in the destination directory, replaces the destination, then synchronizes the directory where the platform supports it. A failure before replacement leaves the previous project intact. A `ProjectDurabilityError` after replacement means the new file is already installed but final directory durability could not be confirmed; the application reports that distinction.

The writer produces deterministic JSON and ZIP metadata for the same project content. This makes project differences reviewable and keeps fixtures stable.

## What belongs in a project

Project files contain portable analysis data and state. Machine-specific settings, temporary output, caches, and window placement do not belong in an `.rcms` file.
