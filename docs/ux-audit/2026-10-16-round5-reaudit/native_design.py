"""Native X11 start-page, results navigation and toolbar-tooltip audit."""
import sys,os,json,hashlib
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
work=HERE/'raw'/'native-design';work.mkdir(parents=True,exist_ok=True)
sys.argv=['native_design.py','doctor',str(work)];os.environ['RCMS_E2E_EVIDENCE_DIR']=str(work)
os.environ['RCMS_REQUIRE_IN_PROCESS_RPY2']='1'
os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(work/'analysis-scratch');(work/'analysis-scratch').mkdir(exist_ok=True)
driver=ROOT/'tests/e2e/desktop_driver.py';ns={'__file__':str(driver),'__name__':'audit_design'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0],str(driver),'exec'),ns)
from PyQt6.QtTest import QTest
from rc_metastudio import automation
from tests.e2e.review1_design import run
from PyQt6 import QtWidgets,QtCore
rows=[]
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=automation.start_automation();sys.excepthook=sys.__excepthook__;ns['app']=app
 try:
  ns['doctor'](app,window)
  def record(action,*widgets,**observations):
   ns['record_step'](action,*widgets,**observations)
   for widget in widgets:
    widget.raise_();widget.activateWindow();app.processEvents();QTest.qWait(500)
    name='design-'+str(len(rows)).zfill(2)+'-'+action+'.png';p=HERE/'screenshots'/name
    assert app.platformName()=='xcb' and widget.windowHandle().isExposed()
    assert widget.screen().grabWindow(int(widget.winId())).save(str(p),'PNG')
    rows.append(dict(path=str(p.relative_to(HERE)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),capture='QScreen.grabWindow',action=action,observations=observations))
    (HERE/'DESIGN.json').write_text(json.dumps(rows,indent=2)+'\n')
  run(app,window,work,ROOT,record,ns['analyze'])
  toolbar=[]
  for bar in window.findChildren(QtWidgets.QToolBar):
   for action in bar.actions():
    button=bar.widgetForAction(action)
    if not button or not button.isVisible():continue
    QTest.mouseMove(button,button.rect().center());QTest.qWait(1000)
    record('toolbar-tooltip',window,text=action.text(),tooltip=action.toolTip(),style=str(getattr(button,'toolButtonStyle',lambda:None)()))
    toolbar.append({'text':action.text(),'tooltip':action.toolTip(),'enabled':action.isEnabled()})
  (HERE/'TOOLBAR.json').write_text(json.dumps(toolbar,indent=2)+'\n')
 finally:
  window.workspace.mark_saved()
  for widget in app.topLevelWidgets():widget.close()
  automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
