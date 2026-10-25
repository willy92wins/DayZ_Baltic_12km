"""Compare numerical derivatives before/after a rigid coordinate translation."""
from pathlib import Path
import ast,json
import numpy as np
B=Path(__file__).parent
source=(B/'solve.py').read_text();tree=ast.parse(source)
stop=next(i for i,node in enumerate(tree.body) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='metric' for t in node.targets))
def model(local):
    n={'__file__':str(B/'solve.py'),'__name__':'derivative_model'}
    exec(compile(ast.Module(body=tree.body[:stop],type_ignores=[]),str(B/'solve.py'),'exec'),n)
    if local:
        offset=np.array([n['c0']*6,12282-n['r1']*6]);n['xy']-=offset
        fn=next(a for a in tree.body if isinstance(a,ast.FunctionDef) and a.name=='contour')
        code=ast.unparse(fn).replace('lo = np.array([c0 * 6 + 0.001, 12282 - r1 * 6 + 0.001])','lo = np.array([0.001, 0.001])').replace('hi = np.array([c1 * 6 - 0.001, 12282 - r0 * 6 - 0.001])','hi = np.array([(c1-c0)*6-0.001, (r1-r0)*6-0.001])')
        assert '12282' not in code
        exec(code,n)
    return n
terrain=np.load(B/'candidate/terrain.npz')['heights']
outputs=[]
for local in [False,True]:
    n=model(local);x=terrain[n['rr'],n['cc']].astype(float).ravel()[n['free']]
    fun=lambda a:n['energies'](n['values'](a))
    base=fun(x);cols=[];coarse=[];fine=[]
    for k in range(len(x)):
        a=x.copy();a[k]+=1.4901161193847656e-8;cols.append((fun(a)-base)/1.4901161193847656e-8)
        a=x.copy();b=x.copy();a[k]+=1e-5;b[k]-=1e-5;coarse.append((fun(a)-fun(b))/2e-5)
        a=x.copy();b=x.copy();a[k]+=1e-6;b[k]-=1e-6;fine.append((fun(a)-fun(b))/2e-6)
    forward=np.array(cols);central=np.array(fine);reference=np.array(coarse)
    outputs.append(dict(local_coordinates=local,energy=base.tolist(),forward_vs_central_max=float(abs(forward-central).max()),forward_vs_central_l2=float(np.linalg.norm(forward-central)),central_stability_max=float(abs(reference-central).max()),central_stability_l2=float(np.linalg.norm(reference-central))))
report=dict(no_new_optimizer_run=True,comparisons=outputs)
(B/'derivative-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
