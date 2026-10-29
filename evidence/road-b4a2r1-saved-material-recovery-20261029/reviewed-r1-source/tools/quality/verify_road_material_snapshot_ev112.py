# Independent saved-snapshot verifier. No extractor/recoverer imports.
import argparse,hashlib,json,math,os,re,stat,sys
from pathlib import Path
SHA=re.compile(r'^[0-9a-f]{64}$')
LIMITS={'unit_seconds':90,'unit_rss_bytes':536870912,'child_seconds':30,'child_rss_bytes':268435456,'file_bytes':16777216,'total_snapshot_bytes':33554432}
ROLES={'report':'report.json','manifest':'manifest.json','original_contract':'original-contract.json','original_approval':'original-approval.json','failed_code':'code-failed.py','corrected_code':'code-corrected.py','parent_receipt':'parent','conversion1_receipt':'receipts/conversion_1','conversion1_text':'decoded/dz/structures/roads/parts/data/asf1_dashedline.rvmat.txt','material1':'assets/dz/structures/roads/parts/data/asf1_dashedline.rvmat','material2':'assets/dz/structures/roads/parts/data/asf2_dashedline.rvmat'}
CK={'schema','snapshot_root','pins','roles','tools','output','attempt_marker','conversion2_receipt','conversion2_text','limits','build_ready','dependency_closure'}
REPORT_KEYS={'schema','status','build_ready','dependency_closure','contract_sha256','original_report_sha256','assets','conversions','texts','receipt_2','receipt_2_pins'}
TEXT_KEYS={'path','sha256','size'}
JOB_KEYS={'id','command','cwd','out','seconds','max_bytes','input_file'}
BS=chr(92)
PREFIXES={'roads':BS.join(('DZ','structures','roads')),'surfaces':BS.join(('DZ','surfaces')),'surfaces_bliss':BS.join(('DZ','surfaces_bliss'))}
class SnapshotError(ValueError): pass
def _err(m): raise SnapshotError(m)
def _sha(b): return hashlib.sha256(b).hexdigest()
def _is_sha(x): return isinstance(x,str) and bool(SHA.match(x))
def _is_int(x): return type(x) is int
def _strict(b):
 def hook(pairs):
  d={}
  for k,v in pairs:
   if k in d: _err('duplicate_key:'+k)
   d[k]=v
  return d
 def bad(x): _err('nonfinite:'+x)
 try: return json.loads(b.decode('utf-8'),object_pairs_hook=hook,parse_constant=bad)
 except SnapshotError: raise
 except Exception as e: _err('json:'+repr(e))
def _num(x): return type(x) in (int,float) and math.isfinite(float(x))
def _reparse(p):
 try: st=os.lstat(p)
 except FileNotFoundError: _err('missing:'+str(p))
 except OSError as e: _err('stat:'+repr(e))
 if stat.S_ISLNK(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400: _err('reparse:'+str(p))
 return st
def _assert_no_reparse_ancestors(p):
 ap=Path(os.path.abspath(str(p))); chain=[]; cur=ap
 while True:
  chain.append(cur)
  if cur.parent==cur: break
  cur=cur.parent
 for part in reversed(chain):
  if os.path.lexists(part): _reparse(part)
def _mtime(p): return Path(p).stat().st_mtime
def _abs(x): return isinstance(x,str) and bool(x) and Path(x).is_absolute()
def _rel(x):
 if not isinstance(x,str) or not x or chr(92) in x or x.startswith('/') or re.match(r'^[A-Za-z]:',x): _err('unsafe_rel:'+str(x))
 if Path(x).is_absolute() or any(p in ('','..') for p in x.split('/')): _err('unsafe_rel:'+x)
 return x
def _read_bounded(p,limit):
 st=_reparse(p)
 if not stat.S_ISREG(st.st_mode): _err('not_file:'+str(p))
 if st.st_size>limit: _err('file_limit:'+str(p))
 b=Path(p).read_bytes()
 if len(b)!=st.st_size: _err('size_race:'+str(p))
 return b
def _hash_file(p):
 _assert_no_reparse_ancestors(p); _reparse(p); h=hashlib.sha256()
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1048576),b''): h.update(c)
 return h.hexdigest()
