"""Retain exact recorded attempts and verbatim failure lines without raw logs."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
records = []
for path in sorted((HERE / "raw").glob("*.json")):
    try:
        row = json.loads(path.read_text())
    except (ValueError, UnicodeError):
        continue
    if not isinstance(row, dict) or not {"label", "command", "exit_code", "log"}.issubset(row):
        continue
    log = HERE / "raw" / row["log"]
    assert hashlib.sha256(log.read_bytes()).hexdigest() == row["sha256"], path
    if row["exit_code"]:
        row["failure_lines_verbatim"] = [line for line in log.read_text(errors="replace").splitlines()
            if re.search(r"(?:\w*Error:|^FAILED |^error:|timed out after|^ERROR|^Status:|^Found \d+ diagnostics)", line)]
    records.append(row)
(HERE / "TEST-RUNS.json").write_text(json.dumps(records, indent=2) + "\n")
commits = subprocess.check_output(["git", "log", "--reverse", "--format=%h %s", "71a8545^..HEAD"], text=True)
(HERE / "COMMITS.md").write_text("# Round 3 commits\n\nEach commit was immediately fast-forward pushed to `origin/ux/audit-improvements`.\n\n```text\n" + commits + "```\n")
print(f"Retained {len(records)} attempts; {sum(bool(row['exit_code']) for row in records)} nonzero exits.")
