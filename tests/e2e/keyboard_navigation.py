"""Real Tab/Backtab traversal and dialog-page accessibility checks."""

from PyQt6 import QtCore, QtWidgets
from tests.python.gui.qt_test_support import key_click, required, wait


def keyboard_traversal(app, window, controls, record, surface):
    """Use actual Tab events; retain the visited focus sequence and final ring."""
    controls = [control for control in controls if control.isEnabled() and control.isVisible()]
    assert controls, surface
    window.raise_()
    window.activateWindow()
    controls[0].setFocus(QtCore.Qt.FocusReason.TabFocusReason)
    wait(80)
    visited, reached = [], set()
    for _ in range(300):
        focus = app.focusWidget()
        assert focus is not None, (surface, visited)
        for index, control in enumerate(controls):
            if control is focus or control.isAncestorOf(focus):
                reached.add(index)
        visited.append(focus.accessibleName() or focus.objectName() or type(focus).__name__)
        if len(reached) == len(controls):
            break
        modifier = QtCore.Qt.KeyboardModifier.NoModifier
        key_click(focus, QtCore.Qt.Key.Key_Tab, modifier)
        app.processEvents()
    assert len(reached) == len(controls), (surface, reached, [c.objectName() for c in controls], visited)
    record("round5-keyboard-" + surface, window, focus_sequence=visited)


def keyboard_dialog_pages(app, dialog, record):
    assert dialog.style_group.title() == "Plot style"
    assert dialog.random_effects_radio.text() == "Random effects"
    assert dialog.fixed_effects_radio.text() == "Fixed effects"
    selected = dialog.specs_tab.currentIndex()
    for index in range(dialog.specs_tab.count()):
        if not dialog.specs_tab.isTabEnabled(index):
            continue
        dialog.specs_tab.setCurrentIndex(index)
        app.processEvents()
        page = dialog.specs_tab.widget(index)
        radio_groups = []
        for radio in page.findChildren(QtWidgets.QRadioButton):
            if not radio.isVisible() or not radio.isEnabled() or not radio.isChecked():
                continue
            group = radio.group()
            buttons = group.buttons() if group else radio.parentWidget().findChildren(
                QtWidgets.QRadioButton, options=QtCore.Qt.FindChildOption.FindDirectChildrenOnly)
            buttons = [button for button in buttons if button.isVisible() and button.isEnabled()]
            radio.setFocus()
            visited = set()
            for _ in range(len(buttons)):
                visited.add(app.focusWidget())
                key_click(required(app.focusWidget()), QtCore.Qt.Key.Key_Right)
                app.processEvents()
            assert visited == set(buttons), ("radio arrow traversal", visited, buttons)
            radio.setFocus()
            key_click(radio, QtCore.Qt.Key.Key_Space)
            app.processEvents()
            assert radio.isChecked(), ("radio selection restoration", radio.text())
            radio_groups.append([button.text() for button in buttons])
        if radio_groups:
            record("round5-radio-setup-page-" + str(index), dialog, groups=radio_groups)
        controls = [widget for widget in page.findChildren(QtWidgets.QWidget)
                    if isinstance(widget, (QtWidgets.QAbstractButton, QtWidgets.QComboBox,
                                           QtWidgets.QAbstractSpinBox, QtWidgets.QLineEdit))
                    and not isinstance(widget.parentWidget(), (QtWidgets.QAbstractSpinBox, QtWidgets.QComboBox))
                    and widget.focusPolicy() & QtCore.Qt.FocusPolicy.TabFocus
                    and (not isinstance(widget, QtWidgets.QRadioButton) or widget.isChecked())]
        if any(control.isVisible() and control.isEnabled() for control in controls):
            keyboard_traversal(app, dialog, controls, record, "setup-page-" + str(index))
    dialog.specs_tab.setCurrentIndex(selected)
    app.processEvents()
