"""Exercise the consumer's actual scale assignments on the frozen solved 49-node case."""
import ast
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
import numpy as np

ROOT=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/global-operator-prototype')
HERE=ROOT/'real-sector-preflight'
consumer=HERE/'verify_real_sector.py'
tree=ast.parse(consumer.read_text(encoding='utf-8'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify_candidate_local')
names={'infnorm','eps_p','eps_d','reported_eps_match'}
body=[n for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
assert len(body)==4
block=compile(ast.Module(body=body,type_ignores=[]),str(consumer),'exec')
solver_path=ROOT/'admm-quantized-pilot/solve.py'
spec=importlib.util.spec_from_file_location('scale_fixture_solver',solver_path)
solver=importlib.util.module_from_spec(spec);sys.modules[spec.name]=solver;spec.loader.exec_module(solver)
prior=solver.load_prior()
base,nodes,A,rhs,C,d,witnesses,exempt,centers,lo,hi,x0,records=prior.build_problem('minimum')
folder=ROOT/'admm-quantized-pilot/run-01'
with np.load(folder/'reference49.npz',allow_pickle=False) as z:
    assert np.array_equal(z['baseline'],base) and np.array_equal(z['nodes_rc'],nodes)
    scope={'np':np,'math':math,'C':C,'x':z['x_float64'],'yb':z['y_box'],
           'yd':z['y_d8'],'zb':z['z_box'],'zd':z['z_d8']}
    diag=json.loads((folder/'report.json').read_text())['cases'][0]['solver']
    scope['diag']=dict(diag)
    exec(block,scope)
    assert scope['reported_eps_match']
    expected=(scope['eps_p'],scope['eps_d'])
    scope['diag']['eps_primal']*=1000
    scope['diag']['eps_dual']*=1000
    exec(block,scope)
    assert not scope['reported_eps_match']
    assert expected==(scope['eps_p'],scope['eps_d'])
result={'status':'PASS_FROZEN_49_KKT_SCALE_FIXTURE','consumer_sha256':hashlib.sha256(consumer.read_bytes()).hexdigest(),
        'positive_saved_solver_tolerances_match':True,'inflated_reported_tolerances_rejected':True,
        'reconstructed_scales_unchanged_by_report':True,'eps_primal':expected[0],'eps_dual':expected[1],
        'solver_called':False}
with (HERE/'kkt-scale-fixture.json').open('x',encoding='utf-8') as stream:
    json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result))
