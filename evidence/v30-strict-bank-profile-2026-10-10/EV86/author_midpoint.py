"""EV86 single half-gradient-preserving profile; no solve or parameter search."""
from pathlib import Path
import hashlib,json
import numpy as np
O=Path(__file__).parent;R=O.parent
BP=R/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
RP=R/'v30-coupled-shore-pilot-20261010/quantized-repair/candidate-terrain.npz'
LP=R/'v30-coupled-shore-feasibility-20261010/feasibility.json'
EXPECTED={BP:'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 RP:'a4434bf7812e1e35299901e93c653f04472f343bcdb93ff3d2c9080c1b61e196',
 LP:'38250740c9fc4cfb22515e0dec488e1719b2ac481069b68dab4ac6e4d0cba587'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def order_gate(b,r,h):
    db=float(b[0])-float(b[1]);dr=float(r[0])-float(r[1]);dh=float(h[0])-float(h[1])
    source_ok=(db*dr>=0) and (db!=0 or dr==0)
    strict_ok=(db*dh>0) if db else dh==0
    exact=np.asarray(b,dtype=np.float64)+(np.asarray(r,dtype=np.float64)-np.asarray(b,dtype=np.float64))/2
    error=sum(abs(float(h[i])-float(exact[i])) for i in (0,1))
    retained=abs(dh)+error>=abs(db)/2
    return source_ok,strict_ok,retained,error

def fixtures():
    b=np.asarray([1.,3.,1.],dtype=np.float32);r=np.ones(3,dtype=np.float32);h=(b.astype(float)+(r-b.astype(float))/2).astype(np.float32)
    assert list(h)==[1.,2.,1.]
    assert all(all(order_gate(b[i:i+2],r[i:i+2],h[i:i+2])[:3]) for i in (0,1))
    assert not order_gate([3.,1.],[0.,2.],[1.5,1.5])[0] # A direction with a new V is invalid.
    assert all(order_gate([2.,2.],[1.,1.],[1.5,1.5])[:3])
    tiny=np.nextafter(np.float32(1.),np.float32(np.inf))
    # A half-ULP slope may quantize to a tie; the exact gate must reject it.
    b=np.asarray([tiny,1.],dtype=np.float32);r=np.asarray([1.,1.],dtype=np.float32)
    h=((b.astype(float)+r.astype(float))/2).astype(np.float32)
    assert not order_gate(b,r,h)[1]
    assert 1.<= (1.+2.)/2 <=2.
    return {'status':'PASS','positive':['summit remains sloped','B tie preserved','convex bounds'],
            'negative':['invalid reversed direction','float32 midpoint tie']}

def main():
    fixture=fixtures();ids={str(p):sha(p) for p in EXPECTED}
    assert all(ids[str(p)]==v for p,v in EXPECTED.items())
    with np.load(BP) as z:arrays={k:z[k] for k in z.files}
    b=arrays['heights'];r=np.load(RP)['heights'];d=json.loads(LP.read_text())
    vars={tuple(q['vertex']) for q in d['scalar_delta_bounds']};edges=set()
    for row,col in vars:
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr or dc:edges.add(tuple(sorted(((row,col),(row+dr,col+dc)))))
    assert len(vars)==39 and len(edges)==220
    assert {tuple(v) for v in np.argwhere(r!=b)}<=vars
    h=b.copy();exact={}
    for v in vars:
        exact[v]=float(b[v])+(float(r[v])-float(b[v]))/2;h[v]=np.float32(exact[v])
    failures=[];ratios=[]
    for u,v in edges:
        g=order_gate([b[u],b[v]],[r[u],r[v]],[h[u],h[v]])
        if not all(g[:3]):failures.append({'edge':[u,v],'source_order':g[0],'strict_order':g[1],'retention':g[2]})
        if b[u]!=b[v]:ratios.append(abs((float(h[u])-float(h[v]))/(float(b[u])-float(b[v]))))
    for q in d['scalar_delta_bounds']:
        v=tuple(q['vertex']);delta=float(h[v])-float(b[v]);lo,hi=q['delta_bounds']
        if not lo<=delta<=hi:failures.append({'vertex':v,'bounds':[lo,hi],'delta':delta})
    focus_deltas=[float(h[v])-float(b[v]) for v in ((1880,191),(1785,366))]
    if not all(x<=-.1 for x in focus_deltas):failures.append('focus descent')
    changed={tuple(v) for v in np.argwhere(h!=b)}
    if not changed<=vars or np.any(h>b):failures.append('scope or no-raise')
    report={'status':'FAIL_AUTHOR' if failures else 'AUTHORED_PENDING_INDEPENDENT_CONSUMER',
            'inputs':ids,'script_sha256':sha(Path(__file__)),'plan_sha256':sha(O/'plan.md'),
            'fixtures':fixture,'coefficient':.5,'order_edges':len(edges),'variables':len(vars),
            'changed':len(changed),'focus_deltas_m':focus_deltas,
            'minimum_final_slope_retention':min(ratios),'failures':failures}
    if not failures:
        out=O/'candidate-terrain.npz'
        if out.exists():raise RuntimeError('candidate exists; no replacement/retry')
        arrays['heights']=h;np.savez_compressed(out,**arrays);report['candidate_sha256']=sha(out)
    (O/'authoring-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
