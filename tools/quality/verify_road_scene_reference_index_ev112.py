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
def _canon(x):
 return json.dumps(x,sort_keys=True)
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
 return all(a[k]==b[k] for k in ('dev','ino','size','mtime_ns','ctime_ns'))
def _canonical_name(s):
 return s.replace(chr(92),'/').lower().strip('/')
def _parse_virtual(raw_b,cap):
 if len(raw_b)==0 or len(raw_b)>cap: raise ValueError('object name length out of bounds')
 try: raw=raw_b.decode('ascii')
 except Exception: raise ValueError('object name is not printable ASCII')
 if any(ord(c)<32 or ord(c)>126 for c in raw): raise ValueError('object name is not printable ASCII')
 core=raw.replace(chr(92),'/').strip('/')
 if not core: raise ValueError('object name empty after exterior slash strip')
 if ':' in core: raise ValueError('object name has drive or colon')
 pieces=core.lower().split('/')
 if any(p in ('','.', '..') for p in pieces): raise ValueError('object name has traversal, dot, empty or double-slash component')
 if not core.lower().endswith('.p3d'): raise ValueError('object name does not require .p3d')
 return raw,core.lower()
def _sha_file_capped(path):
 st=os.stat(path)
 if st.st_size>1048576: raise ValueError('tool file exceeds 1MiB cap before read')
 h=hashlib.sha256()
 with open(path,'rb') as f:
  while True:
   chunk=f.read(1048576)
   if not chunk: break
   h.update(chunk)
 return h.hexdigest()
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
  f.seek(0); h2=hashlib.sha256(); second=0
  while True:
   chunk=f.read(1048576)
   if not chunk: break
   second+=len(chunk)
   if second>cap: raise ValueError('pinned second read exceeds cap')
   h2.update(chunk)
  if second!=total or h2.digest()!=h.digest(): raise ValueError('pinned bytes changed between reads')
  ha=_statd(os.fstat(f.fileno()))
 pa=_statd(os.stat(path))
 if not _same_handle_identity(hb,ha): raise ValueError('handle identity changed for '+path)
 if not _same_path_identity(pb,pa): raise ValueError('path identity changed for '+path)
 if any(pb[k]!=hb[k] or pa[k]!=ha[k] for k in ('dev','ino','size','mtime_ns')): raise ValueError('path and handle identity differ')
 if want_sha is not None and h.hexdigest()!=want_sha: raise ValueError('pinned sha mismatch for '+path)
 return b''.join(chunks),{'path':path,'sha256':h.hexdigest(),'bytes':total,'handle_before':hb,'handle_after':ha,'path_before':pb,'path_after':pa,'hash_before':h.hexdigest(),'hash_after':h2.hexdigest()}
def _exact(d,keys,what):
 if type(d) is not dict or set(d.keys())!=set(keys): raise ValueError(what+' keys mismatch')
def validate_contract(c):
 _exact(c,['schema','scope','plan_sha256','source','candidate','files','expected','limits','budgets','claims'],'contract')
 if c['schema']!=SCHEMA or c['scope']!=SCOPE: raise ValueError('contract schema or scope mismatch')
 if not _hex(c['plan_sha256']): raise ValueError('bad plan sha')
 if _canon(c['claims'])!=_canon(CLAIMS): raise ValueError('claims mismatch')
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
def _hash_all(f,size,prefix,buf):
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
def _read_exact(f,n,what):
 if n<0: raise ValueError('truncated '+what)
 out=b''
 while len(out)<n:
  chunk=f.read(n-len(out))
  if not chunk: raise ValueError('truncated '+what)
  out+=chunk
 return out
def _read_at(f,offset,n,what,size):
 if offset<0 or offset+n>size: raise ValueError('truncated '+what)
 f.seek(offset); out=_read_exact(f,n,what)
 if f.tell()!=offset+n: raise ValueError('short read at '+what)
 return out
