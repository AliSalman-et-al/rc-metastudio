# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Behavioral contracts for the typed CSV import parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from rc_metastudio.csv_import import CsvImportError, normalize_import_rows, parse_csv


def test_normalize_import_rows_pads_ragged_rows() -> None:
    assert normalize_import_rows([["study", "2024"], ["study-2"]], minimum_width=3) == [
        ["study", "2024", ""],
        ["study-2", "", ""],
    ]


def test_parse_csv_assigns_names_to_blank_covariates(tmp_path: Path) -> None:
    path = tmp_path / "import.csv"
    path.write_text("Study,Year,,\nA,2024,1,yes\n", encoding="utf-8")

    result = parse_csv(
        path,
        expected_headers=["Study", "Year"],
        has_headers=True,
        from_excel=False,
        year_column=1,
    )

    assert result.covariate_names == ("Covariate 1", "Covariate 2")
    assert result.covariate_types == ("continuous", "factor")


def test_parse_csv_rejects_missing_or_invalid_year(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"
    missing.write_text("Study,Year\nA\n", encoding="utf-8")
    with pytest.raises(CsvImportError, match="row 2: expected 2 columns, found 1"):
        parse_csv(
            missing,
            expected_headers=["Study", "Year"],
            has_headers=True,
            from_excel=False,
            year_column=1,
        )

    invalid = tmp_path / "invalid.csv"
    invalid.write_text("Study,Year\nA,twenty\n", encoding="utf-8")
    with pytest.raises(CsvImportError, match="year at row 1 is not an integer"):
        parse_csv(
            invalid,
            expected_headers=["Study", "Year"],
            has_headers=True,
            from_excel=False,
            year_column=1,
        )


def test_parse_csv_returns_empty_result_for_empty_input(tmp_path: Path) -> None:
    (tmp_path / "empty.csv").write_text("", encoding="utf-8")
    result = parse_csv(
        tmp_path / "empty.csv",
        expected_headers=["Study", "Year"],
        has_headers=True,
        from_excel=False,
        year_column=1,
    )

    assert result.headers == ()
    assert result.rows == ()
    assert result.covariate_names == ()
    assert result.covariate_types == ()


def test_parse_csv_rejects_blank_header_before_data(tmp_path: Path) -> None:
    path = tmp_path / "blank-header.csv"
    path.write_text("\nAlpha,2020\n", encoding="utf-8")

    with pytest.raises(CsvImportError, match="missing the required header row"):
        parse_csv(
            path,
            expected_headers=["Study", "Year"],
            has_headers=True,
            from_excel=False,
            year_column=1,
        )


def test_parse_csv_rejects_wrong_or_reordered_required_headers(tmp_path: Path) -> None:
    path = tmp_path / "wrong-headers.csv"
    path.write_text("Year,Study,Outcome\n2024,A,1\n", encoding="utf-8")

    with pytest.raises(CsvImportError, match='Column 1: expected "Study", found "Year"'):
        parse_csv(
            path,
            expected_headers=["Study", "Year", "Outcome"],
            has_headers=True,
            from_excel=False,
            year_column=1,
        )


def test_parse_csv_rejects_headerless_rows_below_required_width(
    tmp_path: Path,
) -> None:
    path = tmp_path / "narrow.csv"
    path.write_text("A,2024\n", encoding="utf-8")

    with pytest.raises(CsvImportError, match="row 1 needs Study and Year columns"):
        parse_csv(
            path,
            expected_headers=["Study", "Year", "Outcome"],
            has_headers=False,
            from_excel=False,
            year_column=1,
        )


def test_xlsx_unmapped_date_year(tmp_path: Path) -> None:
    from datetime import datetime
    from openpyxl import Workbook

    path = tmp_path / "date-year.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(["Study", "Year"])
    sheet.append(["Alpha", datetime(2022, 1, 1)])
    workbook.save(path)
    result = parse_csv(path, expected_headers=["Study", "Year"],
                       has_headers=True, from_excel=True)
    assert result.rows == (("Alpha", "2022"),)


@pytest.mark.parametrize("mapping", [None, (0, 1)])
@pytest.mark.parametrize("cells", ["A,2024,10,extra", "A,2024"])
def test_storage_boundary_csv_rejects_header_width_mismatch(tmp_path, mapping, cells):
    path = tmp_path / "width.csv"
    path.write_text("Study,Year,Dose\n" + cells + "\n", encoding="utf-8")
    with pytest.raises(CsvImportError, match="row 2.*3.*columns"):
        parse_csv(path, expected_headers=["Study", "Year"], has_headers=True,
                  from_excel=False, column_mapping=mapping)


def test_storage_boundary_csv_missing_numeric_and_verbatim_categories(tmp_path):
    path = tmp_path / "missing.csv"
    path.write_text("Study,Year,Dose,Region,Empty\nA,2024,10,North,\nB,2024,, South ,\nC,2024,20,NA,\n", encoding="utf-8")
    result = parse_csv(path, expected_headers=["Study", "Year"], has_headers=True, from_excel=False)
    assert result.covariate_types == ("continuous", "factor", "continuous")
    assert [row[2] for row in result.rows] == ["10", "", "20"]
    assert [row[3] for row in result.rows] == ["North", " South ", "NA"]
