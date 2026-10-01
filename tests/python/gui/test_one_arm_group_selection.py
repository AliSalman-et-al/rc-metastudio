# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

from rc_metastudio import automation
from rc_metastudio.settings import get_sample_projects_path


def test_selecting_one_arm_keeps_a_valid_group_index():
    app, window = automation.start_automation()
    try:
        window.workspace.mark_saved()
        assert window.open(str(Path(get_sample_projects_path()) / "amino.rcms"), raise_on_error=True)
        first_group = window.model.get_current_groups()[0]

        window.display_groups([first_group])

        assert window.model.get_current_groups() == [first_group]
        assert window.model.group_index_b == window.model.group_index_a
    finally:
        window._raw_preview_timer.stop()
        window.workspace.mark_saved()
        window.close()
        app.processEvents()
