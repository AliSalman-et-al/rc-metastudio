"""Outcome/arm naming through the real wizard, model, calculators and output."""
import csv
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from PyQt6 import QtCore, QtWidgets


def run(app, window, work, record):
    from analysis_matrix import DATA_TYPES, run as matrix
    from advanced_workflows import click, modal
    from tests.e2e.audit_round3 import analyze_existing, check_report
    from rc_metastudio import main_wizard
    from rc_metastudio.binary_data_dialog import BinaryDataDialog
    from rc_metastudio.continuous_data_dialog import ContinuousDataDialog

    cases = [
        ("twoarm-proportion", ("", ""), ("Intervention", "Control")),
        ("twoarm-proportion", ("  Drug A  ", "  Usual care "), ("Drug A", "Usual care")),
        ("twoarm-mean", ("", ""), ("Intervention", "Control")),
        ("twoarm-mean", ("  Training ", " Usual care  "), ("Training", "Usual care")),
        ("onearm-mean", ("",), ("Group", "Other group")),
        ("diagnostic", ("",), ("Index test",)),
        ("onearm-mean", ("  Participants ",), ("Participants", "Other group")),
        ("diagnostic", ("  PCR assay ",), ("PCR assay",)),
    ]
    for case, (family, entered, expected) in enumerate(cases):
        window.workspace.mark_saved()
        view = matrix(app, window, "analysis-data-"+family, record, keep_results=True, group_names=entered)
        assert tuple(window.model.current_groups) == expected, window.model.current_groups
        assert set(window.model.dataset.get_group_names()) == set(expected), window.model.dataset.get_group_names()
        headers = [str(window.model.headerData(i, QtCore.Qt.Orientation.Horizontal)) for i in range(window.model.columnCount())]
        if family.startswith("twoarm"):
            suffix = "events" if family.endswith("proportion") else "mean"
            assert all(name+" "+suffix in headers for name in expected), headers
        view.hide()
        window.raise_()
        app.processEvents()
        record("round5-arm-grid", window, case=case, groups=expected, headers=headers)
        view.show()
        comparison = "Comparison: " + " / ".join(expected)
        for style in (("revman", "default", "bmj") if family.startswith("twoarm") else ("revman",)):
            if style != "revman":
                view = analyze_existing(app, window, "standard", DATA_TYPES[family][1]+".random", record, {"fp_style":style})
            check_report(app, view, work, record)
            text = view.report_text.toPlainText()
            assert "TX Mean" not in text and "[default]" not in text, text
            if family.startswith("twoarm"):
                assert comparison in view.identity_label.text(), view.identity_label.text()
                assert comparison in app.clipboard().text(), app.clipboard().text()
                if family.endswith("proportion"):
                    assert "equal odds in "+" and ".join(expected) in text, text
                for title, path in view.results.display_images.items():
                    labels = ["".join(n.itertext()) for n in ET.parse(path).iter("{http://www.w3.org/2000/svg}text")]
                    assert all(name in labels for name in expected), (style, expected, labels)
                    export = work / f"arms-{case}-{style}.svg"
                    view.plot_service.export(regenerator="forest", params_path=view.params_paths[title], output_path=str(export))
                    assert all(name in export.read_text() for name in expected)
            assert expected[0] in view.identity_label.text(), view.identity_label.text()
            (work/f"arms-{case}-{style}-report.txt").write_text(app.clipboard().text())
            record("round5-arm-report", view, case=case, style=style, groups=expected, plots=dict(view.results.display_images))
            view.close()
        if family.startswith("twoarm") or family == "onearm-mean":
            kind = BinaryDataDialog if "proportion" in family else ContinuousDataDialog
            def calculator(dialog):
                table = dialog.raw_data_table if kind is BinaryDataDialog else dialog.simple_table
                assert table.verticalHeaderItem(0).text() == expected[0]
                if len(entered)==2:
                    assert table.verticalHeaderItem(1).text() == expected[1]
                record("round5-arm-calculator", dialog, case=case, groups=expected, capture_surface="desktop-composite")
                dialog.reject()
            modal(app, kind, calculator, lambda: window.tableView.row_header_clicked(0))
        if family in {"twoarm-proportion", "twoarm-mean", "onearm-mean"}:
            button, data_type, subtype, metric, _raw = DATA_TYPES[family]
            wizard = main_wizard.MainWizard(path="csv_import")
            wizard.set_dataset_info(dict(arms="two" if family.startswith("twoarm") else "one", data_type=data_type,
                sub_type=subtype, effect=metric, metric_choices=[], name="Verification outcome", groups=list(expected)))
            wizard.setStartId(main_wizard.Page_CsvImport)
            wizard.restart()
            wizard.show()
            app.processEvents()
            page = wizard.currentPage()
            template = work / f"arms-{case}-template.csv"
            with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(template), "CSV")):
                click(app, page.template_btn)
            with template.open(encoding="utf-8-sig") as stream:
                canonical = next(csv.reader(stream))
            assert not any("tx" in label.casefold() for label in canonical), canonical
            assert all(any(name in label for label in canonical) for name in expected), canonical
            columns = [window.model.NAME, window.model.YEAR, *window.model.RAW_DATA, *window.model.OUTCOMES]
            values = [str(window.model.data(window.model.index(0,c)) or "") for c in columns]
            values[1] = "2026"
            legacy = (["Study","Year","Tx A #evts","Tx A #total","Tx B #evts","Tx B #total","OR","Lower","Upper"]
                if data_type == "binary" else ["Study","Year","Tx A N","Tx A Mean","Tx A SD","Tx B N","Tx B Mean","Tx B SD",metric,"Lower","Upper"])
            for spelling, source_headers in (("current", canonical), ("legacy", legacy)):
                source = work / f"arms-{case}-{spelling}.csv"
                with source.open("w", newline="") as stream:
                    writer = csv.writer(stream)
                    writer.writerow(source_headers)
                    writer.writerow(values)
                with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(source), "CSV")):
                    click(app, page.select_file_btn)
                assert page.isComplete(), page.import_status.text()
                displayed=[page.preview_table.horizontalHeaderItem(i).text() for i in range(page.preview_table.columnCount())]
                assert displayed == canonical, (displayed, canonical)
                record("round5-arm-csv-preview", wizard, case=case, spelling=spelling, headers=displayed, exports={"template":str(template),"input":str(source)})
                page.import_tabs.setCurrentWidget(page.mapping_table)
                assert not any("tx " in control.itemText(i).casefold() for control in page.mapping_controls for i in range(control.count()))
                record("round5-arm-csv-mapping", wizard, case=case, spelling=spelling)
            wizard.reject()
    window.workspace.mark_saved()
    legacy = Path(__file__).resolve().parents[2] / "sample_projects/amino.rcms"
    original = legacy.read_bytes()
    assert window.open(str(legacy), raise_on_error=True)
    assert window.model.current_groups == ["tx A", "tx B"], window.model.current_groups
    window.out_path=str(work / "legacy-arm-names.rcms")
    assert window.save() and window.open(window.out_path, raise_on_error=True)
    assert window.model.current_groups == ["tx A", "tx B"]
    assert legacy.read_bytes() == original
    record("round5-arm-legacy-reopened", window, groups=window.model.current_groups)
