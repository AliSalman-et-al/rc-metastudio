"""Replay the sanctioned capture without manufacturing its missing descriptors."""
import json
from pathlib import Path
from collections import Counter
from scripts.verify_golden_compatibility import (_load_frozen_reference, _load_numeric_contract,
    _load_plot_descriptor_contract, _reference_with_numeric_contract, _load_exception_manifest,
    _load_capture_manifest, _compare_plot_descriptors)
from tests.analysis_regression.golden.support.analysis_regression_compare import compare_golden_baseline
root = Path(__file__).resolve().parents[4]
here = Path(__file__).resolve().parent
archive, reference = _load_frozen_reference(root)
numeric = _load_numeric_contract(root, archive, reference)
plots = _load_plot_descriptor_contract(root, archive, reference)
current = json.loads((root/'build/qa567-windows-capture/manifest.json').read_text())
comparison = compare_golden_baseline(_reference_with_numeric_contract(reference, numeric), current,
    exceptions=_load_exception_manifest(root/'tests/analysis_regression/baseline/exceptions.json')['exceptions'],
    manifest=_load_capture_manifest(root/'tests/analysis_regression/baseline/capture-manifest.json'))
comparison['rows'].extend(_compare_plot_descriptors(plots, current))
failures = [r for r in comparison['rows'] if r['classification'] not in ('pass','accepted_exception')]
assert {r["id"] for r in failures} == {"amino-binary-subgroup", "lymph-diagnostic-random-dor"}, failures
assert next(r for r in failures if r["id"]=="lymph-diagnostic-random-dor")["detail"] == "Display identity/content or plot capability metadata drifted."
import zipfile
old_reference = json.loads(zipfile.ZipFile(here/"old/observed-golden-baseline.zip").read("manifest.json"))
old_amino = next(r for r in old_reference["curated_golden_set"] if r["id"]=="amino-binary-subgroup")
new_amino = next(r for r in reference["curated_golden_set"] if r["id"]=="amino-binary-subgroup")
assert old_amino == new_amino, "Unrelated master subgroup reference changed"
report = dict(numeric_and_text_passed=True, unrelated_master_amino_reference_unchanged=True, classifications=dict(Counter(r['classification'] for r in comparison['rows'])),
              unresolved_raw_capture_metadata=failures,
              note='The original Windows capture has null descriptors from the stale title lookup; expectations remain strict. A fresh capture using the repaired path lookup must satisfy them.')
(here/'recomparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
