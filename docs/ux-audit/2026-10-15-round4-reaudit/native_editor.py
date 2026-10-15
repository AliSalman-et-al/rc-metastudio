"""Open an actual saved report in the host native editor; no application mutation."""
import json,hashlib,subprocess,re,os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
HERE=Path(__file__).resolve().parent
report=(HERE/'raw/native-design/review1-report.txt').resolve()
assert report.exists()
app=QApplication([]);assert app.platformName()=='xcb'
editor=subprocess.Popen(['xedit',str(report)])
try:
 QTest.qWait(1500)
 tree=subprocess.check_output(['xwininfo','-root','-tree'],text=True)
 ids=re.findall(r'(0x[0-9a-f]+).*xedit',tree,re.I);assert ids
 subprocess.run(['wmctrl','-ir',ids[0],'-b','add,maximized_vert,maximized_horz'],check=True)
 subprocess.run(['wmctrl','-ia',ids[0]],check=True);QTest.qWait(500)
 path=HERE/'screenshots/shell-exported-report-editor.png'
 assert app.primaryScreen().grabWindow(int(ids[0],16)).save(str(path),'PNG')
 (HERE/'EDITOR.json').write_text(json.dumps(dict(source=str(report),source_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),path=str(path.relative_to(HERE)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),capture='QScreen.grabWindow external xedit'),indent=2)+'\n')
finally:
 editor.terminate();editor.wait(timeout=5);app.quit()
print('WORKFLOW PASSED')

subprocess.run(['uv','run','python',str(HERE/'run.py'),'native-options-remaining','uv','run','python',str(HERE/'native_options_remaining.py')],check=True)
