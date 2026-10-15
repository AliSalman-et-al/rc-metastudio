"""Finish only the case missing after the interrupted prediction helper."""
import os,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
work=HERE/'raw/prediction-remaining';work.mkdir(parents=True,exist_ok=True)
sys.argv=['prediction_remaining.py','doctor',str(work)]
os.environ['RCMS_E2E_EVIDENCE_DIR']=str(work);os.environ['RCMS_REQUIRE_IN_PROCESS_RPY2']='1';os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(work/'scratch');(work/'scratch').mkdir(exist_ok=True)
driver=ROOT/'tests/e2e/desktop_driver.py';ns={'__file__':str(driver),'__name__':'audit_prediction_remaining'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0],str(driver),'exec'),ns)
from rc_metastudio import automation
from PyQt6 import QtCore
source=(ROOT/'tests/e2e/reviewer_fixes.py').read_text()
needle="        for style in ('default', 'revman', 'bmj'):\n"
source=source.replace(needle,needle+"            if (measure, workflow, style) != ('PFT', 'subgroup', 'bmj'): continue\n",1)
review={'__name__':'audit_reviewer_fixes'};exec(compile(source,'<audit filtered reviewer_fixes>', 'exec'),review)
QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat,QtCore.QSettings.Scope.UserScope,str(work))
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=automation.start_automation();ns['app']=app
 try:
  ns['doctor'](app,window)
  review['run_predictions'](app,window,work,ns['record_step'])
 finally:
  window.workspace.mark_saved()
  for w in app.topLevelWidgets():w.close()
  automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
