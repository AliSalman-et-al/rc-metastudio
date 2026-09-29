# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read and stage CSV rows for the workspace import contract."""

from __future__ import annotations

import csv
import math
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

from rc_metastudio import tabular_data


CsvColumnType = Literal["text", "category", "integer", "number"]
COVARIATE_TARGET = "covariate"
COLUMN_TYPES: tuple[CsvColumnType, ...] = ("text", "category", "integer", "number")
_MISSING = frozenset({"", "na", "n/a", "null"})
_NUMBER_CHARACTERS = frozenset("0123456789+-.,eE")


def column_type_label(column_type: str) -> str:
    return {
        "text": "Text",
        "category": "Category",
        "integer": "Integer",
        "number": "Number",
    }.get(column_type, column_type)


class CsvImportError(ValueError):
    """A source, mapping, or value cannot satisfy the import contract."""

    def __init__(self, message: str, *, category: str = "parsing") -> None:
        super().__init__(message)
        self.category = category


@dataclass(frozen=True, slots=True)
class CsvSourceData:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    has_headers: bool


class CsvImportPayload(TypedDict):
    """Mapped rows passed from the wizard to the staged workspace commit."""

    headers: list[str]
    data: list[list[str]]
    expected_headers: list[str]
    covariate_names: list[str]
    covariate_types: list[str]


@dataclass(frozen=True, slots=True)
class CsvImportResult:
    """Mapped preview rows and optional-value counts, ready for explicit commit."""

    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    expected_headers: tuple[str, ...]
    covariate_names: tuple[str, ...]
    covariate_types: tuple[str, ...]
    missing_values: tuple[tuple[str, int], ...] = ()

    @property
    def can_commit(self) -> bool:
        return bool(self.rows)

    def to_payload(self) -> CsvImportPayload:
        return {
            "headers": list(self.headers),
            "data": [list(row) for row in self.rows],
            "expected_headers": list(self.expected_headers),
            "covariate_names": list(self.covariate_names),
            "covariate_types": list(self.covariate_types),
        }


def read_csv(
    path: str | Path,
    *,
    has_headers: bool,
    from_excel: bool,
    delimiter: str = ",",
    quotechar: str = '"',
) -> CsvSourceData:
    """Read strict UTF-8 CSV, accepting and removing a UTF-8 BOM."""
    if not from_excel and (len(delimiter) != 1 or len(quotechar) != 1):
        raise CsvImportError("Delimiter and quote character must each be one character.")
    try:
        with Path(path).open(encoding="utf-8-sig", errors="strict", newline="") as stream:
            reader = (
                csv.reader(stream, dialect="excel", strict=True)
                if from_excel
                else csv.reader(stream, delimiter=delimiter, quotechar=quotechar, strict=True)
            )
            headers = next(reader, []) if has_headers else []
            rows = list(reader)
    except UnicodeDecodeError as exc:
        raise CsvImportError(
            "This CSV is not valid UTF-8. Save or export it as UTF-8 (a UTF-8 BOM is "
            "accepted), then select it again. Other encodings are not guessed."
        ) from exc
    except csv.Error as exc:
        raise CsvImportError(f"CSV syntax error: {exc}") from exc
    except OSError as exc:
        raise CsvImportError(f"Could not read the selected CSV file: {exc}") from exc

    if has_headers and not headers and rows:
        raise CsvImportError("CSV file is missing the required header row.")
    width = max([len(headers), *(len(row) for row in rows)], default=0)
    if not headers and width:
        headers = [f"Column {index + 1}" for index in range(width)]
    elif len(headers) < width:
        headers.extend([""] * (width - len(headers)))
    if has_headers:
        headers = [header.strip() for header in headers]
    return CsvSourceData(
        tuple(headers),
        tuple(tuple(row) for row in normalize_import_rows(rows, minimum_width=width)),
        has_headers,
    )


def infer_column_types(source: CsvSourceData) -> tuple[CsvColumnType, ...]:
    return tuple(
        _infer_column_type(row[column] for row in source.rows)
        for column in range(len(source.headers))
    )


def default_column_mapping(
    source: CsvSourceData,
    expected_headers: Sequence[str],
    *,
    include_unmatched_as_covariates: bool = False,
) -> tuple[int | str | None, ...]:
    """Match familiar labels, or positional columns when a source has no labels."""
    if not source.has_headers:
        return tuple(
            index if index < len(expected_headers) else COVARIATE_TARGET
            for index in range(len(source.headers))
        )
    targets: dict[str, list[int]] = defaultdict(list)
    for index, label in enumerate(expected_headers):
        targets[_normalized_header(label)].append(index)
    mapping: list[int | str | None] = []
    for header in source.headers:
        candidates = targets.get(_normalized_header(header), [])
        mapping.append(candidates.pop(0) if candidates else None)
    if include_unmatched_as_covariates:
        mapping = [COVARIATE_TARGET if target is None else target for target in mapping]
    return tuple(mapping)


