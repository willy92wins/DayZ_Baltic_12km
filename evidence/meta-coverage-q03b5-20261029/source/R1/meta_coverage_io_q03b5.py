"""Bounded pinned I/O only; never decides model coverage."""
from pathlib import Path
from contextlib import contextmanager
import json,os,hashlib,types,math
class Rejected(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)
def need(ok,code):
    if not ok:raise Rejected(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def same(a,b):
    if type(a)!=type(b):return False
    if type(a) is dict:return a.keys()==b.keys() and all(same(a[k],b[k]) for k in a)
    if type(a) is list:return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    return a==b
def pairs(xs):
    d={}
    for k,v in xs:need(k not in d,'SCHEMA');d[k]=v
    return d
def finite(x):v=float(x);need(math.isfinite(v),'SCHEMA');return v
def parse(b):
    try:return json.loads(b,object_pairs_hook=pairs,parse_float=finite,parse_constant=lambda x:need(False,'SCHEMA'))
    except (ValueError,UnicodeError,RecursionError) as e:raise Rejected('SCHEMA') from e
def read(pin,limit=16777216):
    p=Path(pin['path']);need(p.is_absolute(),'SCHEMA')
    try:
        for q in [p,*p.parents]:s=q.lstat();need(not q.is_symlink() and not getattr(s,'st_file_attributes',0)&0x400,'REPARSE')
        a=p.stat();need(0<a.st_size<=limit,'INPUT_CAP')
        with p.open('rb') as f:
            b=os.fstat(f.fileno());data=f.read(a.st_size);tail=f.read(1);z=os.fstat(f.fileno())
        identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
        need(identity(a)==identity(b)==identity(z)==identity(p.stat()) and not tail and len(data)==a.st_size,'SOURCE_CHANGED')
    except OSError as e:raise Rejected('IO_ERROR') from e
    need(sha(data)==pin['sha256'] and ('bytes' not in pin or len(data)==pin['bytes']),'IDENTITY');return data
def load(path,digest):
    c=parse(read({'path':str(path),'sha256':digest}));need(c['schema']=='q03b5-meta-witness-v1','SCHEMA');s=parse(read(c['scene']))
    need(s['schema']=='q03b-saved-scene-binding-r1' and same(c['epoch'],s['epoch']),'EPOCH')
    need(same(c['catalog'],s['pins']['deployed-surface-prototypes-20261028/model-catalog.json']) and same(c['sections'],s['pins']['deployed-surface-prototypes-20261028/model-sections.json']),'EPOCH')
    matches=[a for a in s['arrays'] if a['kind']=='prototypes'];need(len(matches)==1 and same(c['archive'],matches[0]),'EPOCH')
    need(type(c['rows']) is int and c['rows']==s['expected']['prototype_faces'],'SCHEMA')
    expected={'vertices.npy':{'dtype':'<f8','shape':[c['rows'],4,3]},'meta.npy':{'dtype':s['npz_schemas']['prototypes']['meta']['descr'],'shape':[c['rows']]}}
    need(same(c['schemas'],expected),'SCHEMA');read(c['writer']);read(c['failure']);return c
@contextmanager
def sources(c):
    cat=parse(read(c['catalog']));sections=parse(read(c['sections']))
    pin=c['helpers']['saved_scene_archive_q03b2.py'];code=read(pin,65536);m=types.ModuleType('q03b5_sealed');m.__file__=pin['path'];exec(compile(code,pin['path'],'exec'),m.__dict__)
    need(m.HEADER_SHA==c['helpers']['saved_scene_npy_header_q03b1l.py']['sha256'],'IDENTITY');read(c['helpers']['saved_scene_npy_header_q03b1l.py'],65536)
    lim={k:c['limits'][k] for k in ('stored','archive','total','members')};session=m.Session(**lim)
    a=c['archive'];raw,digest=m._snapshot(Path(a['path']),m.Session(**lim));need(digest==a['sha256'] and len(raw)==a['bytes'],'IDENTITY');del raw
    with session.open(Path(a['path']),c['schemas']) as result:
        need(result['source_sha256']==digest,'SOURCE_CHANGED');need(result['arrays']['meta.npy'].dtype.itemsize==35,'SCHEMA')
        yield cat,sections,result
def provenance(c,r):return {'catalog_sha256':c['catalog']['sha256'],'sections_sha256':c['sections']['sha256'],'archive_sha256':r['source_sha256'],'meta_sha256':r['payloads']['meta.npy']['sha256'],'meta_bytes':r['payloads']['meta.npy']['bytes'],'epoch':c['epoch']}
def emit(p,v,limit=4194304):
    data=(json.dumps(v,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode();need(len(data)<=limit,'OUTPUT_CAP')
    with Path(p).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
