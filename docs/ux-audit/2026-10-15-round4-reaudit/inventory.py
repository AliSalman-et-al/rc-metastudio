"""Index retained run receipts and hashes; never promote inventory to visual inspection."""
from pathlib import Path
import json,hashlib,re,runpy
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
runs=[];failures=[]
for f in sorted((HERE/'raw').glob('*.json')):
 try:d=json.loads(f.read_text())
 except (ValueError,OSError):continue
 if not isinstance(d,dict) or not {'command','exit_code'}<=d.keys():continue
 d['receipt']='raw/'+f.name;runs.append(d)
 if d['exit_code']:
  log=HERE/'raw'/d['log'];text=log.read_text();start=text.find('Traceback')
  failures.append({'run':d['label'],'exit_code':d['exit_code'],'log':str(log.relative_to(HERE)),'log_sha256':sha(log),'verbatim':text[start:] if start>=0 else text,'classification':'audit wrapper; wrong expected diagnostic dialog class' if d['label']=='native-options' else 'inspect transcript'})
# Doctor predates the generic recorder; its original manifest remains authoritative.
doctor=ROOT/'artifacts/verification/rcms/20261015T005129Z-709d071e-doctor/manifest.json'
completed=[r['label'][7:] for r in runs if r['label'].startswith('helper-') and r['exit_code']==0]
registry=list(runpy.run_path(str(ROOT/'scripts/verify_rcms.py'))['SCENARIOS'])
(HERE/'OUTCOMES.json').write_text(json.dumps({'scope':'Fresh independent native audit; no full-profile claim','counts':{'recorded_runs':len(runs),'passed':sum(r['exit_code']==0 for r in runs),'failed':sum(r['exit_code']!=0 for r in runs),'helper_scenarios_passed':len(completed)},'doctor_manifest':str(doctor.relative_to(ROOT)),'doctor_manifest_sha256':sha(doctor),'doctor':json.loads(doctor.read_text()),'helper_scenarios_not_freshly_run':[s for s in registry if s not in completed and s!='doctor'],'runs':runs},indent=2)+'\n')
(HERE/'FAILURES.json').write_text(json.dumps({'failed_runs':failures,'other_rejected_or_interrupted_evidence':['Two early matrix processes overlapped; affected frames rejected, binary/proportion serially recaptured.','Two premature contact-sheet builds raised AssertionError before capture files existed; bookkeeping only.','Initial shell editor selected an intermediate *-report.txt; replaced by explicit actual exported report path.','Broad queue stopped between cases after capacity resumption; no completed case repeated.'],'intentional_product_error':'Invalid contour levels: Details: contour levels must be between 0 and 100; valid retry succeeded (EXTRA.json).'},indent=2)+'\n')
shots=[]
for f in sorted((HERE/'screenshots').glob('*.png')):
 shots.append({'path':str(f.relative_to(HERE)),'sha256':sha(f),'inspection':'See INSPECTIONS.json and review-sheet membership; no blanket inspection claim'})
(HERE/'EVIDENCE.json').write_text(json.dumps({'application_start_revision':'f1aa24d','runtime_receipt':'../2026-10-15-round4/RUNTIME.json','installed_source_receipt':'../2026-10-15-round4/INSTALLED-SOURCE.json','provenance':'PROVENANCE.json','raw_logs':'raw/ (ignored); helper artifacts under artifacts/verification/rcms/ (ignored)','screenshots':shots,'capture_methods':{'matrix/design/shell/options/extra':'QScreen.grabWindow on visible xcb native windows','helper':'QWidget.grab in visible xcb native windows','editor':'QScreen.grabWindow of external native xedit'},'inventories':{f.name:sha(f) for f in sorted(HERE.glob('*.json')) if f.name not in ('EVIDENCE.json',)},'replay':'RUN-MATRIX.sh and RUN-FINISH.sh; native_*.py through run.py after sourcing round-three ENV.sh'},indent=2)+'\n')
print('runs',len(runs),'helpers',len(completed),'failed',len(failures),'screenshots',len(shots))
