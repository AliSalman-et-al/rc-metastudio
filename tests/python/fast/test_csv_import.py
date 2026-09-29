# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Behavioral contracts for the typed CSV import parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from rc_metastudio.csv_import import (
    COVARIATE_TARGET,
    CsvImportError,
    default_column_mapping,
    infer_column_types,
    map_csv,
    normalize_import_rows,
    parse_csv,
    read_csv,
)


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
        ("twenty", "Malformed year 'twenty'"),
        ("2020.5", "must be a whole number"),
        ("Infinity", "must be finite"),
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
    )

    assert result.rows == (
        ("Alpha", "2020", ""),
        ("Beta", "2021", ""),
        ("Gamma", "2022", "0"),
    )


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("not-a-number", "Malformed numeric value 'not-a-number'"),
        ("NaN", "'NaN'.*is not finite"),
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
    )

    assert result.covariate_types == ("factor",)
    assert result.rows[1][3] == "control"


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("Infinity", "'Infinity'.*is not finite"),
        ("1.2.3", "Malformed numeric value '1.2.3'"),
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
        )


def test_parse_csv_returns_empty_result_for_empty_input(tmp_path: Path) -> None:
    (tmp_path / "empty.csv").write_text("", encoding="utf-8")
    result = parse_csv(
        tmp_path / "empty.csv",
        expected_headers=["Study", "Year"],
        has_headers=True,
        from_excel=False,
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
        )


def test_map_csv_handles_renamed_reordered_and_unmapped_source_columns(
    tmp_path: Path,
) -> None:
    path = tmp_path / "renamed-columns.csv"
    path.write_text(
        "Publication year,Lead author,Sample B,Cases B,Site,Unused\n"
        "2024,Alpha,12,2,north,ignore me\n",
        encoding="utf-8",
    )
    expected = ["Study Name", "Year", "Tx B #evts", "Tx B #total"]
    source = read_csv(path, has_headers=True, from_excel=False)
    mapping = [1, 0, 3, 2, COVARIATE_TARGET, None]

    result = map_csv(source, expected, mapping, infer_column_types(source))

    assert result.can_commit
    assert result.headers == (*expected, "Site")
    assert result.rows == (("Alpha", "2024", "2", "12", "north"),)
    assert result.covariate_names == ("Site",)
    assert result.covariate_types == ("factor",)


@pytest.mark.parametrize(
    "age_groups",
    [("18-24", "25-34", "35-44"), ("35-44", "25-34", "18-24")],
)
def test_age_range_covariate_inference_is_categorical_regardless_of_row_order(
    tmp_path: Path, age_groups: tuple[str, ...]
) -> None:
    path = tmp_path / "age-groups.csv"
    rows = "".join(
        f"Study {index},202{index},0,{age_group}\n"
        for index, age_group in enumerate(age_groups, start=1)
    )
    path.write_text("Study,Year,Outcome,Age group\n" + rows, encoding="utf-8")

    result = parse_csv(
        path,
        expected_headers=["Study", "Year", "Outcome"],
        has_headers=True,
        from_excel=False,
    )

    assert result.covariate_types == ("factor",)
    assert [row[-1] for row in result.rows] == list(age_groups)


def test_parse_csv_rejects_headerless_rows_below_required_width(
    tmp_path: Path,
) -> None:
    path = tmp_path / "narrow.csv"
    path.write_text("A,2024\n", encoding="utf-8")

    result = parse_csv(
        path,
        expected_headers=["Study", "Year", "Outcome"],
        has_headers=False,
        from_excel=False,
    )

    assert result.can_commit
    assert result.rows == (("A", "2024", ""),)
    assert result.missing_values == (("Outcome", 1),)


def test_read_csv_accepts_utf8_bom_and_rejects_other_encodings_with_recovery(
    tmp_path: Path,
) -> None:
    bom_file = tmp_path / "bom.csv"
    bom_file.write_bytes("\ufeffStudy,Year\nAlpha,2024\n".encode("utf-8"))
    source = read_csv(bom_file, has_headers=True, from_excel=False)
    assert source.headers == ("Study", "Year")

    invalid_file = tmp_path / "not-utf8.csv"
    invalid_file.write_bytes(b"Study,Year\nAlpha,\xff\n")
    with pytest.raises(CsvImportError, match="Save or export it as UTF-8"):
        read_csv(invalid_file, has_headers=True, from_excel=False)


def test_map_csv_preserves_missing_values_and_zero(tmp_path: Path) -> None:
    path = tmp_path / "missing-values.csv"
    path.write_text(
        "Study,Year,Tx A #evts,Tx A #total,Age\n"
        "Alpha,NA,0,10,\n"
        "Beta,2024,2,8,40\n",
        encoding="utf-8",
    )
    expected = ["Study Name", "Year", "Tx A #evts", "Tx A #total"]
    source = read_csv(path, has_headers=True, from_excel=False)
    defaults = list(default_column_mapping(source, expected))
    defaults[-1] = COVARIATE_TARGET
    result = map_csv(source, expected, defaults, infer_column_types(source))

    assert result.can_commit
    assert result.missing_values == (("Age", 1), ("Year", 1))
    assert result.rows[0] == ("Alpha", "", "0", "10", "")


def test_map_csv_classifies_malformed_numeric_values_as_parsing_errors(
    tmp_path: Path,
) -> None:
    expected = ["Study Name", "Year", "Tx A #evts", "Tx A #total"]
    malformed_path = tmp_path / "malformed-count.csv"
    malformed_path.write_text(
        "Study,Year,Tx A #evts,Tx A #total\nAlpha,2024,not-a-number,10\n",
        encoding="utf-8",
    )
    malformed_source = read_csv(malformed_path, has_headers=True, from_excel=False)
    with pytest.raises(CsvImportError, match="Malformed numeric") as parsing_error:
        map_csv(
            malformed_source,
            expected,
            default_column_mapping(malformed_source, expected),
            ("category", "integer", "number", "integer"),
        )
    assert parsing_error.value.category == "parsing"
