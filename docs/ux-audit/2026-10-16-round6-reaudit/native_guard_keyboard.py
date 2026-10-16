"""Native shell/dialog/menu and real text editor evidence in owned state."""
import os,sys,json,hashlib,subprocess,re,ctypes,time
from uuid import uuid4
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
work=HERE/'raw'/'guard-keyboard';work.mkdir(parents=True,exist_ok=True)
sys.argv=['native_shell.py','doctor',str(work)];os.environ['RCMS_E2E_EVIDENCE_DIR']=str(work)
os.environ['RCMS_REQUIRE_IN_PROCESS_RPY2']='1'
os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(work/'analysis-scratch');(work/'analysis-scratch').mkdir(exist_ok=True)
driver=ROOT/'tests/e2e/desktop_driver.py';ns={'__file__':str(driver),'__name__':'audit_shell'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0],str(driver),'exec'),ns)
from PyQt6 import QtCore,QtWidgets
from PyQt6.QtTest import QTest
from rc_metastudio import automation,main_wizard,edit_dialog,confidence_level_dialog,about_legal_dialog,add_new_dialogs
from advanced_workflows import modal,click
rows=[]
def capture(widget,name,observation='',native_id=None):
 widget.raise_();widget.activateWindow();app.processEvents();QTest.qWait(150)
 path=work/'captures'/(name+'.png');path.parent.mkdir(exist_ok=True);assert widget.screen().grabWindow(native_id or int(widget.winId())).save(str(path),'PNG')
 rows.append(dict(path=str(path.relative_to(HERE)),capture='QScreen.grabWindow',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),observation=observation))
 (HERE/'GUARD-KEYBOARD.json').write_text(json.dumps(rows,indent=2)+'\n')
