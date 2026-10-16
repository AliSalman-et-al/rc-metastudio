"""Native shell/dialog/menu and real text editor evidence in owned state."""
import os,sys,json,hashlib,subprocess,re,ctypes
from uuid import uuid4
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
work=HERE/'raw'/'shell';work.mkdir(parents=True,exist_ok=True)
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
 (HERE/'SHELL.json').write_text(json.dumps(rows,indent=2)+'\n')
def dismiss(dialog,name):capture(dialog,name);dialog.reject()
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=automation.start_automation();sys.excepthook=sys.__excepthook__;ns['app']=app;ns['window']=window;sys.excepthook=sys.__excepthook__
 try:
  ns['doctor'](app,window);capture(window,'shell-empty')
  from rc_metastudio.launch import _show_main_window
  from rc_metastudio.settings import save_main_window_placement
  for mode in ('normal','full-screen'):
   window.showNormal() if mode=='normal' else window.showFullScreen();window.resize(700,500) if mode=='normal' else None;app.processEvents();save_main_window_placement(window,window.tableView.column_width_state());_show_main_window(window);app.processEvents();initial={'maximized':window.isMaximized(),'full_screen':window.isFullScreen()};QTest.qWait(500);capture(window,'shell-startup-'+mode,json.dumps({'initial':initial,'settled':{'maximized':window.isMaximized(),'full_screen':window.isFullScreen(),'size':[window.width(),window.height()]}}))
  window.showNormal();app.processEvents();QTest.qWait(150);window.showMaximized();QTest.qWait(300)
  window.start();app.processEvents();QTest.qWait(200);capture(window,'shell-launcher')
  def wizard_drive(w):
   capture(w,'shell-types');click(app,w.currentPage().onearm_generic_effect_size_Button);click(app,w.button(QtWidgets.QWizard.WizardButton.NextButton))
   capture(w,'shell-generic-metric');click(app,w.button(QtWidgets.QWizard.WizardButton.NextButton));capture(w,'shell-empty-outcome');w.reject()
  window.workspace.mark_saved();modal(app,main_wizard.MainWizard,wizard_drive,window.action_new_dataset.trigger)
  assert window.open(str(ROOT/'sample_projects/amino.rcms'),raise_on_error=True);capture(window,'shell-grid')
  original=window.model.dataset.studies[0].name;assert window.model.setData(window.model.index(0,window.model.NAME),'Native unsaved study')
  def cancel_dirty(d):capture(d,'shell-dirty-open-prompt',d.text());click(app,d.button(QtWidgets.QMessageBox.StandardButton.Cancel))
  with patch.object(QtWidgets.QFileDialog,'getOpenFileName',return_value=(str(ROOT/'sample_projects/continuous.rcms'),'')):modal(app,QtWidgets.QMessageBox,cancel_dirty,window.action_open.trigger)
  assert window.model.dataset.studies[0].name=='Native unsaved study' and window.workspace.is_dirty;window.action_undo.trigger();assert window.model.dataset.studies[0].name==original
  destination=work/'shell.rcms'
  with patch.object(QtWidgets.QFileDialog,'getSaveFileName',return_value=(str(destination),'')):window.action_save_as.trigger()
  assert destination.exists() and not window.workspace.is_dirty
  recent=next(a for a in window.action_open_recent_2.actions() if a.data()==str(destination));recent.trigger();app.processEvents();assert window.model.dataset.studies[0].name==original;capture(window,'shell-save-recent-reopened')
  inventory=[]
  def inspect_menu(menu, trail):
   menu.popup(window.menu_bar.mapToGlobal(window.menu_bar.rect().bottomLeft()));app.processEvents();QTest.qWait(100)
   capture(menu,'menu-'+str(len(inventory)),trail)
   actions=list(menu.actions())
   inventory.append({'menu':trail,'actions':[{'text':a.text(),'enabled':a.isEnabled(),'tooltip':a.toolTip(),'shortcut':a.shortcut().toString(),'submenu':bool(a.menu())} for a in actions]})
   menu.close()
   for action in actions:
    if action.menu():inspect_menu(action.menu(),trail+' / '+action.text())
  for action in window.menu_bar.actions():
   if action.menu():inspect_menu(action.menu(),action.text())
  inventory.append({'toolbar':[{'text':a.text(),'tooltip':a.toolTip(),'enabled':a.isEnabled()} for bar in window.findChildren(QtWidgets.QToolBar) for a in bar.actions()]})
  (HERE/'MENU-INVENTORY.json').write_text(json.dumps(inventory,indent=2)+'\n')
  def structure(d):
   for i,name in enumerate(('shell-structure','shell-studies','shell-covariates')):d.edit_tab.setCurrentIndex(i);capture(d,name)
   d.reject()
  modal(app,edit_dialog.EditDialog,structure,window.action_edit.trigger)
  modal(app,add_new_dialogs.AddCovariateDialog,lambda d:dismiss(d,'shell-add-covariate'),window.action_add_covariate.trigger)
  def add_dose(d):d.covariate_name_le.setText('Dose');click(app,d.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
  modal(app,add_new_dialogs.AddCovariateDialog,add_dose,window.action_add_covariate.trigger)
  def duplicate(d):
   d.covariate_name_le.setText('Dose');click(app,d.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok));assert d.isVisible() and d.error_label.text();QTest.qWait(300);capture(d,'shell-duplicate-covariate',d.error_label.text());d.covariate_name_le.setText('Region');click(app,d.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
  modal(app,add_new_dialogs.AddCovariateDialog,duplicate,window.action_add_covariate.trigger)
  modal(app,confidence_level_dialog.ConfidenceLevelDialog,lambda d:dismiss(d,'shell-confidence'),window.action_change_confidence_level.trigger)
  def about(d):
   capture(d,'shell-about')
   for tab in d.findChildren(QtWidgets.QTabWidget):
    for i in range(tab.count()):tab.setCurrentIndex(i);capture(d,'shell-about-'+str(i))
   d.reject()
  modal(app,about_legal_dialog.AboutLegalDialog,about,window.action_about_legal.trigger)
  def quick(d):capture(d,'shell-quick-start');d.reject()
  modal(app,QtWidgets.QDialog,quick,next(a for a in window.menuHelp.actions() if 'Quick start' in a.text()).trigger)
  # Import menu traverses the earlier pages; picker returns a test-owned CSV only.
  def csv(w):
   capture(w,'shell-import-types');click(app,w.currentPage().twoarm_proportions_Button);click(app,w.button(QtWidgets.QWizard.WizardButton.NextButton));click(app,w.button(QtWidgets.QWizard.WizardButton.NextButton))
   w.currentPage().outcome_name_LineEdit.setText('Native import');click(app,w.button(QtWidgets.QWizard.WizardButton.NextButton));page=w.currentPage();capture(w,'shell-csv-entry')
   template=work/('template-'+uuid4().hex[:8]+'.csv')
   def save_picker(picker):
    picker.setDirectory(str(work));picker.selectFile(template.name);QTest.qWait(250)
    tree=subprocess.check_output(['xwininfo','-root','-tree'],text=True);ids=re.findall(r'(0x[0-9a-f]+) \"Save CSV template\"',tree);assert ids,tree
    ids=[wid for wid in ids if re.search(r'=\s*'+str(os.getpid())+r'\b',subprocess.check_output(['xprop','-id',wid,'_NET_WM_PID'],text=True))];assert len(ids)==1,ids
    capture(picker,'shell-template-native-picker','Native Gtk chooser; Qt proxy has no visible button widgets',int(ids[0],16));subprocess.run(['wmctrl','-ia',ids[0]],check=True)
    x=ctypes.CDLL('libX11.so.6');xt=ctypes.CDLL('libXtst.so.6');x.XOpenDisplay.restype=ctypes.c_void_p;x.XOpenDisplay.argtypes=[ctypes.c_char_p];dpy=x.XOpenDisplay(None);assert dpy
    x.XStringToKeysym.argtypes=[ctypes.c_char_p];x.XStringToKeysym.restype=ctypes.c_ulong;x.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong];x.XKeysymToKeycode.restype=ctypes.c_ubyte;x.XFlush.argtypes=[ctypes.c_void_p];x.XCloseDisplay.argtypes=[ctypes.c_void_p];xt.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
    def key(name,down):
     code=x.XKeysymToKeycode(dpy,x.XStringToKeysym(name.encode()));assert code;xt.XTestFakeKeyEvent(dpy,code,int(down),0)
    def tap(name):key(name,True);key(name,False)
    try:
     key('Control_L',True);tap('l');key('Control_L',False);x.XFlush(dpy);QTest.qWait(150);key('Control_L',True);tap('a');key('Control_L',False);x.XFlush(dpy);QTest.qWait(50)
     for char in str(template):
      shift=char.isupper() or char=='_';key('Shift_L',True) if shift else None
      tap({'/':'slash','-':'minus','.':'period','_':'underscore',' ':'space'}.get(char,char.lower()));key('Shift_L',False) if shift else None
     tap('Return');x.XFlush(dpy);QTest.qWait(250)
     tree=subprocess.check_output(['xwininfo','-root','-tree'],text=True)
     if re.search(r'\"Save CSV template\"',tree):tap('Return');x.XFlush(dpy);QTest.qWait(250)
    finally:x.XCloseDisplay(dpy)
   modal(app,QtWidgets.QFileDialog,save_picker,page.template_btn.click)
   assert template.exists();capture(w,'shell-template-saved')
   w.reject()
  window.workspace.mark_saved();modal(app,main_wizard.MainWizard,csv,window.action_import_csv.trigger)
  # The actual helper-exported text is opened in the host's native Xaw text editor.
  report=(HERE/'raw/native-design/review1-report.txt').resolve();assert report.exists()
  before_xedit=set(re.findall(r'0x[0-9a-f]+',subprocess.check_output(['xwininfo','-root','-tree'],text=True)))
  editor=subprocess.Popen(['xedit',str(report)])
  try:
   QTest.qWait(1500)
   tree=subprocess.check_output(['xwininfo','-root','-tree'],text=True)
   ids=[wid for wid in re.findall(r'(0x[0-9a-f]+).*xedit',tree,re.I) if wid not in before_xedit];assert ids,tree
   wid=int(ids[0],16);subprocess.run(['wmctrl','-ir',ids[0],'-b','add,maximized_vert,maximized_horz'],check=True);subprocess.run(['wmctrl','-ia',ids[0]],check=True);QTest.qWait(300)
   path=work/'captures'/'shell-exported-report-editor.png';path.parent.mkdir(exist_ok=True);assert window.screen().grabWindow(wid).save(str(path),'PNG')
   rows.append(dict(path=str(path.relative_to(HERE)),capture='QScreen.grabWindow external xedit',source=str(report.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
   (HERE/'SHELL.json').write_text(json.dumps(rows,indent=2)+'\n')
  finally:editor.terminate();editor.wait(timeout=5)
 finally:
  window.workspace.mark_saved()
  for widget in app.topLevelWidgets():widget.close()
  automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
