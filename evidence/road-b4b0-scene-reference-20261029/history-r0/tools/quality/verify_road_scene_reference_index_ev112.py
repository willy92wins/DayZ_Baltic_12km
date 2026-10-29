import argparse,copy,hashlib,json,math,os,struct,sys
SCHEMA='road-b4b0.v1'
RSCHEMA='road-b4b0-report.v1'
SCOPE='SAVED_SCENE_REFERENCE_INDEX_ONLY'
OK='SAVED_SCENE_REFERENCE_INDEX_ONLY'
BAD='INCONCLUSIVE_REFERENCE_MISMATCH'
VERIFIED_MISMATCH='VERIFIED_MISMATCH_DIAGNOSTIC'
CLAIMS={'build_ready':False,'provider_precedence_current':'NOT_EVALUATED','material_texture_closure':'NOT_EVALUATED','pivots_width_accesses':'NOT_EVALUATED','map_repaired':False,'consumer_id_uniqueness':'INHERITED_SEALED_B3_PRODUCER_RECHECKED'}
FILES=['b3_contract','b3_report','b2a_models','b2a_report','b2a_config','catalog','b4a3_contract','b4a3_summary','road_models','road_entries']
def _int(x):
 return type(x) is int
def _num(x):
 return type(x) in (int,float) and math.isfinite(float(x))
def _hex(s,n=64):
 return type(s) is str and len(s)==n and all(c in '0123456789abcdef' for c in s)
def _nodup(pairs):
 d={}
 for k,v in pairs:
  if k in d: raise ValueError('duplicate JSON key '+k)
  d[k]=v
 return d
def _finite(o):
 if type(o) is float and not math.isfinite(o): raise ValueError('non-finite JSON number')
 if type(o) is dict:
  for v in o.values(): _finite(v)
 elif type(o) is list:
  for v in o: _finite(v)
def parse_json(data):
 if data.startswith(b'\xef\xbb\xbf'): raise ValueError('JSON BOM rejected')
 try:
  o=json.loads(data.decode('utf-8'),object_pairs_hook=_nodup,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('non-finite JSON constant')))
 except Exception as e: raise ValueError('invalid JSON: '+str(e))
 _finite(o); return o
def _statd(st):
 return {'dev':st.st_dev,'ino':st.st_ino,'size':st.st_size,'mtime_ns':st.st_mtime_ns,'ctime_ns':st.st_ctime_ns}
def _same_handle_identity(a,b):
 return all(a[k]==b[k] for k in ('dev','ino','size','mtime_ns','ctime_ns'))
def _same_path_identity(a,b):
 return all(a[k]==b[k] for k in ('dev','ino','size','mtime_ns'))
def norm(s):
 return s.replace(chr(92),'/').lower().strip('/')
def valid_name(raw_bytes,cap):
 if len(raw_bytes)==0 or len(raw_bytes)>cap: raise ValueError('object name length out of bounds')
 if any(b<32 or b>126 for b in raw_bytes): raise ValueError('object name is not printable ASCII')
 raw=raw_bytes.decode('ascii'); t=raw.replace(chr(92),'/')
 if t.startswith('/') or t.endswith('/'): raise ValueError('object name has leading or trailing slash')
 n=norm(raw)
 if not n.endswith('.p3d'): raise ValueError('object name does not require .p3d')
 if ':' in n: raise ValueError('object name has drive or colon')
 parts=n.split('/')
 if any(p in ('','.', '..') for p in parts): raise ValueError('object name has traversal, dot, empty or double-slash component')
 return raw,n
def _load_bytes(path,want_sha,want_size,cap):
 if type(path) is not str or not path: raise ValueError('bad pinned path')
 pb=_statd(os.stat(path))
 if pb['size']>cap: raise ValueError('pinned file exceeds cap before read')
 if want_size is not None and pb['size']!=want_size: raise ValueError('pinned size mismatch for '+path)
 h=hashlib.sha256(); total=0; chunks=[]
 with open(path,'rb') as f:
  hb=_statd(os.fstat(f.fileno()))
  while True:
   chunk=f.read(1048576)
   if not chunk: break
   total+=len(chunk)
   if total>cap: raise ValueError('pinned file exceeds cap')
   h.update(chunk); chunks.append(chunk)
  ha=_statd(os.fstat(f.fileno()))
 pa=_statd(os.stat(path))
 if not _same_handle_identity(hb,ha): raise ValueError('handle identity changed for '+path)
 if not _same_path_identity(pb,pa): raise ValueError('path identity changed for '+path)
 if want_sha is not None and h.hexdigest()!=want_sha: raise ValueError('pinned sha mismatch for '+path)
 return b''.join(chunks),{'path':path,'sha256':h.hexdigest(),'bytes':total}
