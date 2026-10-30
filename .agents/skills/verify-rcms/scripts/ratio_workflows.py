"""Real wizard, input, persistence and analysis proof for HR and IRR."""

import json
import math
import csv
import re
import sys
from pathlib import Path
from unittest.mock import patch

SCENARIOS = ("ratios-hr", "ratios-irr", "ratios-samples")


def run(app, window, scenario, record):
    if scenario == "ratios-samples":
        for hazard in (True, False):
            verify_bundled_sample(app, window, hazard, record)
        return
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtSvg import QSvgRenderer
    from rc_metastudio import main_wizard, analysis_setup_dialog, results_window, r_bridge, analysis_dataset
    from rc_metastudio.subgroup_analysis_dialog import SubgroupAnalysisDialog
    from rc_metastudio.publication_bias_dialog import PublicationBiasDialog
    from rc_metastudio.ratio_data_dialog import RatioDataDialog
    from analysis_matrix import set_parameter
    from advanced_workflows import modal, plots
    from tests.analysis_regression.golden.support.golden_analysis import parsed_numeric_sections, _parse_result_table, _result_row_key

    hazard = scenario == "ratios-hr"
    family, metric = ("time_to_event", "HR") if hazard else ("event_rates", "IRR")
    work = Path(sys.argv[2])

    def click(widget):
        assert widget.isEnabled(), widget.objectName()
        from tests.python.gui.test_types import mouse_click
        mouse_click(widget, QtCore.Qt.MouseButton.LeftButton)
        app.processEvents()

    def visible(kind):
        found = [widget for widget in app.topLevelWidgets() if isinstance(widget, kind) and widget.isVisible()]
        assert len(found) == 1, (kind, found)
        return found[0]

    def create(wizard):
        page = wizard.currentPage()
        assert isinstance(page, main_wizard.DataTypePage)
        # HR/IRR must not appear under the diagnostic test-performance heading.
        assert page.multiArmDataTypesLayout.indexOf(page.time_rates_Button) >= 0
        assert page.diagnosticDataTypeLayout.indexOf(page.time_rates_Button) == -1
        assert page.time_rates_Button.text() == "Time-to-event\nand event rates"
        assert not page.time_rates_Button.icon().isNull()
        click(page.time_rates_Button)
        click(wizard.button(QtWidgets.QWizard.WizardButton.NextButton))
        page = wizard.currentPage()
        assert isinstance(page, main_wizard.ChooseMetricPage)
        assert [page.metric_cbo_box.itemData(i) for i in range(2)] == ["HR", "IRR"]
        assert all(not page.metric_cbo_box.itemIcon(i).isNull() for i in range(2))
        page.metric_cbo_box.setCurrentIndex(page.metric_cbo_box.findData(metric))
        assert wizard.require_dataset_info()["data_type"] == family
        assert wizard.require_dataset_info()["sub_type"] == ("hazard_ratio" if hazard else "incidence_rate_ratio")
        click(wizard.button(QtWidgets.QWizard.WizardButton.BackButton))
        click(wizard.button(QtWidgets.QWizard.WizardButton.NextButton))
        page = wizard.currentPage()
        assert page.metric_cbo_box.currentData() == metric
        assert wizard.require_dataset_info()["data_type"] == family
        record("ratio-family-selected", wizard, family=family, metric=metric)
        click(wizard.button(QtWidgets.QWizard.WizardButton.NextButton))
        wizard.currentPage().outcome_name_LineEdit.setText("Survival" if hazard else "Recurrent events")
        click(wizard.button(QtWidgets.QWizard.WizardButton.FinishButton))

    modal(app, main_wizard.MainWizard, create, window.action_new_dataset.trigger)
    model = window.model
    assert model.get_current_outcome_type() == family
    assert model.current_effect == metric
    assert [c for c in model.OUTCOMES if not window.tableView.isColumnHidden(c)] == model.OUTCOMES[:3]
    ys, ses = [], []
    z90 = 1.6448536269514722
    raws = []
    for i in range(12):
        assert model.setData(model.index(i, model.NAME), f"Study {i+1}")
        assert model.setData(model.index(i, model.YEAR), str(2020+i))
        y, se = -.4 + i * .055 + .035 * math.sin(i), .13 + i * .009
        ys.append(y); ses.append(se)
        raw = [0 if i in (0, 2) else 3+i, 100+i*10, 0 if i == 2 else 5+i, 110+i*11]
        raws.append(raw)
        if i < 2:
            def enter_first(dialog):
                if hazard:
                    for name, value in zip(("estimate", "lower", "upper"), (math.exp(y), math.exp(y-z90*se), math.exp(y+z90*se))):
                        dialog.fields[name].setText(str(value))
                    dialog.fields["confidence"].setText("90")
                else:
                    for field, value in zip(dialog.raw_fields, raw):
                        field.setText(str(value))
                record("ratio-initial-study-dialog", dialog, study=i+1)
                click(dialog.findChild(QtWidgets.QDialogButtonBox).button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
            modal(app, RatioDataDialog, enter_first, lambda: window.tableView.row_header_clicked(i))
            if i == 1:
                assert window.action_go.isEnabled()
        elif not hazard:
            for column, value in zip(model.RAW_DATA, raw):
                assert model.setData(model.index(i, column), str(value)), model.last_data_error
        if i >= 2 and (hazard or i >= 8):
            for column, value in zip(model.OUTCOMES[:3], (math.exp(y), math.exp(y-z90*se), math.exp(y+z90*se))):
                assert model.setData(model.index(i, column), str(value)), model.last_data_error
            assert model.setData(model.index(i, model.OUTCOMES[5]), "90")
            if not hazard:
                assert not model.current_sheet.rows[i].include
                assert model.setData(model.index(i, model.OUTCOMES[6]), "reported")
                assert model.setData(model.index(i, model.OUTCOMES[7]), "person-months")
        assert model.current_sheet.rows[i].include
    model.try_to_update_outcomes()
    if not hazard:
        assert [model.data(model.index(2, column)) for column in model.OUTCOMES[:3]] == [
            "Not estimable", "\u2014", "\u2014"
        ]
        assert "zero events in both groups" in model.data(
            model.index(2, model.OUTCOMES[0]), QtCore.Qt.ItemDataRole.ToolTipRole
        )
    window.tableView._enable_analysis_menus_if_appropriate()
    assert window.action_go.isEnabled()
    record("ratio-inputs-complete", window, family=family, raw=raws, log_effects=ys, log_ses=ses,
           source_confidence=90, selected_sources=["reported" if hazard or i >= 8 else "raw" for i in range(12)])

    # The actual row gesture opens the dedicated calculator. Accept an unchanged,
    # complete record, then prove Cancel preserves it.
    def calculator(dialog):
        assert dialog.fields["confidence"].text() == "90.0"
        assert dialog.fields["lower"].isVisible()
        assert not dialog.fields["se"].isVisible()
        assert not any(field.isVisible() for field in dialog.raw_fields)
        for field in dialog.fields.values():
            if field.isVisible():
                assert field.width() >= 230
        record("ratio-calculator", dialog, source_confidence=dialog.fields["confidence"].text())
        click(dialog.findChild(QtWidgets.QDialogButtonBox).button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    modal(app, RatioDataDialog, calculator, lambda: window.tableView.row_header_clicked(11))
    before = model.get_current_analysis_unit_for_study(11).ratio_input(model.current_groups)
    def cancel(dialog):
        dialog.fields["estimate"].setText("2")
        click(dialog.findChild(QtWidgets.QDialogButtonBox).button(QtWidgets.QDialogButtonBox.StandardButton.Cancel))
    modal(app, RatioDataDialog, cancel, lambda: window.tableView.row_header_clicked(11))
    assert model.get_current_analysis_unit_for_study(11).ratio_input(model.current_groups) == before

    project_path = work / f"{metric}.rcms"
    window.out_path = str(project_path)
    assert window.save()
    assert window.open(str(project_path), raise_on_error=True)
    model = window.model
    reopened = model.get_current_analysis_unit_for_study(11).ratio_input(model.current_groups)
    assert reopened == before
    record("ratio-project-reopened", window, project=str(project_path), input=vars(reopened))
    # A deleted study must disappear from both the document and the displayed
    # rows. Sorting must still delete the study actually named by the menu.
    for sorted_rows in (False, True):
        assert model.setData(model.index(12, model.NAME), "Study 13")
        assert model.setData(model.index(12, model.YEAR), "2032")
        added_id = model.current_sheet.rows[-1].id
        if sorted_rows:
            model.sort_studies(model.NAME, reverse=True)
            app.processEvents()
        row = next(i for i in range(model.rowCount()) if model.data(model.index(i, model.NAME)) == "Study 13")
        table = window.tableView
        point = table.visualRect(model.index(row, model.NAME)).center()
        event = QtGui.QContextMenuEvent(QtGui.QContextMenuEvent.Reason.Mouse, point, table.viewport().mapToGlobal(point))
        table.contextMenuEvent(event)
        app.processEvents()
        menu = app.activePopupWidget()
        assert isinstance(menu, QtWidgets.QMenu)
        delete = next(action for action in menu.actions() if action.text().startswith("Delete study"))
        assert delete.text() == "Delete study “Study 13”…"
        from rc_metastudio import project_adapter
        deletion_before = project_adapter.runtime_project_to_document(window.workspace.snapshot())
        (work / "delete-before.json").write_text(json.dumps(dict(project=deletion_before.project, state=deletion_before.state), indent=2))
        record("ratio-delete-study-menu", window, target_id=added_id, target_row=row, sorted_rows=sorted_rows)
        def confirm_delete(dialog):
            assert dialog.text() == "Delete study Study 13?"
            click(dialog.button(QtWidgets.QMessageBox.StandardButton.Yes))
        modal(app, QtWidgets.QMessageBox, confirm_delete, delete.trigger)
        menu.close(); app.processEvents()
        model = window.model
        assert added_id not in [study.id for study in model.current_sheet.rows]
        assert "Study 13" not in [model.data(model.index(i, model.NAME)) for i in range(model.rowCount())]
        record("ratio-study-deleted", window, remaining_ids=[study.id for study in model.current_sheet.rows])
        window.undo(); app.processEvents()
        model = window.model
        assert added_id in [study.id for study in model.current_sheet.rows]
        assert "Study 13" in [model.data(model.index(i, model.NAME)) for i in range(model.rowCount())]
        deletion_undone = project_adapter.runtime_project_to_document(window.workspace.snapshot())
        (work / "delete-undone.json").write_text(json.dumps(dict(project=deletion_undone.project, state=deletion_undone.state), indent=2))
        record("ratio-delete-undone", window, can_redo=window.workspace.can_redo)
        assert window.workspace.can_redo
        window.redo(); app.processEvents()
        model = window.model
        assert "Study 13" not in [model.data(model.index(i, model.NAME)) for i in range(model.rowCount())]
        model.sort_studies(model.YEAR, reverse=False)
        assert window.save() and window.open(str(project_path), raise_on_error=True)
        model = window.model
        assert len(model.current_sheet.rows) == 12
        record("ratio-delete-reopened", window, study_count=12)
    # Reverse the same comparison twice. Original source CI and SE must survive.
    groups = list(model.current_groups)
    model.current_sheet.arms.reverse()
    reverse = model.get_current_analysis_unit_for_study(11).ratio_input(model.current_groups)
    assert abs(reverse.estimate * reopened.estimate - 1) < 1e-12
    assert reverse.confidence == reopened.confidence
    model.current_sheet.arms.reverse()
    assert model.get_current_analysis_unit_for_study(11).ratio_input(groups) == reopened

    # Import the exported original inputs through the production CSV preview.
    csv_path = work / f"{metric}.csv"
    columns = [model.NAME, model.YEAR, *model.RAW_DATA, *model.OUTCOMES]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow([model.headerData(c, QtCore.Qt.Orientation.Horizontal) for c in columns])
        writer.writerows([[model.data(model.index(i, c), QtCore.Qt.ItemDataRole.EditRole) for c in columns] for i in range(12)])
    wizard = main_wizard.MainWizard(path="csv_import")
    info: main_wizard.DatasetInfo = dict(arms="two", data_type=family, sub_type="hazard_ratio" if hazard else "incidence_rate_ratio",
                effect=metric, metric_choices=[], name="Survival" if hazard else "Recurrent events")
    wizard.set_dataset_info(info)
    name_page = wizard.page(main_wizard.Page_OutcomeName)
    assert isinstance(name_page, main_wizard.OutcomeNamePage)
    name_page.outcome_name_LineEdit.setText(info["name"])
    wizard.setStartId(main_wizard.Page_CsvImport)
    wizard.restart(); wizard.show(); app.processEvents()
    page = wizard.currentPage()
    assert isinstance(page, main_wizard.CsvImportPage)
    with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(csv_path), "")):
        click(page.select_file_btn)
    assert page.isComplete() and page.preview_table.rowCount() == 12
    record("ratio-csv-preview", wizard, csv=str(csv_path), headers=page.required_header_labels)
    window._handle_wizard_results(wizard.get_results())
    wizard.close(); app.processEvents()
    model = window.model
    assert model.get_current_analysis_unit_for_study(11).ratio_input(model.current_groups) == reopened
    assert all(study.include for study in model.current_sheet.rows)

    # A usual RCMS CSV needs only the visible inputs. Advanced source fields
    # remain optional, and omitted fields must acquire documented defaults.
    simple_csv = work / f"{metric}-simple.csv"
    basic_columns = [model.NAME, model.YEAR, *model.RAW_DATA, *model.OUTCOMES[:3]]
    with simple_csv.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow([model.headerData(c, QtCore.Qt.Orientation.Horizontal) for c in basic_columns])
        writer.writerows([[model.data(model.index(i, c), QtCore.Qt.ItemDataRole.EditRole)
                           if hazard or c not in model.OUTCOMES else "" for c in basic_columns] for i in range(12)])
    simple_wizard = main_wizard.MainWizard(path="csv_import")
    simple_wizard.set_dataset_info(info)
    simple_name_page = simple_wizard.page(main_wizard.Page_OutcomeName)
    assert isinstance(simple_name_page, main_wizard.OutcomeNamePage)
    simple_name_page.outcome_name_LineEdit.setText(info["name"])
    simple_wizard.setStartId(main_wizard.Page_CsvImport)
    simple_wizard.restart(); simple_wizard.show(); app.processEvents()
    simple_page = simple_wizard.currentPage()
    assert isinstance(simple_page, main_wizard.CsvImportPage)
    assert len(simple_page.required_header_labels) == len(basic_columns)
    with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(simple_csv), "")):
        click(simple_page.select_file_btn)
    assert simple_page.isComplete()
    window._handle_wizard_results(simple_wizard.get_results())
    simple_wizard.close(); app.processEvents()
    model = window.model
    for i in range(12):
        record_input = model.get_current_analysis_unit_for_study(i).ratio_input(model.current_groups)
        assert record_input.confidence == 95 and record_input.scale == "ratio"
        assert record_input.unit == "person-years" and model.current_sheet.rows[i].include
    record("ratio-simple-csv-imported", window, csv=str(simple_csv), required_columns=len(basic_columns), defaults="ratio, 95% source CI, person-years")
    simple_project = work / f"{metric}-simple.rcms"
    window.out_path = str(simple_project)
    assert window.save()
    assert window.open(str(simple_project), raise_on_error=True)
    assert window.open(str(project_path), raise_on_error=True)
    model = window.model
    assert model.get_current_analysis_unit_for_study(11).ratio_input(model.current_groups) == reopened

    edit_row = 0 if hazard else 8
    window.tableView.setCurrentIndex(model.index(edit_row, model.OUTCOMES[0]))
    original = model.get_current_analysis_unit_for_study(edit_row).ratio_input(model.current_groups)
    app.clipboard().setText("0.7\t2")
    with patch.object(QtWidgets.QMessageBox, "warning") as warning:
        window.action_paste.trigger(); app.processEvents()
    assert model.get_current_analysis_unit_for_study(edit_row).ratio_input(model.current_groups) == original
    assert warning.called or model.last_data_error
    def change_confidence(dialog):
        dialog.fields["confidence"].setText("80")
        click(dialog.findChild(QtWidgets.QDialogButtonBox).button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    modal(app, RatioDataDialog, change_confidence, lambda: window.tableView.row_header_clicked(edit_row))
    assert model.get_current_analysis_unit_for_study(edit_row).ratio_input(model.current_groups).confidence == 80
    window.action_undo.trigger(); model = window.model
    assert model.get_current_analysis_unit_for_study(edit_row).ratio_input(model.current_groups) == original
    window.action_redo.trigger(); model = window.model
    assert model.get_current_analysis_unit_for_study(edit_row).ratio_input(model.current_groups).confidence == 80
    window.action_undo.trigger(); model = window.model
    record("ratio-paste-rollback-undo-redo", window, invalid_paste="0.7 / lower 2", restored=vars(original))

    def log_input(dialog):
        dialog.fields["scale"].setCurrentIndex(dialog.fields["scale"].findData("log"))
        app.processEvents()
        assert dialog.fields["se"].isVisible()
        assert not dialog.fields["lower"].isVisible()
        assert not dialog.fields["confidence"].isVisible()
        assert abs(float(dialog.fields["estimate"].text())-ys[-1]) < 1e-12
        with patch.object(QtWidgets.QMessageBox, "warning") as warning:
            click(dialog.findChild(QtWidgets.QDialogButtonBox).button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
        assert warning.called and dialog.isVisible()
        dialog.fields["estimate"].setText(str(ys[-1]))
        dialog.fields["lower"].clear(); dialog.fields["upper"].clear()
        dialog.fields["se"].setText(str(ses[-1]))
        click(dialog.findChild(QtWidgets.QDialogButtonBox).button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    modal(app, RatioDataDialog, log_input, lambda: window.tableView.row_header_clicked(11))
    assert model.get_current_analysis_unit_for_study(11).ratio_input(model.current_groups).scale == "log"
    assert float(model.data(model.index(11, model.OUTCOMES[0]))) == round(math.exp(ys[-1]), model.NUM_DIGITS)
    record("ratio-log-effect-se-entered", window, estimate=ys[-1], log_se=ses[-1])

    # Public-package input is constructed independently from the entered fixture.
    prefix = "e <- data.frame(yi=c(" + ",".join(map(str, ys)) + "), vi=c(" + ",".join(str(se**2) for se in ses) + ")); "
    vector = lambda column: "c(" + ",".join(str(row[column]) for row in raws) + ")"
    if not hazard:
        prefix += f'raw <- metafor::escalc("IRR", x1i={vector(0)}, t1i={vector(1)}, x2i={vector(2)}, t2i={vector(3)}, add=.5, to="only0", drop00=TRUE); e[1:8,] <- raw[1:8,c("yi","vi")]; '
    prefix += "keep <- is.finite(e$yi) & is.finite(e$vi) & e$vi > 0; e <- e[keep,]; "
    for name, kind, values in (
        ("Region", "factor", {s.label: "A" if i % 2 else "B" for i, s in enumerate(model.current_sheet.rows)}),
        ("Dose", "continuous", {s.label: float(i) for i,s in enumerate(model.current_sheet.rows)}),
    ):
        model.add_covariate(name, kind, values)
    model.reset_model()
    window.enable_menu_options_that_require_dataset()
    # A visible rectangle crosses hidden input metadata. Copy/paste must reach
    # the adjacent covariate, rather than corrupting the original CI settings.
    dose_column = model.columnCount()-1
    window.tableView.copy_contents_in_range(model.index(11, model.OUTCOMES[0]), model.index(11, dose_column), to_clipboard=True)
    assert len(app.clipboard().text().split("\t")) == 5
    original = model.get_current_analysis_unit_for_study(edit_row).ratio_input(model.current_groups)
    window.tableView.setCurrentIndex(model.index(edit_row, model.OUTCOMES[2]))
    app.clipboard().setText(f"{original.upper}\tB\t{edit_row}")
    window.action_paste.trigger(); app.processEvents()
    model = window.model
    assert model.get_current_analysis_unit_for_study(edit_row).ratio_input(model.current_groups).confidence == 90
    assert model.current_sheet.rows[edit_row].covariate_values[model.current_sheet.covariates[0]['id']] == "B"
    record("ratio-compact-table-copy-paste", window, visible_outcomes=3, copied_columns=5)

    def analysis(workflow, suffix="random", confidence=95):
        action = {"standard":window.action_go, "cumulative":window.action_cum_ma,
            "leave-one-out":window.action_loo_ma, "subgroup":window.action_subgroup_ma,
            "meta-regression":window.action_meta_regression}[workflow]
        assert action.isEnabled(), workflow
        action.trigger(); app.processEvents()
        if workflow == "subgroup":
            subgroup = visible(SubgroupAnalysisDialog)
            subgroup.covariate_combo_box.setCurrentText("Region")
            click(subgroup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
        dialog = visible(analysis_setup_dialog.AnalysisSetupDialog)
        method = family + "." + suffix
        if workflow == "meta-regression":
            for cov, checkbox in dialog.covs_and_check_boxes:
                checkbox.setChecked(cov['name'] == 'Dose')
        else:
            label = next(label for label, key in dialog.available_method_d.items() if key == method)
            dialog.method_cbo_box.setCurrentText(label); app.processEvents()
        set_parameter(app, dialog, "digits", 6)
        set_parameter(app, dialog, "conf.level", confidence)
        if suffix == "random" or workflow == "meta-regression":
            set_parameter(app, dialog, "rm.method", "REML")
        record("ratio-analysis-configured", dialog, workflow=workflow, method=method, parameters=dict(dialog.current_param_vals))
        click(dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
        view = visible(results_window.ResultsWindow)
        for path in (view.results.display_images or view.results.images).values():
            assert Path(path).is_file()
            assert QSvgRenderer(path).isValid() if Path(path).suffix == ".svg" else not QtGui.QImage(path).isNull()
        record("ratio-analysis-results", view, workflow=workflow, texts=dict(view.texts), plots=dict(view.results.display_images or view.results.images))
        return view

    for suffix in ("fixed", "random"):
        view = analysis("standard", suffix)
        expression = prefix + f'f <- metafor::rma.uni(e$yi, vi=e$vi, method="{"FE" if suffix == "fixed" else "REML"}"); '
        expected = json.loads(str(r_bridge.execute_r_string("{" + expression + 'jsonlite::toJSON(list(b=as.numeric(f$b), se=f$se, lower=f$ci.lb, upper=f$ci.ub),auto_unbox=TRUE,digits=16)}')[0]))
        actual = parsed_numeric_sections(view.results)["Summary"]
        for key, name in (("estimate","b"), ("standard_error","se"), ("lower_bound","lower"), ("upper_bound","upper")):
            assert abs(actual["calculation_scale."+key] - expected[name]) <= 1.1e-6, (actual,expected)
        record("ratio-public-metafor-comparison", view, estimator=suffix, actual=actual, expected=expected)
        if suffix == "fixed":
            plots(app, window, "forest", record, view=view)
        else:
            view.close()
        app.processEvents()
    view = analysis("standard", "fixed", confidence=90)
    actual = parsed_numeric_sections(view.results)["Summary"]
    expected = json.loads(str(r_bridge.execute_r_string("{" + prefix + 'f <- metafor::rma.uni(e$yi,vi=e$vi,method="FE",level=90); jsonlite::toJSON(list(b=as.numeric(f$b),se=f$se,lower=f$ci.lb,upper=f$ci.ub),auto_unbox=TRUE,digits=16)}')[0]))
    for key, name in (("estimate","b"), ("standard_error","se"), ("lower_bound","lower"), ("upper_bound","upper")):
        assert abs(actual["calculation_scale."+key]-expected[name]) <= 1.1e-6, (actual, expected)
    assert model.get_current_analysis_unit_for_study(edit_row).ratio_input(model.current_groups).confidence == 90
    record("ratio-independent-output-confidence", view, output_confidence=90, source_confidence=90, actual=actual, expected=expected)
    view.close(); app.processEvents()
    for workflow in ("cumulative", "leave-one-out", "subgroup", "meta-regression"):
        view = analysis(workflow)
        if workflow == "meta-regression":
            assert "ratios of " + metric in "\n".join(view.texts.values())
            expression = prefix + 'dose <- (0:11)[keep]; f <- metafor::rma.uni(e$yi,vi=e$vi,mods=~dose,method="REML"); '
            expected = json.loads(str(r_bridge.execute_r_string("{" + expression + 'jsonlite::toJSON(list(b=as.numeric(f$b),se=f$se,lower=f$ci.lb,upper=f$ci.ub),digits=16)}')[0]))
            actual = _parse_result_table(view.texts["Summary"])
            for i, label in enumerate(("intercept", "dose")):
                for field, key in (("coefficient", "b"), ("standard_error", "se"), ("lower_bound", "lower"), ("upper_bound", "upper")):
                    assert abs(actual[f"model.{label}.{field}"]-expected[key][i]) <= 1.1e-6, (actual, expected)
            record("ratio-regression-metafor-comparison", view, actual=actual, expected=expected)
        else:
            regions = "c(" + ",".join('"A"' if i % 2 else '"B"' for i in range(12)) + ")[keep]"
            indices = 'lapply(seq_len(nrow(e)), function(i) seq_len(i))' if workflow == "cumulative" else 'lapply(seq_len(nrow(e)), function(i) setdiff(seq_len(nrow(e)),i))'
            if workflow == "subgroup":
                indices = f'c(lapply(unique({regions}), function(g) which({regions} == g)),list(seq_len(nrow(e))))'
            expression = prefix + f'fits <- lapply({indices}, function(ix) metafor::rma.uni(e$yi[ix],vi=e$vi[ix],method="REML")); '
            expected = json.loads(str(r_bridge.execute_r_string("{" + expression + 'jsonlite::toJSON(lapply(fits,function(f)list(estimate=exp(as.numeric(f$b)),lower_bound=exp(f$ci.lb),upper_bound=exp(f$ci.ub),standard_error=f$se)),auto_unbox=TRUE,digits=16)}')[0]))
            actual = _parse_result_table(view.texts["Subgroup Summary" if workflow == "subgroup" else "Sequential Summary"])
            names = [f"Study {i+1}" for i in range(12) if hazard or i != 2]
            labels = (["B", "A", "Overall"] if workflow == "subgroup" else
                      [f"{name} (k = {i+1})" if workflow == "cumulative" else f"Study omitted: {name}"
                       for i, name in enumerate(names)])
            for label, row in zip(labels, expected, strict=True):
                for key, value in row.items():
                    assert abs(actual[f"model.{_result_row_key(label)}.{key}"]-value) <= 1.1e-6, (label, actual, expected)
            record("ratio-workflow-metafor-comparison", view, workflow=workflow, actual=actual, expected=expected)
        plots(app, window, "regression" if workflow == "meta-regression" else workflow, record, view=view)
        app.processEvents()

    def bias(dialog):
        assert "classical-egger" in str(dialog._eligibility_report)
        assert "_" not in dialog.context_label.text()
        dialog.ordinary_funnel_check.setChecked(True)
        dialog.contour_funnel_check.setChecked(True)
        dialog.trim_fill_check.setChecked(True)
        record("ratio-small-study-configured", dialog, context=dialog.context_label.text())
        click(dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
        assert not dialog.failure_label.isVisible(), dialog.failure_label.text()
    modal(app, PublicationBiasDialog, bias, window.action_publication_bias.trigger)
    view = visible(results_window.ResultsWindow)
    assert any("contour" in key for key in view.results.images)
    record("ratio-small-study-results", view, texts=dict(view.texts), plots=dict(view.results.display_images or view.results.images))
    expression = prefix + f'm <- meta::metagen(e$yi,sqrt(e$vi),sm="{metric}",method.tau="REML",level=.95); f <- meta::metabias(m,method.bias="Egger",k.min=10,level=.95); '
    expected = json.loads(str(r_bridge.execute_r_string("{" + expression + 'jsonlite::toJSON(list(coefficient=as.numeric(f$estimate[1]),se=as.numeric(f$estimate[2]),p=f$p.value),auto_unbox=TRUE,digits=16)}')[0]))
    match = re.search(r"Coefficient: ([-\d.]+) \(SE ([-\d.]+);", view.texts["small-study.tests"])
    assert match is not None
    actual = dict(coefficient=float(match[1]), se=float(match[2]))
    for key, value in actual.items():
        assert abs(value-expected[key]) <= 5e-4 * max(1, abs(expected[key])), (actual, expected)
    record("ratio-egger-meta-comparison", view, actual=actual, expected=expected)
    plots(app, window, "contour", record, view=view)
    app.processEvents()
    if not hazard:
        for i in range(8,12):
            assert model.setData(model.index(i, model.OUTCOMES[6]), "raw")
        view = analysis("standard", "mh")
        expression = f'f <- metafor::rma.mh(measure="IRR",x1i={vector(0)},t1i={vector(1)},x2i={vector(2)},t2i={vector(3)},add=c(.5,0),to=c("only0","none"),drop00=c(TRUE,FALSE)); '
        expected = json.loads(str(r_bridge.execute_r_string("{" + expression + 'jsonlite::toJSON(list(b=as.numeric(f$b),se=f$se,lower=f$ci.lb,upper=f$ci.ub),auto_unbox=TRUE,digits=16)}')[0]))
        actual = parsed_numeric_sections(view.results)["Summary"]
        for key, name in (("estimate","b"), ("standard_error","se"), ("lower_bound","lower"), ("upper_bound","upper")):
            assert abs(actual["calculation_scale."+key] - expected[name]) <= 1.1e-6, (actual,expected)
        record("ratio-mh-metafor-comparison", view, actual=actual, expected=expected)
        view.close(); app.processEvents()
        for workflow in ("cumulative", "leave-one-out", "subgroup"):
            view = analysis(workflow, "mh")
            if workflow == "cumulative":
                assert "zero total events" in "\n".join(view.texts.values())
            indices = 'lapply(1:12,function(i)seq_len(i))' if workflow == "cumulative" else 'lapply(1:12,function(i)setdiff(1:12,i))'
            if workflow == "subgroup":
                indices = 'list(seq(1,12,2),seq(2,12,2),1:12)'
            expression = f'x1 <- {vector(0)}; t1 <- {vector(1)}; x2 <- {vector(2)}; t2 <- {vector(3)}; fits <- lapply({indices},function(ix) {{ if(sum(x1[ix])==0 || sum(x2[ix])==0)return(NULL); f <- metafor::rma.mh(measure="IRR",x1i=x1[ix],t1i=t1[ix],x2i=x2[ix],t2i=t2[ix],add=c(.5,0),to=c("only0","none"),drop00=c(TRUE,FALSE)); list(estimate=exp(as.numeric(f$b)),lower_bound=exp(f$ci.lb),upper_bound=exp(f$ci.ub),standard_error=f$se) }}); jsonlite::toJSON(fits,auto_unbox=TRUE,digits=16)'
            expected = json.loads(str(r_bridge.execute_r_string("{" + expression + "}")[0]))
            actual = _parse_result_table(view.texts["Subgroup Summary" if workflow == "subgroup" else "Sequential Summary"])
            labels = (["B", "A", "Overall"] if workflow == "subgroup" else
                      [f"Study {i+1}, {2020+i} (k = {i+1})" if workflow == "cumulative" else f"Study omitted: Study {i+1}, {2020+i}"
                       for i in range(12)])
            for label, row in zip(labels, expected, strict=True):
                if row is None or row == {}:
                    assert label in view.texts["Non-estimable rows"]
                    continue
                for key, value in row.items():
                    assert abs(actual[f"model.{_result_row_key(label)}.{key}"] - value) <= 1.1e-6, (label, actual, expected)
            record("ratio-mh-workflow-metafor-comparison", view, workflow=workflow, actual=actual, expected=expected)
            view.close(); app.processEvents()
        # Restore mixed sources before saving the durable inspection fixture.
        for i in range(8,12):
            assert model.setData(model.index(i, model.OUTCOMES[6]), "reported")
    window.out_path = str(project_path)
    assert window.save()
    record("ratio-proof-complete", window, repeat_command=f"uv run python scripts/verify_rcms.py {scenario}", project=str(project_path))


def verify_bundled_sample(app, window, hazard, record):
    """Open the shipped metadat sample, fit it, and preserve original inputs."""
    from PyQt6 import QtCore, QtWidgets
    from rc_metastudio import analysis_setup_dialog, results_window, r_bridge
    from rc_metastudio.project_format import load_project
    from rc_metastudio.subgroup_analysis_dialog import SubgroupAnalysisDialog
    from rc_metastudio.publication_bias_dialog import PublicationBiasDialog
    from analysis_matrix import set_parameter
    from advanced_workflows import modal
    from tests.analysis_regression.golden.support.golden_analysis import parsed_numeric_sections, _parse_result_table, _result_row_key

    root = Path(__file__).resolve().parents[4]
    filename = "Pignon2000-HR.rcms" if hazard else "NielWeise2008-IRR.rcms"
    dataset_name = "dat.pignon2000" if hazard else "dat.nielweise2008"
    family, metric = ("time_to_event", "HR") if hazard else ("event_rates", "IRR")
    source = json.loads((root / "sample_projects/sources/metadat-ratios.json").read_text(encoding="utf-8"))
    rows = source["datasets"][dataset_name]["rows"]
    path = root / "sample_projects" / filename
    original = load_project(path)
    window.workspace.mark_saved()
    assert window.open(str(path), raise_on_error=True)

    def check_inputs():
        model = window.model
        assert len(model.current_sheet.rows) == len(rows)
        assert model.current_effect == metric and model.get_current_outcome_type() == family
        assert all(study.include for study in model.current_sheet.rows)
        for i, row in enumerate(rows):
            study = model.current_sheet.rows[i]
            unit = model.get_current_analysis_unit_for_study(i)
            ratio = unit.ratio_input(model.current_groups)
            assert study.label == (row["trial"] if hazard else row["authors"])
            assert study.year == (None if hazard else row["year"])
            if hazard:
                assert ratio.scale == "log" and ratio.source == "reported"
                assert ratio.estimate == row["OmE"] / row["V"]
                assert ratio.se == math.sqrt(1 / row["V"])
                assert study.covariate_values[next(c['id'] for c in model.current_sheet.covariates if c['name']=='Original study ID')] == row["id"]
                assert study.covariate_values[next(c['id'] for c in model.current_sheet.covariates if c['name']=='Chemotherapy timing')] == {1: "Adjuvant", 2: "Neoadjuvant", 3: "Concomitant"}[row["grp"]]
            else:
                assert ratio.source == "raw" and ratio.unit == "catheter-days"
                assert unit.get_raw_data_for_arms(model.current_groups) == [row["x1i"], row["t1i"], row["x2i"], row["t2i"]]
            assert math.isfinite(float(model.data(model.index(i, model.OUTCOMES[0]))))

    def visible(kind):
        widgets = [widget for widget in app.topLevelWidgets() if isinstance(widget, kind) and widget.isVisible()]
        assert len(widgets) == 1
        return widgets[0]

    check_inputs()
    record("bundled-ratio-sample-opened", window, sample=filename, studies=len(rows), source=dataset_name)
    for suffix in ("fixed", "random") if hazard else ("fixed", "random", "mh"):
        assert window.action_go.isEnabled()
        window.action_go.trigger(); app.processEvents()
        dialog = visible(analysis_setup_dialog.AnalysisSetupDialog)
        method = family + "." + suffix
        label = next(label for label, key in dialog.available_method_d.items() if key == method)
        dialog.method_cbo_box.setCurrentText(label); app.processEvents()
        set_parameter(app, dialog, "digits", 6)
        set_parameter(app, dialog, "conf.level", 95)
        if suffix == "random":
            set_parameter(app, dialog, "rm.method", "REML")
        dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click(); app.processEvents()
        view = visible(results_window.ResultsWindow)
        expression = f'data("{dataset_name}",package="metadat"); d <- {dataset_name}; '
        if hazard:
            expression += f'f <- metafor::rma.uni(yi=d$OmE/d$V, vi=1/d$V, method="{"FE" if suffix == "fixed" else "REML"}"); '
        elif suffix == "mh":
            expression += 'f <- metafor::rma.mh(measure="IRR",x1i=d$x1i,t1i=d$t1i,x2i=d$x2i,t2i=d$t2i,add=c(.5,0),to=c("only0","none"),drop00=c(TRUE,FALSE)); '
        else:
            expression += f'f <- metafor::rma.uni(measure="IRR",x1i=d$x1i,t1i=d$t1i,x2i=d$x2i,t2i=d$t2i,method="{"FE" if suffix == "fixed" else "REML"}"); '
        expression += 'jsonlite::toJSON(list(b=as.numeric(f$b),se=f$se,lower=f$ci.lb,upper=f$ci.ub,k=f$k),auto_unbox=TRUE,digits=16)'
        expected = json.loads(str(r_bridge.execute_r_string("{" + expression + "}")[0]))
        actual = parsed_numeric_sections(view.results)["Summary"]
        assert expected["k"] == len(rows)
        for key, name in (("estimate", "b"), ("standard_error", "se"), ("lower_bound", "lower"), ("upper_bound", "upper")):
            assert abs(actual["calculation_scale." + key] - expected[name]) <= 1.1e-6, (actual, expected)
        plot_paths = dict(view.results.display_images or view.results.images)
        assert plot_paths and all(Path(path).is_file() for path in plot_paths.values())
        record("bundled-ratio-sample-metafor-comparison", view, sample=filename, method=method, actual=actual, expected=expected, plots=plot_paths)
        view.close(); app.processEvents()
    if hazard:
        window.action_subgroup_ma.trigger(); app.processEvents()
        subgroup = visible(SubgroupAnalysisDialog)
        subgroup.covariate_combo_box.setCurrentText("Chemotherapy timing")
        subgroup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click(); app.processEvents()
        dialog = visible(analysis_setup_dialog.AnalysisSetupDialog)
        label = next(label for label, key in dialog.available_method_d.items() if key == family + ".random")
        dialog.method_cbo_box.setCurrentText(label); app.processEvents()
        set_parameter(app, dialog, "digits", 6)
        set_parameter(app, dialog, "rm.method", "REML")
        record("bundled-hr-timing-subgroup-configured", dialog, parameters=dict(dialog.current_param_vals))
        dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click(); app.processEvents()
        view = visible(results_window.ResultsWindow)
        expression = 'data("dat.pignon2000",package="metadat"); d <- dat.pignon2000; fits <- lapply(c(lapply(1:3,function(g)which(d$grp==g)),list(seq_len(nrow(d)))),function(ix)metafor::rma.uni(yi=d$OmE[ix]/d$V[ix],vi=1/d$V[ix],method="REML")); jsonlite::toJSON(lapply(fits,function(f)list(estimate=exp(as.numeric(f$b)),lower_bound=exp(f$ci.lb),upper_bound=exp(f$ci.ub),standard_error=f$se)),auto_unbox=TRUE,digits=16)'
        expected = json.loads(str(r_bridge.execute_r_string("{" + expression + "}")[0]))
        actual = _parse_result_table(view.texts["Subgroup Summary"])
        for label, row in zip(("Adjuvant", "Neoadjuvant", "Concomitant", "Overall"), expected, strict=True):
            for key, value in row.items():
                assert abs(actual[f"model.{_result_row_key(label)}.{key}"] - value) <= 1.1e-6, (label, actual, expected)
        record("bundled-hr-timing-subgroup-metafor-comparison", view, actual=actual, expected=expected, plots=dict(view.results.display_images or view.results.images))
        view.close(); app.processEvents()
    else:
        def descriptive_bias(dialog):
            report = dialog._eligibility_report
            assert report is not None and report.usable_studies == 9
            assert report.methods and not any(item.available for item in report.methods)
            assert "9 eligible" in dialog.context_label.text()
            assert "No formal asymmetry test" in dialog.automatic_test_label.text()
            assert dialog.ordinary_funnel_check.isEnabled()
            dialog.ordinary_funnel_check.setChecked(True)
            dialog.contour_funnel_check.setChecked(True)
            record("bundled-irr-nine-study-eligibility", dialog, context=dialog.context_label.text(), eligibility={"usable_studies": report.usable_studies, "methods": [item.to_mapping() for item in report.methods]})
            dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click(); app.processEvents()
            assert not dialog.failure_label.isVisible(), dialog.failure_label.text()
        modal(app, PublicationBiasDialog, descriptive_bias, window.action_publication_bias.trigger)
        view = visible(results_window.ResultsWindow)
        assert any("contour" in key for key in view.results.images)
        assert "requires at least 10 usable studies" in "\n".join(view.texts.values())
        record("bundled-irr-descriptive-funnels", view, texts=dict(view.texts), plots=dict(view.results.display_images or view.results.images))
        view.close(); app.processEvents()
    copy_path = Path(sys.argv[2]) / filename
    window.out_path = str(copy_path)
    assert window.save() and window.open(str(copy_path), raise_on_error=True)
    check_inputs()
    assert load_project(copy_path).project == original.project
    record("bundled-ratio-sample-reopened", window, sample=filename, copy=str(copy_path))