def parse_csv(
    path: str | Path,
    *,
    expected_headers: Sequence[str],
    has_headers: bool,
    from_excel: bool,
    delimiter: str = ",",
    quotechar: str = '"',
    mapping: Sequence[int | str | None] | None = None,
    column_types: Sequence[str] | None = None,
    source: CsvSourceData | None = None,
) -> CsvImportResult:
    """Map a source table into workspace field order without touching a project."""
    source_data = source or read_csv(
        path,
        has_headers=has_headers,
        from_excel=from_excel,
        delimiter=delimiter,
        quotechar=quotechar,
    )
    if mapping is None:
        mapping = default_column_mapping(
            source_data, expected_headers, include_unmatched_as_covariates=True
        )
    if column_types is None:
        column_types = infer_column_types(source_data)
    return map_csv(source_data, expected_headers, mapping, column_types)


def map_csv(
    source: CsvSourceData,
    expected_headers: Sequence[str],
    mapping: Sequence[int | str | None],
    column_types: Sequence[str],
) -> CsvImportResult:
    """Create and validate the final rows shown in the import preview."""
    expected = tuple(expected_headers)
    if len(mapping) != len(source.headers) or len(column_types) != len(source.headers):
        raise CsvImportError("Choose a destination and type for every source column.", category="mapping")
    if not source.rows:
        return CsvImportResult((), (), expected, (), ())

    selected: dict[int, int] = {}
    covariate_sources: list[tuple[int, str]] = []
    for source_index, (target, raw_type) in enumerate(zip(mapping, column_types)):
        if raw_type not in COLUMN_TYPES:
            raise CsvImportError(
                f"Unknown type for source column {source_index + 1}.", category="mapping"
            )
        if target is None:
            continue
        if target == COVARIATE_TARGET:
            covariate_sources.append((source_index, source.headers[source_index]))
            continue
        if not isinstance(target, int) or not 0 <= target < len(expected):
            raise CsvImportError("A selected destination is no longer available.", category="mapping")
        if target in selected:
            raise CsvImportError(
                f"{expected[target]!r} is mapped more than once. Leave one column "
                "unmapped or import it as a covariate.",
                category="mapping",
            )
        selected[target] = source_index

    study_target = next(
        (i for i, label in enumerate(expected) if _normalized_header(label) == "studyname"),
        0,
    )
    if not expected or study_target not in selected:
        raise CsvImportError("Map a source column to the study-name field.", category="invalid")

    covariate_names = _unique_names([name for _index, name in covariate_sources])
    covariate_types = [
        "continuous" if column_types[index] in {"integer", "number"} else "factor"
        for index, _name in covariate_sources
    ]
    headers = expected + tuple(covariate_names)
    rows: list[list[str]] = []
    for row_number, source_row in enumerate(source.rows, start=1):
        row = [""] * len(headers)
        for target, source_index in selected.items():
            value = source_row[source_index].strip()
            if target == study_target:
                if _is_numeric_missing(value):
                    raise CsvImportError(
                        f"Study name is required at row {row_number}.", category="invalid"
                    )
                row[target] = value
                continue
            if _is_numeric_missing(value):
                continue
            if target == 1 and _normalized_header(expected[target]) == "year":
                row[target] = value
                continue
            row[target] = value

        for offset, (source_index, _name) in enumerate(covariate_sources, start=len(expected)):
            value = source_row[source_index].strip()
            kind = column_types[source_index]
            if (kind in {"integer", "number"} and _is_numeric_missing(value)) or (
                kind in {"text", "category"} and value == ""
            ):
                continue
            row[offset] = value
        if not row[study_target]:
            raise CsvImportError(f"Study name is required at row {row_number}.", category="invalid")
        rows.append(row)

    rows = normalize_import_rows(rows, minimum_width=len(headers))
    _normalize_and_validate_years(rows)
    _normalize_and_validate_numeric_fields(rows, expected)
    for offset, (source_index, name) in enumerate(covariate_sources):
        _validate_covariate_column(
            [row[len(expected) + offset] for row in rows],
            name=covariate_names[offset],
            selected_type=column_types[source_index],
        )

    return CsvImportResult(
        headers=headers,
        rows=tuple(tuple(row) for row in rows),
        expected_headers=expected,
        covariate_names=tuple(covariate_names),
        covariate_types=tuple(covariate_types),
        missing_values=_missing_value_counts(rows, expected, covariate_names, covariate_types),
    )