def _exact(d,keys,what):
 if type(d) is not dict or set(d.keys())!=set(keys): raise ValueError(what+' keys mismatch')
def validate_contract(c):
 _exact(c,['schema','scope','plan_sha256','source','candidate','files','expected','limits','budgets','claims'],'contract')
 if c['schema']!=SCHEMA or c['scope']!=SCOPE: raise ValueError('contract schema or scope mismatch')
 if not _hex(c['plan_sha256']): raise ValueError('bad plan sha')
 if c['claims']!=CLAIMS: raise ValueError('claims mismatch')
 for k in ('source','candidate'):
  _exact(c[k],['path','sha256','bytes'],k)
  if type(c[k]['path']) is not str or not _hex(c[k]['sha256']) or not _int(c[k]['bytes']) or c[k]['bytes']<0: raise ValueError('bad '+k+' pin')
 _exact(c['files'],FILES,'files')
 for k,v in c['files'].items():
  _exact(v,['path','sha256','bytes'],'file '+k)
  if type(v['path']) is not str or not _hex(v['sha256']) or not _int(v['bytes']) or v['bytes']<0: raise ValueError('bad file pin '+k)
 _exact(c['expected'],['object_count','max_id','prefix_bytes','prefix_sha256','terminator_hex','objects','candidate_count','catalog_model_count'],'expected')
 e=c['expected']
 for k in ('object_count','max_id','prefix_bytes','candidate_count','catalog_model_count'):
  if not _int(e[k]) or e[k]<0: raise ValueError('bad expected '+k)
 if not _hex(e['prefix_sha256']): raise ValueError('bad prefix sha')
 if type(e['terminator_hex']) is not str or len(e['terminator_hex'])!=112 or any(ch not in '0123456789abcdef' for ch in e['terminator_hex']): raise ValueError('bad terminator hex')
 if type(e['objects']) is not list or len(e['objects'])!=3: raise ValueError('expected objects must be exactly 3')
 for o in e['objects']:
  _exact(o,['name','raw_name_hex','id','matrix12'],'expected object')
  if type(o['name']) is not str or not _int(o['id']) or o['id']<=0: raise ValueError('bad expected object')
  if type(o['raw_name_hex']) is not str or len(o['raw_name_hex'])%2 or any(ch not in '0123456789abcdef' for ch in o['raw_name_hex']): raise ValueError('bad raw name hex')
  if type(o['matrix12']) is not list or len(o['matrix12'])!=12 or any(not _num(x) for x in o['matrix12']): raise ValueError('bad matrix12')
 _exact(c['limits'],['wrp_bytes','name_bytes','references','objects','json_total_bytes','report_bytes','buffer_bytes'],'limits')
 for k,v in c['limits'].items():
  if not _int(v) or v<=0: raise ValueError('bad limit '+k)
 _exact(c['budgets'],['author_s','review_s','suite_s','producer_s','producer_rss','consumer_s','consumer_rss'],'budgets')
 for k,v in c['budgets'].items():
  if not _int(v) or v<=0: raise ValueError('bad budget '+k)
 return c
def _hash_handle(f,size,prefix,buf):
 f.seek(0); h=hashlib.sha256(); p=hashlib.sha256(); left=size; pleft=prefix
 while left>0:
  chunk=f.read(min(buf,left))
  if not chunk: raise ValueError('truncated file during hash')
  h.update(chunk)
  if pleft>0:
   take=chunk[:pleft]; p.update(take); pleft-=len(take)
  left-=len(chunk)
 if pleft!=0: raise ValueError('prefix beyond EOF')
 return h.hexdigest(),p.hexdigest()
