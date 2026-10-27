from pathlib import Path
import copy,json,sys,tempfile
R=Path(__file__).parent;sys.path.insert(0,str(R))
from navv9diag_gate import validate_diagnostic,validate_fields
D=R/'kit7-navv9diag-ram-ab-20261027';n=R/'kit7-nav-consumer-20261026/result.json'
h=json.loads(n.read_text());d=json.loads((D/'deployment.json').read_text());checks=[]
assert validate_diagnostic(n,D/'deployment.json')['acceptance_eligible'] is False
checks.append('actual_known_FAIL_and_deployment_bound')
for name,mutator in [
 ('false_native_PASS',lambda a,b:a.update(status='PASS_KIT7_NATIVE_GRAPH')),
 ('missing_height_failure',lambda a,b:a['height_issues'].pop()),
 ('wrong_height_failure',lambda a,b:a['height_issues'].__setitem__(0,'different/0: error')),
 ('incomplete_queries',lambda a,b:a['cases'].pop()),
 ('eligibility_laundering',lambda a,b:b.update(acceptance_eligible=True)),
 ('wrong_historical_hash',lambda a,b:b.update(height_result_sha256='0'*64)),
 ('wrong_package_hash',lambda a,b:b['packages'].__setitem__(next(iter(b['packages'])),'0'*64)),
 ('missing_package',lambda a,b:b['packages'].pop(next(iter(b['packages'])))),
]:
 a,b=copy.deepcopy(h),copy.deepcopy(d);mutator(a,b)
 try:validate_fields(a,b)
 except AssertionError:checks.append(name+'_rejected')
 else:raise AssertionError(name+' survived')
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'result.json';p.write_bytes(n.read_bytes()+b' ')
 try:validate_diagnostic(p,D/'deployment.json')
 except AssertionError:checks.append('byte_drift_rejected')
 else:raise AssertionError('Hash drift survived')
result=dict(status='PASS_DIAGNOSTIC_GATE_CONTROLS',checks=checks,count=len(checks),native_acceptance=False)
(D/'diagnostic-gate-controls.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
