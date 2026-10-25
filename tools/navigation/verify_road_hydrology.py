"""Independent water-cell identity and protected-land planes after road grading."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine
from shapely.geometry import shape
from verify_foundation_islands import minimum_margin
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def audit(folder,heights=None,outline_v33_parent=False):
    parentfile=ROOT/('tests/regional_outline_smoothing_v33/reference.npz' if outline_v33_parent else 'tests/regional_foundation_combined_v10/reference.npz')
    if outline_v33_parent:assert sha(parentfile)=='8e84d5ce38da8863116c52ecdf9953d5b201a097459513054eea8e0f0e14c45a'
    manifest=json.loads((folder/'solve.json').read_text(encoding='utf-8'))
    assert sha(parentfile)==manifest['source_npz_sha256']
    parent=np.load(parentfile);base=parent['candidate'];candidate=np.load(folder/'reference.npz')
    asc=next(folder.glob('*.asc'))
    with rasterio.open(asc) as ds:h=ds.read(1) if heights is None else heights
    assert h.shape==base.shape and np.isfinite(h).all()
    sources={'water-surfaces-contour-v2.geojson':'df860f693a1bf0115cb4af65a13cea5f8006a5a21bc9bca1d88276b83802ccdc','ocean-game.json':'c72aaafd6ee35abfcdec180135571e34b9c5eaefb42d3bca1bfbabad6493f757'}
    polygons=[]
    for name,digest in sources.items():
        p=EV/name;assert sha(p)==digest,name
        polygons.extend(shape(f['geometry']) for f in json.loads(p.read_text(encoding='utf-8'))['features'])
    watercells=rasterize([(p,1) for p in polygons],out_shape=(2047,2047),transform=Affine(6,0,0,0,-6,12282),all_touched=True,dtype='uint8').astype(bool)
    changed=h!=base
    affected=changed[:-1,:-1]|changed[:-1,1:]|changed[1:,:-1]|changed[1:,1:]
    wet=parent['wet']|parent['ocean'];fairway=parent['fairway_support']
    unchanged_keys=[k for k in parent.files if k not in ['candidate','changed']]
    # Inherited original arrays (including classification and water levels) must
    # remain identical. A new candidate's parent is checked separately.
    unchanged_keys=[k for k in unchanged_keys if k not in ['parent','pilot_support','pilot_allowed']]
    checks=dict(water_native_cells_exact=not bool(np.any(watercells&affected)),wet_vertices_exact=not bool(np.any(wet&changed)),fairway_vertices_exact=not bool(np.any(fairway&changed)),unchanged_source_arrays=all(k in candidate.files and np.array_equal(candidate[k],parent[k],equal_nan=True) for k in unchanged_keys))
    land_source=EV/'protected-islands-game.json';support_source=EV/'island-support-v7.json'
    assert sha(land_source)=='ebc453b8e3b2b95e5f7846d4fba890f69fbbd43f323547780ab41404ed4ffaef'
    assert sha(support_source)=='e51eda3310cf1ee2b5bde588ec60ec89b750ccb73372a3274315d7ea7addff61'
    features=json.loads(land_source.read_text(encoding='utf-8'))['features'];levels=json.loads(support_source.read_text(encoding='utf-8'))['islands']
    assert len(features)==len(levels)==283
    islands=[]
    for i,(f,water) in enumerate(zip(features,levels)):
        g=shape(f['geometry']);level=water['adjacent_water_ceiling_m']
        shore,ns=minimum_margin(h,g,level);core,nc=minimum_margin(h,g.buffer(-6),level+.35)
        p=g.representative_point();r=(12282-p.y)/6;c=p.x/6;ri,ci=int(r),int(c);a,b=c-ci,r-ri
        y=(h[ri,ci]*(1-a)+h[ri,ci+1]*(a-b)+h[ri+1,ci+1]*b) if b<=a else (h[ri,ci]*(1-b)+h[ri+1,ci]*(b-a)+h[ri+1,ci+1]*a)
        ok=shore>=-1e-5 and (not nc or core>=-1e-5) and y>=level+.35-1e-5
        islands.append(dict(index=i,passed=bool(ok),shore_margin_m=shore,core_margin_m=core if nc else None,representative_freeboard_m=float(y-level),shore_vertices=ns,core_vertices=nc))
    checks['protected_land_planes']=all(x['passed'] for x in islands)
    reserve_source=ROOT/'tests/regional_outline_v3/reference.npz'
    assert sha(reserve_source)=='b5ca00409f0814285c82a1fe6688fe49719574eadde415de08443ffedcbc574d'
    reserve=np.load(reserve_source)['reserve'].astype(bool)
    dryreserve=reserve&~wet
    checks['reserve_dry_classification_preserved']=bool(np.all(h[dryreserve]>=np.minimum(base[dryreserve],1.4)-1e-5))
    records=dict(status='PASS_OFFLINE_HYDROLOGY_AND_PROTECTED_LAND' if all(checks.values()) else 'FAIL_HYDROLOGY_OR_PROTECTED_LAND',checks=checks,asc_sha256=sha(asc),source_hashes={**sources,'protected-islands-game.json':sha(land_source),'island-support-v7.json':sha(support_source),'reserve':sha(reserve_source)},water_polygons=len(polygons),water_native_cells=int(watercells.sum()),changed_water_cells=int(np.sum(watercells&affected)),islands=islands,reserve=dict(dry_vertices=int(dryreserve.sum()),dry_area_grid_km2=float(dryreserve.sum()*36/1e6),changed_vertices=int(np.sum(reserve&changed)),maximum_delta_m=float(np.max(abs(h[reserve]-base[reserve])))),limits=['Offline height geometry only; native persistence, navmesh, rendering and physics require separate acceptance.','Reserve footprint and dry ground preserved; no trees placed by this terrain operation.'])
    return records

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--outline-v33-parent',action='store_true');a=ap.parse_args();assert not a.out.exists()
    r=audit(a.folder,outline_v33_parent=a.outline_v33_parent);r['outline_v33_parent']=a.outline_v33_parent;a.out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k!='islands'}));raise SystemExit(0 if r['status'].startswith('PASS_') else 1)

if __name__=='__main__':main()
