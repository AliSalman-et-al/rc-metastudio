"""Replay the actual exact-archive smoke evidence through the unchanged gates."""
import json,hashlib
from pathlib import Path
from scripts import inspect_windows_deployment as gate
from rc_metastudio.result_text_identity import normalize_packaged_summary_identity as norm
root=Path('/tmp/ci575-diagnostics/work/archive-qualification/RCMetaStudio-0.5.1-windows-x64/qualification');smoke=json.loads((root/'packaged-smoke.json').read_text());log=(root/'packaged-smoke.log').read_text();summary=json.loads((root/'workflow-observation.json').read_text())['summary']
old=hashlib.sha256(norm(summary.replace('Metric: Odds ratio','Metric: Odds Ratio')).encode()).hexdigest();new=hashlib.sha256(norm(summary).encode()).hexdigest();assert old=='61ea84ba73eab657282ceabdf3ee1f29ab0ed55a1be574023017bc490d279ab5';assert new==gate.EXPECTED_SUMMARY_SHA256
variants=smoke['workflows']['locale_variants'];assert variants[0]['svg_sha256']==variants[1]['svg_sha256'];gate._validate_windows_smoke(smoke,log);gate._validate_windows_extracted_smoke(smoke,log)
Path('artifacts/batch7-windows/package-proof.json').write_text(json.dumps(dict(passed=True,job=127237038608,cause='stale normalized summary identity, not SVG mismatch or Windows golden drift',only_text_change='Metric: Odds Ratio -> Metric: Odds ratio',old_normalized_sha256=old,new_normalized_sha256=new,english_german_svg_hashes_identical=True,original_smoke_validated_without_policy_changes=True),indent=2)+'\n');print('PASS exact-archive package evidence; only the approved metric-name case changed its expected summary hash.')
