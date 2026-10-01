# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Behavioral checks for CSV wizard input state and controls."""

from __future__ import annotations

import os
from pathlib import Path
import xml.etree.ElementTree as ET

from PyQt6 import QtCore

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()


def _new_csv_wizard():
    from rc_metastudio import main_wizard

    wizard = main_wizard.MainWizard(path="csv_import")
    wizard.set_dataset_info(
        {
            "arms": "two",
            "data_type": "binary",
            "sub_type": "proportions",
            "effect": "OR",
            "metric_choices": [],
        }
    )
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

        assert shown
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

        assert shown
        assert not page.isComplete()
        assert wizard.get_csv_data() is None
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
