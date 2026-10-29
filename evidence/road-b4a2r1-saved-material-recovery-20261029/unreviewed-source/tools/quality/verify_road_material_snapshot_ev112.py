"""Independent saved-snapshot verifier. No extractor/recoverer imports."""
import argparse,hashlib,json,math,os,re,stat,sys
from pathlib import Path
SHA=re.compile(r'^[0-9a-f]{64}$')
LIMITS={"unit_seconds":90,"unit_rss_bytes":536870912,"child_seconds":30,"child_rss_bytes":268435456,"file_bytes":16777216,"total_snapshot_bytes":33554432}
ROLES={"report":"report.json","manifest":"manifest.json","original_contract":"original-contract.json","original_approval":"original-approval.json","failed_code":"code-failed.py","corrected_code":"code-corrected.py","parent_receipt":"parent","conversion1_receipt":"receipts/conversion_1","conversion1_text":"decoded/dz/structures/roads/parts/data/asf1_dashedline.rvmat.txt","material1":"assets/dz/structures/roads/parts/data/asf1_dashedline.rvmat","material2":"assets/dz/structures/roads/parts/data/asf2_dashedline.rvmat"}
CK={"schema","snapshot_root","pins","roles","tools","output","attempt_marker","conversion2_receipt","conversion2_text","limits","build_ready","dependency_closure"}
class SnapshotError(ValueError): pass
def _err(m): raise SnapshotError(m)
def _sha(b): return hashlib.sha256(b).hexdigest()
def _is_sha(x): return isinstance(x,str) and bool(SHA.match(x))
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
 if stat.S_ISLNK(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400: _err('reparse:'+str(p))
 return st
def _abs(x): return isinstance(x,str) and bool(x) and Path(x).is_absolute()
def _rel(x):
 if not isinstance(x,str) or not x or '\\' in x or x.startswith('/') or re.match(r'^[A-Za-z]:',x): _err('unsafe_rel:'+str(x))
 if Path(x).is_absolute() or any(p in ('','..') for p in x.split('/')): _err('unsafe_rel:'+x)
 return x
def _hash_file(p):
 _reparse(p)
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1048576),b''): h.update(c)
 return h.hexdigest()
def load_contract(path,expected_hash):
 if not _is_sha(expected_hash): _err('expected_hash')
 raw=Path(path).read_bytes()
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
 try: Path(c['attempt_marker']).relative_to(out); _err('marker_inside_output')
 except ValueError: pass
 pins=c['pins']
 if not isinstance(pins,dict) or len(pins)!=23: _err('pins_23')
 for k,v in pins.items(): _rel(k); 
 for v in pins.values():
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
 if not isinstance(t['dependencies'],dict) or not t['dependencies']: _err('deps')
 for k,v in t['dependencies'].items():
  if not _abs(k) or not _is_sha(v): _err('dep')
 _reparse(c['snapshot_root'])
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
 if done['stdout_sha']!=_sha(bytes(stdoutbytes)): _err('stdout_sha')
 if done['stderr_sha']!=_sha(bytes(stderrbytes)): _err('stderr_sha')
 return {'pid':pid,'birth':running['birth'],'rc':done['rc'],'reason':None,'seconds':done['seconds'],'peak_rss':done['peak_rss'],'started':running['started'],'finished':done['finished'],'input_sha':running['input_sha'],'executable':running['executable'],'stdout_sha':done['stdout_sha'],'stderr_sha':done['stderr_sha']}