def load_contract(path,expected_hash):
 if not _is_sha(expected_hash): _err('expected_hash')
 _assert_no_reparse_ancestors(path); raw=_read_bounded(path,LIMITS['file_bytes'])
 if _sha(raw)!=expected_hash: _err('contract_hash_before_parse')
 c=_strict(raw)
 if not isinstance(c,dict) or set(c)!=CK: _err('contract_closed_keys')
 if c['schema']!='ROAD_SAVED_MATERIAL_RECOVERY_V1': _err('schema')
 if c['build_ready'] is not False or c['dependency_closure']!='NOT_EVALUATED': _err('contract_flags')
 if c['limits']!=LIMITS or any(type(v) is not int for v in c['limits'].values()): _err('limits_exact')
 if c['roles']!=ROLES: _err('roles_exact')
 for k in ('snapshot_root','output','attempt_marker','conversion2_receipt','conversion2_text'):
  if not _abs(c[k]): _err('absolute:'+k)
 out=Path(c['output'])
 if Path(c['conversion2_receipt'])!=out/'receipts'/'conversion_2': _err('conversion2_receipt_fixed')
 if Path(c['conversion2_text'])!=out/'decoded'/'asf2_dashedline.rvmat.txt': _err('conversion2_text_fixed')
 try:
  Path(c['attempt_marker']).relative_to(out)
 except ValueError:
  pass
 else:
  _err('marker_inside_output')
 _assert_no_reparse_ancestors(c['snapshot_root']); _reparse(c['snapshot_root'])
 for k in ('output','attempt_marker','conversion2_receipt','conversion2_text'):
  _assert_no_reparse_ancestors(c[k])
 pins=c['pins']
 if not isinstance(pins,dict) or len(pins)!=23: _err('pins_23')
 for k,v in pins.items():
  _rel(k)
  if not _is_sha(v): _err('pin_sha')
 for r in ROLES.values():
  if r in ('parent','receipts/conversion_1'): continue
  if r not in pins: _err('role_pin_missing:'+r)
 for pre in ('parent','receipts/conversion_1'):
  for n in ('running.json','completion.json','stdout','stderr'):
   if pre+'/'+n not in pins: _err('receipt_pin_missing:'+pre+'/'+n)
 t=c['tools']
 if not isinstance(t,dict) or set(t)!={'runner','cfgconvert','dependencies'}: _err('tools_keys')
 for k in ('runner','cfgconvert'):
  if not isinstance(t[k],dict) or set(t[k])!={'path','sha256'} or not _abs(t[k]['path']) or not _is_sha(t[k]['sha256']): _err('tool:'+k)
  _assert_no_reparse_ancestors(t[k]['path'])
 if not isinstance(t['dependencies'],dict) or not t['dependencies']: _err('deps')
 for k,v in t['dependencies'].items():
  if not _abs(k) or not _is_sha(v): _err('dep')
  _assert_no_reparse_ancestors(k)
 return c
