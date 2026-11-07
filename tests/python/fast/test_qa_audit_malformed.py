import json
import pytest
from scripts.audit_result_formatting import load_records, audit_records

@pytest.mark.parametrize('wrapper', [lambda x:x, lambda x:{'records':x}, lambda x:{'captures':x}])
def test_malformed_capture_member_is_reported_with_source_and_index(tmp_path, wrapper):
    path=tmp_path/'capture.json'
    path.write_text(json.dumps(wrapper([17])), encoding='utf-8')
    report=audit_records(load_records([path]))
    assert any(f['code']=='malformed-record' and f['source']==str(path)+'#1' for f in report['findings'])
