"""Entered OR/MD source confidence survives output confidence changes."""
from PyQt6 import QtWidgets


def check(app, window, kind, launch, text, family, record):
    from advanced_workflows import modal, click
    from rc_metastudio import r_bridge
    from rc_metastudio.confidence_level_dialog import ConfidenceLevelDialog
    from tests.e2e.audit_round3 import analyze_existing

    def confidence(level):
        def change(dialog):
            dialog.confidence_level_spinbox.setValue(level)
            click(app, dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
        modal(app, ConfidenceLevelDialog, change, window.action_change_confidence_level.trigger)
        assert window.model.get_confidence_level() == level

    confidence(90)
    metric = "OR" if family == "binary" else "MD"
    window.model.set_current_metric(metric)
    window.model.hydrate_derived_previews()
    window.model.reset_model()
    assert window.model.current_effect == metric
    bounds = (2, 1, 4) if family == "binary" else (2, 1, 3)

    def enter(dialog):
        dialog.input_mode_combo.setCurrentIndex(dialog.input_mode_combo.findData("estimate"))
        click(app, dialog.clear_button)
        dialog.effect_combo_box.setCurrentIndex(dialog.effect_combo_box.findData(metric))
        for field, value in zip((dialog.effect_text_box, dialog.lower_text_box, dialog.upper_text_box), bounds):
            text(field, value)
        click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))

    modal(app, kind, enter, launch)
    confidence(95)
    assert window.save() and window.open(window.out_path, raise_on_error=True)
    unit = window.model.get_current_analysis_unit_for_study(0)
    assert all(v in (None, "") for v in unit.get_raw_data_for_arms(window.model.arm_names))
    view = analyze_existing(app, window, "standard", family + ".random", record,
                            parameters={"digits": 6, "rm.method": "DL", "inference.method": "z"})
    transform = "log" if family == "binary" else "identity"
    expected = float(r_bridge.execute_r_string(
        f"({transform}({bounds[2]})-{transform}({bounds[1]}))/(2*qnorm(.95))")[0])
    metafor_se = float(r_bridge.execute_r_string(
        f"sqrt(metafor::conv.wald(out={bounds[0]}, ci.lb={bounds[1]}, ci.ub={bounds[2]}, level=90, transf={transform})$vi)")[0])
    assert abs(metafor_se - expected) < 1e-12
    actual = float(r_bridge.execute_r_string("result$input_data@SE[1]")[0])
    record("entered-90-ci-after-sheet-95", view, metric=metric, bounds=bounds,
           expected_se=expected, actual_se=actual)
    assert abs(actual - expected) < 1e-6, (metric, actual, expected)
    view.close()