def verify_receipt(running,done,stdoutbytes,stderrbytes,expected_input_sha,expected_executable,expected_rc=0,max_running_seconds=30,max_rss_bytes=268435456):
 if not isinstance(running,dict) or set(running)!={'pid','birth','started','seconds','executable','input_sha'}: _err('running_keys')
 if not isinstance(done,dict) or set(done)!={'rc','reason','seconds','peak_rss','started','finished','identities','stdout_sha','stderr_sha'}: _err('completion_keys')
 if not isinstance(stdoutbytes,(bytes,bytearray)) or not isinstance(stderrbytes,(bytes,bytearray)): _err('streams_bytes')
 pid=running['pid']
 if type(pid) is not int or pid<=0: _err('pid')
 if not _num(running['birth']) or float(running['birth'])<=0: _err('birth')
 if not _num(running['started']) or not _num(done['started']) or running['started']!=done['started']: _err('started_equal')
 if not _num(running['seconds']) or not (0<float(running['seconds'])<=max_running_seconds): _err('running_seconds')
 if not _num(done['seconds']) or not (0<=float(done['seconds'])<=float(running['seconds'])): _err('duration')
 if not _num(done['finished']) or not (float(running['started'])<=float(running['birth'])<=float(done['finished'])): _err('birth_window')
 ids=done['identities']
 if not isinstance(ids,dict) or str(pid) not in ids or ids[str(pid)]!=running['birth']: _err('identity')
 for k,v in ids.items():
  if not isinstance(k,str) or not k.isdigit() or not _num(v) or float(v)<=0: _err('identities')
 if type(done['rc']) is not int or done['rc']!=expected_rc: _err('rc_exact')
 if done['reason'] is not None: _err('reason_null')
 if type(done['peak_rss']) not in (int,float) or isinstance(done['peak_rss'],bool) or not math.isfinite(float(done['peak_rss'])) or not (0<=float(done['peak_rss'])<=max_rss_bytes): _err('peak_rss')
 if running['input_sha']!=expected_input_sha or not _is_sha(expected_input_sha): _err('input_sha')
 if running['executable']!=expected_executable or not isinstance(expected_executable,str): _err('executable_exact')
 if not _is_sha(done['stdout_sha']) or done['stdout_sha']!=_sha(bytes(stdoutbytes)): _err('stdout_sha')
 if not _is_sha(done['stderr_sha']) or done['stderr_sha']!=_sha(bytes(stderrbytes)): _err('stderr_sha')
 return {'pid':pid,'birth':running['birth'],'rc':done['rc'],'reason':None,'seconds':done['seconds'],'peak_rss':done['peak_rss'],'started':running['started'],'finished':done['finished'],'input_sha':running['input_sha'],'executable':running['executable'],'stdout_sha':done['stdout_sha'],'stderr_sha':done['stderr_sha']}
