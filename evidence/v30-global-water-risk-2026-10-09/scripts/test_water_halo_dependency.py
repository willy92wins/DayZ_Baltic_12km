"""Independent rectangle consumer: no stale old level may survive inside a lowered boundary cell."""
from pathlib import Path
import sys,json
import numpy as np
import shapely
from shapely.geometry import box
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/terrain'),str(W/'tools/navigation')]
from patch_water_tiles_v30 import dependent_tiles,regenerate_tile,tile_cells,FULL_MODEL
before=np.full((2047,2047),-1,dtype=np.int32)
# A 6x6-tile pond with a single lowered cell, away from world/pond perimeter.
before[1815:1863,144:192]=100
cases=[]
for col,bottom in [(162,194),(160,194),(167,194),(162,192),(162,199),(160,192),(167,199)]:
    row=2046-bottom;after=before.copy();after[row,col]=80
    owner=(col//8,bottom//8);affected=set(dependent_tiles([row],[col]))
    target=box(col*6,bottom*6,col*6+6,bottom*6+6)
    expected={ (tx,tz) for tx in range(owner[0]-1,owner[0]+2) for tz in range(owner[1]-1,owner[1]+2)
        if box(tx*48-.01,tz*48-.01,(tx+1)*48+.01,(tz+1)*48+.01).intersection(target).area>0 }
    assert affected==expected,(affected,expected)
    def build(use_affected,old_full_rule=False):
        polys=[];k=0
        def name():
            nonlocal k
            k+=1;return 'test_'+str(k)
        for tx,tz in expected:
            field=after if (tx,tz) in use_affected else before
            poses,geoms=regenerate_tile(field,tx,tz,name);byname={n:g for n,g,_ in geoms}
            for p in poses:
                if p['band']!=100:continue
                if p['model']==FULL_MODEL:g=box(tx*48-.01,tz*48-.01,(tx+1)*48+.01,(tz+1)*48+.01)
                else:g=byname[p['model'].split('\\')[-1][:-4]]
                if old_full_rule and g.covers(box(tx*48,tz*48,(tx+1)*48,(tz+1)*48)):
                    g=box(tx*48-.01,tz*48-.01,(tx+1)*48+.01,(tz+1)*48+.01)
                polys.append(g)
        return float(shapely.union_all(polys).intersection(target).area)
    repaired=build(affected);assert repaired<1e-9
    stale=build({owner});full=build(affected,True)
    if len(expected)>1:assert stale>.005 and full>.005,(row,col,bottom,stale,full)
    cases.append(dict(row=row,col=col,dependent_tiles=sorted(affected),repaired_wrong_level_area_m2=repaired,
        old_owner_only_wrong_level_area_m2=stale,old_full_reuse_wrong_level_area_m2=full))
assert dependent_tiles([],[])==[]
assert all(x>=0 and z>=0 for x,z in dependent_tiles([2046],[0]))
assert all(x<=255 and z<=255 for x,z in dependent_tiles([0],[2046]))
out=dict(status='PASS',cases=cases,positive='7 exact source rectangle cases',negatives='Old owner-only invalidation and exact-tile full reuse both reproduce wrong-level slivers in all 6 boundary/corner cases.',limits='Generator regression control; compiled preview and runtime validation still required.')
(W/'evidence/v30-global-water-risk-2026-10-09/water-halo-regression.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
