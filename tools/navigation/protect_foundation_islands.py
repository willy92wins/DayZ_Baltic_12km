"""Make the native triangles covering protected islands dry, including small ones.

Raster vertex masks alone miss islands smaller than a cell. Rasterize intersected
cells, constrain their four vertices, then propagate the existing slope envelope.
This preserves the vector coastline and water models; possible bank displacement
is bounded and must pass the independent fairway/road consumers again.
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine
from shapely import STRtree, polygons, intersection, area
from shapely.geometry import shape
from smooth_foundation_shore_pair import majorant
from waterway_common import sample

ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',default='v7');args=ap.parse_args()
    OUT=ROOT/f'tests/regional_foundation_combined_{args.version}'
    assert not OUT.exists(),'Fresh candidate required'
    ref=np.load(ROOT/'tests/regional_foundation_combined_v4/reference.npz')
    h=ref['candidate'];base=ref['base']
    features=json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features']
    water=[shape(f['geometry']) for f in features]
    levels=np.array([f['properties']['level_m'] for f in features]);tree=STRtree(water)
    islands=json.loads((EV/'protected-islands-game.json').read_text())['features']
    lower=np.full(h.shape,-1000.,dtype='float32');body_reports=[]
    for number,feature in enumerate(islands):
        geo=shape(feature['geometry'])
        nearby=tree.query(geo.buffer(6),predicate='intersects')
        level=max(1.,float(levels[nearby].max()) if len(nearby) else 1.)
        target=level+.35
        cells=rasterize([(geo,1)],out_shape=(2047,2047),transform=Affine(6,0,0,0,-6,12282),all_touched=True,dtype='uint8').astype(bool)
        support=np.zeros(h.shape,bool)
        rr,cc=np.nonzero(cells);x=cc*6;z=12282-rr*6
        a=np.c_[x,z];b=np.c_[x+6,z];c=np.c_[x,z-6];d=np.c_[x+6,z-6]
        # Native NW-SE diagonal: preserve precisely the triangles touching land.
        # Constraining the other half of every cell made one Neva sample shallow
        # in rejected v6, although its triangle did not intersect an island.
        first=area(intersection(polygons(np.stack([a,b,d],axis=1)),geo))>1e-9
        second=area(intersection(polygons(np.stack([a,d,c],axis=1)),geo))>1e-9
        for mask,offsets in [(first,[(0,0),(0,1),(1,1)]),(second,[(0,0),(1,1),(1,0)])]:
            for dr,dc in offsets:support[rr[mask]+dr,cc[mask]+dc]=True
        lower[support]=np.maximum(lower[support],target)
        p=geo.representative_point();x,z=p.x,p.y
        body_reports.append(dict(index=number,area_m2=geo.area,adjacent_water_ceiling_m=level,target_m=target,
                                 probe_xz=[x,z],previous_y=float(sample(h,x+200000,z)),baseline_y=float(sample(base,x+200000,z)),
                                 constrained_vertices=int(support.sum())))
    # Propagate only the new island lower bound. Reprocessing the accepted h
    # itself accumulated float32 noise on fixed road vertices in rejected v5.
    island_envelope,history=majorant(np.maximum(lower,float(h.min())))
    candidate=np.maximum(h,island_envelope)
    fixed=ref['road_fixed_vertices']
    fixed_delta=abs(candidate.ravel()[fixed]-h.ravel()[fixed])
    checks={'road_vertices_unchanged':bool(np.array_equal(candidate.ravel()[fixed],h.ravel()[fixed])),
            'all_island_support_vertices_above_target':bool(np.all(candidate>=lower))}
    for record in body_reports:
        x,z=record['probe_xz'];record['candidate_y']=float(sample(candidate,x+200000,z))
    checks['all_protected_representatives_dry']=all(r['candidate_y']>=r['target_m']-.00001 for r in body_reports)
    report=dict(status='ISLAND_SUPPORT_PREPARED_NOT_FULLY_VERIFIED' if all(checks.values()) else 'FAIL',checks=checks,
                protected_count=len(body_reports),prior_representatives_below_local_target=sum(r['previous_y']<r['target_m']-.00001 for r in body_reports),
                baseline_representatives_below_local_target=sum(r['baseline_y']<r['target_m']-.00001 for r in body_reports),
                changed_vertices_from_v4=int((candidate!=h).sum()),max_raise_m=float((candidate-h).max()),
                max_road_vertex_delta_m=float(fixed_delta.max()),envelope_iterations=len(history),islands=body_reports,
                limits=['Requires independent road/depth/slope gates, native export and engine checks.',
                        'Intersected native cells may widen a bank outside the reference polygon; no vector water outline was changed.'])
    if all(checks.values()):
        OUT.mkdir(parents=True)
        asc=OUT/f'baltic_regional_foundation_{args.version}.asc'
        with asc.open('w',encoding='ascii',newline='\n') as f:
            f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
            np.savetxt(f,candidate,fmt='%.9g')
        with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),candidate)
        data={k:ref[k] for k in ref.files};data.update(candidate=candidate,changed=candidate!=base,island_support=lower>-1000,island_minimum=lower)
        np.savez_compressed(OUT/'reference.npz',**data)
        report['asc_sha256']=hashlib.sha256(asc.read_bytes()).hexdigest()
    (EV/f'island-support-{args.version}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='islands'},indent=2))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__=='__main__':main()
