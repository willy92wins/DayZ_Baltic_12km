from pathlib import Path
import importlib.util, json, hashlib
import numpy as np
Q=Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010')
D=Q/'ev91-descent'
BP=Q.parent/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
HP=D/'candidate-terrain.npz'
REPORT=D/'plateau-diagnosis.json'

def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod
shape=load_module('shape_contract_diag',Q/'next-method-consumer/shape_contract.py')
ev=load_module('verify_ev88q_diag',Q/'review-independent/verify_ev88q.py')
B=np.load(BP)['heights'].astype(np.float64)
H=np.load(HP)['heights'].astype(np.float64)
prep=json.loads((D/'prepared.json').read_text(encoding='utf-8'))
records=ev.stencil_records(variables=prep['variables_rc'])
E0=ev.stencil_energy(B,records)[0]
Em=ev.stencil_energy(B+0.5*(H-B),records)[0]
E1=ev.stencil_energy(H,records)[0]
quad_a=2.0*(E1+E0-2.0*Em)
quad_b=E1-E0-quad_a
threshold=0.75*E0
roots=np.roots([quad_a,quad_b,E0-threshold])
roots=[float(x.real) for x in roots if abs(float(x.imag))<1e-10 and 0.0<=float(x.real)<=1.0]
if len(roots)!=1: raise RuntimeError(f'expected one alpha root in [0,1], got {roots}')
alpha=roots[0]
X=np.asarray(B+alpha*(H-B),dtype=np.float32)
energy=ev.stencil_energy(X,records)[0]
collar_energy=ev.stencil_energy(X,records,collar_only=True)[0]
shape_result=shape.evaluate_shape(B.astype(np.float32),X,ev.WINDOW,(840,370))
angle_B=ev.local_mesh_angles(B,center=(840,370),radius=2)['max_incident_hinge_deg']
angle_X=ev.local_mesh_angles(X.astype(np.float64),center=(840,370),radius=2)['max_incident_hinge_deg']
quad=X[836:838,370:372].astype(np.float64)
report=json.loads(REPORT.read_text(encoding='utf-8'))
report['B_to_H_scalar_diagnostic']['fixed_stencil_energy_25pct_boundary']={
    'energy_definition':'Independent consumer verify_ev88q.stencil_energy over stencil_records(variables=prepared.variables_rc); Dxz terms weighted by 2, matching consumer implementation.',
    'energy_quadratic_constant_linear_quadratic_float64_line':[E0,quad_b,quad_a],
    'energies_B_midpoint_H':[E0,Em,E1],
    'target_75pct_B':threshold,
    'roots_in_0_1':roots,
    'lower_bound_alpha':alpha,
    'at_boundary_after_float32_cast':{
        'shape_gates':shape_result['gates'],
        'focus_hinge_B_deg':angle_B,
        'focus_hinge_after_deg':angle_X,
        'focus_angle_reduction_deg':angle_B-angle_X,
        'energy_after':energy,
        'energy_reduction_fraction':1.0-energy/E0,
        'collar_energy_after':collar_energy,
        'collar_energy_B':ev.stencil_energy(B,records,collar_only=True)[0],
        'quad_values_m':quad.tolist(),
        'quad_range_m':float(quad.max()-quad.min()),
        'quad_is_flat':bool(np.all(quad==quad.flat[0]))
    },
    'scope_note':'One in-memory line diagnostic only; no candidate, solver call, alpha selection, or full independent consumer run.'
}
report['inputs']['consumer_energy_helper_sha256']=hashlib.sha256((Q/'review-independent/verify_ev88q.py').read_bytes()).hexdigest()
report['inputs']['shape_contract_sha256']=hashlib.sha256((Q/'next-method-consumer/shape_contract.py').read_bytes()).hexdigest()
report['inputs']['B_terrain_sha256']=hashlib.sha256(BP.read_bytes()).hexdigest()
report['inputs']['candidate_H_sha256']=hashlib.sha256(HP.read_bytes()).hexdigest()
REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(report['B_to_H_scalar_diagnostic']['fixed_stencil_energy_25pct_boundary'],indent=2))
