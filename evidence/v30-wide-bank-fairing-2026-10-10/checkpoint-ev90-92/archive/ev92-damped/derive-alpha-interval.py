from pathlib import Path
import importlib.util, json, hashlib
import numpy as np
Q=Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010')
OUT=Q/'ev92-damped'
D91=Q/'ev91-descent'
BP=Q.parent/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
HP=D91/'candidate-terrain.npz'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
ev=load('verify_ev88q_ev92',Q/'review-independent/verify_ev88q.py')
shape=load('shape_contract_ev92',Q/'next-method-consumer/shape_contract.py')
B=np.load(BP)['heights'].astype(np.float64)
H=np.load(HP)['heights'].astype(np.float64)
D=H-B
prep=json.loads((D91/'prepared.json').read_text(encoding='utf-8'))
records=ev.stencil_records(variables=prep['variables_rc'])
# Exact quadratic coefficients via rational sums over the exact binary float64 inputs
# (B and D originate in float32 heights), matching the consumer stencil rows/weights.
from fractions import Fraction
coeff_frac=[Fraction(0),Fraction(0),Fraction(0)]
for stencil in records:
    wb=Fraction(0); wd=Fraction(0)
    for (rr,cc),k in zip(stencil['nodes'],stencil['coeff']):
        kf=Fraction.from_float(float(k))
        wb += kf*Fraction.from_float(float(B[rr,cc]))
        wd += kf*Fraction.from_float(float(D[rr,cc]))
    weight=Fraction(2 if stencil['kind']=='Dxz' else 1)
    coeff_frac[0] += weight*wb*wb
    coeff_frac[1] += weight*2*wb*wd
    coeff_frac[2] += weight*wd*wd
c0,c1,c2=[float(x) for x in coeff_frac]
energy_target=0.75*c0
roots=np.roots([c2,c1,c0-energy_target])
energy_roots=[float(x.real) for x in roots if abs(float(x.imag))<1e-10 and 0<=float(x.real)<=1]
if not energy_roots: raise RuntimeError('no consumer-energy threshold root in [0,1]')
energy_lo=min(energy_roots)# Cardinal focus prominence P=max(0, center-max(neighbors)); requiring P(alpha)<=.75*P(B)
# is equivalent to imposing center-neighbor<=.75*P(B) for both neighbors on each axis.
r,c=840,370
base_prom=ev.focus_prominence(B,r,c)
focus_constraints=[]
focus_roots=[]
for axis, pairs in [('east_west',[(r,c-1),(r,c+1)]),('north_south',[(r-1,c),(r+1,c)])]:
    p0=base_prom[axis]
    for nr,nc in pairs:
        a0=float(B[r,c]-B[nr,nc])
        slope=float(D[r,c]-D[nr,nc])
        limit=0.75*p0
        root=(limit-a0)/slope if abs(slope)>1e-15 else None
        # If slope is negative, this is a lower bound; positive slope would impose an upper bound.
        focus_constraints.append({'axis':axis,'neighbor_rc':[nr,nc],'base_center_minus_neighbor_m':a0,
          'line_slope_m_per_alpha':slope,'allowed_center_minus_neighbor_m':limit,'root_alpha':root,
          'bound_type':('lower' if slope<0 else 'upper' if slope>0 else 'constant')})
        if slope>1e-15: raise RuntimeError('focus pair slopes are not all descending; derive exact piecewise union before midpoint')
        if slope < -1e-15: focus_roots.append(float(root))
# Since both center-minus-neighbor differences descend along this line, prominence=min(diff_left,diff_right) first satisfies the upper bound at the EARLIER of the two roots per axis.
focus_axis_roots={}
for axis in ('east_west','north_south'):
    axis_roots=[x['root_alpha'] for x in focus_constraints if x['axis']==axis and x['root_alpha'] is not None]
    focus_axis_roots[axis]=min(axis_roots)
focus_lo=max(focus_axis_roots.values())
alpha_lo=max(energy_lo,focus_lo,0.0)
if alpha_lo>=1: raise RuntimeError(f'no positive interval [lower,1]: {alpha_lo}')
alpha_mid=(alpha_lo+1.0)/2.0
# Diagnostic in-memory single cast, no file/candidate output.
Hm=np.asarray(B+alpha_mid*D,dtype=np.float32)
focus_after=ev.focus_prominence(Hm,r,c)
E_B=ev.stencil_energy(B,records)[0]
E_Hm=ev.stencil_energy(Hm,records)[0]
E_collar_B=ev.stencil_energy(B,records,collar_only=True)[0]
E_collar_Hm=ev.stencil_energy(Hm,records,collar_only=True)[0]
q=Hm[836:838,370:372].astype(np.float64)
shape_diag=shape.evaluate_shape(B.astype(np.float32),Hm,ev.WINDOW,(840,370))
angle_B=ev.local_mesh_angles(B,center=(840,370),radius=2)['max_incident_hinge_deg']
angle_mid=ev.local_mesh_angles(Hm.astype(np.float64),center=(840,370),radius=2)['max_incident_hinge_deg']
# Integrity hashes/provenance.
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs={
 'B_path':str(BP),'B_sha256':sha(BP),'H91_direction_path':str(HP),'H91_sha256':sha(HP),
 'prepared_path':str(D91/'prepared.json'),'prepared_sha256':sha(D91/'prepared.json'),
 'consumer_energy_path':str(Q/'review-independent/verify_ev88q.py'),'consumer_energy_sha256':sha(Q/'review-independent/verify_ev88q.py'),
 'shape_contract_path':str(Q/'next-method-consumer/shape_contract.py'),'shape_contract_sha256':sha(Q/'next-method-consumer/shape_contract.py'),
 'ev91_plan_path':str(D91/'plan.md'),'ev91_plan_sha256':sha(D91/'plan.md'),
 'ev91_receipt_path':str(D91/'authoring.json'),'ev91_receipt_sha256':sha(D91/'authoring.json'),
 'derivation_script_path':str(Path(__file__)),'derivation_script_sha256':sha(Path(__file__))}
