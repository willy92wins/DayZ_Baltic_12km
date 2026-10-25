"""Bounded deterministic Neva delta repair. See plans/v30-delta-fairways.md.

Immutable V30/Luga source; create-only candidate and evidence. The native
24 m corridor is audited independently of the distance-based carving rule.
"""
from pathlib import Path
import argparse
import json
import sys

import numpy as np
import rasterio
import shapely
from scipy.ndimage import label, distance_transform_edt
from shapely.geometry import shape, mapping

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/water'))
from water_common import read_shp
from v30_common import cell_planes, grid_xz
from audit_fairway_triangles_v30 import records, describe, controls, sha, save

SOURCE = Path('E:/DayZ-Baltic-Build/v30-fairway-candidate-bounded/terrain_v30.npz')
SOURCE_SHA = '1117b4b11b38e9369ea8ad7179cd3bbbde0517e19a714968357b25fc166b36e0'
AXES = ROOT/'evidence/v30-shore-pilot-2026-10-02/delta-audit/axes-corridors.geojson'
CORE = 12.0 + np.hypot(6.0, 6.0)
REACH = 36.0
BED = -2.55
SLOPE = .60


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--evidence',type=Path,required=True)
    ap.add_argument('--source',type=Path,default=SOURCE)
    ap.add_argument('--source-sha',default=SOURCE_SHA)
    ap.add_argument('--axes',type=Path,default=AXES)
    args=ap.parse_args()
    assert not args.out.exists() and not args.evidence.exists(), 'Fresh directories required'
    if args.source_sha!='any':assert sha(args.source)==args.source_sha, 'Source drift'
    t=dict(np.load(args.source)); h=t['heights'].astype(float)
    axes=[(shape(f['geometry']),f['properties']['branch']) for f in json.loads(args.axes.read_text())['features'] if f['properties']['kind']=='axis']
    source_lines=read_shp('rivers',{'river','canal'})
    connectors=[(g,p) for g,p in source_lines if p['osm_id'] in {'way/34348577','way/78518216'}]
    assert len(connectors)==2
    axes += [(g,p['name']+' '+p['osm_id']) for g,p in connectors]
    # All four original source lines must form one connected network.
    joined=shapely.union_all([g for g,_ in axes]).buffer(.001)
    assert joined.geom_type=='Polygon', 'OSM axes do not join'
    network=shapely.union_all([g for g,_ in axes])
    x,z=grid_xz(); bounds=network.bounds
    local=(x>=bounds[0]-REACH)&(x<=bounds[2]+REACH)&(z>=bounds[1]-REACH)&(z<=bounds[3]+REACH)
    dist=np.full(h.shape,np.inf)
    dist[local]=shapely.distance(shapely.points(x[local],z[local]),network)
    active=dist<=REACH
    target=BED + SLOPE*np.maximum(dist-CORE,0.)
    new=np.where(active,np.minimum(h,target),h)
    # Dry banks retain the approved 1.40 m tide freeboard. New wet vertices
    # have >=.101 m clearance at nominal .75 m, accounting for float32.
    land=~t['water']
    gained=land & active & (target <= .649)
    protected_land=land & ~gained
    new[protected_land]=np.maximum(new[protected_land],np.minimum(h[protected_land],1.4))
    # Approved phase 2 reserves new wet road crossings for future bridges.
    # Freeze every platform outside a reserve and every dry approach vertex.
    reserve_bed=t['reserve'] & (t['water']|gained)
    fixed=t['narva'] | ((t['platform']|t['reserve']) & ~reserve_bed)
    new[fixed]=h[fixed]
    gained &= ~fixed
    new=new.astype('float32')
    changed=new!=t['heights']
    assert not np.any(changed & fixed), 'Protected infrastructure conflict'
    assert not np.any(changed & ~active)
    assert np.all(new[changed]<=t['heights'][changed]) and np.min(new)>=-12.
    # No foreign pond level or water model may change in this sea-level repair.
    assert not np.any(changed & (t['level']>.8)), 'Raised water conflict'
    candidate={k:v.copy() for k,v in t.items()}
    candidate['heights']=new
    candidate['cls'][gained]=4
    candidate['level'][gained]=.75
    candidate['water']=candidate['cls']>0
    candidate['beach'][gained]=False
    before_planes=cell_planes(t['cls'],t['level'])
    after_planes=cell_planes(candidate['cls'],candidate['level'])
    assert np.array_equal(before_planes,after_planes,equal_nan=True), 'Pond pieces need regeneration'
    # Island cores: dry components and their maximum-inscribed grid point,
    # not a self-defined water corridor. Existing components must survive.
    lb,nb=label(h>=1.,structure=np.ones((3,3)))
    la,na=label(new>=1.,structure=np.ones((3,3)))
    shore_dist=distance_transform_edt(h>=1.)*6.
    affected=np.unique(lb[changed & (lb>0)])
    island_reports=[]
    for ident in affected:
        mask=lb==ident
        anchor=int(np.argmax(np.where(mask,shore_dist,-1)))
        assert new.ravel()[anchor]==h.ravel()[anchor], 'Dry component core changed'
        survivor=mask & (new>=1.)
        assert survivor.any(), 'Dry component disappeared'
        is_main=bool(mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any())
        island_reports.append(dict(before_component=int(ident),touches_map_edge=is_main,
             before_vertices=int(mask.sum()),after_vertices=int(survivor.sum()),
             surviving_components=int(len(np.unique(la[survivor]))),
             core_xz=[float(x.ravel()[anchor]),float(z.ravel()[anchor])],core_unchanged=True))
    reports=[]; features=[]
    for line,name in axes:
        corridor=line.buffer(12,cap_style='round',join_style='round',quad_segs=32)
        rec=records(corridor,after_planes)
        reports.append(dict(name=name,length_m=line.length,before=describe(h,rec),after=describe(new.astype(float),rec),controls=controls(new.astype(float),rec)))
        features.extend([dict(type='Feature',properties=dict(name=name,kind=kind),geometry=mapping(geom)) for kind,geom in [('axis',line),('corridor24m',corridor)]])
    assert all(r['after']['failing_faces']==0 for r in reports), 'Delta fairway depth failure'
    args.out.mkdir(parents=True); args.evidence.mkdir(parents=True)
    np.savez_compressed(args.out/'terrain_v30.npz',**candidate)
    asc=args.out/'baltic_terrain_v30.asc'
    with asc.open('x',encoding='ascii',newline='\n') as f:
        f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(f,new,fmt='%.9g')
    with rasterio.open(asc) as ds: assert np.array_equal(ds.read(1).astype('float32'),new)
    rr,cc=np.nonzero(changed)
    changes=[dict(row=int(r),col=int(c),x=int(c*6),z=int(12282-r*6),before=float(h[r,c]),after=float(new[r,c]),class_before=int(t['cls'][r,c]),class_after=int(candidate['cls'][r,c])) for r,c in zip(rr,cc)]
    report=dict(status='PASS_LOCAL_DEPTH_AND_INVARIANTS',
      inputs={str(p):sha(p) for p in [args.source,args.axes,ROOT/'source/vectors/rivers.shp',ROOT/'source/vectors/rivers.dbf',Path(__file__)]},
      outputs={str(p):sha(p) for p in [args.out/'terrain_v30.npz',asc]},
      params=dict(useful_width_m=24.,sea_min_m=.5,bed_m=BED,core_radius_m=CORE,bank_grade=SLOPE,reach_m=REACH),
      changed_vertices=int(changed.sum()),new_water_vertices=int(gained.sum()),max_lowering_m=float((h-new)[changed].max()),
      bounds_xz=[float(x[changed].min()),float(z[changed].min()),float(x[changed].max()),float(z[changed].max())],
      invariants=dict(outside_scope_identical=True,platform_outside_reserve_identical=True,dry_reserve_approaches_identical=True,narva_identical=True,pond_planes_identical=True,asc_float32_roundtrip=True),
      reserved_crossing=dict(changed_vertices=int((changed&t['reserve']).sum()),dry_platform_to_water_vertices=int((gained&t['platform']&t['reserve']).sum()),
                            limitation='Future bridge reserve in the Neva trunk; no bridge or drivable crossing added.'),
      dry_components_before=int(nb),dry_components_after=int(na),affected_land_components=island_reports,
      corridors=reports,changes=changes,
      limitations=['Pending global terrain and road gates, tide contours, source-island review, compiled-world/runtime and new navmesh.',
                   'Connected source axes and exact useful-depth corridors do not prove physical boat control or mouth-to-open-sea traversal.'])
    save(args.evidence/'candidate.json',report)
    save(args.evidence/'axes-corridors.geojson',dict(type='FeatureCollection',features=features))
    print(json.dumps({k:v for k,v in report.items() if k not in ('changes','inputs','outputs')}))


if __name__=='__main__':main()