def _objects_offset(f,size):
 head=_read_at(f,0,24,'WRP header',size)
 if head[0:4]!=b'0WZD': raise ValueError('bad WRP magic')
 tx=int.from_bytes(head[4:8],'little'); tz=int.from_bytes(head[8:12],'little'); nx=int.from_bytes(head[12:16],'little'); nz=int.from_bytes(head[16:20],'little'); cell=struct.unpack('<f',head[20:24])[0]
 if tx<=0 or tz<=0 or nx<=0 or nz<=0: raise ValueError('WRP dimensions must be positive')
 if not math.isfinite(cell) or cell<=0: raise ValueError('WRP cell size must be positive finite')
 pos=24+nx*nz*4+tx*tz*2
 if pos+4>size: raise ValueError('truncated material count')
 count=int.from_bytes(_read_at(f,pos,4,'material count',size),'little'); pos+=4
 if count>(size-pos)//4: raise ValueError('material count out of file bounds')
 for _ in range(count):
  while True:
   if pos+4>size: raise ValueError('truncated material string length')
   ln=int.from_bytes(_read_at(f,pos,4,'material string length',size),'little'); pos+=4
   if ln==0: break
   if pos+ln>size: raise ValueError('truncated material string bytes')
   pos+=ln
 return pos
def _open_wrp(path,exp_size,lim):
 pb=_statd(os.stat(path)); f=open(path,'rb'); hb=_statd(os.fstat(f.fileno()))
 if hb['size']>lim['wrp_bytes']: f.close(); raise ValueError('WRP exceeds cap before read')
 if exp_size is not None and hb['size']!=exp_size: f.close(); raise ValueError('WRP size mismatch before scan for '+path)
 return f,pb,hb
def _finish(f,path,pb,hb,sha_a,sha_b):
 ha=_statd(os.fstat(f.fileno())); pa=_statd(os.stat(path))
 if sha_a!=sha_b: raise ValueError('file hash changed during scan')
 if not _same_handle_identity(hb,ha): raise ValueError('handle identity changed during scan')
 if not _same_path_identity(pb,pa): raise ValueError('path identity changed during scan')
 if any(pb[k]!=hb[k] or pa[k]!=ha[k] for k in ('dev','ino','size','mtime_ns')): raise ValueError('path and handle identity differ')
 return ha,pa
def scan_source(path,contract):
 lim=contract['limits']; exp=contract['expected']; f,pb,hb=_open_wrp(path,contract['source']['bytes'],lim)
 try:
  size=hb['size']; sha_a,pre_a=_hash_all(f,size,exp['prefix_bytes'],lim['buffer_bytes']); offset=_objects_offset(f,size); counts={}; aliases={}; total=0; max_id=0; alias_bytes=0
  while True:
   start=offset; fixed=_read_at(f,offset,56,'object record or terminator',size); ident=int.from_bytes(fixed[48:52],'little'); nlen=int.from_bytes(fixed[52:56],'little')
   if nlen==0:
    if offset+56!=size: raise ValueError('terminator not at EOF')
    term=fixed; term_off=start; break
   if ident==0: raise ValueError('object id must be positive')
   if total>=lim['objects']: raise ValueError('objects cap exceeded')
   if nlen>lim['name_bytes']: raise ValueError('object name exceeds cap before read')
   raw_b=_read_at(f,offset+56,nlen,'object name bytes',size); raw,virt=_parse_virtual(raw_b,lim['name_bytes'])
   if virt not in counts and len(counts)>=lim['references']: raise ValueError('references cap exceeded')
   counts[virt]=counts.get(virt,0)+1
   if raw not in aliases.setdefault(virt,[]):
    if alias_bytes+len(raw_b)>lim['report_bytes']: raise ValueError('alias bytes cap exceeded')
    alias_bytes+=len(raw_b); aliases[virt].append(raw)
   total+=1; max_id=max(max_id,ident); offset+=56+nlen
  sha_b,pre_b=_hash_all(f,size,exp['prefix_bytes'],lim['buffer_bytes']); ha,pa=_finish(f,path,pb,hb,sha_a,sha_b)
  if pre_a!=pre_b: raise ValueError('prefix hash changed during scan')
  for v in aliases: aliases[v]=sorted(aliases[v])
  info={'path':path,'sha256':sha_a,'bytes':size,'object_count':total,'max_id':max_id,'terminator_offset':term_off,'terminator_hex':term.hex(),'prefix_bytes':exp['prefix_bytes'],'prefix_sha256':pre_a,'handle_before':hb,'handle_after':ha,'path_before':pb,'path_after':pa,'hash_before':sha_a,'hash_after':sha_b}
  return info,counts,aliases
 finally: f.close()
