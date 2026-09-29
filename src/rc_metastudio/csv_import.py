# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Parse CSV files into the workspace import contract."""

from __future__ import annotations

import csv
import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from rc_metastudio import tabular_data


class CsvImportError(ValueError):
    """A CSV file cannot satisfy the workspace import contract."""


_NUMERIC_MISSING_MARKERS = frozenset({"", "na", "n/a", "null"})
_NUMERIC_TEXT_CHARACTERS = frozenset("0123456789+-.,eE")


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
) -> CsvImportResult:
    """Read, normalize, and validate one CSV file."""
    with Path(path).open(newline="") as stream:
        reader = (
            csv.reader(stream, dialect="excel")
            if from_excel
            else csv.reader(stream, delimiter=delimiter, quotechar=quotechar)
        )
        headers = next(reader, []) if has_headers else []
        rows = list(reader)

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

    _normalize_and_validate_years(normalized_rows, year_column)
    _normalize_and_validate_numeric_fields(normalized_rows, expected_headers)
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
    found = ", ".join(headers[:required_count]) or "none"
    expected = ", ".join(expected_headers)
    raise CsvImportError(
        "CSV headers must start with these required columns in this order: "
        f"{expected}. Found: {found}."
    )


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


def _normalize_and_validate_years(rows: list[list[str]], year_column: int) -> None:
    for row_number, row in enumerate(rows, start=1):
        if year_column >= len(row):
            raise CsvImportError(
                f"The year at row {row_number} is missing from the CSV row."
            )
        if _is_numeric_missing(row[year_column]):
            row[year_column] = ""
            continue
        raw_year = row[year_column].strip()
        try:
            numeric_year = float(raw_year)
        except ValueError as exc:
            raise CsvImportError(
                f"The year at row {row_number} has malformed value {raw_year!r}; "
                "enter an integer year or a recognized missing marker."
            ) from exc
        except OverflowError as exc:
            raise CsvImportError(
                f"The year at row {row_number} has non-finite value {raw_year!r}; "
                "enter an integer year or a recognized missing marker."
            ) from exc
        if not math.isfinite(numeric_year):
            raise CsvImportError(
                f"The year at row {row_number} has non-finite value {raw_year!r}; "
                "enter an integer year or a recognized missing marker."
            )
        try:
            int(raw_year)
        except ValueError as exc:
            raise CsvImportError(
                f"The year at row {row_number} has invalid non-integer value "
                f"{raw_year!r}; enter an integer year or a recognized missing marker."
            ) from exc


def _normalize_and_validate_numeric_fields(
    rows: list[list[str]], expected_headers: list[str] | tuple[str, ...]
) -> None:
    for column, name in enumerate(expected_headers[2:], start=2):
        for row_number, row in enumerate(rows, start=1):
            value = row[column].strip()
            if _is_numeric_missing(value):
                row[column] = ""
                continue
            try:
                number = float(value)
            except ValueError as exc:
                raise CsvImportError(
                    f"Column {name!r} at row {row_number} has malformed numeric "
                    f"value {value!r}."
                ) from exc
            if not math.isfinite(number):
                raise CsvImportError(
                    f"Column {name!r} at row {row_number} has non-finite numeric "
                    f"value {value!r}. Use a recognized missing marker for missing data."
                )


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
    types = []
    for index in range(covariate_count):
        name = normalized_names[index]
        column = [row[offset + index] for row in rows]
        covariate_type = _covariate_type(column, name=name)
        types.append(covariate_type)
        if covariate_type == "continuous":
            for row, value in zip(rows, column):
                if _is_numeric_missing(value):
                    row[offset + index] = ""
    return normalized_names, types


def _covariate_type(values: Iterable[str], *, name: str) -> str:
    for row_number, value in enumerate(values, start=1):
        if _is_numeric_missing(value):
            continue
        normalized = value.strip()
        try:
            number = float(normalized)
        except ValueError as exc:
            if _looks_like_malformed_number(normalized):
                raise CsvImportError(
                    f"Covariate {name!r} at row {row_number} has malformed numeric "
                    f"value {normalized!r}."
                ) from exc
            return "factor"
        if not math.isfinite(number):
            raise CsvImportError(
                f"Covariate {name!r} at row {row_number} has non-finite numeric "
                f"value {normalized!r}. Use a recognized missing marker for missing data."
            )
    return "continuous"


def _is_numeric_missing(value: str) -> bool:
    return value.strip().casefold() in _NUMERIC_MISSING_MARKERS


def _looks_like_malformed_number(value: str) -> bool:
    return bool(value) and any(char.isdigit() for char in value) and all(
        char in _NUMERIC_TEXT_CHARACTERS for char in value
    )
