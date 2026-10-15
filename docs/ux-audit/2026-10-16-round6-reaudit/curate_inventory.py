"""Copy completed native screen inventories and build inspection sheets."""
from pathlib import Path
import hashlib,json,shutil,sys
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
receipts={'EDITOR-INVENTORY':'native-editor-inventory','DESIGN':'native_design','SHELL':'native_shell','OPTIONS':'native_options','OPTIONS-REMAINDER':'native_options_remaining','CONTROLS':'native-controls','MATRIX-samples':'native-samples','GUARD-KEYBOARD':'native-guard-keyboard'}
for group in sys.argv[1:]:
 index=HERE/(group+'.json')
 receipt=HERE/'raw'/(receipts[group]+'.json')
 assert json.loads(receipt.read_text())['exit_code']==0,receipt
 data=json.loads(index.read_text())
 if isinstance(data,dict):data=data.get('screenshots',data.get('rows',[]))
 if group=='OPTIONS-REMAINDER':data=data[len(json.loads((HERE/'OPTIONS.json').read_text())):]
 rows=[]
 for r in data:
  if 'path' not in r:continue
  src=HERE/r['path'];dst=HERE/'screenshots'/src.name
  shutil.copy2(src,dst)
  rows.append({**r,'path':str(dst.relative_to(HERE)),'source':str(src),'scenario':group,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
 assert rows,group
 (HERE/('SELECTED-'+group+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
 for offset in range(0,len(rows),4):
  canvas=Image.new('RGB',(1600,1200),'#ddd');draw=ImageDraw.Draw(canvas)
  for j,r in enumerate(rows[offset:offset+4]):
   im=Image.open(HERE/r['path']).convert('RGB');im.thumbnail((790,560));x=j%2*800;y=j//2*600
   draw.text((x+5,y+5),str(offset+j)+': '+Path(r['path']).name,fill='black');canvas.paste(im,(x,y+30))
  canvas.save(HERE/'raw'/('inspect-'+group+'-'+str(offset//4).zfill(2)+'.png'))
 print(group,len(rows))
