"""Independent malformed framing cases from a real EV110 probe."""
from pathlib import Path
import sys,json,hashlib
O=Path(__file__).parent;sys.path.insert(0,str(O));import eval_bridge_regression_ev112 as G
D=O/sys.argv[1];D.mkdir(exist_ok=False)
bp=O.parent/'ev110/probe/bridges-points.json';bl=O.parent/'ev110/probe/split/bridges-baltic_bridge_probe_v2.log'
p=json.loads(bp.read_text());lines=bl.read_text().splitlines();assert len(G.load_rows(bl,p))==len(p)
begin=[x for x in lines if x.startswith('BEGIN;')];end=[x for x in lines if x.startswith('END;')];data=[x for x in lines if x.startswith('P;')]
assert len(begin)==len(end)==1 and len(data)==len(p)
cases={'rows-before-begin':data+begin+end,'end-before-rows':begin+end+data,'row-after-end':begin+data[:-1]+end+data[-1:],'duplicate-begin':begin+begin+data+end,'missing-end':begin+data}
results={}
for name,rows in cases.items():
 f=D/(name+'.log');f.write_text('\n'.join(rows)+'\n')
 try:G.load_rows(f,p);results[name]={'rejected':False}
 except (ValueError,IndexError) as e:results[name]={'rejected':True,'reason':str(e)}
result={'status':'PASS' if all(v['rejected'] for v in results.values()) else 'FAIL','positive_real_log':'PASS','tool_sha256':hashlib.sha256((O/'eval_bridge_regression_ev112.py').read_bytes()).hexdigest(),'baseline_sha256':hashlib.sha256(bl.read_bytes()).hexdigest(),'cases':results}
(D/'controls.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));sys.exit(result['status']!='PASS')
