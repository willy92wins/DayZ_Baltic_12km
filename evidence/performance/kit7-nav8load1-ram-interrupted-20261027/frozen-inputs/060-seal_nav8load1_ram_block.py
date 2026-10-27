from pathlib import Path
import hashlib,json
R=Path(__file__).parent;D=R/'kit7-nav8load1-ram-ab-20261027';V=R/'kit7-nav8load1-ram-review-20261027';F=R/'kit7-nav8load1-recovery-review-20261027';N=R/'kit7-nav8load1-consumer-20261027'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
assert __debug__ and not (D/'accepted.json').exists()
review=read(F/'response.json');assert not review['is_error'] and not review.get('permission_denials') and 'claude-fable-5-1' in review['modelUsage']
assert read(F/'completion.json')['returncode']==0 and read(F/'adjudication.json')['status']=='ACCEPTED_AFTER_REVIEW'
latest=read(F/'adjudication.json')['inputs']
assert set(read(F/'source-hashes.json'))<=set(latest)
assert set(read(V/'source-hashes.json'))<=set(latest)
for p,h in latest.items():assert sha(p)==h,p
joint=read(N/'joint-result.json');assert joint['status']=='PASS_LOAD1_CONFIG_AND_NATIVE607'
assert read(N/'config-result.json')['status']=='PASS_NATIVE_LOAD1_CONFIG' and read(N/'result.json')['status']=='PASS_KIT7_NATIVE_GRAPH'
assert joint['run_id']==read(N/'host-identity.json')['run_id']==read(N/'identity-verification.json')['run_id'] and joint['packages']==read(N/'deployment.json')['packages']
assert read(D/'joint-gate-controls.json')['status']=='PASS_LOAD1_NATIVE_ADMISSION_CONTROLS' and read(D/'joint-gate-controls.json')['count']==80
for p,h in read(D/'joint-gate-controls.json')['inputs'].items():assert sha(p)==h
coord=R/'orchestrate_nav8load1_ram.js'
for name in ('coordinator-controls.json','command-flow-controls.json'):
 c=read(D/name);assert c['coordinator_sha256']==sha(coord) and all(x['passed'] for x in c['cases'])
assert not list(D.glob('pass-*')) and not (D/'attempt-reservations').exists()
manifest=read(D/'missions.json');assert manifest['order']=='A-B-B-A-A-B' and len(manifest['passes'])==6
for n,row in enumerate(manifest['passes'],1):
 m=Path(row['mission']);assert row['order']==n and {p.name for p in m.iterdir()}=={'init.c'} and sha(m/'init.c')==row['mission_sha256']
 assert not (Path('C:/temp/DayZ_MCP_130_dev/_server/profiles-130')/row['profile_log']).exists()
paths=[F/n for n in ['response.json','completion.json','source-hashes.json','adjudication.json']]+[N/n for n in ['config-result.json','joint-result.json','config-recovery.json','result.json','identity-verification.json','deployment.json','host-identity.json']]+[Path(__file__),V/'response.json',V/'completion.json',V/'source-hashes.json']
inputs={**latest,**{str(p):sha(p) for p in paths}}
write(V/'adjudication.json',dict(status='ACCEPTED_AFTER_REVIEW',original_verdict='SOUND-with-fixes',post_review_changes=[str(R/n) for n in ['prepare_nav8load1_ram_pass.py','finalize_nav8load1_ram_ab.py','test_nav8load1_joint_gate.py']]+[str(D/'joint-gate-controls.json')],followup_review=str(F/'response.json'),fixes=['Joint bound to exact run and package set','Complete reviewed source coverage required','Exclusive reservation, unique runs and honest unverified wider repeat history','Fresh mission inventory'],inputs=inputs))
write(D/'accepted.json',dict(status='ACCEPTED_AFTER_REVIEW',inputs={**inputs,str(V/'adjudication.json'):sha(V/'adjudication.json')},max_passes=6,max_retries=0,ram_ratio_limit=1.10,dispersion_limit=0.05,order='A-B-B-A-A-B',native_run=joint['run_id']))
print(json.dumps(dict(status='SEALED_FRESH_LOAD1_RAM_BLOCK',native_run=joint['run_id'],inputs=len(inputs))))
