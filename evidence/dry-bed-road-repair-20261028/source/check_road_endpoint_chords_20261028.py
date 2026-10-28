from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
import shapely
from shapely import LineString
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sp=importlib.util.spec_from_file_location('profiles',W/'tools/quality/pilot_bank_profiles_ev112.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p)
geom=R/'road-bed-water-discovery-20261028/geometry.json';source=R/'pilot-bank-constraint-census-20261028/sites/kit-118.npz';hp=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz'
road=shapely.from_geojson(json.loads(geom.read_bytes())['road']);h=np.load(hp)['heights'].astype(float);grid=np.load(source)['grid'];out=[]
for row in (0,8,len(grid)-9,len(grid)-1):
 for col,(a,b) in enumerate(zip(grid[row],grid[row,1:])):
  aa,bb=a[[0,2]],b[[0,2]];line=LineString([aa,bb]);hit=line.intersection(road)
  if hit.is_empty:continue
  for part in shapely.get_parts(hit):
   coords=np.asarray(part.coords);ts=[line.project(shapely.Point(z))/line.length for z in coords];lo,hi=min(ts),max(ts)
   all_t=sorted(set([lo,hi]+[float(t) for t in p.cuts(aa,bb,12282.) if lo<t<hi]))
   points=aa+(bb-aa)*np.asarray(all_t)[:,None];by=a[1]+(b[1]-a[1])*np.asarray(all_t);diff=by-p.native(h,points)
   out.append(dict(row=row,col=col,t=all_t,points=points.tolist(),difference=diff.tolist(),max_B_H=float(diff.max())))
result=dict(status='FIXED_CHORD_DISCRIMINATOR',maximum=max(x['max_B_H'] for x in out),positive=[x for x in out if x['max_B_H']>1e-9],segments=len(out),pins={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (Path(__file__),geom,source,hp)})
target=R/'road-endpoint-chords-20261028.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(maximum=result['maximum'],positive_segments=len(result['positive']),segments=len(out))))
