from pathlib import Path
import hashlib,json,subprocess,time,sys
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025')
OUT=R/'prism-b3d-execution-20261028'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
OUT.mkdir(exist_ok=False)
prior_path=R/'prism-b3-binary-replay-20261028/contract-r1.json'
witness_path=R/'prism-b3-quantization-discovery-20261028/report.json'
prior=json.loads(prior_path.read_bytes());witness=json.loads(witness_path.read_bytes())
pins=dict(prior['pins'])
for p,h in pins.items():
    if sha(p)!=h:raise RuntimeError('Inherited pin changed: '+p)
tests=json.loads((R/'prism-b3d-final-tests-r1-20261028/report.json').read_bytes())
assert tests['status']=='PASS' and tests['tests']==35
for t in tests['results']:assert sha(W/'tools/quality'/t['script'])==t['sha256']
extra=[prior_path,witness_path,W/'plans/ev112-prism-b3-numeric-author-20261028.md',
 R/'prism-b3d-final-tests-r1-20261028/report.json',R/'prism-b3d-review-capsule-20261028/completion.json',R/'prism-b3d-review-capsule-20261028/adjudication.md',Path(__file__)]
for name in ['prism_b3_numeric_author_ev112.py','verify_prism_b3_numeric_ev112.py','test_prism_b3_numeric_ev112.py','test_prism_b3_numeric_cli_ev112.py']:extra.append(W/'tools/quality'/name)
for p in extra:pins[str(p)]=sha(p)
c=dict(schema='B3D_NUMERIC_MLOD_V1',expected_changes=17,expected_counts=[9120,12160,1520],
 source=prior['candidate_mlod'],reference=prior['source_control'],previous_report=prior['offline_proof'],original_result=prior['original_result'],
 prior_contract=str(prior_path),witness=str(witness_path),centre=witness['centre_fixed'],pins=pins)
for k in ['origin','matrix','targets','selected_components']:c[k]=prior[k]
contract=OUT/'contract.json';dump(contract,c)
dump(OUT/'start.json',dict(contract_sha256=sha(contract),author_budget_s=60,consumer_budget_s=180,memory_budget_bytes=2*1024**3,pin_count=len(pins)))
state=R/'ACTIVE-WORK.md'
state.write_text('# B3D single author and independent consumer in progress\n\nOwn operation: execute_prism_b3d_20261028.py; sealed contract in prism-b3d-execution-20261028.\n35 final tests PASS; Fable review delivered/adjudicated. Follow result, no duplicate.\nNo binarization/package/DayZ/lease.\n\n---\n'+state.read_text(encoding='utf-8'),encoding='utf-8')
steps=[('author','prism_b3_numeric_author_ev112.py',[str(contract),str(R/'prism-b3d-candidate-20261028')],70),
 ('consumer','verify_prism_b3_numeric_ev112.py',[str(contract),str(R/'prism-b3d-candidate-20261028/candidate.p3d'),str(R/'prism-b3d-consumer-20261028')],190)]
results=[]
for label,script,args,budget in steps:
    start=time.monotonic()
    with (OUT/(label+'.stdout')).open('wb') as stdout,(OUT/(label+'.stderr')).open('wb') as stderr:
        p=subprocess.run([sys.executable,'-I',str(W/'tools/quality'/script),*args],cwd=W,stdout=stdout,stderr=stderr,timeout=budget)
    row=dict(step=label,returncode=p.returncode,seconds=time.monotonic()-start);results.append(row);dump(OUT/'steps.json',results)
    print(json.dumps(row),flush=True)
    if p.returncode:raise SystemExit(p.returncode)
report=json.loads((R/'prism-b3d-consumer-20261028/report.json').read_bytes())
assert report['status']=='OFFLINE_CANDIDATE_ONLY'
assert report['exact_mlod_pairs']==4560 and report['changed_y']==17 and report['incident_faces']==report['incident_normals']==50
assert report['contract_sha256']==sha(contract)
assert report['candidate_sha256']==sha(R/'prism-b3d-candidate-20261028/candidate.p3d')
dump(OUT/'completion.json',dict(status=report['status'],candidate_sha256=report['candidate_sha256'],contract_sha256=sha(contract),report_sha256=sha(R/'prism-b3d-consumer-20261028/report.json'),steps=results))
print(json.dumps(report),flush=True)
