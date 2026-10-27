"""Single isolated source-array pilot; no asset build, native or RAM acceptance."""
from pathlib import Path
import ast,hashlib,json,sys,datetime
import numpy as np
from scipy.optimize import minimize
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');O=R/'dry-apron-linear-pilot-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def check_expected(expected):
 if any(sha(p)!=h for p,h in expected.items()):raise ValueError('identity')

def support_rounding_lower_bound(H,x,z,ground):
 """Conservative height bound for pre-round XZ within +/-1/1024 each.

 Native NW-SE triangle derivatives, from tri_h: ne-nw/se-sw in X,
 se-ne/sw-nw in row direction. Four corner cells cover the tiny rectangle.
 A Lipschitz bound handles a diagonal valley inside it, unlike just four heights.
 """
 eps=1/1024;gx=np.zeros_like(ground);gz=np.zeros_like(ground)
 for dx in (-eps,eps):
  for dz in (-eps,eps):
   c=np.clip(np.floor((x+dx)/6).astype(int),0,H.shape[1]-2);r=np.clip(np.floor((12282-z-dz)/6).astype(int),0,H.shape[0]-2)
   nw,ne,sw,se=H[r,c],H[r,c+1],H[r+1,c],H[r+1,c+1]
   gx=np.maximum(gx,np.maximum(abs(ne-nw),abs(se-sw))/6);gz=np.maximum(gz,np.maximum(abs(se-ne),abs(sw-nw))/6)
 return ground-eps*(gx+gz)

def quantize_bounded(values,original,free,floor,ceiling):
 if not all(np.isfinite(x).all() for x in (values,original,floor,ceiling)):raise ValueError('nonfinite')
 lo=np.ceil(floor*512);hi=np.floor(ceiling*512);valid=free&(lo<=hi);out=original.copy()
 out[valid]=np.clip(np.rint(values[valid]*512),lo[valid],hi[valid])/512
 return out,valid

def slope_metrics(bed,faces):
 y=bed[:,:,1];xz=bed[:,:,[0,2]];slopes=[]
 for axis in (0,1):
  d=np.linalg.norm(np.diff(xz,axis=axis),axis=2)
  if np.any(d<=1e-9):raise ValueError('collapsed grid edge')
  slopes.append(float(np.max(np.abs(np.diff(y,axis=axis))/d)))
 tri=bed.reshape(-1,3)[faces];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);den=np.abs(normal[:,1])
 if np.any(den<=1e-12):raise ValueError('collapsed XZ face')
 slopes.append(float(np.max(np.linalg.norm(normal[:,[0,2]],axis=1)/den)))
 return dict(longitudinal_max=slopes[0],transverse_max=slopes[1],face_max=slopes[2])

def historical_functions(author):
 tree=ast.parse(author.read_text(encoding='utf-8'));names={'fair_energy','fair_support','strip_faces'}
 defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(defs)==3
 ns={'np':np,'minimize':minimize};exec(compile(ast.Module(body=defs,type_ignores=[]),str(author),'exec'),ns);return ns

