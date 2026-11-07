"""Bounded historical driver contracts; no Qt, R, installs, or live audit runs.

Run with --baseline to execute the preserved parent versions as broken controls.
All driver copies, generated input archives and command stand-ins live in temp dirs.
"""
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASELINE = '--baseline' in sys.argv
sys.argv = [sys.argv[0]]

def source(path):
    if BASELINE:
        return subprocess.check_output(['git', 'show', 'f6ffae40:' + path], cwd=ROOT, text=True)
    return (ROOT / path).read_text()

def block(path, start, end, ns):
    tree = ast.parse(source(path))
    nodes = [node for node in tree.body if node.lineno >= start and node.lineno < end]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), path, 'exec'), ns)

class HistoricalContracts(unittest.TestCase):
    def test_G7A_002_archive_inventory(self):
        path = 'artifacts/batch7-review/prove-goldens.py'
        code = source(path).split('old_contract=')[0]
        case = {'id': 'one', 'outputs': {'estimate': 1}, 'parameters': {}}
        def archive(cases, extra=False):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w') as z:
                z.writestr('manifest.json', json.dumps({'curated_golden_set': cases}))
                z.writestr('one.png', b'original raster')
                if extra: z.writestr('extra.png', b'unexpected')
            return stream.getvalue()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); base = root/'tests/analysis_regression/baseline'; base.mkdir(parents=True)
            old = archive([case])
            with patch('subprocess.check_output', return_value=old):
                # Path's relative IO follows real cwd; no live historical path is run.
                import os
                previous = Path.cwd(); os.chdir(root)
                try:
                    for cases, extra, fails in [([case],False,False),([],False,True),([dict(case,id='other')],False,True),([case],True,True)]:
                        (base/'observed-golden-baseline.zip').write_bytes(archive(cases,extra))
                        if fails:
                            with self.assertRaises(AssertionError): exec(code, {'__file__': str(root/'proof.py')})
                        else: exec(code, {'__file__': str(root/'proof.py')})
                finally: os.chdir(previous)

    def test_G7B_004_axis_inventory_and_ticks(self):
        code = source('docs/ux-audit/2026-10-16-round6-release-fixes/axis_text_probe.py')
        from types import ModuleType
        fake = ModuleType('tests.e2e.axis_conventions')
        fake.ticks = lambda path: [(x, 10) for x in (0,.2,.4,.6,.8,1)]
        names = [f'{f}-{h/100:g}.svg' for f in ('sans','serif','Arial','Liberation-Sans') for h in range(200,211)]
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, {'tests.e2e.axis_conventions':fake}), patch.object(sys,'argv',['probe',directory]):
            folder=Path(directory)
            with self.assertRaises(AssertionError): exec(code,{})
            for name in names: (folder/name).write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
            exec(code,{})
            (folder/names[0]).rename(folder/'wrong.svg')
            with self.assertRaises(AssertionError): exec(code,{})
            (folder/'wrong.svg').rename(folder/names[0])
            fake.ticks=lambda path: [(x,10) for x in (0,.1,.4,.6,.8,1)]
            with self.assertRaises(AssertionError): exec(code,{})

    def test_G7A_005_destination(self):
        code=source('docs/ux-audit/2026-10-13-implementation/collect-finish-evidence.py')
        start=code.index('    target = destination / source.name'); end=code.index('\nux =')
        body='for source in runs:\n'+code[start:end]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); src=root/'src'/'run';src.mkdir(parents=True);dest=root/'dest';dest.mkdir()
            (src/'image').write_bytes(b'right')
            manifest={'files':[{'path':'image','sha256':hashlib.sha256(b'right').hexdigest()}], 'scenario':'test','native_requested':True,'head':'head','tracked_diff_sha256':'diff','passed':True}
            (src/'manifest.json').write_text(json.dumps(manifest))
            def run(): exec(body,dict(runs=[src],destination=dest,manifest=manifest,hashlib=hashlib,shutil=shutil,audit=root,rows=[]))
            run();(dest/'run/image').write_bytes(b'wrong')
            with self.assertRaises(AssertionError): run()

    def test_G7A_004_mutant_preimages(self):
        helper=ROOT/'artifacts/statistical-mutants/mutate.py'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); subprocess.run(['git','init','-q',str(root)],check=True)
            p=root/'owned.txt';p.write_bytes(b'original\n'); other=root/'unrelated';other.write_bytes(b'dirty')
            diff=root/'change.patch';diff.write_text('diff --git a/owned.txt b/owned.txt\n--- a/owned.txt\n+++ b/owned.txt\n@@ -1 +1 @@\n-original\n+mutant\n', newline='\n')
            if BASELINE:
                (root/'artifacts/statistical-mutants').mkdir(parents=True)
                (root/'artifacts/statistical-mutants/env.sh').write_text('')
                (root/'tests/mutants').mkdir(parents=True)
                (root/'tests/mutants/ci-z-instead-of-t.patch').write_bytes(diff.read_bytes())
                driver=root/'prove.sh';driver.write_text(source('artifacts/statistical-mutants/prove.sh'),newline='\n')
                bash='C:/Program Files/Git/bin/bash.exe' if sys.platform=='win32' else 'bash'
                result=subprocess.run([bash,'-c','Rscript() { return 0; }; export -f Rscript; bash prove.sh'],cwd=root,capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(p.read_bytes(),b'original\n')
                return
            for exit_code in (0,7):
                result=subprocess.run([sys.executable,str(helper),str(diff),sys.executable,'-c',f'from pathlib import Path; assert Path("owned.txt").read_text()=="mutant\\n"; raise SystemExit({exit_code})'],cwd=root)
                self.assertEqual(result.returncode,exit_code);self.assertEqual(p.read_bytes(),b'original\n');self.assertEqual(other.read_bytes(),b'dirty')

    def test_G7B_005_before_preflight(self):
        path=ROOT/'docs/ux-audit/2026-10-16-round6/reviewer_preflight.py'
        if BASELINE:
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory).resolve();here=root/'docs/ux-audit/2026-10-16-round6';here.mkdir(parents=True)
                env=root/'docs/ux-audit/2026-10-14-round3/ENV.sh';env.parent.mkdir();env.write_text('')
                driver=here/'REVIEWER-REPRODUCE.sh';driver.write_text(source('docs/ux-audit/2026-10-16-round6/REVIEWER-REPRODUCE.sh'),newline='\n')
                bash='C:/Program Files/Git/bin/bash.exe' if sys.platform=='win32' else 'bash'
                result=subprocess.run([bash,'-c','uv() { echo "$*" >> probe.log; return 42; }; export -f uv; bash docs/ux-audit/2026-10-16-round6/REVIEWER-REPRODUCE.sh'],cwd=root,capture_output=True,text=True)
                self.assertEqual(result.returncode,42)
                self.assertIn('reviewer_preflight.py',(root/'probe.log').read_text())
            return
        spec=importlib.util.spec_from_file_location('preflight',path); module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            here=Path(directory);raw=here/'raw';raw.mkdir();evidence=here/'evidence';evidence.mkdir()
            with self.assertRaises(FileNotFoundError):module.preflight(here)
            (raw/'reviewer-groups-before.json').write_text(json.dumps({'exit_code':0,'log':'before.log'}))
            (raw/'before.log').write_text(f'Evidence: {evidence}\n')
            (evidence/'manifest.json').write_text(json.dumps({'passed':True,'native_requested':True}))
            (evidence/'steps.jsonl').write_text(json.dumps({'captures':['before.png']})+'\n')
            with self.assertRaises(ValueError):module.preflight(here)
            (evidence/'before.png').write_bytes(b'owned fixture image')
            self.assertEqual(module.preflight(here),evidence)

    def test_G7B_006_gallery_relocation(self):
        page=source('docs/ux-audit/2026-10-16-round6/reviewer-gallery.html')
        paths=re.findall(r'"([^"\n]*reviewer-screenshots/[^"\n]*\.png)"',page)
        self.assertEqual(len(paths),51)
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory);shutil.copytree(ROOT/'docs/ux-audit/2026-10-16-round6/reviewer-screenshots',target/'reviewer-screenshots')
            for name in paths:
                self.assertFalse(Path(name).is_absolute(),name)
                self.assertTrue((target/name).is_file(),name)
                self.assertEqual(hashlib.sha256((target/name).read_bytes()).digest(),hashlib.sha256((ROOT/'docs/ux-audit/2026-10-16-round6'/name).read_bytes()).digest())

    def test_G7A_003_replay_identity(self):
        code=source('artifacts/qa-r1/shard-repair/replay.py')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();here=root/'artifacts/qa-r1/shard-repair';here.mkdir(parents=True)
            (root/'sample_projects').mkdir();(root/'sample_projects/input.rcms').write_bytes(b'input')
            (here/'run_scenario.py').write_text('driver')
            calls=[]
            def run(command, **kwargs):
                calls.append(command);kwargs['stdout'].write('Evidence: fixture\n')
                return subprocess.CompletedProcess(command,0)
            revision=['revision-a']
            def output(command,**kwargs):return revision[0]+'\n' if 'rev-parse' in command else b'diff'
            def execute(args):
                with patch.object(sys,'argv',args),patch('subprocess.run',side_effect=run),patch('subprocess.check_output',side_effect=output),patch('platform.platform',return_value='Windows fixture'):
                    with self.assertRaises(SystemExit) as result:exec(code,{'__file__':str(here/'replay.py')})
                    self.assertEqual(result.exception.code,False)
            execute(['replay']);first=len(calls);self.assertGreater(first,0)
            execute(['replay']);self.assertEqual(len(calls),first*2)
            execute(['replay','--resume']);self.assertEqual(len(calls),first*2)
            revision[0]='revision-b'
            with self.assertRaises(AssertionError):execute(['replay','--resume'])

    def test_G7A_006_aggregate_receipts(self):
        from types import ModuleType
        fake=ModuleType('scripts.verify_rcms');fake.SCENARIOS=['one','two']
        code=source('docs/ux-audit/2026-10-14-round3-reaudit/run_all.py')
        with tempfile.TemporaryDirectory() as directory,patch.dict(sys.modules,{'scripts.verify_rcms':fake}):
            here=Path(directory)/'docs/ux-audit/audit';(here/'raw').mkdir(parents=True)
            failure=[False]
            def run(command,**kwargs):
                label=command[2];status=int(failure[0] and label=='native-one')
                (here/'raw'/(label+'.json')).write_text(json.dumps({'label':label,'exit_code':status}))
                return subprocess.CompletedProcess(command,status)
            with patch('subprocess.run',side_effect=run):
                for failed in (False,True):
                    failure[0]=failed
                    with self.assertRaises(SystemExit) as result:exec(code,{'__file__':str(here/'run_all.py')})
                    self.assertEqual(result.exception.code,int(failed))
                    self.assertEqual(len(json.loads((here/'RUNS.json').read_text())),2)

    def test_G7B_001_menu_schema(self):
        tree=ast.parse(source('docs/ux-audit/2026-10-15-round4-reaudit/native_options_remaining.py'))
        assignment=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='menu_rows' for t in n.targets))
        with tempfile.TemporaryDirectory() as directory:
            here=Path(directory);(here/'OPTIONS.json').write_text('[{"controls":[],"path":"screenshot.png"}]')
            ns={'HERE':here,'json':json};exec(compile(ast.Module(body=[assignment],type_ignores=[]),'menu','exec'),ns)
            ns['menu_rows'].append({'title':'Analysis','actions':[]})
            self.assertEqual(ns['menu_rows'],[{'title':'Analysis','actions':[]}])

    def test_G7B_002_owned_window(self):
        for path in ('docs/ux-audit/2026-10-16-round5-reaudit/native_editor.py','docs/ux-audit/2026-10-15-round4-reaudit/native_shell.py'):
            tree=ast.parse(source(path));nodes=list(ast.walk(tree))
            statement=next(n for n in nodes if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ids' for t in n.targets) and 'xedit' in ast.unparse(n) ) if BASELINE else next(n for n in nodes if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ids' for t in n.targets) and 'hex' in ast.unparse(n))
            # Execute the actual command + parse + cardinality assertion with a foreign desktop window.
            parent=next(n for n in nodes if hasattr(n,'body') and isinstance(n.body,list) and statement in n.body)
            i=parent.body.index(statement);segment=parent.body[i-1:i+2]
            from types import SimpleNamespace
            def output(command,**kwargs):
                self.assertEqual(command,['xdotool','search','--onlyvisible','--pid','42'])
                return '123\n'
            ns={'subprocess':subprocess,'re':re,'editor':SimpleNamespace(pid=42)}
            with patch('subprocess.check_output',side_effect=output):exec(compile(ast.Module(body=segment,type_ignores=[]),'window','exec'),ns)
            self.assertEqual(ns['ids'],['0x7b'])

    def test_G7B_003_version_output(self):
        code=source('docs/ux-audit/2026-10-16-round5/review1_bcg_source.py');node=ast.parse(code).body[-1]
        from contextlib import redirect_stdout
        stream=io.StringIO()
        with redirect_stdout(stream):exec(compile(ast.Module(body=[node],type_ignores=[]),'version','exec'),{'source':{'package':'different-version'}})
        self.assertIn('different-version',stream.getvalue());self.assertNotIn('1.6-0',stream.getvalue())

    def test_G7A_001_curve_mismatch(self):
        import numpy as np
        from PIL import Image, ImageDraw
        import textwrap
        code=source('artifacts/batch7-windows/check_windows.py')
        start=code.index("  if best[0] and case == 'continuous-meta-regression':") if BASELINE else code.index('  if best[0]:')
        end=code.index("(HERE/'windows-data-marks.json')")
        body='for _case in [1]:\n'+textwrap.indent(textwrap.dedent(code[start:end]),' ')
        image=Image.new('RGB',(400,400),'white');draw=ImageDraw.Draw(image)
        for y in range(40,300,40):draw.ellipse((100,y,110,y+10),fill=(170,170,220))
        class Marks:
            def __getitem__(self,key):return np.array([[1,1],[2,2]])
        ns=dict(np=np,old=image,new=image,case='continuous-meta-regression',best=(.2,0,0,0),oa=(100,10,200),na=(100,10,200),rows=[],a=Marks(),aa=np.array([[1,1],[2,2]]),mb=None,matched=lambda *args:np.array([False,False]),roi=(0,1,0,1))
        with self.assertRaises(AssertionError):exec(body,ns)

if __name__ == '__main__': unittest.main(verbosity=2)
