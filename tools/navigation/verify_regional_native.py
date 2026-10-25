"""Verify a literal regional TB export against frozen ASC and native objects."""
import argparse
import json
import numpy as np
import rasterio
from prepare_regional_outline import ROOT,NATIVE,NATIVE_SHA,sha,save
from verify_regional_outline import read

p=argparse.ArgumentParser()
p.add_argument('--wrp',required=True,type=__import__('pathlib').Path)
p.add_argument('--out',required=True,type=__import__('pathlib').Path)
a=p.parse_args()
asc=ROOT/'tests/regional_outline_v3/baltic_regional_outline_v3.asc'
if sha(NATIVE)!=NATIVE_SHA or sha(asc)!='3e2f6a9643ba4a8c58a86534c75de6033b7dbdf7a3de5d09a5ea46ff66680ac6':
    raise ValueError('Frozen inputs changed')
old,new=read(NATIVE),read(a.wrp)
with rasterio.open(asc) as ds:
    expected=ds.read(1)
actual=np.frombuffer(new['heights'],dtype='<f4').reshape(2048,2048)[::-1]
before=np.frombuffer(old['heights'],dtype='<f4').reshape(2048,2048)[::-1]
changed=expected!=before
after_height=24+actual.size*4
key=lambda o:(o['name'],o['id'],o['matrix'])
checks={'all4194304heights_exact':bool(np.array_equal(actual,expected)),
        'all_untouched_vertices_native':bool(np.array_equal(actual[~changed],before[~changed])),
        'header_exact':old['bytes'][:24]==new['bytes'][:24],
        'material_grid_and_table_exact':old['bytes'][after_height:old['objects_start']]==new['bytes'][after_height:new['objects_start']],
        'all_object_records_exact':sorted(map(key,old['objects']))==sorted(map(key,new['objects']))}
report={'status':'PASS_NATIVE_EXPORT' if all(checks.values()) else 'FAIL','checks':checks,
        'wrp':str(a.wrp),'wrp_sha256':sha(a.wrp),'asc_sha256':sha(asc),'native_baseline_sha256':NATIVE_SHA,
        'differing_vertices':int(np.count_nonzero(actual!=expected)),
        'maximum_error_m':float(np.max(abs(actual.astype('float64')-expected))),
        'objects':new['objects'],
        'limits':['Does not itself prove reopening, compiled WRP, navmesh or runtime.']}
save(a.out,report)
print(json.dumps({k:v for k,v in report.items() if k!='objects'},indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
