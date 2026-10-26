"""Read-only forest impact against saved kit7 bed/water; no stage edit or PASS claim."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
import shapely
from shapely.geometry import Polygon
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018');S=R/'stage-rectangle-f';K=R/'river-kit7-midpoint-a-20261026';O=R/'kit7-forest-impact-20261026'
sys.path[:0]=[str(W/'tools/vegetation'),str(W/'tools/water'),'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
from review_visual_forest_support_v31 import forest_arrays,read
from streambed_kit_v31 import tri_h
import py3d,review_visual_forest_support_v31,streambed_kit_v31
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
jread=lambda p:json.loads(Path(p).read_text())
assert jread(R/'kit7-compiled-review-20261026/accepted.json')['status']=='ACCEPTED_KIT7_PACKED_OFFLINE'
wrp=S/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';assert sha(wrp)=='6e649b72bf4ec6789a83050f21b7e5597de417e14f251f854728eb20d8b84bd8'
meta=jread(S/'stage-report.json');ref=Path(meta['forest_reference']['path']);assert sha(ref)==meta['forest_reference']['sha256'];models=jread(ref)['models']
oldterrain=R/'rectangle-pilot-f-merged/terrain-buried.npz';terrain=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz'
assert sha(oldterrain)=='caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc' and sha(terrain)=='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'
nf=B/'stage-nonforest-c/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
paths=[Path(__file__),wrp,S/'stage-report.json',ref,nf,oldterrain,terrain,K/'author-report.json',Path(review_visual_forest_support_v31.__file__),Path(streambed_kit_v31.__file__),Path(py3d.__file__)]
inputs={str(p):sha(p) for p in paths};O.mkdir(exist_ok=False);(O/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
oldids={o['id'] for o in read(nf)['objects']};H0=np.load(oldterrain)['heights'];H=np.load(terrain)['heights']
count=meta['remaining_objects']-(len(oldids)-meta['removed_old_kit_records'])
names,ids,mat=forest_arrays(wrp,oldids,sorted(models),count,H0)
M=mat[:,:9].reshape(-1,3,3).transpose(0,2,1).astype(float);bc=np.array([models[n]['bc'] for n in names])
root=mat[:,9:]-np.einsum('nij,nj->ni',M,bc);scale=np.linalg.norm(M[:,:,0],axis=1)
base=np.array([models[n]['base_radius_plan'] for n in names])*scale;radius=np.where([models[n]['family']=='reed' for n in names],.25,base+.25)
inside=(root[:,0]>=0)&(root[:,0]<=12282)&(root[:,2]>=0)&(root[:,2]<=12282);dy=np.zeros(count)
dy[inside]=tri_h(H,root[inside,0],root[inside,2])-tri_h(H0,root[inside,0],root[inside,2])
author=jread(K/'author-report.json');beds=[];waters=[]
for inst in author['instances']:
 path=K/'source'/inst['model'].replace('\\','/');assert sha(path)==inst['sha256'];inputs[str(path)]=inst['sha256']
 with path.open('rb') as f:
  assert struct.unpack('<4sII',f.read(12))==(b'MLOD',257,4);lod=py3d.LOD(f)
 xyz=np.array([p.coords for p in lod.points])+inst['origin']
 for face in lod.faces:
  polygon=Polygon(xyz[[v.point_index for v in face.vertices]][:,[0,2]])
  (waters if 'water_streambed' in face.material else beds).append(polygon)
bp=shapely.union_all(beds);wp=shapely.union_all(waters);assert bp.is_valid and wp.is_valid
bound=shapely.union_all([bp,wp]).bounds;margin=max(float(base.max()+.5),float(radius.max()))
near=np.flatnonzero((root[:,0]>=bound[0]-margin)&(root[:,0]<=bound[2]+margin)&(root[:,2]>=bound[1]-margin)&(root[:,2]<=bound[3]+margin))
points=shapely.points(root[near][:,[0,2]]);bd=shapely.distance(bp,points);wd=shapely.distance(wp,points)
bed_hits=near[bd<base[near]+.5];water_hits=near[wd<radius[near]];drop=np.union1d(bed_hits,water_hits);shift=np.flatnonzero(dy)
def row(i):return dict(id=int(ids[i]),model=str(names[i]),root=root[i].tolist(),ground_delta_m=float(dy[i]),base_radius_m=float(base[i]),water_margin_m=float(radius[i]))
same=all(sha(p)==h for p,h in inputs.items());assert same
(O/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
result=dict(status='DISCOVERY_NOT_ACCEPTANCE',forest_records=count,nearby_records=len(near),height_adjustment_candidates=len(shift),bed_margin_conflicts=len(bed_hits),water_margin_conflicts=len(water_hits),water_conflicts_subset_of_bed=bool(set(water_hits)<=set(bed_hits)),union_conflicts=len(drop),retained_height_adjustment_candidates=int(len(np.setdiff1d(shift,drop))),outside_roots_untouched=int((~inside).sum()),conflicts=[row(i) for i in drop],height_candidates=[row(i) for i in shift],inputs_unchanged=same,limits=['Exact saved visual-bed/water distance and native-triangle root deltas only; full support/transform/context and boundary/native gates remain.','No forest/WRP/PBO modified. Old kit removal/composition is a separate prerequisite.'])
(O/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['conflicts','height_candidates']},indent=2))
