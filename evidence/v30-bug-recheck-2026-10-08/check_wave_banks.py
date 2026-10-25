"""Independent native-surface, road and contour consumers for the local bank fix."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'tools/terrain'),str(ROOT/'tools/navigation')]
from waterway_common import sample
from v30_common import cell_planes,vertex_plane_bounds
from verify_roads_v30 import evaluate

oldpath=Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008/combined/terrain_inland.npz')
newpath=Path('E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/wave-banks-r1/terrain_wave_banks.npz')
a,b=np.load(oldpath),np.load(newpath)
old,new=a['heights'].astype(float),b['heights'].astype(float)
changed=old!=new
plane=cell_planes(a['cls'],a['level'],sea_cut=.51)
_,high=vertex_plane_bounds(plane)
checks=dict(metadata_exact=all(np.array_equal(a[k],b[k],equal_nan=True) for k in a.files if k!='heights'),
            water_beds_exact=bool(np.array_equal(old[a['cls']>0],new[a['cls']>0])),
            only_dry_banks=bool(np.all(a['cls'][changed]==0)),
            reserves_fixed=bool(np.array_equal(old[a['reserve']],new[a['reserve']])),
            platforms_fixed=bool(np.array_equal(old[a['platform']],new[a['platform']])),
            bounded_lowering=bool(np.all(new<=old) and (old-new).max()<=.25),
            dry_floor=bool(np.all(new[changed]>=1.4)),
            bank_freeboard=bool(np.all(new[changed & np.isfinite(high)]>high[changed & np.isfinite(high)]+.05)))
points=[]
for p in json.loads((OUT/'wave-reference.json').read_text())['points']:
    h0=float(sample(old,p['x']+200000,p['z']))
    h1=float(sample(new,p['x']+200000,p['z']))
    r,c=int((12282-p['z'])//6),int(p['x']//6)
    level=plane[r,c]
    points.append(dict(id=p['id'],before_ground=h0,after_ground=h1,
                       before_depth=float(level-h0) if np.isfinite(level) else None,
                       after_depth=float(level-h1) if np.isfinite(level) else None))
checks['known_exposures_baseline_rejected']=all(p['before_depth']<.181 for p in points if p['id'] in (765,1176))
checks['known_exposures_nominal_margin']=all(p['after_depth']>=.20099 for p in points if p['id'] in (765,1176))
checks['other_observers_exact']=all(p['before_ground']==p['after_ground'] for p in points if p['id'] not in (765,1176))
# Keep all 463 original dry controls, beyond the 17 temporal sites. Their
# classification is not re-derived to erase inconvenient points.
dryref=Path('E:/DayZ-Baltic-Build/v30-continuity-dedup-package/runtime-fixture/reference.json')
dry=[p for p in json.loads(dryref.read_text())['points'] if p['kind']=='dry']
xx=np.array([p['x']+200000 for p in dry]);zz=np.array([p['z'] for p in dry])
dry_changes=int(np.count_nonzero(sample(old,xx,zz)!=sample(new,xx,zz)))
checks['463_frozen_dry_observers_exact']=len(dry)==463 and dry_changes==0
# The already executed vehicle consumers remain valid only if no edited
# triangle can intersect their full lateral tolerance, hull and support halo.
vertices=[Point(float(c*6),float(12282-r*6)) for r,c in zip(*np.nonzero(changed))]
route_checks=[]
for kind,path in [('car',OUT/'drive-reference.json'),
                  ('boat',ROOT/'evidence/v30-bounded-integration-2026-10-08/boat-reference.json')]:
    for case in json.loads(path.read_text())['cases']:
        raw=np.array(case['route_xyz']) if kind=='car' else np.array(case['waypoints_xz'])
        coords=raw[:,[0,2]] if kind=='car' else raw
        axis=LineString(coords)
        nearest=min(p.distance(axis) for p in vertices)
        route_checks.append(dict(kind=kind,case=case['case'],nearest_changed_vertex_m=nearest))
checks['vehicle_corridors_unchanged_with_25m_support_halo']=all(p['nearest_changed_vertex_m']>25 for p in route_checks)
bad=[]
land=a['cls']==0
for dr,dc in [(0,1),(1,0)]:
    def slopes(h):
        mid=h[dr:dr+2047,dc:dc+2047]
        return np.degrees(np.arctan(np.hypot(mid-h[:-1,:-1],h[1:,1:]-mid)/6))
    before,after=slopes(old),slopes(new)
    touch=land[:-1,:-1]|land[dr:dr+2047,dc:dc+2047]|land[1:,1:]
    bad.extend(dict(row=int(r),col=int(c),half=[dr,dc],before=float(before[r,c]),after=float(after[r,c]))
               for r,c in zip(*np.nonzero(touch & (after>35.01) & (after>before+1e-6))))
checks['no_new_or_worsened_steep_faces']=not bad
# Native nominal shoreline segments in affected cells, including an unchanged
# collar. Check both directed distances at <=0.25 m spacing, with that spacing
# retained as a conservative error bound rather than an exact Hausdorff claim.
cells=set()
for r,c in zip(*np.nonzero(changed)):
    cells.update((i,j) for i in range(r-2,r+2) for j in range(c-2,c+2))
def contours(h):
    lines=[]
    for r,c in sorted(cells):
        level=plane[r,c]
        if not np.isfinite(level):continue
        for triangle in [((r,c),(r,c+1),(r+1,c+1)),((r,c),(r+1,c),(r+1,c+1))]:
            hits=[]
            for (ra,ca),(rb,cb) in zip(triangle,triangle[1:]+triangle[:1]):
                za,zb=h[ra,ca]-level,h[rb,cb]-level
                if za*zb<0:
                    t=za/(za-zb)
                    hits.append((6*(ca+t*(cb-ca)),12282-6*(ra+t*(rb-ra))))
            if len(hits)==2:lines.append(LineString(hits))
    return lines
before,after=contours(old),contours(new)
assert before and after
maxima=[]
for source,target in [(before,after),(after,before)]:
    union=unary_union(target)
    maxima.append(max(line.interpolate(float(d)).distance(union) for line in source
                      for d in np.linspace(0,line.length,max(2,int(np.ceil(line.length/.25))+1))))
contour_bound=max(maxima)+.25
checks['shoreline_displacement_under_4m']=contour_bound<4
roads=evaluate(new,a['water'].astype(bool))
checks['roads_pass']=roads['status']=='PASS'
result=dict(status='PASS_OFFLINE_WAVE_BANKS' if all(checks.values()) else 'FAIL',checks=checks,
            terrain_sha256=hashlib.sha256(newpath.read_bytes()).hexdigest(),changed_vertices=int(changed.sum()),
            points=points,steep_faces=bad,contour_directed_samples_max_m=maxima,
            contour_conservative_bound_m=contour_bound,roads=roads,
            dry_reference_sha256=hashlib.sha256(dryref.read_bytes()).hexdigest(),frozen_dry_points=len(dry),
            changed_dry_observers=dry_changes,vehicle_routes=route_checks,
            limits=['Engine wave replay remains required.','Nominal contour bound uses sampled line segments plus 0.25 m error allowance.'])
(OUT/'wave-bank-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=result['status'],checks=checks,contour_bound_m=contour_bound,steep_faces=bad),indent=1))
raise SystemExit(0 if all(checks.values()) else 1)
