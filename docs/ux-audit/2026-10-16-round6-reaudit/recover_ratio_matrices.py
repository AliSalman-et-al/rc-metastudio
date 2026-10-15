"""Reconcile four retained cells plus a known-wording meta-regression continuation."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
proofs=[]
for family in ('hr','irr'):
 original=json.loads((HERE/'raw'/('matrix-'+family+'.json')).read_text())
 continuation=json.loads((HERE/'raw'/('matrix-'+family+'--wording-recovery.json')).read_text())
 assert original['exit_code']==1 and continuation['exit_code']==0
 log=(HERE/'raw'/original['log']).read_text();assert 'intrcpt' in log and 'AssertionError:' in log
 before=json.loads((HERE/('MATRIX-'+family+'.json')).read_text());after=json.loads((HERE/('MATRIX-'+family+'--wording-recovery.json')).read_text())
 expected={'standard','cumulative','leave-one-out','subgroup'}
 assert {r['workflow'] for r in before}==expected
 for workflow in expected:assert family+' '+workflow+' PASSED' in log
 assert {r['workflow'] for r in after}=={'meta-regression'}
 rows=[]
 for row in before+after:
  src=HERE/row['path'];assert sha(src)==row['sha256'],src
  if '-bottom' in src.name:
   top=src.with_name(src.name.replace('-bottom',''));assert top.exists()
   if sha(top)==sha(src):continue
  dst=HERE/'screenshots'/src.name;shutil.copy2(src,dst)
  rows.append({**row,'path':str(dst.relative_to(HERE)),'source':str(src),'scenario':'MATRIX-'+family+'-recovered'})
 index=HERE/('SELECTED-MATRIX-'+family+'-recovered.json');index.write_text(json.dumps(rows,indent=2)+'\n')
 for offset in range(0,len(rows),4):
  canvas=Image.new('RGB',(1600,1200),'#ddd');draw=ImageDraw.Draw(canvas)
  for j,row in enumerate(rows[offset:offset+4]):
   im=Image.open(HERE/row['path']).convert('RGB');im.thumbnail((790,560));x=j%2*800;y=j//2*600;draw.text((x+5,y+5),Path(row['path']).name,fill='black');canvas.paste(im,(x,y+30))
  canvas.save(HERE/'raw'/('inspect-MATRIX-'+family+'-recovered-'+str(offset//4).zfill(2)+'.png'))
 proofs.append({'family':family,'original_receipt':str(Path('raw')/('matrix-'+family+'.json')),'original_exit':1,'retained_completed_workflows':sorted(expected),'continuation_receipt':str(Path('raw')/('matrix-'+family+'--wording-recovery.json')),'continuation_workflows':['meta-regression'],'known_wording_exception':'R6-08 intrcpt; original failure remains and no UX fix is claimed.','unique_cells':5,'selected_index':index.name,'selected_frames':len(rows),'original_index_sha256':sha(HERE/('MATRIX-'+family+'.json')),'continuation_index_sha256':sha(HERE/('MATRIX-'+family+'--wording-recovery.json'))})
 print(family,len(rows),'retained/recovered frames')
(HERE/'RATIO-MATRIX-RECOVERY.json').write_text(json.dumps(proofs,indent=2)+'\n')
