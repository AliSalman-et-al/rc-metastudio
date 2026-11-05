from pathlib import Path
import json,collections
from scripts import verify_golden_compatibility as v
root=Path.cwd();src=Path('/tmp/ci575-golden');archive,ref=v._load_frozen_reference(root);numeric=v._load_numeric_contract(root,archive,ref);plot=v._load_plot_descriptor_contract(root,archive,ref)
current=v._validate_capture(json.loads((src/'manifest.json').read_text()))
c=v.compare_golden_baseline(v._reference_with_numeric_contract(ref,numeric),current,exceptions=v._load_exception_manifest(root/'tests/analysis_regression/baseline/exceptions.json')['exceptions'],manifest=v._load_capture_manifest(root/'tests/analysis_regression/baseline/capture-manifest.json'));c['rows'].extend(v._compare_plot_descriptors(plot,current));failed=[x for x in c['rows'] if x['classification'] not in ['pass','accepted_exception']];counts=dict(collections.Counter(x['classification'] for x in c['rows']));result=dict(passed=not failed,source_run=42024841510,counts=counts,comparison=c);Path('artifacts/batch7-windows/windows-strict-replay.json').write_text(json.dumps(result,indent=2)+'\n');print(counts);assert not failed
