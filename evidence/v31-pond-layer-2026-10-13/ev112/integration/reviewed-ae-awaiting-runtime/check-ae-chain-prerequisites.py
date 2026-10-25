"""Exercise the actual chain receipt guard, including a poll that skips the exact first-stage count."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).parent;p=O/'run-ae-validated-chain.py';tree=ast.parse(p.read_text())
guard=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='check_steps')
current=None
env={'read':lambda name:current}
exec(compile(ast.Module(body=[guard],type_ignores=[]),str(p)+'#receipt-guard','exec'),env)
cases=[
 ('absent_wait',None,5,None,True,False,False),
 ('empty_wait',{'steps':[]},5,None,True,False,False),
 ('exact_first_stage',{'steps':[{'step':'place','rc':0}]},1,None,True,True,False),
 ('poll_skips_first_count',{'steps':[{'step':'place','rc':0},{'step':'subset','rc':0}]},1,None,True,True,False),
 ('missing_required',None,5,None,False,None,True),
 ('incomplete_required',{'steps':[{'step':'place','rc':0}]},5,None,False,None,True),
 ('actual_failure',{'steps':[{'step':'place','rc':1}]},1,None,True,None,True),
 ('declared_unpainted_exception',{'steps':[{'step':'g8-unpainted','rc':1}]},1,'g8-unpainted',False,True,False),
 ('unrelated_failure_not_exempt',{'steps':[{'step':'g2','rc':1}]},1,'g8-unpainted',False,None,True),
]
def exercise(fn):
    global current
    rows=[]
    for name,value,count,exception,partial,expected,reject in cases:
        current=value;rejected=False;actual=None
        try:actual=fn('fixture',count,exception,partial)
        except AssertionError:rejected=True
        assert rejected==reject,(name,'unexpected rejection/acceptance')
        if not reject:assert actual==expected,(name,actual)
        rows.append(dict(case=name,expected_rejection=reject,result='PASS'))
    return rows
rows=exercise(env['check_steps'])
# A harness that accidentally catches its own expectation assertion can false-pass
# unexpected acceptance. Prove this harness rejects a permissive guard specifically.
mutant_rejected=False
try:
    current=None
    def permissive(name,count,exception=None,partial=False):
        return False if partial and current is None else (len(current['steps'])>=count if partial and current else True)
    exercise(permissive)
except AssertionError as error:
    assert error.args[0][0]=='missing_required';mutant_rejected=True
assert mutant_rejected
out=O/'ae-chain-prerequisite-controls-v2.json';assert not out.exists()
out.write_text(json.dumps(dict(status='PASS',scope=__doc__,chain_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=rows,permissive_mutant_rejected=True,production_outputs_changed=False),indent=2)+'\n')
print('PASS',len(rows),'actual receipt-guard controls')
