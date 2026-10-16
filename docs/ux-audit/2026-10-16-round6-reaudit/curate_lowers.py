"""Retain distinct lower matrix views; unchanged duplicate frames stay raw."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,shutil,sys
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for index in sorted(HERE.glob('MATRIX-*.json')):
 if index.stem=='MATRIX-samples' or sys.argv[1:] and index.stem not in sys.argv[1:]:continue
 receipt=HERE/'raw'/(index.stem.lower()+'.json')
 if not receipt.exists() or json.loads(receipt.read_text()).get('exit_code')!=0:continue
 rows=[]
 for row in json.loads(index.read_text()):
  src=HERE/row['path']
  if '-bottom' not in src.name:continue
  # The initial Default diagnostic run scrolled to the whole scene bottom.
  if index.stem=='MATRIX-diagnostic' and src.name.endswith('-figure-bottom.png'):continue
  if index.stem.endswith(('-revman','-bmj')) and '-report' in src.name:continue
  top=src.with_name(src.name.replace('-bottom',''))
  assert top.exists(),top
  if sha(src)==sha(top):continue
  dst=HERE/'screenshots'/src.name;shutil.copy2(src,dst)
  rows.append({**row,'path':str(dst.relative_to(HERE)),'source':str(src),'scenario':'lower-'+index.stem,'sha256':sha(src)})
 if not rows:continue
 (HERE/('SELECTED-lower-'+index.stem+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
 for offset in range(0,len(rows),4):
  canvas=Image.new('RGB',(1600,1200),'#ddd');draw=ImageDraw.Draw(canvas)
  for j,row in enumerate(rows[offset:offset+4]):
   im=Image.open(HERE/row['path']).convert('RGB');im.thumbnail((790,560));x=j%2*800;y=j//2*600
   draw.text((x+5,y+5),Path(row['path']).name,fill='black');canvas.paste(im,(x,y+30))
  canvas.save(HERE/'raw'/('inspect-lower-'+index.stem+'-'+str(offset//4).zfill(2)+'.png'))
 print(index.stem,len(rows),'distinct lower captures')