def verify_snapshot(contract_path,expected_hash):
 c=load_contract(contract_path,expected_hash); root=Path(c['snapshot_root']); _assert_no_reparse_ancestors(root); _reparse(root)
 if not root.is_dir(): _err('snapshot_root_dir')
 blobs={}; total=0
 for rel,pin in c['pins'].items():
  p=root/rel; _assert_no_reparse_ancestors(p); st=_reparse(p)
  if not p.is_file(): _err('snapshot_file:'+rel)
  if st.st_size>c['limits']['file_bytes']: _err('file_limit:'+rel)
  b=_read_bounded(p,c['limits']['file_bytes']); total+=len(b)
  if total>c['limits']['total_snapshot_bytes']: _err('total_limit')
  if _sha(b)!=pin: _err('pin_mismatch:'+rel)
  blobs[rel]=b
 report=_strict(blobs[ROLES['report']]); manifest=_strict(blobs[ROLES['manifest']]); old=_strict(blobs[ROLES['original_contract']]); appr=_strict(blobs[ROLES['original_approval']])
 if not all(isinstance(x,dict) for x in (report,manifest,old,appr)): _err('snapshot_docs')
 toolpairs=[(c['tools']['runner']['path'],c['tools']['runner']['sha256']),(c['tools']['cfgconvert']['path'],c['tools']['cfgconvert']['sha256'])]+list(c['tools']['dependencies'].items())
 for name,pin in toolpairs:
  if _hash_file(name)!=pin: _err('tool_hash:'+name)
 if old.get('cfgconvert')!=c['tools']['cfgconvert']['path'] or old.get('runner')!=c['tools']['runner']['path']: _err('old_tool_link')
 oldpins=old.get('pins',{})
 if not isinstance(oldpins,dict): _err('old_pins')
 for name,pin in toolpairs:
  if name in oldpins and oldpins[name]!=pin: _err('old_tool_pin:'+name)
 assets=report.get('assets')
 if not isinstance(assets,list) or len(assets)!=8 or not all(isinstance(a,dict) for a in assets): _err('assets_8')
 if len({a.get('virtual_path') for a in assets})!=8 or len({a.get('local_path') for a in assets})!=8: _err('assets_unique')
 sel=old.get('selected')
 if not isinstance(sel,list) or len(sel)!=7 or not all(isinstance(s,dict) for s in sel): _err('selected_7')
 selmap={}
 for s in sel:
  vp=s.get('virtual_path')
  if not isinstance(vp,str) or not vp or vp in selmap: _err('selected_unique')
  if not _is_sha(s.get('sha256')): _err('selected_sha')
  selmap[vp]=s
 extold=old.get('external')
 if not isinstance(extold,list) or len(extold)!=1 or not isinstance(extold[0],str): _err('external_old_1')
 byvirt={}
 for a in assets:
  if not _is_sha(a.get('sha256')) or not _is_int(a.get('size')) or a.get('size')<0: _err('asset_fields')
  byvirt[a.get('virtual_path')]=a
 for vp,s in selmap.items():
  a=byvirt.get(vp)
  if not a or a.get('sha256')!=s.get('sha256') or a.get('provider')!='roads': _err('selected_match:'+str(vp))
 ext=report.get('external')
 if not isinstance(ext,list) or len(ext)!=1 or not isinstance(ext[0],dict) or ext[0].get('virtual_path')!=extold[0] or ext[0].get('provider')!='surfaces' or ext[0].get('providers')!=['surfaces'] or not _is_sha(ext[0].get('sha256')): _err('external_literal')
 ea=byvirt.get(extold[0])
 if not ea or ea.get('provider')!='surfaces' or ea.get('sha256')!=ext[0].get('sha256'): _err('external_asset')
 if set(byvirt)!=set(selmap)|{extold[0]}: _err('assets_partition')
 for a in assets:
  lp=a.get('local_path'); _rel(lp)
  if lp not in blobs or lp not in c['pins']: _err('asset_pin:'+str(lp))
  b=blobs[lp]
  if a.get('sha256')!=c['pins'][lp] or a.get('size')!=len(b) or a.get('prefix16')!=b[:16].hex(): _err('asset_exact:'+lp)
 if manifest.get('report_sha256')!=_sha(blobs[ROLES['report']]): _err('manifest_report_sha')
 if manifest.get('contract_sha256')!=_sha(blobs[ROLES['original_contract']]) or report.get('contract_sha256')!=_sha(blobs[ROLES['original_contract']]): _err('contract_link')
 if manifest.get('assets')!=assets: _err('manifest_assets_exact')
 arts=manifest.get('artifacts')
 if not isinstance(arts,list) or len(arts)!=8 or not all(isinstance(x,dict) for x in arts) or {(x.get('local_path'),x.get('sha256'),x.get('size')) for x in arts}!={(a['local_path'],a['sha256'],a['size']) for a in assets}: _err('artifacts_8')
 if appr.get('contract_sha256')!=_sha(blobs[ROLES['original_contract']]): _err('approval_contract')
 if appr.get('tool_sha256')!=c['pins'][ROLES['failed_code']] or appr.get('tool_sha256')!=_sha(blobs[ROLES['failed_code']]): _err('approval_tool_failed')
 if _sha(blobs[ROLES['corrected_code']])!=c['pins'][ROLES['corrected_code']]: _err('corrected_pin')
 for doc in (report,manifest):
  if doc.get('status')!='INCONCLUSIVE_INITIAL_DISCOVERY' or doc.get('error')!='DiscoveryError:conversion_stream_missing' or doc.get('build_ready') is not False or doc.get('dependency_closure')!='NOT_EVALUATED': _err('historical_status')
 tables=report.get('tables')
 if not isinstance(tables,dict) or set(tables)!={'roads','surfaces','surfaces_bliss'}: _err('tables_3')
 pbos=old.get('pbos',{})
 if not isinstance(pbos,dict): _err('old_pbos')
 for name,t in tables.items():
  if not isinstance(t,dict): _err('table_dict:'+name)
  shas=[t.get('sha256_after'),t.get('sha256_observed'),t.get('sha256_observed_now')]
  if not all(_is_sha(x) for x in shas) or not (shas[0]==shas[1]==shas[2]): _err('table_sha:'+name)
  if t.get('prefix')!=PREFIXES[name]: _err('table_prefix:'+name)
  tp=t.get('path')
  if not isinstance(tp,str) or not (tp.startswith('/') or re.match(r'^[A-Za-z]:',tp)) or not tp.lower().endswith('.pbo'): _err('table_path:'+name)
  if not _is_int(t.get('entry_count')) or t['entry_count']<=0: _err('table_entry_count:'+name)
  if not _is_int(t.get('size')) or t['size']<=0: _err('table_size_type:'+name)
  for key in ('stat_before','stat_after'):
   sv=t.get(key)
   if not isinstance(sv,list) or len(sv)!=4 or not all(_is_int(x) for x in sv): _err('table_stat:'+name+':'+key)
  if t['stat_before']!=t['stat_after'] or t['stat_after'][2]!=t['size']: _err('table_stat_size:'+name)
  pb=pbos.get(name)
  if not isinstance(pb,dict) or pb.get('bytes')!=t['size']: _err('table_old_size:'+name)
  if 'sha256' in pb and (not _is_sha(pb.get('sha256')) or pb['sha256']!=shas[0]): _err('table_old_sha:'+name)
 def receipt(pre):
  return _strict(blobs[pre+'/running.json']),_strict(blobs[pre+'/completion.json']),blobs[pre+'/stdout'],blobs[pre+'/stderr']
 prun,pdone,pso,pse=receipt(ROLES['parent_receipt'])
 pmeta=verify_receipt(prun,pdone,pso,pse,_sha(blobs[ROLES['original_approval']]),prun.get('executable'),expected_rc=1,max_running_seconds=120,max_rss_bytes=536870912)
 crun,cdone,cso,cse=receipt(ROLES['conversion1_receipt'])
 cmeta=verify_receipt(crun,cdone,cso,cse,c['pins'][ROLES['material1']],c['tools']['cfgconvert']['path'],expected_rc=0)
 text=blobs[ROLES['conversion1_text']]
 if not (0<len(text)<=c['limits']['file_bytes']): _err('decoded1_size')
 for role in ('material1','material2'):
  if blobs[ROLES[role]][:4]!=bytes([0])+b'raP': _err('signature:'+role)
 result={'status':'SAVED_SNAPSHOT_VERIFIED_ONLY','assets':8,'conversions':1,'conversion_1':cmeta,'parent':pmeta,'historical_status':'INCONCLUSIVE_INITIAL_DISCOVERY','build_ready':False,'dependency_closure':'NOT_EVALUATED','report_sha256':c['pins'][ROLES['report']]}
 return {'contract':c,'blobs':blobs,'result':result}
