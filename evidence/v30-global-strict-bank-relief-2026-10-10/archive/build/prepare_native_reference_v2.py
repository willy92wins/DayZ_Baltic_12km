"""Repair the omitted serialized points list, preserving V1 and its failing report."""
from pathlib import Path
import ast,csv,hashlib,json,copy
import numpy as np
R=Path(__file__).parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(R/'verify_native.py')=='230d65404f5087b54ed1704fbc5f3d912328117f4a43a4674005fb0a7939e229'
assert sha(R/'candidate/terrain.npz')=='8e239f8e2815b61a920421af1dfbb1b64f353ab4978d633eb39fe74f04946d1b'
assert sha(R/'native-snapshot.log')=='f69470851e82ce01f144a5530f1e28edf6541a3ef82cdf270bb20778103281c8'
old=json.loads((R/'native-reference.json').read_text())
failed=json.loads((R/'native-verification.json').read_text())
assert failed['status']=='FAIL' and failed['errors']==['calibrated_height']
ref=copy.deepcopy(old)
local=Path(ref['local_mission']);rows=list(csv.reader((local/'risks.csv').open(),delimiter=';'))
for name,digest in ref['files'].items():
 assert sha(local/name)==digest and sha(Path(ref['mission'])/name)==digest
H=np.load(R/'candidate/terrain.npz')['heights'].astype(float)
base_path=Path('E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
assert sha(base_path)=='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
HB=np.load(base_path)['heights'].astype(float)
assert len(rows)==len(ref['points'])==1212
changed=[];csv_errors=[]
def barycentric_height(h,x,z):
 c=int(x//6);r=int((12282-z)//6);u=x/6-c;v=(12282-z)/6-r
 nodes=((r,c),(r,c+1),(r+1,c+1)) if u>=v else ((r,c),(r+1,c),(r+1,c+1))
 # Independent plane coefficients, without importing the production sampler.
 matrix=np.array([[cc-c,rr-r,1.] for rr,cc in nodes])
 coeff=np.linalg.solve(matrix,np.array([h[rr,cc] for rr,cc in nodes]))
 return float(coeff@np.array([u,v,1.]))
for i,(row,q) in enumerate(zip(rows,ref['points'])):
 assert int(row[0])==i and int(row[4])==q['cls']
 x,z=float(row[1]),float(row[2]);assert abs(q['x']-x)<1e-7 and abs(q['z']-z)<1e-7
 expected=barycentric_height(H,x,z)
 csv_errors.append(abs(expected-float(row[3])))
 assert csv_errors[-1]<1e-5,(i,expected,float(row[3]),csv_errors[-1])
 if abs(expected-barycentric_height(HB,x,z))>1e-7:changed.append(i)
 q['expected_ground']=expected
 assert {k:v for k,v in q.items() if k!='expected_ground'}=={k:v for k,v in old['points'][i].items() if k!='expected_ground'}
assert len(changed)==old['ground_points_changed_vs_ev82']==11
ref['supersedes_reference']={'path':str(R/'native-reference.json'),'sha256':sha(R/'native-reference.json'),
 'reason':'prepare_probe recomputed points but omitted points from reference.update; risk CSV and terrain were correct.'}
ref['status']='CORRECTED_REFERENCE_FOR_EXISTING_NATIVE_SNAPSHOT'
ref['points_reference_source']={'path':str(local/'risks.csv'),'sha256':sha(local/'risks.csv'),
 'check':'Each serialized expected ground independently verified by triangle-plane solve from candidate heights.'}
out=R/'native-reference-v2.json';assert not out.exists()
out.write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
code=(R/'verify_native.py').read_text()
assert code.count("'native-reference.json'")==2
code=code.replace("E/'native-reference.json'","E/'native-reference-v2.json'")
code=code.replace("E/'native-verification.json'","E/'native-verification-v2.json'")
code=code.replace('strictbank-physical-anomalies.csv','strictbank-physical-anomalies-v2.csv').replace('strictbank-unflagged-scalar-queries.csv','strictbank-unflagged-scalar-queries-v2.csv').replace('strictbank-fullwater-runtime.log','strictbank-fullwater-runtime-v2.log')
marker='assert all(negative.values()),negative'
assert marker in code
extra="""# A stale expected-ground list must fail even when all grid vertices are valid.
original_expected = ref['points'][45]['expected_ground']
ref['points'][45]['expected_ground'] = original_expected + .01
negative['stale_calibrated_height_reference'] = not judge(content)['pass_gate']
ref['points'][45]['expected_ground'] = original_expected
"""
code=code.replace(marker,extra+marker)
code=code.replace("status='PASS_COMPLETE_NATIVE_READBACK' if r['pass_gate'] else 'FAIL'","reference_sha256=sha(E/'native-reference-v2.json'),preserved_v1_fail_sha256=sha(E/'native-verification.json'),status='PASS_COMPLETE_NATIVE_READBACK' if r['pass_gate'] else 'FAIL'")
code+="\nraise SystemExit(0 if r['pass_gate'] else 1)\n"
ast.parse(code);verifier=R/'verify_native_v2.py';assert not verifier.exists();verifier.write_text(code,encoding='utf-8')
receipt={'status':'REFERENCE_CORRECTED_NOT_REJUDGED','original_reference_sha256':sha(R/'native-reference.json'),
 'original_fail_sha256':sha(R/'native-verification.json'),'original_verifier_sha256':sha(R/'verify_native.py'),
 'corrected_reference_sha256':sha(out),'new_verifier_sha256':sha(verifier),'changed_point_ids':changed,
 'snapshot_sha256':sha(R/'native-snapshot.log'),'max_independent_plane_vs_serialized_ground_m':max(csv_errors),'no_terrain_or_mission_change':True,
 'limits':'No new engine run and no tolerance change. Existing FAIL remains preserved; V2 report required.'}
(R/'native-reference-correction.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