class _Cur:
 def __init__(s,f,size): s.f=f; s.size=size; s.pos=f.tell()
 def read(s,n,what):
  if n<0 or s.pos+n>s.size: raise ValueError('truncated '+what)
  out=b''
  while len(out)<n:
   chunk=s.f.read(n-len(out))
   if not chunk: raise ValueError('truncated '+what)
   out+=chunk
  s.pos+=n; return out
 def skip(s,n,what):
  if n<0 or s.pos+n>s.size: raise ValueError('truncated '+what)
  s.f.seek(s.pos+n); s.pos+=n
 def u32(s,what): return struct.unpack('<I',s.read(4,what))[0]
def _objects_begin(cur):
 head=cur.read(24,'WRP header')
 magic,tx,tz,nx,nz,cell=struct.unpack('<4s4If',head)
 if magic!=b'0WZD': raise ValueError('bad WRP magic')
 if tx<=0 or tz<=0 or nx<=0 or nz<=0: raise ValueError('WRP dimensions must be positive')
 if not math.isfinite(cell) or cell<=0: raise ValueError('WRP cell size must be positive finite')
 cur.skip(nx*nz*4,'heights'); cur.skip(tx*tz*2,'material indices')
 count=cur.u32('material count')
 if count>(cur.size-cur.pos)//4: raise ValueError('material count out of file bounds')
 for _ in range(count):
  while True:
   ln=cur.u32('material string length')
   if ln==0: break
   cur.skip(ln,'material string bytes')
 return cur.pos
def _wrp_open(path,lim):
 pb=_statd(os.stat(path)); f=open(path,'rb'); hb=_statd(os.fstat(f.fileno()))
 if hb['size']>lim['wrp_bytes']: f.close(); raise ValueError('WRP exceeds cap before read')
 return f,pb,hb
def _close_check(f,path,pb,hb,sha_a,sha_b):
 ha=_statd(os.fstat(f.fileno())); pa=_statd(os.stat(path))
 if sha_a!=sha_b: raise ValueError('file hash changed during scan')
 if not _same_handle_identity(hb,ha): raise ValueError('handle identity changed during scan')
 if not _same_path_identity(pb,pa): raise ValueError('path identity changed during scan')
 return ha,pa
def scan_source(path,contract):
 lim=contract['limits']; exp=contract['expected']; f,pb,hb=_wrp_open(path,lim)
 try:
  size=hb['size']; sha_a,pre_a=_hash_handle(f,size,exp['prefix_bytes'],lim['buffer_bytes']); f.seek(0); cur=_Cur(f,size); begin=_objects_begin(cur); counts={}; aliases={}; total=0; max_id=0
  while True:
   start=cur.pos; fixed=cur.read(56,'object record or terminator'); ident,nlen=struct.unpack_from('<II',fixed,48)
   if nlen==0:
    if cur.pos!=size: raise ValueError('terminator not at EOF')
    term=fixed; term_off=start; break
   if ident==0: raise ValueError('object id must be positive')
   if total>=lim['objects']: raise ValueError('objects cap exceeded')
   if nlen>lim['name_bytes']: raise ValueError('object name exceeds cap before read')
   raw_b=cur.read(nlen,'object name bytes'); raw,virt=valid_name(raw_b,lim['name_bytes'])
   counts[virt]=counts.get(virt,0)+1; aliases.setdefault(virt,[])
   if raw not in aliases[virt]: aliases[virt].append(raw)
   if len(counts)>lim['references']: raise ValueError('references cap exceeded')
   total+=1; max_id=max(max_id,ident)
  sha_b,pre_b=_hash_handle(f,size,exp['prefix_bytes'],lim['buffer_bytes']); ha,pa=_close_check(f,path,pb,hb,sha_a,sha_b)
  if pre_a!=pre_b: raise ValueError('prefix hash changed during scan')
  for v in aliases: aliases[v]=sorted(aliases[v])
  info={'path':path,'sha256':sha_a,'bytes':size,'object_count':total,'max_id':max_id,'terminator_offset':term_off,'terminator_hex':term.hex(),'prefix_bytes':exp['prefix_bytes'],'prefix_sha256':pre_a,'handle_before':hb,'handle_after':ha,'path_before':pb,'path_after':pa,'hash_before':sha_a,'hash_after':sha_b}
  return info,counts,aliases
 finally: f.close()
