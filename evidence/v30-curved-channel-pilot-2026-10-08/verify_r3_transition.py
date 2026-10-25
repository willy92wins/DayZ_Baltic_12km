"""Independent gate replay on the proposed R3 bank exception.

Reuse the expensive frozen corridor result only after geometric separation of
every changed support from all its polygons; inspect native slopes directly,
without reusing the LP constraints or its solver success status.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import shapely
from shapely.geometry import shape
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008');E=W/'evidence/v30-curved-channel-pilot-2026-10-08'
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import cell_planes,vertex_plane_bounds,tri_sample
from verify_roads_v30 import evaluate
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
original=Path('E:/DayZ-Baltic-Build/v30-navigation-contract-20261008/terrain_floor.npz')
source=B/'flat-profile/terrain_flat.npz';candidate=B/'r3-transition-proposal/terrain_flat.npz'
initial=json.loads((E/'flat-verification.json').read_text())
assert initial['inputs'][str(source)]==sha(source)
assert initial['inputs'][str(B/'flat-water/water/pieces.json')]==sha(B/'flat-water/water/pieces.json')
assert [k for k,v in initial['checks'].items() if not v]==['wet_corners_covered']
a,b,c=np.load(original),np.load(source),np.load(candidate)
base=a['heights'].astype(float);old=b['heights'].astype(float);new=c['heights'].astype(float)
planes=cell_planes(c['cls'],c['level']);pmin,pmax=vertex_plane_bounds(planes)
mask=np.load(B/'r3-transition-proposal/masks.npz');changed=new!=old;allchanged=new!=base
pts=shapely.points(np.array([(col*6,12282-row*6) for row,col in zip(*np.nonzero(changed))]))
corpath=Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson')
assert initial['inputs'][str(corpath)]==sha(corpath)
distances=[float(shapely.distance(pts,shape(f['geometry'])).min()) for f in json.loads(corpath.read_text())['features']]
assert min(distances)>6*np.sqrt(2),min(distances)
inspect=mask['core']|allchanged
bad_dry=inspect&(c['cls']==0)&np.isfinite(pmax)&(new<pmax-1e-6)
bad_wet=inspect&np.isin(c['cls'],(2,3,5,6,7))&np.isfinite(pmin)&(new>pmin-.02+1e-6)
steep=[];rounding=[]
for dr,dc in ((0,1),(1,0)):
    def slopes(h):
        middle=h[dr:dr+2047,dc:dc+2047]
        return np.degrees(np.arctan(np.hypot(middle-h[:-1,:-1],h[1:,1:]-middle)/6))
    before,after=slopes(base),slopes(new);land=c['cls']==0
    touch=land[:-1,:-1]|land[dr:dr+2047,dc:dc+2047]|land[1:,1:]
    for r,col in zip(*np.nonzero(touch&(after>35.01)&(after>before+1e-6))):
        row=(int(r),int(col),float(before[r,col]),float(after[r,col]))
        # Match the established native-face gate's 1e-4 degree allowance
        # (finish_shores_v30.py discard_steeper_land_faces). Heights are float32;
        # report rather than hide smaller differences after quantisation.
        (steep if after[r,col]>before[r,col]+1e-4 else rounding).append(row)
roads=evaluate(new,c['water'].astype(bool))
floor=np.isin(c['cls'],(2,3,5,6,7))&(base>=1)
checks=dict(initial['checks']);checks.update(wet_corners_covered=not bool(bad_wet.any()),no_dry_corner_under_water=not bool(bad_dry.any()),
    metadata_exact=all(np.array_equal(a[k],c[k],equal_nan=True) for k in a.files if k!='heights'),
    outside_exact=not bool(np.any(allchanged&~mask['allowed'])),frozen_exact=not bool(np.any(allchanged&mask['frozen'])),
    existing_floor_preserved=bool(np.all(new[floor]>=1)),no_steepening=not steep,roads_pass=roads['status']=='PASS',
    corridor_proof_reused_with_geometric_separation=bool(min(distances)>6*np.sqrt(2)))
# Genuine consumer mutation: raise every support of a previously PASS corridor
# sample to nominal level -0.94 m and resample the native triangle at that point.
prior=json.loads((W/'evidence/v30-navigation-contract-2026-10-08/verification.json').read_text())
point=min(prior['corridors'],key=lambda p:p['worst']['depth_m'])['worst'];x,z=point['xz'];r,col=point['cell']
lv=max(float(planes[r,col]),.5);before_depth=lv-float(tri_sample(new,x,z))
mutant=new.copy();mutant[r:r+2,col:col+2]=lv-.94
mutated_depth=lv-float(tri_sample(mutant,x,z))
assert before_depth>=.95 and mutated_depth<.95
controls=dict(initial['controls'],depth_094_rejected=before_depth>=.95 and mutated_depth<.95,
              depth_positive_m=before_depth,depth_mutated_m=mutated_depth)
checks['negative_controls']=all(controls[k] for k in ('hole_rejected','duplicate_rejected','depth_094_rejected'))
report=dict(status='PASS_OFFLINE_FLAT_FALLBACK' if all(checks.values()) else 'FAIL',checks=checks,
    source_verification_sha256=sha(E/'flat-verification.json'),inputs={str(p):sha(p) for p in (original,source,candidate,corpath,Path(__file__))},
    min_distance_of_new_edits_to_global_corridors_m=min(distances),corridors=initial['corridors'],roads=roads,
    coverage=initial['coverage'],complete_cell_gap_m2=initial['complete_cell_gap_m2'],redundant_area_ratio=initial['redundant_area_ratio'],
    steep_faces=steep,float32_rounding_faces=rounding,slope_tolerance_degrees=.0001,dry_failures=int(bad_dry.sum()),wet_failures=int(bad_wet.sum()),controls=controls,
    initial_changed_vertices=int((old!=base).sum()),additional_changed_vertices=int(changed.sum()),total_changed_vertices=int(allchanged.sum()),
    limits=['Local R3 nature bank heights are an explicit implementation exception; perimeter/classes/levels remain exact.',
            'Only source geometry checked; compiled placements, runtime and visual acceptance remain.'])
(E/'flat-verification-r2.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('corridors','roads','inputs')},indent=2))
assert all(checks.values())
