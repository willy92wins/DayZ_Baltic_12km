"""Exercise the real CLI against saved exports and explicit binary mutations.

Consumer: the native gate used by prepare_foundation_package.py. Fixtures here
are test inputs only, never native exports or deployable terrain. See the
bounded scope in plans/overnight-2026-10-01.md, step 2.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

import numpy as np
import rasterio

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from verify_texture_grid_change import read


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',required=True,type=Path)
    args=parser.parse_args()
    args.evidence.mkdir(parents=True,exist_ok=False)
    fixtures=args.evidence/'fixtures';fixtures.mkdir()
    current=ROOT/'tb/regional_foundation_v1/baltic_foundation_bridges_v9.wrp'
    baseline=ROOT/'tb/regional_outline_v3/baltic_regional_persisted_v3.wrp'
    first=ROOT/'tb/regional_foundation_v1/baltic_foundation_heights_v9.wrp'
    asc=ROOT/'tests/regional_foundation_combined_v9/baltic_regional_foundation_v9.asc'
    native,old=read(current),read(baseline)
    data=native['bytes'];rows=2048
    objects={obj['id']:obj for obj in native['objects']}
    def save(name,payload):
        path=fixtures/(name+'.wrp');path.write_bytes(payload);return path
    def float_change(name,offset,value):
        payload=bytearray(data);struct.pack_into('<f',payload,offset,value)
        return save(name,payload)
    def offset(row,col):return 24+4*((rows-1-row)*rows+col)
    def following_float(byte_offset):
        value=np.float32(struct.unpack_from('<f',data,byte_offset)[0])
        return float(np.nextafter(value,np.float32(np.inf)))
    west=objects[16777218]['start'];centre=objects[16777216]['start']
    cases=[('strict_current',current,'strict',False,False),
           ('bounded_current',current,'native-v9-micrometre',True,False),
           ('old_world',baseline,'native-v9-micrometre',False,False),
           ('displaced_bridges',first,'native-v9-micrometre',False,False)]
    exact=bytearray(data)
    with rasterio.open(asc) as ds:expected=ds.read(1)
    exact[24:24+expected.size*4]=expected[::-1].astype('<f4').tobytes()
    for obj in old['objects']:
        start=objects[obj['id']]['start'];exact[start:start+48]=bytes.fromhex(obj['matrix'])
    cases.append(('synthetic_exact_control',save('synthetic_exact_control',exact),'strict',True,False))
    edge=offset(158,2047)
    cases.append(('edge_1mm',float_change('edge_1mm',edge,float(expected[158,2047])+.001),'native-v9-micrometre',False,False))
    r,c=np.argwhere(np.abs(expected[1:-1,1:-1])<1)[0]+1
    interior=offset(int(r),int(c))
    cases.append(('interior_one_ulp',float_change('interior_one_ulp',interior,following_float(interior)),'native-v9-micrometre',False,False))
    cases.append(('west_y_1mm',float_change('west_y_1mm',west+40,struct.unpack_from('<f',data,west+40)[0]+.001),'native-v9-micrometre',False,False))
    cases.append(('central_y_one_ulp',float_change('central_y_one_ulp',centre+40,following_float(centre+40)),'native-v9-micrometre',False,False))
    cases.append(('bridge_x_one_ulp',float_change('bridge_x_one_ulp',west+36,following_float(west+36)),'native-v9-micrometre',False,False))
    cases.append(('bridge_rotation',float_change('bridge_rotation',west+4,.001),'native-v9-micrometre',False,False))
    cases.append(('nonfinite_bridge',float_change('nonfinite_bridge',west+40,float('nan')),'native-v9-micrometre',False,False))
    material=bytearray(data);mi=24+2048*2048*4
    original=struct.unpack_from('<H',material,mi)[0]
    struct.pack_into('<H',material,mi,1 if original!=1 else 2)
    cases.append(('material_change',save('material_change',material),'native-v9-micrometre',False,False))
    duplicate=bytearray(data);struct.pack_into('<I',duplicate,west+48,16777216)
    cases.append(('duplicate_id',save('duplicate_id',duplicate),'native-v9-micrometre',False,False))
    cases.append(('truncated',save('truncated',data[:-20]),'native-v9-micrometre',False,False))
    cases.append(('missing_water_full_scope',current,'native-v9-micrometre',False,True))
    results=[]
    gate=ROOT/'tools/navigation/verify_foundation_native.py'
    for name,path,contract,accepted,full in cases:
        output=args.evidence/(name+'.json')
        command=[sys.executable,str(gate),'--wrp',str(path),'--out',str(output),'--precision-contract',contract]
        if not full:command.append('--terrain-only')
        result=subprocess.run(command,capture_output=True)
        (args.evidence/(name+'.log')).write_bytes(result.stdout+result.stderr)
        report=json.loads(output.read_text()) if output.exists() else None
        actual=result.returncode==0 and report is not None and report['status']=='PASS_NATIVE_EXPORT'
        matched=actual==accepted
        if name=='bounded_current':matched=matched and report['strict_status']=='FAIL'
        if name=='strict_current':matched=matched and report['precision_contract']=='strict'
        results.append({'case':name,'expected_accepted':accepted,'actual_accepted':actual,
                        'matched':matched,'exit_code':result.returncode,
                        'fixture_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        print(name+': '+('PASS' if matched else 'FAIL'),flush=True)
    summary={'status':'PASS_CONTROLS' if all(r['matched'] for r in results) else 'FAIL_CONTROLS',
             'gate_sha256':hashlib.sha256(gate.read_bytes()).hexdigest(),
             'tests':results,'limits':['Controls of the verifier; not persistence, water integration or runtime acceptance.']}
    (args.evidence/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    raise SystemExit(0 if summary['status']=='PASS_CONTROLS' else 1)


if __name__=='__main__':main()
