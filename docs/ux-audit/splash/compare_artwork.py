from PIL import Image, ImageChops, ImageStat, ImageDraw
from pathlib import Path
import json
import hashlib
import re
import runpy
r=Path('docs/ux-audit/splash')
ref=Image.open(r/'direction.png').convert('RGBA').crop((80,80,2000,1280))
art=Image.open('src/rc_metastudio/images/splash/splash@2x.png').convert('RGBA')
print(ref.size,art.size)
background=Image.new('RGBA',art.size,(30,30,30,255));background.alpha_composite(art)
diff=ImageChops.difference(ref.convert('RGB'),background.convert('RGB'))
mask=Image.new('L',art.size,255);d=ImageDraw.Draw(mask)
# Runtime text is deliberately absent; the reference page shadow affects only the edge.
for box in [(110,398,802,442),(110,530,802,620),(110,702,802,746),(110,922,802,1010)]:d.rectangle(box,fill=0)
d.rectangle((0,0,1919,1199),outline=0,width=3)
stat=ImageStat.Stat(diff,mask)
masked=Image.composite(diff,Image.new('RGB',diff.size),mask)
masked.save(r/'evidence/artwork-diff.png')
values=list(masked.get_flattened_data()); count=sum(any(p) for p in values)
(r/'evidence/artwork-diff.json').write_text(json.dumps({'command':'uv run python docs/ux-audit/splash/compare_artwork.py','reference_crop':[80,80,2000,1280],'artwork_size':art.size,'excluded':'runtime text rectangles and 3 physical pixel border affected by presentation shadow','mean_absolute_RGB':stat.mean,'different_pixels':count,'compared_pixels':sum(v>0 for v in mask.get_flattened_data()),'max_channel_difference':max(max(p) for p in values)},indent=2))
page = runpy.run_path('scripts/build_splash_artwork.py')['html']
original = (r / 'direction.html').read_text(encoding='utf-8')
svg = re.search(r'<svg.*?</svg>', page, re.S).group()
approved_svg = re.search(r'<svg.*?</svg>', original, re.S).group()
assert svg == approved_svg
report = r / 'evidence/artwork-diff.json'
metrics = json.loads(report.read_text())
metrics.update(svg_identical_to_approved_html=True, svg_sha256=hashlib.sha256(svg.encode()).hexdigest())
report.write_text(json.dumps(metrics, indent=2))
print(stat.mean,count,max(max(p) for p in values))
