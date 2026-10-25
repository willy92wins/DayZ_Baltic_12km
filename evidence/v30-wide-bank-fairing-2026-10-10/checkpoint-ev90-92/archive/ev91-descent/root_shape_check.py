from pathlib import Path
import importlib.util,json,hashlib,numpy as np
Q=Path('E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010')
D=Q/'ev91-descent';BP=Q.parent/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
shape=module('shape_root91',Q/'next-method-consumer/shape_contract.py')
ev=module('shape_geom91',Q/'review-independent/verify_ev88q.py')
b=np.load(BP)['heights'];h=np.load(D/'candidate-terrain.npz')['heights']
report=shape.evaluate_shape(b,h,ev.WINDOW,(840,370))
report['focus_hinge_B']=ev.local_mesh_angles(b.astype(float),center=(840,370),radius=2)['max_incident_hinge_deg']
report['focus_hinge_H']=ev.local_mesh_angles(h.astype(float),center=(840,370),radius=2)['max_incident_hinge_deg']
prep=json.loads((D/'prepared.json').read_text());stencils=ev.stencil_records(variables=prep['variables_rc'])
report['energy_B']=ev.stencil_energy(b,stencils)[0];report['energy_H']=ev.stencil_energy(h,stencils)[0]
report['collar_energy_B']=ev.stencil_energy(b,stencils,collar_only=True)[0];report['collar_energy_H']=ev.stencil_energy(h,stencils,collar_only=True)[0]
report['scope']='Root local diagnostic only; complete consumer still required.'
report['candidate_sha256']=hashlib.sha256((D/'candidate-terrain.npz').read_bytes()).hexdigest()
(D/'root-shape-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['gates','focus_hinge_B','focus_hinge_H','energy_B','energy_H','collar_energy_B','collar_energy_H']}))
