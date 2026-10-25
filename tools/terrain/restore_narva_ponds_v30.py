"""Restore four approved ponds suppressed by the broad legacy Narva circle.

This is an explicit, local authoring exception to the radius protection, not a
change to the bridge/fairways/roads. Only polygon-interior grid vertices may
change. The candidate must pass the independent post-build consumer checks.
"""
from pathlib import Path
import argparse
import json

import numpy as np
import shapely
from shapely.geometry import shape

from audit_fairway_triangles_v30 import save, sha
from finish_shores_v30 import protect_corridors
from v30_common import cell_planes, grid_xz, raster_vertices, vertex_plane_bounds

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path('E:/DayZ-Baltic-Build/v30-shore-finish-corrected/terrain_v30.npz')
EXPECTED='73b01bb4a6e94e7659c51ae3fd274c72caeb408a11ee3a31560678ba98036dbd'
INDICES=(98,376,408,409)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--source',type=Path,default=SOURCE)
    ap.add_argument('--source-sha',default=EXPECTED)
    ap.add_argument('--design',type=Path,default=ROOT/'tests/water_v3')
    ap.add_argument('--nature',type=Path,default=ROOT/'tests/regional_outline_v1/reference.npz')
    a=ap.parse_args()
    assert not a.out.exists()
    if a.source_sha!='any':assert sha(a.source)==a.source_sha
    design=a.design/'water_v3.geojson'
    feats=json.loads(design.read_text(encoding='utf-8'))['features']
    t=np.load(a.source);old=t['heights'].astype(float)
    h=old.copy();cls=t['cls'].copy();level=t['level'].copy()
    planes=cell_planes(cls,level)
    _,channel_margin,_,_=protect_corridors(planes)
    nature=np.load(a.nature)['reserve'].astype(bool)
    fixed=channel_margin|t['platform']|t['reserve']|nature
    xx,zz=grid_xz();allowed=np.zeros_like(cls,dtype=bool)
    details=[]
    for index in INDICES:
        f=feats[index];prop=f['properties'];g=shape(f['geometry'])
        assert prop['class']=='pond' and g.is_valid
        footprint=raster_vertices([g]).astype(bool)
        # Preserve already present non-pond water and engineered vertices.
        mutable=footprint&~fixed&np.isin(cls,(0,7))
        assert mutable.any(), (index,'No mutable polygon-interior vertex')
        dist=shapely.distance(shapely.points(xx[mutable],zz[mutable]),g.boundary)
        depth=np.clip(.20+.12*dist,.20,1.20)
        target=float(prop['level_m'])-depth
        h[mutable]=np.minimum(h[mutable],target)
        cls[mutable]=7;level[mutable]=float(prop['level_m'])
        allowed|=mutable
        details.append(dict(index=index,osm_id=prop['osm_id'],name=prop.get('name',''),
                            design_level_m=prop['level_m'],vector_area_m2=g.area,
                            footprint_vertices=int(footprint.sum()),mutable_vertices=int(mutable.sum()),
                            protected_vertices=int((footprint&fixed).sum())))
    newplanes=cell_planes(cls,level)
    pmin,pmax=vertex_plane_bounds(newplanes)
    h[allowed]=np.minimum(h[allowed],pmin[allowed]-.1001)
    candidate=h.astype('float32')
    changed=candidate!=t['heights']
    assert not (changed&~allowed).any() and not (changed&fixed).any()
    assert changed.any() and float((old-candidate).max())<=3.0 and candidate.min()>=-12
    # A new piece may cover neighbouring dry corners. Never create a plane
    # above those corners, and do not raise unrelated ground to hide a conflict.
    plane_change=~np.isclose(planes,newplanes,equal_nan=True,atol=1e-8,rtol=0)
    edge=np.zeros_like(cls,dtype=bool)
    for dr in (0,1):
        for dc in (0,1):edge[dr:dr+2047,dc:dc+2047]|=plane_change
    dry=(cls==0)&edge
    assert np.all(candidate[dry]>=pmax[dry]+.03-1e-5), 'New water covers existing dry ground'
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out/'terrain_v30.npz',**{k:(candidate if k=='heights' else cls if k=='cls'
                        else level if k=='level' else cls>0 if k=='water' else t[k]) for k in t.files})
    with (a.out/'baltic_terrain_v30.asc').open('x',encoding='ascii',newline='\n') as stream:
        stream.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(stream,candidate,fmt='%.9g')
    np.savez_compressed(a.out/'pond_repair_masks.npz',allowed=allowed,changed=changed,
                        fixed=fixed,plane_change=plane_change)
    report=dict(status='BUILT_PENDING_GROUPED_GATES',source_sha256=a.source_sha if a.source_sha!='any' else sha(a.source),
                candidate_sha256=sha(a.out/'terrain_v30.npz'),asc_sha256=sha(a.out/'baltic_terrain_v30.asc'),
                changed_vertices=int(changed.sum()),new_water_vertices=int(((t['cls']==0)&(cls==7)).sum()),
                changed_plane_cells=int(plane_change.sum()),max_cut_m=float((old-candidate).max()),ponds=details,
                inputs={str(p):sha(p) for p in (a.source,design,Path(__file__),
                        Path(cell_planes.__code__.co_filename),Path(protect_corridors.__code__.co_filename))},
                limits=['The old radius-480m identity gate intentionally differs only inside the four approved polygon footprints.',
                        'Water pieces, satellite, native sources and navmesh must be regenerated before engine use.',
                        'No claim of full vector coverage or continuous water on shapes narrower than the 6m grid.'])
    save(a.out/'build.json',report)
    print(json.dumps(report,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
