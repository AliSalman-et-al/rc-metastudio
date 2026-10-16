from pathlib import Path
from PIL import Image,ImageDraw
import sys,json
p=Path(__file__).resolve().parent
family=sys.argv[1]
paths=[p/'screenshots'/f'matrix-{family}-{workflow}-{kind}.png' for workflow in ('standard','cumulative','leave-one-out','subgroup','meta-regression') for kind in ('figure','report')]
assert all(f.exists() for f in paths)
rows=[]
for i in range(0,len(paths),2):
 images=[Image.open(f).convert('RGB') for f in paths[i:i+2]]
 sheet=Image.new('RGB',(max(x.width for x in images),sum(x.height+28 for x in images)),'#ddd');d=ImageDraw.Draw(sheet);y=0
 for f,im in zip(paths[i:i+2],images):d.text((5,y+5),f.name,fill='black');sheet.paste(im,(0,y+28));y+=im.height+28
 out=p/'raw'/f'pair-{family}-{i//2}.png';sheet.save(out);rows.append({'sheet':str(out.relative_to(p)),'members':[str(f.relative_to(p)) for f in paths[i:i+2]]})
(p/f'REVIEW-PAIRS-{family}.json').write_text(json.dumps(rows,indent=2)+'\n')
