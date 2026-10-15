"""Targeted native release proof using the production desktop composition."""
import os
from pathlib import Path
import sys
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / '.agents/skills/verify-rcms/scripts')]
mode = sys.argv[1]
work = HERE / 'raw' / mode
work.mkdir(parents=True, exist_ok=False)
sys.argv = [__file__, 'doctor', str(work)]
os.environ['RCMS_E2E_EVIDENCE_DIR'] = str(work)
os.environ['RCMS_REQUIRE_IN_PROCESS_RPY2'] = '1'
os.environ['RCMS_ANALYSIS_SCRATCH_DIR'] = str(work / 'analysis-scratch')
(work / 'analysis-scratch').mkdir()
driver = ROOT / 'tests/e2e/desktop_driver.py'
ns = {'__file__': str(driver), '__name__': 'release_driver'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0], str(driver), 'exec'), ns)
from rc_metastudio import automation
from PyQt6 import QtCore
QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope, str(work))
with patch('rc_metastudio.settings.get_base_path', return_value=str(work)):
    app, window = automation.start_automation()
    try:
        ns.update(app=app, window=window)
        sys.excepthook = sys.__excepthook__
        ns['doctor'](app, window)
        if mode.startswith('headers') or mode.startswith('baseline'):
            from tests.e2e.round6_polish import run_headers
            run_headers(app, window, work, ns['record_step'])
        elif mode.startswith('presentation'):
            from tests.e2e.release_fixes import run_presentation
            run_presentation(app, window, work, ns['record_step'])
        else:
            from tests.e2e.release_fixes import run_coefficients
            run_coefficients(app, window, work, ns['record_step'])
        print('WORKFLOW PASSED', flush=True)
    finally:
        window.workspace.mark_saved()
        for widget in app.topLevelWidgets():
            widget.close()
        automation.dispose_qobjects(app, app.topLevelWidgets())
        app.quit()
