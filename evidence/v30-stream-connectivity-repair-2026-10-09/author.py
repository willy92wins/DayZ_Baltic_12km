from pathlib import Path
import json,sys,hashlib,heapq
import numpy as np
import shapely
from shapely.geometry import shape,Point,LineString
B=Path(__file__).parent;C=Path('E:/DayZ-Baltic-Build/v30-hydro-design-census-20261009')
sys.path.insert(0,str(C));from census import SOURCE,PFILE,FFILE,DESIGN,sample,sha
sys.path.insert(0,'E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009');from optimize_native_turns import face_constraints
def main():
 assert not (B/'authoring.json').exists(),'one proposal only'
 t=dict(np.load(SOURCE));h=t['heights'].astype(float);candidate=h.copy();p=np.load(PFILE);f=np.load(FFILE)
 assert sha(SOURCE)=='fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6'
 gaps=json.loads((C/'attribution.json').read_text())['unattributed'];gaps=[g for g in gaps if g['id'] in ('stream_0094','stream_0264')];assert len(gaps)==2
 profiles=np.load(DESIGN/'profiles.npz');features={a['properties']['id']:a for a in json.loads((DESIGN/'streams_candidates.geojson').read_text())['features']}
 fixed=t['reserve']|t['platform']|t['narva']|t['beach']|np.isin(t['cls'],[1,2,3,4,7]);reports=[];allpath=[];allids=[]
 for gap in gaps:
  profile=profiles[gap['id']];s=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(profile[:,1:3],axis=0),axis=1))]
  lo=max(0,gap['start_s']-18);hi=min(s[-1],gap['end_s']+18);ss=np.linspace(lo,hi,max(2,int((hi-lo)*4)+1));q=np.c_[np.interp(ss,s,profile[:,1]),np.interp(ss,s,profile[:,2])]
  geom=shape(features[gap['id']]['geometry']).buffer(6);line=LineString(q)
  c0=max(1,int(np.floor(q[:,0].min()/6))-3);c1=min(2046,int(np.ceil(q[:,0].max()/6))+3);r0=max(1,int(np.floor((12282-q[:,1].max())/6))-3);r1=min(2046,int(np.ceil((12282-q[:,1].min())/6))+3)
  nodes={};forbidden=0
  for r in range(r0,r1+1):
   for c in range(c0,c1+1):
    pt=Point(c*6,12282-r*6)
    if fixed[r,c] or not geom.covers(pt):continue
    water=[]
    for slot,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
     rr,cc=r-dr,c-dc
     if np.isfinite(p[rr,cc]):water.extend([float(p[rr,cc]),float(f[rr,cc,slot])])
    if not water:continue
    target=min(h[r,c],min(water)-.1501)
    if target<1 or h[r,c]-target>1.5:forbidden+=1;continue
    nodes[(r,c)]=dict(target=target,cut=h[r,c]-target,dist=line.distance(pt),wet=h[r,c]<min(water)-.10,level=min(water))
  anchors=[]
  for point in (q[0],q[-1]):
   eligible=[rc for rc,v in nodes.items() if v['wet'] and np.linalg.norm(np.array([rc[1]*6,12282-rc[0]*6])-point)<12]
   if not eligible:raise AssertionError((gap['id'],'no wet anchor'))
   anchors.append(min(eligible,key=lambda rc:np.linalg.norm(np.array([rc[1]*6,12282-rc[0]*6])-point)))
  start,end=anchors;dist={start:0.};prev={};queue=[(0.,start)]
  while queue:
   cost,cur=heapq.heappop(queue)
   if cost!=dist[cur]:continue
   if cur==end:break
   for dr,dc in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1)):
    nxt=(cur[0]+dr,cur[1]+dc)
    if nxt not in nodes:continue
    # A real edge must also have a water plane on at least one incident triangle/cell.
    v=nodes[nxt];step=np.hypot(dr,dc)*(1+16*v['cut']**2+.1*v['dist']**2);new=cost+step
    if new<dist.get(nxt,float('inf')):dist[nxt]=new;prev[nxt]=cur;heapq.heappush(queue,(new,nxt))
  if end not in dist:raise AssertionError((gap['id'],'no permitted native edge route'))
  route=[end]
  while route[-1]!=start:route.append(prev[route[-1]])
  route=route[::-1];ids=np.array([r*2048+c for r,c in route],dtype=int)
  for r,c in route:candidate[r,c]=nodes[(r,c)]['target']
  changed=np.flatnonzero(candidate!=h);fn,jac,faces=face_constraints(changed,h);delta=candidate.ravel()[changed]-h.ravel()[changed]
  slope_ok=bool(np.min(fn(delta))>=-1e-5)
  reports.append(dict(id=gap['id'],gap=gap,box_cells=[r0,c0,r1,c1],anchors=[list(start),list(end)],route=[list(rc) for rc in route],path_cost=dist[end],variables=len(nodes),forbidden=forbidden,slope_gate=slope_ok,changed_vertices=int(np.count_nonzero(candidate.ravel()[ids]!=h.ravel()[ids])),changed_old_land=[int(i) for i in ids if t['cls'].ravel()[i]==0 and candidate.ravel()[i]!=h.ravel()[i]],target_levels=[nodes[rc]['level'] for rc in route]))
  allpath.extend(route);allids.extend(ids.tolist())
 # Float32 is authoritative; no classification edits hidden inside the terrain author.
 out={k:v.copy() for k,v in t.items()};out['heights']=candidate.astype(np.float32)
 for report in reports:
  for rc,level in zip(report['route'],report['target_levels']):
   r,c=rc
   if out['cls'][r,c]==0 and out['heights'][r,c]!=h[r,c]:out['cls'][r,c]=6;out['water'][r,c]=True;out['level'][r,c]=level
 ids=np.flatnonzero(out['heights']!=h);folder=B/'candidate';folder.mkdir(exist_ok=False);np.savez_compressed(folder/'terrain.npz',**out)
 np.savez_compressed(B/'delta.npz',ids=ids,before=h.ravel()[ids],after=out['heights'].ravel()[ids],cls_before=t['cls'].ravel()[ids],cls_after=out['cls'].ravel()[ids])
 result=dict(status='CANDIDATE_REQUIRES_CONSUMER',source_sha256=sha(SOURCE),candidate_sha256=sha(folder/'terrain.npz'),physical_plane_sha256=sha(PFILE),visible_field_sha256=sha(FFILE),changed_vertices=len(ids),maximum_lower_m=float(np.max(h-out['heights'])),class_changes=int(np.count_nonzero(t['cls']!=out['cls'])),reports=reports)
 (B/'authoring.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
