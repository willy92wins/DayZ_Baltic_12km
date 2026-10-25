from pathlib import Path
R=Path(__file__).parent
text=(R/'diagnose_e_residuals.py').read_text(encoding='utf-8-sig')
text=text.replace('from scipy.optimize import linprog,LinearConstraint','from scipy.optimize import linprog,LinearConstraint,minimize')
text=text.replace("failed={r['cluster'] for r in report['clusters'] if r['status']=='SOLVER_FAILED'}","failed={15,44}")
text=text.replace("out=R/'guarded-e-residual-feasibility'","out=R/'guarded-e-residual-phase1'")
old="    if lp.success:result['nonlinear_minimum']=[float(x['fun'](lp.x).min()) for x in kwargs['constraints'] if isinstance(x,dict)]"
new='''    if lp.success:
        nl=[x for x in kwargs['constraints'] if isinstance(x,dict)]
        result['nonlinear_minimum']=[float(c['fun'](lp.x).min()) for c in nl]
        lifted=[]
        for c in nl:
            lifted.append(dict(type='ineq',fun=lambda y,c=c:c['fun'](y[:-1])+y[-1],jac=lambda y,c=c:np.c_[c['jac'](y[:-1]),np.ones(len(c['fun'](y[:-1]))) ]))
        lifted.append(LinearConstraint(np.c_[linear[0].A,-np.ones(len(linear[0].ub))],-np.inf,linear[0].ub))
        start=np.r_[lp.x,max(0.,-min(result['nonlinear_minimum']))+.001]
        def objective(y):
            gradient=np.zeros_like(y);gradient[-1]=1.
            return float(y[-1]),gradient
        phase=minimize(objective,start,jac=True,method='SLSQP',bounds=[*kwargs['bounds'],(0.,None)],constraints=lifted,options={'maxiter':500,'ftol':1e-11})
        actual=[float(c['fun'](phase.x[:-1]).min()) for c in nl]
        linear_margin=float(np.min(linear[0].ub-linear[0].A@phase.x[:-1]))
        result['phase1']=dict(success=bool(phase.success),message=str(phase.message),iterations=int(phase.nit),slack=float(phase.x[-1]),nonlinear_minimum=actual,linear_minimum=linear_margin,
                             feasible=bool(min(actual+[linear_margin])>=-1e-8 and phase.x[-1]<=1e-8))
        np.savez_compressed(out/f'cluster-{current["cluster"]}-phase1.npz',solution=phase.x)
        # A positive local slack is NOT a proof of global infeasibility.
'''
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace("'No terrain, geometry, package or production source authored or changed.'","'No terrain, geometry, package or production source authored or changed.','Positive phase-I local slack is not a proof of global infeasibility.'")
exec(compile(text,str(R/'diagnose_e_residuals.py'),'exec'),{'__name__':'__main__','__file__':str(R/'diagnose_e_residuals.py')})
