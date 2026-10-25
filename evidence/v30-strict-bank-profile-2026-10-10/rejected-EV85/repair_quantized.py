"""Single explicit EV85-R isotonic float32 correction. Never reruns SLSQP."""
from pathlib import Path
import hashlib,json
import numpy as np

O=Path(__file__).parent; R=O.parent; OUT=O/'quantized-repair'
BP=R/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
DP=O/'diagnostic-vector.npz'
LP=R/'v30-coupled-shore-feasibility-20261010/feasibility.json'
EXPECTED={BP:'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
          DP:'e3b6389586c88b7028f156bab7f8fc10b7f3503c91479aef3032672880b1861e',
          LP:'38250740c9fc4cfb22515e0dec488e1719b2ac481069b68dab4ac6e4d0cba587'}
LIMIT=1e-4
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def inward(lo,hi):
    assert np.isfinite(lo) and np.isfinite(hi)
    lower=np.float32(lo); upper=np.float32(hi)
    if float(lower)<lo: lower=np.nextafter(lower,np.float32(np.inf))
    if float(upper)>hi: upper=np.nextafter(upper,np.float32(-np.inf))
    if not (lo<=float(lower)<=float(upper)<=hi):
        raise ValueError('no float32 value in interval')
    return lower,upper

def project(base, diagnostic, intervals, edges, variables, limit=LIMIT):
    """Dictionaries keyed by vertices; all fixed vertices have point intervals."""
    nodes=set(base); assert nodes==set(diagnostic)==set(intervals)
    parent={v:v for v in nodes}
    def find(v):
        while parent[v]!=v:
            parent[v]=parent[parent[v]];v=parent[v]
        return v
    for u,v in edges:
        if base[u]==base[v]:
            a,b=find(u),find(v)
            if a!=b:parent[max(a,b)]=min(a,b)
    groups={}
    for v in sorted(nodes):groups.setdefault(find(v),[]).append(v)
    vertex_group={v:g for g,vs in groups.items() for v in vs}
    lower={};upper={};values={};levels={};pred={g:set() for g in groups}
    for g,vs in groups.items():
        levels[g]=float(base[vs[0]])
        assert all(float(base[v])==levels[g] for v in vs)
        inward_bounds=[inward(*intervals[v]) for v in vs]
        lower[g]=max(p[0] for p in inward_bounds)
        upper[g]=min(p[1] for p in inward_bounds)
        if lower[g]>upper[g]:raise ValueError('empty group interval')
        values[g]=np.float32(max([lower[g]]+[diagnostic[v] for v in vs]))
    for u,v in edges:
        a,b=vertex_group[u],vertex_group[v]
        if a==b:continue
        if levels[a]>levels[b]:a,b=b,a
        assert levels[a]<levels[b]
        pred[b].add(a)
    for g in sorted(groups,key=lambda g:(levels[g],g)):
        values[g]=np.float32(max([values[g]]+[values[p] for p in pred[g]]))
        if values[g]>upper[g]:raise ValueError('propagation above upper bound')
    result={v:values[vertex_group[v]] for v in nodes}
    for v,z in result.items():
        if v not in variables and z!=base[v]:raise ValueError('fixed vertex moved')
        if z>base[v]:raise ValueError('above B')
        if not intervals[v][0]<=float(z)<=intervals[v][1]:raise ValueError('outside original bounds')
        correction=float(z)-float(diagnostic[v])
        if correction<0 or correction>limit:raise ValueError('correction limit exceeded')
    for u,v in edges:
        a=float(base[u])-float(base[v]);b=float(result[u])-float(result[v])
        if (a>0 and b<0) or (a<0 and b>0) or (a==0 and b!=0):raise ValueError('order failure')
    return result,{'groups':len(groups),'directed_edges':sum(map(len,pred.values()))}