def scan_candidate(path,contract,source_total,source_max,source_counts):
 lim=contract['limits']; exp=contract['expected']; f,pb,hb=_wrp_open(path,lim)
 try:
  size=hb['size']; sha_a,pre_a=_hash_handle(f,size,exp['prefix_bytes'],lim['buffer_bytes'])
  if exp['prefix_bytes']>size: raise ValueError('candidate prefix beyond EOF')
  f.seek(exp['prefix_bytes']); cur=_Cur(f,size); cur.pos=exp['prefix_bytes']; added=[]; tally=dict(source_counts)
  for want in exp['objects']:
   fixed=cur.read(56,'candidate object record'); ident,nlen=struct.unpack_from('<II',fixed,48)
   if nlen==0: raise ValueError('candidate object omitted; terminator found early')
   if nlen>lim['name_bytes']: raise ValueError('candidate name exceeds cap before read')
   raw_b=cur.read(nlen,'candidate name bytes'); raw,virt=valid_name(raw_b,lim['name_bytes'])
   if ident!=want['id'] or raw_b!=bytes.fromhex(want['raw_name_hex']) or virt!=norm(want['name']): raise ValueError('candidate object does not match contract object')
   if fixed[:48]!=struct.pack('<12f',*[float(x) for x in want['matrix12']]): raise ValueError('candidate matrix does not match contract object')
   added.append({'name':virt,'raw_name':raw,'id':ident}); tally[virt]=tally.get(virt,0)+1
  term_off=cur.pos; term=cur.read(56,'candidate terminator'); ident,nlen=struct.unpack_from('<II',term,48)
  if nlen!=0 or cur.pos!=size or f.read(1)!=b'': raise ValueError('candidate terminator not exact at EOF')
  sha_b,pre_b=_hash_handle(f,size,exp['prefix_bytes'],lim['buffer_bytes']); ha,pa=_close_check(f,path,pb,hb,sha_a,sha_b)
  max_id=source_max
  for a in added: max_id=max(max_id,a['id'])
  info={'path':path,'sha256':sha_a,'bytes':size,'object_count':source_total+len(added),'max_id':max_id,'terminator_offset':term_off,'terminator_hex':term.hex(),'prefix_bytes':exp['prefix_bytes'],'prefix_sha256':pre_a,'handle_before':hb,'handle_after':ha,'path_before':pb,'path_after':pa,'hash_before':sha_a,'hash_after':sha_b,'added':added}
  return info,added,tally
 finally: f.close()
def _issue(issues,code,detail): issues.append({'code':code,'detail':str(detail)})
def _load_inputs(contract):
 if sum(v['bytes'] for v in contract['files'].values())>contract['limits']['json_total_bytes']: raise ValueError('JSON inputs exceed total cap before read')
 parsed={}; pins={}; total=0
 for key in FILES:
  pin=contract['files'][key]; data,obs=_load_bytes(pin['path'],pin['sha256'],pin['bytes'],contract['limits']['json_total_bytes']-total); total+=obs['bytes']; pins[key]=obs
  if key=='road_models': parsed[key]=[parse_json(line.encode('utf-8')) for line in data.decode('utf-8').splitlines() if line.strip()]
  else: parsed[key]=parse_json(data)
 return parsed,pins
def _provider(package,sha,prefix,entry,model_sha):
 return {'package':package,'package_sha256':sha,'prefix':prefix,'entry':entry,'model_sha256':model_sha}
