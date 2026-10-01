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
    _validate_csv_dialect(from_excel, delimiter, quotechar)
    headers, rows = _read_csv_records(
        path,
        has_headers=has_headers,
        from_excel=from_excel,
        delimiter=delimiter,
        quotechar=quotechar,
    )
    return _make_csv_source(headers, rows, has_headers)


def _validate_csv_dialect(from_excel: bool, delimiter: str, quotechar: str) -> None:
    if not from_excel and (len(delimiter) != 1 or len(quotechar) != 1):
        raise CsvImportError("Delimiter and quote character must each be one character.")


def _make_csv_source(
    headers: list[str], rows: list[list[str]], has_headers: bool
) -> CsvSourceData:
    if has_headers and not headers and rows:
        raise CsvImportError("CSV file is missing the required header row.")
    width = _source_width(headers, rows)
    headers = _complete_headers(headers, width)
    if has_headers:
        headers = [header.strip() for header in headers]
    return CsvSourceData(
        tuple(headers),
        tuple(tuple(row) for row in normalize_import_rows(rows, minimum_width=width)),
        has_headers,
    )


def _read_csv_records(
    path: str | Path,
    *,
    has_headers: bool,
    from_excel: bool,
    delimiter: str,
    quotechar: str,
) -> tuple[list[str], list[list[str]]]:
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
    return headers, rows


