"""Reproduce fifty cells with actual X11 window captures; reuse maintained drives."""
import json, os, sys, traceback, hashlib, shutil
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, UTC
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '.agents/skills/verify-rcms/scripts'))
family = 'samples'
work = HERE / 'raw' / ('matrix-' + family)
work.mkdir(parents=True, exist_ok=True)
sys.argv = ['native_matrix.py', 'doctor', str(work)]
os.environ['RCMS_E2E_EVIDENCE_DIR'] = str(work)
os.environ['RCMS_REQUIRE_IN_PROCESS_RPY2']='1'
os.environ['RCMS_ANALYSIS_SCRATCH_DIR']=str(work/'analysis-scratch');(work/'analysis-scratch').mkdir(exist_ok=True)
# Reuse the helper's initialization and observation functions, without its scenario dispatch.
driver = ROOT / 'tests/e2e/desktop_driver.py'
namespace = {'__file__': str(driver), '__name__': 'audit_driver'}
exec(compile(driver.read_text().split('\nbase_path_patch = patch(')[0], str(driver), 'exec'), namespace)
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtTest import QTest
from rc_metastudio import automation, results_window, analysis_setup_dialog
from rc_metastudio.analysis_dataset import Covariate
from analysis_matrix import run as matrix
from tests.e2e.audit_round3 import analyze_existing, check_report, check_sequential, check_subgroup
QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope, str(work))
index=[]
def native(widget, name):
    widget.raise_(); widget.activateWindow(); app.processEvents(); QTest.qWait(500)
    assert app.platformName() == 'xcb' and widget.isVisible()
    assert widget.windowHandle().isExposed()
    output = work / 'captures' / (name + '.png')
    output.parent.mkdir(exist_ok=True)
    assert widget.screen().grabWindow(int(widget.winId())).save(str(output),'PNG')
    index.append(dict(path=output.relative_to(HERE).as_posix(),sha256=hashlib.sha256(output.read_bytes()).hexdigest(),capture='QScreen.grabWindow',family=family,workflow=workflow,identity=getattr(getattr(widget,'results',None),'identity',None)))
    (HERE / ('MATRIX-'+family+'.json')).write_text(json.dumps(index,indent=2)+'\n')
def prepare(target):
    model=target.model
    if workflow in ('subgroup','meta-regression'):
        name,kind=('Group','factor') if workflow=='subgroup' else ('Dose','continuous')
        model.dataset.add_covariate(Covariate(name,kind),{s.name: ('A' if i%2 else 'B') if kind=='factor' else float(i+1) for i,s in enumerate(model.get_studies(only_if_included=True))})
        model.reset_model(); target.enable_menu_options_that_require_dataset()
    target.out_path=str(work/(workflow+'-input.rcms'));assert target.save()
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
    app,window=automation.start_automation();sys.excepthook=sys.__excepthook__;namespace['app']=app;namespace['window']=window;workflow='standard'
    try:
        namespace['doctor'](app,window)
        proofs=[]
        for filename,method in [('amino.rcms','binary.random'),('BCG.rcms','binary.random'),('continuous.rcms','continuous.random'),('meantime.rcms','binary.random'),('lymph.rcms','diagnostic.random'),('Pignon2000-HR.rcms','time_to_event.random'),('NielWeise2008-IRR.rcms','event_rates.random')]:
            source=ROOT/'sample_projects'/filename;before=source.read_bytes()
            window.workspace.mark_saved();assert window.open(str(source),raise_on_error=True)
            groups=list(window.model.current_groups);native(window,'sample-'+source.stem+'-grid')
            view=namespace['analyze'](app,window,method)
            check_report(app,view,work,namespace['record_step'])
            (work/(source.stem+'-report.txt')).write_text(app.clipboard().text())
            view.report_action.setChecked(False);view.report_action.trigger();native(view,'sample-'+source.stem+'-report')
            view.report_action.trigger();native(view,'sample-'+source.stem+'-figure');view.close();app.processEvents()
            destination=work/filename;window.out_path=str(destination);assert window.save();assert window.open(str(destination),raise_on_error=True)
            assert list(window.model.current_groups)==groups and source.read_bytes()==before
            proofs.append(dict(file=str(source.relative_to(ROOT)),sha256=hashlib.sha256(before).hexdigest(),groups=groups,method=method,reopened=str(destination.relative_to(HERE))))
            (HERE/'SAMPLE-NATIVE.json').write_text(json.dumps(proofs,indent=2)+'\n')
            print(filename,'SAMPLE PASSED',flush=True)
    finally:
        window.workspace.mark_saved()
        for widget in app.topLevelWidgets():widget.close()
        automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