def build_report(contract,contract_sha,role):
 issues=[]; parsed,pins=_load_inputs(contract); exp=contract['expected']
 src_info,counts,aliases=scan_source(contract['source']['path'],contract)
 cand_info,added,candidate_counts=scan_candidate(contract['candidate']['path'],contract,src_info['object_count'],src_info['max_id'],counts)
 checks=[(src_info['sha256']!=contract['source']['sha256'],'SOURCE_PIN'),(src_info['bytes']!=contract['source']['bytes'],'SOURCE_SIZE'),(cand_info['sha256']!=contract['candidate']['sha256'],'CANDIDATE_PIN'),(cand_info['bytes']!=contract['candidate']['bytes'],'CANDIDATE_SIZE'),(src_info['object_count']!=exp['object_count'],'SOURCE_COUNT'),(src_info['max_id']!=exp['max_id'],'SOURCE_MAX_ID'),(src_info['terminator_offset']!=exp['prefix_bytes'],'PREFIX_BYTES'),(src_info['prefix_sha256']!=exp['prefix_sha256'],'PREFIX_SHA'),(src_info['terminator_hex']!=exp['terminator_hex'],'TERMINATOR'),(cand_info['prefix_sha256']!=exp['prefix_sha256'],'CANDIDATE_PREFIX_SHA'),(cand_info['terminator_hex']!=exp['terminator_hex'],'CANDIDATE_TERMINATOR'),(cand_info['object_count']!=exp['candidate_count'],'CANDIDATE_COUNT')]
 for bad,code in checks:
  if bad: _issue(issues,code,code)
 b3c=parsed['b3_contract']; b3r=parsed['b3_report']
 if type(b3c) is not dict or type(b3r) is not dict: raise ValueError('B3 inputs must be objects')
 for field,want in [('source_sha256',contract['source']['sha256']),('source_bytes',contract['source']['bytes']),('object_count',exp['object_count']),('max_id',exp['max_id']),('prefix_bytes',exp['prefix_bytes']),('prefix_sha256',exp['prefix_sha256']),('terminator_hex',exp['terminator_hex']),('objects',exp['objects'])]:
  if b3c.get(field)!=want: _issue(issues,'B3_CONTRACT_'+field.upper(),field)
 added_ids=[o['id'] for o in exp['objects']]
 for field,want in [('source_sha256',contract['source']['sha256']),('source_bytes',contract['source']['bytes']),('candidate_sha256',contract['candidate']['sha256']),('candidate_bytes',contract['candidate']['bytes']),('object_count',exp['object_count']),('candidate_object_count',exp['candidate_count']),('max_id',exp['max_id']),('candidate_max_id',max(added_ids)),('prefix_sha256',exp['prefix_sha256']),('added_count',3),('added_ids',added_ids)]:
  if field in b3r and b3r.get(field)!=want: _issue(issues,'B3_REPORT_'+field.upper(),field)
 if 'ok' in b3r and b3r.get('ok') is not True: _issue(issues,'B3_REPORT_OK','ok')
 models=parsed['b2a_models']; catalog=parsed['catalog']; b2ar=parsed['b2a_report']; b2ac=parsed['b2a_config']
 if type(models) is not list or type(catalog) is not list or type(b2ar) is not dict or type(b2ac) is not dict: raise ValueError('B2A root types')
 packages={}
 for p in b2ar.get('packages',[]):
  if type(p) is dict and type(p.get('path')) is str: packages[p['path']]=(p.get('sha256'),p.get('prefix'))
 pin_map=b2ac.get('package_pins')
 if type(pin_map) is not dict: raise ValueError('package_pins')
 for path,(sha,prefix) in packages.items():
  if path in pin_map:
   pv=pin_map[path]; psha=pv if type(pv) is str else (pv.get('sha256') if type(pv) is dict else None)
   if psha!=sha: _issue(issues,'B2A_PACKAGE_SEAL',path)
 cat_dict={}; seen_idx=set()
 for row in catalog:
  if type(row) is not dict or not _int(row.get('index')) or type(row.get('name')) is not str or not _int(row.get('instances')) or row.get('instances',-1)<0: raise ValueError('bad catalog row')
  if row['index'] in seen_idx: _issue(issues,'CATALOG_INDEX','duplicate')
  seen_idx.add(row['index']); cat_dict[norm(row['name'])]=row['instances']
 if cat_dict!=counts: _issue(issues,'CATALOG_COUNTS','catalog differs from source')
 if len(catalog)!=exp['catalog_model_count']: _issue(issues,'CATALOG_MODEL_COUNT','length')
 if set(norm(m['name']) for m in models if type(m) is dict and type(m.get('name')) is str)!=set(cat_dict.keys()): _issue(issues,'B2A_CATALOG_SET','set differs')
 b4c=parsed['b4a3_contract']; b4s=parsed['b4a3_summary']; road_models=parsed['road_models']; road_entries=parsed['road_entries']
 if type(b4c) is not dict or type(b4s) is not dict or type(road_models) is not list or type(road_entries) is not list: raise ValueError('B4A3 root types')
 sources=b4c.get('sources')
 if type(sources) is not dict or 'models' not in sources or 'catalog' not in sources: raise ValueError('B4A3 sources')
 for skey,fkey in [('models','road_models'),('catalog','road_entries')]:
  sv=sources.get(skey)
  if type(sv) is dict and (sv.get('sha256')!=contract['files'][fkey]['sha256'] or sv.get('size')!=contract['files'][fkey]['bytes']): _issue(issues,'B4A3_SOURCE_PIN',skey)
 asset_pins={}
 for k,v in sources.items():
  if '/assets/' in k and type(v) is dict: asset_pins[norm(k.split('/assets/',1)[1])]=v.get('sha256')
 pbo=b4s.get('pbo')
 if type(pbo) is not dict: raise ValueError('pbo')
 pbo_prefix=norm(pbo.get('prefix','')); entry_by={}; model_by={}
 for e in road_entries:
  if type(e) is dict and type(e.get('name')) is str: entry_by.setdefault(norm(e.get('normalized_name') or e['name']),set()).add((e.get('name'),e.get('sha256'),e.get('mime'),e.get('size')))
 for m in road_models:
  if type(m) is dict and type(m.get('name')) is str: model_by.setdefault(norm(m['name']),set()).add((m.get('sha256'),m.get('status')))
 def road_provider(v):
  if not v.startswith(pbo_prefix+'/'): return None,'not-under-prefix'
  rel=v[len(pbo_prefix)+1:]; es=entry_by.get(rel,set()); ms=model_by.get(rel,set())
  if len(es)!=1 or len(ms)!=1: return None,'not unambiguous'
  ename,esha,mime,esize=next(iter(es)); msha,mstatus=next(iter(ms))
  if type(mime) is not int or mime!=0 or mstatus!='READ_STRICT' or msha!=esha: return None,'road evidence mismatch'
  if v in asset_pins and asset_pins[v]!=esha: return None,'asset pin mismatch'
  return _provider(pbo['path'],pbo['sha256'],pbo['prefix'],ename,esha),'ok'
 added_names=[a['name'] for a in added]
 for a in added:
  if a['raw_name'] not in aliases.get(a['name'],[]): aliases.setdefault(a['name'],[]).append(a['raw_name']); aliases[a['name']]=sorted(aliases[a['name']])
 table=[]
 for v in sorted(set(list(counts.keys())+added_names)):
  provs={}
  for m in models:
   if type(m) is dict and type(m.get('name')) is str and norm(m['name'])==v and m.get('package') in packages:
    sha,prefix=packages[m['package']]; p=_provider(m['package'],sha,prefix,m.get('entry'),m.get('sha256')); provs[json.dumps(p,sort_keys=True)]=p
  rp,rwhy=road_provider(v)
  if rp is not None: provs[json.dumps(rp,sort_keys=True)]=rp
  elif v in added_names or v in asset_pins: _issue(issues,'ROAD_PROVIDER',v+': '+rwhy)
  plist=[provs[k] for k in sorted(provs.keys())]
  if len(plist)>1: provider=None; state='UNRESOLVED'; _issue(issues,'PROVIDER_CONFLICT',v)
  elif len(plist)==1: provider=plist[0]; state='NEW_REFERENCE_WITH_B4A3_PIN' if (v in added_names and v in asset_pins and rp is not None) else 'PROVIDER_RESOLVED'
  else: provider=None; state='UNRESOLVED'; _issue(issues,'PROVIDER_UNRESOLVED',v)
  if v in added_names and state!='NEW_REFERENCE_WITH_B4A3_PIN' and len(plist)<=1: _issue(issues,'NEW_REFERENCE_STATE',v)
  table.append({'name':v,'source_instances':counts.get(v,0),'candidate_instances':candidate_counts.get(v,0),'aliases':aliases.get(v,[]),'provider':provider,'state':state})
 issues_sorted=sorted(issues,key=lambda x: json.dumps(x,sort_keys=True)); status=OK if not issues_sorted else BAD
 with open(__file__,'rb') as tf: tool_sha=hashlib.sha256(tf.read()).hexdigest()
 return {'schema':RSCHEMA,'scope':SCOPE,'status':status,'contract_sha256':contract_sha,'tool':{'role':role,'path':os.path.abspath(__file__),'sha256':tool_sha,'pid':os.getpid()},'source':src_info,'candidate':cand_info,'inputs':pins,'table':table,'issues':issues_sorted,'claims':dict(CLAIMS),'counts':{'distinct_references':len(table),'source_total':src_info['object_count'],'candidate_total':cand_info['object_count']}}
