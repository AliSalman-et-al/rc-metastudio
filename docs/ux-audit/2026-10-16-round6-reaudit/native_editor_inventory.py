"""Fill missing native lower-editor scroll views; Cancel retains real figures."""
from pathlib import Path
import hashlib,json,os,sys
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
work=HERE/'raw/editor-inventory';work.mkdir(exist_ok=True)
sys.argv=['native_editor_inventory.py','doctor',str(work)]
os.environ['RCMS_E2E_EVIDENCE_DIR']=str(work);os.environ['RCMS_REQUIRE_IN_PROCESS_RPY2']='1';os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(work/'scratch');(work/'scratch').mkdir(exist_ok=True)
driver=ROOT/'tests/e2e/desktop_driver.py';ns={'__file__':str(driver),'__name__':'audit_editor_inventory'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0],str(driver),'exec'),ns)
from PyQt6 import QtCore,QtWidgets
from PyQt6.QtTest import QTest
from rc_metastudio import automation
from analysis_matrix import run as matrix
from advanced_workflows import modal
producers=['analysis-binary.fixed.inv.var','analysis-amino-binary-cumulative','analysis-amino-binary-leave-one-out','analysis-amino-binary-subgroup','analysis-amino-binary-meta-regression','analysis-diagnostic-joint','analysis-diagnostic-regression-continuous','small-study-binary-extended','small-study-diagnostic']
rows=[];kinds=set()
def capture(d,tag):
 d.raise_();d.activateWindow();app.processEvents();QTest.qWait(250)
 p=work/'captures'/('editor-'+str(len(rows)).zfill(3)+'-'+tag+'.png');p.parent.mkdir(exist_ok=True)
 assert d.windowHandle().isExposed() and app.platformName()=='xcb'
 assert d.screen().grabWindow(int(d.winId())).save(str(p),'PNG')
 controls=[]
 for w in d.findChildren(QtWidgets.QWidget):
  if not w.isVisible():continue
  if isinstance(w,(QtWidgets.QLabel,QtWidgets.QAbstractButton,QtWidgets.QLineEdit,QtWidgets.QComboBox,QtWidgets.QAbstractSpinBox)):
   r={'class':w.metaObject().className(),'name':w.objectName(),'tooltip':w.toolTip(),'enabled':w.isEnabled()}
   if hasattr(w,'text'):r['text']=w.text()
   if isinstance(w,QtWidgets.QComboBox):r['choices']=[w.itemText(i) for i in range(w.count())]
   controls.append(r)
 rows.append({'path':str(p.relative_to(HERE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'tag':tag,'controls':controls,'capture':'Native QScreen.grabWindow'})
 (HERE/'EDITOR-INVENTORY.json').write_text(json.dumps(rows,indent=2)+'\n')
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=automation.start_automation();sys.excepthook=sys.__excepthook__;ns.update(app=app,window=window)
 try:
  ns['doctor'](app,window)
  for producer in producers:
   window.workspace.mark_saved();view=matrix(app,window,producer,ns['record_step'],keep_results=True)
   for title,path in view.results.images.items():
    artifact=view.create_plot_artifact(title,path,params_path=view.results.image_params_paths.get(title))
    kind=artifact.plot_kind
    if kind=='forest' and artifact.params_path and view.plot_service.load_params(artifact.params_path).get('reitsma.coefficient.scale'):kind='coefficient'
    if kind in kinds or not artifact.params_path:continue
    heading=next(s.title for s in view.results.sections if s.kind=='image' and s.source_key==title)
    items=view.nav_tree.findItems(heading,QtCore.Qt.MatchFlag.MatchExactly|QtCore.Qt.MatchFlag.MatchRecursive);assert len(items)==1
    view.nav_tree.scrollToItem(items[0]);QTest.mouseClick(view.nav_tree.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=view.nav_tree.visualItemRect(items[0]).center());app.processEvents()
    before={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in view.results.display_images.values()}
    def editor(d):
     capture(d,kind+'-top')
     for area in d.findChildren(QtWidgets.QAbstractScrollArea):
      if not area.isVisible():continue
      bar=area.verticalScrollBar();limit=bar.maximum();step=max(1,area.viewport().height()*3//4)
      for value in sorted({*range(step,limit,step),limit}):
       if not value:continue
       bar.setValue(value);app.processEvents();capture(d,kind+'-scroll-'+str(value))
     d.reject()
    modal(app,QtWidgets.QDialog,editor,view.edit_plot_action.trigger)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest for p,digest in before.items())
    kinds.add(kind);print(kind,'SCROLL/CANCEL PASSED',flush=True)
   view.close();app.processEvents()
  expected={'forest','coefficient','cumulative_forest','leave_one_out_forest','subgroup_forest','regression','sroc','funnel','contour_funnel','trimfill_funnel','deeks_funnel'}
  assert expected<=kinds,(expected-kinds,kinds)
 finally:
  window.workspace.mark_saved()
  for w in app.topLevelWidgets():w.close()
  automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
