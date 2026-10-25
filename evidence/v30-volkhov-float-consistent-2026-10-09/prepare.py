from pathlib import Path
import hashlib,json
B=Path(__file__).parent;OLD=B.parent/'v30-volkhov-constrained-apron-20261009'
code=(OLD/'solve.py').read_text()
assert 'limit=np.minimum(angle+2,np.maximum(angle,10));' in code
code=code.replace('limit=np.minimum(angle+2,np.maximum(angle,10));','limit=np.minimum(angle+2,np.maximum(angle,10)+.00005);')
old='slopesA=np.maximum(np.hypot(na[:,0],na[:,2]),np.tan(np.deg2rad(35)));slopesB=np.maximum(np.hypot(nb[:,0],nb[:,2]),np.tan(np.deg2rad(35)))'
new='slopesA=np.tan(np.maximum(np.arctan(np.hypot(na[:,0],na[:,2])),np.deg2rad(35))+np.deg2rad(.00005));slopesB=np.tan(np.maximum(np.arctan(np.hypot(nb[:,0],nb[:,2])),np.deg2rad(35))+np.deg2rad(.00005))'
assert old in code;code=code.replace(old,new)
code=code.replace("report.pop('history',None)","\nfor key in ['history','controls','gradient_direction_error','displacement_bending_energy']:report.pop(key,None)\nreport['author_precision_margin_degrees']=.00005\nreport['independent_consumer_precision_degrees']=.0001")
(B/'solve.py').write_text(code)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(B/'repair-reference.json').write_text(json.dumps(dict(original_solver_sha256=sha(OLD/'solve.py'),diagnosis_sha256=sha(OLD/'float-feasibility.json'),consumer_sha256=sha(OLD/'verify.py'),repaired_solver_sha256=sha(B/'solve.py')),indent=2)+'\n')
