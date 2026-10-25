from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.optimize import linprog,LinearConstraint
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/terrain'))
import repair_free_shapes_ev112 as solver
report=json.loads((R/'guarded-relief-batch-e/report.json').read_text())
failed={r['cluster'] for r in report['clusters'] if r['status']=='SOLVER_FAILED'}
current={};results=[];out=R/'guarded-e-residual-feasibility'
def diagnose(fun,x0,**kwargs):
    linear=[x for x in kwargs['constraints'] if isinstance(x,LinearConstraint)]
    assert len(linear)==1 and np.isneginf(linear[0].lb).all()
    lp=linprog(np.zeros(len(x0)),A_ub=linear[0].A,b_ub=linear[0].ub,bounds=kwargs['bounds'],method='highs')
    result=dict(cluster=current['cluster'],variables=len(x0),linear_rows=len(linear[0].ub),linear_witness_feasible=bool(lp.success),lp_status=int(lp.status),message=lp.message)
    np.savez_compressed(out/f'cluster-{current["cluster"]}.npz',x0=x0,A=linear[0].A,b=linear[0].ub,bounds=np.asarray(kwargs['bounds']),lp_solution=lp.x if lp.success else np.empty(0))
    if lp.success:result['nonlinear_minimum']=[float(x['fun'](lp.x).min()) for x in kwargs['constraints'] if isinstance(x,dict)]
    results.append(result)
    raise ValueError('DIAGNOSTIC_ONLY_NO_AUTHOR_SOLUTION')
solver.minimize=diagnose
src=W/'tools/terrain/repair_guarded_shapes_ev112.py';text=src.read_text(encoding='utf-8')
needle='    for ident,sl0 in enumerate(find_objects(clusters),1):'
assert text.count(needle)==1
text=text.replace(needle,needle+'\n        if ident not in DIAG_FAILED:continue\n        DIAG_CURRENT["cluster"]=ident')
tail='    h=h.astype(np.float32);changed=h!=h0.astype(np.float32);'
assert text.count(tail)==1
text=text[:text.index(tail)]+'    raise SystemExit(0)\n\nif __name__=="__main__":main()\n'
sys.argv=[str(src),str(R/'combined-merged'),str(R/'guarded-relief-discovery'),str(out),
 '--expected-terrain-sha256',report['input_sha256'],'--expected-domains-sha256',report['domains_sha256'],
 '--retain-candidate',str(R/'guarded-relief-batch-e'),'--expected-retained-sha256',report['output_sha256'],
 '--expected-retained-domains-sha256','272a4138c18d0d7c55882bd67b4574250a783635b1a11f81778edbf4fa37242d','--hybrid-witnesses']
scope=dict(__name__='__main__',__file__=str(src),DIAG_FAILED=failed,DIAG_CURRENT=current)
try:exec(compile(text,str(src),'exec'),scope)
except SystemExit as exc:assert exc.code==0
assert len(results)==len(failed)
receipt=dict(status='DIAGNOSTIC_ONLY_NO_CANDIDATE',selected_clusters=sorted(failed),results=results,
 source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),solver_sha256=hashlib.sha256(Path(solver.__file__).read_bytes()).hexdigest(),
 instrumented_author_sha256=hashlib.sha256(text.encode()).hexdigest(),retained_terrain_sha256=report['output_sha256'],
 limits=['LP infeasibility applies only to the selected sufficient witnesses, not to unrestricted min/max prominence.','No terrain, geometry, package or production source authored or changed.'])
(out/'instrumented-author.py').write_bytes(text.encode())
(out/'linear-feasibility.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
