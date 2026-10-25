from pathlib import Path
import hashlib,json,sys,numpy as np
R=Path(__file__).parent;D=R/'recheck-20261024-forest-boundary'
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
W=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(B/'forest-final-tools/r2/gates'),str(W/'tools/water')]
import geom
from eval_visual_probe_v31 import parse
from streambed_kit_v31 import tri_h
meta=json.loads((R/'boundary-probe-r/points-130.json').read_text())
rows=parse((D/'boundary-probe.log').read_text(encoding='utf-8-sig'),216)
terrain=B/'road-merged-20261024-h/terrain-buried.npz'
assert hashlib.sha256(terrain.read_bytes()).hexdigest()=='d3d41a8b71253ce1eae427ade4b9a327bd44062a6f58a835cd79d01e48db8762'
H=np.load(terrain)['heights'];S=np.load(R/'road-merged-s3/terrain-buried.npz')['heights']
same=all(np.array_equal(a,b) for a,b in [(H[:5],S[:5]),(H[-5:],S[-5:]),(H[:,:5],S[:,:5]),(H[:,-5:],S[:,-5:])])
measurements=[]
for p in meta['points']:
    r=rows[p['id']];clamp=float(geom.h_at(H,p['x'],p['z']));extrap=float(tri_h(H,p['x'],p['z']))
    measurements.append(dict(p,ground=r['ground'],coordinate_clamp=clamp,index_clamp_extrapolation=extrap,
                             delta_coordinate_clamp=r['ground']-clamp,delta_index_clamp_extrapolation=r['ground']-extrap))
groups={}
for kind in sorted({p['kind'] for p in measurements}):
    p=[v for v in measurements if v['kind']==kind]
    groups[kind]=dict(count=len(p),max_coordinate_clamp_error=max(abs(v['delta_coordinate_clamp']) for v in p),
                     max_index_clamp_extrapolation_error=max(abs(v['delta_index_clamp_extrapolation']) for v in p))
data=np.load(D/'boundary-forest-s3.npz');o=data['origin'];r=data['required'];t=data['trunk'];sel=np.isin(data['families'],['conifer','broadleaf','bush'])
sw=(o[:,0]-r<0)|(o[:,2]-r<0)
result=dict(status='RUNTIME_BOUNDARY_DIAGNOSTIC',run_id=json.loads((D/'launch-result.json').read_text())['run_id'],
            log_sha256=hashlib.sha256((D/'boundary-probe.log').read_bytes()).hexdigest(),points=216,groups=groups,
            same_R_S3_border_30m=same,
            boundary_discs=dict(total=len(o),south_or_west=int(sw.sum()),south_or_west_trunks=int((sel&((o[:,0]-t<0)|(o[:,2]-t<0))).sum()),
                                beyond_world_north_or_east=int(((o[:,0]+r>12288)|(o[:,2]+r>12288)).sum()),
                                footprint_bounds=[float(min(o[:,0]-r)),float(min(o[:,2]-r)),float(max(o[:,0]+r)),float(max(o[:,2]+r))]),
            measurements=measurements,
            interpretation=['Previous clamped_hypothesis was misnamed: tri_h clamps indices, then extrapolates fractions.',
                            'Coordinate clamp agrees with all 120 north/east transect/root measurements within 0.000026 m.',
                            'Negative south/west coordinates disagree; do not generalize a clamp or declare all discs accepted.',
                            '216 measurements do not prove continuous support, roots beyond the selected 24, or world exterior past 12288.'])
(D/'boundary-analysis-v2.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='measurements'},indent=2))
