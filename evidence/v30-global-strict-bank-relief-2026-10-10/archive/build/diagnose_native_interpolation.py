"""Read-only compare native samples to independently written interpolation formulas."""
from pathlib import Path
import hashlib,json,csv
import numpy as np
R=Path(__file__).parent
ref=json.loads((R/'native-reference.json').read_text())
H=np.load(R/'candidate/terrain.npz')['heights'].astype(np.float64)
points=[s.split(';') for s in (R/'native-snapshot.log').read_text().splitlines() if s.startswith('P;')]
risks=list(csv.reader((Path(ref['local_mission'])/'risks.csv').open(),delimiter=';'))
records=[]
for i,(q,p,rr) in enumerate(zip(ref['points'],points,risks)):
 # Mission parses coordinate strings into single-precision float arguments.
 x,z=map(float,(np.float32(rr[1]),np.float32(rr[2])))
 col=x/6;row=(12282-z)/6;c=int(np.floor(col));r=int(np.floor(row));u=col-c;v=row-r
 nw,ne,sw,se=H[r,c],H[r,c+1],H[r+1,c],H[r+1,c+1]
 nwd=nw+u*(ne-nw)+v*(se-ne) if u>=v else nw+v*(sw-nw)+u*(se-sw)
 ned=nw+u*(ne-nw)+v*(sw-nw) if u+v<=1 else se+(1-u)*(sw-se)+(1-v)*(ne-se)
 bilinear=(1-u)*(1-v)*nw+u*(1-v)*ne+(1-u)*v*sw+u*v*se
 actual=float(p[2]);expected=q['expected_ground']
 records.append({'index':i,'x':x,'z':z,'row':r,'col':c,'u':u,'v':v,'vertices':[nw,ne,sw,se],
  'actual':actual,'reference':expected,'reference_error':abs(actual-expected),'NWSE':nwd,'NESW':ned,'bilinear':bilinear,
  'error_NWSE':abs(actual-nwd),'error_NESW':abs(actual-ned),'error_bilinear':abs(actual-bilinear)})
bad=[q for q in records if q['reference_error']>.001]
out={'status':'READONLY_NATIVE_INTERPOLATION_DIAGNOSIS','snapshot_sha256':hashlib.sha256((R/'native-snapshot.log').read_bytes()).hexdigest(),
 'counts':{'all':len(records),'reference_mismatches':len(bad)},
 'models':{name:{'max_error_all':max(q['error_'+name] for q in records),'mismatches_all':sum(int(q['error_'+name]>.001) for q in records),'max_error_failed_points':max(q['error_'+name] for q in bad)} for name in ('NWSE','NESW','bilinear')},'bad_reference_points':bad}
(R/'native-interpolation-diagnosis.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='bad_reference_points'},indent=2))
print(json.dumps([{k:q[k] for k in ('index','actual','reference','NWSE','NESW','bilinear')} for q in bad],indent=2))