def scan_candidate(path,contract,source_total,source_max,source_counts):
 lim=contract['limits']; exp=contract['expected']; f,pb,hb=_open_wrp(path,contract['candidate']['bytes'],lim)
 try:
  size=hb['size']; sha_a,pre_a=_hash_all(f,size,exp['prefix_bytes'],lim['buffer_bytes'])
  if exp['prefix_bytes']>size: raise ValueError('candidate prefix beyond EOF')
  offset=exp['prefix_bytes']; added=[]; tally=dict(source_counts); added_bytes=0
  for want in exp['objects']:
   fixed=_read_at(f,offset,56,'candidate object record',size); ident=int.from_bytes(fixed[48:52],'little'); nlen=int.from_bytes(fixed[52:56],'little')
   if nlen==0: raise ValueError('candidate object omitted; terminator found early')
   if nlen>lim['name_bytes']: raise ValueError('candidate name exceeds cap before read')
   raw_b=_read_at(f,offset+56,nlen,'candidate name bytes',size); raw,virt=_parse_virtual(raw_b,lim['name_bytes'])
   if ident!=want['id'] or raw_b!=bytes.fromhex(want['raw_name_hex']) or virt!=_canonical_name(want['name']): raise ValueError('candidate object does not match contract object')
   if fixed[:48]!=struct.pack('<12f',*[float(x) for x in want['matrix12']]): raise ValueError('candidate matrix does not match contract object')
   added.append({'name':virt,'raw_name':raw,'id':ident}); tally[virt]=tally.get(virt,0)+1; added_bytes+=56+nlen
   if added_bytes>lim['wrp_bytes']: raise ValueError('candidate added bytes cap exceeded')
   offset+=56+nlen
  term_off=offset; term=_read_at(f,offset,56,'candidate terminator',size)
  if int.from_bytes(term[52:56],'little')!=0 or offset+56!=size: raise ValueError('candidate terminator not exact at EOF')
  sha_b,pre_b=_hash_all(f,size,exp['prefix_bytes'],lim['buffer_bytes']); ha,pa=_finish(f,path,pb,hb,sha_a,sha_b)
  if pre_a!=pre_b: raise ValueError('candidate prefix hash changed')
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
  if key=='road_models': parsed[key]=[parse_json(line.encode('utf-8')) for line in data.decode('utf-8').split('\n') if line.strip()]
  else: parsed[key]=parse_json(data)
 return parsed,pins
def _provider(package,sha,prefix,entry,model_sha):
 return {'package':package,'package_sha256':sha,'prefix':prefix,'entry':entry,'model_sha256':model_sha}
