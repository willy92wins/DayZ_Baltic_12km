"""Frozen consumer gate for literal full native exports of the regional base."""
from pathlib import Path
import argparse,hashlib,json,struct,sys
import numpy as np
import rasterio
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
sys.path.insert(0,str(ROOT/'tools/playtest'))
from verify_texture_grid_change import read
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--wrp',required=True,type=Path);ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--terrain-only',action='store_true');ap.add_argument('--terrain-version',choices=['v4','v8','v9'],default='v9');a=ap.parse_args()
    assert not a.out.exists(),'Preserve prior evidence'
    baseline=ROOT/'tb/regional_outline_v3/baltic_regional_persisted_v3.wrp'
    asc=ROOT/f'tests/regional_foundation_combined_{a.terrain_version}/baltic_regional_foundation_{a.terrain_version}.asc'
    assert sha(baseline)=='9bf50853799764571d4c3a7ce87c17583019af149bed93ac1e73f2c91c7c8c68'
    assert sha(asc)=={'v4':'e305b35fd8b89373de8303fb4b874f7822623e7516ddca0c4dd8d50f231c0816',
                     'v8':'3ff3f7739d57cd7e8eee6524cd39a41782fc65ec4bc9903d88362b560860eea1',
                     'v9':'335554a6ea06f8546eeac5444aec7597eaf45df18be0c69b0baab48a573947b2'}[a.terrain_version]
    old,new=read(baseline),read(a.wrp)
    with rasterio.open(asc) as ds:expected=ds.read(1)
    actual=np.frombuffer(new['heights'],dtype='<f4').reshape(2048,2048)[::-1]
    start=24+expected.size*4
    bridges=[o for o in new['objects'] if not o['name'].lower().startswith('baltic_water\\')]
    key=lambda o:(o['name'].lower(),o['id'],o['matrix'])
    checks={'all_heights_exact':bool(np.array_equal(expected,actual)),
            'header_exact':old['bytes'][:24]==new['bytes'][:24],
            'material_grid_and_table_exact':old['bytes'][start:old['objects_start']]==new['bytes'][start:new['objects_start']],
            'original_bridges_exact':sorted(map(key,old['objects']))==sorted(map(key,bridges))}
    mismatches=[];maximum=0.;count=0
    if not a.terrain_only:
        asset=json.loads((EV/'regional-water-assets-verification-v2.json').read_text())
        assert asset['status']=='PASS_OFFLINE_MODELS_AND_PLACEMENT'
        expected_objects=asset['native_objects'];count=len(expected_objects)
        actual_groups={};expected_groups={}
        for obj in new['objects']:
            if not obj['name'].lower().startswith('baltic_water\\'):continue
            matrix=struct.unpack('<12f',bytes.fromhex(obj['matrix']))
            assert list(matrix[:9])==[1,0,0,0,1,0,0,0,1],obj
            actual_groups.setdefault(obj['name'].lower(),[]).append(matrix[9:])
        for obj in expected_objects:expected_groups.setdefault(obj['model'].lower(),[]).append(obj['native_position'])
        checks['all_water_models_present']=set(actual_groups)==set(expected_groups)
        for name,positions in expected_groups.items():
            seen=actual_groups.get(name,[])
            if len(seen)!=len(positions):mismatches.append({'model':name,'expected_count':len(positions),'actual_count':len(seen)});continue
            distances,indices=cKDTree(np.asarray(positions,dtype='float32')).query(seen)
            maximum=max(maximum,float(distances.max()))
            if distances.max()>.001 or len(set(indices))!=len(positions):
                mismatches.append({'model':name,'maximum_position_error_m':float(distances.max()),'unique_matches':len(set(indices)),'count':len(positions)})
        checks['all_water_poses_within_1mm']=not mismatches
        checks['object_count_exact']=len(new['objects'])==3+count
    report={'status':'PASS_NATIVE_EXPORT' if all(checks.values()) else 'FAIL','terrain_only':a.terrain_only,'checks':checks,
            'wrp':str(a.wrp),'wrp_sha256':sha(a.wrp),'asc_sha256':sha(asc),'differing_vertices':int((expected!=actual).sum()),
            'maximum_height_error_m':float(abs(expected.astype('float64')-actual).max()),
            'water_objects':count,'maximum_pose_error_m':maximum,'pose_mismatches':mismatches,
            'limits':['Requires reopened export, compiled parity and runtime consumers before acceptance.']}
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    raise SystemExit(0 if all(checks.values()) else 1)
if __name__=='__main__':main()
