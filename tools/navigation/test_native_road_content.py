"""Exercise the road-import consumer on accepted V10 and three corrupted exports."""
from pathlib import Path
import argparse,json,struct,tempfile
from verify_native_road_terrain import inspect,ROOT
from verify_texture_grid_change import read

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
    wrp=ROOT/'tb/regional_foundation_v10/02_reopened_v10.wrp'
    asc=ROOT/'tests/regional_foundation_combined_v10/baltic_regional_foundation_v10.asc'
    digest='8e25fab25e8f0909fdda302ed4ba3db4c43884c523920f5ef3424db90780eb8b'
    positive=inspect(wrp,asc,digest);assert positive['status']=='PASS_NATIVE_ROAD_TERRAIN_CONTENT'
    baseline=read(wrp);raw=baseline['bytes'];records=[]
    with tempfile.TemporaryDirectory(prefix='native-consumer-negative-',dir=a.out.parent) as temporary:
        directory=Path(temporary);assert directory.resolve().is_relative_to(a.out.parent.resolve())
        variants=[]
        h=bytearray(raw);where=24+(700*2048+500)*4;struct.pack_into('<f',h,where,struct.unpack_from('<f',h,where)[0]+1)
        variants.append(('changed_native_height',h,'interior_heights_exact'))
        water=next(o for o in baseline['objects'] if o['name'].lower().startswith('baltic_water\\'))
        p=bytearray(raw);where=water['start']+40;struct.pack_into('<f',p,where,struct.unpack_from('<f',p,where)[0]+1)
        variants.append(('moved_water_object',p,'all_10161_water_bridge_objects_exact'))
        m=bytearray(raw);where=24+2048*2048*4;old=struct.unpack_from('<H',m,where)[0];new=2 if old!=2 else 1
        struct.pack_into('<H',m,where,new);variants.append(('changed_material_assignment',m,'all_material_bytes_exact'))
        for name,data,check in variants:
            path=directory/(name+'.wrp');path.write_bytes(data);report=inspect(path,asc,digest)
            rejected=report['status']=='FAIL_NATIVE_ROAD_TERRAIN_CONTENT' and not report['checks'][check]
            records.append(dict(name=name,rejected=rejected,failed_checks=[k for k,v in report['checks'].items() if not v]));assert rejected,name
    result=dict(status='PASS_ACCEPTED_NATIVE_V10_AND_THREE_NEGATIVES',positive=positive,negative_controls=records,
                limit='Consumer validation only; no road candidate has been imported by this test.')
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(status=result['status'],negative_controls=records)))

if __name__=='__main__':main()
