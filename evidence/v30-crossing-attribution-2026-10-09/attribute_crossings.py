"""Attribute exact dry stations to read-only builder replay, without declaring them fixed."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
import shapely
from scipy.spatial import cKDTree
B=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
R=Path('E:/DayZ-Baltic-Build');V=R/'v30-v11';C=R/'v30-hydro-design-census-20261009'
sys.path[:0]=[str(C),str(W/'tools/terrain')]
from census import sample,SOURCE,PFILE,FFILE
from verify_roads_v30 import road_chains
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 replay=json.loads((B/'replay.json').read_text());assert replay['status']=='EXACT_BUILDER_REPLAY'
 state=dict(np.load(B/'before-road-cut.npz'));removed=state['keep_ground'];rr,cc=np.nonzero(removed);tree=cKDTree(np.c_[cc*6,12282-rr*6])
 roadlines=np.array([shapely.LineString(q) for q in road_chains() if len(q)>=2],object);roadtree=shapely.STRtree(roadlines)
 reference=np.load(V/'terrain_v30/water_v30.npz');current=np.load(SOURCE);p=np.load(PFILE);f=np.load(FFILE);profiles=np.load(V/'design/profiles.npz');data=json.loads((C/'exact-sections.json').read_text());rows=[]
 for alarm in data['rows']:
  if alarm['status']!='EXACT_DRY_CONFIRMED':continue
  gap=alarm['original_gap'];a=profiles[gap['id']];station=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(a[:,1:3],axis=0),axis=1))]
  ss=np.arange(max(station[0],gap['start_s']-2),min(station[-1],gap['end_s']+2)+.01,.25);assert len(ss)==alarm['sections']
  dry=np.zeros(len(ss),bool)
  for start,end,length in alarm['physical_dry_intervals']:dry[start:end+1]=True
  q=np.c_[np.interp(ss[dry],station,a[:,1]),np.interp(ss[dry],station,a[:,2])]
  h,depth,vdepth,r,c=sample(current['heights'],p,f,q[:,0],q[:,1]);assert np.all(~np.isfinite(depth)|(depth<=.011))
  fc=q[:,0]/6-c;fr=(12282-q[:,1])/6-r;upper=fc>=fr
  a0=removed[r,c];a1=removed[r+1,c+1];a2=np.where(upper,removed[r,c+1],removed[r+1,c]);cut_support=a0|a1|a2
  current_absent=~np.isfinite(p[r,c]);dist,near=tree.query(q);nearest_road=roadtree.nearest(shapely.points(q));road_distance=shapely.distance(shapely.points(q),roadlines[nearest_road])
  exact_cut_before=[state['cls'][r,c],state['cls'][r+1,c+1],np.where(upper,state['cls'][r,c+1],state['cls'][r+1,c])]
  roadcleared=[reference['cls'][r,c],reference['cls'][r+1,c+1],np.where(upper,reference['cls'][r,c+1],reference['cls'][r+1,c])]
  # Positive mechanism: explicit water->land vertex mutation at the replay's road cut.
  mechanism=(a0&(exact_cut_before[0]>0)&(roadcleared[0]==0))|(a1&(exact_cut_before[1]>0)&(roadcleared[1]==0))|(a2&(exact_cut_before[2]>0)&(roadcleared[2]==0))
  assert np.array_equal(mechanism,cut_support)
  label='ROAD_CUT_IN_EVERY_DRY_CENTRE_TRIANGLE' if np.all(mechanism) else ('ROAD_CUT_IN_PART_OF_DRY_CENTRE_TRIANGLES' if np.any(mechanism) else 'NO_DIRECT_ROAD_CUT_VERTEX_IN_DRY_CENTRE_TRIANGLES')
  rows.append(dict(id=gap['id'],start_s=gap['start_s'],end_s=gap['end_s'],mid=gap['mid'],dry_stations=len(q),direct_cut_stations=int(mechanism.sum()),current_no_plane_stations=int(current_absent.sum()),current_plane_but_dry_stations=int((~current_absent).sum()),nearest_cut_distance_min_m=float(dist.min()),nearest_cut_distance_max_m=float(dist.max()),nearest_road_distance_max_m=float(road_distance.max()),current_ground_min_m=float(h.min()),current_ground_max_m=float(h.max()),status=label,unattributed_dry_stations=[dict(s=float(s),x=float(point[0]),z=float(point[1]),no_plane=bool(absent),nearest_cut_m=float(d)) for s,point,absent,d in zip(ss[dry][~mechanism],q[~mechanism],current_absent[~mechanism],dist[~mechanism])]))
 report=dict(status='ATTRIBUTED_SOURCE_TRANSFORM_NOT_CROSSING_ACCEPTANCE',builder_removed_vertices=int(removed.sum()),counts=dict(collections.Counter(row['status'] for row in rows)),total_dry_stations=sum(row['dry_stations'] for row in rows),direct_cut_stations=sum(row['direct_cut_stations'] for row in rows),current_no_plane_stations=sum(row['current_no_plane_stations'] for row in rows),rows=rows,inputs={str(path):sha(path) for path in (SOURCE,PFILE,FFILE,C/'exact-sections.json',B/'replay.json',B/'before-road-cut.npz',W/'tools/terrain/build_v30.py')},limits=['Direct attribution proves a replayed water-to-land vertex mutation at the road reservation, not that every dry part has the same cause.','A documented automatic cut is not user acceptance of a dry river crossing. Preserve P9/P11 and do not lower road platforms blindly.','Physical centre triangle only; exact full-width dryness is inherited from EV36.','This does not check rendering or close the reported visual water-tile seams.'])
 (B/'attribution.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['rows','inputs']},indent=2))
if __name__=='__main__':main()
