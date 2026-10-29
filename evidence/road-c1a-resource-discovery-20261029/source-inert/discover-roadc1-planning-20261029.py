from pathlib import Path
import hashlib,json,struct,time,os
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
D=R/'road-c1-planning-discovery-20261029'
D.mkdir(exist_ok=False)
t=time.monotonic(); used=0
def read(p,cap=1024*1024):
 global used
 assert time.monotonic()-t<60
 p=Path(p);s=p.stat();assert s.st_size<=cap and used+s.st_size<=64*1024**2
 b=p.read_bytes();assert len(b)==s.st_size and p.stat().st_mtime_ns==s.st_mtime_ns
 used+=len(b);return b
def sh(b):return hashlib.sha256(b).hexdigest()
def save(n,v):(D/n).write_bytes((json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
save('scope-before.json',{'purpose':'planning only: source material names and saved stage dependencies','seconds':60,'read_bytes_cap':67108864,'per_text_cap':1048576,'max_material_entries':4096,'max_references':8192,'no_build':True,'no_stage_copy':True,'no_PBO':True,'no_original_population_census':True,'no_tools_executed':True})
p=R/'road-c0-isolated-sources-20261029/control.wrp';b=read(p,32*1024**2)
assert sh(b)=='f00c3f57ab3660e93c44a1cb612c6338f87db1bfd4c047acf6f7389c61c7e6df'
magic,tx,tz,nx,nz,cell=struct.unpack_from('<4s4If',b);assert magic==b'0WZD'
at=24+nx*nz*4+tx*tz*2;count=struct.unpack_from('<I',b,at)[0];at+=4
assert count<=4096
groups=[]
for i in range(count):
 row=[]
 while True:
  n=struct.unpack_from('<I',b,at)[0];at+=4
  if n==0:break
  assert 0<n<=4096 and at+n<=len(b);raw=b[at:at+n];at+=n
  row.append(raw.decode('ascii'))
 groups.append(row)
assert at==17307629
root=R/'stage-kit7-fc-20261026/root';local=[];refs=set();configs=[]
for raw in sorted({s for g in groups for s in g}):
 rel=raw.replace('\\','/').strip('\0');assert ':' not in rel and '..' not in rel.split('/')
 f=root/rel
 if not f.is_file():local.append({'path':raw,'state':'MISSING'});continue
 data=read(f);text=data.decode('utf-8-sig');strings=[]
 # Observation of quoted strings only; NOT a semantic dependency parser.
 pos=0
 while True:
  a=text.find('"',pos)
  if a<0:break
  z=text.find('"',a+1);assert z>=0;strings.append(text[a+1:z]);pos=z+1
 for s in strings:
  if s.lower().endswith(('.paa','.rvmat','.p3d','.bisurf')):refs.add(s)
 assert len(refs)<=8192
 local.append({'path':raw,'state':'OBSERVED_TEXT','sha256':sh(data),'bytes':len(data),'quoted_strings':strings})
references=[]
for raw in sorted(refs):
 rel=raw.replace('\\','/').lstrip('/');assert ':' not in rel and '..' not in rel.split('/')
 candidate=root/rel
 kind='SAVED_STAGE'
 if not candidate.is_file():candidate=Path('P:/')/rel;kind='BUILD_PATH_UNPINNED'
 if candidate.is_file():
  s=candidate.stat();references.append({'raw':raw,'path':str(candidate),'state':'LOCATED_NOT_READ','source':kind,'bytes':s.st_size})
 else:references.append({'raw':raw,'state':'MISSING'})
cfg=root/'dayz_baltic_12km_dev/tb/narva_trial/config.cpp';data=read(cfg)
save('config-anchor.json',{'path':str(cfg),'bytes':len(data),'sha256':sh(data),'text':data.decode()})
for f in [Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/Binarize/bin/config.cpp'),Path('P:/bin/config.cpp'),Path('P:/core/config.cpp')]:
 if f.is_file():
  data=read(f,8*1024**2);configs.append({'path':str(f),'sha256':sh(data),'bytes':len(data),'prefix_hex':data[:16].hex(),'text_includes':[x for x in data.decode('utf-8-sig',errors='replace').splitlines() if x.lstrip().startswith('#include')]})
 else:configs.append({'path':str(f),'state':'MISSING'})
save('report.json',{'status':'PLANNING_RESOURCE_OBSERVATIONS_ONLY','control_sha256':sh(b),'material_groups':groups,'material_rows':local,'quoted_file_references':references,'core_config_observations':configs,'material_count':count,'prefix_bytes':at,'bytes_read':used,'elapsed_seconds':time.monotonic()-t,'build_ready':False,'dependency_closure':'NOT_EVALUATED','reference_parser':'QUOTED_STRING_OBSERVATION_NOT_SEMANTIC','compiled_decoder':'NOT_LOCATED_CAPABLE_OF_0_3_AND_TERRAIN'})
print(json.dumps({'directory':str(D),'material_count':count,'refs':len(references),'read_bytes':used,'seconds':time.monotonic()-t,'states':{k:sum(r['state']==k for r in references) for k in ['LOCATED_NOT_READ','MISSING']}}))
