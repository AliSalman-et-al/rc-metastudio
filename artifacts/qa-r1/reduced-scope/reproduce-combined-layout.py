from pathlib import Path
from unittest.mock import patch
import json,sys
from PyQt6 import QtCore,QtGui,QtWidgets
from rc_metastudio.qt6_ui import prepare_generated_ui_imports
prepare_generated_ui_imports()
from rc_metastudio.automation import _start_package_application,_close_automation_window
from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
root=Path(__file__).resolve().parents[3]
work=root/'artifacts/qa-r1/reduced-scope/combined-layout'
work.mkdir(exist_ok=True)
QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat,QtCore.QSettings.Scope.UserScope,str(work/'settings'))
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=_start_package_application()
 sys.excepthook=sys.__excepthook__
 try:
  assert window.open(str(root/'sample_projects/lymph.rcms'),raise_on_error=True)
  font=QtGui.QFont(app.font());font.setPointSize(14);app.setFont(font)
  dialog=AnalysisSetupDialog(window.model,diagnostic_metrics=['sens','spec','dor'],confidence_level=95.0)
  label=next(label for label,method in dialog.available_method_d.items() if method=='diagnostic.reitsma')
  dialog.method_cbo_box.setCurrentText(label)
  dialog.show()
  for _ in range(12): app.processEvents()
  if '--characters' in sys.argv:
   from rc_metastudio import adaptive_controls
   for c in dialog.methods_tab.findChildren(QtWidgets.QComboBox):
    if isinstance(c,adaptive_controls.AdaptiveComboBox): adaptive_controls.configure_choice_control(c,visible_characters=18)
  if '--controls' in sys.argv:
   for c in dialog.methods_tab.findChildren(QtWidgets.QComboBox):
    c.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored,c.sizePolicy().verticalPolicy())
  if '--tab' in sys.argv:
   dialog.methods_tab.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored,QtWidgets.QSizePolicy.Policy.Preferred)
  for _ in range(12): app.processEvents()
  viewport=dialog.content_scroll_area.viewport()
  def metrics(w):
   return {'class':type(w).__name__,'name':w.objectName(),'width':w.width(),'minimum_width':w.minimumWidth(),'minimum_hint':w.minimumSizeHint().width(),'hint':w.sizeHint().width(),'policy':str(w.sizePolicy().horizontalPolicy())}
  controls=[]
  for c in dialog.methods_tab.findChildren(QtWidgets.QWidget):
   if c.isVisible() and isinstance(c,(QtWidgets.QLabel,QtWidgets.QComboBox,QtWidgets.QSpinBox,QtWidgets.QDoubleSpinBox)):
    left=c.mapTo(viewport,QtCore.QPoint()).x()
    if left<0 or left+c.width()>viewport.width():
     chain=[];p=c
     while p is not None and p!=dialog:
      chain.append(metrics(p));p=p.parentWidget()
     controls.append({'text':c.text() if isinstance(c,QtWidgets.QLabel) else '', 'left':left,'right':left+c.width(),'chain':chain})
  report={'viewport':viewport.width(),'overflow':controls,'method_row':metrics(dialog._method_row),'method_layout_width':dialog._method_layout.contentsRect().width()}
  (work/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
  dialog.grab().save(str(work/'dialog.png'))
  print(json.dumps(report,indent=2),flush=True)
  dialog.close()
  assert not controls, 'combined diagnostic controls extend outside viewport'
 finally:
  _close_automation_window(app,window)
