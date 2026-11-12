# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Parse CSV files into the workspace import contract."""

from __future__ import annotations

import csv
from contextlib import ExitStack
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from rc_metastudio import row_padding


class CsvImportError(ValueError):
    """A CSV file cannot satisfy the workspace import contract."""


class CsvImportPayload(TypedDict):
    """Mutable representation retained by the wizard and undo command."""

    headers: list[str]
    data: list[list[str]]
    expected_headers: list[str]
    covariate_names: list[str]
    covariate_types: list[str]


@dataclass(frozen=True, slots=True)
class CsvImportResult:
    """Normalized, validated rows ready for preview and workspace import."""

    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    expected_headers: tuple[str, ...]
    covariate_names: tuple[str, ...]
    covariate_types: tuple[str, ...]

    def to_payload(self) -> CsvImportPayload:
        return {
            "headers": list(self.headers),
            "data": [list(row) for row in self.rows],
            "expected_headers": list(self.expected_headers),
            "covariate_names": list(self.covariate_names),
            "covariate_types": list(self.covariate_types),
        }


def read_rows(
    path: str | Path,
    *,
    has_headers: bool,
    from_excel: bool,
    delimiter: str = ",",
    quotechar: str = '"',
    worksheet: str | None = None,
    year_column: int | None = None,
    numeric_columns: Iterable[int] = (),
    notices: list[str] | None = None,
) -> tuple[list[str], list[list[str]]]:
    """Read file cells, omitting fully blank rows from import and preview."""
    suffix = Path(path).suffix.lower()
    if suffix == ".xls":
        raise CsvImportError("Save this workbook as .xlsx before importing it.")
    if suffix == ".xlsx":
        headers, rows, _names, _selected = read_xlsx(path, worksheet, has_headers=has_headers, year_column=year_column, numeric_columns=numeric_columns, notices=notices)
    else:
        with Path(path).open(encoding="utf-8-sig", newline="") as stream:
            reader = (
                csv.reader(stream, dialect="excel")
                if from_excel
                else csv.reader(stream, delimiter=delimiter, quotechar=quotechar)
            )
            headers = next(reader, []) if has_headers else []
            rows = list(reader)
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    return headers, rows


def parse_csv(
    path: str | Path,
    *,
    expected_headers: list[str] | tuple[str, ...],
    has_headers: bool,
    from_excel: bool,
    delimiter: str = ",",
    quotechar: str = '"',
    year_column: int = 1,
    optional_headers: Mapping[str, str] | None = None,
    column_mapping: tuple[int, ...] | None = None,
    positional_width: int | None = None,
    header_aliases: Mapping[str, str] | None = None,
    worksheet: str | None = None,
    notices: list[str] | None = None,
) -> CsvImportResult:
    """Read and validate rows; mapping index -1 leaves an optional field empty."""
    headers, rows = read_rows(
        path, has_headers=has_headers, from_excel=from_excel,
        delimiter=delimiter, quotechar=quotechar, worksheet=worksheet,
        year_column=column_mapping[year_column] if column_mapping else year_column,
        numeric_columns=column_mapping[1:] if column_mapping else range(1, len(expected_headers)),
        notices=notices,
    )
    if has_headers and headers:
        for row_number, row in enumerate(rows, start=2):
            if len(row) > len(headers):
                raise CsvImportError(
                    f"CSV row {row_number}: expected {len(headers)} columns, found {len(row)}."
                )
    if header_aliases:
        headers = [header_aliases.get(header.casefold(), header) for header in headers]

    if column_mapping is not None:
        if not has_headers:
            raise CsvImportError("Column mapping requires a header row.")
        mapped = [index for index in column_mapping if index >= 0]
        if len(column_mapping) != len(expected_headers) or len(set(mapped)) != len(mapped):
            raise CsvImportError("Map each required field to a different CSV column.")
        if any(index < -1 or index >= len(headers) for index in column_mapping):
            raise CsvImportError("Select a CSV column for every required field.")
        indices = list(column_mapping) + [index for index in range(len(headers)) if index not in column_mapping]
        rows = [[row[index] if 0 <= index < len(row) else "" for index in indices] for row in rows]
        headers = list(expected_headers) + [headers[index] for index in indices[len(expected_headers):]]

    if has_headers:
        if headers:
            _validate_headers(headers, expected_headers)
        elif rows:
            raise CsvImportError("CSV file is missing the required header row.")
    else:
        _validate_minimum_width(rows, positional_width or len(expected_headers))
        rows = normalize_import_rows(rows, minimum_width=len(expected_headers))
    normalized_rows = normalize_import_rows(rows, minimum_width=len(headers))
    if headers:
        width = len(normalized_rows[0]) if normalized_rows else len(headers)
        headers = headers + [""] * (width - len(headers))

    if optional_headers:
        base_width = len(expected_headers)
        width = len(normalized_rows[0]) if normalized_rows else len(headers)
        optional_indices = {}
        for name in optional_headers:
            matches = [i for i, header in enumerate(headers) if header == name]
            if len(matches) > 1:
                raise CsvImportError(f"CSV contains duplicate input column: {name}.")
            optional_indices[name] = matches[0] if matches else None
        covariate_indices = [i for i in range(base_width, width) if i not in optional_indices.values()]
        expanded_rows = []
        for row in normalized_rows:
            values = row[:base_width]
            for name, default in optional_headers.items():
                index = optional_indices[name]
                values.append(default if index is None else row[index])
            expanded_rows.append(values + [row[i] for i in covariate_indices])
        normalized_rows = expanded_rows
        if has_headers:
            headers = list(expected_headers) + list(optional_headers) + [headers[i] for i in covariate_indices]
        expected_headers = list(expected_headers) + list(optional_headers)

    _validate_years(normalized_rows, year_column)
    covariate_names, covariate_types = _infer_covariates(
        normalized_rows,
        headers=headers,
        expected_headers=expected_headers,
        has_headers=has_headers,
    )
    return CsvImportResult(
        headers=tuple(headers),
        rows=tuple(tuple(row) for row in normalized_rows),
        expected_headers=tuple(expected_headers),
        covariate_names=tuple(covariate_names),
        covariate_types=tuple(covariate_types),
    )


