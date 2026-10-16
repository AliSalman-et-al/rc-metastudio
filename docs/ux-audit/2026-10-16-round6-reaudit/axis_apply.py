"""Prove scale Apply, a later draft Cancel, reopen, exports and rerun through Qt/R."""
import os,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
work=HERE/'raw/axis-apply';work.mkdir(parents=True,exist_ok=True)
sys.argv=['axis_apply.py','doctor',str(work)]
os.environ['RCMS_E2E_EVIDENCE_DIR']=str(work);os.environ['RCMS_REQUIRE_IN_PROCESS_RPY2']='1';os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(work/'scratch');(work/'scratch').mkdir(exist_ok=True)
driver=ROOT/'tests/e2e/desktop_driver.py';ns={'__file__':str(driver),'__name__':'audit_prediction_remaining'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0],str(driver),'exec'),ns)
from rc_metastudio import automation
from PyQt6 import QtCore
source=(ROOT/'tests/e2e/axis_conventions.py').read_text()
needle="                        click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))"
replacement="""                        click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Apply))
                        assert dialog.isVisible() and dialog.axis_scale.currentData() == other
                        record('axis-apply-before-cancel',dialog,measure=measure,style=style,applied=other)
                        dialog.axis_scale.setCurrentIndex(dialog.axis_scale.findData(expected_default))
                        click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel))"""
assert source.count(needle)==1
source=source.replace(needle,replacement)
review={'__name__':'audit_axis_apply'};exec(compile(source,'<audit Apply variant of axis_conventions>','exec'),review)
QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat,QtCore.QSettings.Scope.UserScope,str(work))
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=automation.start_automation();ns['app']=app;ns['window']=window;sys.excepthook=sys.__excepthook__
 try:
  ns['doctor'](app,window)
  for family in ('proportions','others'):
   review['run'](app,window,work,ns['record_step'],family)
 finally:
  window.workspace.mark_saved()
  for w in app.topLevelWidgets():w.close()
  automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
