# Recover only conversion 2 from a verified saved snapshot.
# Memory enforcement: the 512 MiB unit RSS limit in the contract is NOT self-checked here.
# It must be enforced by the mandatory external bounded runner supervising this process (unit window 90 s).
# This process only enforces its internal 90 s deadline. Child limits 30 s / 256 MiB are carried in the pinned runner job.
import argparse,hashlib,importlib.util,json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_road_material_snapshot_ev112 as V
def _sha(b): return hashlib.sha256(b).hexdigest()
def _canon(o): return (json.dumps(o,ensure_ascii=False,indent=2,sort_keys=True)+chr(10)).encode()
def _norm(o): return json.loads(json.dumps(o,ensure_ascii=False,sort_keys=True))
def _write(p,data,mode='xb'):
 p.parent.mkdir(parents=True,exist_ok=True); V._assert_no_reparse_ancestors(p)
 with open(p,mode) as f: f.write(data); f.flush(); os.fsync(f.fileno())
def _wj(p,obj,overwrite=False): _write(p,_canon(obj),'wb' if overwrite else 'xb')
def _load_runner(contract):
 rp=contract['tools']['runner']['path']
 if V._hash_file(rp)!=contract['tools']['runner']['sha256']: raise V.SnapshotError('runner_hash')
 spec=importlib.util.spec_from_file_location('pinned_runner_ev112',rp); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod.run
def _state(c):
 tools={}
 for name,pin in [(c['tools']['runner']['path'],c['tools']['runner']['sha256']),(c['tools']['cfgconvert']['path'],c['tools']['cfgconvert']['sha256'])]+list(c['tools']['dependencies'].items()):
  h=V._hash_file(name)
  if h!=pin: raise V.SnapshotError('tool_changed:'+name)
  tools[name]=h
 snap={}
 root=Path(c['snapshot_root'])
 for rel,pin in c['pins'].items():
  h=V._hash_file(root/rel)
  if h!=pin: raise V.SnapshotError('snapshot_changed:'+rel)
  snap[rel]=h
 return {'tools':tools,'snapshot':snap}
