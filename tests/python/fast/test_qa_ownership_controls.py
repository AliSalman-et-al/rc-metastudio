import pytest
from scripts import qt_window_ownership as ownership
from scripts.audit_qt_layout_contracts import audit_repository

@pytest.mark.parametrize('body,live', [('def __init__(self):\n        adaptive_window.register_adaptive_window(self, adaptive_window.WindowRole.MAIN)',True),('def helper(self):\n        adaptive_window.register_adaptive_window(self, adaptive_window.WindowRole.MAIN)',False),('def __init__(self):\n        if False:\n            adaptive_window.register_adaptive_window(self, adaptive_window.WindowRole.MAIN)',False),('def __init__(self):\n        return\n        adaptive_window.register_adaptive_window(self, adaptive_window.WindowRole.MAIN)',False)])
def test_initializer_registration_contract(tmp_path,monkeypatch,body,live):
    monkeypatch.setattr(ownership,'TOP_LEVEL_FORM_INVENTORY',{'one.ui':(('one.py','One','MAIN'),)})
    (tmp_path/'one.ui').write_text('<ui><widget class="QMainWindow"/></ui>')
    (tmp_path/'one.py').write_text('class One:\n    '+body+'\n')
    findings=ownership.audit_top_level_form_ownership(tmp_path,tmp_path)
    assert bool(findings) is not live

def test_malformed_sources_keep_classified_findings(tmp_path):
    source=tmp_path/'src'/'rc_metastudio'; forms=source/'forms'; forms.mkdir(parents=True)
    (forms/'about_legal.ui').write_text('<ui>')
    (source/'about_legal_dialog.py').write_text('class !!!')
    codes={finding.rule for finding in audit_repository(tmp_path)}
    assert {'invalid-ui-xml','invalid-python'} <= codes
