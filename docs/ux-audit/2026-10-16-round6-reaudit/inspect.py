"""Build indexed inspection sheets from retained native helper screenshots."""
import json,sys,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
HERE=Path(__file__).resolve().parent
scenario=sys.argv[1]
log=HERE/'raw'/('helper-'+scenario+'.log')
evidence=Path(next(x.removeprefix('Evidence: ') for x in log.read_text().splitlines() if x.startswith('Evidence: ')))
actions=sys.argv[2:]
items=[]
for line in (evidence/'steps.jsonl').read_text().splitlines():
 step=json.loads(line)
 if actions and step['action'] not in actions:continue
 for capture in step.get('captures',[]):
  source=evidence/capture
  name=scenario+'-'+capture
  dest=HERE/'screenshots'/name
  shutil.copy2(source,dest)
  items.append({'path':str(dest.relative_to(HERE)),'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'action':step['action'],'step':step['step'],'scenario':scenario})
(HERE/('SELECTED-'+scenario+'.json')).write_text(json.dumps(items,indent=2)+'\n')
for offset in range(0,len(items),4):
 canvas=Image.new('RGB',(1600,1200),'#ddd');draw=ImageDraw.Draw(canvas)
 for j,item in enumerate(items[offset:offset+4]):
  im=Image.open(HERE/item['path']).convert('RGB');im.thumbnail((790,560))
  x=(j%2)*800;y=(j//2)*600
  draw.text((x+5,y+5),str(offset+j)+': '+Path(item['path']).name[:90],fill='black')
  canvas.paste(im,(x,y+30))
 canvas.save(HERE/'raw'/f'inspect-{scenario}-{offset//4:02}.png')
print(len(items),evidence)