def verify_snapshot(contract_path,expected_hash):
 c=load_contract(contract_path,expected_hash); root=Path(c['snapshot_root']); _reparse(root)
 if not root.is_dir(): _err('snapshot_root_dir')
 blobs={}; total=0
 for rel,pin in c['pins'].items():
  p=root/rel; st=_reparse(p)
  if not p.is_file(): _err('snapshot_file:'+rel)
  if st.st_size>c['limits']['file_bytes']: _err('file_limit:'+rel)
  b=p.read_bytes(); total+=len(b)
  if total>c['limits']['total_snapshot_bytes']: _err('total_limit')
  if _sha(b)!=pin: _err('pin_mismatch:'+rel)
  blobs[rel]=b
 report=_strict(blobs[ROLES['report']]); manifest=_strict(blobs[ROLES['manifest']]); old=_strict(blobs[ROLES['original_contract']]); appr=_strict(blobs[ROLES['original_approval']])
 for name,pin in [(c['tools']['runner']['path'],c['tools']['runner']['sha256']),(c['tools']['cfgconvert']['path'],c['tools']['cfgconvert']['sha256'])]+list(c['tools']['dependencies'].items()):
  if _hash_file(name)!=pin: _err('tool_hash:'+name)
 if old.get('cfgconvert')!=c['tools']['cfgconvert']['path'] or old.get('runner')!=c['tools']['runner']['path']: _err('old_tool_link')
 oldpins=old.get('pins',{})
 for name,pin in [(c['tools']['runner']['path'],c['tools']['runner']['sha256']),(c['tools']['cfgconvert']['path'],c['tools']['cfgconvert']['sha256'])]+list(c['tools']['dependencies'].items()):
  if name in oldpins and oldpins[name]!=pin: _err('old_tool_pin:'+name)
 assets=report.get('assets')
 if not isinstance(assets,list) or len(assets)!=8: _err('assets_8')
 if len({a.get('virtual_path') for a in assets})!=8 or len({a.get('local_path') for a in assets})!=8: _err('assets_unique')
 sel=old.get('selected'); 
 if not isinstance(sel,list) or len(sel)!=7: _err('selected_7')
 selmap={s['virtual_path']:s for s in sel}; extold=old.get('external')
 if not isinstance(extold,list) or len(extold)!=1: _err('external_old_1')
 byvirt={a['virtual_path']:a for a in assets}
 for vp,s in selmap.items():
  a=byvirt.get(vp)
  if not a or a.get('sha256')!=s.get('sha256') or a.get('provider')!='roads': _err('selected_match:'+vp)
 ext=report.get('external')
 if not isinstance(ext,list) or len(ext)!=1 or ext[0].get('virtual_path')!=extold[0] or ext[0].get('provider')!='surfaces' or ext[0].get('providers')!=['surfaces']: _err('external_literal')
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
 if not isinstance(arts,list) or len(arts)!=8 or {(x.get('local_path'),x.get('sha256'),x.get('size')) for x in arts}!={(a['local_path'],a['sha256'],a['size']) for a in assets}: _err('artifacts_8')
 if appr.get('contract_sha256')!=_sha(blobs[ROLES['original_contract']]): _err('approval_contract')
 if appr.get('tool_sha256')!=c['pins'][ROLES['failed_code']] or appr.get('tool_sha256')!=_sha(blobs[ROLES['failed_code']]): _err('approval_tool_failed')
 if _sha(blobs[ROLES['corrected_code']])!=c['pins'][ROLES['corrected_code']]: _err('corrected_pin')
 for doc in (report,manifest):
  if doc.get('status')!='INCONCLUSIVE_INITIAL_DISCOVERY' or doc.get('error')!='DiscoveryError:conversion_stream_missing' or doc.get('build_ready') is not False or doc.get('dependency_closure')!='NOT_EVALUATED': _err('historical_status')
 tables=report.get('tables')
 if not isinstance(tables,dict) or set(tables)!={'roads','surfaces','surfaces_bliss'}: _err('tables_3')
 pbos=old.get('pbos',{})
 for name,t in tables.items():
  if not (t.get('sha256_after')==t.get('sha256_observed')==t.get('sha256_observed_now')): _err('table_sha:'+name)
  if t.get('stat_before')!=t.get('stat_after') or not isinstance(t.get('stat_after'),list) or len(t['stat_after'])!=4: _err('table_stat:'+name)
  if t['stat_after'][2]!=t.get('size') or pbos.get(name,{}).get('bytes')!=t.get('size'): _err('table_size:'+name)
 if tables['roads'].get('sha256_after')!=pbos.get('roads',{}).get('sha256'): _err('roads_sha_oldpin')
 def receipt(pre):
  return _strict(blobs[pre+'/running.json']),_strict(blobs[pre+'/completion.json']),blobs[pre+'/stdout'],blobs[pre+'/stderr']
 prun,pdone,pso,pse=receipt(ROLES['parent_receipt'])
 pmeta=verify_receipt(prun,pdone,pso,pse,_sha(blobs[ROLES['original_approval']]),prun.get('executable'),expected_rc=1,max_running_seconds=120,max_rss_bytes=536870912)
 crun,cdone,cso,cse=receipt(ROLES['conversion1_receipt'])
 cmeta=verify_receipt(crun,cdone,cso,cse,c['pins'][ROLES['material1']],c['tools']['cfgconvert']['path'],expected_rc=0)
 text=blobs[ROLES['conversion1_text']]
 if not (0<len(text)<=c['limits']['file_bytes']): _err('decoded1_size')
 for role in ('material1','material2'):
  if blobs[ROLES[role]][:4]!=b'\x00raP': _err('signature:'+role)
 result={'status':'SAVED_SNAPSHOT_VERIFIED_ONLY','assets':8,'conversions':1,'conversion_1':cmeta,'parent':pmeta,'historical_status':'INCONCLUSIVE_INITIAL_DISCOVERY','build_ready':False,'dependency_closure':'NOT_EVALUATED','report_sha256':c['pins'][ROLES['report']]}
 return {'contract':c,'blobs':blobs,'result':result}
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--contract',required=True); ap.add_argument('--contract-sha256',required=True); ap.add_argument('--report',required=True); a=ap.parse_args(argv)
 try: out=verify_snapshot(a.contract,a.contract_sha256)['result']
 except Exception as e: print(json.dumps({'status':'REJECTED','error':repr(e)}),file=sys.stderr); return 1
 data=(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
 with open(a.report,'xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
 print(data.decode()); return 0
if __name__=='__main__': raise SystemExit(main())
