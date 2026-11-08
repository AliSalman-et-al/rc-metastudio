"""Keep fixed analysis buttons reachable when a short tab grows."""

from PyQt6 import QtCore, QtWidgets


def check(app, form, sample, record):
    from tests.python.gui.test_types import mouse_click, wait

    screen = form.screen()
    assert screen is not None
    available = screen.availableGeometry()
    frame = form.frameGeometry()
    target = QtCore.QPoint(available.center().x() - frame.width() // 2,
                          available.bottom() - frame.height() - 12)
    form.move(form.pos() + target - frame.topLeft())
    app.processEvents()
    before = form.frameGeometry()
    assert available.contains(before), (sample, before, available)
    tabs = form.specs_tab
    plots = next(i for i in range(tabs.count()) if tabs.tabText(i).casefold() == 'plots')
    bar = tabs.tabBar()
    assert bar is not None
    mouse_click(bar, QtCore.Qt.MouseButton.LeftButton, pos=bar.tabRect(plots).center())
    wait(250)
    app.processEvents()
    buttons = [form.buttonBox.button(role) for role in (
        QtWidgets.QDialogButtonBox.StandardButton.Ok, QtWidgets.QDialogButtonBox.StandardButton.Cancel)]
    record('analysis-plots-working-area', form, sample=sample, available=available.getRect(),
           before=before.getRect(), after=form.frameGeometry().getRect(),
           buttons=[button.mapToGlobal(button.rect().center()).y() for button in buttons if button is not None])
    assert available.contains(form.frameGeometry()), (sample, available, before, form.frameGeometry())
    for button in buttons:
        assert button is not None and button.isVisible() and button.isEnabled()
        assert available.contains(button.mapToGlobal(button.rect().center()))
    scrollbar = form.content_scroll_area.verticalScrollBar()
    assert scrollbar is not None
    scrollbar.setValue(scrollbar.maximum())
    app.processEvents()
    assert available.contains(form.frameGeometry())
    tabs.setCurrentIndex(0)
    app.processEvents()
