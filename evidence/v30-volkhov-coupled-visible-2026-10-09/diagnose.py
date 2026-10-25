"""Read the saved iterate without running another optimization."""
from pathlib import Path
import ast,json
import numpy as np
B=Path(__file__).parent
source=(B/'solve.py').read_text()
tree=ast.parse(source)
stop=next(i for i,node in enumerate(tree.body) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='metric' for t in node.targets))
namespace={'__file__':str(B/'solve.py'),'__name__':'diagnostic_model'}
exec(compile(ast.Module(body=tree.body[:stop],type_ignores=[]),str(B/'solve.py'),'exec'),namespace)
n=namespace
terrain=np.load(B/'candidate/terrain.npz')['heights']
v=terrain[n['rr'],n['cc']].astype(float).ravel();free=n['free'];x=v[free]
def jacobian(fn):
    cols=[]
    for k in range(len(x)):
        a=x.copy();b=x.copy();a[k]+=1e-5;b[k]-=1e-5
        cols.append((fn(n['values'](a))-fn(n['values'](b)))/2e-5)
    return np.asarray(cols).T
ja=jacobian(n['areas']);sv=np.linalg.svd(ja,compute_uv=False)
e=n['energies'](v);a=n['areas'](v)
report=dict(saved_iterate_only=True,no_new_optimizer_run=True,area_jacobian_singular_values=sv.tolist(),area_jacobian_row_difference_max=float(abs(ja[0]-ja[1]).max()),area_jacobian_row_norms=np.linalg.norm(ja,axis=1).tolist(),area_residual=(a-n['target']).tolist(),energy_remaining_slack=(.9*n['reference']-1e-4-e).tolist(),corner_remaining_slack=float(n['amax']-n['angles'](v).max()),hinge_remaining_slack=float(n['hinge_limit']-n['hinge_square'](v)),slope_remaining_slack=float((n['limit']-n['slopes'](v)).min()),bounds_remaining_slack=float(min((x-n['lower']).min(),(n['upper']-x).min())),jacobian_rank=int(np.linalg.matrix_rank(ja,tol=1e-7)),max_physical_visible_node_level_difference=float(abs(n['wp']-n['wf']).max()))
np.savez_compressed(B/'diagnostic-jacobian.npz',area_jacobian=ja,free_vertex_ids=n['gids'].ravel()[free],areas=a,target=n['target'])
(B/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