def _validate_headers(
    headers: list[str], expected_headers: list[str] | tuple[str, ...]
) -> None:
    """Require the workspace columns to be present in the expected order."""
    required_count = len(expected_headers)
    if headers[:required_count] == list(expected_headers):
        return
    for index, expected in enumerate(expected_headers):
        found = headers[index] if index < len(headers) else "(missing)"
        if found != expected:
            raise CsvImportError(f'Column {index + 1}: expected "{expected}", found "{found}". Use the template or map this field to a CSV column.')


def _validate_minimum_width(rows: list[list[str]], minimum_width: int) -> None:
    """Reject headerless rows that cannot supply all workspace columns."""
    for row_number, row in enumerate(rows, start=1):
        if len(row) < minimum_width:
            raise CsvImportError(
                f"CSV row {row_number} needs Study and Year columns before the data columns "
                f"({minimum_width} columns in total). Use the CSV template."
            )


def normalize_import_rows(
    rows: list[list[str]] | tuple[tuple[str, ...], ...], *, minimum_width: int = 0
) -> list[list[str]]:
    """Return mutable, rectangular rows for insertion into the Qt model."""
    return row_padding.normalize_rows(
        [list(row) for row in rows], minimum_width=minimum_width
    )


def _validate_years(rows: list[list[str]], year_column: int) -> None:
    for row_number, row in enumerate(rows, start=1):
        if year_column >= len(row):
            raise CsvImportError(f"The year at row {row_number} is missing.")
        try:
            int(row[year_column])
        except ValueError as exc:
            raise CsvImportError(
                f"The year at row {row_number} is not an integer number."
            ) from exc


def _infer_covariates(
    rows: list[list[str]],
    *,
    headers: list[str],
    expected_headers: list[str] | tuple[str, ...],
    has_headers: bool,
) -> tuple[list[str], list[str]]:
    width = len(rows[0]) if rows else len(headers)
    covariate_count = max(0, width - len(expected_headers))
    if covariate_count == 0:
        return [], []

    names = headers[len(expected_headers) :] if has_headers else []
    names += [""] * (covariate_count - len(names))
    normalized_names = [
        name if name.strip() else f"Covariate {index + 1}"
        for index, name in enumerate(names[:covariate_count])
    ]
    offset = len(expected_headers)
    types = [
        _covariate_type(row[offset + index] for row in rows)
        for index in range(covariate_count)
    ]
    return normalized_names, types


def _covariate_type(values: Iterable[str]) -> str:
    # An all-missing column remains numeric until a nonnumeric value is supplied.
    for value in values:
        if not value.strip():
            continue
        try:
            float(value)
        except ValueError:
            return "factor"
    return "continuous"


MAX_IMPORT_ROWS = 100_000
MAX_IMPORT_COLUMNS = 512
MAX_IMPORT_CELLS = 1_000_000


def _xlsx_check_extent(sheet):
    rows, columns = sheet.max_row or 0, sheet.max_column or 0
    if rows > MAX_IMPORT_ROWS or columns > MAX_IMPORT_COLUMNS or rows * columns > MAX_IMPORT_CELLS:
        raise CsvImportError("Worksheet exceeds the import limit: 100,000 rows, 512 columns and 1,000,000 cells.")


def _xlsx_metadata(path, sheet, selected, row_numbers, columns, notices):
    from zipfile import ZipFile
    from xml.parsers import expat
    from openpyxl.utils.cell import range_boundaries

    imported_rows = set(row_numbers)
    hidden_rows = set()
    hidden_columns = set()

    def inspect_element(name, attrs):
        tag = name.rsplit("}", 1)[-1]
        if tag == "mergeCell":
            left, top, right, bottom = range_boundaries(attrs["ref"])
            if top <= row_numbers[-1] and bottom >= row_numbers[0] and left <= columns[-1] + 1 and right >= columns[0] + 1:
                raise CsvImportError(f"{selected}!{attrs['ref']} intersects the data; unmerge these cells first.")
        if attrs.get("hidden") not in ("1", "true"):
            return
        if tag == "row" and int(attrs["r"]) in imported_rows:
            hidden_rows.add(int(attrs["r"]))
        elif tag == "col":
            hidden_columns.update(i for i in columns if int(attrs["min"]) <= i + 1 <= int(attrs["max"]))

    # Event parsing retains no worksheet XML tree or second normal workbook.
    parser = expat.ParserCreate(namespace_separator="}")
    parser.StartElementHandler = inspect_element
    with ZipFile(path) as archive, archive.open(sheet._worksheet_path) as stream:
        parser.ParseFile(stream)
    if notices is not None:
        for count, label in ((len(hidden_rows), "row"), (len(hidden_columns), "column")):
            if count:
                notices.append(f"{count} hidden {label}{' was' if count == 1 else 's were'} imported.")