def recover(contract_path,sha,runner_call=None):
 t0=time.monotonic(); phases=[]; created_out=False; out=None
 def check():
  if time.monotonic()-t0>90: raise V.SnapshotError('unit_deadline')
  phases.append(round(time.monotonic()-t0,6))
 snap=V.verify_snapshot(contract_path,sha); check(); c=snap['contract']; blobs=snap['blobs']; out=Path(c['output']); marker=Path(c['attempt_marker'])
 V._assert_no_reparse_ancestors(marker); marker.parent.mkdir(parents=True,exist_ok=True); V._assert_no_reparse_ancestors(marker)
 with open(marker,'xb') as f: f.write((json.dumps({'contract_sha256':sha,'output':c['output'],'status':'ATTEMPT_CONSUMED'},sort_keys=True)+chr(10)).encode()); f.flush(); os.fsync(f.fileno())
 try:
  V._assert_no_reparse_ancestors(out); out.mkdir(parents=True,exist_ok=False); created_out=True; check()
  report_path=out/'report.json'; original=V._strict(blobs[c['roles']['report']])
  for a in original['assets']:
   dest=out/'snapshot'/a['local_path']; _write(dest,blobs[a['local_path']])
   if V._read_bounded(dest,c['limits']['file_bytes'])!=blobs[a['local_path']]: raise V.SnapshotError('copy_hash')
  text1rel=c['roles']['conversion1_text']; _write(out/'snapshot'/text1rel,blobs[text1rel]); check()
  input2=out/'snapshot'/c['roles']['material2']
  if _sha(V._read_bounded(input2,c['limits']['file_bytes']))!=c['pins'][c['roles']['material2']]: raise V.SnapshotError('input2_hash')
  text2=Path(c['conversion2_text']); receipt=Path(c['conversion2_receipt'])
  if os.path.lexists(text2) or os.path.lexists(receipt): raise V.SnapshotError('conversion2_dest_exists')
  text2.parent.mkdir(parents=True,exist_ok=True); receipt.parent.mkdir(parents=True,exist_ok=True); V._assert_no_reparse_ancestors(text2); V._assert_no_reparse_ancestors(receipt); check()
  job={'id':'conversion_2','command':[c['tools']['cfgconvert']['path'],'-txt','-dst',str(text2),str(input2)],'cwd':str(out),'out':str(receipt),'seconds':30,'max_bytes':268435456,'input_file':str(input2)}
  _wj(out/'job.json',job); _wj(out/'phases.json',{'phases':list(phases)}); check()
  before=_state(c); run=runner_call or _load_runner(c); check()
  result=run(job); check(); _wj(out/'phases.json',{'phases':list(phases)},overwrite=True)
  if not isinstance(result,dict): raise V.SnapshotError('runner_no_delivery')
  after=_state(c)
  if after!=before: raise V.SnapshotError('state_changed_during_runner')
  raw={}
  for name in ('running.json','completion.json','stdout','stderr'):
   p=receipt/name
   if not p.is_file(): raise V.SnapshotError('receipt_partial:'+name)
   raw[name]=V._read_bounded(p,c['limits']['file_bytes'])
  runj=V._strict(raw['running.json']); done=V._strict(raw['completion.json'])
  try: normalized=_norm(result); expected={'id':job['id'],**_norm(done)}
  except Exception as e: raise V.SnapshotError('runner_return_not_serializable:'+repr(e))
  if normalized!=expected: raise V.SnapshotError('runner_return_mismatch')
  if not text2.is_file(): raise V.SnapshotError('text2_missing')
  tst=V._reparse(text2)
  if not (0<tst.st_size<=16777216): raise V.SnapshotError('text2_size')
  tb=V._read_bounded(text2,16777216); ib=V._read_bounded(input2,c['limits']['file_bytes'])
  if _sha(ib)!=c['pins'][c['roles']['material2']]: raise V.SnapshotError('input2_changed')
  meta=V.verify_receipt(runj,done,raw['stdout'],raw['stderr'],c['pins'][c['roles']['material2']],c['tools']['cfgconvert']['path'],expected_rc=0); check()
  t1=blobs[text1rel]
  rep={'schema':'ROAD_SAVED_MATERIAL_RECOVERY_V1','status':'MATERIAL_SAMPLES_RECOVERED_ONLY','build_ready':False,'dependency_closure':'NOT_EVALUATED','contract_sha256':sha,'texts':[{'path':str(out/'snapshot'/text1rel),'sha256':_sha(t1),'size':len(t1)},{'path':str(text2),'sha256':_sha(tb),'size':len(tb)}],'receipt_2':meta,'receipt_2_pins':{n:_sha(raw[n]) for n in ('running.json','completion.json','stdout','stderr')},'original_report_sha256':c['pins'][c['roles']['report']],'assets':8,'conversions':2}
  _write(report_path,_canon(rep)); _wj(out/'phases.json',{'phases':list(phases),'status':rep['status']},overwrite=True); check()
  validated=V.verify_recovery(contract_path,sha)
  if validated!=rep: raise V.SnapshotError('final_consumer_mismatch')
  return validated
 except Exception as e:
  if created_out and out is not None:
   try:
    failed=out/'failure.json' if (out/'report.json').exists() else out/'report.json'
    _write(failed,_canon({'status':'INCONCLUSIVE_RECOVERY','error':repr(e),'build_ready':False,'dependency_closure':'NOT_EVALUATED'}))
   except Exception: pass
  raise
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--contract',required=True); ap.add_argument('--contract-sha256',required=True); a=ap.parse_args(argv)
 try: rep=recover(a.contract,a.contract_sha256)
 except Exception as e: print(json.dumps({'status':'INCONCLUSIVE_RECOVERY','error':repr(e)}),file=sys.stderr); return 1
 print(json.dumps(rep,ensure_ascii=False,indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
