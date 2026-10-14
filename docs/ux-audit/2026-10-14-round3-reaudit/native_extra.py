"""Visible diagnostic and small-study result variants, at a readable review size."""
import sys,os,json,hashlib,shutil
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
work=HERE/'raw'/'extra';work.mkdir(parents=True,exist_ok=True)
sys.argv=['native_extra.py','doctor',str(work)];os.environ['RCMS_E2E_EVIDENCE_DIR']=str(work)
os.environ['RCMS_REQUIRE_IN_PROCESS_RPY2']='1'
os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(work/'analysis-scratch');(work/'analysis-scratch').mkdir(exist_ok=True)
driver=ROOT/'tests/e2e/desktop_driver.py';ns={'__file__':str(driver),'__name__':'audit_extra'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0],str(driver),'exec'),ns)
from PyQt6 import QtCore,QtWidgets
from PyQt6.QtTest import QTest
from rc_metastudio import automation,publication_bias_dialog,results_window
from analysis_matrix import run as matrix
from tests.e2e.audit_round3 import check_report
rows=[]
def copy_export(view,scenario):
 view.copy_report_action.trigger();copied=app.clipboard().text();assert copied.startswith(view.results.identity+'\n')
 output=work/(scenario+'-report.txt')
 with patch.object(results_window.QFileDialog,'getSaveFileName',return_value=(str(output),'Text report (*.txt)')):view.export_report_action.trigger()
 assert output.read_text()==copied
 for section in view.results.sections:
  for table in section.tables:
   assert '\t'.join(table.headers) in copied
   for row in table.rows:assert '\t'.join(row) in copied
 ns['record_step']('audit-small-study-copy-export',view,identity=view.results.identity,text=copied)
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=automation.start_automation();sys.excepthook=sys.__excepthook__;ns['app']=app
 try:
  ns['doctor'](app,window)
  def capture(view,name):
   view.raise_();view.activateWindow();app.processEvents();QTest.qWait(150)
   p=HERE/'screenshots'/('extra-'+name+'.png');assert app.platformName()=='xcb' and view.windowHandle().isExposed()
   assert view.screen().grabWindow(int(view.winId())).save(str(p),'PNG')
   rows.append(dict(path=str(p.relative_to(HERE)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),capture='QScreen.grabWindow',identity=getattr(getattr(view,'results',None),'identity',None)))
   (HERE/'EXTRA.json').write_text(json.dumps(rows,indent=2)+'\n')
  for scenario in ('analysis-diagnostic-joint','analysis-diagnostic-combined','analysis-diagnostic-regression-multiple','small-study-binary-extended','small-study-continuous-extended','small-study-diagnostic'):
   window.workspace.mark_saved();view=matrix(app,window,scenario,ns['record_step'],keep_results=True)
   QTest.qWait(300);capture(view,scenario+'-initial');ns['record_step']('audit-default-result-geometry',view,size=[view.width(),view.height()],maximized=view.isMaximized(),exposed=view.windowHandle().isExposed())
   view.resize(1500,850);app.processEvents();QTest.qWait(150);check_report(app,view,work,ns['record_step']) if scenario.startswith('analysis-') else copy_export(view,scenario)
   view.report_action.setChecked(True);view._show_report(True);view.report_text.verticalScrollBar().setValue(0);capture(view,scenario+'-report')
   view.report_text.verticalScrollBar().setValue(view.report_text.verticalScrollBar().maximum());capture(view,scenario+'-report-bottom')
   view.report_action.setChecked(False);view._show_report(False)
   for component,(title,path) in enumerate((view.results.display_images or view.results.images).items()):
    items=[item for item in view.nav_tree.findItems('',QtCore.Qt.MatchFlag.MatchContains|QtCore.Qt.MatchFlag.MatchRecursive) if id(item) in view._nav_plot_artifacts and view._nav_plot_artifacts[id(item)].title==title];assert len(items)==1,(title,[a.title for a in view._nav_plot_artifacts.values()])
    view.nav_tree.scrollToItem(items[0]);QTest.mouseClick(view.nav_tree.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=view.nav_tree.visualItemRect(items[0]).center());app.processEvents();capture(view,scenario+'-figure-'+str(component))
   for artifact_index,(title,base) in enumerate(view.params_paths.items()):
    for artifact in Path(base).parent.glob(Path(base).name+'.*'):
     if artifact.is_file():shutil.copy2(artifact,work/(scenario+'-'+str(artifact_index)+'-'+artifact.name))
   ns['record_step']('audit-extra-result',view,scenario=scenario,identity=view.results.identity,text=view.report_text.toPlainText());view.close();app.processEvents();print(scenario,'PASSED',flush=True)
  window.workspace.mark_saved();assert window.open(str(ROOT/'sample_projects/NielWeise2008-IRR.rcms'),raise_on_error=True)
  from advanced_workflows import modal,click
  def invalid_contour(dialog):
   dialog.ordinary_funnel_check.setChecked(True);dialog.contour_funnel_check.setChecked(True);dialog.contour_levels_edit.setText('95,100')
   capture(dialog,'irr-invalid-contour-controls')
   def error_box(box):capture(box,'irr-invalid-contour-error');ns['record_step']('audit-irr-invalid-contour',box,message=box.text());box.accept()
   modal(app,QtWidgets.QMessageBox,error_box,lambda:click(app,dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)))
   assert dialog.isVisible();capture(dialog,'irr-invalid-contour-recoverable');dialog.contour_levels_edit.setText('85,95,99');click(app,dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
  modal(app,publication_bias_dialog.PublicationBiasDialog,invalid_contour,window.action_publication_bias.trigger)
  recovered=next(w for w in app.topLevelWidgets() if isinstance(w,results_window.ResultsWindow) and w.isVisible());assert any('contour' in title.lower() for title in (recovered.results.display_images or recovered.results.images))
  recovered.resize(1500,850);copy_export(recovered,'irr-recovered');capture(recovered,'irr-contour-recovered-report');ns['record_step']('audit-irr-contour-recovered',recovered,text=recovered.report_text.toPlainText(),plots=dict(recovered.results.display_images or recovered.results.images));recovered.close();print('IRR invalid contour recovery PASSED',flush=True)
 finally:
  window.workspace.mark_saved()
  for widget in app.topLevelWidgets():widget.close()
  automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
