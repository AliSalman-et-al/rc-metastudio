"""Native close view of the duplicate-author subgroup weight discrepancy."""
import sys,os,json,hashlib
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
work=HERE/'raw'/'weights-native';work.mkdir(parents=True,exist_ok=True)
sys.argv=['native_weights.py','doctor',str(work)];os.environ['RCMS_E2E_EVIDENCE_DIR']=str(work);os.environ['RCMS_REQUIRE_IN_PROCESS_RPY2']='1';os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(work/'analysis');(work/'analysis').mkdir(exist_ok=True)
driver=ROOT/'tests/e2e/desktop_driver.py';ns={'__file__':str(driver),'__name__':'audit_weights'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0],str(driver),'exec'),ns)
from PyQt6 import QtCore
from PyQt6.QtTest import QTest
from rc_metastudio import automation
from tests.e2e.audit_round3 import analyze_existing
rows=[]
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=automation.start_automation();sys.excepthook=sys.__excepthook__;ns['app']=app
 try:
  ns['doctor'](app,window);assert window.open(str(HERE/'raw/matrix-irr/subgroup-input.rcms'),raise_on_error=True)
  view=analyze_existing(app,window,'subgroup','event_rates.random',ns['record_step'],{'digits':6});view.resize(1500,850);app.processEvents();QTest.qWait(200)
  item=next(i for i in view.nav_tree.findItems('',QtCore.Qt.MatchFlag.MatchContains|QtCore.Qt.MatchFlag.MatchRecursive) if id(i) in view._nav_plot_artifacts)
  QTest.mouseClick(view.nav_tree.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=view.nav_tree.visualItemRect(item).center());app.processEvents();scroll=view.graphics_view.verticalScrollBar();start=scroll.value();maximum=scroll.maximum()
  for label,value in [('middle',round((start+maximum)/2)),('bottom',maximum)]:
   scroll.setValue(value);view.raise_();view.activateWindow();app.processEvents();QTest.qWait(150);p=HERE/'screenshots'/('weights-irr-subgroup-'+label+'.png');assert view.screen().grabWindow(int(view.winId())).save(str(p),'PNG');rows.append({'path':str(p.relative_to(HERE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'capture':'QScreen.grabWindow','scroll':value})
  (HERE/'WEIGHTS-NATIVE.json').write_text(json.dumps(rows,indent=2)+'\n');ns['record_step']('audit-duplicate-name-weights',view,plots=dict(view.results.display_images),text=view.report_text.toPlainText())
 finally:
  window.workspace.mark_saved()
  for widget in app.topLevelWidgets():widget.close()
  automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
