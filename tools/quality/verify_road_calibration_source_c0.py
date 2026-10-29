"""Independent cursor readback of an isolated 0/3-object source pair."""
import argparse,hashlib,io,json,math,os,stat,struct,sys
from pathlib import Path
LIMIT=512*1024**2;BLOCK=1024**2
class Error(Exception):
 def __init__(self,code):super().__init__(code);self.code=code
def check(test,code):
 if not test:raise Error(code)
def signature(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def no_links(p):
 q=p
 while True:
  try:s=q.lstat()
  except FileNotFoundError:s=None
  if s:check(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'REPARSE')
  if q.parent==q:break
  q=q.parent
def small(p):
 no_links(p);s=p.stat();check(s.st_size<=BLOCK,'CONTRACT')
 with p.open('rb') as f:
  start=signature(os.fstat(f.fileno()));b=f.read(BLOCK+1);check(start==signature(s)==signature(os.fstat(f.fileno()))==signature(p.stat()),'SOURCE_CHANGED')
 check(len(b)==s.st_size and len(b)<=BLOCK,'SOURCE_CHANGED');return b
def dec(b):
 try:return json.loads(b,parse_constant=lambda x:(_ for _ in ()).throw(ValueError()))
 except (ValueError,UnicodeError):raise Error('CONTRACT')
def hx(t,n=None):
 check(type(t) is str and len(t)%2==0 and all(c in '0123456789abcdef' for c in t),'CONTRACT');b=bytes.fromhex(t);check(n is None or len(b)==n,'CONTRACT');return b
def settings(path,pin):
 raw=small(Path(path));check(hashlib.sha256(raw).hexdigest()==pin,'CONTRACT');c=dec(raw)
 check(type(c) is dict and set(c)=={'schema','domain','source','objects','output','consumer_result','pins'} and c['schema']=='road-calibration-source-pair.v1' and c['domain']=='ISOLATED_LAB_ONLY','CONTRACT')
 s=c['source'];check(type(s) is dict and set(s)=={'path','sha256','bytes','terrain_material_prefix_bytes','terrain_material_prefix_sha256','source_pre_terminator_bytes','terminator_hex'},'CONTRACT')
 check(all(type(s[k]) is int for k in ('bytes','terrain_material_prefix_bytes','source_pre_terminator_bytes')),'CONTRACT');check(0<=s['bytes']<=LIMIT,'SOURCE_CAP')
 check(24<=s['terrain_material_prefix_bytes']<=32*BLOCK and s['terrain_material_prefix_bytes']+56<=s['bytes'] and s['source_pre_terminator_bytes']==s['bytes']-56,'CONTRACT')
 hx(s['sha256'],32);hx(s['terrain_material_prefix_sha256'],32);check(hx(s['terminator_hex'],56)[52:]==b'\0'*4,'CONTRACT')
 check(type(c['objects']) is list and len(c['objects'])==3,'CONTRACT');ids=[];nbytes=0
 for o in c['objects']:
  check(type(o) is dict and set(o)=={'id','raw_name_hex','matrix48_hex','record_bytes'},'CONTRACT');check(type(o['id']) is int and 0<o['id']<2**32 and o['id'] not in ids,'CONTRACT');ids.append(o['id'])
  name=hx(o['raw_name_hex']);check(0<len(name)<=4096 and all(32<=x<127 for x in name),'CONTRACT');v=name.decode('ascii').replace('\\','/');check(':' not in v and v.lower().endswith('.p3d') and all(x not in ('','.','..') for x in v.split('/')),'CONTRACT')
  check(all(math.isfinite(x) for x in struct.unpack('<12f',hx(o['matrix48_hex'],48))),'CONTRACT');check(type(o['record_bytes']) is int and o['record_bytes']==56+len(name),'CONTRACT');nbytes+=o['record_bytes']
 check(2*(s['terrain_material_prefix_bytes']+56)+nbytes<=64*BLOCK,'CONTRACT')
 check(type(s['path']) is str and Path(s['path']).is_absolute(),'CONTRACT')
 for k in ('output','consumer_result'):check(type(c[k]) is str and Path(c[k]).is_absolute(),'CONTRACT')
 check(Path(c['output'])!=Path(s['path']) and Path(c['consumer_result']).parent!=Path(c['output']),'CONTRACT')
 check(type(c['pins']) is dict and len(c['pins'])<=32,'CONTRACT')
 for p,h in c['pins'].items():check(type(p) is str and Path(p).is_absolute(),'CONTRACT');hx(h,32);check(hashlib.sha256(small(Path(p))).hexdigest()==h,'CONTRACT')
 return c
class Cursor:
 def __init__(self,b):self.f=io.BytesIO(b);self.n=len(b)
 def read(self,n):
  check(type(n) is int and 0<=n<=self.n-self.f.tell(),'SOURCE_STRUCTURE');v=self.f.read(n);check(len(v)==n,'SOURCE_STRUCTURE');return v
 def skip(self,n):
  check(0<=n<=self.n-self.f.tell(),'SOURCE_STRUCTURE');self.f.seek(n,1)
 def u32(self):return int.from_bytes(self.read(4),'little')
def prefix_cursor(b):
 r=Cursor(b);check(r.read(4)==b'0WZD','SOURCE_STRUCTURE');tx=r.u32();tz=r.u32();nx=r.u32();nz=r.u32();cell=struct.unpack('<f',r.read(4))[0]
 check(min(tx,tz,nx,nz)>0 and math.isfinite(cell) and cell>0,'SOURCE_STRUCTURE');r.skip(4*nx*nz);r.skip(2*tx*tz);count=r.u32();check(count<=(r.n-r.f.tell())//4,'SOURCE_STRUCTURE')
 for _ in range(count):
  while True:
   n=r.u32()
   if n==0:break
   r.skip(n)
 check(r.f.tell()==r.n,'SOURCE_STRUCTURE')
def load_source(c):
 s=c['source'];p=Path(s['path']);no_links(p);before=signature(p.stat());check(before[2]<=LIMIT,'SOURCE_CAP');check(before[2]==s['bytes'],'SOURCE_HASH');h=hashlib.sha256()
 with p.open('rb') as f:
  check(signature(os.fstat(f.fileno()))==before,'SOURCE_CHANGED');pre=f.read(s['terrain_material_prefix_bytes']);check(len(pre)==s['terrain_material_prefix_bytes'],'SOURCE_STRUCTURE');h.update(pre);remaining=s['bytes']-len(pre)
  while remaining:
   chunk=f.read(min(BLOCK,remaining));check(bool(chunk),'SOURCE_HASH');h.update(chunk);remaining-=len(chunk)
  check(f.read(1)==b'','SOURCE_CHANGED');f.seek(s['source_pre_terminator_bytes']);tail=f.read(56);check(signature(os.fstat(f.fileno()))==before==signature(p.stat()),'SOURCE_CHANGED')
 check(h.hexdigest()==s['sha256'] and hashlib.sha256(pre).hexdigest()==s['terrain_material_prefix_sha256'],'SOURCE_HASH');check(tail==hx(s['terminator_hex'],56),'SOURCE_STRUCTURE');prefix_cursor(pre)
 return pre,before
def inspect_file(p,pre,objects,term):
 no_links(p);ss=signature(p.stat());expected_size=len(pre)+56+sum(o['record_bytes'] for o in objects);check(ss[2]==expected_size<=64*BLOCK,'PAIR_STRUCTURE');h=hashlib.sha256()
 with p.open('rb') as f:
  check(signature(os.fstat(f.fileno()))==ss,'SOURCE_CHANGED')
  for at in range(0,len(pre),BLOCK):
   b=f.read(min(BLOCK,len(pre)-at));check(b==pre[at:at+len(b)] and len(b)==min(BLOCK,len(pre)-at),'PAIR_STRUCTURE');h.update(b)
  for o in objects:
   mat=f.read(48);nums=f.read(8);check(len(mat)==48 and len(nums)==8,'PAIR_STRUCTURE');ident,n=struct.unpack('<II',nums);check(ident==o['id'] and n==len(hx(o['raw_name_hex'])) and mat==hx(o['matrix48_hex'],48),'PAIR_STRUCTURE');name=f.read(n);check(name==hx(o['raw_name_hex']),'PAIR_STRUCTURE');h.update(mat);h.update(nums);h.update(name)
  tail=f.read(56);check(tail==term and f.read(1)==b'','PAIR_STRUCTURE');h.update(tail);check(signature(os.fstat(f.fileno()))==ss==signature(p.stat()),'SOURCE_CHANGED')
 return {'sha256':h.hexdigest(),'bytes':expected_size}
def verify(path,pin):
 c=settings(path,pin);out=Path(c['consumer_result']);no_links(out);check(not out.exists(),'OUTPUT_EXISTS');out.parent.mkdir(parents=True,exist_ok=True)
 with (out.parent/'CONSUMED').open('xb') as f:f.write(b'one readback attempt\n')
 pre,identity=load_source(c);root=Path(c['output']);no_links(root);term=hx(c['source']['terminator_hex'],56)
 check({p.name for p in root.iterdir()}=={'CONSUMED','control.wrp','candidate.wrp','report.json'},'PAIR_STRUCTURE');check(small(root/'CONSUMED')==b'one isolated source pair attempt\n','PAIR_STRUCTURE')
 files={'control.wrp':inspect_file(root/'control.wrp',pre,[],term),'candidate.wrp':inspect_file(root/'candidate.wrp',pre,c['objects'],term)}
 expected={'status':'ISOLATED_SOURCE_PAIR_ONLY','contract_sha256':pin,'source_sha256':c['source']['sha256'],'source_identity':identity,'terrain_material_prefix_bytes':len(pre),'terrain_material_prefix_sha256':hashlib.sha256(pre).hexdigest(),'files':files,'control_objects':0,'candidate_objects':3,'original_object_census':'INHERITED_B3_NOT_REPEATED','build_ready':False,'native_pivot':'UNKNOWN','map_changed':False}
 observed=dec(small(root/'report.json'));check(json.dumps(observed,sort_keys=True)==json.dumps(expected,sort_keys=True),'REPORT_MISMATCH')
 check(signature(Path(c['source']['path']).stat())==identity,'SOURCE_CHANGED')
 result={'status':'VERIFIED_ISOLATED_SOURCE_PAIR_ONLY','contract_sha256':pin,'source_sha256':c['source']['sha256'],'report_sha256':hashlib.sha256(small(root/'report.json')).hexdigest(),'files':files,'control_objects':0,'candidate_objects':3,'build_ready':False,'map_changed':False,'native_pivot':'UNKNOWN','independence':'Own source read, cursor prefix and sequential record traversal; common Python standard libraries'}
 data=(json.dumps(result,indent=2)+'\n').encode();check(len(data)<=BLOCK,'CONTRACT')
 with out.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--contract-sha256',required=True);a=p.parse_args()
 try:r=verify(a.contract,a.contract_sha256);code=0
 except Error as e:r={'status':'REJECTED','code':e.code};code=1
 except OSError as e:r={'status':'REJECTED','code':'IO_ERROR','error_type':type(e).__name__};code=2
 except Exception as e:r={'status':'REJECTED','code':'INTERNAL_ERROR','error_type':type(e).__name__};code=3
 print(json.dumps(r));return code
if __name__=='__main__':sys.exit(main())
