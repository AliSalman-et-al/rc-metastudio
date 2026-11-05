"""Real Qt viewport/menu loop using the SVG retained from the failing HR run."""
import os,sys,json
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
from PyQt6 import QtCore,QtWidgets,QtGui
from rc_metastudio.qt6_ui import prepare_generated_ui_imports
prepare_generated_ui_imports()
from rc_metastudio.analysis_results import parse_analysis_result
from rc_metastudio.results_window import ResultsWindow
root=Path(__file__).parent
app=QtWidgets.QApplication([])
QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat,QtCore.QSettings.Scope.UserScope,str(root/'viewport-settings'))
QtCore.QSettings().clear()
svg=str((root/'viewport-repro.svg').resolve())
title='Subgroup Forest Plot'
result=parse_analysis_result({'version':1,'texts':{'Summary':'Retained real HR subgroup plot'},'images':{title:svg},'display_images':{title:svg},'image_params_paths':{title:str(root/'params')},'plot_capabilities':{title:{'plot_kind':'subgroup_forest','editable':True,'styleable':True,'regenerator':'forest','composition':'single'}},'sections':[{'id':'text.summary','kind':'text','order':0,'title':'Summary','source_key':'Summary'},{'id':'image.forest','kind':'image','order':1,'title':title,'source_key':title}]})
if '--legacy' in sys.argv:
 import ast,subprocess,textwrap
 from rc_metastudio import results_window
 old_source=subprocess.check_output(['git','show','2974b88b:src/rc_metastudio/results_window.py'],text=True)
 tree=ast.parse(old_source)
 node=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='_layout_viewport_width')
 namespace={}
 exec(textwrap.dedent(ast.get_source_segment(old_source,node)),results_window.__dict__,namespace)
 ResultsWindow._layout_viewport_width=namespace['_layout_viewport_width']
count=0
original=ResultsWindow._run_scheduled_viewport_refit

def traced(self):
 global count
 count+=1
 if count<30 or count%1000==0:
  print('refit',count,self.graphics_view.viewport().width(),self.graphics_view.viewport().height(),self.scene.width(),self.scene.height(),flush=True)
 return original(self)
ResultsWindow._run_scheduled_viewport_refit=traced
if '--stable' in sys.argv:
 old_layout_width=ResultsWindow._layout_viewport_width
 def stable_width(self):
  width=old_layout_width(self)
  return min(width,self.graphics_view.maximumViewportSize().width()-self.graphics_view.verticalScrollBar().sizeHint().width())
 ResultsWindow._layout_viewport_width=stable_width
if '--reserve' in sys.argv:
 old_width=ResultsWindow._plot_viewport_width
 ResultsWindow._plot_viewport_width=lambda self:max(1,old_width(self)-2)
view=ResultsWindow(result)
view.resize(800,800)
view.show()

def context():
 item=view._svg_plot_items[0]
 view.graphics_view.ensureVisible(item)
 app.processEvents()
 point=view.graphics_view.mapFromScene(item.sceneBoundingRect().center())
 print('context',point.x(),point.y(),flush=True)
 def close_menu():
  menu=app.activePopupWidget();print('popup',type(menu).__name__,flush=True)
  if menu:menu.close()
 QtCore.QTimer.singleShot(1000,close_menu)
 viewport=view.graphics_view.viewport()
 event=QtGui.QContextMenuEvent(QtGui.QContextMenuEvent.Reason.Mouse,point,viewport.mapToGlobal(point))
 QtWidgets.QApplication.sendEvent(viewport,event)
 print('context returned',flush=True)
 view.close();app.quit()
QtCore.QTimer.singleShot(500,context)
QtCore.QTimer.singleShot(10000,app.quit)
app.exec()
print('refits total',count,flush=True)

if '--assert-stable' in sys.argv:
 assert count < 10, ('viewport refit loop',count)