def _semantic(report):
 r=copy.deepcopy(report); r.pop('tool',None)
 for k in ('source','candidate'):
  if type(r.get(k)) is dict:
   for f in ('handle_before','handle_after','path_before','path_after','hash_before','hash_after'): r[k].pop(f,None)
 return r
def _validate_report(report,contract,contract_sha):
 _exact(report,['schema','scope','status','contract_sha256','tool','source','candidate','inputs','table','issues','claims','counts'],'report')
 if report['schema']!=RSCHEMA or report['scope']!=SCOPE or report['contract_sha256']!=contract_sha or report['claims']!=CLAIMS: raise ValueError('report header mismatch')
 if report['status'] not in (OK,BAD): raise ValueError('report status mismatch')
 tool=report['tool']; _exact(tool,['role','path','sha256','pid'],'tool')
 if tool['role']!='producer' or not _int(tool['pid']) or tool['pid']<=0 or not _hex(tool['sha256']): raise ValueError('producer tool binding mismatch')
 with open(tool['path'],'rb') as tf:
  if hashlib.sha256(tf.read()).hexdigest()!=tool['sha256']: raise ValueError('producer tool sha mismatch')
 for key in ('source','candidate'):
  info=report[key]
  if type(info) is not dict: raise ValueError('report wrp info missing')
  if info.get('hash_before')!=info.get('sha256') or info.get('hash_after')!=info.get('sha256'): raise ValueError('report hash snapshots inconsistent')
  for a,b in [('handle_before','handle_after')]:
   if not _same_handle_identity(info[a],info[b]): raise ValueError('report handle identity inconsistent')
  if not _same_path_identity(info['path_before'],info['path_after']): raise ValueError('report path identity inconsistent')
  if info['handle_before'].get('size')!=info.get('bytes'): raise ValueError('report size inconsistent')
 if report['inputs']!={k:{'path':v['path'],'sha256':v['sha256'],'bytes':v['bytes']} for k,v in contract['files'].items()}: raise ValueError('report input pins differ from contract')
