"""Retain primary matrix pairs for visual review; incidental frames stay raw."""
from pathlib import Path
import json,shutil,hashlib
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
for index in sorted(HERE.glob('MATRIX-*.json')):
 if index.name=='MATRIX-samples.json':continue
 rows=[]
 for r in json.loads(index.read_text()):
  src=HERE/r['path'];name=src.name
  if '-bottom' in name:continue
  dst=HERE/'screenshots'/name;shutil.copy2(src,dst)
  rows.append({**r,'path':str(dst.relative_to(HERE)),'source':str(src),'scenario':index.stem,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
 if not rows:continue
 (HERE/('SELECTED-'+index.stem+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
 for offset in range(0,len(rows),4):
  canvas=Image.new('RGB',(1600,1200),'#ddd');draw=ImageDraw.Draw(canvas)
  for j,r in enumerate(rows[offset:offset+4]):
   im=Image.open(HERE/r['path']).convert('RGB');im.thumbnail((790,560));x=j%2*800;y=j//2*600
   draw.text((x+5,y+5),str(offset+j)+': '+Path(r['path']).name,fill='black');canvas.paste(im,(x,y+30))
  canvas.save(HERE/'raw'/('inspect-'+index.stem+'-'+str(offset//4).zfill(2)+'.png'))
 print(index.stem,len(rows))
