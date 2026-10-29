from pathlib import Path
import os,stat,hashlib,json,struct,time
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1a-research-20261029';O=D/'capture'
ROOT=R/'stage-kit7-fc-20261026/root';T=time.monotonic();READ=0;OUT=0;READS=[]
class Stop(Exception):pass
def need(b,code):
 if not b:raise Stop(code)
def tick():need(time.monotonic()-T<60,'INCONCLUSIVE_RESOURCE_TIME')
def sha(b):return hashlib.sha256(b).hexdigest()
def write(name,value):
 global OUT
 data=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()+b'\n';need(OUT+len(data)<=4*1024**2,'INCONCLUSIVE_RESOURCE_OUTPUT')
 with (O/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 OUT+=len(data)
def stamp(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def guarded(p):
 p=Path(p)
 for a in [*reversed(p.parents),p]:
  try:s=a.lstat()
  except FileNotFoundError:return {'state':'MISSING','at':str(a)}
  if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&1024:
   return {'state':'BLOCKED_REPARSE','at':str(a),'identity':stamp(s),'reparse_tag':getattr(s,'st_reparse_tag',None)}
 return {'state':'LOCATED_NOT_READ','identity':stamp(s)}
def read(p,cap):
 global READ
 tick();p=Path(p);g=guarded(p);need(g['state']=='LOCATED_NOT_READ',g['state'])
 need(g['identity'][2]<=cap and READ+g['identity'][2]<=64*1024**2,'INCONCLUSIVE_RESOURCE_READ')
 with p.open('rb') as f:
  need(stamp(os.fstat(f.fileno()))==g['identity'],'SOURCE_CHANGED');b=f.read(cap+1)
  need(stamp(os.fstat(f.fileno()))==g['identity']==stamp(p.stat()),'SOURCE_CHANGED')
 need(len(b)==g['identity'][2] and len(b)<=cap,'SOURCE_CHANGED');READ+=len(b)
 READS.append({'path':str(p),'bytes':len(b),'sha256':sha(b),'identity':g['identity']});return b
def quoted(b):
 text=b.decode('utf-8-sig');out=[];i=0
 while True:
  a=text.find('"',i)
  if a<0:break
  z=text.find('"',a+1);need(z>=0,'UNKNOWN_QUOTE_GRAMMAR');out.append(text[a+1:z]);i=z+1
 return out
def virtual(raw):
 need(isinstance(raw,str) and raw.isascii(),'REJECTED_PATH')
 s=raw[:-1] if raw.endswith('\0') else raw
 need(all(32<=ord(c)<127 for c in s),'REJECTED_PATH');s=s.replace('\\','/')
 need(':' not in s and not s.startswith('/') and all(x not in ('','.','..') for x in s.split('/')),'REJECTED_PATH')
 return s
def candidate(raw):
 v=virtual(raw);top=v.split('/')[0].lower()
 if top=='dayz_baltic_12km_dev':return ROOT/v,'SAVED_STAGE',v
 if top=='dz':return Path('P:/')/v,'BUILD_PATH_UNPINNED',v
 return None,'UNRESOLVED_NAMESPACE',v
def run():
 global OUT
 O.mkdir(exist_ok=False);write('phase-00.json',{'stage':'START','scope':'READ_ONLY_PLANNING','limits':{'seconds':60,'read_bytes':64*1024**2,'output_bytes':4*1024**2}})
 p=R/'road-c0-isolated-sources-20261029/control.wrp';b=read(p,32*1024**2)
 need(sha(b)=='f00c3f57ab3660e93c44a1cb612c6338f87db1bfd4c047acf6f7389c61c7e6df','SOURCE_HASH')
 magic,tx,tz,nx,nz,cell=struct.unpack_from('<4s4If',b);need((magic,tx,tz,nx,nz,cell)==(b'0WZD',256,256,2048,2048,48.),'SOURCE_HEADER')
 at=24+nx*nz*4+tx*tz*2;need(at==16908312,'SOURCE_OFFSET');count=struct.unpack_from('<I',b,at)[0];at+=4;need(count==4776,'REJECTED_SOURCE_STRUCTURE')
 table=b[16908316:17307629];need(len(table)==399313,'REJECTED_SOURCE_STRUCTURE')
 with (O/'material-table.bin').open('xb') as f:f.write(table);f.flush();os.fsync(f.fileno())
 OUT+=len(table);groups=[];unique={}
 for i in range(count):
  tick();row=[]
  while True:
   need(at+4<=17307629,'REJECTED_SOURCE_STRUCTURE');n=struct.unpack_from('<I',b,at)[0];at+=4
   if n==0:break
   need(n<=4096 and at+n<=17307629,'REJECTED_SOURCE_STRUCTURE');s=b[at:at+n].decode('ascii');at+=n;virtual(s)
   if s not in unique:need(len(unique)<16384,'INCONCLUSIVE_RESOURCE_NAMES');unique[s]=len(unique)
   row.append(unique[s])
  groups.append(row)
 need(at==17307629,'REJECTED_SOURCE_STRUCTURE');del b
 write('phase-01.json',{'stage':'MATERIAL_TABLE','rows':count,'unique':len(unique),'sha256':sha(table),'end':at})
 refs={};refrows=[]
 def add(raw,origin):
  if not raw.lower().endswith(('.paa','.rvmat','.p3d','.bisurf','.wrp','.nm')):return None
  virtual(raw)
  if raw not in refs:
   need(len(refs)<32768,'INCONCLUSIVE_RESOURCE_REFERENCES');refs[raw]=len(refrows);refrows.append({'raw':raw,'origins':set()})
  refrows[refs[raw]]['origins'].add(origin);return refs[raw]
 config=ROOT/'dayz_baltic_12km_dev/tb/narva_trial/config.cpp';cfg=read(config,1024**2)
 config_refs=[x for s in quoted(cfg) if (x:=add(s,'world_config')) is not None]
 materials=[]
 for raw in unique:
  tick();p,ns,v=candidate(raw);m={'raw':raw,'namespace':ns}
  if p is None:m['state']='UNRESOLVED_NAMESPACE'
  else:
   g=guarded(p);m.update(state=g['state'],path=str(p))
   if g['state']=='LOCATED_NOT_READ' and ns=='SAVED_STAGE' and v.lower().endswith('.rvmat'):
    content=read(p,1024**2);m.update(state='OBSERVED_TEXT',sha256=sha(content),bytes=len(content),references=[x for s in quoted(content) if (x:=add(s,'terrain_material')) is not None])
   elif g['state']=='BLOCKED_REPARSE':m['blocked_at']=g
  materials.append(m)
 write('phase-02.json',{'stage':'TEXTS','material_texts':sum(m['state']=='OBSERVED_TEXT' for m in materials),'read_bytes':READ,'distinct_refs':len(refrows)})
 for r in refrows:
  tick();p,ns,v=candidate(r['raw']);r['origins']=sorted(r['origins']);r['namespace']=ns
  if p is None:r['state']='UNRESOLVED_NAMESPACE'
  else:r.update(guarded(p));r['path']=str(p)
 configs=[]
 for p in [Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/Binarize/bin/config.cpp'),Path('P:/bin/config.cpp'),Path('P:/core/config.cpp')]:
  tick();g=guarded(p);entry={'path':str(p),**g}
  if g['state']=='LOCATED_NOT_READ':
   c=read(p,8*1024**2);entry.update(sha256=sha(c),bytes=len(c),includes=[s for s in c.decode('utf-8-sig').splitlines() if s.lstrip().startswith('#include')],state='OBSERVED_TEXT')
  configs.append(entry)
 tools=[]
 for p in [Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/Binarize'),Path('C:/Program Files (x86)/Mikero/DePboTools/bin')]:
  need(guarded(p)['state']=='LOCATED_NOT_READ','TOOLS_ROOT')
  for q in p.iterdir():
   tick();need(len(tools)<256,'INCONCLUSIVE_RESOURCE_TOOLS');tools.append({'directory':str(p),'name':q.name})
 report={'status':'PLANNING_RESOURCE_OBSERVATIONS_ONLY','source_control_sha256':'f00c3f57ab3660e93c44a1cb612c6338f87db1bfd4c047acf6f7389c61c7e6df','table_sha256':sha(table),'material_count':count,'groups':groups,'materials':materials,'references':refrows,'config_refs':config_refs,'core_configs':configs,'tool_entries':tools,'read_receipts':READS,'bytes_read':READ,'seconds':time.monotonic()-T,'build_ready':False,'dependency_closure':'NOT_EVALUATED','compiled_terrain_decoder':'NOT_VERIFIED','map_changed':False}
 write('report.json',report);print(json.dumps({'status':report['status'],'materials':len(materials),'references':len(refrows),'read_bytes':READ,'output_bytes':OUT,'seconds':report['seconds']}))
if __name__=='__main__':
 try:run()
 except Exception as e:
  if O.exists():
   try:write('failure.json',{'status':'INCONCLUSIVE_RESEARCH','error_type':type(e).__name__,'error':str(e),'read_bytes':READ,'seconds':time.monotonic()-T})
   except Exception:pass
  raise