def build_report(contract,contract_sha,role):
 issues=[]; parsed,pins=_load_inputs(contract); exp=contract['expected']
 src_info,counts,aliases=scan_source(contract['source']['path'],contract)
 cand_info,added,candidate_counts=scan_candidate(contract['candidate']['path'],contract,src_info['object_count'],src_info['max_id'],counts)
 for bad,code in [(src_info['sha256']!=contract['source']['sha256'] or src_info['bytes']!=contract['source']['bytes'],'SOURCE_PIN'),(cand_info['sha256']!=contract['candidate']['sha256'] or cand_info['bytes']!=contract['candidate']['bytes'],'CANDIDATE_PIN'),(src_info['object_count']!=exp['object_count'],'SOURCE_COUNT'),(src_info['max_id']!=exp['max_id'],'SOURCE_MAX_ID'),(src_info['terminator_offset']!=exp['prefix_bytes'],'PREFIX_BYTES'),(src_info['prefix_sha256']!=exp['prefix_sha256'],'PREFIX_SHA'),(src_info['terminator_hex']!=exp['terminator_hex'],'TERMINATOR'),(cand_info['prefix_sha256']!=exp['prefix_sha256'],'CANDIDATE_PREFIX_SHA'),(cand_info['terminator_hex']!=exp['terminator_hex'],'CANDIDATE_TERMINATOR'),(cand_info['object_count']!=exp['candidate_count'],'CANDIDATE_COUNT')]:
  if bad: _issue(issues,code,code)
 b3c=parsed['b3_contract']; b3r=parsed['b3_report']
 if type(b3c) is not dict or type(b3r) is not dict: raise ValueError('B3 inputs must be objects')
 for field,want in [('source_sha256',contract['source']['sha256']),('source_bytes',contract['source']['bytes']),('object_count',exp['object_count']),('max_id',exp['max_id']),('prefix_bytes',exp['prefix_bytes']),('prefix_sha256',exp['prefix_sha256']),('terminator_hex',exp['terminator_hex']),('objects',exp['objects'])]:
  if field not in b3c or _canon(b3c.get(field))!=_canon(want): _issue(issues,'B3_CONTRACT_'+field.upper(),'B3 contract field missing or differs: '+field)
 added_ids=[o['id'] for o in exp['objects']]
 for field,want in [('source_sha256',contract['source']['sha256']),('source_bytes',contract['source']['bytes']),('candidate_sha256',contract['candidate']['sha256']),('candidate_bytes',contract['candidate']['bytes']),('object_count',exp['object_count']),('candidate_object_count',exp['candidate_count']),('max_id',exp['max_id']),('candidate_max_id',max(added_ids) if added_ids else exp['max_id']),('prefix_sha256',exp['prefix_sha256']),('added_count',3),('added_ids',added_ids)]:
  if field not in b3r or _canon(b3r.get(field))!=_canon(want): _issue(issues,'B3_REPORT_'+field.upper(),'B3 report field missing or differs: '+field)
 if b3r.get('ok') is not True: _issue(issues,'B3_REPORT_OK','B3 report ok missing or not true')
 models=parsed['b2a_models']; catalog=parsed['catalog']; b2ar=parsed['b2a_report']; b2ac=parsed['b2a_config']
 if type(models) is not list or type(catalog) is not list or type(b2ar) is not dict or type(b2ac) is not dict: raise ValueError('B2A inputs have wrong root types')
 if not _int(b2ar.get('scene_instances')) or b2ar.get('scene_instances')!=exp['object_count']: _issue(issues,'B2A_SCENE_INSTANCES','B2A scene_instances missing, bool, non-int or differs')
 if not _int(b2ar.get('scene_models')) or b2ar.get('scene_models')!=exp['catalog_model_count']: _issue(issues,'B2A_SCENE_MODELS','B2A scene_models missing, bool, non-int or differs')
 raw_packages=b2ar.get('packages')
 if type(raw_packages) is not list: _issue(issues,'B2A_REPORT_PACKAGES','B2A packages missing or not a list'); raw_packages=[]
 packages={}
 for p in raw_packages:
  if type(p) is not dict or type(p.get('path')) is not str or not p.get('path') or not _hex(p.get('sha256')) or type(p.get('prefix')) is not str: raise ValueError('bad B2A package pin')
  tup=(p['sha256'],p['prefix'])
  if p['path'] in packages and packages[p['path']]!=tup: _issue(issues,'B2A_PACKAGE_DUPLICATE','conflicting B2A package pin for '+p['path'])
  packages[p['path']]=tup
 pin_map=b2ac.get('package_pins')
 if type(pin_map) is not dict: raise ValueError('B2A config package_pins must be an object')
 for path,(sha,prefix) in packages.items():
  if path not in pin_map: _issue(issues,'B2A_PACKAGE_PIN_MISSING','config package pin missing for '+path)
  else:
   pv=pin_map[path]; psha=pv if type(pv) is str else (pv.get('sha256') if type(pv) is dict else None)
   if not _hex(psha) or psha!=sha: _issue(issues,'B2A_PACKAGE_SEAL','config package pin differs from report package for '+path)
 cat_dict={}; seen_idx=set()
 for row in catalog:
  if type(row) is not dict or 'index' not in row or 'name' not in row or 'instances' not in row or not _int(row.get('index')) or type(row.get('name')) is not str or not _int(row.get('instances')) or row.get('instances',-1)<0: raise ValueError('bad catalog row')
  if row['index'] in seen_idx: _issue(issues,'CATALOG_INDEX','duplicate catalog index')
  seen_idx.add(row['index']); v=_canonical_name(row['name'])
  if v in cat_dict: _issue(issues,'CATALOG_NAME','duplicate catalog virtual name '+v)
  else: cat_dict[v]=row['instances']
 if cat_dict!=counts: _issue(issues,'CATALOG_COUNTS','catalog counts differ from source observed counts')
 if len(catalog)!=exp['catalog_model_count']: _issue(issues,'CATALOG_MODEL_COUNT','catalog length differs from expected catalog_model_count')
 model_index={}; model_names=set()
 for m in models:
  if type(m) is not dict or any(k not in m for k in ('name','sha256','package','entry')): raise ValueError('bad B2A model row missing fields')
  if type(m.get('name')) is not str or not _hex(m.get('sha256')) or type(m.get('package')) is not str or type(m.get('entry')) is not str: raise ValueError('bad B2A model row types')
  v=_canonical_name(m['name']); model_names.add(v)
  if m['package'] not in packages: _issue(issues,'B2A_PACKAGE_MISSING','model package absent from B2A report for '+v); continue
  sha,prefix=packages[m['package']]; joined=_canonical_name(prefix+'/'+m['entry']) if prefix else _canonical_name(m['entry'])
  if joined!=v: _issue(issues,'B2A_PROVIDER_ENTRY','B2A provider prefix plus entry does not resolve to '+v)
  prov=_provider(m['package'],sha,prefix,m['entry'],m['sha256']); model_index.setdefault(v,{})[_canon(prov)]=prov
 if model_names!=set(cat_dict.keys()): _issue(issues,'B2A_CATALOG_SET','B2A model set differs from catalog set')
 b4c=parsed['b4a3_contract']; b4s=parsed['b4a3_summary']; road_models=parsed['road_models']; road_entries=parsed['road_entries']
 if type(b4c) is not dict or type(b4s) is not dict or type(road_models) is not list or type(road_entries) is not list: raise ValueError('B4A3 inputs have wrong root types')
 sources=b4c.get('sources')
 if type(sources) is not dict or 'models' not in sources or 'catalog' not in sources: raise ValueError('B4A3 sources missing models or catalog')
 for skey,fkey in [('models','road_models'),('catalog','road_entries')]:
  sv=sources.get(skey)
  if type(sv) is not dict or _canon(sv.get('sha256'))!=_canon(contract['files'][fkey]['sha256']) or _canon(sv.get('size'))!=_canon(contract['files'][fkey]['bytes']): _issue(issues,'B4A3_SOURCE_PIN','B4A3 source pin missing or differs for '+skey)
 asset_pins={}
 for k,v in sources.items():
  if k in ('models','catalog'): continue
  if not k.startswith('previous:assets/'): continue  # Other sealed B4A3 receipt/tool/text pins are not model assets.
  rel=k[len('previous:assets/'):]
  if not rel or type(v) is not dict or not _hex(v.get('sha256')) or not _int(v.get('size')) or v.get('size',-1)<0: raise ValueError('bad B4A3 asset pin for '+k)
  virt=_canonical_name(rel)
  if virt in asset_pins and asset_pins[virt]!=v['sha256']: _issue(issues,'B4A3_ASSET_DUPLICATE','conflicting B4A3 asset pin for '+virt)
  asset_pins[virt]=v['sha256']
 pbo=b4s.get('pbo')
 if type(pbo) is not dict or type(pbo.get('path')) is not str or not pbo.get('path') or not _hex(pbo.get('sha256')) or type(pbo.get('prefix')) is not str: raise ValueError('B4A3 summary pbo must have path, prefix and sha256')
 pbo_prefix=_canonical_name(pbo['prefix']); entry_by={}; model_by={}
 for e in road_entries:
  if type(e) is not dict or set(e.keys())!={'name','normalized_name','category','size','mime','sha256'}: raise ValueError('road entry must have exactly 6 fields')
  if type(e.get('name')) is not str or type(e.get('normalized_name')) is not str or type(e.get('category')) is not str or not _int(e.get('size')) or e.get('size',-1)<0 or not _int(e.get('mime')) or not _hex(e.get('sha256')): raise ValueError('bad road entry types')
  entry_key=_canonical_name(e['normalized_name'])
  if entry_key!=_canonical_name(e['name']): raise ValueError('road entry normalized name mismatch')
  entry_by.setdefault(entry_key,set()).add((e.get('name'),e.get('sha256'),e.get('mime'),e.get('size')))
 for m in road_models:
  if type(m) is not dict or any(k not in m for k in ('name','sha256','status')): raise ValueError('bad road model row missing fields')
  if type(m.get('name')) is not str or not _hex(m.get('sha256')) or type(m.get('status')) is not str: raise ValueError('bad road model row types')
  rel=_canonical_name(m['name'])
  if not rel or ':' in rel or any(p in ('','.', '..') for p in rel.split('/')) or not rel.endswith('.p3d'): raise ValueError('road model name must be relative')
  model_by.setdefault(rel,set()).add((m.get('sha256'),m.get('status')))
 def road_provider(v):
  if not pbo_prefix or not v.startswith(pbo_prefix+'/'): return None,'not-under-road-prefix'
  rel=v[len(pbo_prefix)+1:]; es=entry_by.get(rel,set()); ms=model_by.get(rel,set())
  if len(es)!=1 or len(ms)!=1: return None,'road entry or model not unambiguous'
  ename,esha,mime,esize=next(iter(es)); msha,mstatus=next(iter(ms))
  if type(mime) is not int or mime!=0: return None,'road entry mime is not integer zero'
  if mstatus!='READ_STRICT' or msha!=esha: return None,'road model READ_STRICT sha differs from entry'
  if v in asset_pins and asset_pins[v]!=esha: return None,'B4A3 asset pin sha differs from road entry'
  return _provider(pbo['path'],pbo['sha256'],pbo['prefix'],ename,esha),'ok'
 added_names=[a['name'] for a in added]; added_set=set(added_names)
 for a in added:
  if a['raw_name'] not in aliases.get(a['name'],[]): aliases.setdefault(a['name'],[]).append(a['raw_name']); aliases[a['name']]=sorted(aliases[a['name']])
 table=[]
 for v in sorted(set(list(counts.keys())+added_names)):
  provs=dict(model_index.get(v,{})); rp,rwhy=road_provider(v)
  if rp is not None: provs[_canon(rp)]=rp
  elif v in added_set or v in asset_pins: _issue(issues,'ROAD_PROVIDER',v+': '+rwhy)
  plist=[provs[k] for k in sorted(provs.keys())]; is_new=v in added_set and v not in counts; new_ok=is_new and v in asset_pins and rp is not None
  if is_new and not new_ok: _issue(issues,'NEW_REFERENCE_WITH_B4A3_PIN','new reference lacks real B4A3 asset pin or road provider for '+v)
  if len(plist)>1: state='UNRESOLVED'; provider=None; _issue(issues,'PROVIDER_CONFLICT','multiple distinct providers for '+v)
  elif len(plist)==1 and (not is_new or new_ok): provider=plist[0]; state='NEW_REFERENCE_WITH_B4A3_PIN' if is_new else 'PROVIDER_RESOLVED'
  else: state='UNRESOLVED'; provider=None; _issue(issues,'PROVIDER_UNRESOLVED','no provider for '+v)
  table.append({'name':v,'source_instances':counts.get(v,0),'candidate_instances':candidate_counts.get(v,0),'aliases':aliases.get(v,[]),'provider':provider,'state':state})
 issues_sorted=sorted(issues,key=lambda x: _canon(x)); status=OK if not issues_sorted else BAD
 return {'schema':RSCHEMA,'scope':SCOPE,'status':status,'contract_sha256':contract_sha,'tool':{'role':role,'path':os.path.abspath(__file__),'sha256':_sha_file_capped(__file__),'pid':os.getpid()},'source':src_info,'candidate':cand_info,'inputs':pins,'table':table,'issues':issues_sorted,'claims':dict(CLAIMS),'counts':{'distinct_references':len(table),'source_total':src_info['object_count'],'candidate_total':cand_info['object_count']}}
