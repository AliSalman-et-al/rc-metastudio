"""Exercise the repaired lookup on a real Qt/R lymph fit; keep strict metadata."""
import json
from pathlib import Path
from rc_metastudio.qt6_ui import prepare_generated_ui_imports
prepare_generated_ui_imports()
from rc_metastudio.app_error_handler import get_or_create_application
app = get_or_create_application([])
from rc_metastudio import r_bridge
from tests.analysis_regression.golden.support import golden_analysis, headless_analysis
from scripts.verify_golden_compatibility import _compare_plot_descriptors
root = Path(__file__).resolve().parents[4]
here = Path(__file__).resolve().parent
r_bridge.RLibraryLoader().load_rcmetar()
bundle = next(b for b in golden_analysis.curated_golden_bundles(str(root)) if b['id']=='lymph-diagnostic-random-dor')
result = headless_analysis.run_headless_analysis(bundle['case'])
descriptors = golden_analysis._capture_plot_descriptors(bundle, result)
contract = json.loads((root/'tests/analysis_regression/baseline/plot-descriptors.json').read_text())
contract['rows'] = [r for r in contract['rows'] if r['id']==bundle['id']]
rows = _compare_plot_descriptors(contract, {'curated_golden_set':[{'id':bundle['id'], 'plot_descriptors':descriptors}]})
assert all(r['classification']=='pass' for r in rows), rows
identity = descriptors[0]['display']['identity']
assert identity=='Diagnostic Odds Ratio Forest Plot', identity
(here/'descriptor-proof.json').write_text(json.dumps(dict(passed=True, descriptors=descriptors, comparison=rows),indent=2)+'\n')
print('PASS: actual SVG content, identity, filename/type and all five capability fields satisfy the unchanged strict descriptor requirements')
