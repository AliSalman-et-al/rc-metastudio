import os
from pathlib import Path
from qt_test_support import required

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("RCMS_QT6_BUILD_ROOT", str(ROOT / "build" / "qt6-verification"))

from PyQt6 import QtWidgets
from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()


def test_parented_application_wizard_does_not_inherit_shell_width(qapp):
    from rc_metastudio import main_wizard

    parent = QtWidgets.QMainWindow()
    parent.resize(1600, 900)
    parent.show()
    qapp.processEvents()

    wizard = main_wizard.MainWizard(parent=parent)
    try:
        wizard.show()
        qapp.processEvents()
        qapp.processEvents()

        page = required(wizard.currentPage(), "current wizard page")

        assert wizard.width() <= int(parent.width() * 0.75)
        assert (
            page.width()
            >= required(page.parentWidget(), "wizard parent").contentsRect().width() - 4
        )
    finally:
        wizard.close()
        parent.close()
        qapp.processEvents()
