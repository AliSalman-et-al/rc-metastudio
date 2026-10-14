"""Install current RCMetaR and retain the exact input and installed file hashes."""

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
package = ROOT / "r/RCMetaR"
library = Path(os.environ["RCMS_R_LIBS"]).resolve()
r_home = Path(os.environ["RCMS_R_HOME"]).resolve()
assert library.is_relative_to(ROOT / "build/ux-round3"), library
files = [package / "DESCRIPTION", package / "NAMESPACE"]
files.extend(p for folder in ("R", "inst", "man") for p in (package / folder).rglob("*") if p.is_file())
hashes = {p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
command = [str(r_home / "bin/R"), "CMD", "INSTALL", "--library=" + str(library), str(package)]
subprocess.run(command, cwd=ROOT, check=True)
assert hashes == {p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
installed = library / "RCMetaR"
record = dict(command=command, exit_code=0, utc=datetime.now(UTC).isoformat(),
              revision=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              r_home=str(r_home), library=str(library), source_sha256=hashes,
              installed_sha256={p.relative_to(installed).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(installed.rglob("*")) if p.is_file()},
              runtime_archive_sha256=hashlib.sha256((ROOT / "build/ux-round3/runtime-cache/r-4.6.1_1_amd64.deb").read_bytes()).hexdigest())
assert record["runtime_archive_sha256"] == "5af816371126c8e5895600de035153cd3a64b12f4beb43f291ee34bf24f8fd2d"
(HERE / "INSTALLED-SOURCE.json").write_text(json.dumps(record, indent=2) + "\n")
print("Installed current RCMetaR; source and installed hashes: " + str(HERE / "INSTALLED-SOURCE.json"))
