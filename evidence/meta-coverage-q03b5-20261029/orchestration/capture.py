from pathlib import Path
import json,hashlib,time,sys
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'q03b5-local-author-20261029'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(R));import council29_runner as runner
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
pins=load(D/'correction-delivery.json')['files'];start=load(D/'correction-start.json')
timing={}
for n,h in pins.items():
 assert sha(D/n)==h
 timing[n]=(D/n).stat().st_mtime
 assert timing[n]<=start['deadline']
assert sha(D/'contract.json')=='8b5b2476baf8963304e2ed285b161db39ea936828384184dfddb6bb964b5a1cc'
c=load(D/'contract.json');assert sha(D/'oracle.json')==c['oracle_sha256']
assert sha(W/'plans/quality-council-q03b5-meta-coverage-witness-20261029.md')==c['plan_sha256']
for pin in [c['scene'],c['writer'],c['failure'],*c['helpers'].values()]:assert sha(pin['path'])==pin['sha256']
suite=load(R/'q03b5-private-suite-r2-20261029/completion.json')
assert suite['rc']==0 and suite['reason'] is None
assert 'Ran 9 tests' in (R/'q03b5-private-suite-r2-20261029/stderr').read_text()
assert 'claude-fable-5-1' in load(D/'review-identity.json')
approval={'status':'AUTHORIZED_SINGLE_META_DIAGNOSTIC','time':time.time(),'source_code':pins,'contract_sha256':sha(D/'contract.json'),'oracle_sha256':sha(D/'oracle.json'),'private_methods':9,'review':'Fable SOUND-with-fixes, H1/H2/H6 adjudicated and narrow delta integrated','external_postimage_review':False,'author_integrator_shared_context':True,'correction_file_mtimes':timing,'correction_receipt_late_seconds':load(D/'correction-delivery.json')['completed']-start['deadline'],'timing_scope':'Patch completed in previous tool invocation at correction start; mtimes support that observation. Receipt written after context compaction 0.611s beyond deadline, retained as late; no code changes after deadline. No continuous identity claim.','suite_r1':'9 setup errors: new temporary root was not created; R2 only prepares root, code hashes identical.','scope':'one pinned historical prototype archive plus saved metadata; no geometry interpretation, other archives, map or DayZ','output_cap':4194304}
with (D/'capture-approval.json').open('x',encoding='utf-8') as f:json.dump(approval,f,indent=2)
py='C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe'
def job(name,script,args):return {'id':name,'command':[py,'-I','-X','utf8',str(D/script),str(D/'contract.json'),approval['contract_sha256'],*args],'cwd':str(D),'out':str(R/(name+'-20261029')),'seconds':60,'max_bytes':268435456,'input_file':str(D/script)}
p=runner.run(job('q03b5-real-producer-receipts','meta_coverage_producer_q03b5.py',[c['output']]))
print(json.dumps(p),flush=True);result={'producer':p,'consumer':None,'map_modified':False}
if p['rc']==0 and p['reason'] is None:
 report=Path(c['output'])/'report.json';assert report.stat().st_size<=4194304
 before=sha(report);saved=load(report)
 assert saved['status']=='META_COVERAGE_DIAGNOSTIC' and saved['contract_sha256']==approval['contract_sha256']
 result['consumer']=runner.run(job('q03b5-real-consumer-receipts','meta_coverage_consumer_q03b5.py',[str(report),c['consumer_output']]))
 print(json.dumps(result['consumer']),flush=True)
 assert sha(report)==before
 result['report_sha256']=before;result['report_bytes']=report.stat().st_size
for n,h in pins.items():assert sha(D/n)==h
with (D/'capture-result.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
