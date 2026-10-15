"""Retain tracked/reviewed screenshots; archive incidental frames with a hash inventory."""
from pathlib import Path
import subprocess,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
tracked=set(subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines())
archive=HERE/'raw/uncurated';archive.mkdir(exist_ok=True);mapping={};rows=[]
for p in sorted((HERE/'screenshots').glob('*.png')):
 if str(p.relative_to(ROOT)) in tracked:continue
 target=archive/p.name
 if target.exists() and target.read_bytes()!=p.read_bytes():target=archive/(p.stem+'-'+hashlib.sha256(p.read_bytes()).hexdigest()[:8]+p.suffix)
 old=str(p.relative_to(HERE));new=str(target.relative_to(HERE));mapping[old]=new
 rows.append({'original_path':old,'retained_path':new,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'incidental execution frame, not curated visual acceptance'})
 p.replace(target)
def rewrite(obj):
 if isinstance(obj,str):return mapping.get(obj,obj)
 if isinstance(obj,list):return [rewrite(v) for v in obj]
 if isinstance(obj,dict):return {k:rewrite(v) for k,v in obj.items()}
 return obj
for p in HERE.glob('*.json'):
 if p.name in ('EVIDENCE.json','CURATION.json'):continue
 data=json.loads(p.read_text());updated=rewrite(data)
 if updated!=data:p.write_text(json.dumps(updated,indent=2,ensure_ascii=False)+'\n')
(HERE/'CURATION.json').write_text(json.dumps({'policy':'Only visually reviewed selected frames are curated. Original transient captures remain ignored, without claiming aesthetic inspection.','archived':rows},indent=2)+'\n')
print('archived',len(rows))
