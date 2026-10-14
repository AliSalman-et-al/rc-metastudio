"""Run the existing installed-package, 21-case deterministic visual check."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.verify_rcmetar_r_stack import verify_reitsma_visual_evidence

work = ROOT / "artifacts/verification/rcms/review2-reitsma-complete"
work.mkdir(parents=True, exist_ok=True)
verify_reitsma_visual_evidence(
    ROOT, Path(os.environ["RCMS_R_HOME"]) / "bin/Rscript.exe", dict(os.environ), work
)
