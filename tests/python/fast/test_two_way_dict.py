import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rc_metastudio.two_way_dict import TwoWayDict


def test_two_way_dict_replaces_existing_reverse_mapping():
    mapping = TwoWayDict({"a": 1, "b": 2})

    mapping["c"] = 2

    assert "b" not in mapping
    assert mapping["c"] == 2
    assert mapping.key(2) == "c"
