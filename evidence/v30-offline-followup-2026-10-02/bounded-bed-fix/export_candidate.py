"""Export the accepted offline heights and measure the local shoreline effect."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import rasterio
R=Path('P:/DayZ_Baltic_12km_dev');E=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tools/terrain'))
from v30_common import cell_planes,tri_sample
from audit_fairway_triangles_v30 import sha,save

report=json.loads((E/'candidate.json').read_text())
path=Path(report['file']);assert sha(path)==report['sha256']
old=np.load(R/'tests/terrain_v30/terrain_v30.npz');new=np.load(path)
a=old['heights'].astype(float);b=new['heights'].astype(float)
assert json.loads((E/'terrain-gates.json').read_text())['status']=='PASS'
assert json.loads((E/'road-gates.json').read_text())['status']=='PASS'
asc=path.parent/'baltic_terrain_v30_fairway_candidate.asc'
with asc.open('x',encoding='ascii',newline='\n') as f:
 f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
 np.savetxt(f,new['heights'],fmt='%.9g')
with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),new['heights'])
planes=cell_planes(old['cls'],old['level'].astype(float))
changed=np.argwhere(a!=b);cells=set()
for rr,cc in changed:
 for dr in (-1,0):
  for dc in (-1,0):
   r,c=int(rr+dr),int(cc+dc)
   if 0<=r<2047 and 0<=c<2047:cells.add((r,c))
shifts=[]
for r,c in cells:
 lv=planes[r,c] if np.isfinite(planes[r,c]) else .5
 corners=[(r,c),(r,c+1),(r+1,c),(r+1,c+1)]
 for triangle in [(0,1,3),(0,2,3)]:
  for u,v in zip(triangle,triangle[1:]+triangle[:1]):
   p,q=corners[u],corners[v]
   if (a[p]-lv)*(a[q]-lv)>=0:continue
   assert (b[p]-lv)*(b[q]-lv)<0
   f0=(lv-a[p])/(a[q]-a[p]);f1=(lv-b[p])/(b[q]-b[p])
   shifts.append(float(abs(f1-f0)*6*np.hypot(p[0]-q[0],p[1]-q[1])))
g0=json.loads((R/'evidence/v30-resume-2026-10-02/terrain-gate.json').read_text())
g1=json.loads((E/'terrain-gates.json').read_text())
out=dict(status='ASC_ROUNDTRIP_PASS_OFFLINE_ONLY',path=str(asc),sha256=sha(asc),bytes=asc.stat().st_size,
 heights_sha256=hashlib.sha256(new['heights'].astype('<f4').tobytes()).hexdigest(),
 changed_vertices=int(len(changed)),affected_cells=len(cells),
 shoreline_crossings_checked=len(shifts),max_nominal_waterline_shift_m=max(shifts,default=0),
 shore_triangles_over_35_before=g0['slopes']['shore_triangles_over_35'],
 shore_triangles_over_35_after=g1['slopes']['shore_triangles_over_35'],
 scope='Dry vertices and masks unchanged. Submerged interpolation changes the nominal local waterline; not a render or wave test.')
save(E/'export.json',out);print(json.dumps(out,indent=2))

# Render separately through the actual extremum, including a bend corner.
import runpy
runpy.run_path(str(E/'render_profile.py'),run_name='__main__')
