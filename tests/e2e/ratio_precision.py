"""Original-source precision through each HR/IRR study dialog input mode."""
import json
import math
from dataclasses import asdict
from pathlib import Path

from PyQt6 import QtCore, QtWidgets
from tests.python.gui.qt_test_support import key_click, key_clicks


def run(app, window, work, record):
    from advanced_workflows import modal, click
    from rc_metastudio import r_bridge
    from rc_metastudio.calculators.ratio_dialog import RatioDataDialog
    from tests.e2e.analysis_presentation_workflows import analyze_existing
    from tests.fit_observations import observe_fit
    root = Path(__file__).resolve().parents[2]
    for metric, sample, modes in (
        ('HR','Pignon2000-HR', ('ratio','log')),
        ('IRR','NielWeise2008-IRR', ('raw','ratio','log')),
    ):
        for mode in modes:
            window.workspace.mark_saved()
            assert window.open(str(root/'sample_projects'/(sample+'.rcms')), raise_on_error=True)
            def sheet_confidence(level):
                from rc_metastudio.confidence_level_dialog import ConfidenceLevelDialog
                def change(dialog):
                    dialog.confidence_level_spinbox.setValue(level)
                    click(app, dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
                modal(app, ConfidenceLevelDialog, change, window.action_change_confidence_level.trigger)
                assert window.model.get_confidence_level() == level
            if mode == 'ratio':
                sheet_confidence(90)
            def text(field, value):
                field.setFocus()
                key_click(field, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier)
                key_clicks(field, value)
                key_click(field, QtCore.Qt.Key.Key_Tab)
                app.processEvents()
            def drive(dialog):
                if metric == 'IRR':
                    dialog.fields['source'].setCurrentIndex(dialog.fields['source'].findData('raw' if mode == 'raw' else 'reported'))
                if mode == 'raw':
                    for field, value in zip(dialog.raw_fields, ('1e6','1.2345678901234567e-8','5','1e12')):
                        text(field, value)
                else:
                    dialog.fields['scale'].setCurrentIndex(dialog.fields['scale'].findData(mode))
                    text(dialog.fields['estimate'], '0,12345678901234566')
                    if mode == 'ratio':
                        text(dialog.fields['confidence'], '90')
                        text(dialog.fields['lower'], '1.2345678901234567e-8')
                        text(dialog.fields['upper'], '1e12')
                    else:
                        text(dialog.fields['se'], '1.2345678901234567e-8')
                record('ratio-precision-keyboard', dialog, metric=metric, mode=mode)
                click(app, dialog.findChild(QtWidgets.QDialogButtonBox).button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
            modal(app, RatioDataDialog, drive, lambda: window.tableView.row_header_clicked(0))
            unit = window.model.get_current_analysis_unit_for_study(0)
            expected = asdict(unit.ratio_input(window.model.arm_names))
            raw = list(unit.get_raw_data_for_arms(window.model.arm_names))
            if mode == 'raw':
                assert raw == [1e6,1.2345678901234567e-8,5,1e12], raw
            else:
                assert expected['estimate'] == .12345678901234566, expected
                assert expected['lower'] == 1.2345678901234567e-8 if mode == 'ratio' else expected['se'] == 1.2345678901234567e-8
            window.action_undo.trigger()
            window.action_redo.trigger()
            assert window.save(destination=work/(metric+'-'+mode+'.rcms')) and window.open(window.workspace.path, raise_on_error=True)
            unit = window.model.get_current_analysis_unit_for_study(0)
            assert asdict(unit.ratio_input(window.model.arm_names)) == expected
            assert unit.get_raw_data_for_arms(window.model.arm_names) == raw
            with observe_fit() as fit:
                view = analyze_existing(app, window, 'standard', 'time_to_event.random' if metric == 'HR' else 'event_rates.random', record,
                                        parameters={'digits':6,'rm.method':'DL','inference.method':'z'})
            if mode == 'raw':
                expression = f'metafor::escalc("IRR", x1i={raw[0]}, t1i={raw[1]}, x2i={raw[2]}, t2i={raw[3]})'
                expected_effect, expected_se = math.log(raw[0]/raw[1]/(raw[2]/raw[3])), math.sqrt(1/raw[0]+1/raw[2])
            elif mode == 'log':
                expression = f'data.frame(yi={expected["estimate"]}, vi={expected["se"]}^2)'
                expected_effect, expected_se = expected['estimate'], expected['se']
            else:
                expression = f'metafor::conv.wald(out={expected["estimate"]},ci.lb={expected["lower"]},ci.ub={expected["upper"]},level={expected["confidence"]},transf=log)'
                # Direct public conversion, independently from RCMS's source-selection adapter.
                reference = json.loads(str(r_bridge.execute_r_string('jsonlite::toJSON('+expression+',digits=16)')[0]))[0]
                expected_effect, expected_se = reference['yi'], math.sqrt(reference['vi'])
            derived = fit.evaluate('c(result$input_data@y[1], result$input_data@SE[1])')
            assert math.isclose(float(derived[0]), expected_effect, abs_tol=1e-12)
            assert math.isclose(float(derived[1]), expected_se, rel_tol=1e-12, abs_tol=1e-15)
            if mode == 'ratio':
                from statistics import NormalDist
                assert math.isclose(expected_se, (math.log(expected['upper'])-math.log(expected['lower']))/(2*NormalDist().inv_cdf(.95)), rel_tol=1e-12)
                fit.evaluate('local({d<-result$input_data; ref<-metafor::rma.uni(d@y,sei=d@SE,method="DL"); stopifnot(max(abs(weights(ref)-weights(result$res)))<1e-6)})')
            record('ratio-precision-reopened-fit', view, metric=metric, mode=mode,
                   source=expected, raw=raw, expected_effect=expected_effect, expected_se=expected_se,
                   observed_effect=float(derived[0]), observed_se=float(derived[1]))
            view.close()
            if mode == 'ratio':
                assert expected['confidence'] == 90
                sheet_confidence(95)
                assert asdict(window.model.get_current_analysis_unit_for_study(0).ratio_input(window.model.arm_names)) == expected
                with observe_fit() as changed_confidence_fit:
                    view = analyze_existing(app, window, 'standard', 'time_to_event.random' if metric == 'HR' else 'event_rates.random', record,
                                            parameters={'digits':6,'rm.method':'DL','inference.method':'z'})
                after = changed_confidence_fit.evaluate('result$input_data@SE[1]')
                assert math.isclose(float(after[0]), expected_se, rel_tol=1e-12)
                weights = changed_confidence_fit.evaluate('local({d<-result$input_data; ref<-metafor::rma.uni(d@y,sei=d@SE,method="DL"); stopifnot(max(abs(weights(ref)-weights(result$res)))<1e-6); weights(ref)})')
                record('original-90-ci-after-sheet-95', view, source=expected, observed_se=float(after[0]), weights=list(weights))
                view.close()
            if mode in ('raw', 'ratio'):
                from xml.etree import ElementTree as ET
                from tests.e2e.plot_geometry_checks import check_annotation_spacing
                for style in ('revman', 'bmj'):
                    view = analyze_existing(app, window, 'standard', 'time_to_event.random' if metric == 'HR' else 'event_rates.random', record,
                                            parameters={'digits':6,'rm.method':'DL','inference.method':'z','fp_style':style})
                    check_annotation_spacing(view, style=style)
                    labels = [''.join(n.itertext()) for path in view.results.display_images.values()
                              for n in ET.parse(path).iter('{http://www.w3.org/2000/svg}text')]
                    assert any('e−' in text or 'e-' in text or 'e+' in text for text in labels), ('stress notation absent', metric, mode, style, labels)
                    if mode == 'ratio':
                        from statistics import NormalDist
                        from zipfile import ZipFile
                        from rc_metastudio.results.report import write_docx

                        fitted_lower = math.exp(expected_effect - NormalDist().inv_cdf(.975) * expected_se)
                        displayed = f'{fitted_lower:.1e}'.replace('e-', 'e−')
                        row = next(text for text in labels if text.startswith(f'{expected["estimate"]:.6f} '))
                        assert row.startswith((f'0.123457 [{displayed}, ', f'0.123457 ({displayed} to ')), row
                        study = next(table for section in view.results.sections for table in section.tables
                                     if table.role == 'study_results')
                        bound, = study.quantities[0][2]
                        assert bound.role == 'ci_lower' and bound.value is not None
                        assert math.isclose(bound.value, fitted_lower, rel_tol=1e-12), bound
                        assert study.rows[0][2] == displayed, study.rows[0]
                        assert displayed in view.manuscript.plain_text()
                        assert displayed in view.manuscript.html(supplementary=True) or displayed in view.manuscript.html()
                        docx = work / f'{metric}-{mode}-{style}.docx'
                        write_docx(view.manuscript, docx)
                        with ZipFile(docx) as document:
                            assert displayed in document.read('word/document.xml').decode('utf-8')
                    record('stress-journal-after-reopen', view, metric=metric, mode=mode, style=style,
                           source=expected, raw=raw, plots=dict(view.results.display_images))
                    view.close()
