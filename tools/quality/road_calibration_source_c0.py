"""Create a 0/3-object laboratory source pair; never edit the production WRP."""
from pathlib import Path
import argparse,hashlib,json,math,os,stat,struct,sys
MAX_SOURCE=512*1024**2
MAX_PREFIX=32*1024**2
MAX_OUTPUT=64*1024**2
CHUNK=1024**2
class Error(Exception):
 def __init__(self,code):super().__init__(code);self.code=code
def need(ok,code):
 if not ok:raise Error(code)
def digest(b):return hashlib.sha256(b).hexdigest()
def stamp(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def guard_path(p):
 for q in (p,*p.parents):
  try:s=q.lstat()
  except FileNotFoundError:continue
  need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&1024,'REPARSE')
def bounded_json(p,expected):
 guard_path(p);need(p.stat().st_size<=CHUNK,'CONTRACT')
 with p.open('rb') as f:
  first=stamp(os.fstat(f.fileno()));b=f.read(CHUNK+1);need(stamp(os.fstat(f.fileno()))==first==stamp(p.stat()),'SOURCE_CHANGED')
 need(len(b)<=CHUNK and len(b)==first[2] and digest(b)==expected,'CONTRACT')
 try:return json.loads(b,parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
 except (ValueError,UnicodeError):raise Error('CONTRACT')
def unpack_hex(s,n=None):
 need(type(s) is str and len(s)%2==0 and all(c in '0123456789abcdef' for c in s),'CONTRACT')
 b=bytes.fromhex(s);need(n is None or len(b)==n,'CONTRACT');return b
def contract(path,pin):
 c=bounded_json(Path(path),pin)
 need(type(c) is dict and set(c)=={'schema','domain','source','objects','output','consumer_result','pins'},'CONTRACT')
 need(c['schema']=='road-calibration-source-pair.v1' and c['domain']=='ISOLATED_LAB_ONLY','CONTRACT')
 s=c['source'];need(type(s) is dict and set(s)=={'path','sha256','bytes','terrain_material_prefix_bytes','terrain_material_prefix_sha256','source_pre_terminator_bytes','terminator_hex'},'CONTRACT')
 for k in ('bytes','terrain_material_prefix_bytes','source_pre_terminator_bytes'):need(type(s[k]) is int and s[k]>=0,'CONTRACT')
 need(s['bytes']<=MAX_SOURCE,'SOURCE_CAP');need(24<=s['terrain_material_prefix_bytes']<=MAX_PREFIX and s['terrain_material_prefix_bytes']+56<=s['bytes'] and s['source_pre_terminator_bytes']==s['bytes']-56,'CONTRACT')
 for k in ('sha256','terrain_material_prefix_sha256'):unpack_hex(s[k],32)
 term=unpack_hex(s['terminator_hex'],56);need(term[-4:]==b'\0'*4,'CONTRACT')
 need(type(c['objects']) is list and len(c['objects'])==3,'CONTRACT');records=[];ids=set()
 for o in c['objects']:
  need(type(o) is dict and set(o)=={'id','raw_name_hex','matrix48_hex','record_bytes'},'CONTRACT')
  need(type(o['id']) is int and 0<o['id']<=0xffffffff and o['id'] not in ids,'CONTRACT');ids.add(o['id'])
  name=unpack_hex(o['raw_name_hex']);need(0<len(name)<=4096 and all(32<=b<127 for b in name),'CONTRACT')
  text=name.decode('ascii').replace('\\','/');need(':' not in text and all(p not in ('','.','..') for p in text.split('/')) and text.lower().endswith('.p3d'),'CONTRACT')
  mat=unpack_hex(o['matrix48_hex'],48);need(all(math.isfinite(x) for x in struct.unpack('<12f',mat)),'CONTRACT')
  need(type(o['record_bytes']) is int and o['record_bytes']==56+len(name),'CONTRACT');records.append(mat+struct.pack('<II',o['id'],len(name))+name)
 need(2*(s['terrain_material_prefix_bytes']+56)+sum(map(len,records))<=MAX_OUTPUT,'CONTRACT')
 for key in ('output','consumer_result'):
  need(type(c[key]) is str and Path(c[key]).is_absolute(),'CONTRACT')
 need(type(s['path']) is str and Path(s['path']).is_absolute(),'CONTRACT')
 need(Path(c['output'])!=Path(s['path']) and Path(c['consumer_result']).parent!=Path(c['output']),'CONTRACT')
 need(type(c['pins']) is dict and len(c['pins'])<=32,'CONTRACT')
 for p,h in c['pins'].items():
  need(type(p) is str and Path(p).is_absolute(),'CONTRACT');unpack_hex(h,32);guard_path(Path(p));need(Path(p).stat().st_size<=CHUNK,'CONTRACT');need(digest(Path(p).read_bytes())==h,'CONTRACT')
 return c,records,term
def parse_prefix(b):
 need(len(b)>=24,'SOURCE_STRUCTURE');magic,tx,tz,nx,nz,cell=struct.unpack_from('<4s4If',b)
 need(magic==b'0WZD' and min(tx,tz,nx,nz)>0 and math.isfinite(cell) and cell>0,'SOURCE_STRUCTURE')
 at=24+nx*nz*4+tx*tz*2;need(at+4<=len(b),'SOURCE_STRUCTURE');count=struct.unpack_from('<I',b,at)[0];at+=4;need(count<=(len(b)-at)//4,'SOURCE_STRUCTURE')
 for _ in range(count):
  while True:
   need(at+4<=len(b),'SOURCE_STRUCTURE');n=struct.unpack_from('<I',b,at)[0];at+=4
   if n==0:break
   need(at+n<=len(b),'SOURCE_STRUCTURE');at+=n
 need(at==len(b),'SOURCE_STRUCTURE')
def source(c):
 s=c['source'];p=Path(s['path']);guard_path(p);before=stamp(p.stat());need(before[2]<=MAX_SOURCE,'SOURCE_CAP');need(before[2]==s['bytes'],'SOURCE_HASH')
 prefix=bytearray();h=hashlib.sha256();total=0;tail=b''
 with p.open('rb') as f:
  need(stamp(os.fstat(f.fileno()))==before,'SOURCE_CHANGED')
  while True:
   b=f.read(CHUNK)
   if not b:break
   total+=len(b);need(total<=s['bytes'],'SOURCE_CHANGED');h.update(b)
   remain=s['terrain_material_prefix_bytes']-len(prefix)
   if remain>0:prefix.extend(b[:remain])
   tail=(tail+b)[-56:]
  need(stamp(os.fstat(f.fileno()))==before==stamp(p.stat()),'SOURCE_CHANGED')
 need(total==s['bytes'] and h.hexdigest()==s['sha256'],'SOURCE_HASH');need(digest(prefix)==s['terrain_material_prefix_sha256'],'SOURCE_HASH');need(tail==bytes.fromhex(s['terminator_hex']),'SOURCE_STRUCTURE');parse_prefix(prefix)
 return prefix,before
def report_value(c,pin,identity,files):
 return {'status':'ISOLATED_SOURCE_PAIR_ONLY','contract_sha256':pin,'source_sha256':c['source']['sha256'],'source_identity':identity,'terrain_material_prefix_bytes':c['source']['terrain_material_prefix_bytes'],'terrain_material_prefix_sha256':c['source']['terrain_material_prefix_sha256'],'files':files,'control_objects':0,'candidate_objects':3,'original_object_census':'INHERITED_B3_NOT_REPEATED','build_ready':False,'native_pivot':'UNKNOWN','map_changed':False}
def create(path,pin):
 c,records,term=contract(path,pin);root=Path(c['output']);guard_path(root);need(not root.exists(),'OUTPUT_EXISTS');root.mkdir();(root/'CONSUMED').write_bytes(b'one isolated source pair attempt\n')
 prefix,identity=source(c);files={}
 for name,parts in [('control.wrp',[prefix,term]),('candidate.wrp',[prefix,*records,term])]:
  h=hashlib.sha256();n=0
  with (root/name).open('xb') as f:
   for b in parts:
    need(n+len(b)<=MAX_OUTPUT,'CONTRACT');f.write(b);h.update(b);n+=len(b)
   f.flush();os.fsync(f.fileno())
  files[name]={'sha256':h.hexdigest(),'bytes':n}
 # A second bounded source hash is a final snapshot, not continuous surveillance.
 _,after=source(c);need(after==identity,'SOURCE_CHANGED')
 report=report_value(c,pin,identity,files);b=(json.dumps(report,indent=2,sort_keys=True)+'\n').encode();need(len(b)<=CHUNK,'CONTRACT')
 with (root/'report.json').open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return report
def main():
 p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--contract-sha256',required=True);a=p.parse_args()
 try:r=create(a.contract,a.contract_sha256);code=0
 except Error as e:r={'status':'REJECTED','code':e.code};code=1
 except OSError as e:r={'status':'REJECTED','code':'IO_ERROR','error_type':type(e).__name__};code=2
 except Exception as e:r={'status':'REJECTED','code':'INTERNAL_ERROR','error_type':type(e).__name__};code=3
 print(json.dumps(r));return code
if __name__=='__main__':sys.exit(main())