def main():
 O.mkdir(exist_ok=False);start=datetime.datetime.now(datetime.timezone.utc);deadline=start+datetime.timedelta(minutes=15)
 (O/'budget.json').write_text(json.dumps(dict(started_utc=start.isoformat(),deadline_utc=deadline.isoformat(),max_solver_iterations=500,max_candidates=1,prior_weight=.002,dayz_runs=0),indent=2)+'\n')
 source=R/'river-kit7-a-on-f-20261026/kit-7-surfaces.npz';author=W/'tools/water/continuous_stream_pilot_v31.py';base=R/'rectangle-pilot-f-merged/terrain-buried.npz';fp=R/'rectangle-pilot-f-merged/bury-work/fp0/footprint.npz';support=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz'
 expected={source:'9d8caf0fb75d2bd34f71b877ecd3f71079898fbc01c28e67ddab0bf8dca50063',author:'8b340a2ab4e25d69ff9baf46f71c8f843c9da2c02137c32fa356a0bb9deb9169',base:'caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc',fp:'95f7a26304e88c726679ec69ef076bb149ec1f1f8bdf4a6cd1e83e40f3b6be83',support:'815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'}
 check_expected(expected)
 bound_paths=[Path(__file__),author,source,base,fp,support,W/'tools/water/streambed_kit_v31.py',W/'tools/terrain/shape_repair_constraints_ev112.py',W/'tools/terrain/verify_roads_v30.py',W/'plans/ev112-dry-apron-offline-pilot-20261027.md',R/'bank-source-attribution-20261027/result.json',R/'river-kit7-a-on-f-20261026/author-report.json']
 input_before={str(p):sha(p) for p in bound_paths}
 sys.path[:0]=[str(W/'tools/water'),str(W/'tools/terrain')]
 import streambed_kit_v31 as kit
 from shape_repair_constraints_ev112 import s3_road_guard
 functions=historical_functions(author);a=np.load(source);arrays={k:a[k].copy() for k in a.files};bed=arrays['bed'];original=bed[:,:,1].copy();n,m=original.shape
 if not np.array_equal(original,np.rint(original*512)/512):raise ValueError('baseline not on source grid')
 qs=np.unique(np.r_[np.arange(-18,19,dtype=float),-2.25,2.25]);assert m==len(qs)
 ba=np.load(base);H=np.load(support)['heights'].astype(float)
 keys=['reserve','platform','narva','v31_bridge_cut','v31_bridge_fill','v31_dam','v31_causeway','v31_shore_ramp']
 protected=np.logical_or.reduce([ba[k] for k in keys]);guard,refs=s3_road_guard();protected|=guard
 history=read(R/'river-kit7-a-on-f-20261026/author-report.json');assert refs==history['road_reference_hashes']
 for key in ('v31_road_repair','v31_road_mesh_repair','v31_continuous_pilot'):
  if key in ba.files:protected|=ba[key]
 protected|=kit.c2v(np.isfinite(np.load(fp)['plane']));rr,cc=np.mgrid[:2048,:2048];protected|=np.hypot(cc*6.-10397.4,12282-rr*6.-9421.9)<=60
 ground=kit.tri_h(H,bed[:,:,0],bed[:,:,2]);pweight=kit.tri_h(protected.astype(float),bed[:,:,0],bed[:,:,2]);free=np.broadcast_to((abs(qs)>4)&(abs(qs)<18),original.shape).copy();free[[0,-1],:]=False;free&=pweight<=0
 gmin=support_rounding_lower_bound(H,bed[:,:,0],bed[:,:,2],ground)
 if np.any(original[free]<gmin[free]+.02-1/1024-2e-6):raise ValueError('source support does not satisfy historical floor')
 water=arrays['level'][:,None]+np.zeros_like(original);floor=ground+.02;was_dry=original>=water+.025;floor=np.where(was_dry,np.maximum(floor,water+.025),floor);ceiling=original.copy()
 infeasible=free&(floor>ceiling);free&=~infeasible
 quant_bad=free&(np.ceil(floor*512)>np.floor(ceiling*512));free&=~quant_bad
 prior=original.copy()
 for side in (-1,1):
  ii=int(np.flatnonzero(qs==side*4)[0]);oo=int(np.flatnonzero(qs==side*18)[0]);columns=np.flatnonzero((qs*side>4)&(qs*side<18))
  t=(np.abs(qs[columns])-4)/14
  prior[:,columns]=original[:,ii,None]*(1-t)+original[:,oo,None]*t
 if np.any(free):values,solver=functions['fair_support'](original,prior,free,floor,ceiling)
 else:values=original.copy();solver=dict(success=True,message='NO_FREE_POINTS',iterations=0)
 assert datetime.datetime.now(datetime.timezone.utc)<deadline
 candidate,valid=quantize_bounded(values,original,free,floor,ceiling);outbed=bed.copy();outbed[:,:,1]=candidate
 assert np.array_equal(candidate[~free],original[~free]) and np.all(candidate[free]>=floor[free]) and np.all(candidate[free]<=ceiling[free])
 assert np.array_equal(outbed[:,:,[0,2]],bed[:,:,[0,2]])
 faces=functions['strip_faces'](n,m);before=slope_metrics(bed,faces);after=slope_metrics(outbed,faces);energy_before=float(functions['fair_energy'](original,original,weight=0)[0]);energy_after=float(functions['fair_energy'](candidate,candidate,weight=0)[0])
 gates=dict(finite=bool(np.isfinite(candidate).all()),fixed_exact=bool(np.array_equal(candidate[~free],original[~free])),bounds=bool(np.all(candidate[free]>=floor[free]) and np.all(candidate[free]<=ceiling[free])),curvature_nonincreasing=energy_after<=energy_before,slope_nonincreasing=all(after[k]<=before[k] for k in before),improved=energy_after<energy_before)
 arrays['bed']=outbed;np.savez_compressed(O/'candidate-surfaces.npz',**arrays)
 for key in a.files:
  if key!='bed':assert np.array_equal(arrays[key],a[key])
 # Use archived attribution weights at the same XZ, never move queries or claim native PASS.
 native=read(R/'bank-source-attribution-20261027/result.json');points=[]
 for row in native['rows']:
  hits=[]
  for old in row['all_candidates']:
   vertices=faces[old['triangle']];assert np.array_equal(bed.reshape(-1,3)[vertices],np.array(old['triangle_vertices']));y=float(np.array(old['weights'])@outbed.reshape(-1,3)[vertices,1]);hits.append(y)
  y=max(hits);points.append(dict(mesh=row['mesh'],query=row['query'],index=row['index'],previous_failed=row['failed'],baseline_surface_y=row['native_roadway_y'],candidate_surface_y=y,delta_y=y-row['native_roadway_y'],visual_water_y=row['selected']['visual_water_y'],candidate_above_water=y-row['selected']['visual_water_y'],difference_to_OLD_nav_y=abs(y-row['navigation_y']),NOT_NATIVE_VERDICT=True))
 assert all(sha(p)==h for p,h in expected.items());assert all(sha(Path(p))==h for p,h in refs.items());assert all(sha(Path(p))==h for p,h in input_before.items())
 result=dict(status='OFFLINE_CANDIDATE_ONLY' if all(gates.values()) else 'REJECTED_OFFLINE',gates=gates,solver=solver,inputs={str(p):sha(p) for p in bound_paths}|refs,inputs_unchanged=True,source_grid_shape=list(original.shape),changed_points=int(np.count_nonzero(candidate!=original)),infeasible_fixed=int(infeasible.sum()),no_quantized_value_fixed=int(quant_bad.sum()),free_points=int(free.sum()),delta_range_m=[float((candidate-original).min()),float((candidate-original).max())],curvature_energy=[energy_before,energy_after],slopes=dict(baseline=before,candidate=after),points=points,candidate_sha256=sha(O/'candidate-surfaces.npz'),limits=['One fixed .002 prior weight, one solver capped500; no parameter sweep.','Discrete grid energy is not physical curvature or visual acceptance.','OLD nav Y comparisons are descriptive only: regenerated topology/height not predicted.','No native graph/RAM/actor/visual PASS, asset package or deployment.'])
 (O/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','points')},indent=2))

if __name__=='__main__':main()
