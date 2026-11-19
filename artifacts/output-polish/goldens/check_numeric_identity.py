from io import BytesIO
from pathlib import Path
from subprocess import check_output
from zipfile import ZipFile
import json

base = Path("tests/analysis_regression/baseline")
prior = "70f4997a410ea558430d7408fea4a154f1ef3b59"

def frozen(path):
    return check_output(["git", "show", f"{prior}:{path.as_posix()}"])

contract = base / "numeric-contract.json"
old, new = (json.loads(source) for source in (frozen(contract), contract.read_bytes()))
old.pop("oracle_sha256")
new.pop("oracle_sha256")
assert old == new
assert sum(len(metrics) for case in new["cases"] for metrics in case["sections"].values()) == 416

archive = base / "observed-golden-baseline.zip"
with ZipFile(BytesIO(frozen(archive))) as before, ZipFile(archive) as after:
    assert before.namelist() == after.namelist()
    for member in before.namelist():
        if not member.startswith("captures/"):
            continue
        first, second = (json.loads(snapshot.read(member)) for snapshot in (before, after))
        for field in ("outputs", "tolerances", "numeric_tolerance_policy"):
            assert first.get(field) == second.get(field), (member, field)
print("All 416 contract values and tolerance policy identical; capture numerical outputs unchanged.")
