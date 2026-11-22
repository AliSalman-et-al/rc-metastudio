from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def test_direct_provenance_entrypoint_works_without_pythonpath():
    result = subprocess.run(
        [sys.executable, "-E", str(ROOT / "scripts/build_macos_direct_provenance.py"), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "--qualification-root" in result.stdout