def _source_width(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> int:
    return max([len(headers), *(len(row) for row in rows)], default=0)


def _complete_headers(headers: list[str], width: int) -> list[str]:
    if not headers and width:
        headers = [f"Column {index + 1}" for index in range(width)]
    elif len(headers) < width:
        headers.extend([""] * (width - len(headers)))
    return headers


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
        return _positional_column_mapping(len(source.headers), len(expected_headers))
    mapping = _header_column_mapping(source.headers, expected_headers)
    if include_unmatched_as_covariates:
        mapping = [COVARIATE_TARGET if target is None else target for target in mapping]
    return tuple(mapping)


def _positional_column_mapping(
    source_count: int, expected_count: int
) -> tuple[int | str, ...]:
    return tuple(
        index if index < expected_count else COVARIATE_TARGET
        for index in range(source_count)
    )


def _header_column_mapping(
    headers: Sequence[str], expected_headers: Sequence[str]
) -> list[int | None]:
    targets: dict[str, list[int]] = defaultdict(list)
    for index, label in enumerate(expected_headers):
        targets[_normalized_header(label)].append(index)
    mapping: list[int | None] = []
    for header in headers:
        candidates = targets.get(_normalized_header(header), [])
        mapping.append(candidates.pop(0) if candidates else None)
    return mapping


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
    _validate_mapping_lengths(source, mapping, column_types)
    if not source.rows:
        return CsvImportResult((), (), expected, (), ())

    selected, covariate_sources = _select_columns(
        source, expected, mapping, column_types
    )
    study_target = _study_name_target(expected)
    if not expected or study_target not in selected:
        raise CsvImportError("Map a source column to the study-name field.", category="invalid")

    covariate_names = _unique_names([name for _index, name in covariate_sources])
    covariate_types = _covariate_types(covariate_sources, column_types)
    headers = expected + tuple(covariate_names)
    rows = _map_source_rows(
        source.rows,
        expected,
        selected,
        study_target,
        covariate_sources,
        column_types,
        len(headers),
    )
    rows = _validate_mapped_rows(
        rows, expected, covariate_sources, covariate_names, column_types
    )
    return CsvImportResult(
        headers=headers,
        rows=tuple(tuple(row) for row in rows),
        expected_headers=expected,
        covariate_names=tuple(covariate_names),
        covariate_types=tuple(covariate_types),
        missing_values=_missing_value_counts(rows, expected, covariate_names, covariate_types),
    )


def _validate_mapping_lengths(
    source: CsvSourceData,
    mapping: Sequence[int | str | None],
    column_types: Sequence[str],
) -> None:
    if len(mapping) != len(source.headers) or len(column_types) != len(source.headers):
        raise CsvImportError(
            "Choose a destination and type for every source column.", category="mapping"
        )


def _select_columns(
    source: CsvSourceData,
    expected: Sequence[str],
    mapping: Sequence[int | str | None],
    column_types: Sequence[str],
) -> tuple[dict[int, int], list[tuple[int, str]]]:
    selected: dict[int, int] = {}
    covariate_sources: list[tuple[int, str]] = []
    for source_index, (target, raw_type) in enumerate(zip(mapping, column_types)):
        _select_column(
            source_index,
            target,
            raw_type,
            source.headers[source_index],
            expected,
            selected,
            covariate_sources,
        )
    return selected, covariate_sources


def _select_column(
    source_index: int,
    target: int | str | None,
    raw_type: str,
    source_header: str,
    expected: Sequence[str],
    selected: dict[int, int],
    covariate_sources: list[tuple[int, str]],
) -> None:
    if raw_type not in COLUMN_TYPES:
        raise CsvImportError(
            f"Unknown type for source column {source_index + 1}.", category="mapping"
        )
    if target is None:
        return
    if target == COVARIATE_TARGET:
        covariate_sources.append((source_index, source_header))
        return
    if not isinstance(target, int) or not 0 <= target < len(expected):
        raise CsvImportError("A selected destination is no longer available.", category="mapping")
    if target in selected:
        raise CsvImportError(
            f"{expected[target]!r} is mapped more than once. Leave one column "
            "unmapped or import it as a covariate.",
            category="mapping",
        )
    selected[target] = source_index


def _study_name_target(expected: Sequence[str]) -> int:
    return next(
        (i for i, label in enumerate(expected) if _normalized_header(label) == "studyname"),
        0,
    )


def _covariate_types(
    covariate_sources: Sequence[tuple[int, str]], column_types: Sequence[str]
) -> list[str]:
    return [
        "continuous" if column_types[index] in {"integer", "number"} else "factor"
        for index, _name in covariate_sources
    ]


def _map_source_rows(
    source_rows: Sequence[Sequence[str]],
    expected: Sequence[str],
    selected: dict[int, int],
    study_target: int,
    covariate_sources: Sequence[tuple[int, str]],
    column_types: Sequence[str],
    width: int,
) -> list[list[str]]:
    rows: list[list[str]] = []
    for row_number, source_row in enumerate(source_rows, start=1):
        row = [""] * width
        _map_expected_columns(row, source_row, selected, study_target, row_number)
        _map_covariate_columns(row, source_row, expected, covariate_sources, column_types)
        rows.append(row)
    return rows


def _map_expected_columns(
    row: list[str],
    source_row: Sequence[str],
    selected: dict[int, int],
    study_target: int,
    row_number: int,
) -> None:
    for target, source_index in selected.items():
        value = source_row[source_index].strip()
        if target == study_target and _is_numeric_missing(value):
            raise CsvImportError(
                f"Study name is required at row {row_number}.", category="invalid"
            )
        if not _is_numeric_missing(value):
            row[target] = value


def _map_covariate_columns(
    row: list[str],
    source_row: Sequence[str],
    expected: Sequence[str],
    covariate_sources: Sequence[tuple[int, str]],
    column_types: Sequence[str],
) -> None:
    for offset, (source_index, _name) in enumerate(covariate_sources, start=len(expected)):
        value = source_row[source_index].strip()
        kind = column_types[source_index]
        if _is_missing_covariate(value, kind):
            continue
        row[offset] = value


def _is_missing_covariate(value: str, kind: str) -> bool:
    if kind in {"integer", "number"}:
        return _is_numeric_missing(value)
    return value == ""


def _validate_mapped_rows(
    rows: list[list[str]],
    expected: Sequence[str],
    covariate_sources: Sequence[tuple[int, str]],
    covariate_names: Sequence[str],
    column_types: Sequence[str],
) -> list[list[str]]:
    rows = normalize_import_rows(rows, minimum_width=len(expected) + len(covariate_sources))
    _normalize_and_validate_years(rows)
    _normalize_and_validate_numeric_fields(rows, expected)
    for offset, (source_index, name) in enumerate(covariate_sources):
        _validate_covariate_column(
            [row[len(expected) + offset] for row in rows],
            name=covariate_names[offset],
            selected_type=column_types[source_index],
        )
    return rows


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
        _count_missing_expected_fields(row, expected_headers, counts)
        _count_missing_covariates(
            row, expected_headers, covariate_names, covariate_types, counts
        )
    return tuple(sorted(counts.items()))


def _count_missing_expected_fields(
    row: Sequence[str], expected_headers: Sequence[str], counts: Counter[str]
) -> None:
    for index, field in enumerate(expected_headers[1:], start=1):
        if _is_numeric_missing(row[index]):
            counts[field] += 1


def _count_missing_covariates(
    row: Sequence[str],
    expected_headers: Sequence[str],
    covariate_names: Sequence[str],
    covariate_types: Sequence[str],
    counts: Counter[str],
) -> None:
    for offset, (name, kind) in enumerate(
        zip(covariate_names, covariate_types), start=len(expected_headers)
    ):
        if _is_counted_covariate_missing(row[offset], kind):
            counts[name] += 1


def _is_counted_covariate_missing(value: str, kind: str) -> bool:
    if kind == "continuous":
        return _is_numeric_missing(value)
    return kind == "factor" and value == ""


def _infer_column_type(values: Iterable[str]) -> CsvColumnType:
    column = [value.strip() for value in values if not _is_numeric_missing(value)]
    return _infer_non_missing_column_type(column)


def _infer_non_missing_column_type(column: Sequence[str]) -> CsvColumnType:
    if any(_is_category_label(value) for value in column):
        return "category"
    return "integer" if _all_values_are_finite_integers(column) else "number"


def _all_values_are_finite_integers(values: Sequence[str]) -> bool:
    for value in values:
        try:
            number = float(value)
        except ValueError:
            return False
        if not math.isfinite(number) or not number.is_integer():
            return False
    return True


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
