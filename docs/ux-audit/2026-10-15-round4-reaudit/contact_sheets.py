"""Make lossless, original-size review sheets in ignored scratch, with membership."""
from PIL import Image,ImageDraw
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent
prefix=sys.argv[1] if len(sys.argv)>1 else 'helper'
paths=sorted((HERE/'screenshots').glob(prefix+'*.png'))
rows=[]
for page in range(0,len(paths),4):
 selected=paths[page:page+4];images=[Image.open(p).convert('RGB') for p in selected]
 width=max(i.width for i in images);height=max(i.height for i in images)
 sheet=Image.new('RGB',(width*2,(height+28)*2),'#ddd');draw=ImageDraw.Draw(sheet)
 for n,(p,im) in enumerate(zip(selected,images)):
  x=n%2*width;y=n//2*(height+28);draw.text((x+5,y+5),p.name,fill='black');sheet.paste(im,(x,y+28))
 output=HERE/'raw'/f'review-{prefix}-{page//4:02d}.png';sheet.save(output)
 rows.append({'sheet':str(output.relative_to(HERE)),'members':[str(p.relative_to(HERE)) for p in selected]})
(HERE/('REVIEW-SHEETS-'+prefix+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
print(len(paths),'images in',len(rows),'sheets')
