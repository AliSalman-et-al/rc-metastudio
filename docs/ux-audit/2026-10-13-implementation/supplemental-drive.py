import os, sys, json, traceback, hashlib, subprocess
from datetime import UTC, datetime
from pathlib import Path
ROOT=Path.cwd()
AUDIT=ROOT/'docs/ux-audit/2026-10-13-implementation'
kind, workflow=sys.argv[1:3]
E=AUDIT/'evidence-final'/(datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')+'-supplemental-'+kind+'-'+workflow)
E.mkdir(parents=True, exist_ok=True)
W=E/'workflow'; W.mkdir(exist_ok=True)
os.environ['RCMS_E2E_EVIDENCE_DIR']=str(E)
os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(W/'analysis')
sys.argv=['desktop_driver.py','audit',str(W)]
driver=ROOT/'tests/e2e/desktop_driver.py'
namespace={'__file__':str(driver),'__name__':'audit_driver'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0],str(driver),'exec'),namespace)
app=None; errors=[]
patcher=namespace['patch']('rc_metastudio.settings.get_base_path',return_value=W.as_posix()); patcher.start()
try:
 app,window=namespace['automation'].start_automation()
 sys.excepthook=sys.__excepthook__
 namespace['doctor'](app,window)
 sys.path.insert(0,str(ROOT/'.agents/skills/verify-rcms/scripts'))
 from analysis_matrix import run
 from rc_metastudio.analysis_dataset import Covariate
 def prepare(window):
  if workflow in ('subgroup','meta-regression'):
   studies=window.model.get_studies(only_if_included=True)
   name,typ=('Group','factor') if workflow=='subgroup' else ('Dose','continuous')
   window.model.dataset.add_covariate(Covariate(name,typ),{s.name:('A' if i%2 else 'B') if typ=='factor' else float(i+1) for i,s in enumerate(studies)})
   window.model.reset_model(); window.enable_menu_options_that_require_dataset()
   window.out_path=str(W/'with-covariates.rcms'); window.save()
 def reject_messages():
  for item in app.topLevelWidgets():
   if isinstance(item,namespace['QtWidgets'].QMessageBox) and item.isVisible():
    errors.append(item.text()); namespace['record_step']('unexpected-dialog',item,message=item.text()); item.reject()
 timer=namespace['QtCore'].QTimer(); timer.timeout.connect(reject_messages); timer.start(100)
 run(app,window,'analysis-data-'+kind,namespace['record_step'],workflow_override=workflow,prepare=prepare)
 assert not errors,errors
 namespace['record_step']('audit-workflow-passed',window,data_type=kind,workflow=workflow)
 (E/'status.json').write_text(json.dumps({'passed':True,'type':kind,'workflow':workflow,'entrypoint':'audit supplemental driver; existing analysis_matrix widgets and real R backend','command':['uv','run','python','docs/ux-audit/2026-10-13-implementation/supplemental-drive.py',kind,workflow], 'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(), 'worktree_status':subprocess.check_output(['git','status','--short'],text=True).strip(), 'numerical_scope':'rendering and routing, no independent numerical oracle'},indent=2))
finally:
 if app:
  window.workspace.mark_saved()
  for item in app.topLevelWidgets(): item.close()
  namespace['automation'].dispose_qobjects(app,app.topLevelWidgets());app.quit()
 patcher.stop()
