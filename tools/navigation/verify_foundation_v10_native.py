"""Read a complete V10 export against frozen terrain, water and bridge sources."""
from pathlib import Path
import argparse,hashlib,json,struct,sys
import numpy as np
import rasterio
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from verify_texture_grid_change import read
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def inspect(path):
    asc=ROOT/'tests/regional_foundation_combined_v10/baltic_regional_foundation_v10.asc'
    base=ROOT/'tb/regional_outline_v3/baltic_regional_persisted_v3.wrp'
    assert sha(asc)=='8e25fab25e8f0909fdda302ed4ba3db4c43884c523920f5ef3424db90780eb8b'
    assert sha(base)=='9bf50853799764571d4c3a7ce87c17583019af149bed93ac1e73f2c91c7c8c68'
    bridge_ref=ROOT/'tests/narva_bridge_v10/reference.json'
    assert sha(bridge_ref)=='3845bcf4b2aef06ad222105fdccebf07184e8f28b8183d8631f0284006a53a86'
    design=json.loads(bridge_ref.read_text())
    assert design['deck_m']==11 and len(design['objects'])==9
    with rasterio.open(asc) as ds:expected=ds.read(1)
    old,new=read(base),read(path)
    actual=np.frombuffer(new['heights'],dtype='<f4').reshape(2048,2048)[::-1]
    delta=abs(expected.astype(float)-actual)
    material_start=24+expected.size*4
    checks={
        'header_exact':old['bytes'][:24]==new['bytes'][:24],
        'interior_heights_exact':bool(np.array_equal(expected[:-1,:-1],actual[:-1,:-1])),
        'terminal_heights_bounded_1micrometre':bool(np.isfinite(actual).all() and np.max(delta)<=1e-6),
        'material_grid_and_table_exact':old['bytes'][material_start:old['objects_start']]==new['bytes'][material_start:new['objects_start']],
        'all_object_ids_unique':len({o['id'] for o in new['objects']})==len(new['objects']),
        'expected_total_objects':len(new['objects'])==10161,
    }
    original={o['id']:o for o in old['objects']}
    bridges=[o for o in new['objects'] if not o['name'].lower().startswith('baltic_water\\')]
    remaining={o['id']:o for o in bridges};bridge_fail=[];bridge_max_error=0.
    for desired in design['objects']:
        if desired['existing_id'] is not None:
            observed=remaining.pop(desired['existing_id'],None)
            if observed is None:bridge_fail.append({'offset':desired['offset_m'],'reason':'original ID missing'});continue
            b0=bytes.fromhex(original[observed['id']]['matrix']);b1=bytes.fromhex(observed['matrix'])
            check=b0[:40]==b1[:40] and b0[44:]==b1[44:]
            check=check and abs(struct.unpack_from('<f',b1,40)[0]-struct.unpack_from('<f',b0,40)[0]-2)<=1e-6
        else:
            if not remaining:bridge_fail.append({'offset':desired['offset_m'],'reason':'new span missing'});continue
            def distance(obj):return np.linalg.norm(np.array(struct.unpack('<12f',bytes.fromhex(obj['matrix']))[9:])-desired['native_xyz'])
            observed=min(remaining.values(),key=distance);remaining.pop(observed['id'])
            matrix=np.array(struct.unpack('<12f',bytes.fromhex(observed['matrix'])))
            error=float(distance(observed));bridge_max_error=max(bridge_max_error,error)
            check=error<=.001 and bool(np.max(abs(matrix[:9]-desired['native_rotation']))<=1e-7)
        check=check and observed['name'].lower()==desired['model'].lower()
        if not check:bridge_fail.append({'offset':desired['offset_m'],'id':observed['id'],'reason':'pose/model mismatch'})
    checks['nine_bridge_poses']=len(bridges)==9 and not remaining and not bridge_fail
    water_ref=ROOT/'evidence/regional-foundation-v1/regional-water-assets-verification-v2.json'
    assert sha(water_ref)=='a46e885f5c19f7a0476811675e07da6152e9a11065c4f95845a6bf2671648d7a'
    water=json.loads(water_ref.read_text());assert water['status']=='PASS_OFFLINE_MODELS_AND_PLACEMENT'
    expected_groups={};actual_groups={};water_fail=[];water_max=0.
    for obj in water['native_objects']:expected_groups.setdefault(obj['model'].lower(),[]).append(obj['native_position'])
    for obj in new['objects']:
        if not obj['name'].lower().startswith('baltic_water\\'):continue
        m=struct.unpack('<12f',bytes.fromhex(obj['matrix']))
        if list(m[:9])!=[1,0,0,0,1,0,0,0,1]:water_fail.append({'id':obj['id'],'reason':'nonidentity water rotation/scale'})
        actual_groups.setdefault(obj['name'].lower(),[]).append(m[9:])
    checks['water_models_exact']=set(expected_groups)==set(actual_groups)
    for name,positions in expected_groups.items():
        seen=actual_groups.get(name,[])
        if len(seen)!=len(positions):water_fail.append({'model':name,'reason':'count mismatch'});continue
        distances,indices=cKDTree(np.asarray(positions,dtype='float32')).query(seen)
        water_max=max(water_max,float(np.max(distances)))
        if np.max(distances)>.001 or len(set(indices))!=len(positions):water_fail.append({'model':name,'reason':'pose mismatch'})
    checks['all_10152_water_poses']=not water_fail and sum(map(len,actual_groups.values()))==10152
    return dict(status='PASS_NATIVE_V10_CONTENT' if all(checks.values()) else 'FAIL',checks=checks,wrp=str(path),wrp_sha256=sha(path),asc_sha256=sha(asc),bridge_reference_sha256=sha(bridge_ref),water_reference_sha256=sha(water_ref),all_heights_exact=bool(np.array_equal(expected,actual)),maximum_height_error_m=float(np.max(delta)),new_bridge_maximum_pose_error_m=bridge_max_error,bridge_mismatches=bridge_fail,water_maximum_pose_error_m=water_max,water_mismatches=water_fail,limits=['Individual export only. Actual save/reopen and exact canonical persistence remain required.','No compiled, navigation, collision or runtime acceptance.'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--wrp',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve previous evidence')
    report=inspect(a.wrp);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['status']=='PASS_NATIVE_V10_CONTENT' else 1)

if __name__=='__main__':main()
