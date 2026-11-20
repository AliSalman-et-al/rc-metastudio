from pathlib import Path
import argparse
from PyQt6.QtCore import QMimeData, QTimer
from PyQt6.QtWidgets import QApplication

parser = argparse.ArgumentParser(description="Replay the clipboard captured by the F3 native drive.")
parser.add_argument("workflow", type=Path)
path = parser.parse_args().workflow
app = QApplication([])
data = QMimeData()
data.setText((path / "clipboard.txt").read_text(encoding="utf-8"))
data.setHtml((path / "clipboard.html").read_text(encoding="utf-8"))
app.clipboard().setMimeData(data)
print("Loaded the captured RCMS HTML and TSV onto the Windows clipboard", flush=True)
QTimer.singleShot(180_000, app.quit)
app.exec()