def fixtures():
    # Variable following a lexicographically earlier fixed low neighbour.
    result,_=project({0:1.,1:2.},{0:np.float32(1.),1:np.float32(.999999)},
                     {0:(1.,1.),1:(.9,2.)},[(0,1)],{1})
    assert result[1]==1.
    result,_=project({0:1.,1:2.,2:3.},{0:np.float32(1.),1:np.float32(.999999),2:np.float32(.999998)},
                     {0:(1.,1.),1:(.8,2.),2:(.8,3.)},[(0,1),(1,2)],{1,2})
    assert all(x==1. for x in result.values())
    result,_=project({0:2.,1:2.,2:3.},{0:np.float32(1.5),1:np.float32(1.500001),2:np.float32(1.6)},
                     {0:(1.,2.),1:(1.2,1.8),2:(1.,3.)},[(0,1),(1,2)],{0,1,2})
    assert result[0]==result[1] and result[2]>=result[1]
    lo,hi=inward(1.00000001,1.0000003)
    assert 1.00000001<=float(lo)<=float(hi)<=1.0000003
    negatives=[]
    def reject(name,fn):
        try:fn()
        except ValueError:negatives.append(name)
        else:raise AssertionError('fixture did not reject '+name)
    reject('unrepresentable interval',lambda:inward(1.00000001,1.00000002))
    reject('upper bound propagation',lambda:project({0:1.,1:2.},{0:np.float32(1.),1:np.float32(.9)},
                 {0:(1.,1.),1:(.8,.99)},[(0,1)],{1}))
    reject('correction limit',lambda:project({0:1.,1:2.},{0:np.float32(1.),1:np.float32(.9)},
                 {0:(1.,1.),1:(.8,2.)},[(0,1)],{1}))
    # A tie with a fixed vertex pins its group exactly to B.
    result,_=project({0:2.,1:2.},{0:np.float32(2.),1:np.float32(1.999999)},
                     {0:(2.,2.),1:(1.,2.)},[(0,1)],{1})
    assert result[0]==result[1]==2.
    return {'status':'PASS','positive':['fixed earlier','three level chain','connected equality','directed rounding','fixed equality group'],
            'negatives_rejected':negatives}

def main():
    fixture=fixtures(); ids={str(p):sha(p) for p in EXPECTED}
    assert all(ids[str(p)]==s for p,s in EXPECTED.items())
    with np.load(BP) as f:arrays={k:f[k] for k in f.files}
    B=arrays['heights']; D=np.load(DP)['heights']; info=json.loads(LP.read_text())
    vertices={tuple(q['vertex']) for q in info['scalar_delta_bounds']}; edges=set()
    for r,c in vertices:
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr or dc:edges.add(tuple(sorted(((r,c),(r+dr,c+dc)))))
    assert len(vertices)==39 and len(edges)==220
    nodes=set(v for e in edges for v in e); base={v:B[v] for v in nodes}; diagnostic={v:D[v] for v in nodes}
    intervals={v:(float(B[v]),float(B[v])) for v in nodes}
    for q in info['scalar_delta_bounds']:
        v=tuple(q['vertex']);a,b=q['delta_bounds'];intervals[v]=(float(B[v])+a,float(B[v])+b)
    out,meta=project(base,diagnostic,intervals,sorted(edges),vertices)
    candidate=B.copy()
    for v in vertices:candidate[v]=out[v]
    assert candidate.dtype==np.float32
    changed={tuple(v) for v in np.argwhere(candidate!=B)}
    assert changed<=vertices
    assert all(float(candidate[v])-float(B[v])<=-.1 for v in ((1880,191),(1785,366)))
    assert candidate[1786,366]==B[1786,366]
    trace=[{'vertex':v,'B':float(B[v]),'diagnostic':float(D[v]),'repaired':float(candidate[v]),
            'correction_m':float(candidate[v])-float(D[v]),'bounds':intervals[v]} for v in sorted(vertices)]
    # Proves the unrepaired diagnostic actually triggers the exact order gate.
    original_failures=sum((float(B[u])-float(B[v]))*(float(D[u])-float(D[v]))<0 for u,v in edges)
    assert original_failures==12
    OUT.mkdir(exist_ok=True); path=OUT/'candidate-terrain.npz'
    if path.exists():raise RuntimeError('repair candidate already exists; do not overwrite/retry')
    arrays['heights']=candidate;np.savez_compressed(path,**arrays)
    report={'status':'REPAIR_AUTHORED_PENDING_FULL_INDEPENDENT_CONSUMER',
            'original_solver_status':'SOLVER_FAILED unchanged','inputs':ids,
            'script_sha256':sha(Path(__file__)),'plan_sha256':sha(O/'quantized-repair-plan.md'),
            'fixtures':fixture,'order_edges':len(edges),'original_order_failures':original_failures,
            'variables':len(vertices),'changed_vertices':len(changed),'dag':meta,
            'max_correction_m':max(q['correction_m'] for q in trace),
            'focus_deltas':[float(candidate[v])-float(B[v]) for v in ((1880,191),(1785,366))],
            'candidate_sha256':sha(path),'trace':trace}
    (OUT/'repair-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in ('status','changed_vertices','max_correction_m','focus_deltas','candidate_sha256')}))

if __name__=='__main__':main()
