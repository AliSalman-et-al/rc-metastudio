"""Reproduce native clipboard ownership independently of RCMS and R."""

import json
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QLabel


app = QApplication([])
label = QLabel("Native Qt clipboard ownership probe; no RCMS components loaded")
label.show()
app.processEvents()
clipboard = app.clipboard()
assert clipboard is not None
rows = []
for text in (
    "simple",
    "1.00\tSouth\n2.00\tNorth",
    "1.00 South\n2.00 North",
    "\n".join(f"{i + 1:.2f}\t{'North' if i % 2 else 'South'}" for i in range(19)),
):
    clipboard.setText(text)
    observed = clipboard.text()
    mime = clipboard.mimeData()
    rows.append({
        "input": text,
        "observed": observed,
        "matches": text == observed,
        "owns_clipboard": clipboard.ownsClipboard(),
        "formats": mime.formats() if mime is not None else [],
    })
print(json.dumps({"platform": app.platformName(), "observations": rows}, indent=2))
label.grab().save(str(Path(__file__).with_name("screenshots") / "clipboard-probe.png"))
label.close()
app.quit()
