# File names and ownership

Use [CONTEXT.md](../CONTEXT.md) for domain terms and the
[maintainer responsibility map](maintaining.md#where-a-change-belongs) to find the
boundary responsible for a change. Name files and symbols for the responsibility
or operation they own, following established language and framework conventions.
A file's length alone is not a reason to split it.

## Module responsibilities

These owners are under `src/rc_metastudio/`:

| Owner | Responsibility |
| --- | --- |
| `application_metadata.py` | Application/organization identity and the version derived from the package version |
| `project/` | Project archive, migration, semantic validation and live study data |
| `workspace/` | Session history, sheet editing, column rules and Qt table |
| `importing/` | CSV, XLSX and RevMan project ingestion |
| `analysis/catalog.py` | Data-family IDs, supported metrics, labels and default arm names |
| `analysis/validation.py` | Numeric analysis parameter limits, validation and input predicates |
| `analysis/requests.py` | Validated analysis requests and dispatch to the R bridge |
| `results/` | Result sections, written reports, plot editors and export |
| `results/formatting.py` | Result numbers, labels, references, precision defaults and plain-text tables |
| `calculators/controls.py` | Calculator input widgets, table controls, validation and field sizing |
| `calculators/effect_readout.py` | Selected effect source, display-scale conversion and readout presentation |
| `calculators/edit_history.py` | Dialog-local edit commands and undo/redo history |

Catalogue and validation remain independent of Qt. Metadata imports the canonical
package version. Calculator readouts depend on controls; controls do not depend
on readouts or history. History needs no Qt or R dependency. Callers and Qt
Designer custom-widget headers import the owner they use directly.

## Relocation and public contracts

Move imports, dynamic symbol references, protocols, build inputs, resource paths,
manifests, tests and current documentation together. The form manifest controls
Qt Designer sources and generated module/class names. Keep public verification
and packaging commands stable.

Preserve data-family IDs, metric strings and ordering, statistical method IDs,
project/settings keys, supported input aliases, Qt identifiers and framework
overrides. Stored user names, notes and labels are data. Follow the canonical
[project-format](project-format.md) and [import](rm5-import.md) contracts rather
than introducing another migration or compatibility route.

Verify changed ownership through the affected [testing and desktop workflows](testing.md),
including calculator source selection, inactive inputs, rounding, signals,
undo/redo and persistence where applicable. Preserve frozen numerical references
and historical evidence identities. Review callers before removing an apparently
unused owner, then remove newly orphaned helpers; the [maintaining guide](maintaining.md)
covers the unused-code scan and required qualification.
