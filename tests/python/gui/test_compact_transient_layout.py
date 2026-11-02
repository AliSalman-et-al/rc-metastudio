import json
import os
from pathlib import Path
import subprocess
import sys
from typing import cast

import pytest
from PyQt6 import QtCore, QtGui, QtWidgets


ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("RCMS_QT6_BUILD_ROOT", str(ROOT / "build" / "qt6-verification"))
from rc_metastudio.qt6_ui import prepare_generated_ui_imports
from test_types import key_click, required

prepare_generated_ui_imports()
LONG_VALUE = "A representative translated value with complete required content " * 20


def _show(window, qapp):
    window.show()
    qapp.processEvents()
    qapp.processEvents()




def _frame_margins(window):
    frame = window.frameGeometry()
    return QtCore.QSize(
        max(0, frame.width() - window.width()),
        max(0, frame.height() - window.height()),
    )


def _pixmap_logical_size(pixmap):
    ratio = max(1.0, pixmap.devicePixelRatioF())
    return QtCore.QSize(round(pixmap.width() / ratio), round(pixmap.height() / ratio))


def _assert_content_preferred_outer_size(window, available, fraction, tolerance=6):
    hint = window.sizeHint().expandedTo(window.minimumSizeHint())
    frame_extra = _frame_margins(window)
    expected_width = min(
        hint.width() + frame_extra.width(), int(available.width() * fraction)
    )
    expected_height = min(
        hint.height() + frame_extra.height(), int(available.height() * fraction)
    )
    frame = window.frameGeometry()
    assert abs(frame.width() - expected_width) <= tolerance
    assert abs(frame.height() - expected_height) <= tolerance




def _remaining_surface_inventory():
    from rc_metastudio import about_legal_dialog
    from rc_metastudio import add_new_dialogs
    from rc_metastudio import edit_name_dialogs
    from rc_metastudio import launch
    from rc_metastudio import main_window
    from rc_metastudio import progress_dialog

    surfaces = [
        ("add-study", "compact", add_new_dialogs.AddStudyDialog()),
        ("add-covariate", "choice", add_new_dialogs.AddCovariateDialog()),
        (
            "edit-group-name",
            "compact",
            edit_name_dialogs.EditGroupNameDialog("Treatment group"),
        ),
        (
            "edit-covariate-name",
            "compact",
            edit_name_dialogs.EditCovariateNameDialog("Baseline risk"),
        ),
        ("about-legal", "about", about_legal_dialog.AboutLegalDialog()),
        (
            "import-progress",
            "progress",
            main_window.ImportProgressDialog(min_=0, max_=100),
        ),
        ("shared-progress", "progress", progress_dialog.AnalysisProgressDialog()),
        ("startup-splash", "splash", launch.create_startup_splash()),
    ]
    for _name, kind, window in surfaces:
        for line_edit in window.findChildren(QtWidgets.QLineEdit):
            line_edit.setText(LONG_VALUE)
        if kind == "choice":
            combo = required(window.findChild(QtWidgets.QComboBox), "choice combo")
            combo.addItem(LONG_VALUE)
            combo.setCurrentText(LONG_VALUE)
        if kind == "progress":
            progress_control = cast(
                QtWidgets.QProgressBar,
                required(getattr(window, "progress_bar", None), "progress bar"),
            )
            progress_control.setFormat("Loading analysis resources: %p%")
        if kind == "splash":
            cast(QtWidgets.QSplashScreen, window).showMessage(LONG_VALUE)
    return surfaces

def test_choice_control_state_is_typed_and_rejects_stale_ownership(qapp):
    from rc_metastudio import adaptive_controls

    unconfigured = adaptive_controls.AdaptiveComboBox()
    with pytest.raises(LookupError, match="not configured"):
        adaptive_controls.choice_control_controller(unconfigured)

    owner = adaptive_controls.AdaptiveComboBox()
    stale_target = adaptive_controls.AdaptiveComboBox()
    controller = adaptive_controls.configure_choice_control(owner)
    setattr(stale_target, "_adaptive_choice_controller", controller)
    with pytest.raises(LookupError, match="stale ownership"):
        adaptive_controls.choice_control_controller(stale_target)

    assert adaptive_controls.choice_control_controller(owner) is controller




