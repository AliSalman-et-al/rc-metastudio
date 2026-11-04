"""Exercise the exact CI authority step against a private installed package."""
import os
from pathlib import Path
from scripts.verify_rcmetar_r_stack import verify_analysis_authorities
verify_analysis_authorities(Path.cwd(), Path(os.environ["RCMS_R_HOME"]) / "bin/Rscript", dict(os.environ))
