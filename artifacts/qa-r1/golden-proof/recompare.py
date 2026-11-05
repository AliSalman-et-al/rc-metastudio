from pathlib import Path
import json
from scripts.verify_golden_compatibility import _load_frozen_reference, _load_numeric_contract, _load_plot_descriptor_contract, _reference_with_numeric_contract, _load_exception_manifest, _load_capture_manifest, _compare_plot_descriptors
from tests.analysis_regression.golden.support.analysis_regression_compare import compare_golden_baseline
root=Path(__file__).resolve().parents[3]
archive, reference=_load_frozen_reference(root)
numeric=_load_numeric_contract(root, archive, reference)
plots=_load_plot_descriptor_contract(root, archive, reference)
current=json.loads((root/'artifacts/qa-r1/golden-proof/current/manifest.json').read_text())
comparison=compare_golden_baseline(_reference_with_numeric_contract(reference,numeric), current, exceptions=_load_exception_manifest(root/'tests/analysis_regression/baseline/exceptions.json')['exceptions'], manifest=_load_capture_manifest(root/'tests/analysis_regression/baseline/capture-manifest.json'))
comparison['rows'].extend(_compare_plot_descriptors(plots,current))
failed=[row for row in comparison['rows'] if row['classification'] not in ('pass','accepted_exception')]
print(json.dumps({'passed':not failed, 'rows':len(comparison['rows']), 'failures':failed},indent=2))
assert not failed
