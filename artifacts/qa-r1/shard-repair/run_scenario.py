"""Run one ordinary real Qt/R evidence scenario with a generous timeout."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root))
import scripts.verify_rcms as verify
verify._scenario_timeout = lambda scenario: 1800
raise SystemExit(verify.main())
