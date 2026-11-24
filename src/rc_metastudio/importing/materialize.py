"""Bind normalized imports to the editable fields of a detached sheet."""

from collections.abc import Callable
from dataclasses import replace

from rc_metastudio.analysis.validation import DEFAULT_CONFIDENCE_LEVEL
from rc_metastudio.importing.field_plan import ImportFieldPlan
from rc_metastudio.importing.tabular import CsvImportResult
from rc_metastudio.project.model import Sheet
from rc_metastudio.workspace.editing import (
    WorkspaceEditingContext,
    WorkspaceEditingService,
    add_covariate,
    selected_metric,
)


def populate_imported_sheet(
    sheet: Sheet,
    source: CsvImportResult,
    plan: ImportFieldPlan,
    editing: WorkspaceEditingService,
    on_row_loaded: Callable[[int], None],
) -> list[str]:
    for name, data_type in zip(source.covariate_names, source.covariate_types, strict=True):
        add_covariate(sheet, name, data_type)
    columns = plan.columns
    sections = (*plan.sections, *range(columns.first_covariate, columns.first_covariate + len(sheet.covariates)))
    fields = [columns.editable_field(section, sheet.covariates) for section in sections]
    identities = {name: fields.index(name) for name in ("name", "year")}
    confidence = editing.confidence_settings(sheet.settings.get("confidence_level", DEFAULT_CONFIDENCE_LEVEL))
    context = replace(
        WorkspaceEditingContext.for_sheet(sheet, selected_metric(sheet), confidence),
        preserve_entered_effects_with_raw=True,
    )
    rejection, _ = editing.edit_study_identities(
        sheet,
        {row: {field: values[column] for field, column in identities.items()}
         for row, values in enumerate(source.rows)},
    )
    if rejection is not None:
        raise ValueError(rejection.message)

    warnings = []
    for row, values in enumerate(source.rows):
        for section, field, value in zip(sections, fields, values):
            if field in ("name", "year"):
                continue
            if field is None:
                raise ValueError(f"Study row {row + 1}, column {section} is calculated automatically and cannot be edited directly.")
            rejection = editing.apply_edit(sheet, row, field, context, value)
            if rejection is not None:
                message = f"Study row {row + 1}, column {section}: {rejection.message}"
                if rejection.kind == "backend":
                    raise ValueError(message)
                warnings.append(message)
        on_row_loaded(row + 1)
    return warnings