def _empty(contract_sha,issues):
 with open(__file__,'rb') as tf: sha=hashlib.sha256(tf.read()).hexdigest()
 return {'schema':RSCHEMA,'scope':SCOPE,'status':BAD,'contract_sha256':contract_sha,'tool':{'role':'consumer','path':os.path.abspath(__file__),'sha256':sha,'pid':os.getpid()},'source':None,'candidate':None,'inputs':{},'table':[],'issues':sorted(issues,key=lambda x: json.dumps(x,sort_keys=True)),'claims':dict(CLAIMS),'counts':{'distinct_references':0,'source_total':0,'candidate_total':0}}
def _write(path,report,cap):
 data=(json.dumps(report,sort_keys=True,indent=2)+'\n').encode('utf-8')
 if len(data)>cap: raise ValueError('report exceeds cap')
 with open(path,'xb') as f: f.write(data)
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--contract',required=True); ap.add_argument('--contract-sha',required=True); ap.add_argument('--output',required=True); ap.add_argument('--report',required=True); a=ap.parse_args(argv)
 issues=[]; contract_sha=a.contract_sha.lower(); cap=16777216; out=None; rc=2
 try:
  data,obs=_load_bytes(a.contract,contract_sha,None,16777216); contract=validate_contract(parse_json(data)); cap=contract['limits']['report_bytes']
  recomputed=build_report(contract,contract_sha,'consumer')
  rdata,robs=_load_bytes(a.report,None,None,cap); producer_report=parse_json(rdata); _validate_report(producer_report,contract,contract_sha)
  if _semantic(producer_report)!=_semantic(recomputed): raise ValueError('producer report differs from independent rescan')
  out=copy.deepcopy(recomputed)
  if producer_report['status']==OK and recomputed['status']==OK: out['status']=OK; rc=0
  elif producer_report['status']==BAD and recomputed['status']==BAD: out['status']=VERIFIED_MISMATCH; rc=2
  else: out['status']=BAD; rc=2
 except Exception as e:
  _issue(issues,'FATAL',str(e))
  try: out=recomputed
  except Exception: out=None
  if out is None: out=_empty(contract_sha,issues)
  else:
   out=copy.deepcopy(out); out['issues']=sorted(out.get('issues',[])+issues,key=lambda x: json.dumps(x,sort_keys=True)); out['status']=BAD
  rc=2
 try: _write(a.output,out,cap)
 except Exception: return 2
 return rc
if __name__=='__main__': sys.exit(main())
