"""Inventory real native setup controls and their available choices without fitting."""
import os,sys,json,hashlib
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
work=HERE/'raw'/'options';work.mkdir(parents=True,exist_ok=True)
sys.argv=['native_options.py','doctor',str(work)]
os.environ['RCMS_E2E_EVIDENCE_DIR']=str(work);os.environ['RCMS_REQUIRE_IN_PROCESS_RPY2']='1'
os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(work/'scratch');(work/'scratch').mkdir(exist_ok=True)
driver=ROOT/'tests/e2e/desktop_driver.py';ns={'__file__':str(driver),'__name__':'audit_options'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0],str(driver),'exec'),ns)
from PyQt6 import QtCore,QtWidgets,QtGui
from PyQt6.QtTest import QTest
from rc_metastudio import automation,analysis_setup_dialog,publication_bias_dialog
from advanced_workflows import modal
rows=[]
def inventory(dialog,tag):
 dialog.raise_();dialog.activateWindow();app.processEvents();QTest.qWait(500)
 controls=[]
 for w in dialog.findChildren(QtWidgets.QWidget):
  if not isinstance(w,(QtWidgets.QLabel,QtWidgets.QComboBox,QtWidgets.QAbstractButton,QtWidgets.QLineEdit,QtWidgets.QAbstractSpinBox)):continue
  item={'class':w.metaObject().className(),'name':w.objectName(),'visible':w.isVisible(),'enabled':w.isEnabled(),'tooltip':w.toolTip(),'accessible_name':w.accessibleName()}
  if hasattr(w,'text'):item['text']=w.text()
  if isinstance(w,QtWidgets.QComboBox):item.update(choices=[w.itemText(i) for i in range(w.count())],selected=w.currentText())
  if isinstance(w,QtWidgets.QLineEdit):item['placeholder']=w.placeholderText()
  controls.append(item)
 name='options-'+str(len(rows)).zfill(3)+'-'+tag+'.png';p=HERE/'screenshots'/name
 assert app.platformName()=='xcb' and dialog.windowHandle().isExposed()
 assert dialog.screen().grabWindow(int(dialog.winId())).save(str(p),'PNG')
 actions=[{'text':a.text(),'tooltip':a.toolTip(),'enabled':a.isEnabled()} for a in dialog.actions()] if isinstance(dialog,QtWidgets.QMenu) else []
 rows.append({'actions':actions,'tag':tag,'path':str(p.relative_to(HERE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'controls':controls})
 (HERE/'OPTIONS.json').write_text(json.dumps(rows,indent=2)+'\n')
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=automation.start_automation();ns['app']=app;sys.excepthook=sys.__excepthook__
 try:
  ns['doctor'](app,window)
  # Diagnostic/HR/IRR continue in native_options_remaining; diagnostics opens a metric selector first.
  for family in ('onearm-proportion','onearm-mean','reg-coef','generic-effect','twoarm-proportion','twoarm-mean','twoarm-smd'):
   window.workspace.mark_saved();assert window.open(str(HERE/'raw'/('matrix-'+family)/'standard-input.rcms'),raise_on_error=True)
   # Enumerate actual type-dependent menu actions, not UI resource strings.
   menu_rows=[]
   for menu in window.findChildren(QtWidgets.QMenu):
    menu_rows.append({'title':menu.title(),'actions':[{'text':a.text(),'enabled':a.isEnabled(),'tooltip':a.toolTip()} for a in menu.actions()]})
   (work/(family+'-menus.json')).write_text(json.dumps(menu_rows,indent=2)+'\n')
   from rc_metastudio.analysis_dataset import Covariate
   for name,kind in [('Audit numeric','continuous'),('Audit category','factor')]:
    window.model.dataset.add_covariate(Covariate(name,kind),{study.name:1.0 if kind=='continuous' else 'A' for study in window.model.get_studies(only_if_included=True)})
   window.model.reset_model();window.enable_menu_options_that_require_dataset();app.processEvents()
   header=window.tableView.horizontalHeader()
   for column in range(window.model.columnCount()):
    window.tableView.scrollTo(window.model.index(0,column));app.processEvents()
    pos=QtCore.QPoint(header.sectionViewportPosition(column)+header.sectionSize(column)//2,header.height()//2)
    header.customContextMenuRequested.emit(pos);app.processEvents()
    popup=app.activePopupWidget()
    if isinstance(popup,QtWidgets.QMenu):inventory(popup,family+'-header-'+str(column));popup.close();app.processEvents()
   index=window.model.index(0,1);window.tableView.scrollTo(index);app.processEvents()
   pos=window.tableView.visualRect(index).center()
   event=QtGui.QContextMenuEvent(QtGui.QContextMenuEvent.Reason.Mouse,pos,window.tableView.viewport().mapToGlobal(pos))
   window.tableView.contextMenuEvent(event);app.processEvents();popup=app.activePopupWidget()
   if isinstance(popup,QtWidgets.QMenu):inventory(popup,family+'-study-context');popup.close();app.processEvents()
   def setup(d):
    labels=[d.method_cbo_box.itemText(i) for i in range(d.method_cbo_box.count())]
    for label in labels:
     d.method_cbo_box.setCurrentText(label);app.processEvents();inventory(d,family+'-method-'+str(labels.index(label)))
    d.reject()
   modal(app,analysis_setup_dialog.AnalysisSetupDialog,setup,window.action_go.trigger)
   print(family,'OPTIONS PASSED',flush=True)
  def small(d):inventory(d,'small-study');d.reject()
  modal(app,publication_bias_dialog.PublicationBiasDialog,small,window.action_publication_bias.trigger)
 finally:
  window.workspace.mark_saved()
  for w in app.topLevelWidgets():w.close()
  automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
