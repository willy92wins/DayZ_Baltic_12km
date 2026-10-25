from pathlib import Path
import numpy as np,json
B=Path(__file__).parent;d=np.load(B/'solver-domain.npz');ref=json.loads((B/'verification.json').read_text())
xy=np.c_[d['cc'].ravel()*6,12282-d['rr'].ravel()*6];a,b=d['edge'].T
def energy(q):
    ds=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))];result=[]
    for phase in [0,.25,.5,.75]:
        at=np.arange(phase,ds[-1],1.);p=np.c_[np.interp(at,ds,q[:,0]),np.interp(at,ds,q[:,1])];v=np.diff(p,axis=0)
        result.append(float(np.sum(np.arctan2(abs(v[:-1,0]*v[1:,1]-v[:-1,1]*v[1:,0]),(v[:-1]*v[1:]).sum(1))**2)))
    return float(np.mean(result))
out=[]
for field,key in [('old','physical_before'),('after','physical_after')]:
    v=d[field].astype(np.float32).astype(float);f=(3.425-v[a])/(v[b]-v[a]);q=(xy[a]+f[:,None]*(xy[b]-xy[a]))[d['order']];raw=energy(q)
    for i,j in [(0,1),(-1,-2)]:
        target=12162.001;q[i]+=((target-q[i,0])/(q[j,0]-q[i,0]))*(q[j]-q[i])
    measured=ref[key]['one_metre_turn_square_mean'];trim=energy(q)
    out.append(dict(field=field,untrimmed=raw,trimmed=trim,consumer=measured,absolute_error=abs(trim-measured)))
assert max(v['absolute_error'] for v in out)<2e-6
result=dict(status='DOMAIN_MISMATCH_ISOLATED',mechanism='GEOS consumer removes a 1mm extent-boundary buffer; author used complete endpoint segments. Matching this exact interval removes discrepancy.',measurements=out)
(B/'domain-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
