from pathlib import Path
import json,hashlib,sys,time
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1b-local-author-20261029';O=R/'road-c1b-real-20261029'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins={'contract.json':'b7d335883f33629f8e9fc1f1b98018dadb2cb95541a33a643f6805a3bcb3d1c6','bindings.json':'b632818ad796320ef60c33cc65125683c2ac7f40bd6080afed8d85c98154f052','oracle.json':'677c4561ac867a0fbfc5a1edeaf1da59b6b63c03063821154cedc549b91d5429','stage_road_lab_c1b.py':'b01ff8d2ae6a6f4fde7ef226730cbc6d0c681958a57366f831eacea721075882','verify_road_lab_c1b.py':'774e032a7b4ceaffc10d340d280f8a62385d62b9e8d4290e52d41983257a3e98','test_road_lab_c1b.py':'85ab746a6f577129d6d50a783fc62fe7f8fba9c0b4c6356d4dd7ab770affd027'}
assert all(sha(D/f)==v for f,v in pins.items())
suite=json.loads((D/'tests-R1/completion.json').read_bytes());assert suite['rc']==0 and suite['reason'] is None
review=R/'road-c1b-code-review-20261029';assert 'SOUND-with-fixes' in (review/'review.md').read_text(encoding='utf-8')
assert json.loads((D/'correction-completion.json').read_bytes())['within_budget']
approval={'status':'APPROVED_FOR_SINGLE_STAGE_AND_CONSUMER','review':'Muse native157.5s SOUND-with-fixes','corrections':'Config refs consistency and ancestor collision, repro saved; 18 tests R1 pass','integrator':'Codex same author context, no external rereview of postimage','pins':pins,'limits':'Byte stage only; no DayZ tools/build/native/map','time':time.time()}
(D/'approval.json').write_text(json.dumps(approval,indent=2),encoding='utf-8')
O.mkdir(exist_ok=False)
sys.path.insert(0,str(R));import council29_runner as runner
py='C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe'
common=[py,'-I','-X','utf8'];args=['--contract',str(D/'contract.json'),'--sha',pins['contract.json'],'--bindings-sha',pins['bindings.json']]
for role,script,extra in [('producer','stage_road_lab_c1b.py',[]),('consumer','verify_road_lab_c1b.py',['--report',str(O/'consumer.json')])]:
 job={'id':role,'command':common+[str(D/script)]+args+extra,'input_file':str(D/'contract.json'),'cwd':str(D),'out':str(O/role),'seconds':120,'max_bytes':268435456}
 (O/(role+'-job.json')).write_text(json.dumps(job,indent=2));r=runner.run(job);print(json.dumps(r),flush=True)
 if r['rc']!=0 or r['reason'] is not None:
  (O/'stopped.json').write_text(json.dumps({'role':role,'receipt':r},indent=2));sys.exit(2)
result=json.loads((O/'consumer.json').read_bytes());assert result['status']=='VERIFIED_LAB_STAGE_BYTES_ONLY';(O/'result.json').write_text(json.dumps({'status':result['status'],'contract_sha256':pins['contract.json'],'consumer_sha256':sha(O/'consumer.json'),'producer_sha256':sha(R/'road-c1b-stage-20261029/producer.json'),'python_sha256':sha(py),'map_changed':False},indent=2));print((O/'result.json').read_text())
