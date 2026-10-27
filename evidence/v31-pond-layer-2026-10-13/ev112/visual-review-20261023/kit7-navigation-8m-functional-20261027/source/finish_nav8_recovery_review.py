from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).parent;O=R/'kit7-nav8-recovered-postprocess-review-20261027';I=R/'nav-kit7-8m-preparation-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assert read(O/'completion.json')['returncode']==0 and read(O/'completion.json')['inputs_unchanged']
assert 'SOUND-with-fixes' in read(O/'response.json')['result'] and not (O/'accepted.json').exists()
before=read(O/'source-hashes.json');assert all(sha(p)==h for p,h in before.items())
archive=O/'reviewed-sources';archive.mkdir(exist_ok=False);rows=[]
for n,(p,h) in enumerate(before.items()):
 p=Path(p);target=archive/f'{n:02}-{p.name}';target.write_bytes(p.read_bytes());assert sha(target)==h
 rows.append(dict(original=str(p),archived=str(target),sha256=h))
write(O/'reviewed-archive.json',rows)
p=R/'package_and_deploy_kit7_nav8_recovered.py';s=p.read_text(encoding='utf-8')
old="assert {str(Path(__file__)),str(R/'verify_nav8_recovered_exit.py'),str(R/'resume_kit7_nav8_generation.js')}<=set(recovery_gate['inputs'])"
new="""recovery_required=[Path(__file__),R/'verify_nav8_recovered_exit.py',R/'resume_kit7_nav8_generation.js',R/'nav8-recovery-addendum.md',R/'test_nav8_recovered_exit.py',R/'kit7-nav8-recovered-exit-controls.json']
recovery_required += [I/n for n in ('generator-identity.json','generator-after-unexecuted-cancel.json','completion-before-lease-recovery.json','cleanup-before-lease-recovery.json','mcp-recovered.json','mcp-before.json','lease-recovery.json')]
assert {str(p) for p in recovery_required}<=set(recovery_gate['inputs'])
assert read(I/'lease-recovery.json')['source_sha256']==sha(R/'resume_kit7_nav8_generation.js')"""
assert s.count(old)==1;p.write_text(s.replace(old,new),encoding='utf-8')
p=R/'test_nav8_recovered_exit.py';s=p.read_text(encoding='utf-8')
needle="[('generator_after','pid',71041),";replacement="[('generation','started_utc','2026-10-27T02:00:00Z'),('generator_after','created_utc','2026-10-27T02:40:00Z'),('generator_after','pid',71041),";assert s.count(needle)==1;p.write_text(s.replace(needle,replacement),encoding='utf-8')
oldreport=R/'kit7-nav8-recovered-exit-controls.json';target=R/'kit7-nav8-recovered-exit-controls-before-review.json';assert not target.exists();oldreport.rename(target)
q=subprocess.run([sys.executable,'-I',str(p)],capture_output=True)
(O/'controls.stdout.log').write_bytes(q.stdout);(O/'controls.stderr.log').write_bytes(q.stderr)
assert q.returncode==0,q.stderr.decode(errors='replace')
checks=read(oldreport);assert checks['count']==23 and checks['status']=='PASS_RECOVERY_CLASSIFIER_CONTROLS' and not checks['native_acceptance']
assert all(sha(p)==h for p,h in checks['sources'].items())
paths=[Path(p) for p in before]
paths += [O/n for n in ['source-hashes.json','brief.md','response.json','completion.json','reviewed-archive.json','controls.stdout.log','controls.stderr.log']]
paths += [Path(x['archived']) for x in rows]+[Path(__file__),target]
write(O/'accepted.json',dict(status='ACCEPTED_AFTER_REVIEW',scope='Same-run unexecuted cancellation intent classifier and recovered packer. Geometric/native607 tolerances unchanged.',review_verdict='SOUND-with-fixes',fixes_closed=['All thirteen recovery inputs mandatory in gate; resume hash cross-checked.','Restarted wrapper and reused PID negative controls added and passed.'],inputs={str(p):sha(p) for p in paths},control_count=23,native_generation_acceptance=False,limits=['Generator remains running. No package or native graph acceptance before completed generation and original orderly-close/RPT/observer gates.','Never re-run the live resume coordinator; use only its existing cell541.']))
print(json.dumps(dict(status='ACCEPTED_AFTER_REVIEW',control_count=23,inputs=len(read(O/'accepted.json')['inputs']),next='Only package_and_deploy_kit7_nav8_recovered.py after actual generation and close complete')))
