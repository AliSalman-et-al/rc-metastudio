# RC MetaStudio project format

RC MetaStudio saves projects as `.rcms` files. The current format is version 2.

## Archive contents

An `.rcms` file is a ZIP archive with three required UTF-8 JSON members and zero
or more saved-figure assets:

- `manifest.json` identifies the format and records the size and SHA-256 digest
  of each other member.
- `project.json` stores the analysis dataset, saved analysis records, and
  unfinished analysis drafts.
- `state.json` stores the active outcome, follow-up, groups, effect, and
  confidence level.
- `assets/<sha256>.(svg|png|jpg)` stores portable figures referenced by saved
  analysis records. The filename digest identifies the figure bytes.

The schemas under `src/rc_metastudio/project_schemas/v2` are the authoritative
field-level contract. Format v1 schemas remain available for migration.

## Compatibility

The reader accepts structured formats v1 and v2. It validates a v1 project,
migrates it in memory to v2, and supplies empty saved-analysis and draft lists.
The writer always emits v2. The reader rejects unknown versions before decoding
project data. Historical pickle projects are not supported.

Saving a loaded v1 project writes it in the current v2 format.

## Safety and durability

The reader validates member names, sizes, compression ratios, hashes, JSON structure, schemas, and project semantics. It rejects duplicate properties, non-finite numbers, path traversal, links, extra archive members, and resource use above the configured limits.

Saving is atomic. RC MetaStudio writes and synchronizes a temporary file in the destination directory, replaces the destination, then synchronizes the directory where the platform supports it. A failed save does not intentionally replace the previous project.

The writer produces deterministic JSON and ZIP metadata for the same project content. This makes project differences reviewable and keeps fixtures stable.

## What belongs in a project

Project files contain portable analysis data and state. Machine-specific settings, temporary output, caches, and window placement do not belong in an `.rcms` file.