def _check_stats(info,what):
 if type(info) is not dict: raise ValueError(what+' missing')
 for sk in ('handle_before','handle_after','path_before','path_after'):
  st=info.get(sk)
  if type(st) is not dict or set(st.keys())!={'dev','ino','size','mtime_ns','ctime_ns'} or any(not _int(st[k]) for k in st): raise ValueError(what+' stat observation invalid: '+sk)
 if not _same_handle_identity(info['handle_before'],info['handle_after']): raise ValueError(what+' handle identity inconsistent')
 if not _same_path_identity(info['path_before'],info['path_after']): raise ValueError(what+' path identity inconsistent')
 if any(info['handle_before'][k]!=info['path_before'][k] for k in ('dev','ino','size','mtime_ns')): raise ValueError(what+' handle and path observations differ')
 if info['handle_before']['size']!=info.get('bytes'): raise ValueError(what+' size inconsistent')
def _validate_report(report,contract,contract_sha):
 _exact(report,['schema','scope','status','contract_sha256','tool','source','candidate','inputs','table','issues','claims','counts'],'report')
 if report['schema']!=RSCHEMA or report['scope']!=SCOPE or report['contract_sha256']!=contract_sha: raise ValueError('report header mismatch')
 if _canon(report['claims'])!=_canon(CLAIMS): raise ValueError('report claims mismatch')
 if report['status'] not in (OK,BAD): raise ValueError('report status mismatch')
 if type(report['issues']) is not list or any(type(i) is not dict or set(i.keys())!={'code','detail'} or type(i.get('code')) is not str or type(i.get('detail')) is not str for i in report['issues']): raise ValueError('report issues invalid')
 if (report['status']==OK)!=(len(report['issues'])==0): raise ValueError('report status and issues inconsistent')
 tool=report['tool']; _exact(tool,['role','path','sha256','pid'],'tool')
 expected_tool=os.path.join(os.path.dirname(os.path.abspath(__file__)),'road_scene_reference_index_ev112.py')
 if tool['role']!='producer': raise ValueError('producer tool role mismatch')
 if tool['path']!=expected_tool: raise ValueError('producer tool path mismatch: expected fixed sibling producer')
 if not _int(tool['pid']) or tool['pid']<=0 or tool['pid']==os.getpid(): raise ValueError('producer tool pid binding mismatch')
 if not _hex(tool['sha256']): raise ValueError('producer tool sha invalid')
 if _sha_file_capped(expected_tool)!=tool['sha256']: raise ValueError('producer tool sha mismatch')
 for key in ('source','candidate'):
  info=report[key]; _check_stats(info,'report '+key)
  if type(info.get('path')) is not str or not _hex(info.get('sha256')): raise ValueError('report wrp pin invalid')
  for fk in ('bytes','object_count','max_id','terminator_offset','prefix_bytes'):
   if not _int(info.get(fk)): raise ValueError('report wrp field not strict int: '+fk)
  if info.get('hash_before')!=info.get('sha256') or info.get('hash_after')!=info.get('sha256'): raise ValueError('report hash snapshots inconsistent')
  if type(info.get('terminator_hex')) is not str or len(info.get('terminator_hex',''))!=112 or not _hex(info.get('prefix_sha256')): raise ValueError('report wrp hex invalid')
 if type(report['inputs']) is not dict or set(report['inputs'].keys())!=set(FILES): raise ValueError('report inputs keys mismatch')
 for k,v in contract['files'].items():
  obs=report['inputs'][k]; _check_stats(obs,'report input '+k)
  if obs.get('path')!=v['path'] or obs.get('sha256')!=v['sha256'] or _canon(obs.get('bytes'))!=_canon(v['bytes']): raise ValueError('report input pins differ from contract')
 _exact(report['counts'],['distinct_references','source_total','candidate_total'],'report counts')
 if any(not _int(report['counts'][k]) for k in report['counts']): raise ValueError('report counts not strict int')
 if type(report['table']) is not list: raise ValueError('report table invalid')
 for row in report['table']:
  _exact(row,['name','source_instances','candidate_instances','aliases','provider','state'],'table row')
  if type(row['name']) is not str or not _int(row['source_instances']) or not _int(row['candidate_instances']) or type(row['aliases']) is not list or any(type(x) is not str for x in row['aliases']) or type(row['state']) is not str or row['state'] not in ('PROVIDER_RESOLVED','NEW_REFERENCE_WITH_B4A3_PIN','UNRESOLVED'): raise ValueError('report table row invalid')
  if row['provider'] is not None:
   _exact(row['provider'],['package','package_sha256','prefix','entry','model_sha256'],'provider')
   if any(type(row['provider'][k]) is not str for k in row['provider']) or not _hex(row['provider']['package_sha256']) or not _hex(row['provider']['model_sha256']): raise ValueError('report provider invalid')
