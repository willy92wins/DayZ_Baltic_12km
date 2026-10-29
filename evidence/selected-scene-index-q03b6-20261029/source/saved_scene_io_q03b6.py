"""Pinned I/O only; semantic predicates belong to each caller."""
from pathlib import Path
from contextlib import contextmanager
import hashlib, io, json, os, struct, types, zipfile, math
import numpy as np

class Rejected(Exception):
    def __init__(self, code, detail=''):
        self.code=code;super().__init__(code+(':'+detail if detail else ''))
def require(ok,code,detail=''):
    if not ok:raise Rejected(code,detail)
def digest(data):return hashlib.sha256(data).hexdigest()
def pairs(rows):
    out={}
    for k,v in rows:
        require(k not in out,'SCHEMA','duplicate key');out[k]=v
    return out
def bad_number(x):raise Rejected('SCHEMA','nonfinite JSON')
def finite_float(x):
    value=float(x)
    require(math.isfinite(value),'SCHEMA','nonfinite JSON float')
    return value
def parse(data):
    try:return json.loads(data,object_pairs_hook=pairs,parse_constant=bad_number,parse_float=finite_float)
    except (ValueError,RecursionError,UnicodeError) as e:raise Rejected('SCHEMA','JSON') from e
def keys(obj,names):require(type(obj) is dict and set(obj)==set(names),'SCHEMA','keys')
def exact(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,dict):return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a==b
def load_module(pin):
    p=Path(pin['path']);b=read_small(p,pin,65536)
    m=types.ModuleType('_sealed_q03b6_archive');m.__file__=str(p)
    exec(compile(b,str(p),'exec'),m.__dict__);return m
def read_small(path,pin=None,limit=16777216):
    p=Path(path)
    require(p.is_absolute() and '..' not in p.parts,'SCHEMA','path')
    for q in [p,*p.parents]:
        s=os.lstat(q);require(not q.is_symlink() and not getattr(s,'st_file_attributes',0)&0x400,'REPARSE')
    before=p.stat();require(0<before.st_size<=limit,'JSON_CAP')
    with p.open('rb') as f:
        start=os.fstat(f.fileno());data=f.read(before.st_size);end=os.fstat(f.fileno());tail=f.read(1)
    identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    require(identity(before)==identity(start)==identity(end)==identity(p.stat()) and len(data)==before.st_size and not tail,'SOURCE_CHANGED')
    if pin:require(digest(data)==pin['sha256'] and ('bytes' not in pin or len(data)==pin['bytes']),'IDENTITY',str(p))
    return data
def load_contract(path,sha):
    data=read_small(path,{'sha256':sha});c=parse(data)
    require(c['schema']=='q03b6-covered-domain-index-v1','SCHEMA')
    b=read_small(c['scene']['path'],c['scene']);s=parse(b)
    require(s['schema']=='q03b-saved-scene-binding-r1','SCHEMA')
    for pin in c['evidence_pins'].values():read_small(pin['path'],pin)
    require(exact(c['claims_delta'],{'scene_geometry_complete':False}),'SCHEMA')
    return c,s
def descriptions(arrays,payloads):
    return {n:{'descriptor':a.dtype.str if a.dtype.fields is None else [list(x) for x in a.dtype.descr],
        'shape':list(a.shape),'data_sha256':payloads[n]['sha256'],'bytes':a.nbytes} for n,a in sorted(arrays.items())}
def header_candidate(member,expanded):
    prefix=member.read(8);require(len(prefix)==8 and prefix[:6]==b'\x93NUMPY','SCHEMA','NPY magic')
    require(prefix[6:] in (b'\x01\x00',b'\x02\x00'),'SCHEMA','NPY version')
    width=2 if prefix[6]==1 else 4;raw=member.read(width);require(len(raw)==width,'SCHEMA')
    n=int.from_bytes(raw,'little');require(n<=16384,'HEADER_LIMIT')
    text=member.read(n);require(len(text)==n,'SCHEMA')
    bounded=io.BytesIO(prefix+raw+text);bounded.seek(8)
    parser=np.lib.format.read_array_header_1_0 if width==2 else np.lib.format.read_array_header_2_0
    shape,order,dt=parser(bounded,max_header_size=16384)
    require(not order and not dt.hasobject and dt.subdtype is None,'SCHEMA','unsafe dtype/order')
    require(len(shape)<=3 and all(type(v) is int and 0<=v<=2000000 for v in shape),'SCHEMA','shape')
    count=1
    for v in shape:
        require(v==0 or count<=134217728//v,'SCHEMA','size');count*=v
    require(dt.itemsize>0 and count<=134217728//dt.itemsize and count*dt.itemsize+8+width+n==expanded,'SCHEMA','extent')
    desc=dt.str if dt.fields is None else [list(x) for x in dt.descr]
    return {'dtype':desc,'shape':list(shape)},prefix+raw+text
class Reader:
    def __init__(self,c):
        self.archive=load_module(c['helpers']['saved_scene_archive_q03b2.py'])
        h=c['helpers']['saved_scene_npy_header_q03b1l.py'];require(self.archive.HEADER_SHA==h['sha256'],'IDENTITY','header')
        lim={k:c['limits'][k] for k in ('stored','archive','total','members')}
        self.session=self.archive.Session(**lim);self.records=[];self.json_bytes=0
    def json(self,label,pin):
        data=read_small(pin['path'],pin);self.json_bytes+=len(data);require(self.json_bytes<=33554432,'JSON_CAP')
        self.records.append({'label':label,'sha256':digest(data),'bytes':len(data),'members':None})
        return parse(data)
    @contextmanager
    def open(self,spec,names,predicate):
        probe=self.archive.Session(**self.session.limits)
        data,sha=self.archive._snapshot(Path(spec['path']),probe)
        require(sha==spec['sha256'] and len(data)==spec['bytes'],'IDENTITY','archive')
        rows,expanded=self.archive._central(data,{x+'.npy':None for x in names},self.session.limits)
        require(expanded<=spec['expanded_bound'],'SCHEMA','expanded bound')
        require(expanded<=self.session.limits['total']-self.session.cumulative_expanded_reserved,'TOTAL_CAP')
        schemas={};heads={}
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for row in rows:
                with z.open(row['name']) as f:schemas[row['name']],heads[row['name']]=header_candidate(f,row['expanded'])
        predicate(schemas)
        for row in rows:self.archive.header.inspect_header(io.BytesIO(heads[row['name']]),row['expanded'],schemas[row['name']])
        del data,heads,rows,probe
        with self.session.open(Path(spec['path']),schemas) as result:
            require(result['source_sha256']==sha==spec['sha256'],'SOURCE_CHANGED','inspection/load')
            desc=descriptions(result['arrays'],result['payloads'])
            self.records.append({'label':spec['relative'],'sha256':sha,'bytes':spec['bytes'],'members':desc})
            yield {n[:-4]:a for n,a in result['arrays'].items()},desc
def emit(path,report):
    data=(json.dumps(report,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()
    require(len(data)<=33554432,'OUTPUT_CAP')
    with Path(path).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
