from pathlib import Path
import copy,hashlib,json,sys
R=Path(__file__).parent;D=R/'nav-kit7-8m-preparation-20261027'
sys.path.insert(0,str(R))
from verify_nav8_recovered_exit import verify_recovery,RUN
from verify_c_orderly_close import validate_generation_exit as original
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
proof=dict(cancel_file_exists=False,wrapper_cancel_file_exists=False,
 original_completion=read(D/'completion-before-lease-recovery.json'),original_cleanup=read(D/'cleanup-before-lease-recovery.json'),
 generator_before=read(D/'generator-identity.json'),generator_after=read(D/'generator-after-unexecuted-cancel.json'),
 generation=dict(run_id=RUN,status='GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION',returncode=0,inputs_unchanged=True,failure_reasons=[],started_utc='2026-10-27T01:59:33Z',finished_utc='2026-10-27T04:00:00Z'),
 completion=dict(run_id=RUN,status='GENERATION_STAGE_COMPLETE_PENDING_VALIDATION',error=None,cleanup_error=None),
 progress=[json.loads(x) for x in (D/'progress.jsonl').read_text(encoding='utf-8-sig').splitlines()],
 mcp_recovered=read(D/'mcp-recovered.json'),mcp_before=read(D/'mcp-before.json'))
events=[json.loads(x) for x in (D/'timeline.jsonl').read_text(encoding='utf-8-sig').splitlines()]
events.append(dict(event='CLOSE_INTENT',run_id=RUN,utc='2026-10-27T04:00:01Z'))
observer=dict(status='EXIT_OBSERVED',error=None,exit_code=0,observed_utc='2026-10-27T04:00:05Z')
rows=[]
def reject(name,p=None,e=None,o=None,legacy=False):
 try:
  if legacy:original(observer,events,RUN)
  else:verify_recovery(o or observer,e or events,RUN,p or proof)
 except (AssertionError,KeyError,TypeError,ValueError):rows.append(dict(name=name,status='PASS_REJECTED'))
 else:raise AssertionError('Unexpected acceptance '+name)
reject('original_still_rejects_raw_timeline',legacy=True)
assert verify_recovery(observer,events,RUN,proof)==0;rows.append(dict(name='same_run_unexecuted_intent_synthetic_close',status='PASS'))
for field in ('cancel_file_exists','wrapper_cancel_file_exists'):
 p=copy.deepcopy(proof);p[field]=True;reject(field,p=p)
for obj,key,value in [('generation','started_utc','2026-10-27T02:00:00Z'),('generator_after','created_utc','2026-10-27T02:40:00Z'),('generator_after','pid',71041),('generator_after','parent_pid',59941),('generator_after','command_line_sha256','changed'),('generator_after','observed_utc','2026-10-27T02:30:00Z'),('generation','returncode',1),('generation','returncode',False),('generation','status','STARTED'),('generation','run_id','other'),('completion','error','incomplete'),('original_completion','status','INCONCLUSIVE')]:
 p=copy.deepcopy(proof);p[obj][key]=value;reject(obj+'.'+key+'.'+str(value),p=p)
p=copy.deepcopy(proof);p['progress']=[x for x in p['progress'] if x['utc']<'2026-10-27T02:34'];reject('no_progress_after_intent',p=p)
p=copy.deepcopy(proof);p['mcp_recovered']['processes'][0]['pid']=46289;reject('changed_recovered_server',p=p)
e=copy.deepcopy(events);e.append(copy.deepcopy(next(x for x in e if x['event']=='GENERATOR_CANCEL_INTENT')));reject('second_cancel_intent',e=e)
e=copy.deepcopy(events);next(x for x in e if x['event']=='GENERATOR_CANCEL_INTENT')['utc']='2026-10-27T02:34:30Z';reject('different_intent_time',e=e)
e=copy.deepcopy(events);e.append(dict(event='SERVER_EXIT_OBSERVED',run_id=RUN,utc='2026-10-27T03:00:00Z'));reject('server_exit_before_close',e=e)
reject('unknown_server_exit_code',o={**observer,'exit_code':123})
reject('server_exit_too_late',o={**observer,'observed_utc':'2026-10-27T04:01:00Z'})
out=R/'kit7-nav8-recovered-exit-controls.json';assert not out.exists()
result=dict(status='PASS_RECOVERY_CLASSIFIER_CONTROLS',cases=rows,count=len(rows),native_acceptance=False,limits=['Current identity/progress inputs, synthetic future generation and termination. No runtime result.'],sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'verify_nav8_recovered_exit.py',R/'verify_c_orderly_close.py',Path(__file__)]})
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
