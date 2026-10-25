from pathlib import Path
import sys,json,time
import numpy as np
import shapely
from shapely.geometry import shape,Point,Polygon,box,mapping
from scipy.spatial import cKDTree
B=Path(__file__).parent
sys.path.insert(0,'E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
from discover_native_turns import sha
from verify_native_turns import geometry,line_stats
from optimize_native_turns import face_constraints
SOURCE=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')
PFILE=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
FFILE=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009/preserved-field.npy')
def main():
 assert not (B/'authoring.json').exists(),'one cap candidate only'
 t=dict(np.load(SOURCE));h=t['heights'].astype(float);v=h.copy();p=np.load(PFILE);f=np.load(FFILE);pf=np.repeat(p[:,:,None],4,axis=2)
 assert sha(SOURCE)=='fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6'
 source_discovery=Path('E:/DayZ-Baltic-Build/v30-rounded-terminal-footprint-20261009/discovery.json');jobs=json.loads(source_discovery.read_text())['jobs'];jobs=[j for j in jobs if j['features'][0]!='stream_0431:0']
 fixed=np.load('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/constraints.npz')['fixed'];reports=[]
 for job in jobs:
  r0,c0,r1,c1=job['box_cells'];cx,cz=job['center'];wet=shape(job['physical_geometry']);parts=list(getattr(wet,'geoms',[wet]));targets=[];polys=[]
  for poly in parts:
   if poly.area<1:targets.append(poly);continue
   radius=min(6.,.9*shapely.maximum_inscribed_circle(poly).length)
   opened=poly.buffer(-radius,quad_segs=24).buffer(radius,quad_segs=24).intersection(poly)
   distance=shapely.hausdorff_distance(poly.boundary,opened.boundary) if not opened.is_empty else float('inf')
   accept=bool(not opened.is_empty and opened.area>=.9*poly.area and distance<=6)
   targets.append(opened if accept else poly);polys.append(dict(radius_m=radius,before_m2=poly.area,target_m2=opened.area,hausdorff_m=distance,used=accept))
  target=shapely.union_all(targets);before=geometry(h,pf,[(r,c) for r in range(r0,r1) for c in range(c0,c1) if np.isfinite(p[r,c])])
  changed=[];full_to_land=[]
  for r in range(r0+1,r1):
   for c in range(c0+1,c1):
    if fixed[r,c] or t['cls'][r,c] not in (0,5,6):continue
    xy=Point(c*6,12282-r*6);distance=xy.distance(Point(cx,cz))
    if distance>=60 or xy.distance(wet.boundary)>12:continue
    levels=[]
    for slot,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
     if np.isfinite(p[r-dr,c-dc]):levels.extend([float(p[r-dr,c-dc]),float(f[r-dr,c-dc,slot])])
    if not levels:continue
    sd=xy.distance(target.boundary)*(-1 if target.covers(xy) else 1)
    lam=max(levels);want=lam+.15*sd
    if t['cls'][r,c]==0:want=max(h[r,c],want)
    elif want>=min(levels):want=max(1.8,max(levels)+.0501,want);full_to_land.append(r*2048+c)
    else:want=min(want,min(levels)-.1001)
    w=1.
    if distance>36:
     q=(distance-36)/24;w=1-(6*q**5-15*q**4+10*q**3)
    want=h[r,c]+max(0,min(1.5,w*(want-h[r,c])))
    # Never leave a newly dry water vertex in the forbidden near-plane/freeboard band.
    if t['cls'][r,c] in (5,6) and want>=min(levels)-.1001:
     if want<max(1.8,max(levels)+.0501):want=min(want,max(h[r,c],min(levels)-.1001))
    if want>h[r,c]+1e-7:v[r,c]=np.float32(want);changed.append(r*2048+c)
  ids=np.array(changed,dtype=int);reverted=[]
  if len(ids):
   fun,jac,faces=face_constraints(ids,h)
   for _ in range(len(ids)+1):
    delta=v.ravel()[ids]-h.ravel()[ids];bad=fun(delta)<-1e-5
    if not bad.any():break
    choices=np.unique(faces[bad].ravel());choices=choices[v.ravel()[choices]!=h.ravel()[choices]]
    if not len(choices):raise AssertionError('uneditable slope regression')
    for i in choices:v.ravel()[i]=h.ravel()[i]
    reverted.extend(choices.tolist())
   assert np.min(fun(v.ravel()[ids]-h.ravel()[ids]))>=-1e-5
  cells=[(r,c) for r in range(r0,r1) for c in range(c0,c1) if np.isfinite(p[r,c])];after=geometry(v,pf,cells)
  extent=box(c0*6,12282-r1*6,c1*6,12282-r0*6)
  def measure(poly):
   b=shapely.line_merge(poly.boundary.difference(extent.boundary.buffer(.001)));lines=[l for l in getattr(b,'geoms',[b]) if l.geom_type=='LineString' and l.length>24]
   return line_stats(lines)
  a0,a1=measure(before),measure(after);retained=[int(i) for i in ids if v.ravel()[i]!=h.ravel()[i]]
  reports.append(dict(features=job['features'],box_cells=job['box_cells'],polygons=polys,changed=len(retained),ids=retained,reverted_vertices=len(set(reverted)),before=a0,after=a1,area_before_m2=before.area,area_after_m2=after.area,new_water_m2=after.difference(before).area,lost_water_m2=before.difference(after).area,target_geometry=mapping(target)))
 out={k:a.copy() for k,a in t.items()};out['heights']=v.astype(np.float32);changed=np.flatnonzero(out['heights']!=h)
 for i in changed:
  r,c=divmod(int(i),2048)
  if t['cls'][r,c] not in (5,6):continue
  levels=[]
  for slot,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
   if np.isfinite(p[r-dr,c-dc]):levels.extend([float(p[r-dr,c-dc]),float(f[r-dr,c-dc,slot])])
  if levels and out['heights'][r,c]>=max(levels)+.05009:out['cls'][r,c]=0;out['water'][r,c]=False;out['level'][r,c]=np.nan
 folder=B/'candidate'
 if folder.exists():
  # First run saved the candidate before a numpy-bool JSON serialization error.
  # The single implementation repair only reconstructs its report, never replaces it.
  saved=dict(np.load(folder/'terrain.npz'));assert set(saved)==set(out)
  assert all(np.array_equal(saved[k],out[k],equal_nan=True) for k in out)
 else:
  folder.mkdir(exist_ok=False);np.savez_compressed(folder/'terrain.npz',**out)
  np.savez_compressed(B/'delta.npz',ids=changed,before=h.ravel()[changed],after=out['heights'].ravel()[changed],cls_before=t['cls'].ravel()[changed],cls_after=out['cls'].ravel()[changed])
 result=dict(status='CAP_PROFILE_CANDIDATE_REQUIRES_VALIDATION',source_sha256=sha(SOURCE),candidate_sha256=sha(folder/'terrain.npz'),changed_vertices=len(changed),class_changes=int(np.count_nonzero(t['cls']!=out['cls'])),max_raise_m=float(np.max(out['heights']-h)),reports=reports)
 (B/'authoring.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='reports'},indent=2))
 for row in reports:print(json.dumps({k:v for k,v in row.items() if k not in ['ids','target_geometry','polygons']},indent=2))
if __name__=='__main__':main()