def verify_recovery(contract_path,expected_hash):
 # Final consumer. It never trusts report.json as oracle: every value below is recomputed from contract-pinned snapshot bytes and raw output files.
 snap=verify_snapshot(contract_path,expected_hash); c=snap['contract']; blobs=snap['blobs']; out=Path(c['output']); root=Path(c['snapshot_root'])
 for p in (c['output'],c['attempt_marker'],c['conversion2_receipt'],c['conversion2_text']): _assert_no_reparse_ancestors(p)
 _reparse(out)
 if not out.is_dir(): _err('output_dir')
 rep_raw=_read_bounded(out/'report.json',c['limits']['file_bytes']); rep=_strict(rep_raw)
 if not isinstance(rep,dict) or set(rep)!=REPORT_KEYS: _err('recovery_report_closed_keys')
 if rep.get('schema')!='ROAD_SAVED_MATERIAL_RECOVERY_V1' or rep.get('status')!='MATERIAL_SAMPLES_RECOVERED_ONLY' or rep.get('build_ready') is not False or rep.get('dependency_closure')!='NOT_EVALUATED': _err('recovery_report')
 if rep.get('contract_sha256')!=expected_hash: _err('recovery_contract_sha256')
 if rep.get('original_report_sha256')!=c['pins'][ROLES['report']]: _err('recovery_original_pin')
 if rep.get('assets')!=8 or type(rep.get('assets')) is not int or rep.get('conversions')!=2 or type(rep.get('conversions')) is not int: _err('recovery_counts')
 marker_raw=_read_bounded(c['attempt_marker'],c['limits']['file_bytes']); marker=_strict(marker_raw)
 if marker!={'contract_sha256':expected_hash,'output':c['output'],'status':'ATTEMPT_CONSUMED'}: _err('marker_exact')
 snapout=out/'snapshot'; original=_strict(blobs[ROLES['report']]); assets=original['assets']
 for a in assets:
  dest=snapout/a['local_path']; _assert_no_reparse_ancestors(dest); b=_read_bounded(dest,c['limits']['file_bytes'])
  if b!=blobs[a['local_path']] or _sha(b)!=a['sha256'] or len(b)!=a['size']: _err('copy_exact:'+a['local_path'])
 text1rel=ROLES['conversion1_text']; text1dest=snapout/text1rel; _assert_no_reparse_ancestors(text1dest); text1=_read_bounded(text1dest,c['limits']['file_bytes'])
 if text1!=blobs[text1rel]: _err('text1_byteidentical')
 input2=snapout/ROLES['material2']; _assert_no_reparse_ancestors(input2); input2b=_read_bounded(input2,c['limits']['file_bytes'])
 if input2b!=blobs[ROLES['material2']] or _sha(input2b)!=c['pins'][ROLES['material2']]: _err('input2_fixed')
 texts=rep.get('texts')
 if not isinstance(texts,list) or len(texts)!=2 or not all(isinstance(x,dict) and set(x)==TEXT_KEYS for x in texts): _err('texts_2_closed')
 if texts[0]!={'path':str(text1dest),'sha256':_sha(text1),'size':len(text1)}: _err('text1_entry_fixed')
 text2=Path(c['conversion2_text']); receipt=Path(c['conversion2_receipt'])
 if text2!=out/'decoded'/'asf2_dashedline.rvmat.txt' or receipt!=out/'receipts'/'conversion_2': _err('conversion2_paths_fixed')
 job=_strict(_read_bounded(out/'job.json',c['limits']['file_bytes']))
 expected_job={'id':'conversion_2','command':[c['tools']['cfgconvert']['path'],'-txt','-dst',str(text2),str(input2)],'cwd':str(out),'out':str(receipt),'seconds':30,'max_bytes':268435456,'input_file':str(input2)}
 if job!=expected_job: _err('job_exact')
 raw={}
 for n in ('running.json','completion.json','stdout','stderr'):
  p=receipt/n; _assert_no_reparse_ancestors(p); raw[n]=_read_bounded(p,c['limits']['file_bytes'])
 if rep.get('receipt_2_pins')!={n:_sha(raw[n]) for n in raw}: _err('receipt2_pins')
 runj=_strict(raw['running.json']); done=_strict(raw['completion.json'])
 meta=verify_receipt(runj,done,raw['stdout'],raw['stderr'],c['pins'][ROLES['material2']],c['tools']['cfgconvert']['path'],expected_rc=0,max_running_seconds=30,max_rss_bytes=268435456)
 if rep.get('receipt_2')!=meta: _err('receipt2_meta')
 _assert_no_reparse_ancestors(text2); st=_reparse(text2); 
 if not (0<st.st_size<=c['limits']['file_bytes']): _err('text2_size')
 text2b=_read_bounded(text2,c['limits']['file_bytes'])
 if texts[1]!={'path':str(text2),'sha256':_sha(text2b),'size':len(text2b)}: _err('text2_entry_fixed')
 mt=_mtime(text2)
 if not (float(meta['started'])<=float(mt)<=float(meta['finished'])): _err('text2_stale_or_future')
 return rep
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--contract',required=True); ap.add_argument('--contract-sha256',required=True); ap.add_argument('--report'); ap.add_argument('--recovery',action='store_true'); a=ap.parse_args(argv)
 try: out=verify_recovery(a.contract,a.contract_sha256) if a.recovery else verify_snapshot(a.contract,a.contract_sha256)['result']
 except Exception as e: print(json.dumps({'status':'REJECTED','error':repr(e)}),file=sys.stderr); return 1
 data=(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+chr(10)).encode()
 if a.report:
  _assert_no_reparse_ancestors(a.report)
  with open(a.report,'xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
 print(data.decode()); return 0
if __name__=='__main__': raise SystemExit(main())
