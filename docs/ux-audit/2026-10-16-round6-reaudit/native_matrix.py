"""Reproduce fifty cells with actual X11 window captures; reuse maintained drives."""
import json, os, sys, traceback, hashlib, shutil
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, UTC
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '.agents/skills/verify-rcms/scripts'))
family = sys.argv[1]
style = os.environ.get('RCMS_AUDIT_STYLE', 'default')
assert style in ('default','revman','bmj')
suffix = '' if style == 'default' else '-' + style
work = HERE / 'raw' / ('matrix-' + family + suffix)
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
    output = HERE / 'screenshots' / (name + suffix + '.png')
    assert widget.screen().grabWindow(int(widget.winId())).save(str(output),'PNG')
    index.append(dict(path=output.relative_to(HERE).as_posix(),sha256=hashlib.sha256(output.read_bytes()).hexdigest(),capture='QScreen.grabWindow',family=family,workflow=workflow,identity=getattr(getattr(widget,'results',None),'identity',None)))
    (HERE / ('MATRIX-'+family+suffix+'.json')).write_text(json.dumps(index,indent=2)+'\n')
def prepare(target):
    model=target.model
    if workflow in ('subgroup','meta-regression'):
        name,kind=('Group','factor') if workflow=='subgroup' else ('Dose','continuous')
        model.dataset.add_covariate(Covariate(name,kind),{s.name: ('A' if i%2 else 'B') if kind=='factor' else float(i+1) for i,s in enumerate(model.get_studies(only_if_included=True))})
        model.reset_model(); target.enable_menu_options_that_require_dataset()
    target.out_path=str(work/(workflow+'-input.rcms'));assert target.save()
with patch('rc_metastudio.settings.get_base_path',return_value=str(work)):
    app,window=automation.start_automation()
    try:
        namespace['app']=app;namespace['window']=window;sys.excepthook=sys.__excepthook__
        namespace['doctor'](app,window)
        record=namespace['record_step']
        for workflow in ('standard','cumulative','leave-one-out','subgroup','meta-regression'):
            window.workspace.mark_saved()
            if family not in ('hr','irr'):
                view=matrix(app,window,'analysis-data-'+family,record,keep_results=True,workflow_override=workflow,parameters={'digits':6,'fp_style':style},prepare=prepare)
            else:
                sample='Pignon2000-HR' if family=='hr' else 'NielWeise2008-IRR'
                assert window.open(str(ROOT/'sample_projects'/(sample+'.rcms')),raise_on_error=True)
                prepare(window)
                if workflow!='meta-regression':
                    view=analyze_existing(app,window,workflow,('time_to_event' if family=='hr' else 'event_rates')+'.random',record,{'digits':6})
                else:
                    window.action_meta_regression.trigger();app.processEvents()
                    dialog=next(w for w in app.topLevelWidgets() if isinstance(w,analysis_setup_dialog.AnalysisSetupDialog) and w.isVisible())
                    for cov,checkbox in dialog.covs_and_check_boxes: checkbox.setChecked(cov.name=='Dose')
                    from analysis_matrix import set_parameter
                    set_parameter(app,dialog,'digits',6)
                    set_parameter(app,dialog,'fp_style',style)
                    QTest.mouseClick(dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok),QtCore.Qt.MouseButton.LeftButton);app.processEvents()
                    view=next(w for w in app.topLevelWidgets() if isinstance(w,results_window.ResultsWindow) and w.isVisible())
            view.resize(1500,850); app.processEvents(); QTest.qWait(500)
            check_report(app,view,work,record)
            if workflow in ('cumulative','leave-one-out'):check_sequential(view,workflow,record)
            if workflow=='subgroup':check_subgroup(view,record)
            (work/(workflow+'-report.txt')).write_text(app.clipboard().text())
            view.report_action.setChecked(False);view.report_action.trigger();view.report_text.verticalScrollBar().setValue(0)
            native(view,'matrix-'+family+'-'+workflow+'-report')
            view.report_text.verticalScrollBar().setValue(view.report_text.verticalScrollBar().maximum())
            native(view,'matrix-'+family+'-'+workflow+'-report-bottom')
            view.report_action.trigger()
            from PyQt6.QtCore import Qt
            for component,(title,path) in enumerate((view.results.display_images or view.results.images).items()):
                heading=next(s.title for s in view.results.sections if s.kind=='image' and s.source_key==title)
                items=view.nav_tree.findItems(heading,Qt.MatchFlag.MatchExactly|Qt.MatchFlag.MatchRecursive)
                assert len(items)==1
                view.nav_tree.scrollToItem(items[0]);QTest.mouseClick(view.nav_tree.viewport(),QtCore.Qt.MouseButton.LeftButton,pos=view.nav_tree.visualItemRect(items[0]).center());app.processEvents()
                assert view.content_stack.currentWidget() is view.figure_page and view.figure_page.isVisible()
                stem='matrix-'+family+'-'+workflow+'-figure'+('' if component==0 else '-'+str(component))
                native(view,stem)
                view.graphics_view.verticalScrollBar().setValue(view.graphics_view.verticalScrollBar().maximum())
                native(view,stem+'-bottom')
            for artifact_index,(title,base) in enumerate(view.params_paths.items()):
                for artifact in Path(base).parent.glob(Path(base).name+'.*'):
                    if artifact.is_file():shutil.copy2(artifact,work/(workflow+'-'+str(artifact_index)+'-'+artifact.name))
            record('audit-matrix-complete',view,family=family,workflow=workflow,identity=view.results.identity,text=view.report_text.toPlainText())
            view.close();app.processEvents()
            print(family,workflow,'PASSED',flush=True)
    finally:
        window.workspace.mark_saved()
        for widget in app.topLevelWidgets():widget.close()
        automation.dispose_qobjects(app,app.topLevelWidgets());app.quit()
print('WORKFLOW PASSED')
