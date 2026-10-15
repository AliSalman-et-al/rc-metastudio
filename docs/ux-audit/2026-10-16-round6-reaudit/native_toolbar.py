"""Recover only the custom post-design toolbar tooltip captures."""
from pathlib import Path
import hashlib,json,os,sys
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
work=HERE/'raw/toolbar-recovery';work.mkdir(exist_ok=True)
sys.argv=['native_toolbar.py','doctor',str(work)];os.environ['RCMS_E2E_EVIDENCE_DIR']=str(work);os.environ['RCMS_REQUIRE_IN_PROCESS_RPY2']='1';os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(work/'scratch');(work/'scratch').mkdir(exist_ok=True)
driver=ROOT/'tests/e2e/desktop_driver.py';ns={'__file__':str(driver),'__name__':'audit_toolbar_recovery'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0],str(driver),'exec'),ns)
from PyQt6 import QtCore,QtGui,QtWidgets,sip
from PyQt6.QtTest import QTest
from rc_metastudio import automation
rows=[];properties=[]
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=automation.start_automation();sys.excepthook=sys.__excepthook__;ns.update(app=app,window=window)
 try:
  ns['doctor'](app,window);assert window.open(str(ROOT/'sample_projects/amino.rcms'),raise_on_error=True)
  window.showMaximized();window.raise_();window.activateWindow();app.processEvents();QTest.qWait(250)
  for bar in window.findChildren(QtWidgets.QToolBar):
   if sip.isdeleted(bar) or not bar.isVisible():continue
   for action in list(bar.actions()):
    if sip.isdeleted(action):continue
    button=bar.widgetForAction(action)
    if not button or not button.isVisible() or not action.toolTip():continue
    point=button.rect().center();event=QtGui.QHelpEvent(QtCore.QEvent.Type.ToolTip,point,button.mapToGlobal(point))
    QtWidgets.QApplication.sendEvent(button,event);app.processEvents();QTest.qWait(150)
    assert QtWidgets.QToolTip.isVisible(),action.text()
    properties.append({'text':action.text(),'tooltip':action.toolTip(),'shown_tooltip':QtWidgets.QToolTip.text(),'enabled':action.isEnabled()})
    origin=window.mapToGlobal(QtCore.QPoint(0,0));p=work/'captures'/('toolbar-'+str(len(rows)).zfill(2)+'.png');p.parent.mkdir(exist_ok=True)
    assert window.screen().grabWindow(0,origin.x(),origin.y(),window.width(),window.height()).save(str(p),'PNG')
    rows.append({'path':str(p.relative_to(HERE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'capture':'Native QScreen desktop-composite of owned maximized client','tooltip':QtWidgets.QToolTip.text(),'action':action.text()})
    QtWidgets.QToolTip.hideText();app.processEvents()
  assert len(rows)>=5,len(rows)
  (HERE/'TOOLBAR-RECOVERY.json').write_text(json.dumps(rows,indent=2)+'\n');(HERE/'TOOLBAR.json').write_text(json.dumps(properties,indent=2)+'\n')
 finally:
  window.workspace.mark_saved()
  for w in app.topLevelWidgets():w.close()
  automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