def normalize_import_rows(
    rows: list[list[str]] | tuple[tuple[str, ...], ...], *, minimum_width: int = 0
) -> list[list[str]]:
    """Return mutable, rectangular rows for insertion into the Qt model."""
    return tabular_data.normalize_rows([list(row) for row in rows], minimum_width=minimum_width)


def _normalize_and_validate_years(rows: list[list[str]]) -> None:
    for row_number, row in enumerate(rows, start=1):
        value = row[1].strip()
        if _is_numeric_missing(value):
            row[1] = ""
            continue
        try:
            number = float(value)
        except ValueError as exc:
            raise CsvImportError(
                f"Malformed year {value!r} at row {row_number}; enter an integer year "
                "or a recognized missing marker."
            ) from exc
        if not math.isfinite(number):
            raise CsvImportError(
                f"Year {value!r} at row {row_number} must be finite.", category="invalid"
            )
        if not number.is_integer():
            raise CsvImportError(
                f"Year {value!r} at row {row_number} must be a whole number.",
                category="invalid",
            )
        row[1] = str(int(number))


def _normalize_and_validate_numeric_fields(
    rows: list[list[str]], expected_headers: Sequence[str]
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
                    f"Malformed numeric value {value!r} in {name!r} at row {row_number}."
                ) from exc
            if not math.isfinite(number):
                raise CsvImportError(
                    f"{value!r} in {name!r} at row {row_number} is not finite.",
                    category="invalid",
                )


def _validate_covariate_column(
    values: Sequence[str], *, name: str, selected_type: str
) -> None:
    if selected_type not in {"integer", "number"}:
        return
    for row_number, value in enumerate(values, start=1):
        if _is_numeric_missing(value):
            continue
        try:
            number = float(value)
        except ValueError as exc:
            raise CsvImportError(
                f"Malformed numeric value {value!r} in covariate {name!r} at row "
                f"{row_number}."
            ) from exc
        if not math.isfinite(number):
            raise CsvImportError(
                f"{value!r} in covariate {name!r} at row {row_number} is not finite.",
                category="invalid",
            )
        if selected_type == "integer" and not number.is_integer():
            raise CsvImportError(
                f"{value!r} in covariate {name!r} at row {row_number} is not a whole "
                "number.",
                category="invalid",
            )


def _missing_value_counts(
    rows: Sequence[Sequence[str]],
    expected_headers: Sequence[str],
    covariate_names: Sequence[str],
    covariate_types: Sequence[str],
) -> tuple[tuple[str, int], ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        for index, field in enumerate(expected_headers[1:], start=1):
            if _is_numeric_missing(row[index]):
                counts[field] += 1
        for offset, (name, kind) in enumerate(zip(covariate_names, covariate_types), start=len(expected_headers)):
            if (kind == "continuous" and _is_numeric_missing(row[offset])) or (
                kind == "factor" and row[offset] == ""
            ):
                counts[name] += 1
    return tuple(sorted(counts.items()))


def _infer_column_type(values: Iterable[str]) -> CsvColumnType:
    column = [value.strip() for value in values if not _is_numeric_missing(value)]
    if any(_is_category_label(value) for value in column):
        return "category"
    numbers = []
    for value in column:
        try:
            numbers.append(float(value))
        except ValueError:
            return "number"
    return "integer" if all(math.isfinite(number) and number.is_integer() for number in numbers) else "number"


def _is_category_label(value: str) -> bool:
    if re.fullmatch(r"\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?(?:\s*(?:years?|yrs?))?", value, re.IGNORECASE):
        return True
    try:
        float(value)
    except ValueError:
        return not _looks_like_malformed_number(value)
    return False


def _normalized_header(value: str) -> str:
    compact = re.sub(r"[^a-z0-9]+", "", value.casefold())
    if compact in {"study", "studies", "studyid", "studyname", "author", "authors"}:
        return "studyname"
    if compact in {"year", "studyyear", "publicationyear"}:
        return "year"
    return compact


def _is_numeric_missing(value: str) -> bool:
    return value.strip().casefold() in _MISSING


def _looks_like_malformed_number(value: str) -> bool:
    return bool(value) and any(char.isdigit() for char in value) and all(
        char in _NUMBER_CHARACTERS for char in value
    )


def _unique_names(names: Sequence[str]) -> list[str]:
    used: set[str] = set()
    result = []
    for index, name in enumerate(names, start=1):
        base = name.strip() or f"Covariate {index}"
        candidate, suffix = base, 2
        while candidate.casefold() in used:
            candidate = f"{base} ({suffix})"
            suffix += 1
        used.add(candidate.casefold())
        result.append(candidate)
    return result
