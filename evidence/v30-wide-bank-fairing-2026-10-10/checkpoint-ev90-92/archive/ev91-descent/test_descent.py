"""Fixtures for actual descent matrix and quantized witness predicate, no solver."""
from pathlib import Path
import hashlib,json
import numpy as np
from author_ev91 import descent_constraints,witnesses_hold

r,c=np.indices((9,9));b=(10+r+.25*c).astype(np.float32)
nodes=[(4,4),(3,3)]
C,d,w,e,centers=descent_constraints(b,nodes)
x=np.asarray([b[p] for p in nodes],dtype=float)
assert np.all(C@x>=d) and witnesses_hold(b,w)
assert any(t['center'] not in [list(z) for z in nodes] and t['witness'] in [list(z) for z in nodes] for t in w)
for trial in (np.asarray([100.,100.]),np.asarray([-100.,-100.]),np.asarray([14.,13.])):
    h=b.copy()
    for p,v in zip(nodes,trial):h[p]=v
    assert bool(np.all(C@trial>=d))==witnesses_hold(h,w)
pit=b.copy();pit[4,4]=-3.
_,_,wp,ep,_=descent_constraints(pit,[(4,4)])
assert [4,4] in ep
flat=np.ones((9,9),dtype=np.float32)
cf,df,wf,ef,_=descent_constraints(flat,[(4,4),(4,5)])
assert not ef and witnesses_hold(flat,wf) and np.all(cf@np.ones(2)>=df)
wrong=flat.copy();wrong[4,4]=np.nextafter(np.float32(1),np.float32(-np.inf))
assert not witnesses_hold(wrong,wf)
cycle=np.full((9,9),2.,dtype=np.float32);cycle[4,4]=cycle[4,5]=1.
cc,dc,wc,ec,_=descent_constraints(cycle,[(4,4),(4,5)])
links={tuple(t['center']):tuple(t['witness']) for t in wc}
assert links[(4,4)]==(4,5) and links[(4,5)]==(4,4)
assert np.all(cc@np.ones(2)>=dc) and witnesses_hold(cycle,wc)
broken=cycle.copy();broken[4,4]=np.nextafter(np.float32(1),np.float32(-np.inf))
assert not witnesses_hold(broken,wc)
out={'status':'PASS_DESCENT_FIXTURES_ONLY','cases':['variable_and_fixed_centers',
     'linear_rows_agree_with_direct_heights','baseline_minimum_exempt','flat_equalities_feasible',
     'one_ulp_strict_minimum_rejected','two_vertex_cycle_requires_equality'],
     'author_sha256':hashlib.sha256(Path(__file__).with_name('author_ev91.py').read_bytes()).hexdigest()}
Path(__file__).with_name('fixtures.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out))
