"""Keep the final-source R build/check directory after verification."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
work = ROOT / "build/verification/round2-package-check"
work.mkdir(parents=True, exist_ok=True)
r = str(Path(os.environ["RCMS_R_HOME"]) / "bin/R.exe")
commands = [[r, "CMD", "build", "--no-build-vignettes", str(ROOT / "r/RCMetaR")],
            [r, "CMD", "check", "--no-manual", "--no-build-vignettes", "RCMetaR_0.4.2.tar.gz"]]
for command in commands:
    print(json.dumps(dict(command=command, cwd=str(work))), flush=True)
    subprocess.run(command, cwd=work, check=True)
