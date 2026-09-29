# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Behavioral checks for CSV wizard input state and controls."""

from __future__ import annotations

import os
from pathlib import Path
from typing import cast
import xml.etree.ElementTree as ET

import pytest
from PyQt6 import QtCore

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()


def _new_csv_wizard(dataset_info=None):
    from rc_metastudio import main_wizard

    wizard = main_wizard.MainWizard(path="csv_import")
    wizard.set_dataset_info(
        dataset_info
        or {
            "arms": "two",
            "data_type": "binary",
            "sub_type": "proportions",
            "effect": "OR",
            "metric_choices": [],
        }
    )
    outcome_page = wizard.page(main_wizard.Page_OutcomeName)
    assert isinstance(outcome_page, main_wizard.OutcomeNamePage)
    outcome_page.outcome_name_LineEdit.setText("Outcome")
    page = wizard.page(main_wizard.Page_CsvImport)
    assert isinstance(page, main_wizard.CsvImportPage)
    page.initializePage()
    return wizard, page


def _write_csv(path, *, quoted_study=False):
    study = '"Alpha, study"' if quoted_study else "Alpha"
    path.write_text(
        "Study Name,Year,Tx A #evts,Tx A #total,Tx B #evts,Tx B #total,OR,Lower,Upper\n"
        f"{study},2020,1,10,2,12,,,\n",
        encoding="utf-8",
    )


def test_csv_quote_label_targets_quote_character_field(qapp):
    del qapp
    form = (
        Path(__file__).resolve().parents[3]
        / "src/rc_metastudio/forms/csv_import_page.ui"
    )
    root = ET.parse(form).getroot()
    label = root.find(".//widget[@name='label_2']")
    assert label is not None
    buddy = label.find("./property[@name='buddy']/cstring")
    assert buddy is not None
    assert buddy.text == "quotechar_le"


