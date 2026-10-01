# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()

from rc_metastudio.progress_dialog import AnalysisProgressDialog


def test_progress_is_nonmodal_and_stop_stays_pending_until_worker_reply(qapp):
    progress = AnalysisProgressDialog()
    requests = []
    progress.stop_requested.connect(lambda: requests.append(True))
    try:
        progress.show()
        assert progress.windowModality() == Qt.WindowModality.NonModal
        progress.stop_button.click()
        assert requests == [True]
        assert not progress.stop_button.isEnabled()
        assert "Stopping" in progress.stage_label.text()
        progress.request_stop()
        assert requests == [True]
    finally:
        progress.hide()
        progress.deleteLater()
        qapp.processEvents()