def test_about_legal_has_explicit_overflow_and_reachable_action(qapp):
    from rc_metastudio import about_legal_dialog

    dialog = about_legal_dialog.AboutLegalDialog()
    dialog.content_scroll_area.setHtml("<p>{}</p>".format(LONG_VALUE * 8))
    enlarged = QtGui.QFont(dialog.font())
    enlarged.setPointSize(max(16, enlarged.pointSize() + 6))
    dialog.setFont(enlarged)
    dialog.resize(420, 300)
    _show(dialog, qapp)
    try:
        close_button = required(
            dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Close),
            "close button",
        )
        from rc_metastudio import adaptive_window

        assert (
            adaptive_window.adaptive_window_state(dialog).policy.archetype
            is adaptive_window.WindowArchetype.TRANSACTIONAL
        )
        assert (
            required(
                dialog.content_scroll_area.verticalScrollBar(), "vertical scrollbar"
            ).maximum()
            > 0
        )
        assert close_button.isVisible()
        assert not dialog.content_scroll_area.isAncestorOf(close_button)
        assert dialog.content_scroll_area.lineWrapMode() != (
            QtWidgets.QTextEdit.LineWrapMode.NoWrap
        )
        assert dialog.content_scroll_area.tabChangesFocus()
        assert dialog.content_scroll_area.accessibleName()
        assert close_button.objectName() == "about_legal_close_button"
        assert close_button.accessibleName()
        assert close_button.focusPolicy() & QtCore.Qt.FocusPolicy.TabFocus
        dialog.content_scroll_area.setFocus(QtCore.Qt.FocusReason.TabFocusReason)
        qapp.processEvents()
        assert qapp.focusWidget() is dialog.content_scroll_area
        press = QtGui.QKeyEvent(
            QtCore.QEvent.Type.KeyPress,
            QtCore.Qt.Key.Key_Tab,
            QtCore.Qt.KeyboardModifier.NoModifier,
        )
        release = QtGui.QKeyEvent(
            QtCore.QEvent.Type.KeyRelease,
            QtCore.Qt.Key.Key_Tab,
            QtCore.Qt.KeyboardModifier.NoModifier,
        )
        QtCore.QCoreApplication.sendEvent(dialog, press)
        QtCore.QCoreApplication.sendEvent(dialog, release)
        qapp.processEvents()
        assert qapp.focusWidget() is close_button
    finally:
        dialog.close()
        qapp.processEvents()


def test_all_progress_entry_points_are_minimal_stable_transient_windows(qapp):
    progress_surfaces = [
        entry for entry in _remaining_surface_inventory() if entry[1] == "progress"
    ]
    try:
        for name, _kind, dialog in progress_surfaces:
            _show(dialog, qapp)
            _assert_content_preferred_outer_size(
                dialog, qapp.primaryScreen().availableGeometry(), 1.0
            )
            frame = QtCore.QRect(dialog.frameGeometry())
            assert frame.width() < 480, name
            assert frame.height() < 160, name
            dialog.progress_bar.setValue(dialog.progress_bar.maximum())
            qapp.processEvents()
            assert dialog.frameGeometry() == frame, name
    finally:
        for _name, _kind, dialog in progress_surfaces:
            dialog.close()
        qapp.processEvents()


def test_bounded_dpr_splash_preserves_its_logical_size(qapp):
    from rc_metastudio import launch

    source = QtGui.QPixmap(800, 600)
    source.fill(QtGui.QColor("navy"))
    source.setDevicePixelRatio(2.0)

    bounded = launch.screen_bounded_splash_pixmap(source, QtCore.QSize(500, 400))

    assert bounded.devicePixelRatioF() == 2.0
    assert bounded.size() == QtCore.QSize(800, 600)
    assert _pixmap_logical_size(bounded) == QtCore.QSize(400, 300)


def test_oversized_dpr_splash_is_bounded_without_double_scaling(qapp):
    from rc_metastudio import launch

    source = QtGui.QPixmap(1600, 1200)
    source.fill(QtGui.QColor("navy"))
    source.setDevicePixelRatio(2.0)

    bounded = launch.screen_bounded_splash_pixmap(source, QtCore.QSize(500, 320))
    logical_width = bounded.width() / bounded.devicePixelRatioF()
    logical_height = bounded.height() / bounded.devicePixelRatioF()

    assert bounded.devicePixelRatioF() == 2.0
    assert logical_width <= 500
    assert logical_height <= 320
    assert logical_width > 400
    assert abs((logical_width / logical_height) - (4.0 / 3.0)) < 0.01
