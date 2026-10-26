"""Deterministic kit7 path proposals from frozen surface geometry; no engine queries."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/terrain')]
from prepare_visual_probe_v31 import triangles,height
from streambed_kit_v31 import tri_h
D=R/'kit7-nav-route-discovery-20261026';D.mkdir(exist_ok=False)
pilot=R/'river-kit7-contact-only-20261026';surface=pilot/'kit-7-surfaces.npz';terrain=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
paths=[Path(__file__),surface,terrain,pilot/'author-report.json',pilot/'records.json',R/'patch-nav-f45/reference.json',W/'tools/water/prepare_visual_probe_v31.py',W/'tools/water/streambed_kit_v31.py']
inputs={str(p):sha(p) for p in paths}
assert inputs[str(terrain)]=='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'
data=np.load(surface);bed=data['bed'];station=data['station'];axis=data['axis'];H=np.load(terrain)['heights'];author=read(pilot/'author-report.json')
qs=np.unique(np.r_[np.arange(-18,19,dtype=float),-2.25,2.25]);assert len(qs)==bed.shape[1]
columns={side:int(np.flatnonzero(qs==offset)[0]) for side,offset in [('left',-6),('right',6)]}
queries=[];screen=[]
def at(st,side):
 j=columns[side];return np.array([np.interp(st,station,bed[:,j,d]) for d in range(3)])
def add(name,start,stop,side,models,kind):
 if not 0<=start<stop<=station[-1]:raise ValueError('Invalid station interval')
 ts=np.linspace(start,stop,int(np.ceil((stop-start)/.5))+1)
 requested=np.stack([at(t,side) for t in ts])
 lo=max(0,int(np.searchsorted(station,start))-2);hi=min(len(station),int(np.searchsorted(station,stop))+3)
 bedtris=triangles(bed[lo:hi]);wettris=triangles(data['water'][lo:hi])
 profile=[]
 for t,p in zip(ts,requested):
  by=height(bedtris,p[[0,2]]);wy=height(wettris,p[[0,2]]);ground=float(tri_h(H,p[0],p[2]))
  assert by is not None
  profile.append(dict(station=float(t),x=float(p[0]),z=float(p[2]),roof=by,terrain=ground,wet_footprint=wy is not None))
 pts=np.array([[p['x'],max(p['roof'],p['terrain']),p['z']] for p in profile])
 slopes=np.abs(np.diff(pts[:,1]))/np.maximum(np.linalg.norm(np.diff(pts[:,[0,2]],axis=0),axis=1),1e-12)
 uncovered=[i for i,p in enumerate(profile) if p['wet_footprint']]
 q=dict(name=name,start=(pts[0]+[0,.2,0]).tolist(),end=(pts[-1]+[0,.2,0]).tolist(),expect='path',side=side,kind=kind,station=[start,stop],models=models)
 queries.append(q);screen.append(dict(name=name,dry_samples=len(profile)-len(uncovered),samples=len(profile),wet_indices=uncovered,max_profile_slope_deg=float(np.rad2deg(np.arctan(slopes.max(initial=0)))),max_roof_ground_separation_m=max(p['roof']-p['terrain'] for p in profile),profile=profile))
instances=author['instances'];assert len(instances)==139
for ix,inst in enumerate(instances):
 a,b=map(float,inst['station'])
 for side in columns:add(f'kit7_piece_{ix:03d}_{side}',a+.25*(b-a),a+.75*(b-a),side,[inst['model']],'piece')
for ix,(left,right) in enumerate(zip(instances,instances[1:])):
 seam=float(left['station'][1]);assert seam==right['station'][0]
 for side in columns:add(f'kit7_seam_{ix:03d}_{side}',seam-2,seam+2,side,[left['model'],right['model']],'seam')
# Natural end region remains in scope; external cap-to-land legs need packed-mesh discovery separately.
for end,a,b in [('head',float(station[0]),float(station[6])),('tail',float(station[-7]),float(station[-1]))]:
 for side in columns:add(f'kit7_end_{end}_{side}',a,b,side,[instances[0 if end=='head' else -1]['model']],'natural_end')
old=read(R/'patch-nav-f45/reference.json');assert len(old['queries'])==45
report=dict(status='GEOMETRIC_ROUTE_DISCOVERY_NOT_ACCEPTANCE',queries=queries,counts=dict(piece=278,seam=276,natural_end=4,total_local=len(queries),inherited_pending_retarget=45),screen=screen,inputs=inputs,
 issues=[dict(name=p['name'],wet=len(p['wet_indices']),slope=p['max_profile_slope_deg']) for p in screen if p['wet_indices'] or p['max_profile_slope_deg']>35],
 limits=['Half-metre geometric samples do not prove continuous dry/slope corridor.','Inherited45must retain full query contracts except justified Y retarget.','Coverage consumer must use packed Roadway labels and actual WRP poses, not accept detours bypassing models.','External end cap transitions still need explicit packed-mesh legs.','No navigation or locomotion verdict.'])
assert report['counts']['total_local']==558 and len({q['name'] for q in queries})==558
assert all(sha(Path(p))==h for p,h in inputs.items())
report['inputs_unchanged']=True;(D/'proposals.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],counts=report['counts'],issues=report['issues'],max_profile_slope=max(p['max_profile_slope_deg'] for p in screen)),indent=2))

