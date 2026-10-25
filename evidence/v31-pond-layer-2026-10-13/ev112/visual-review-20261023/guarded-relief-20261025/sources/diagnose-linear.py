from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.optimize import linprog,LinearConstraint
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/terrain'))
import repair_free_shapes_ev112 as solver
report=json.loads((R/'guarded-relief-batch-d/report.json').read_text())
failed={r['cluster'] for r in report['clusters'] if r['status']=='SOLVER_FAILED'}
current={};results=[]
def diagnose(fun,x0,**kwargs):
    linear=[x for x in kwargs['constraints'] if isinstance(x,LinearConstraint)]
    assert len(linear)==1
    lp=linprog(np.zeros(len(x0)),A_ub=linear[0].A,b_ub=linear[0].ub,bounds=kwargs['bounds'],method='highs')
    result=dict(cluster=current['cluster'],linear_witness_feasible=bool(lp.success),lp_status=int(lp.status),message=lp.message)
    if lp.success:
        result['nonlinear_minimum']=[float(x['fun'](lp.x).min()) for x in kwargs['constraints'] if isinstance(x,dict)]
    results.append(result)
    raise ValueError('DIAGNOSTIC_ONLY_NO_AUTHOR_SOLUTION')
solver.minimize=diagnose
src=W/'tools/terrain/repair_guarded_shapes_ev112.py';text=src.read_text(encoding='utf-8')
needle='    for ident,sl0 in enumerate(find_objects(clusters),1):'
text=text.replace(needle,needle+'\n        if ident not in DIAG_FAILED:continue\n        DIAG_CURRENT["cluster"]=ident')
sys.argv=[str(src),str(R/'combined-merged'),str(R/'guarded-relief-discovery'),str(R/'guarded-rejection-diagnostic'),
          '--expected-terrain-sha256',report['input_sha256'],'--expected-domains-sha256',report['domains_sha256']]
scope=dict(__name__='__main__',__file__=str(src),DIAG_FAILED=failed,DIAG_CURRENT=current)
try:exec(compile(text,str(src),'exec'),scope)
except SystemExit as exc:assert exc.code==1
assert len(results)==len(failed)
receipt=dict(status='DIAGNOSTIC_ONLY',selected_clusters=sorted(failed),results=results,
             source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
             limits='LP infeasibility applies only to the selected sufficient witnesses, not to the underlying unrestricted min/max prominence. No candidate authored.')
(R/'guarded-rejection-diagnostic/linear-feasibility.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
