"""Screen the approved flat fallback against current native water, before creating assets."""
from pathlib import Path
import json,math,sys
import numpy as np
import shapely
from shapely.geometry import Point,box
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-curved-channel-pilot-2026-10-08'
FIT=Path(r'E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water')]
from v30_common import cell_planes,tri_sample
from verify_channel_reaches_v30 import retained_pond_faces
import engine_water_model as ewm
t=np.load(r'E:/DayZ-Baltic-Build/v30-navigation-contract-20261008/terrain_floor.npz')
axes=json.loads((FIT/'axes.json').read_text())
manifest=json.loads((FIT/'water/pieces.json').read_text())
plane=cell_planes(t['cls'],t['level'])
all_removed={tuple(rc) for a in axes.values() for rc in a['removed_cells']}
domain=shapely.union_all([box(c*6,12282-(r+1)*6,(c+1)*6,12282-r*6) for r,c in all_removed])
retained=retained_pond_faces(FIT,manifest,domain.buffer(6))
polys=[p[0] for p in retained];tree=shapely.STRtree(polys)
oldpieces=[ewm.Piece(p['type'],p['matrix']) for a in axes.values() for p in a['pieces']]
def flat_levels(x,z):
    ci=int(math.floor(x/6));ri=int(math.floor((12282-z)/6))
    return [float(plane[r,c]) for r in range(ri-1,ri+2) for c in range(ci-1,ci+2)
            if (r,c) in all_removed and math.isfinite(plane[r,c])
            and 6*c-1e-6<=x<=6*(c+1)+1e-6 and 12282-6*(r+1)-1e-6<=z<=12282-6*r+1e-6]
results={};records=[]
for name,a in axes.items():
    coords=set()
    for r,c in a['removed_cells']:
        coords.update((6*c+dx,12282-6*r-dz) for dx in (0,3,6) for dz in (0,3,6))
    points=np.array([Point(x,z) for x,z in sorted(coords)],dtype=object)
    ii,jj=tree.query(points,predicate='intersects')
    ponds={}
    for i,j in zip(ii,jj):ponds.setdefault(int(i),[]).append(retained[j][1])
    new_wet=[];lost_wet=[];no_coverage=[];drops=[]
    for i,(x,z) in enumerate(sorted(coords)):
        ground=float(tri_sample(t['heights'],x,z))
        old=[q.level(x,ground+.01,z) for q in oldpieces]
        old=[v for v in old if v is not None]+ponds.get(i,[])
        new=flat_levels(x,z)+ponds.get(i,[])
        before=max(old) if old else None;after=max(new) if new else None
        row=dict(reach=name,x=x,z=z,ground=ground,old=before,new=after)
        records.append(row)
        if before is not None and after is None:no_coverage.append(row)
        if (before is None or before<=ground) and after is not None and after>ground+1e-6:new_wet.append(row)
        if before is not None and before>ground and (after is None or after<=ground):lost_wet.append(row)
        if before is not None and after is not None:drops.append(after-before)
    results[name]=dict(samples=len(coords),new_wet_count=len(new_wet),new_wet_examples=new_wet[:15],
                       lost_wet_count=len(lost_wet),lost_wet_examples=lost_wet[:15],
                       missing_coverage_count=len(no_coverage),level_change_min_max=[min(drops),max(drops)],
                       pass_nominal_screen=not new_wet and not lost_wet and not no_coverage)
    print(name,json.dumps(results[name]),flush=True)
out=dict(status='FLAT_FALLBACK_SCREEN_ONLY',reaches=results,
         pass_nominal_screen=all(v['pass_nominal_screen'] for v in results.values()),
         limits=['Source rule over the existing removed cells; no new P3D/WRP/PBO generated.',
                 'Three-meter lattice is not continuous shore certification.',
                 'Nominal surface only, not wave envelope or visual/physical acceptance.',
                 'Previous piece skirt depths can differ from the flat band by up to the scaled skirt height.'])
assert not (E/'flat-screen.json').exists()
(E/'flat-screen.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
(E/'flat-samples.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
