"""Interact with Qt controls and drive modal dialogs in desktop scenarios."""

import traceback

from PyQt6 import QtCore, QtWidgets

from tests.python.gui.qt_test_support import mouse_click, wait


def click(app, widget):
    assert widget.isEnabled(), widget.objectName()
    mouse_click(widget, QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()


def modal(app, kind, drive, launch):
    """Tell the watchdog to expect a message before launching the modal loop."""
    errors = []
    completed = []
    poll = QtCore.QTimer()
    poll.setSingleShot(True)

    def ready():
        dialog = app.activeModalWidget()
        if not isinstance(dialog, kind):
            poll.start(10)
            return
        if isinstance(dialog, QtWidgets.QMessageBox):
            dialog.setProperty("verificationExpectedMessage", True)
        try:
            drive(dialog)
        except Exception as error:
            traceback.print_exc()
            errors.append(error)
            dialog.reject()
        finally:
            completed.append(True)

    poll.timeout.connect(ready)
    expecting_message = kind is QtWidgets.QMessageBox
    previous_expectation = app.property("verificationExpectingMessageBox")
    if expecting_message:
        app.setProperty("verificationExpectingMessageBox", True)
    try:
        poll.start(0)
        launch()
        deadline = QtCore.QDeadlineTimer(5000)
        while not completed and not deadline.hasExpired():
            wait(10)
        assert completed, ("modal did not open", kind)
        assert not errors, errors
    finally:
        poll.stop()
        if expecting_message:
            app.setProperty("verificationExpectingMessageBox", previous_expectation)


def set_parameter(app, dialog, key, value):
    from rc_metastudio.analysis.method_labels import parameter_display_label

    if key == "fp_style":
        from rc_metastudio.results.plot_defaults import PLOT_STYLE_LABELS
        dialog.style_cbo.setCurrentText(PLOT_STYLE_LABELS[value])
        app.processEvents()
        return

    plot_controls = {"bp_plot_lb": dialog.plot_lb_le, "bp_plot_ub": dialog.plot_ub_le,
                     "fp_plot_lb": dialog.plot_lb_le, "fp_plot_ub": dialog.plot_ub_le,
                     "fp_show_col3": dialog.show_3, "fp_show_col4": dialog.show_4}
    if key in plot_controls:
        control = plot_controls[key]
        if isinstance(control, QtWidgets.QCheckBox):
            control.setChecked(str(value).upper() == "TRUE")
        else:
            control.setText(str(value))
        app.processEvents()
        return
    label = parameter_display_label(key, dialog.param_d.get(key))
    controls = [
        w.buddy()
        for w in dialog.findChildren(QtWidgets.QLabel)
        if w.text().casefold() == label.casefold() and w.buddy() is not None
    ]
    assert controls, (key, label)
    control = controls[0]
    if isinstance(control, QtWidgets.QComboBox):
        index = control.findData(value)
        assert index >= 0, (key, value)
        control.setCurrentIndex(index)
    elif isinstance(control, QtWidgets.QCheckBox):
        control.setChecked(str(value).upper() == "TRUE")
    elif isinstance(control, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
        control.setValue(value)
    else:
        control.setText(str(value))
    app.processEvents()


def analyze_existing(app, window, workflow, method, record, parameters=None, *, covariates=('Dose',)):
    from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog
    from rc_metastudio.results import window as results_window
    from rc_metastudio.analysis.subgroup_dialog import SubgroupAnalysisDialog

    def visible(kind):
        return next(w for w in app.topLevelWidgets() if isinstance(w, kind) and w.isVisible())

    action = {"standard": window.action_go, "cumulative": window.action_cum_ma,
              "leave-one-out": window.action_loo_ma, "subgroup": window.action_subgroup_ma,
              "meta-regression": window.action_meta_regression}[workflow]
    action.trigger()
    app.processEvents()
    if workflow == "subgroup":
        subgroup = visible(SubgroupAnalysisDialog)
        subgroup.covariate_combo_box.setCurrentIndex(subgroup.covariate_combo_box.findText("Group"))
        mouse_click(subgroup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok), QtCore.Qt.MouseButton.LeftButton)
    dialog = visible(analysis_setup_dialog.AnalysisSetupDialog)
    if workflow == "meta-regression":
        for covariate, checkbox in dialog.covs_and_check_boxes:
            checkbox.setChecked(covariate["name"] in covariates)
    else:
        dialog.method_cbo_box.setCurrentIndex(dialog.method_cbo_box.findData(method))
    app.processEvents()
    for key, value in {"digits": 6, **(parameters or {})}.items():
        set_parameter(app, dialog, key, value)
    from tests.e2e.keyboard_navigation import keyboard_traversal
    parameter_controls = [control for control in dialog.current_widgets if control.focusPolicy() & QtCore.Qt.FocusPolicy.TabFocus]
    keyboard_traversal(app, dialog, [dialog.method_cbo_box, *parameter_controls,
                       dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok),
                       dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)], record, "setup")
    if workflow == "meta-regression":
        from tests.e2e.keyboard_navigation import keyboard_dialog_pages
        keyboard_dialog_pages(app, dialog, record)
    record("round3-configured", dialog, workflow=workflow, method=method, parameters=dialog.current_param_vals)
    mouse_click(dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok), QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()
    view = visible(results_window.ResultsWindow)
    view.resize(1500, 850)
    app.processEvents()
    return view
