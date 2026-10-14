"""Native shell/dialog/menu and real text editor evidence in owned state."""
import os,sys,json,hashlib,subprocess,re
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
work=HERE/'raw'/'shell';work.mkdir(parents=True,exist_ok=True)
sys.argv=['native_shell.py','doctor',str(work)];os.environ['RCMS_E2E_EVIDENCE_DIR']=str(work)
driver=ROOT/'tests/e2e/desktop_driver.py';ns={'__file__':str(driver),'__name__':'audit_shell'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0],str(driver),'exec'),ns)
from PyQt6 import QtCore,QtWidgets
from PyQt6.QtTest import QTest
from rc_metastudio import automation,main_wizard,edit_dialog,confidence_level_dialog,about_legal_dialog,add_new_dialogs
from advanced_workflows import modal,click
rows=[]
def capture(widget,name,observation=''):
 widget.raise_();widget.activateWindow();app.processEvents();QTest.qWait(150)
 path=HERE/'screenshots'/(name+'.png');assert widget.screen().grabWindow(int(widget.winId())).save(str(path),'PNG')
 rows.append(dict(path=str(path.relative_to(HERE)),capture='QScreen.grabWindow',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),observation=observation))
 (HERE/'SHELL.json').write_text(json.dumps(rows,indent=2)+'\n')
def dismiss(dialog,name):capture(dialog,name);dialog.reject()
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=automation.start_automation();ns['app']=app
 try:
  ns['doctor'](app,window);capture(window,'shell-empty')
  window.start();app.processEvents();QTest.qWait(200);launcher=window._startup_wizard;assert launcher;capture(launcher,'shell-launcher');launcher.reject();app.processEvents()
  def wizard_drive(w):
   capture(w,'shell-types');click(app,w.currentPage().onearm_generic_effect_size_Button);click(app,w.button(QtWidgets.QWizard.WizardButton.NextButton))
   capture(w,'shell-generic-metric');click(app,w.button(QtWidgets.QWizard.WizardButton.NextButton));capture(w,'shell-empty-outcome');w.reject()
  window.workspace.mark_saved();modal(app,main_wizard.MainWizard,wizard_drive,window.action_new_dataset.trigger)
  assert window.open(str(ROOT/'sample_projects/amino.rcms'),raise_on_error=True);capture(window,'shell-grid')
  for action in window.menu_bar.actions():
   menu=action.menu()
   if menu:
    menu.popup(window.menu_bar.mapToGlobal(window.menu_bar.actionGeometry(action).bottomLeft()));app.processEvents();capture(menu,'menu-'+action.text().replace('&','').lower());menu.close()
  def structure(d):
   for i,name in enumerate(('shell-structure','shell-studies','shell-covariates')):d.edit_tab.setCurrentIndex(i);capture(d,name)
   d.reject()
  modal(app,edit_dialog.EditDialog,structure,window.action_edit.trigger)
  modal(app,add_new_dialogs.AddCovariateDialog,lambda d:dismiss(d,'shell-add-covariate'),window.action_add_covariate.trigger)
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
   template=work/'template.csv'
   def save_picker(picker):
    picker.setDirectory(str(work));picker.selectFile('template.csv');capture(picker,'shell-template-native-picker');box=picker.findChild(QtWidgets.QDialogButtonBox);assert box;click(app,box.button(QtWidgets.QDialogButtonBox.StandardButton.Save))
   modal(app,QtWidgets.QFileDialog,save_picker,page.template_btn.click)
   assert template.exists();capture(w,'shell-template-saved')
   w.reject()
  window.workspace.mark_saved();modal(app,main_wizard.MainWizard,csv,window.action_import_csv.trigger)
  # The actual helper-exported text is opened in the host's native Xaw text editor.
  runs=list((HERE/'raw').glob('matrix-*/round3-report.txt'));assert runs
  report=runs[-1].resolve();editor=subprocess.Popen(['xedit',str(report)])
  try:
   QTest.qWait(1500)
   tree=subprocess.check_output(['xwininfo','-root','-tree'],text=True)
   ids=re.findall(r'(0x[0-9a-f]+).*xedit',tree,re.I);assert ids,tree
   wid=int(ids[0],16);subprocess.run(['wmctrl','-ir',ids[0],'-b','add,maximized_vert,maximized_horz'],check=True);subprocess.run(['wmctrl','-ia',ids[0]],check=True);QTest.qWait(300)
   path=HERE/'screenshots'/'shell-exported-report-editor.png';assert window.screen().grabWindow(wid).save(str(path),'PNG')
   rows.append(dict(path=str(path.relative_to(HERE)),capture='QScreen.grabWindow external xedit',source=str(report.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
   (HERE/'SHELL.json').write_text(json.dumps(rows,indent=2)+'\n')
  finally:editor.terminate();editor.wait(timeout=5)
 finally:
  window.workspace.mark_saved()
  for widget in app.topLevelWidgets():widget.close()
  automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
