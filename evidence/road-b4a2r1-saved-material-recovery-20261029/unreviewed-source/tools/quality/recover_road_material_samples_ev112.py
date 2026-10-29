"""Recover only conversion 2 from verified saved snapshot."""
import argparse,hashlib,importlib.util,json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_road_material_snapshot_ev112 as V
def _sha(b): return hashlib.sha256(b).hexdigest()
def _write(p,data,mode='xb'):
 p.parent.mkdir(parents=True,exist_ok=True)
 with open(p,mode) as f: f.write(data); f.flush(); os.fsync(f.fileno())
def _wj(p,obj): _write(p,(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode(),'wb' if p.exists() else 'xb')
def _rss():
 try:
  import psutil; return psutil.Process().memory_info().rss
 except Exception: return 0
def _load_runner(contract):
 rp=contract['tools']['runner']['path']
 if V._hash_file(rp)!=contract['tools']['runner']['sha256']: raise V.SnapshotError('runner_hash')
 spec=importlib.util.spec_from_file_location('pinned_runner_ev112',rp); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod.run
def recover(contract_path,sha,runner_call=None):
 t0=time.monotonic(); phases=[]
 def check():
  if time.monotonic()-t0>90: raise V.SnapshotError('unit_deadline')
  if _rss()>536870912: raise V.SnapshotError('unit_rss')
  phases.append(round(time.monotonic()-t0,6))
 snap=V.verify_snapshot(contract_path,sha); check(); c=snap['contract']; blobs=snap['blobs']; out=Path(c['output']); marker=Path(c['attempt_marker'])
 marker.parent.mkdir(parents=True,exist_ok=True)
 with open(marker,'xb') as f: f.write((json.dumps({'contract_sha256':sha,'output':c['output'],'status':'ATTEMPT_CONSUMED'},sort_keys=True)+'\n').encode()); f.flush(); os.fsync(f.fileno())
 try:
  out.mkdir(parents=True,exist_ok=False); check()
  report_path=out/'report.json'
  for a in V._strict(blobs[c['roles']['report']])['assets']:
   dest=out/'snapshot'/a['local_path']; _write(dest,blobs[a['local_path']]); 
   if _sha(dest.read_bytes())!=a['sha256']: raise V.SnapshotError('copy_hash')
  text1rel=c['roles']['conversion1_text']; _write(out/'snapshot'/text1rel,blobs[text1rel]); check()
  input2=out/'snapshot'/c['roles']['material2']
  if _sha(input2.read_bytes())!=c['pins'][c['roles']['material2']]: raise V.SnapshotError('input2_hash')
  text2=Path(c['conversion2_text']); receipt=Path(c['conversion2_receipt'])
  if text2.exists() or receipt.exists(): raise V.SnapshotError('conversion2_dest_exists')
  text2.parent.mkdir(parents=True,exist_ok=True); receipt.parent.mkdir(parents=True,exist_ok=True)
  job={'id':'conversion_2','command':[c['tools']['cfgconvert']['path'],'-txt','-dst',str(text2),str(input2)],'cwd':str(out),'out':str(receipt),'seconds':30,'max_bytes':268435456,'input_file':str(input2)}
  _wj(out/'job.json',job); _wj(out/'phases.json',{'phases':phases}); check()
  run=runner_call or _load_runner(c); check()
  result=run(job); check(); _wj(out/'phases.json',{'phases':phases,'runner_result':result})
  if not isinstance(result,dict): raise V.SnapshotError('runner_no_delivery')
  for name in ('running.json','completion.json','stdout','stderr'):
   if not (receipt/name).is_file(): raise V.SnapshotError('receipt_partial:'+name)
  if V._hash_file(c['tools']['cfgconvert']['path'])!=c['tools']['cfgconvert']['sha256']: raise V.SnapshotError('tool_changed')
  if _sha(input2.read_bytes())!=c['pins'][c['roles']['material2']]: raise V.SnapshotError('input2_changed')
  if not text2.is_file(): raise V.SnapshotError('text2_missing')
  tb=text2.read_bytes()
  if not (0<len(tb)<=16777216): raise V.SnapshotError('text2_size')
  st=text2.stat(); _= (st.st_mtime,st.st_ctime)
  runj=V._strict((receipt/'running.json').read_bytes()); done=V._strict((receipt/'completion.json').read_bytes())
  meta=V.verify_receipt(runj,done,(receipt/'stdout').read_bytes(),(receipt/'stderr').read_bytes(),_sha(input2.read_bytes()),c['tools']['cfgconvert']['path'],expected_rc=0); check()
  t1=blobs[text1rel]
  rep={'status':'MATERIAL_SAMPLES_RECOVERED_ONLY','build_ready':False,'dependency_closure':'NOT_EVALUATED','texts':[{'path':str(out/'snapshot'/text1rel),'sha256':_sha(t1),'size':len(t1)},{'path':str(text2),'sha256':_sha(tb),'size':len(tb)}],'receipt_2':meta,'receipt_2_pins':{n:_sha((receipt/n).read_bytes()) for n in ('running.json','completion.json','stdout','stderr')},'original_report_sha256':c['pins'][c['roles']['report']],'assets':8,'conversions':2}
  _write(report_path,(json.dumps(rep,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()); _wj(out/'phases.json',{'phases':phases,'status':rep['status']}); check(); return rep
 except Exception as e:
  try:
   if out.is_dir(): _write(out/'report.json',(json.dumps({'status':'INCONCLUSIVE_RECOVERY','error':repr(e),'build_ready':False,'dependency_closure':'NOT_EVALUATED'},indent=2,sort_keys=True)+'\n').encode(),'wb')
  except Exception: pass
  raise
def verify_recovery(contract_path,sha):
 snap=V.verify_snapshot(contract_path,sha); c=snap['contract']; out=Path(c['output']); rep=V._strict((out/'report.json').read_bytes())
 if rep.get('status')!='MATERIAL_SAMPLES_RECOVERED_ONLY' or rep.get('build_ready') is not False or rep.get('dependency_closure')!='NOT_EVALUATED': raise V.SnapshotError('recovery_report')
 texts=rep.get('texts')
 if not isinstance(texts,list) or len(texts)!=2: raise V.SnapshotError('texts_2')
 for t in texts:
  b=Path(t['path']).read_bytes()
  if _sha(b)!=t.get('sha256') or len(b)!=t.get('size') or not b: raise V.SnapshotError('text_hash')
 receipt=Path(c['conversion2_receipt']); runj=V._strict((receipt/'running.json').read_bytes()); done=V._strict((receipt/'completion.json').read_bytes()); input2=out/'snapshot'/c['roles']['material2']
 V.verify_receipt(runj,done,(receipt/'stdout').read_bytes(),(receipt/'stderr').read_bytes(),_sha(input2.read_bytes()),c['tools']['cfgconvert']['path'],expected_rc=0); return rep
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--contract',required=True); ap.add_argument('--contract-sha256',required=True); a=ap.parse_args(argv)
 try: rep=recover(a.contract,a.contract_sha256)
 except Exception as e: print(json.dumps({'status':'INCONCLUSIVE_RECOVERY','error':repr(e)}),file=sys.stderr); return 1
 print(json.dumps(rep,ensure_ascii=False,indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
