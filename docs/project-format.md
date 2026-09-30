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

## Saved results and figure edits

A saved analysis retains its scientific request, input snapshot, study order,
report, backend versions, and figure assets. Supported figures also retain a
validated JSON snapshot of their computed plotting values. Forest plots use the
original study effects, pooled estimates, intervals, weights, and subgroup or
sequential results. Regression, funnel, SROC, and coefficient figures retain
their computed coordinates and intervals.

Appearance edits redraw this snapshot without fitting the statistical model.
Each figure has its own presentation overrides. A successful edit replaces that
figure's portable assets in the saved record; its scientific request, report,
and computed snapshot remain unchanged. Concurrent edits check the record
revision and project identity before committing.

Snapshots contain data only, with a limit of 1 MB per figure and 2 MB per
analysis. They contain no serialized R model or executable code. An older
record, unsupported renderer, or oversized snapshot can still retain viewable
and exportable assets; appearance editing is unavailable with a recorded reason.

## Safety and durability

The reader validates member names, sizes, compression ratios, hashes, JSON structure, schemas, and project semantics. It rejects duplicate properties, non-finite numbers, path traversal, links, extra archive members, and resource use above the configured limits.

Saving is atomic. RC MetaStudio writes and synchronizes a temporary file in the destination directory, replaces the destination, then synchronizes the directory where the platform supports it. A failed save does not intentionally replace the previous project.

The writer produces deterministic JSON and ZIP metadata for the same project content. This makes project differences reviewable and keeps fixtures stable.

## What belongs in a project

Project files contain portable analysis data and state. Machine-specific settings, temporary output, caches, and window placement do not belong in an `.rcms` file.