def dismiss(dialog,name):capture(dialog,name);dialog.reject()
import shutil
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=automation.start_automation();sys.excepthook=sys.__excepthook__;ns['app']=app;ns['window']=window
 try:
  ns['doctor'](app,window)
  original=ROOT/'sample_projects/amino.rcms'; original_bytes=original.read_bytes()
  owned=work/'guard-source.rcms';target=work/'guard-target.rcms'
  shutil.copy2(original,owned);shutil.copy2(ROOT/'sample_projects/continuous.rcms',target)
  def choose(button,name):
   def operation(d):capture(d,name,d.text());click(app,d.button(button))
   return operation
  assert window.open(str(owned),raise_on_error=True)
  assert window.model.setData(window.model.index(0,window.model.NAME),'Discarded guard edit')
  before=owned.read_bytes()
  with patch.object(QtWidgets.QFileDialog,'getOpenFileName',return_value=(str(target),'')):
   modal(app,QtWidgets.QMessageBox,choose(QtWidgets.QMessageBox.StandardButton.No,'guard-open-no'),window.action_open.trigger)
  assert window.model.dataset.studies[0].name=='Carroll' and owned.read_bytes()==before
  capture(window,'guard-open-no-result')
  assert window.open(str(owned),raise_on_error=True)
  assert window.model.setData(window.model.index(0,window.model.NAME),'Saved guard edit')
  with patch.object(QtWidgets.QFileDialog,'getOpenFileName',return_value=(str(target),'')):
   modal(app,QtWidgets.QMessageBox,choose(QtWidgets.QMessageBox.StandardButton.Yes,'guard-open-yes'),window.action_open.trigger)
  assert window.model.dataset.studies[0].name=='Carroll'
  assert window.open(str(owned),raise_on_error=True) and window.model.dataset.studies[0].name=='Saved guard edit'
  capture(window,'guard-open-yes-reopened')
  assert window.model.setData(window.model.index(0,window.model.NAME),'Cancelled save-as guard edit')
  window.out_path=None
  with patch.object(QtWidgets.QFileDialog,'getOpenFileName',return_value=(str(target),'')),patch.object(QtWidgets.QFileDialog,'getSaveFileName',return_value=('','')):
   modal(app,QtWidgets.QMessageBox,choose(QtWidgets.QMessageBox.StandardButton.Yes,'guard-save-as-cancel'),window.action_open.trigger)
  assert window.workspace.is_dirty and window.model.dataset.studies[0].name=='Cancelled save-as guard edit'
  capture(window,'guard-save-as-cancel-preserved')
  window.workspace.mark_saved();assert window.open(str(owned),raise_on_error=True)
  window.raise_();window.activateWindow();QTest.qWait(150)
  def key(code,modifier=QtCore.Qt.KeyboardModifier.NoModifier):
   QTest.keyClick(app.activePopupWidget() or app.focusWidget() or window,code,modifier);app.processEvents();QTest.qWait(80)
  subprocess.run(['wmctrl','-ia',hex(int(window.winId()))],check=True)
  app.processEvents();QTest.qWait(250)
  visited=[]
  for _ in range(120):
   focus=app.focusWidget();visited.append(focus.objectName() or type(focus).__name__ if focus else 'None')
   if focus is window.analysis_button:break
   key(QtCore.Qt.Key.Key_Tab,QtCore.Qt.KeyboardModifier.ControlModifier if focus is window.tableView else QtCore.Qt.KeyboardModifier.NoModifier)
  assert app.focusWidget() is window.analysis_button,visited
  capture(window,'keyboard-toolbar-focus',json.dumps(visited))
  menu_errors=[]
  def select_meta():
   try:
    menu=app.activePopupWidget();assert isinstance(menu,QtWidgets.QMenu),type(menu)
    actions=[]
    for _ in range(12):
     if menu.activeAction() is window.action_go:break
     key(QtCore.Qt.Key.Key_Down)
     actions.append(menu.activeAction().text() if menu.activeAction() else 'None')
    assert menu.activeAction() is window.action_go,actions
    capture(menu,'keyboard-analysis-menu',menu.activeAction().text())
    key(QtCore.Qt.Key.Key_Return)
   except Exception as error:
    menu_errors.append(repr(error))
    if app.activePopupWidget():app.activePopupWidget().close()
  QtCore.QTimer.singleShot(200,select_meta)
  key(QtCore.Qt.Key.Key_Space)
  app.processEvents();QTest.qWait(250)
  assert not menu_errors,menu_errors
  from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
  from rc_metastudio.results_window import ResultsWindow
  setup=next(w for w in app.topLevelWidgets() if isinstance(w,AnalysisSetupDialog) and w.isVisible())
  capture(setup,'keyboard-analysis-setup')
  key(QtCore.Qt.Key.Key_Return)
  deadline=time.monotonic()+60
  while not any(isinstance(w,ResultsWindow) and w.isVisible() for w in app.topLevelWidgets()):
   assert time.monotonic()<deadline,'No Results window after keyboard Run'
   app.processEvents();QTest.qWait(50)
  view=next(w for w in app.topLevelWidgets() if isinstance(w,ResultsWindow) and w.isVisible())
  view.raise_();view.activateWindow();QTest.qWait(100)
  key(QtCore.Qt.Key.Key_T,QtCore.Qt.KeyboardModifier.ControlModifier)
  assert view.report_text.isVisible()
  app.clipboard().setText('keyboard-audit-sentinel')
  modifier=QtCore.Qt.KeyboardModifier.ControlModifier|QtCore.Qt.KeyboardModifier.ShiftModifier
  key(QtCore.Qt.Key.Key_C,modifier)
  copied=app.clipboard().text();assert copied.startswith(view.identity_label.text()) and 'Pooled ' in copied
  report=work/'keyboard-exported-report.txt'
  with patch.object(QtWidgets.QFileDialog,'getSaveFileName',return_value=(str(report),'')):
   key(QtCore.Qt.Key.Key_S,modifier)
  assert report.read_text()==copied
  capture(view,'keyboard-report-copied-exported')
  assert original.read_bytes()==original_bytes
  print('GUARD AND KEYBOARD WORKFLOW PASSED',flush=True)
 finally:
  window.workspace.mark_saved()
  for w in app.topLevelWidgets():w.close()
  automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