def _xlsx_cell_value(cell, cached, selected, row_index, output_column, year_column, numeric_columns, dates):
    from datetime import date, datetime
    formula = 0
    value = cell.value
    location = f"{selected}!{cell.coordinate}" if value is not None else ""
    if cell.data_type == "f":
        value = cached.value if cached is not None else None
        if value is None:
            raise CsvImportError(f"{location} has a formula with no saved value. Open and save it in Excel first.")
        formula = 1
    if row_index and output_column in numeric_columns and (cell.data_type == "e" or isinstance(value, str) and value.startswith(("#DIV/0!", "#N/A"))):
        raise CsvImportError(f"{location} contains an Excel error value.")
    if isinstance(value, (datetime, date)):
        if row_index and output_column == year_column:
            dates.append(location)
            value = str(value.year)
        else:
            value = value.isoformat()
    if isinstance(value, float):
        value = str(int(value)) if value.is_integer() else repr(value)
    return "" if value is None else str(value), formula


def _xlsx_select_sheet(book, worksheet):
    names = [sheet.title for sheet in book if sheet.sheet_state == "visible"]
    if not names:
        raise CsvImportError("This workbook has no visible worksheets.")
    if worksheet in names:
        return names, worksheet
    selected = next((name for name in names if _xlsx_has_values(book[name])), names[0])
    return names, selected


def _xlsx_has_values(sheet):
    _xlsx_check_extent(sheet)
    return any(any(cell.value is not None for cell in row) for row in sheet.iter_rows())


def _xlsx_extent(sheet):
    _xlsx_check_extent(sheet)
    row_numbers, columns = [], set()
    formulas = False
    for row_index, row in enumerate(sheet.iter_rows(), start=1):
        if row_index > MAX_IMPORT_ROWS or len(row) > MAX_IMPORT_COLUMNS or row_index * len(row) > MAX_IMPORT_CELLS:
            raise CsvImportError("Worksheet exceeds the import cell limit.")
        populated = [i for i, cell in enumerate(row) if cell.value is not None]
        if populated:
            row_numbers.append(row_index)
            columns.update(populated)
            formulas = formulas or any(row[i].data_type == "f" for i in populated)
    return row_numbers, sorted(columns), formulas


def xlsx_worksheets(path):
    """Discover selectable sheets without validating the first sheet's cells."""
    from openpyxl import load_workbook
    try:
        book = load_workbook(path, read_only=True, data_only=False)
    except Exception as exc:
        raise CsvImportError("Could not read this workbook; use an unprotected .xlsx file.") from exc
    try:
        return _xlsx_select_sheet(book, None)
    finally:
        book.close()


def read_xlsx(path, worksheet=None, *, has_headers=True, year_column=None, numeric_columns=(), notices=None):
    """Read bounded worksheet rows, preserving coordinates for actionable errors."""
    from openpyxl import load_workbook

    with ExitStack() as cleanup:
        def open_book(data_only):
            try:
                book = load_workbook(path, read_only=True, data_only=data_only)
            except Exception as exc:
                raise CsvImportError("Could not read this workbook; use an unprotected .xlsx file.") from exc
            cleanup.callback(book.close)
            return book

        book = open_book(False)
        names, selected = _xlsx_select_sheet(book, worksheet)
        sheet = book[selected]
        row_numbers, columns, has_formulas = _xlsx_extent(sheet)
        if not row_numbers:
            return [], [], names, selected
        _xlsx_metadata(path, sheet, selected, row_numbers, columns, notices)
        cached_rows = iter(open_book(True)[selected].iter_rows()) if has_formulas else None
        formulas, dates, result = 0, [], []
        for row in sheet.iter_rows():
            cached = next(cached_rows, ()) if cached_rows is not None else ()
            if not any(cell.value is not None for cell in row):
                continue
            values = []
            for output_column, i in enumerate(columns):
                value, formula = _xlsx_cell_value(
                    row[i], cached[i] if i < len(cached) else None, selected,
                    len(result) + int(not has_headers), output_column,
                    year_column, numeric_columns, dates)
                formulas += formula
                values.append(value)
            result.append(values)
        if notices is not None:
            if formulas:
                notices.append(f"{formulas} formula cells use their saved values.")
            if dates:
                notices.append("Dates use their year: " + ", ".join(dates) + ".")
        return (result[0], result[1:], names, selected) if has_headers else ([], result, names, selected)
