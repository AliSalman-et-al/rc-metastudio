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


def test_parse_csv_normalizes_headers_and_infers_covariate_types(
    tmp_path: Path,
) -> None:
    path = tmp_path / "import.csv"
    path.write_text(
        "Study,Year,Outcome,Age,Design\n"
        "A,2024,1,42,randomized\n"
        "B,2025,0,37,observational\n",
        encoding="utf-8",
    )

    result = parse_csv(
        path,
        expected_headers=["Study", "Year", "Outcome"],
        has_headers=True,
        from_excel=False,
        year_column=1,
    )

    assert result.headers == ("Study", "Year", "Outcome", "Age", "Design")
    assert result.covariate_names == ("Age", "Design")
    assert result.covariate_types == ("continuous", "factor")
    assert result.rows[0] == ("A", "2024", "1", "42", "randomized")


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


def test_parse_csv_preserves_blank_and_recognized_missing_years(tmp_path: Path) -> None:
    path = tmp_path / "missing-years.csv"
    path.write_text(
        "Study,Year,Outcome,Dose\n"
        "Alpha,,0,0\n"
        "Beta,NA,1,12\n"
        "Gamma,2024,2,14\n"
        "Delta\n",
        encoding="utf-8",
    )

    result = parse_csv(
        path,
        expected_headers=["Study", "Year", "Outcome"],
        has_headers=True,
        from_excel=False,
        year_column=1,
    )

    assert result.rows == (
        ("Alpha", "", "0", "0"),
        ("Beta", "", "1", "12"),
        ("Gamma", "2024", "2", "14"),
        ("Delta", "", "", ""),
    )


@pytest.mark.parametrize(
    ("year", "message"),
    [
        ("twenty", "malformed value 'twenty'"),
        ("2020.5", "non-integer value '2020.5'"),
        ("Infinity", "non-finite value 'Infinity'"),
    ],
)
def test_parse_csv_reports_invalid_years_separately_from_missing(
    tmp_path: Path, year: str, message: str
) -> None:
    path = tmp_path / "invalid-year.csv"
    path.write_text(f"Study,Year\nAlpha,{year}\n", encoding="utf-8")

    with pytest.raises(CsvImportError, match=message):
        parse_csv(
            path,
            expected_headers=["Study", "Year"],
            has_headers=True,
            from_excel=False,
            year_column=1,
        )


def test_parse_csv_normalizes_missing_markers_in_numeric_data_fields(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing-numeric-data.csv"
    path.write_text(
        "Study,Year,Outcome\nAlpha,2020,NA\nBeta,2021,N/A\nGamma,2022,0\n",
        encoding="utf-8",
    )

    result = parse_csv(
        path,
        expected_headers=["Study", "Year", "Outcome"],
        has_headers=True,
        from_excel=False,
        year_column=1,
    )

    assert result.rows == (
        ("Alpha", "2020", ""),
        ("Beta", "2021", ""),
        ("Gamma", "2022", "0"),
    )


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("not-a-number", "malformed numeric value 'not-a-number'"),
        ("NaN", "non-finite numeric value 'NaN'"),
    ],
)
def test_parse_csv_reports_invalid_numeric_data_fields(
    tmp_path: Path, value: str, message: str
) -> None:
    path = tmp_path / "invalid-numeric-data.csv"
    path.write_text(f"Study,Year,Outcome\nAlpha,2020,{value}\n", encoding="utf-8")

    with pytest.raises(CsvImportError, match=message):
        parse_csv(
            path,
            expected_headers=["Study", "Year", "Outcome"],
            has_headers=True,
            from_excel=False,
            year_column=1,
        )


def test_parse_csv_ignores_numeric_missing_markers_for_type_inference(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing-moderators.csv"
    path.write_text(
        "Study,Year,Outcome,Dose,Region\n"
        "Alpha,2020,0,0,north\n"
        "Beta,2021,1,NA,south\n"
        "Gamma,2022,2, n/a ,north\n"
        "Delta,2023,3,NULL,N/A\n",
        encoding="utf-8",
    )

    result = parse_csv(
        path,
        expected_headers=["Study", "Year", "Outcome"],
        has_headers=True,
        from_excel=False,
        year_column=1,
    )

    assert result.covariate_types == ("continuous", "factor")
    assert result.rows == (
        ("Alpha", "2020", "0", "0", "north"),
        ("Beta", "2021", "1", "", "south"),
        ("Gamma", "2022", "2", "", "north"),
        ("Delta", "2023", "3", "", "N/A"),
    )


def test_parse_csv_keeps_mixed_text_values_as_a_factor_covariate(
    tmp_path: Path,
) -> None:
    path = tmp_path / "factor-covariate.csv"
    path.write_text(
        "Study,Year,Outcome,Group\nAlpha,2020,0,1\nBeta,2021,1,control\n",
        encoding="utf-8",
    )

    result = parse_csv(
        path,
        expected_headers=["Study", "Year", "Outcome"],
        has_headers=True,
        from_excel=False,
        year_column=1,
    )

    assert result.covariate_types == ("factor",)
    assert result.rows[1][3] == "control"


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("Infinity", "non-finite numeric value 'Infinity'"),
        ("1.2.3", "malformed numeric value '1.2.3'"),
    ],
)
def test_parse_csv_reports_bad_numeric_moderator_values(
    tmp_path: Path, value: str, message: str
) -> None:
    path = tmp_path / "invalid-moderator.csv"
    path.write_text(
        f"Study,Year,Outcome,Dose\nAlpha,2020,0,0\nBeta,2021,1,{value}\n",
        encoding="utf-8",
    )

    with pytest.raises(CsvImportError, match=message):
        parse_csv(
            path,
            expected_headers=["Study", "Year", "Outcome"],
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

    with pytest.raises(CsvImportError, match="required columns in this order"):
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

    with pytest.raises(CsvImportError, match="row 1 must contain at least 3 columns"):
        parse_csv(
            path,
            expected_headers=["Study", "Year", "Outcome"],
            has_headers=False,
            from_excel=False,
            year_column=1,
        )
