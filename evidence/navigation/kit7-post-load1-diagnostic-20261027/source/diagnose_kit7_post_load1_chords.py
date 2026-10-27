from pathlib import Path
import json,hashlib,datetime
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');A=W/'evidence/navigation/kit7-nav12-rejected-20261027/diagnostics';D=R/'kit7-post-load1-vertex-surfaces-20261027';O=R/'kit7-post-load1-chords-20261027';O.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
budget=read(D/'budget.json');assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(budget['deadline_utc'])
surface=read(D/'result.json');native=read(A/'kit7-nav12-height-diagnostic-20261027.json');recon=read(A/'kit7-nav12-height-reconstruction-20261027.json');points={(r['x'],r['z']):r for r in surface['points']}
def weights(tri,x,z):
 a=np.array(tri)[:,[0,2]];m=np.vstack([a.T,np.ones(3)]);det=np.linalg.det(m)
 if abs(det)<1e-10:return None
 v=np.linalg.solve(m,np.array([x,z,1.]));return v if min(v)>=-1e-7 else None
fixture=[[0,0,0],[1,2,0],[0,1,1]];v=weights(fixture,.25,.25);assert np.allclose(v,[.5,.25,.25]) and abs(np.dot(v,[0,2,1])-.75)<1e-12
assert weights(fixture,2,2) is None and weights([[0,0,0],[1,0,1],[2,0,2]],0,0) is None
triangles=[]
for tile in recon['tiles']:
 for pi,p in enumerate(tile['polygons']):
  vs=p['vertices']
  for t in range(1,len(vs)-1):triangles.append((tile['tile'],pi,[vs[0],vs[t],vs[t+1]]))
rows=[]
for s in native['samples']:
 x,yn,z=s['nav'];hits=[]
 for tile,poly,tri in triangles:
  v=weights(tri,x,z)
  if v is None:continue
  y=float(np.dot(v,np.array(tri)[:,1]));corners=[]
  for a,b,c in tri:
   row=points[(a,c)];known=max(row['terrain_y'],row['roadway_y'] if row['roadway_y'] is not None else -float('inf'))
   corners.append(dict(x=a,z=c,nav_y=b,terrain_y=row['terrain_y'],roadway_y=row['roadway_y'],known_surface_y=known,nav_minus_known_surface_m=b-known))
  physical=float(np.dot(v,[c['known_surface_y'] for c in corners]));hits.append(dict(tile=tile,polygon=poly,weights=v.tolist(),nav_plane_y=y,known_surface_chord_y=physical,corners=corners))
 assert hits
 # Same geometric maximum rule as the archived height helper, independent of native Y.
 selected=max(hits,key=lambda t:t['nav_plane_y']);assert abs(selected['nav_plane_y']-yn)<1e-6
 actual=s['engine_roadway'][1];gap=actual-selected['known_surface_chord_y'];bias=selected['nav_plane_y']-selected['known_surface_chord_y']
 assert abs((gap-bias)-(actual-yn))<1e-6
 rows.append(dict(query=s['query'],index=s['index'],failed=s['excess_m']>0,native_y=yn,engine_surface_y=actual,absolute_native_error_m=abs(actual-yn),known_surface_chord_gap_m=gap,interpolated_vertex_bias_m=bias,candidate_triangles=len(hits),selected=selected))
result=dict(status='LOCAL_INTERPOLATION_DISCREPANCY_OBSERVED',acceptance_eligible=False,samples=rows,failed_samples=sum(s['failed'] for s in rows),max_reconstruction_residual_m=max(abs(s['selected']['nav_plane_y']-s['native_y']) for s in rows),inputs={str(p):sha(p) for p in [Path(__file__),D/'result.json',D/'budget.json',A/'kit7-nav12-height-diagnostic-20261027.json',A/'kit7-nav12-height-reconstruction-20261027.json']},limits=['Six archived Nav12 waypoints and their actual empirical local polygon fan; not a generic format or full mesh.','Known corner surface is max(terrain, fluvial Roadway); other object classes are not surveyed.','Engine surface at corners not probed; only six waypoint observations are native.','The numeric discrepancy is decomposed locally; generator selection mechanism and a corrective parameter remain unverified.','No RAM result, map mutation, new native run or global acceptance.'])
(O/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');(O/'completion.json').write_text(json.dumps(dict(returncode=0,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),dayz_runs=0,inputs_unchanged=all(sha(Path(p))==h for p,h in result['inputs'].items())),indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k!='selected'} for r in rows],indent=2))
