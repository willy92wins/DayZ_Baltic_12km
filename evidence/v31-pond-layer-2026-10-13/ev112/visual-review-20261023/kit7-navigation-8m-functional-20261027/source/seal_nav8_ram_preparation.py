from pathlib import Path
import hashlib,json
R=Path(__file__).parent;D=R/'kit7-nav8-ram-ab-20261027';A=R/'kit7-nav8-ram-review-20261027';B=R/'kit7-nav8-recovery-ram-fixes-review-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (D/'accepted.json').exists()
assert read(B/'completion.json')['returncode']==0 and read(B/'completion.json')['inputs_unchanged']
assert 'Parte 1 SOUND' in read(B/'response.json')['result']
controls=read(D/'coordinator-controls.json');conditions=read(D/'conditions-controls.json')
assert controls['status']=='PASS_NAV8_RAM_CONTROL_FLOW' and len(controls['cases'])==11 and all(x['passed'] for x in controls['cases'])
assert controls['coordinator_sha256']==sha(R/'orchestrate_nav8_ram.js')
assert conditions['status']=='PASS_RAM_CONSUMER_CONTRACT_CONTROLS' and conditions['count']==11 and not conditions['native_measurement']
assert all(sha(p)==h for p,h in conditions['inputs'].items())
validation=read(D/'mission-validation.json');manifest=read(D/'missions.json');assert validation['status']=='PASS_SIX_MISSION_FILES'
for row,check in zip(manifest['passes'],validation['missions'],strict=True):
 assert sha(Path(row['mission'])/'init.c')==row['mission_sha256']==check['mission_sha256'] and check['status']=='PASS' and check['files']==1
paths=[Path(p) for p in read(A/'source-hashes.json')]
paths += [R/'test_nav8_ram_conditions.py',R/'fix_nav8_ram_review.py',D/'conditions-controls.json',D/'coordinator-controls-before-review.json',Path(__file__)]
paths += [x/n for x in [A,B] for n in ['source-hashes.json','brief.md','response.json','completion.json']]
paths += [A/'adjudication.md',A/'corrected-source-hashes.json']
report=dict(status='ACCEPTED_AFTER_REVIEW',scope='RAM preparation only; Fable confirmation Part1 SOUND. Part2 generation recovery has a separate review and is not approved by this gate.',inputs={str(p):sha(p) for p in paths},control_counts=dict(missions=6,consumer_contract=11,lifecycle=11),native_measurement=False,launch_conditions=['Native607 PASS and identical deployed package bindings required by per-pass preparer.','Load nav8RamConfig directly from the frozen missions.json before running benchKit7Nav8; do not reconstruct it manually.','Three fresh passes per map in ABBAAB order; unchanged 1.10 RAM budget and 5 percent dispersion.'],limits=['No performance, client, actor or global acceptance yet.'])
(D/'accepted.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],scope=report['scope'],inputs=len(report['inputs']))))
