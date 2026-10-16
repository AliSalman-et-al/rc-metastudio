"""Native Open/Save/export/colour chooser cancellation and dirty Quit recovery."""
import ctypes,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
work=HERE/'raw/native-controls';work.mkdir(parents=True,exist_ok=True)
sys.argv=['native_controls.py','doctor',str(work)]
os.environ['RCMS_E2E_EVIDENCE_DIR']=str(work);os.environ['RCMS_REQUIRE_IN_PROCESS_RPY2']='1';os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(work/'scratch');(work/'scratch').mkdir(exist_ok=True)
driver=ROOT/'tests/e2e/desktop_driver.py';ns={'__file__':str(driver),'__name__':'native_controls_audit'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0],str(driver),'exec'),ns)
from PyQt6 import QtCore,QtWidgets
from PyQt6.QtTest import QTest
from rc_metastudio import automation
from rc_metastudio.plot_editor_dialog import EditPlotDialog
from advanced_workflows import modal,click
rows=[]
def capture(widget,tag,wid=None):
 path=work/'captures'/('controls-'+tag+'.png');path.parent.mkdir(exist_ok=True)
 assert widget.screen().grabWindow(wid or int(widget.winId())).save(str(path),'PNG')
 rows.append({'path':str(path.relative_to(HERE)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'title':widget.windowTitle(),'window_id':wid,'capture':'Native QScreen.grabWindow','tag':tag})
 (HERE/'CONTROLS.json').write_text(json.dumps(rows,indent=2)+'\n')
def native_cancel(dialog,tag):
 if isinstance(dialog,QtWidgets.QFileDialog):dialog.setDirectory(str(work.resolve()))
 app.processEvents();QTest.qWait(350)
 tree=subprocess.check_output(['xwininfo','-root','-tree'],text=True);(work/(tag+'-xwininfo.txt')).write_text(tree)
 candidates=re.findall(r'(0x[0-9a-f]+) "'+re.escape(dialog.windowTitle())+'"',tree)
 owned=[]
 for candidate in candidates:
  prop=subprocess.check_output(['xprop','-id',candidate,'_NET_WM_PID'],text=True)
  match=re.search(r'=\s*(\d+)',prop)
  if match and int(match[1])==os.getpid():owned.append(candidate)
 assert len(owned)==1,(dialog.windowTitle(),owned,candidates)
 wid=owned[0];subprocess.run(['wmctrl','-ia',wid],check=True);QTest.qWait(200)
 active=subprocess.check_output(['xprop','-root','_NET_ACTIVE_WINDOW'],text=True)
 assert int(re.search(r'0x[0-9a-f]+',active)[0],16)==int(wid,16),active
 capture(dialog,tag,int(wid,16))
 x=ctypes.CDLL('libX11.so.6');xt=ctypes.CDLL('libXtst.so.6')
 x.XOpenDisplay.restype=ctypes.c_void_p;x.XOpenDisplay.argtypes=[ctypes.c_char_p]
 x.XStringToKeysym.argtypes=[ctypes.c_char_p];x.XStringToKeysym.restype=ctypes.c_ulong
 x.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong];x.XKeysymToKeycode.restype=ctypes.c_ubyte
 x.XFlush.argtypes=[ctypes.c_void_p];x.XCloseDisplay.argtypes=[ctypes.c_void_p]
 xt.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
 display=x.XOpenDisplay(None);assert display
 try:
  code=x.XKeysymToKeycode(display,x.XStringToKeysym(b'Escape'));assert code
  xt.XTestFakeKeyEvent(display,code,1,0);xt.XTestFakeKeyEvent(display,code,0,0);x.XFlush(display);QTest.qWait(350)
 finally:x.XCloseDisplay(display)
 assert not dialog.isVisible(),tag+' did not close after native Escape'
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
 app,window=automation.start_automation();sys.excepthook=sys.__excepthook__;ns.update(app=app,window=window)
 try:
  ns['doctor'](app,window)
  original=ROOT/'sample_projects/amino.rcms';before=original.read_bytes();owned=work/'input.rcms';shutil.copy2(original,owned)
  assert window.open(str(owned),raise_on_error=True);path=window.out_path
  modal(app,QtWidgets.QFileDialog,lambda d:native_cancel(d,'open-picker'),window.action_open.trigger)
  assert window.out_path==path and not window.workspace.is_dirty
  modal(app,QtWidgets.QFileDialog,lambda d:native_cancel(d,'save-as-picker'),window.action_save_as.trigger)
  assert window.out_path==path and owned.read_bytes()==before
  view=ns['analyze'](app,window,'binary.random')
  modal(app,QtWidgets.QFileDialog,lambda d:native_cancel(d,'plot-export-picker'),view.export_plot_action.trigger)
  plot_before={p:Path(p).read_bytes() for p in view.results.display_images.values()}
  def editor(d):
   modal(app,QtWidgets.QColorDialog,lambda colour:native_cancel(colour,'accent-colour-picker'),d.color_btn.click)
   capture(d,'editor-after-colour-cancel');d.reject()
  modal(app,EditPlotDialog,editor,view.edit_plot_action.trigger)
  assert all(Path(p).read_bytes()==data for p,data in plot_before.items())
  view.close();app.processEvents()
  assert window.model.setData(window.model.index(0,window.model.NAME),'Owned quit-cancel probe')
  def cancel_quit(d):capture(d,'dirty-quit-prompt');click(app,d.button(QtWidgets.QMessageBox.StandardButton.Cancel))
  modal(app,QtWidgets.QMessageBox,cancel_quit,window.action_quit.trigger)
  assert window.isVisible() and window.workspace.is_dirty and window.model.dataset.studies[0].name=='Owned quit-cancel probe'
  assert owned.read_bytes()==before and original.read_bytes()==before
  capture(window,'dirty-quit-cancel-preserved')
 finally:
  window.workspace.mark_saved()
  for widget in app.topLevelWidgets():widget.close()
  automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
