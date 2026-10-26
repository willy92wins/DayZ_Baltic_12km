from pathlib import Path
import sys,json,copy,hashlib,datetime
R=Path(__file__).parent;sys.path.insert(0,str(R))
from verify_c_orderly_close import validate_close,validate_rpt,validate_generation_exit
V=R/'nav-c-retry-postprocess-review';O=V/'after-fixes';O.mkdir(exist_ok=True)
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
rows=[]
def case(label,fn,reject=False):
 failed=False
 try:fn()
 except (AssertionError,KeyError,ValueError,TypeError):failed=True
 assert failed==reject,label
 rows.append(dict(case=label,rejected=failed,passed=True))
c=dict(run_retired=True,graceful=True,exit_metrics_valid=True,stop_method='orderly_close',stop_required=False,reason=None,roles=[dict(role='server',termination_line=True,rpt_rotated=False)])
case('complete_official_close',lambda:validate_close(c))
for field,value in [('graceful',False),('exit_metrics_valid',False),('stop_method','terminate'),('stop_required',True),('reason','timeout'),('roles',[])]:
 case('reject_'+field,lambda field=field,value=value:validate_close({**c,field:value}),True)
events=[dict(run_id='fixture',event='CLOSE_INTENT',utc='2026-10-26T13:00:00Z')]
observer=dict(status='EXIT_OBSERVED',error=None,exit_code=0,observed_utc='2026-10-26T13:00:01Z')
for code in [0,-1,True,1,23,-1073741819,4294967295]:
 case('exit_'+str(code),lambda code=code:validate_generation_exit({**observer,'exit_code':code},events,'fixture'),type(code) is not int or code not in [0,-1])
for name,obs,ev,run in [('before_intent',{**observer,'observed_utc':'2026-10-26T12:59:59Z'},events,'fixture'),('after_deadline',{**observer,'observed_utc':'2026-10-26T13:00:31Z'},events,'fixture'),('wrong_run',observer,events,'other'),('duplicate_intent',observer,events*2,'fixture'),('premature_exit',observer,events+[dict(run_id='fixture',event='SERVER_EXIT_OBSERVED')],'fixture')]:
 case(name,lambda obs=obs,ev=ev,run=run:validate_generation_exit(obs,ev,run),True)
prior=R/'nav-c-data-preparation-v2-20261026';binding=read(prior/'rpt-binding.json');host=read(prior/'host-identity.json')
case('actual_prior_rpt_termination_bound',lambda:validate_rpt(binding,host,prior/'server.RPT'))
case('wrong_rpt_hash',lambda:validate_rpt({**binding,'sha256':'0'*64},host,prior/'server.RPT'),True)
case('wrong_rpt_mission',lambda:validate_rpt({**binding,'mission':'C:/wrong'},host,prior/'server.RPT'),True)
prior_events=[json.loads(x) for x in (prior/'timeline.jsonl').read_text(encoding='utf-8-sig').splitlines()]
prior_observer=read(prior/'observer/terminal.json')
case('actual_prior_early_human_close_still_rejected',lambda:validate_generation_exit(prior_observer,prior_events,host['run_id']),True)
data=dict(status='PASS_ORDERLY_CLOSE_CONTROLS',helper_sha256=sha(R/'verify_c_orderly_close.py'),test_sha256=sha(__file__),cases=rows,measured_prior=dict(observer_sha256=sha(prior/'observer/terminal.json'),rpt_sha256=sha(prior/'server.RPT'),exit_code=prior_observer['exit_code'],conclusion='Native orderly termination can return -1; this previous run remains rejected due to early exit. Not an initiator trace.'),limits='Synthetic positive close records and mutations plus actual prior early-exit negative; current C generation must supply its own complete native receipts.')
target=O/'close-controls.json';assert not target.exists();target.write_text(json.dumps(data,indent=2)+'\n');print(data['status'],len(rows))
