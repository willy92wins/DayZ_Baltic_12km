"""Compare a native road-grading export to its ASC and accepted V10 objects/materials."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
import rasterio
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from verify_texture_grid_change import read
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def inspect(wrp,asc,expected_sha):
    baseline=ROOT/'tb/regional_foundation_v10/02_reopened_v10.wrp'
    assert sha(baseline)=='cdd6838f522a5b66b729db7c6bda39b0a5a41eb256fb26804eb39f5479ef905a'
    assert sha(asc)==expected_sha
    with rasterio.open(asc) as ds:
        expected=ds.read(1)
        assert ds.width==2048 and ds.height==2048 and ds.res==(6.,6.) and tuple(ds.bounds)==(200000.,0.,212288.,12288.)
    old,new=read(baseline),read(wrp)
    actual=np.frombuffer(new['heights'],dtype='<f4').reshape(2048,2048)[::-1]
    delta=abs(expected.astype(float)-actual)
    material_start=24+expected.size*4
    canonical=lambda obj:(obj['id'],obj['name'].lower(),obj['matrix'])
    checks=dict(header_exact=old['bytes'][:24]==new['bytes'][:24],
        interior_heights_exact=bool(np.array_equal(expected[:-1,:-1],actual[:-1,:-1])),
        terminal_heights_bounded_1micrometre=bool(np.isfinite(actual).all() and np.max(delta)<=1e-6),
        all_material_bytes_exact=old['bytes'][material_start:old['objects_start']]==new['bytes'][material_start:new['objects_start']],
        all_object_ids_unique=len({o['id'] for o in new['objects']})==len(new['objects']),
        all_10161_water_bridge_objects_exact=len(new['objects'])==10161 and sorted(map(canonical,old['objects']))==sorted(map(canonical,new['objects'])))
    return dict(status='PASS_NATIVE_ROAD_TERRAIN_CONTENT' if all(checks.values()) else 'FAIL_NATIVE_ROAD_TERRAIN_CONTENT',
        checks=checks,wrp=str(wrp),wrp_sha256=sha(wrp),asc=str(asc),asc_sha256=expected_sha,
        baseline_wrp_sha256=sha(baseline),maximum_height_error_m=float(delta.max()),
        limits=['Content of one export. Real save/close/reopen provenance and a second matching export are separate.',
                'Does not accept compiled WRP, new navmesh, rendered pixels or runtime driving.'])

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--wrp',type=Path,required=True);ap.add_argument('--asc',type=Path,required=True)
    ap.add_argument('--asc-sha256',required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists();result=inspect(a.wrp,a.asc,a.asc_sha256)
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));raise SystemExit(0 if result['status'].startswith('PASS_') else 1)

if __name__=='__main__':main()
