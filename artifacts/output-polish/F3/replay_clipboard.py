from pathlib import Path
from PyQt6.QtCore import QMimeData, QTimer
from PyQt6.QtWidgets import QApplication

path = Path(__file__).resolve().parent
app = QApplication([])
data = QMimeData()
data.setText((path / "clipboard.txt").read_text(encoding="utf-8"))
data.setHtml((path / "clipboard.html").read_text(encoding="utf-8"))
app.clipboard().setMimeData(data)
print("Loaded the captured RCMS HTML and TSV onto the Windows clipboard", flush=True)
QTimer.singleShot(180_000, app.quit)
app.exec()
