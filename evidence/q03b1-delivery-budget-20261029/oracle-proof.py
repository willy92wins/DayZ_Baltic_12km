"""Integrator check of frozen literal data only, not a reader implementation."""
from pathlib import Path
import json,hashlib,io,struct,sys
import numpy as np
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');P=R/'q03b1-reader-inputs-20261029/oracle.json'
raw=P.read_bytes();assert hashlib.sha256(raw).hexdigest()=='79b946237ff06dfc414cb47fbee38063a6eedf66af784a0ea2b769fc7d8e18f9'
o=json.loads(raw);assert np.__version__=='2.5.3'
rows=[]
for f in o['fixtures']:
    for major in [1,2]:
        for limit in ([None,16384] if f['id']=='signed' else [None]):
            body=f['header_dictionary'].encode('latin1')
            header=body+b' '*((limit if limit else len(body)+1)-len(body)-1)+b'\n'
            prefix=bytes.fromhex(o['npy_prefixes'][f'{major}.0_magic_version_hex'])+struct.pack('<H' if major==1 else '<I',len(header))
            expected=bytes.fromhex(f['payload_hex'])
            a=np.lib.format.read_array(io.BytesIO(prefix+header+expected),allow_pickle=False,max_header_size=16384)
            assert list(a.shape)==f['schema']['shape'] and a.tobytes(order='C')==expected
            if f['id']=='meta':
                assert [list(v) for v in a.dtype.descr]==f['schema']['dtype']
                assert [a.dtype.fields[n][1] for n in a.dtype.names]==f['expected_offsets'] and a.dtype.itemsize==35
            else:
                assert a.dtype.str==f['schema']['dtype']
                values=f['expected_values']
                if f['id']=='matrix':values=[x for row in values for x in row]
                for actual,value in zip(a.flat,values,strict=True):
                    if value=='-0.0':assert actual==0 and np.signbit(actual)
                    else:assert actual==value
            rows.append({'id':f['id'],'version':[major,0],'header_bytes':len(header),'payload_bytes':len(expected),'status':'LITERAL_MATCH'})
result={'status':'ORACLE_LITERALS_VERIFIED_ONLY','rows':rows,'count':len(rows),'oracle_sha256':hashlib.sha256(raw).hexdigest(),'numpy':np.__version__,'runtime':sys.version,'reader_implemented':False,'real_npz_opened':0,'map_modified':False}
out=Path(sys.argv[1]);out.parent.mkdir(exist_ok=False,parents=True);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'count':len(rows),'status':result['status']}))
