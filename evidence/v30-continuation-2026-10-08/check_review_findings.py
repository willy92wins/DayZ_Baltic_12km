"""Independent reproductions of the frozen Claude review; no terrain authoring."""
from pathlib import Path
import copy,hashlib,json,sys
import numpy as np
import shapely
from shapely.geometry import Polygon,box,shape
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/terrain'))
from audit_fairway_triangles_v30 import records
from v30_common import cell_planes
from verify_channel_reaches_v30 import check_face_coverage,retained_pond_surface
source=Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008/combined/terrain_inland.npz')
a=np.load(source);b=np.load('E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/fairway-proposal-r2/terrain_fairways.npz')
wave=np.load('E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/wave-banks-r1/terrain_wave_banks.npz')
nature_path=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/tests/regional_outline_v1/reference.npz')
nature=np.load(nature_path)['reserve']
delta=a['heights'].astype(float)-b['heights'].astype(float);changed=delta!=0
fairway=dict(changed_vertices=int(changed.sum()),road_reserve_vertices=int((changed&a['reserve']).sum()),
             nature_reserve_vertices=int((changed&nature).sum()),
             high_below1_before=int((changed&(a['level']>=2)&(a['heights']<1)).sum()),
             high_below1_after=int((changed&(a['level']>=2)&(b['heights']<1)).sum()),
             lowering_quantiles_m=np.quantile(delta[changed],[0,.1,.5,.9,1]).tolist(),
             single_ulp_changes=int((changed&(delta<=np.spacing(a['heights']))).sum()),
             prior_candidate_verdict='FAIL_PROTECTED_ROAD_RESERVE',
             protected_generator_result=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/fairway-protected/report.json').read_text()))
fit=Path('E:/DayZ-Baltic-Build/v30-v11/24');axes=json.loads((fit/'axes.json').read_text())
removed={tuple(rc) for reach in axes.values() for rc in reach['removed_cells']}
plane=cell_planes(a['cls'],a['level'],sea_cut=.51)
overlap=[]
for f in json.loads(Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson').read_text())['features']:
    rec=records(shape(f['geometry']),plane)
    overlap.append(dict(river=f['properties']['river'],removed_cell_intersections=len({tuple(rc) for rc in rec['cell_rc']}&removed)))
triangle=Polygon([(0,0),(6,0),(6,6)])
hole=box(4.25,1.25,4.5,1.5);surface=triangle.difference(hole)
assert all(surface.covers(shapely.Point(p)) for p in [(0,0),(6,0),(6,6)])
coverage_controls=dict(full_face_pass=check_face_coverage([triangle],triangle)['uncovered_faces']==0,
                       subcell_hole_rejected=check_face_coverage([triangle],surface)['uncovered_faces']==1)
manifest=json.loads((fit/'water/pieces.json').read_text())
rotated=copy.deepcopy(manifest)
next(p for p in rotated['poses'] if 'origin' in p)['rotation']=[0,90,0]
try:retained_pond_surface(fit,rotated,2208,7080)
except ValueError:coverage_controls['unsupported_orientation_rejected']=True
else:coverage_controls['unsupported_orientation_rejected']=False
actual=retained_pond_surface(fit,manifest,2208,7080)
coverage_controls['real_junction_retained']=abs(actual[0]-1.45)<1e-8
checks=dict(nature_unchanged_in_both_candidates=not np.any((a['heights']!=wave['heights'])&nature) and fairway['nature_reserve_vertices']==0,
            invalid_fairway_rejected=fairway['road_reserve_vertices']==483 and fairway['protected_generator_result']['status']=='INFEASIBLE',
            removed_fairway_overlap_disproved=all(p['removed_cell_intersections']==0 for p in overlap),
            coverage_negative_controls=all(coverage_controls.values()))
result=dict(status='PASS_REVIEW_REPRODUCTIONS' if all(checks.values()) else 'FAIL',checks=checks,
            fairway=fairway,removed_overlap=overlap,geometry_controls=coverage_controls,
            nature_reference_sha256=hashlib.sha256(nature_path.read_bytes()).hexdigest(),
            limits=['Source face coverage is not a maximum-wave, collision or rendered-seam verdict.',
                    '88 new exceptions use the frozen vertex-level >=2 m definition; not cell-mean level.'])
(OUT/'review-reproductions.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],checks=checks,fairway=fairway),indent=1))
assert all(checks.values())