def _semantic(report):
 r=copy.deepcopy(report); r.pop('tool',None)
 def strip_stats(container):
  if type(container) is dict:
   for sk in ('handle_before','handle_after','path_before','path_after'):
    if type(container.get(sk)) is dict: container[sk]={k:container[sk][k] for k in ('dev','ino','size','mtime_ns')}
 for k in ('source','candidate'):
  if type(r.get(k)) is dict: strip_stats(r[k])
 if type(r.get('inputs')) is dict:
  for obs in r['inputs'].values(): strip_stats(obs)
 codes=sorted([i['code'] for i in r.get('issues',[])])
 r['issues']=codes
 return r
def _empty(contract_sha,issues):
 return {'schema':RSCHEMA,'scope':SCOPE,'status':BAD,'contract_sha256':contract_sha,'tool':{'role':'consumer','path':os.path.abspath(__file__),'sha256':_sha_file_capped(__file__),'pid':os.getpid()},'source':None,'candidate':None,'inputs':{},'table':[],'issues':sorted(issues,key=lambda x: _canon(x)),'claims':dict(CLAIMS),'counts':{'distinct_references':0,'source_total':0,'candidate_total':0}}
def _write(path,report,cap):
 data=(json.dumps(report,sort_keys=True,indent=2)+'\n').encode('utf-8')
 if len(data)>cap: raise ValueError('report exceeds cap')
 with open(path,'xb') as f: f.write(data)
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--contract',required=True); ap.add_argument('--contract-sha',required=True); ap.add_argument('--output',required=True); ap.add_argument('--report',required=True); a=ap.parse_args(argv)
 issues=[]; contract_sha=a.contract_sha.lower(); cap=16777216; out=None; rc=2; recomputed=None
 try:
  data,obs=_load_bytes(a.contract,contract_sha,None,16777216); contract=validate_contract(parse_json(data)); cap=contract['limits']['report_bytes']
  recomputed=build_report(contract,contract_sha,'consumer')
  rdata,robs=_load_bytes(a.report,None,None,cap); producer_report=parse_json(rdata); _validate_report(producer_report,contract,contract_sha)
  if _canon(_semantic(producer_report))!=_canon(_semantic(recomputed)): raise ValueError('producer report differs from independent rescan')
  out=copy.deepcopy(recomputed)
  if producer_report['status']==OK and recomputed['status']==OK: out['status']=OK; rc=0
  elif producer_report['status']==BAD and recomputed['status']==BAD: out['status']=VERIFIED_MISMATCH; rc=2
  else: out['status']=BAD; rc=2
 except Exception as e:
  _issue(issues,'FATAL',str(e))
  if recomputed is None: out=_empty(contract_sha,issues)
  else: out=copy.deepcopy(recomputed); out['issues']=sorted(out.get('issues',[])+issues,key=lambda x: _canon(x)); out['status']=BAD
  rc=2
 try: _write(a.output,out,cap)
 except Exception: return 2
 return rc
if __name__=='__main__': sys.exit(main())
