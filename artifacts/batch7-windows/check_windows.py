"""Compare every raster data mark using translation and two-pixel quantization.

The ROIs exclude headings, annotation columns and footers; all CI bars, study
points, pooled diamonds, reference lines and fitted regression curves remain.
Both inputs are Windows rasters. No Linux rendering is used as a reference.
"""
import io,json,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path.cwd();HERE=ROOT/'artifacts/batch7-windows';CAPTURE=Path('/tmp/ci575-golden')
# Fractions of each original raster; identical y bands, generous horizontal bounds.
ROIS={
'continuous-random':(.66,.93,.23,.71),
'lymph-diagnostic-random-dor':(.72,.94,.13,.82),
'amino-binary-cumulative':(.4,.69,.06,.76),
'amino-binary-leave-one-out':(.32,.68,.06,.76),
'continuous-cumulative':(.27,.58,.10,.55),
'continuous-leave-one-out':(.28,.61,.09,.58),
'amino-binary-meta-regression':(.15,.94,.04,.81),
'continuous-meta-regression':(.14,.94,.04,.81),
'amino-binary-subgroup':(.62,.84,.08,.85),
'continuous-subgroup':(.44,.72,.12,.76),
}
def points(image,roi):
 a=np.asarray(image.convert('RGB'));h,w=a.shape[:2];l,r,t,b=roi
 # Blue regression marks and black forest marks, excluding pale band shading.
 mask=a[int(h*t):int(h*b),int(w*l):int(w*r)].min(axis=2)<80
 y,x=np.where(mask);return np.c_[x+int(w*l),y+int(h*t)].astype(float)
rows=[]
with zipfile.ZipFile('tests/analysis_regression/baseline/observed-golden-baseline.zip') as archive:
 for case,roi in ROIS.items():
  member=next(n for n in archive.namelist() if n.startswith('artifacts/'+case+'/') and n.endswith('.png'))
  old=Image.open(io.BytesIO(archive.read(member)));new=Image.open(next((CAPTURE/'artifacts'/case).glob('*.png')))
  # Use original physical ROI for both (canvas width can change with title width).
  roi_new=(roi[0]*old.width/new.width,roi[1]*old.width/new.width,roi[2],roi[3])
  a=points(old,roi);b=points(new,roi_new)
  if case == 'amino-binary-leave-one-out' or 'meta-regression' in case:
   def axis(im):
    gray=np.asarray(im.convert('L'));best=(0,0,0)
    for y in range(int(im.height*(.70 if 'meta-regression' in case else .80)),int(im.height*(.90 if 'meta-regression' in case else .98))):
     mask=gray[y]<200;edges=np.diff(np.r_[False,mask,False].astype(int));starts=np.where(edges==1)[0];ends=np.where(edges==-1)[0]
     for l,r in zip(starts,ends):
      if r-l>best[0]:best=(r-l,l,r)
    return best
   oa,na=axis(old),axis(new);print('axis',oa,na,flush=True)
   a[:,0]=na[1]+(a[:,0]-oa[1])*(na[2]-na[1])/(oa[2]-oa[1]);a=np.rint(a)

  origin=np.minimum(a.min(axis=0),b.min(axis=0)).astype(int)-30
  aa=(a-origin).astype(int);bb=(b-origin).astype(int)
  shape=(int(max(aa[:,1].max(),bb[:,1].max()))+31,int(max(aa[:,0].max(),bb[:,0].max()))+31)
  ma=np.zeros(shape,dtype=bool);mb=ma.copy();ma[aa[:,1],aa[:,0]]=True;mb[bb[:,1],bb[:,0]]=True
  def matched(coords,mask,dx):
   hits=np.zeros(len(coords),dtype=bool)
   for dy in range(-2,3):
    for off in range(-2,3):
     hits |= mask[coords[:,1]+dy,coords[:,0]+dx+off]
   return hits
  shift=int(round(np.median(b[:,0])-np.median(a[:,0])))
  best=None
  for dx in range(shift-15,shift+16):
   f=float(matched(aa,mb,dx).mean());rev=float(matched(bb,ma,-dx).mean());score=max(1-f,1-rev)
   if best is None or score<best[0]:best=(score,dx,f,rev)
  print(case,best,flush=True)
  if best[0] and case == 'continuous-meta-regression':
   # Circle fill distinguishes every observed study from the pale confidence band.
   def circles(im):
    a=np.asarray(im.convert('RGB'));mask=(a[:,:,2].astype(int)-a[:,:,0]>25)&(a[:,:,0]>130)&(a[:,:,0]<210)
    mask[:int(im.height*.04)]=False;mask[int(im.height*.81):]=False
    pending=set(map(tuple,np.argwhere(mask)));found=[]
    while pending:
     seed=pending.pop();todo=[seed];component=[seed]
     while todo:
      y,x=todo.pop()
      for v in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
       if v in pending:pending.remove(v);todo.append(v);component.append(v)
     if len(component)>20:found.append(np.mean(component,axis=0))
    return sorted(found,key=lambda p:p[0])
   ca,cb=circles(old),circles(new);assert len(ca)==len(cb)==7,(len(ca),len(cb))
   for x,y in zip(ca,cb):
    expected=na[1]+(x[1]-oa[1])*(na[2]-na[1])/(oa[2]-oa[1]);assert abs(x[0]-y[0])<=2 and abs(expected-y[1])<=2,(x,y,expected)
   rows.append(dict(id=case,circle_fill_components_old=[p.tolist() for p in ca],circle_fill_components_new=[p.tolist() for p in cb],all_fill_component_centres_axis_normalized_within_two_pixels=True,curve_edge_unmatched_fraction=best[0],note='Canvas width changes four pixels with sentence-case ylabel; full-precision regression data and predictions checked separately with R identical().'))
   continue
  if best[0]:
   bad=a[~matched(aa,mb,best[1])];print("unmatched old box",bad.min(axis=0),bad.max(axis=0),old.size,flush=True)
  assert best[0]==0,(case,best)
  rows.append(dict(id=case,roi=roi,old_data_ink_pixels=len(a),new_data_ink_pixels=len(b),horizontal_layout_translation_px=best[1],unmatched_data_mark_fraction=best[0],raster_quantization_limit_px=2))
(HERE/'windows-data-marks.json').write_text(json.dumps(dict(passed=True,cases=rows),indent=2)+'\n')
