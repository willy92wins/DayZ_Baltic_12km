"""Shared pinned I/O and checked rational scalars; no polygon geometry."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,math,os,types,argparse,sys
import numpy as np
IO_SHA='d0734c068d59c87a9d35e31e431a0eb864d4e5ce22d29b2ab9c597c62bd15a44'
CAPS={'bits':4096,'ops':100000,'pieces':1024,'vertices':8192,'output':33554432,'retained_arrays':16777216}
CLAIMS={'terrain_evaluated':False,'exposure_evaluated':False,'native_acceptance':False,'map_repaired':False,'human_resolved':0,'C1':'NOT_REVIEWED'}
class Rejected(Exception):
 def __init__(self,code,detail=''):self.code=code;super().__init__(code+(':'+detail if detail else ''))
def need(x,code,detail=''):
 if not x:raise Rejected(code,detail)
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def exact(a,b):return type(a)==type(b) and (a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a) if type(a) is dict else len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b)) if type(a) is list else a==b)
def pairs(rows):
 d={}
 for k,v in rows:need(k not in d,'SCHEMA');d[k]=v
 return d
def parse(b):
 def bad(x):raise Rejected('SCHEMA','nonfinite')
 try:return json.loads(b,object_pairs_hook=pairs,parse_constant=bad)
 except (ValueError,UnicodeError,RecursionError) as e:raise Rejected('SCHEMA','JSON') from e
def read(path,pin=None,cap=16777216):
 p=Path(path);need(p.is_absolute() and '..' not in p.parts,'SCHEMA')
 for q in (p,*p.parents):
  s=os.lstat(q);need(not q.is_symlink() and not getattr(s,'st_file_attributes',0)&0x400,'REPARSE')
 identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
 before=p.stat();need(0<before.st_size<=cap,'SCHEMA','size')
 with p.open('rb') as f:
  first=os.fstat(f.fileno());b=f.read(before.st_size);tail=f.read(1);last=os.fstat(f.fileno())
 need(identity(before)==identity(first)==identity(last)==identity(p.stat()) and len(b)==before.st_size and not tail,'SOURCE_CHANGED')
 if pin:need(digest(b)==pin['sha256'] and ('bytes' not in pin or len(b)==pin['bytes']),'IDENTITY')
 return b
def config(path,sha):
 c=parse(read(path,{'sha256':sha}));need(c['schema']=='q03c1-selected-water-overlay-v1','SCHEMA')
 need(exact(c['claims'],CLAIMS) and exact(c['limits'],CAPS),'SCHEMA','limits/claims')
 need(c['io']['sha256']==IO_SHA,'IDENTITY','sealed IO');b=read(c['io']['path'],c['io'],65536)
 m=types.ModuleType('_q03c1_saved_io');m.__file__=c['io']['path'];exec(compile(b,m.__file__,'exec'),m.__dict__)
 return c,m
class Budget:
 def __init__(self,limits=None):
  self.limits=dict(CAPS)
  if limits:
   need(all(k in CAPS and type(v) is int and 0<v<=CAPS[k] for k,v in limits.items()),'SCHEMA');self.limits.update(limits)
  self.ops=0;self.peak_pieces=0;self.peak_vertices=0
 def tick(self):
  need(self.ops<self.limits['ops'],'RESOURCE_INCONCLUSIVE','ops');self.ops+=1
 def bound(self,*bits):need(max(bits,default=0)<=self.limits['bits'],'RESOURCE_INCONCLUSIVE','bits')
 def check(self,q):self.bound(abs(q.numerator).bit_length(),q.denominator.bit_length());return q
 def val(self,v):
  self.tick();need(type(v) in (int,float) and (type(v) is int or math.isfinite(v)),'GEOMETRY')
  n,d=v.as_integer_ratio() if type(v) is float else (v,1);self.bound(abs(n).bit_length(),d.bit_length());return F(n,d)
 def op(self,a,b,kind):
  self.tick();self.check(a);self.check(b);an,ad,bn,bd=abs(a.numerator).bit_length(),a.denominator.bit_length(),abs(b.numerator).bit_length(),b.denominator.bit_length()
  if kind in ('add','sub'):self.bound(max(an+bd,bn+ad)+1,ad+bd);v=a+b if kind=='add' else a-b
  elif kind=='mul':self.bound(an+bn,ad+bd);v=a*b
  elif kind=='div':need(b.numerator!=0,'INTERNAL_ERROR','zero denominator');self.bound(an+bd,ad+bn);v=a/b
  else:raise Rejected('INTERNAL_ERROR','operation')
  return self.check(v)
 def add(self,a,b):return self.op(a,b,'add')
 def sub(self,a,b):return self.op(a,b,'sub')
 def mul(self,a,b):return self.op(a,b,'mul')
 def div(self,a,b):return self.op(a,b,'div')
 def cmp(self,a,b):
  self.tick();self.check(a);self.check(b);self.bound(abs(a.numerator).bit_length()+b.denominator.bit_length(),abs(b.numerator).bit_length()+a.denominator.bit_length());return (a>b)-(a<b)
 def reserve(self,pieces,vertices):
  need(pieces<=self.limits['pieces'] and vertices<=self.limits['vertices'],'RESOURCE_INCONCLUSIVE','pieces/vertices');self.peak_pieces=max(self.peak_pieces,pieces);self.peak_vertices=max(self.peak_vertices,vertices)
 def sum(self,values):
  r=F(0)
  for v in values:r=self.add(r,v)
  return r
 def stats(self):return {'ops':self.ops,'peak_pieces':self.peak_pieces,'peak_vertices':self.peak_vertices}
def pack(q):return [q.numerator,q.denominator]
def unpack(q):
 need(type(q) is list and len(q)==2 and all(type(x) is int for x in q),'REPORT','rational type');n,d=q
 need(d>0 and max(abs(n).bit_length(),d.bit_length())<=4096 and math.gcd(n,d)==1 and (n!=0 or d==1),'REPORT','rational canonical');return F(n,d)
def validate_face(a,n=3,flag=0,padding=None):
 need(type(n) is int and n==3 and type(flag) is int and flag==0,'GEOMETRY')
 need(type(a) is list and len(a)==3 and all(type(p) is list and len(p)==3 for p in a),'GEOMETRY')
 need(all(type(v) in (int,float) and (type(v) is int or math.isfinite(v)) for p in a for v in p),'GEOMETRY')
 if padding is not None:need(np.array_equal(np.asarray(padding,dtype='<f8').view('<u8'),np.zeros(3,'<u8')),'GEOMETRY','padding')
def key_ok(k):need(type(k) is list and len(k)==3 and type(k[0]) is int and type(k[1]) is int and k[0]>=0 and k[1]>=0 and type(k[2]) is list and len(k[2])==2 and all(type(v) is int and v>=0 for v in k[2]),'SCHEMA','face key')
def fixture_data(path,sha):
 b=read(path,{'sha256':sha},1048576);x=parse(b);need(type(x) is dict and set(x)=={'bed','water'},'SCHEMA')
 for group in ('bed','water'):
  need(type(x[group]) is list and len(x[group])<=128,'SCHEMA');seen=set()
  for row in x[group]:
   need(type(row) is dict and set(row)=={'key','triangle'},'SCHEMA');key_ok(row['key']);validate_face(row['triangle']);k=canonical(row['key']);need(k not in seen,'IDENTITY','duplicate key');seen.add(k)
 need(len(x['bed'])>0,'SCHEMA');return x['bed'],x['water'],{'mode':'FIXTURE','sha256':digest(b)}
def historical(c,I):
 s=I.parse(I.read_small(c['scene']['path'],c['scene']));cc=I.parse(I.read_small(c['index_contract']['path'],c['index_contract']));idx=I.parse(I.read_small(c['index']['path'],c['index']));proof=I.parse(I.read_small(c['index_consumer']['path'],c['index_consumer']))
 # Saved consumer binds its contract; exact report bytes are independently pinned
 # in this external contract. Do not invent a report_sha256 field in that receipt.
 need(proof['status']=='VERIFIED_SAVED_SELECTED_SURFACE_INDEX_ONLY' and proof['files_read']==204 and proof['contract_sha256']==c['index_contract']['sha256'] and idx['status']==proof['status'],'IDENTITY','proof')
 need(idx['contract_sha256']==c['index_contract']['sha256'] and exact(s['epoch'],c['epoch']) and cc['scene']['sha256']==c['scene']['sha256'],'IDENTITY','epoch')
 for p in c['receipts']:
  v=I.parse(I.read_small(p['path'],p));need(v['rc']==0 and v['reason'] is None,'IDENTITY','completion')
 for p in s['pins'].values():I.read_small(p['path'],p)
 need(all(cc['limits'][k]==v for k,v in c['archive_limits'].items()),'IDENTITY')
 rd=I.Reader(cc);pilots={p['model_index']:p for p in idx['pilots']};need(len(pilots)==len(idx['pilots'])==c['pilot_count'],'IDENTITY')
 specs={p['relative']:p for p in s['arrays'] if p['kind']=='pilot'};need(len(specs)==c['pilot_count'],'IDENTITY','specs')
 waters=[];beds=[];retained=0;inventory=[]
 for mi,p in sorted(pilots.items()):
  need(p['archive'] in specs,'IDENTITY','spec')
  spec=specs[p['archive']];desc=p['arraydigestmap'];names=[n[:-4] for n in desc]
  def pred(heads):need(exact(heads,{n:{'dtype':d['descriptor'],'shape':d['shape']} for n,d in desc.items()}),'IDENTITY','descriptors')
  with rd.open(spec,names,pred) as (arrays,actual):
   need(exact(desc,actual),'IDENTITY','array digests')
   groups=['water']+(['bed'] if mi==c['target']['model_index'] else [])
   for group in groups:
    v=arrays[group];counts=arrays[group+'_n'];flags=arrays[group+'_flags'];ids=arrays[group+'_source_ids'];n=len(v)
    need(v.dtype==np.dtype('<f8') and ids.dtype.kind in 'iu' and v.shape==(n,4,3) and ids.shape==(n,2) and counts.shape==flags.shape==(n,) and np.isfinite(v).all() and np.all(counts==3) and not np.any(flags),'GEOMETRY')
    need(not np.any(v[:,3,:].view('<u8')),'GEOMETRY','padding')
    # Conservative retained Python list budget: 1024 bytes per triangle including keys.
    need(retained+n*1024<=c['limits']['retained_arrays'],'RESOURCE_INCONCLUSIVE','retained');retained+=n*1024
    target=waters if group=='water' else beds
    for j in range(n):
     row={'key':[mi,j,[int(z) for z in ids[j]]],'triangle':v[j,:3].tolist()};key_ok(row['key']);target.append(row)
   inventory.append({'archive':p['archive'],'sha256':spec['sha256'],'members':actual})
 need(len(waters)==c['water_count'] and len(beds)==c['target']['bed_count'],'IDENTITY','count')
 p=pilots[c['target']['model_index']]
 need(all(p[k]==c['target'][k] for k in ('model_index','model','instance_id','pose_row')),'IDENTITY','target')
 return beds,waters,{'mode':'HISTORICAL','epoch':s['epoch'],'index_sha256':c['index']['sha256'],'archives':inventory,'retained_charge':retained}
def result(key,b,status,areas=None,pair_rows=None,contacts=None,detail=None):
 return {'key':key,'status':status,'areas':areas,'pairs':pair_rows or [],'contacts':contacts or [],'detail':detail,'stats':b.stats()}
def semantic(r):
 need(type(r) is dict and set(r)=={'key','status','areas','pairs','contacts','detail','stats'},'REPORT');key_ok(r['key'])
 need(r['status'] in ('DEFINED','DEGENERATE_PROJECTION','INCONCLUSIVE_GEOMETRY','RESOURCE_INCONCLUSIVE'),'REPORT')
 need((r['status']=='DEFINED')==(r['areas'] is not None),'REPORT')
 st=r['stats'];need(type(st) is dict and set(st)=={'ops','peak_pieces','peak_vertices'} and all(type(v) is int and v>=0 for v in st.values()),'REPORT')
 need(st['ops']<=CAPS['ops'] and st['peak_pieces']<=CAPS['pieces'] and st['peak_vertices']<=CAPS['vertices'],'REPORT')
 if r['areas'] is not None:
  need(type(r['areas']) is list and len(r['areas'])==3,'REPORT');need(all(unpack(q)>=0 for q in r['areas']),'REPORT')
 need(type(r['pairs']) is list and type(r['contacts']) is list,'REPORT')
 for p in r['pairs']:
  need(type(p) is dict and set(p)=={'water','area','min_W_B','max_W_B'},'REPORT');key_ok(p['water']);need(unpack(p['area'])>0 and unpack(p['min_W_B'])<=unpack(p['max_W_B']),'REPORT')
 for k in r['contacts']:key_ok(k)
 return {k:v for k,v in r.items() if k!='stats'}
class Output:
 def __init__(self,path,cap):self.path=Path(path);self.path.mkdir(exist_ok=False);self.cap=cap;self.used=0
 def write(self,name,value):
  data=canonical(value);need(self.used+len(data)<=self.cap,'OUTPUT_CAP');p=self.path/name;temp=self.path/(name+'.tmp');need(not p.exists() and not temp.exists(),'TERMINAL')
  with temp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(temp,p);self.used+=len(data);return {'bytes':len(data),'sha256':digest(data)}
 def terminal(self,i,row):
  n=f'{i:04d}.json';encoded=canonical(row);receipt={'seq':i,'bytes':len(encoded),'sha256':digest(encoded)}
  need(self.used+len(encoded)+len(canonical(receipt))<=self.cap,'OUTPUT_CAP')
  self.write(n,row);self.write(f'{i:04d}.receipt.json',receipt)
def prefix(path,cap):
 path=Path(path);entries=list(path.iterdir());need(all(p.is_file() and not p.is_symlink() for p in entries),'TERMINAL');names={p.name for p in entries};size=sum(p.stat().st_size for p in entries);need(size<=cap,'OUTPUT_CAP')
 receipts=sorted(n for n in names if n.endswith('.receipt.json'));rows=[]
 for i,n in enumerate(receipts):
  need(n==f'{i:04d}.receipt.json','TERMINAL','gap');r=parse(read(path/n));need(type(r) is dict and set(r)=={'seq','bytes','sha256'} and type(r['seq']) is int and r['seq']==i and type(r['bytes']) is int,'TERMINAL')
  b=read(path/f'{i:04d}.json',r,cap=cap);rows.append(parse(b))
 allowed={'header.json','manifest.json'}|{f'{i:04d}{suffix}' for i in range(len(rows)) for suffix in ('.json','.receipt.json')}
 if 'manifest.json' not in names:allowed|={f'{len(rows):04d}{suffix}' for suffix in ('.json','.json.tmp','.receipt.json.tmp')}
 need(names<=allowed,'TERMINAL','unexpected/orphan files')
 return rows
def arguments(consumer=False):
 p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--sha',required=True);p.add_argument('--out',required=True);p.add_argument('--fixture');p.add_argument('--fixture-sha')
 if consumer:p.add_argument('--capture',required=True)
 return p.parse_args()
def data(c,I,a):return fixture_data(a.fixture,a.fixture_sha) if a.fixture else historical(c,I)
def main_guard(fn):
 try:fn()
 except Exception as e:
  code=getattr(e,'code',None) or ('IO_ERROR' if isinstance(e,OSError) else 'INTERNAL_ERROR');print(json.dumps({'status':'REJECTED','code':code,'detail':str(e)}),file=sys.stderr);sys.exit(1)
