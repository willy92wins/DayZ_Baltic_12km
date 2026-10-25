"""Independent scope/physical review of the four approved Narva pond repairs."""
from pathlib import Path
import argparse
import json

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation
from shapely.geometry import shape

from audit_fairway_triangles_v30 import records,save,sha
from compare_water_design_v30 import sample_body
from v30_common import cell_planes,raster_vertices,vertex_plane_bounds

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path('E:/DayZ-Baltic-Build/v30-shore-finish-corrected/terrain_v30.npz')
SOURCE_SHA='73b01bb4a6e94e7659c51ae3fd274c72caeb408a11ee3a31560678ba98036dbd'
DESIGN_SHA='5060aa79f0898074055a217857c76d3f9953252cd850d840c8a55c6796ce764a'


def face_angles(h):
    nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    return (np.degrees(np.arctan(np.hypot(ne-nw,se-ne)/6)),
            np.degrees(np.arctan(np.hypot(sw-nw,se-sw)/6)))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists()
    design=ROOT/'tests/water_v3/water_v3.geojson'
    assert sha(SOURCE)==SOURCE_SHA and sha(design)==DESIGN_SHA
    old=np.load(SOURCE);new=np.load(a.candidate)
    oh,nh=old['heights'].astype(float),new['heights'].astype(float)
    changed=oh!=nh
    feats=json.loads(design.read_text())['features']
    envelope=np.zeros((2048,2048),bool);rows=[]
    op=cell_planes(old['cls'],old['level']);np_=cell_planes(new['cls'],new['level'])
    expected_classes=old['cls'].copy();expected_levels=old['level'].copy()
    for index in (98,376,408,409):
        geom=shape(feats[index]['geometry']);m=raster_vertices([geom]).astype(bool)
        envelope|=m
        # These selected polygons contain no protected engineered vertices;
        # prove it below, rather than trusting the author's saved mask.
        expected_classes[m]=7;expected_levels[m]=feats[index]['properties']['level_m']
        before=sample_body(geom,oh,op);after=sample_body(geom,nh,np_)
        rows.append(dict(index=index,before=before,after=after))
    nature=np.load(ROOT/'tests/regional_outline_v1/reference.npz')['reserve'].astype(bool)
    fixed=old['platform']|old['reserve']|nature
    corridors=[]
    for p in (ROOT/'evidence/v30-offline-followup-2026-10-02/corridors.geojson',
              ROOT/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson'):
        for f in json.loads(p.read_text())['features']:
            if f['properties'].get('kind','corridor24m')!='corridor24m':continue
            ids=np.unique(records(shape(f['geometry']),op)['ids'])
            corridors.append(dict(name=f['properties'].get('name',f['properties'].get('river')),
                                  identical=bool(np.array_equal(oh.ravel()[ids],nh.ravel()[ids]))))
            mask=np.zeros_like(fixed);mask.ravel()[ids]=True
            fixed|=binary_dilation(mask)
    pmin,pmax=vertex_plane_bounds(np_)
    changed_cells=~np.isclose(op,np_,equal_nan=True,atol=1e-8,rtol=0)
    corners=np.zeros_like(fixed)
    for dr in (0,1):
        for dc in (0,1):corners[dr:dr+2047,dc:dc+2047]|=changed_cells
    wet=corners&(new['cls']>0);dry=corners&(new['cls']==0)
    worsened=0;newsteep=0
    for oa,na in zip(face_angles(oh),face_angles(nh)):
        worsened+=int(((na>35.0001)&(na>oa+.0001)).sum())
        newsteep+=int(((na>35.0001)&(oa<=35.0001)).sum())
    checks=dict(nonempty=bool(changed.any()),finite=bool(np.isfinite(nh).all()),
                exact_class_scope=bool(np.array_equal(new['cls'],expected_classes)),
                exact_level_scope=bool(np.array_equal(new['level'],expected_levels,equal_nan=True)),
                exact_water_scope=bool(np.array_equal(new['water'],new['cls']>0)),
                no_height_change_outside_polygons=not bool((changed&~envelope).any()),
                narva_unchanged_outside_explicit_pond_exception=bool(np.array_equal(oh[old['narva']&~envelope],nh[old['narva']&~envelope])),
                all_engineering_and_nature_fixed=not bool((changed&fixed).any()),
                ponds_do_not_intersect_fixed_vertices=not bool((envelope&fixed).any()),
                water_corners_under_all_new_planes=bool(np.all(nh[wet]<=pmin[wet]-.05+1e-5)),
                dry_corners_above_all_new_planes=bool(np.all(nh[dry]>=pmax[dry]+.03-1e-5)),
                bounded_lowering_only=bool(np.all(nh<=oh) and (oh-nh).max()<=3),
                bed_floor_retained=bool(nh.min()>=-12),
                no_new_or_worsened_steep_faces=worsened==0,
                all_four_bodies_regain_water=all(r['after']['wet_fraction']['0.5']>r['before']['wet_fraction']['0.5'] for r in rows),
                channel_count_retained=len(corridors)==23,
                all_channel_vertices_fixed=all(r['identical'] for r in corridors))
    for k in old.files:
        if k not in ('heights','cls','level','water'):
            checks['unchanged_'+k]=bool(np.array_equal(old[k],new[k],equal_nan=True))
    with rasterio.open(a.candidate.parent/'baltic_terrain_v30.asc') as ds:
        checks['asc_exact']=bool(np.array_equal(ds.read(1),new['heights']))
        checks['asc_grid_exact']=ds.shape==(2048,2048) and ds.transform.a==6 and ds.transform.e==-6 and ds.bounds.left==200000 and ds.bounds.bottom==0
    result=dict(status='PASS_LOCAL_GEOMETRY' if all(checks.values()) else 'FAIL',checks=checks,
                candidate_sha256=sha(a.candidate),source_sha256=SOURCE_SHA,
                changed_vertices=int(changed.sum()),changed_plane_cells=int(changed_cells.sum()),
                new_steep_faces=newsteep,new_or_worsened_steep_faces=worsened,ponds=rows,corridors=corridors,
                limits=['The legacy full Narva-radius identity test should fail in these declared pond footprints; it has not been weakened.',
                        'Road consumer, regenerated assets, engine loading and navigation remain separate.',
                        'A positive water fraction does not establish complete shoreline or channel continuity.'])
    save(a.out,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('ponds','corridors')},indent=2))
    return 0 if all(checks.values()) else 1


if __name__=='__main__':raise SystemExit(main())
