from pathlib import Path
from unittest.mock import patch
import hashlib,json
from PyQt6.QtCore import QSettings,QStandardPaths
from rc_metastudio.qt6_ui import prepare_generated_ui_imports
prepare_generated_ui_imports()
from rc_metastudio.automation import start_package_analyze
from rc_metastudio.result_text_identity import normalize_packaged_summary_identity
from scripts.inspect_windows_deployment import EXPECTED_SUMMARY_SHA256
root=Path(__file__).resolve().parents[3]
work=root/'artifacts/qa-r1/reduced-scope/package-source'
work.mkdir(exist_ok=True)
QStandardPaths.setTestModeEnabled(True)
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat,QSettings.Scope.UserScope,str(work/'settings'))
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
    code=start_package_analyze(str(work/'observation.json'),str(root/'sample_projects/amino.rcms'),'binary.random')
assert code==0
summary=json.loads((work/'observation.json').read_text())['texts']['Summary']
actual=hashlib.sha256(normalize_packaged_summary_identity(summary).encode()).hexdigest()
report={'passed':actual==EXPECTED_SUMMARY_SHA256,'expected':EXPECTED_SUMMARY_SHA256,'observed':actual,'scope':'real source application through the package automation entry, Linux offscreen, private R library; not Windows package qualification'}
(work/'summary-identity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert report['passed']
