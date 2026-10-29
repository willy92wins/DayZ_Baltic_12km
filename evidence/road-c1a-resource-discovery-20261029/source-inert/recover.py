from pathlib import Path
import json,hashlib,os,stat,time
D=Path(__file__).parent;PIN='22dae2436356cde3259fc50cb68136f956f8179f04177ccbb0fac52a1efebbbc';T=time.monotonic()
def sh(b):return hashlib.sha256(b).hexdigest()
def need(ok,code):
 if not ok:raise ValueError(code)
def js(p):return json.loads(p.read_bytes())
def stamp(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def guard(p):
 for q in [*reversed(p.parents),p]:
  try:s=q.lstat()
  except FileNotFoundError:return {'state':'MISSING','at':str(q)}
  if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&1024:return {'state':'BLOCKED_REPARSE','at':str(q),'identity':stamp(s)}
 return {'state':'LOCATED_NOT_READ','identity':stamp(s)}
def tokens(text):
 out=[]
 for line,s in enumerate(text.splitlines(),1):
  opened=None
  for i,c in enumerate(s):
   if c!='"':continue
   need(i==0 or s[i-1]!='\\','UNKNOWN_QUOTE_GRAMMAR')
   if opened is None:opened=i+1
   else:out.append([line,s[opened:i]]);opened=None
  need(opened is None,'UNKNOWN_QUOTE_GRAMMAR')
 return out
def dump(name,v):
 b=json.dumps(v,ensure_ascii=False,separators=(',',':')).encode()+b'\n'
 need(len(b)<=C['output_cap'],'INCONCLUSIVE_OUTPUT_CAP')
 with (OUT/name).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def tick():need(time.monotonic()-T<C['seconds'],'INCONCLUSIVE_TIME')
cb=(D/'contract.json').read_bytes();need(sh(cb)==PIN,'CONTRACT');C=json.loads(cb);ob=(D/'oracle.json').read_bytes();need(sh(ob)==C['oracle_sha256'],'ORACLE');O=json.loads(ob)
need(tokens(O['input'])==O['expected'],'ORACLE')
for x in O['negative']:
 try:tokens(x)
 except ValueError as e:need(str(e)==O['negative_code'],'ORACLE_CODE')
 else:raise ValueError('ORACLE_FALSE_PASS')
mutant=[x for x in tokens(O['input']) if x[1].endswith(('.paa','.rvmat','.p3d','.bisurf','.wrp','.nm'))];need(mutant!=O['expected'],'MUTANT_SURVIVED')
OUT=Path(C['output']);OUT.mkdir(exist_ok=False);dump('oracle-check.json',{'positive':True,'negative_cases':2,'suffix_mutant_rejected':True,'geometric_tests':0})
try:
 rp=Path(C['report']['path']);need(rp.stat().st_size==C['report']['bytes']<=4*1024**2,'REPORT_CAP');b=rp.read_bytes();need(sh(b)==C['report']['sha256'],'REPORT_PIN');r=json.loads(b)
 rc=Path(C['reconciliation']['path']);need(rc.stat().st_size<=1024**2 and sh(rc.read_bytes())==C['reconciliation']['sha256'],'RECONCILIATION_PIN')
 mats=r['materials'];need(len(mats)==C['material_count'] and sum(m['bytes'] for m in mats)==C['material_bytes'],'INPUT_COUNTS')
 old={a['path']:a for a in r['read_receipts']};strings=[];idx={};files=[];read_bytes=0
 for i,m in enumerate(mats):
  tick();p=Path(m['path']);rel=m['raw'].replace('\\','/');need(p==Path(C['source_root'])/rel,'PATH_BINDING');g=guard(p);need(g['state']=='LOCATED_NOT_READ','SOURCE_REPARSE_OR_MISSING')
  need(g['identity']==old[str(p)]['identity'],'SOURCE_CHANGED');need(g['identity'][2]==m['bytes']<=C['file_cap'] and read_bytes+m['bytes']<=C['read_cap'],'READ_CAP')
  with p.open('rb') as f:
   need(stamp(os.fstat(f.fileno()))==g['identity'],'SOURCE_CHANGED');b=f.read(C['file_cap']+1);need(stamp(os.fstat(f.fileno()))==g['identity']==stamp(p.stat()),'SOURCE_CHANGED')
  need(len(b)==m['bytes'] and sh(b)==m['sha256'],'SOURCE_CHANGED');read_bytes+=len(b);q=tokens(b.decode('utf-8-sig'));need(len(q)<=C['strings_per_file'],'INCONCLUSIVE_STRINGS_CAP')
  if i==0:need(all(v in q for v in O['literal_counterexample']),'LITERAL_COUNTEREXAMPLE')
  uses=[]
  for ln,s in q:
   if s not in idx:need(len(strings)<C['unique_strings'],'INCONCLUSIVE_UNIQUE_CAP');idx[s]=len(strings);strings.append(s)
   uses.append([ln,idx[s]])
  files.append({'material_index':i,'sha256':m['sha256'],'bytes':m['bytes'],'uses':uses})
 need(read_bytes==C['material_bytes'],'READ_TOTAL');dump('phase-texts.json',{'files':len(files),'bytes':read_bytes,'strings':len(strings),'uses':sum(len(f['uses']) for f in files)})
 located=[]
 for i,s in enumerate(strings):
  tick();a={'string_index':i}
  if ('/' not in s and '\\' not in s) or s.startswith('#('):a['state']='LITERAL_NOT_RESOLVED'
  else:
   v=s.replace('\\','/');need(s.isascii() and all(32<=ord(ch)<127 for ch in s) and ':' not in v and not v.startswith('/') and all(x not in ('','.','..') for x in v.split('/')),'REJECTED_PATH')
   top=v.split('/')[0].lower();base=Path(C['source_root']) if top=='dayz_baltic_12km_dev' else Path('P:/') if top=='dz' else None
   a['normalized']=v
   if base is None:a['state']='UNRESOLVED_NAMESPACE'
   else:
    p=base/v;a.update(guard(p));a['path']=str(p)
  located.append(a)
 report={'status':'RECOVERED_QUOTED_MATERIAL_REFERENCES_ONLY','contract_sha256':PIN,'input_report_sha256':C['report']['sha256'],'strings':strings,'files':files,'locations':located,'read_bytes':read_bytes,'seconds':time.monotonic()-T,'build_ready':False,'dependency_closure':'NOT_EVALUATED','compiled_terrain_decoder':'NOT_VERIFIED','quote_count_check':'SELF_CONSISTENCY_ONLY','source_payloads_other_than_material_texts_read':False,'map_changed':False}
 dump('report.json',report);print(json.dumps({'status':report['status'],'files':len(files),'strings':len(strings),'path_candidates':sum(x['state']!='LITERAL_NOT_RESOLVED' for x in located),'read_bytes':read_bytes,'seconds':report['seconds']}))
except Exception as e:
 dump('failure.json',{'status':'INCONCLUSIVE_RECOVERY','type':type(e).__name__,'error':str(e),'build_ready':False});raise
