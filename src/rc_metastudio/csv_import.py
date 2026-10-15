# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Parse CSV files into the workspace import contract."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from rc_metastudio import tabular_data


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
    header_aliases: Mapping[str, str] | None = None,
) -> CsvImportResult:
    """Read, normalize, and validate one CSV file."""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = (
            csv.reader(stream, dialect="excel")
            if from_excel
            else csv.reader(stream, delimiter=delimiter, quotechar=quotechar)
        )
        headers = next(reader, []) if has_headers else []
        rows = list(reader)
    if header_aliases:
        headers = [header_aliases.get(header.casefold(), header) for header in headers]

    if column_mapping is not None:
        if not has_headers:
            raise CsvImportError("Column mapping requires a header row.")
        if len(column_mapping) != len(expected_headers) or len(set(column_mapping)) != len(column_mapping):
            raise CsvImportError("Map each required field to a different CSV column.")
        if any(index < 0 or index >= len(headers) for index in column_mapping):
            raise CsvImportError("Select a CSV column for every required field.")
        indices = list(column_mapping) + [index for index in range(len(headers)) if index not in column_mapping]
        rows = [[row[index] if index < len(row) else "" for index in indices] for row in rows]
        headers = list(expected_headers) + [headers[index] for index in indices[len(expected_headers):]]

    if has_headers:
        if headers:
            _validate_headers(headers, expected_headers)
        elif rows:
            raise CsvImportError("CSV file is missing the required header row.")
    else:
        _validate_minimum_width(rows, len(expected_headers))
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
                f"CSV row {row_number} must contain at least {minimum_width} columns."
            )


def normalize_import_rows(
    rows: list[list[str]] | tuple[tuple[str, ...], ...], *, minimum_width: int = 0
) -> list[list[str]]:
    """Return mutable, rectangular rows for insertion into the Qt model."""
    return tabular_data.normalize_rows(
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
    for value in values:
        try:
            float(value)
        except ValueError:
            return "factor"
    return "continuous"
