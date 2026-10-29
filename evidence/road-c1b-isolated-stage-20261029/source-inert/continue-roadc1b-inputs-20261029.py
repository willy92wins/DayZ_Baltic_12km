from pathlib import Path
import os,stat,time,json,hashlib,difflib
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'road-c1b-local-author-20261029';assert D.is_dir()
START=json.loads((D/'author-start.json').read_bytes())['started']
def put(p,x):
 b=json.dumps(x,ensure_ascii=False,indent=2).encode();assert len(b)<=8*1024**2;p.write_bytes(b);return hashlib.sha256(b).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ident(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def guard(p):
 for a in [p,*p.parents]:
  s=a.lstat();assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&1024,('REPARSE',str(a))
def capture(p):
 p=Path(p);guard(p);before=ident(p.stat());assert 0<=before[2]<=32*1024**2,('FILE_CAP',str(p),before[2]);h=hashlib.sha256();n=0
 with p.open('rb') as f:
  assert before==ident(os.fstat(f.fileno()))
  while True:
   assert time.time()-READ_START<120,'TIMEOUT';b=f.read(1024**2)
   if not b:break
   n+=len(b);assert n<=before[2];h.update(b)
  assert before==ident(os.fstat(f.fileno()))
 guard(p);assert before==ident(p.stat()) and n==before[2]
 return {'path':str(p),'identity':before,'sha256':h.hexdigest(),'bytes':n}
def inp(rel,pin=None):
 p=R/rel;b=p.read_bytes();assert len(b)<8*1024**2
 if pin:assert hashlib.sha256(b).hexdigest()==pin
 return json.loads(b)
old=inp('road-c1a-research-20261029/capture/report.json','f3eb0ab1b672ba742a82d6d7fe2114373c75e3604f30db4ddd508880efb4ce6a')
new=inp('road-c1a1-recovery-20261029/capture/report.json')
b4=inp('road-b4a3-dependencies-20261029/report.json','d5ce5307f926ead5a6f599da96b336c5b76451372e8ebf3f742a06cc5ce930a5')
assert new['input_report_sha256']=='f3eb0ab1b672ba742a82d6d7fe2114373c75e3604f30db4ddd508880efb4ce6a'
cfg=R/'stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb/narva_trial/config.cpp';raw=cfg.read_bytes();lines=raw.decode('utf-8').splitlines(keepends=True)
assert 'class Navmesh' in lines[55] and 'class Names' in lines[212]
literal=''.join(lines[:55]+lines[212:]).replace('BalticTrialWorld','BalticRoadPivotLab').replace('BalticTrial:','BalticRoadPivotLab:').replace('Baltic trial — Narva pilot','Baltic road pivot laboratory')
# Preserve exact other lines; remove the two Baltic dependency lines and preceding comma.
literal=literal.replace('\t\t\t"DZ_Surfaces",','\t\t\t"DZ_Surfaces"')
literal=''.join(l for l in literal.splitlines(keepends=True) if '"Baltic_Water_V30"' not in l and '"Baltic_Stream_Pilot"' not in l)
assert 'Navmesh' not in literal and 'Baltic_Water' not in literal and 'class BalticRoadPivotLab' in literal
# Description is an explicit single-line replacement, not an assumed historical spelling.
literal=''.join('        description = "Baltic road pivot laboratory";\n' if 'description=' in l else l for l in literal.splitlines(keepends=True))
(D/'config.cpp').write_bytes(literal.encode());(D/'config.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),literal.splitlines(True),fromfile='historical',tofile='laboratory')),encoding='utf-8')
items=[]
def add(src,dest,origin,pin=None,size=None,scope='common'):
 items.append((Path(src),dest.replace('\\','/').strip('/').lower(),origin,pin,size,scope))
for a in old['materials']:add(a['path'],a['raw'],'C1A_RVMAT',a['sha256'],a['bytes'])
located=[a for a in new['locations'] if a['state']=='LOCATED_NOT_READ'];assert len(located)==2056
for a in located:add(a['path'],a['normalized'],'C1A1_LITERAL',None,a['identity'][2])
config_refs=[]
for i in [0,1,2,4,5,6,7,8]:
 a=old['references'][i];add(a['path'],a['raw'],'CONFIG_REFERENCE',None,a['identity'][2]);config_refs.append({'raw':a['raw'],'source':a['path'],'dest':a['raw'].replace('\\','/').lower()})
for a in b4['saved_assets']:add(a['path'],a['virtual_path'],'B4A3',a['sha256'],a['size'])
for a in b4['leaves']:add(R/'road-b4a3-dependencies-20261029'/a['output'],a['virtual_path'],'B4A3',a['sha256'],a['size'])
core=Path('P:/core');stack=[core];corefiles=[];entries=0
while stack:
 p=stack.pop();guard(p)
 for c in p.iterdir():
  entries+=1;assert entries<=2048;guard(c)
  if c.is_dir():stack.append(c)
  else:corefiles.append(c)
assert entries==57 and len(corefiles)==41 and sum(p.stat().st_size for p in corefiles)==9717421
for p in sorted(corefiles):add(p,'core/'+p.relative_to(core).as_posix(),'CORE')
add('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/Binarize/bin/config.cpp','bin/config.cpp','INSTALLED_BIN','dcf19f271d6537e6ba45fe6af47cc0865d52768bca05ecc9abc1b0314bc1f4ea',199732)
add(D/'config.cpp','dayz_baltic_12km_dev/tb/narva_trial/config.cpp','LAB_LITERAL',sha(D/'config.cpp'),(D/'config.cpp').stat().st_size)
for arm,pin,size in [('control','f00c3f57ab3660e93c44a1cb612c6338f87db1bfd4c047acf6f7389c61c7e6df',17307685),('candidate','2fb3686b6d86888609caeace3be14f8422cfe8c1da9d77db263c86e21ddcb426',17307968)]:add(R/f'road-c0-isolated-sources-20261029/{arm}.wrp','dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp','C0',pin,size,arm)
READ_START=time.time();seen={};cache={};total=0
try:
 for p,dest,origin,pin,size,scope in items:
  key=(scope,dest);pc=str(p)
  if pc not in cache:cache[pc]=capture(p)
  a=cache[pc].copy();a['origin']=origin
  if pin:assert a['sha256']==pin,('PIN',pc)
  if size is not None:assert a['bytes']==size,('SIZE',pc)
  if key in seen:
   e=seen[key];assert e['sha256']==a['sha256'] and e['bytes']==a['bytes'] and e['sources'][0]['identity']==a['identity'],('COLLISION',dest)
   if a not in e['sources']:e['sources'].append(a)
  else:
   seen[key]={'scope':scope,'dest':dest,'sha256':a['sha256'],'bytes':a['bytes'],'sources':[a]};total+=a['bytes'];assert len(seen)<=8194 and total<=512*1024**2
 files=sorted(seen.values(),key=lambda x:(x['scope'],x['dest']));common=[x for x in files if x['scope']=='common'];cb=sum(x['bytes'] for x in common)
 assert len(common)<=8192 and cb<=384*1024**2 and cb*2+sum(x['bytes'] for x in files if x['scope']!='common')<=1024**3
 bindings=[{'scope':x['scope'],'dest':x['dest'],'sources':[s['path'] for s in x['sources']]} for x in files]
 bs=put(D/'bindings.json',bindings)
 caps={'entries':8192,'file':32*1024**2,'common':384*1024**2,'pair':1024**3,'json':8*1024**2}
 contract={'schema':'road-c1b-stage.v1','caps':caps,'bindings':{'path':str(D/'bindings.json'),'sha256':bs},'files':files,'output':str(R/'road-c1b-stage-20261029'),'claims':{'build_ready':False,'dependency_closure':'NOT_EVALUATED','compiled_terrain_decoder':'NOT_VERIFIED'},'config_refs':config_refs}
 ch=put(D/'contract.json',contract)
 # Small external literal expected set. Runtime fixture may instantiate paths but never derives expected bytes from author.
 oracle={'schema':'road-c1b-literal.v1','common':{'data/a space.png':'PNG literal\n','config.cpp':'class Lab {};\n'},'control':{'lab.wrp':'control zero\n'},'candidate':{'lab.wrp':'candidate three\n'},'claims':contract['claims'],'negatives':['EXTRA','MISSING','STAGE_HASH','SOURCE_PIN','BINDING','COLLISION','PATH','SIZE_TYPE','EXISTS','REPARSE','CONTRACT_PIN','CONFIG','WRP_PIN']}
 oh=put(D/'oracle.json',oracle)
 put(D/'prepared.json',{'status':'MANIFEST_PREPARED_ONLY','contract_sha256':ch,'bindings_sha256':bs,'oracle_sha256':oh,'common_files':len(common),'common_bytes':cb,'core_entries':entries,'core_files':len(corefiles),'seconds':time.time()-READ_START,'pins':{rel:sha(R/rel) for rel in ['road-c1a-research-20261029/capture/report.json','road-c1a1-recovery-20261029/capture/report.json','road-b4a3-dependencies-20261029/report.json']}})
 print((D/'prepared.json').read_text())
except Exception as e:
 put(D/'prepare-rejected.json',{'status':'REJECTED','error':repr(e),'files_observed':len(cache),'seconds':time.time()-READ_START});raise