report={
 'status':'PROPOSED_SCALAR_RULE_ONLY_NO_SOLVE_NO_TERRAIN',
 'scope':'EV92 design proposal from frozen EV91 direction H91-B. This calculation does not authorize, run, or emit a candidate.',
 'inputs':inputs,
 'line':'H(alpha)=B+alpha*(H91-B), alpha in [0,1]; coefficients and roots use float64 uncast B,D.',
 'energy':{'definition':'Independent consumer stencil_records(variables=prepared.variables_rc); exact rational summation of binary float64 B,D values and stencil coefficients/weights (Dxz weight 2), then converted to float64.',
   'records_count':len(records),'quadratic_constant_linear_quadratic':[c0,c1,c2],
   'exact_binary_rational_coefficients_num_den':[[str(x.numerator),str(x.denominator)] for x in coeff_frac],
   'energy_B':c0,'energy_H91':c0+c1+c2,'target_75pct_B':energy_target,
   'roots_in_0_1':energy_roots,'lower_bound':energy_lo},
 'focus_25pct':{'focus_rc':[r,c],'B_prominence_m':base_prom,
   'linear_constraints':focus_constraints,'axis_first_crossing_roots':focus_axis_roots,'lower_bound':focus_lo},
 'material_interval':{'lower_bound':alpha_lo,'upper_bound':1.0,
   'midpoint_rule':'alpha_proposed=(lower_bound+upper_bound)/2; this is a deterministic design point, not selected production alpha.',
   'alpha_proposed':alpha_mid,'interval_length':1.0-alpha_lo,
   'interpretation':'This interval certifies only the scalar energy and cardinal focus 25% materiality inequalities on the uncast line. It is not feasibility for all shape, angle, topology, physical, compiled, corridor, sector, or runtime gates.'},
 'single_point_diagnostic_after_one_float32_cast':{'focus_prominence_m':focus_after,
   'focus_reductions_fraction':{k:1-focus_after[k]/base_prom[k] for k in base_prom},
   'energy_consumer':E_Hm,'energy_reduction_fraction':1-E_Hm/E_B,
   'collar_energy_B':E_collar_B,'collar_energy_point':E_collar_Hm,
   'quad_836_370_values_m':q.tolist(),'quad_range_m':float(q.max()-q.min()),
   'quad_exactly_flat':bool(np.all(q==q.flat[0])),
   'local_shape_gates':shape_diag['gates'],'focus_angle_B_deg':angle_B,'focus_angle_mid_deg':angle_mid,'focus_angle_reduction_deg':angle_B-angle_mid,
   'note':'In-memory diagnostic only; not a test of the full consumer and not saved as terrain.'},
 'policy_review':{'same_frozen_direction_only':True,'one_candidate_maximum_if_later_authorized':True,
   'full_independent_consumer_required':True,'if_any_gate_fails':'reject without selecting another alpha or changing thresholds',
   'criteria_to_retain':['all EV90 physical/compiled/P9/protection gates','focus and population shape gates','energy and collar gates','angle/sector/p99/count gates','no new strict minima','no new exact-flat 2x2 quads','profile inspection at real scale'],
   'limitations':['EV91 itself remains rejected and unchanged.','The scalar interval does not show that midpoint passes global gates.','Any float32 output must be independently rechecked against exact bounds and every frozen contract.','This is a new EV92 proposal; EV91 plan forbids post-solve repair/damping.']}}
(OUT/'alpha-interval.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'energy_coeffs':[c0,c1,c2],'energy_roots':energy_roots,'focus_constraints':focus_constraints,'alpha_lo':alpha_lo,'alpha_mid':alpha_mid,'energy_mid_reduction':1-E_Hm/E_B,'focus_mid_reductions':report['single_point_diagnostic_after_one_float32_cast']['focus_reductions_fraction'],'flat':report['single_point_diagnostic_after_one_float32_cast']['quad_exactly_flat'],'local_shape_gates':shape_diag['gates'],'focus_angle_mid_deg':angle_mid},indent=2))