def test_csv_schema_tables_keep_readable_columns_and_own_overflow(
    tmp_path, qapp
):
    from PyQt6 import QtWidgets
    from rc_metastudio import main_wizard

    csv_path = tmp_path / "readable-schema.csv"
    _write_csv(csv_path)
    wizard, page = _new_csv_wizard()
    try:
        for table in (page.required_fmt_table,):
            header = table.horizontalHeader()
            assert (
                table.horizontalScrollBarPolicy()
                == QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            for column in range(table.columnCount()):
                assert (
                    header.sectionResizeMode(column)
                    == QtWidgets.QHeaderView.ResizeMode.Interactive
                )
                label = table.horizontalHeaderItem(column)
                assert label is not None
                assert table.columnWidth(column) >= table.fontMetrics().horizontalAdvance(
                    label.text()
                )

        wizard.setStartId(main_wizard.Page_CsvImport)
        wizard.restart()
        page = wizard.page(main_wizard.Page_CsvImport)
        assert isinstance(page, main_wizard.CsvImportPage)
        page.file_path = str(csv_path)
        page._rebuild_display()
        assert page.imported_data_ok
        table = page.preview_table
        header = table.horizontalHeader()
        for column in range(table.columnCount()):
            assert (
                header.sectionResizeMode(column)
                == QtWidgets.QHeaderView.ResizeMode.Interactive
            )
            label = table.horizontalHeaderItem(column)
            assert label is not None
            assert table.columnWidth(column) >= table.fontMetrics().horizontalAdvance(
                label.text()
            )

        wizard.show()
        qapp.processEvents()
        wizard.resize(560, 400)
        qapp.processEvents()
        assert table.horizontalScrollBar().maximum() > 0
        footer = wizard.button(QtWidgets.QWizard.WizardButton.FinishButton)
        page_scroll = page.pageScrollArea
        assert footer is not None and footer.isVisible()
        assert not page_scroll.isAncestorOf(footer)
    finally:
        wizard.close()
        qapp.processEvents()


def test_csv_input_changes_clear_stale_payload_until_reparse(tmp_path, monkeypatch, qapp):
    from rc_metastudio import main_wizard

    csv_path = tmp_path / "studies.csv"
    _write_csv(csv_path)
    wizard, page = _new_csv_wizard()
    shown = []
    monkeypatch.setattr(
        main_wizard.QFileDialog,
        "getOpenFileName",
        lambda **_kwargs: (str(csv_path), "csv files (*.csv)"),
    )
    monkeypatch.setattr(
        main_wizard.QMessageBox,
        "warning",
        lambda *args, **_kwargs: shown.append(args),
    )
    try:
        page._select_file()
        assert page.isComplete()
        assert wizard.get_csv_data() is not None

        page.delimter_le.setText(";")

        assert "study-name field" in page.review_status_label.text()
        assert not page.isComplete()
        assert wizard.get_csv_data() is None
        assert wizard.get_results()["csv_data"] is None

        page.delimter_le.setText(",")
        assert page.isComplete()
        assert wizard.get_csv_data() is not None
    finally:
        wizard.close()
        qapp.processEvents()


def test_csv_file_selection_cancel_clears_previous_payload(tmp_path, monkeypatch, qapp):
    from rc_metastudio import main_wizard

    csv_path = tmp_path / "studies.csv"
    _write_csv(csv_path)
    wizard, page = _new_csv_wizard()
    selections = iter(((str(csv_path), "csv files (*.csv)"), ("", "csv files (*.csv)")))
    monkeypatch.setattr(
        main_wizard.QFileDialog,
        "getOpenFileName",
        lambda **_kwargs: next(selections),
    )
    try:
        page._select_file()
        assert page.isComplete()
        assert wizard.get_csv_data() is not None

        page._select_file()

        assert not page.isComplete()
        assert wizard.get_csv_data() is None
        assert page.preview_table.rowCount() == 0
    finally:
        wizard.close()
        qapp.processEvents()


def test_csv_excel_mode_disables_custom_dialect_controls(qapp):
    wizard, page = _new_csv_wizard()
    try:
        assert page.delimter_le.isEnabled()
        assert page.quotechar_le.isEnabled()
        assert page.delimiter_label.isEnabled()
        assert page.label_2.isEnabled()

        page.from_excel_chkbx.setChecked(True)
        assert not page.delimter_le.isEnabled()
        assert not page.quotechar_le.isEnabled()
        assert not page.delimiter_label.isEnabled()
        assert not page.label_2.isEnabled()

        page.from_excel_chkbx.setChecked(False)
        assert page.delimter_le.isEnabled()
        assert page.quotechar_le.isEnabled()
        assert page.delimiter_label.isEnabled()
        assert page.label_2.isEnabled()
    finally:
        wizard.close()
        qapp.processEvents()


def test_csv_quote_change_reparses_and_invalidates_payload(
    tmp_path, monkeypatch, qapp
):
    from rc_metastudio import main_wizard

    csv_path = tmp_path / "quoted-studies.csv"
    _write_csv(csv_path, quoted_study=True)
    wizard, page = _new_csv_wizard()
    shown = []
    monkeypatch.setattr(
        main_wizard.QFileDialog,
        "getOpenFileName",
        lambda **_kwargs: (str(csv_path), "csv files (*.csv)"),
    )
    monkeypatch.setattr(
        main_wizard.QMessageBox,
        "warning",
        lambda *args, **_kwargs: shown.append(args),
    )
    try:
        page._select_file()
        assert page.isComplete()
        assert wizard.get_csv_data() is not None

        page.quotechar_le.setText("'")

        assert "parsing" in page.review_status_label.text().casefold()
        assert not page.isComplete()
        assert wizard.get_csv_data() is None
    finally:
        wizard.close()
        qapp.processEvents()


def test_csv_mapping_reviews_renamed_reordered_and_unmapped_columns(
    tmp_path, monkeypatch, qapp
):
    from rc_metastudio import main_wizard

    csv_path = tmp_path / "source-columns.csv"
    csv_path.write_text(
        "Author,Publication year,B total,B events,A events,A total,Odds ratio,CI lower,CI upper,Age group,Dose,Notes\n"
        "Alpha,NA,12,2,1,10,1.5,0.8,2.3,18-24,5.5,not imported\n",
        encoding="utf-8",
    )
    wizard, page = _new_csv_wizard()
    monkeypatch.setattr(
        main_wizard.QFileDialog,
        "getOpenFileName",
        lambda **_kwargs: (str(csv_path), "csv files (*.csv)"),
    )
    try:
        page._select_file()
        expected_targets = {
            "B total": "Tx B #total",
            "B events": "Tx B #evts",
            "A events": "Tx A #evts",
            "A total": "Tx A #total",
            "Odds ratio": "OR",
            "CI lower": "Lower",
            "CI upper": "Upper",
        }
        for row in range(page.mapping_table.rowCount()):
            source_label = page.mapping_table.item(row, 0).text()
            source_name = source_label.split(" (column ", maxsplit=1)[0]
            if source_name in expected_targets:
                mapping_combo = page.mapping_table.cellWidget(row, 2)
                target = page.required_header_labels.index(expected_targets[source_name])
                mapping_combo.setCurrentIndex(mapping_combo.findData(target))
            elif source_name == "Notes":
                mapping_combo = page.mapping_table.cellWidget(row, 2)
                mapping_combo.setCurrentIndex(mapping_combo.findData(None))

        dose_row = next(
            row
            for row in range(page.mapping_table.rowCount())
            if page.mapping_table.item(row, 0).text().startswith("Dose ")
        )
        type_combo = page.mapping_table.cellWidget(dose_row, 3)
        assert type_combo.currentData() == "number"
        type_combo.setCurrentIndex(type_combo.findData("category"))

        assert page.isComplete()
        payload = wizard.get_csv_data()
        assert payload["headers"] == [
            *page.required_header_labels,
            "Age group",
            "Dose",
        ]
        assert payload["data"] == [
            ["Alpha", "", "1", "10", "2", "12", "1.5", "0.8", "2.3", "18-24", "5.5"]
        ]
        assert payload["covariate_types"] == ["factor", "factor"]
        assert "not imported" not in str(payload["data"])
        assert "Year: 1 missing" in page.missing_values_label.text()
        assert wizard.button(main_wizard.QWizard.WizardButton.FinishButton).text() == (
            "Import reviewed data"
        )
    finally:
        wizard.close()
        qapp.processEvents()


def test_csv_domain_error_blocks_commit_until_mapping_is_corrected(
    tmp_path, monkeypatch, qapp
):
    from rc_metastudio import main_wizard

    csv_path = tmp_path / "out-of-range-count.csv"
    csv_path.write_text(
        "Study Name,Year,Tx A #evts,Tx A #total,Tx B #evts,Tx B #total,OR,Lower,Upper\n"
        "Alpha,2024,11,10,2,12,1.5,0.8,2.3\n",
        encoding="utf-8",
    )
    wizard, page = _new_csv_wizard()
    monkeypatch.setattr(
        main_wizard.QFileDialog,
        "getOpenFileName",
        lambda **_kwargs: (str(csv_path), "csv files (*.csv)"),
    )
    try:
        page._select_file()
        assert not page.isComplete()
        assert page.preview_table.rowCount() == 0
        assert "invalid" in page.review_status_label.text().casefold()
        assert "events cannot be greater" in page.review_status_label.text().casefold()
        assert wizard.get_csv_data() is None

        events_column = next(
            row
            for row in range(page.mapping_table.rowCount())
            if page.mapping_table.item(row, 0).text().startswith("Tx A #evts ")
        )
        total_column = next(
            row
            for row in range(page.mapping_table.rowCount())
            if page.mapping_table.item(row, 0).text().startswith("Tx A #total ")
        )
        events_mapping = page.mapping_table.cellWidget(events_column, 2)
        total_mapping = page.mapping_table.cellWidget(total_column, 2)
        events_target = page.required_header_labels.index("Tx A #total")
        total_target = page.required_header_labels.index("Tx A #evts")
        events_mapping.setCurrentIndex(events_mapping.findData(events_target))
        total_mapping.setCurrentIndex(total_mapping.findData(total_target))

        assert page.isComplete()
        assert page.csv_data()["data"][0][2:6] == ["10", "11", "2", "12"]
    finally:
        wizard.close()
        qapp.processEvents()


def test_outcome_name_page_rejects_whitespace_only_names(qapp):
    from rc_metastudio import main_wizard

    wizard = main_wizard.MainWizard(path="new_dataset")
    page = wizard.page(main_wizard.Page_OutcomeName)
    assert isinstance(page, main_wizard.OutcomeNamePage)
    try:
        page.outcome_name_LineEdit.setText(" \t ")
        assert not page.isComplete()

        page.outcome_name_LineEdit.setText("  Outcome  ")
        assert page.isComplete()
    finally:
        wizard.close()
        qapp.processEvents()


def test_staged_import_rejects_malformed_row_shape(qapp):
    del qapp
    from rc_metastudio import csv_import, main_wizard

    result = csv_import.CsvImportResult(
        headers=("Study Name", "Year"),
        rows=(("Alpha",),),
        expected_headers=("Study Name", "Year"),
        covariate_names=(),
        covariate_types=(),
    )
    dataset_info = {"name": "Outcome", "data_type": "binary"}
    payload = cast(csv_import.CsvImportPayload, result.to_payload())
    payload["data"] = [None]

    with pytest.raises(csv_import.CsvImportError, match="staged rows"):
        main_wizard.build_staged_import_model(payload, dataset_info)


def test_complete_csv_rows_stage_without_starting_r(monkeypatch, qapp):
    del qapp
    from rc_metastudio import csv_import, main_wizard, r_bridge

    result = csv_import.CsvImportResult(
        headers=(
            "Study Name", "Year", "Tx A #evts", "Tx A #total",
            "Tx B #evts", "Tx B #total", "OR", "Lower", "Upper",
        ),
        rows=(("Alpha", "2020", "1", "10", "2", "12", "", "", ""),),
        expected_headers=(
            "Study Name", "Year", "Tx A #evts", "Tx A #total",
            "Tx B #evts", "Tx B #total", "OR", "Lower", "Upper",
        ),
        covariate_names=(),
        covariate_types=(),
    )
    monkeypatch.setattr(
        r_bridge,
        "effect_for_study",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("CSV validation must not calculate effects in the GUI")
        ),
    )

    model = main_wizard.build_staged_import_model(
        result,
        {
            "name": "Outcome", "arms": "two", "data_type": "binary",
            "sub_type": "proportions", "effect": "OR", "metric_choices": [],
        },
    )

    assert model.dataset.studies[0].include is True
    assert model.take_pending_raw_previews()[0].raw_data == (1.0, 10.0, 2.0, 12.0)


def test_staged_import_wraps_covariate_creation_errors(monkeypatch, qapp):
    from rc_metastudio import csv_import, main_wizard

    result = csv_import.CsvImportResult(
        headers=("Study Name", "Year", "Dose"),
        rows=(("Alpha", "2020", "5"),),
        expected_headers=("Study Name", "Year"),
        covariate_names=("Dose",),
        covariate_types=("continuous",),
    )
    dataset_info = {
        "name": "Outcome",
        "arms": "two",
        "data_type": "binary",
        "sub_type": "proportions",
        "effect": "OR",
        "metric_choices": [],
    }

    def fail_add_covariate(*_args, **_kwargs):
        raise RuntimeError("covariate creation failed")

    monkeypatch.setattr(main_wizard.DatasetTableModel, "add_covariate", fail_add_covariate)
    with pytest.raises(csv_import.CsvImportError, match="covariate creation failed"):
        main_wizard.build_staged_import_model(result, dataset_info)
