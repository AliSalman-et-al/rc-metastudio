from pathlib import Path
import json,sys,collections
sys.path.insert(0,str(Path.cwd()))
from scripts import verify_golden_compatibility as v
root=Path.cwd();src=Path('/tmp/win-golden-bca2/full-r-stack-windows-golden-capture')
archive,reference=v._load_frozen_reference(root)
plot=v._load_plot_descriptor_contract(root,archive,reference);numeric=v._load_numeric_contract(root,archive,reference)
current=v._validate_capture(json.loads((src/'manifest.json').read_text()))
v._validate_case_contract(reference,current,root)
comparison=v._validate_comparison(v.compare_golden_baseline(v._reference_with_numeric_contract(reference,numeric),current,exceptions=v._load_exception_manifest(root/'tests/analysis_regression/baseline/exceptions.json').get('exceptions',[]),manifest=v._load_capture_manifest(root/'tests/analysis_regression/baseline/capture-manifest.json')))
comparison['rows'].extend(v._compare_plot_descriptors(plot,current));counts=dict(collections.Counter(r['classification'] for r in comparison['rows']));comparison['passed']=all(r['classification'] in {'pass','accepted_exception'} for r in comparison['rows'])
result=dict(source_manifest=str(src/'manifest.json'),counts=counts,comparison=comparison)
(root/'docs/ci/2026-11-03-windows-goldens/windows-strict-replay.json').write_text(json.dumps(result,indent=2)+'\n');print(counts);assert comparison['passed'] and counts=={'pass':462,'accepted_exception':13}
