# RoadB4A read-only build discovery. Stdlib only.
# Attribution: exact/string/pbo_table adapted from tools/quality/deployed_surface_inventory_ev112.py
# pinned helper sha256 b7a17598c68294622b4bf2ba8bb36afe74d91b24876b8451e10ab0425651bcb6
import argparse
import ctypes
import hashlib
import json
import ntpath
import os
import re
import stat
import struct
from ctypes import wintypes
from pathlib import Path
BSL=chr(92)
REPARSE=0x400
REPARSE_SYMLINK=0xA000000C
REPARSE_MOUNT=0xA0000003
NAME_SURROGATE=0x20000000
CHUNK=1048576
TOKENS=('class','shader','pix','vertex','stage','texture')
PAA_TYPES={0xff01,0xff03,0xff05,0x4444,0x1555,0x8888,0x8080}
SHA_RE=re.compile(r'^[0-9a-fA-F]{64}$')
CONTRACT_FIELDS={'schema','pbo','catalog_models','catalog_entries','pins','models','build_alias','build_root','prerequisites','stage_paths','limits'}
def require(c,m):
    if not bool(c): raise ValueError(m)
def is_sha(v): return isinstance(v,str) and bool(SHA_RE.match(v))
def exact(f,n):
    r=f.read(n); require(len(r)==n,'truncated_pbo'); return r
def string(f):
    r=bytearray()
    for _ in range(4096):
        c=exact(f,1)
        if c==bytes(1): return r.decode('utf-8')
        r.extend(c)
    raise ValueError('unbounded_pbo_string')
def unsafe_raw(raw):
    if not isinstance(raw,str) or raw=='' : return True
    if raw.strip()!=raw: return True
    q=raw.replace(BSL,'/')
    if ':' in q: return True
    if q.startswith('/'): return True
    parts=q.split('/')
    if any(p in ('','.','..') for p in parts): return True
    return False
def pbo_table(f,length):
    entries,properties,seen=[],{},set()
    while True:
        name=string(f); mime,original,reserved,timestamp,size=struct.unpack('<5I',exact(f,20))
        if not name:
            if mime==0x56657273:
                while True:
                    k=string(f)
                    if not k: break
                    require(k not in properties,'duplicate_property'); properties[k]=string(f)
                continue
            require(not any((mime,original,reserved,timestamp,size)),'invalid_pbo_sentinel'); break
        require(not unsafe_raw(name),'unsafe_pbo_path')
        key=name.replace(BSL,'/').lower()
        require(key not in seen,'duplicate_pbo_path'); seen.add(key)
        entries.append(dict(name=key,mime=mime,size=size)); require(len(entries)<=100000,'pbo_entry_budget')
    off=f.tell()
    for e in entries:
        e['offset']=off; off+=e['size']; require(off<=length,'truncated_pbo_payload')
    return properties,entries
def norm(v): return str(v).replace(BSL,'/').strip('/').lower()
def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def stat_tuple(s): return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def ident_tuple(s): return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
def attrs_of(s): return int(getattr(s,'st_file_attributes',0) or 0)
def tag_of(s): return int(getattr(s,'st_reparse_tag',0) or 0)
def is_link(s):
    """True means a symlink or a blocked unapproved reparse point; not all reparse points are symlinks."""
    if stat.S_ISLNK(s.st_mode): return True
    return bool(attrs_of(s) & REPARSE)
def link_info(path,s):
    t=None; err=None
    if stat.S_ISLNK(s.st_mode) or bool(attrs_of(s) & REPARSE):
        try: t=os.readlink(path)
        except OSError as e: err=str(e)
    return dict(attrs=attrs_of(s),reparse_tag=tag_of(s),is_link=bool(is_link(s)),readlink=t,readlink_error=err,mode=int(s.st_mode))
def detect_format(name,sample):
    ext=os.path.splitext(str(name))[1].lower(); s=bytes(sample or b'')
    if s[:4]==b'ODOL': return 'ODOL'
    if s[:4]==b'MLOD': return 'MLOD'
    if s[:4]==b'\x00raP': return 'RVMAT_RAP'
    if s[:8]==bytes([137,80,78,71,13,10,26,10]): return 'PNG'
    if ext=='.paa':
        if len(s)>=2 and struct.unpack('<H',s[:2])[0] in PAA_TYPES: return 'PAA'
        return 'UNKNOWN'
    if ext=='.rvmat':
        if b'\x00' in s: return 'UNKNOWN'
        try: t=s.decode('utf-8')
        except Exception: return 'UNKNOWN'
        if any((ord(c)<32 and c not in ('\r','\n','\t')) for c in t): return 'UNKNOWN'
        return 'RVMAT_TEXT' if any(x in t.lower() for x in TOKENS) else 'UNKNOWN'
    return 'UNKNOWN'
def hash_stream(f):
    h=hashlib.sha256(); sample=bytearray(); n=0
    while True:
        b=f.read(CHUNK)
        if not b: break
        h.update(b); n+=len(b)
        if len(sample)<8192: sample.extend(b[:8192-len(sample)])
    return h.hexdigest(),bytes(sample),n
def _capture_file(path,expected=None,read_data=False,max_bytes=None):
    p=str(path); o=dict(path=p,expected_sha256=expected,status='MISSING',sha256=None,size=None,stable=False)
    try: lst=os.lstat(p)
    except FileNotFoundError: return o
    except OSError: o['status']='UNREADABLE'; return o
    if is_link(lst): o['status']='UNRESOLVED_LINK'; o.update(link_info(p,lst)); return o
    try: before=os.stat(p)
    except FileNotFoundError: return o
    except OSError: o['status']='UNREADABLE'; return o
    if not stat.S_ISREG(before.st_mode): o['status']='UNREADABLE'; return o
    data=bytearray() if read_data else None; sample=bytearray(); h=hashlib.sha256(); n=0
    try:
        with open(p,'rb') as f:
            fb=os.fstat(f.fileno())
            while True:
                b=f.read(CHUNK)
                if not b: break
                h.update(b); n+=len(b)
                if max_bytes is not None and n>int(max_bytes): raise ValueError('metadata_too_large')
                if len(sample)<8192: sample.extend(b[:8192-len(sample)])
                if data is not None: data.extend(b)
            fa=os.fstat(f.fileno()); path_after=os.stat(p); lst_after=os.lstat(p)
    except OSError: o['status']='UNREADABLE'; return o
    digest=h.hexdigest()
    stable=(stat_tuple(fb)==stat_tuple(fa) and ident_tuple(before)==ident_tuple(fb) and ident_tuple(path_after)==ident_tuple(fa) and ident_tuple(lst_after)==ident_tuple(fa) and not is_link(lst_after))
    o.update(sha256=digest,size=n,stable=bool(stable),before=stat_tuple(fb),after=stat_tuple(fa),path_after=list(ident_tuple(path_after)),sample=bytes(sample))
    if data is not None: o['_data']=bytes(data)
    if not stable: o['status']='SOURCE_UNSTABLE'
    elif expected is None: o['status']='UNPINNED'
    else: o['status']='MATCH' if digest==str(expected).lower() else 'DIFFER'
    return o
def observe_file(path,expected=None,read_data=False,max_bytes=None): return _capture_file(path,expected,read_data,max_bytes)
def stage_info(path):
    p=str(path)
    try: s=os.lstat(p)
    except FileNotFoundError: return dict(path=p,status='MISSING',exists=False)
    except OSError as e: return dict(path=p,status='UNREADABLE',exists=False,error=str(e))
    o=dict(path=p,status='LINK_OBSERVED' if is_link(s) else 'OBSERVED',exists=True); o.update(link_info(p,s)); o['size']=s.st_size; return o
def query_dos_device(alias):
    dev=str(alias).replace(BSL,'/').rstrip('/')
    if not re.fullmatch(r'[A-Za-z]:',dev): raise ValueError('bad_build_alias')
    if os.name!='nt': raise OSError('query_dos_device_windows_only')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True); q=kernel.QueryDosDeviceW
    q.argtypes=[wintypes.LPCWSTR,wintypes.LPWSTR,wintypes.DWORD]; q.restype=wintypes.DWORD
    buf=ctypes.create_unicode_buffer(32768); n=q(dev,buf,len(buf))
    if not n: raise ctypes.WinError(ctypes.get_last_error())
    return buf.value
def win_norm(p): return ntpath.normcase(ntpath.normpath(str(p).replace('/',BSL)))
def expected_mapping(build_root): return BSL+'??'+BSL+ntpath.normpath(str(build_root).replace('/',BSL))
def reparse_ancestor(root):
    drive,rest=ntpath.splitdrive(ntpath.normpath(str(root).replace('/',BSL)))
    if not drive: return None
    cur=drive+BSL; paths=[cur]
    for part in [x for x in rest.split(BSL) if x]:
        cur=cur.rstrip(BSL)+BSL+part; paths.append(cur)
    for p in paths:
        try: s=os.lstat(p)
        except OSError: continue
        if is_link(s): return p
    return None
def inspect_build(root,normalized,trusted=True):
    base=str(root); rel=normalized; o=dict(path=os.path.join(base,*rel.split('/')),normalized=rel,status='MISSING',sha256=None,format='UNKNOWN',prefix16=None,size=None,stable=False)
    if not trusted: o['status']='UNRESOLVED_LINK'; o['reason']='build_alias_unresolved'; return o
    comps=[]; cur=base
    try: rs=os.lstat(cur)
    except FileNotFoundError: return o
    except OSError: o['status']='UNREADABLE'; return o
    if is_link(rs): o['status']='UNRESOLVED_LINK'; o.update(link_info(cur,rs)); return o
    comps.append((cur,ident_tuple(rs)))
    s=rs
    for part in rel.split('/'):
        cur=os.path.join(cur,part)
        try: s=os.lstat(cur)
        except FileNotFoundError: o['missing_component']=cur; return o
        except OSError: o['status']='UNREADABLE'; return o
        if is_link(s): o['status']='UNRESOLVED_LINK'; o['link_component']=cur; o.update(link_info(cur,s)); return o
        comps.append((cur,ident_tuple(s)))
    if not stat.S_ISREG(s.st_mode): o['status']='UNREADABLE'; return o
    cand=_capture_file(cur,None)
    for cp,ident0 in comps:
        try: cs=os.lstat(cp)
        except OSError: cand['status']='SOURCE_UNSTABLE'; cand['stable']=False; break
        if is_link(cs) or ident_tuple(cs)!=ident0: cand['status']='SOURCE_UNSTABLE'; cand['stable']=False; break
    if cand.get('status') in ('MISSING','UNREADABLE','UNRESOLVED_LINK','SOURCE_UNSTABLE'): o['status']=cand.get('status'); o['stable']=bool(cand.get('stable')); return o
    sample=cand.get('sample') or b''
    o.update(status='OK' if cand.get('stable') else 'SOURCE_UNSTABLE',sha256=cand.get('sha256'),size=cand.get('size'),stable=bool(cand.get('stable')),format=detect_format(rel,sample),prefix16=sample[:16].hex(),sample_prefix16=sample[:16].hex())
    return o
def classify(expected_sha,expected_format,cand):
    if cand.get('status')!='OK': return cand.get('status') or 'UNREADABLE'
    if expected_sha and cand.get('sha256')==str(expected_sha).lower(): return 'MATCH'
    ef=expected_format or 'UNKNOWN'; cf=cand.get('format') or 'UNKNOWN'
    if ef!='UNKNOWN' and cf!='UNKNOWN': return 'DIFFER' if ef==cf else 'FORMAT_DIFFERS'
    return 'UNDETERMINED_FORMAT'
def hash_range(f,e):
    f.seek(e['offset']); h=hashlib.sha256(); sample=bytearray(); left=e['size']
    while left>0:
        b=f.read(min(CHUNK,left)); require(bool(b),'truncated_pbo'); h.update(b); left-=len(b)
        if len(sample)<8192: sample.extend(b[:8192-len(sample)])
    return h.hexdigest(),bytes(sample)
def manifest_sha256(m): return sha_bytes(m if isinstance(m,(bytes,bytearray)) else canon(m))
def verify_manifest(report,manifest,expected_manifest_sha):
    try:
        rb=bytes(report) if isinstance(report,(bytes,bytearray)) else canon(report); mb=bytes(manifest) if isinstance(manifest,(bytes,bytearray)) else canon(manifest)
        if sha_bytes(mb)!=str(expected_manifest_sha).lower(): return False
        if not isinstance(manifest,dict): return False
        if manifest.get('report_sha256')!=sha_bytes(rb): return False
        if isinstance(report,dict):
            if manifest.get('contract_sha256')!=report.get('contract_sha256'): return False
            if manifest.get('tool_sha256')!=report.get('tool_sha256'): return False
        return True
    except Exception: return False
def run_discovery(contract_path,contract_sha256,out_dir):
    out=Path(out_dir)
    if out.exists(): raise ValueError('output_exists')
    require(is_sha(contract_sha256),'bad_contract_sha256')
    cp=str(contract_path); cobs=observe_file(cp,contract_sha256,read_data=True)
    if cobs.get('status')!='MATCH': raise ValueError('contract_not_pinned_match:'+str(cobs.get('status')))
    try: contract=json.loads(cobs['_data'].decode('utf-8'))
    except Exception: raise ValueError('bad_contract_json')
    require(isinstance(contract,dict) and set(contract)==CONTRACT_FIELDS,'bad_contract_schema_fields')
    require(contract.get('schema')=='road-build-discovery.v1','bad_contract_schema')
    pbo_c=contract.get('pbo'); pins=contract.get('pins'); models=contract.get('models'); limits=contract.get('limits')
    require(isinstance(pbo_c,dict) and set(pbo_c)=={'path','sha256','bytes','prefix'},'bad_pbo_fields')
    require(isinstance(pbo_c.get('path'),str) and pbo_c.get('path'),'bad_pbo_path'); require(is_sha(pbo_c.get('sha256')),'bad_pbo_sha'); require(isinstance(pbo_c.get('bytes'),int) and pbo_c.get('bytes')>0,'bad_pbo_bytes'); require(isinstance(pbo_c.get('prefix'),str) and pbo_c.get('prefix') and not unsafe_raw(pbo_c.get('prefix')),'bad_pbo_prefix')
    require(isinstance(contract.get('catalog_models'),str) and contract.get('catalog_models'),'bad_catalog_models'); require(isinstance(contract.get('catalog_entries'),str) and contract.get('catalog_entries'),'bad_catalog_entries')
    require(isinstance(pins,dict) and pins,'bad_pins'); require(all(isinstance(k,str) and k and is_sha(v) for k,v in pins.items()),'bad_pin_values')
    require(contract.get('catalog_models') in pins and contract.get('catalog_entries') in pins,'missing_catalog_pin')
    require(isinstance(contract.get('build_alias'),str) and contract.get('build_alias'),'bad_build_alias'); require(isinstance(contract.get('build_root'),str) and contract.get('build_root'),'bad_build_root')
    require(isinstance(contract.get('prerequisites'),list),'bad_prerequisites')
    for it in contract.get('prerequisites'):
        require(isinstance(it,dict) and set(it)=={'path','sha256'} and isinstance(it.get('path'),str) and it.get('path') and (it.get('sha256') is None or is_sha(it.get('sha256'))),'bad_prerequisite')
    require(isinstance(contract.get('stage_paths'),list) and all(isinstance(x,str) and x for x in contract.get('stage_paths')),'bad_stage_paths')
    require(isinstance(limits,dict) and set(limits)=={'seconds','bytes'} and isinstance(limits.get('seconds'),int) and isinstance(limits.get('bytes'),int) and 0<limits.get('seconds')<=60 and 0<limits.get('bytes')<=1073741824,'bad_limits')
    require(isinstance(models,list) and len(models)==3,'models_exactly_three')
    prefix_norm=norm(pbo_c.get('prefix'))
    seenm=set()
    for m in models:
        require(isinstance(m,dict) and set(m)=={'name','entry'} and isinstance(m.get('name'),str) and isinstance(m.get('entry'),str),'bad_model_fields')
        require(not unsafe_raw(m.get('name')) and not unsafe_raw(m.get('entry')),'unsafe_model_path')
        require(norm(m.get('name'))==prefix_norm+'/'+norm(m.get('entry')),'model_name_prefix_entry_mismatch')
        k=norm(m.get('entry')); require(k not in seenm,'duplicate_contract_model'); seenm.add(k)
    tool_path=Path(__file__); tool_bytes=tool_path.read_bytes(); tool_sha=sha_bytes(tool_bytes)
    pin_obs=[]
    for path in sorted(pins,key=lambda x: norm(x)):
        o=observe_file(path,pins[path]); pin_obs.append(o)
        if o.get('status')!='MATCH': raise ValueError('pin_not_match:'+str(path)+':'+str(o.get('status')))
    prereq=[]
    for it in contract.get('prerequisites'):
        o=observe_file(it.get('path'),it.get('sha256')); prereq.append(o)
    stages=[stage_info(p) for p in contract.get('stage_paths')]
    max_meta=limits.get('bytes')
    cm_obs=observe_file(contract.get('catalog_models'),pins.get(contract.get('catalog_models')),read_data=True,max_bytes=max_meta)
    if cm_obs.get('status')!='MATCH': raise ValueError('catalog_models_not_match:'+str(cm_obs.get('status')))
    ce_obs=observe_file(contract.get('catalog_entries'),pins.get(contract.get('catalog_entries')),read_data=True,max_bytes=max_meta)
    if ce_obs.get('status')!='MATCH': raise ValueError('catalog_entries_not_match:'+str(ce_obs.get('status')))
    catalog=[]
    try:
        for line in cm_obs['_data'].decode('utf-8').splitlines():
            if line.strip(): catalog.append(json.loads(line))
    except Exception: raise ValueError('bad_catalog_models_json')
    try: entries_cat=json.loads(ce_obs['_data'].decode('utf-8'))
    except Exception: raise ValueError('bad_catalog_entries_json')
    require(isinstance(entries_cat,list),'entries_not_list')
    cat_by={}
    for row in catalog:
        require(isinstance(row,dict) and isinstance(row.get('name'),str) and row.get('name') and not unsafe_raw(row.get('name')),'bad_catalog_row')
        k=norm(row['name']); require(k not in cat_by,'duplicate_catalog_model'); cat_by[k]=row
    entry_by={}
    for e in entries_cat:
        require(isinstance(e,dict) and {'name','normalized_name','size','mime','sha256'}<=set(e)<={'name','normalized_name','category','size','mime','sha256'} and ('category' not in e or isinstance(e.get('category'),str)),'bad_entry_fields')
        require(isinstance(e.get('name'),str) and isinstance(e.get('normalized_name'),str) and not unsafe_raw(e.get('name')) and not unsafe_raw(e.get('normalized_name')),'unsafe_entry_path')
        require(isinstance(e.get('size'),int) and e.get('size')>=0 and isinstance(e.get('mime'),int) and e.get('mime')>=0 and is_sha(e.get('sha256')),'bad_entry_values')
        require(norm(e.get('normalized_name'))==norm(e.get('name')),'entry_normalized_mismatch')
        nn=norm(e['normalized_name']); require(nn not in entry_by,'duplicate_entry'); entry_by[nn]=e
    alias=contract.get('build_alias'); build_root=contract.get('build_root'); canonical_root=os.path.normpath(str(build_root))
    raw_alias_info=stage_info(str(alias))
    raw_alias_link=bool(raw_alias_info.get('is_link'))
    mapping_raw=None; mapping_error=None
    try: mapping_raw=query_dos_device(alias)
    except Exception as e: mapping_error=str(e)
    mapping_ok=bool(mapping_raw is not None and win_norm(mapping_raw)==win_norm(expected_mapping(build_root)))
    bad_ancestor=reparse_ancestor(canonical_root)
    trusted=bool(mapping_ok and not raw_alias_link and bad_ancestor is None)
    comparisons=[]; ref_reports=[]; model_reports=[]
    def add(kind,name,status,detail): comparisons.append(dict(kind=kind,name=name,status=status,detail=detail))
    refs={}; model_rows={}; model_lod_status={}
    for m in models:
        en=norm(m['entry']); row=cat_by.get(en); model_rows[en]=row
        if not row: model_lod_status[en]='MISSING'; continue
        valid=True
        meas=row.get('measurement') if isinstance(row,dict) else None
        if not isinstance(row.get('sha256'),str) or not row.get('sha256') or not isinstance(row.get('status'),str) or not row.get('status'): valid=False
        if not isinstance(meas,dict) or not isinstance(meas.get('lods'),list) or not meas.get('lods'): valid=False; model_lod_status[en]='UNREADABLE'
        else:
            for lod in meas.get('lods'):
                if not isinstance(lod,dict) or not all(k in lod for k in ('index','resolution','role','sections','textures','materials')) or not isinstance(lod.get('sections'),list) or not isinstance(lod.get('textures'),list) or not isinstance(lod.get('materials'),list): valid=False; continue
                vals=[]; vals.extend(lod.get('textures') or []); vals.extend(lod.get('materials') or [])
                for sec in lod.get('sections') or []:
                    if not isinstance(sec,dict) or 'material_raw' not in sec or 'texture_raw' not in sec: valid=False; continue
                    vals.append(sec.get('material_raw')); vals.append(sec.get('texture_raw'))
                for raw in vals:
                    if raw is None or str(raw)=='' : continue
                    raw_s=str(raw); n=norm(raw_s); rec=refs.setdefault(n,dict(normalized=n,raws=[],models=[],lod_indexes=[]))
                    if raw_s not in rec['raws']: rec['raws'].append(raw_s)
                    if m['name'] not in rec['models']: rec['models'].append(m['name'])
                    if lod.get('index') not in rec['lod_indexes']: rec['lod_indexes'].append(lod.get('index'))
            model_lod_status[en]='MATCH' if valid else 'UNREADABLE'
    selected=set(norm(m['entry']) for m in models)
    for n in list(refs):
        if not any(unsafe_raw(r) for r in refs[n]['raws']) and (n==prefix_norm or n.startswith(prefix_norm+'/')): selected.add(n[len(prefix_norm)+1:])
    pbo_path=pbo_c.get('path'); pbo_info=dict(path=pbo_path,expected_sha256=pbo_c.get('sha256'),expected_bytes=pbo_c.get('bytes'),prefix=pbo_c.get('prefix'),status='MISSING',sha256=None,stable=False,properties={},prefix_status='UNKNOWN',global_status='UNKNOWN',size_status='UNKNOWN',size=None)
    pbo_ranges={}
    if pbo_path and os.path.exists(str(pbo_path)):
        try:
            with open(str(pbo_path),'rb') as f:
                fb=os.fstat(f.fileno()); length=fb.st_size; h1,_,_=hash_stream(f)
                if int(pbo_c.get('bytes'))!=length: raise ValueError('pbo_size_mismatch')
                if h1!=str(pbo_c.get('sha256')).lower(): raise ValueError('pbo_hash_mismatch')
                f.seek(0); props,entries=pbo_table(f,length); by={e['name']:e for e in entries}
                for name in sorted(selected):
                    e=by.get(name)
                    if not e: continue
                    if e['mime']!=0: pbo_ranges[name]=dict(entry=e,status='UNSUPPORTED_COMPRESSION',sha256=None,format='UNKNOWN',sample=b'')
                    else:
                        rh,sample=hash_range(f,e); pbo_ranges[name]=dict(entry=e,status='OK',sha256=rh,format=detect_format(name,sample),sample=sample)
                f.seek(0); h2,_,_=hash_stream(f); fa=os.fstat(f.fileno()); path_after=os.stat(str(pbo_path))
            pref=None
            for k,v in props.items():
                if k.lower()=='prefix': pref=v
            stable=bool(stat_tuple(fb)==stat_tuple(fa) and ident_tuple(path_after)==ident_tuple(fa) and h1==h2)
            if not stable: raise ValueError('pbo_unstable')
            pbo_info.update(status='OK',sha256=h1,sha256_after=h2,size=length,stable=True,properties=props,prefix_value=pref,prefix_status='MATCH' if pref==pbo_c.get('prefix') else 'PREFIX_MISMATCH',entry_count=len(entries),global_status='MATCH',size_status='MATCH')
        except OSError: pbo_info['status']='UNREADABLE'
    for o in pin_obs: add('pin',o['path'],'MATCH',o.get('sha256'))
    for o in prereq: add('prerequisite',o['path'],o.get('status'),o.get('sha256'))
    add('catalog_models',str(contract.get('catalog_models')),'MATCH',cm_obs.get('sha256')); add('catalog_entries',str(contract.get('catalog_entries')),'MATCH',ce_obs.get('sha256'))
    if trusted: add('build_alias',str(alias),'MATCH',mapping_raw)
    else: add('build_alias',str(alias),'UNRESOLVED_LINK',mapping_raw or mapping_error or bad_ancestor or canonical_root)
    if pbo_info['status']!='OK': add('pbo',str(pbo_path),pbo_info['status'],None)
    else:
        add('pbo_prefix',str(pbo_c.get('prefix')),pbo_info['prefix_status'],pbo_info.get('prefix_value')); add('pbo_global',str(pbo_path),'MATCH',pbo_info.get('sha256')); add('pbo_size',str(pbo_path),'MATCH',pbo_info.get('size')); add('pbo_stability',str(pbo_path),'MATCH',None)
    for m in models:
        en=norm(m['entry']); row=model_rows.get(en); full=norm(m['name']); mr=dict(model=m['name'],entry=m['entry'],catalog_status='MISSING',pbo_status='MISSING',build_status='MISSING',catalog_sha256=None)
        if not row: add('model_catalog',m['name'],'MISSING',None); add('model_lods',m['name'],'MISSING',en); model_reports.append(mr); continue
        mr['catalog_sha256']=row.get('sha256'); mr['catalog_status']=row.get('status') or 'UNKNOWN'
        add('model_catalog',m['name'],'MATCH' if row.get('status')=='READ_STRICT' and is_sha(row.get('sha256')) else 'UNREADABLE',row.get('status'))
        add('model_lods',m['name'],model_lod_status.get(en,'UNREADABLE'),en)
        ce=entry_by.get(en); pr=pbo_ranges.get(en); exp_fmt=pr.get('format') if pr else 'UNKNOWN'
        if ce is None: add('model_entry_catalog',m['name'],'MISSING',en)
        elif pbo_info.get('status')=='OK' and en not in pbo_ranges: add('model_pbo',m['name'],'MISSING',en); mr['pbo_status']='MISSING'
        elif pr is None: add('model_pbo',m['name'],pbo_info.get('status'),en); mr['pbo_status']=pbo_info.get('status')
        elif pr.get('status')=='UNSUPPORTED_COMPRESSION': add('model_pbo',m['name'],'UNSUPPORTED_COMPRESSION',en); mr['pbo_status']='UNSUPPORTED_COMPRESSION'
        else:
            ok=(ce.get('sha256')==pr.get('sha256') and int(ce.get('size'))==int(pr['entry']['size']) and int(ce.get('mime'))==int(pr['entry']['mime']) and row.get('sha256')==pr.get('sha256'))
            st='MATCH' if ok else 'DIFFER'; add('model_pbo',m['name'],st,pr.get('sha256')); mr['pbo_status']=st; mr['pbo_sha256']=pr.get('sha256')
        cand=inspect_build(canonical_root,full,trusted); bst=classify(row.get('sha256'),exp_fmt,cand); mr['build']=cand; mr['build_status']=bst; add('model_build',m['name'],bst,cand.get('sha256')); model_reports.append(mr)
    for n in sorted(refs):
        rec=refs[n]; raw0=rec['raws'][0]; rr=dict(normalized=n,raws=rec['raws'],models=rec['models'],lod_indexes=rec['lod_indexes'],status='UNKNOWN')
        if raw0.lstrip().startswith('#'): rr['status']='PROCEDURAL'; ref_reports.append(rr); continue
        if any(unsafe_raw(r) for r in rec['raws']): rr['status']='UNSAFE_PATH'; add('reference_build',n,'UNSAFE_PATH',raw0); ref_reports.append(rr); continue
        if not (n==prefix_norm or n.startswith(prefix_norm+'/')): rr['status']='UNRESOLVED_EXTERNAL'; add('reference_build',n,'UNRESOLVED_EXTERNAL',raw0); ref_reports.append(rr); continue
        rel=n[len(prefix_norm)+1:]; ce=entry_by.get(rel); pr=pbo_ranges.get(rel); rr['entry']=rel
        if pr and pr.get('status')=='UNSUPPORTED_COMPRESSION': rr['status']='UNSUPPORTED_COMPRESSION'; add('reference_build',n,'UNSUPPORTED_COMPRESSION',raw0); ref_reports.append(rr); continue
        if pbo_info.get('status')=='OK' and pr is None: rr['status']='MISSING'; add('reference_build',n,'MISSING',raw0); ref_reports.append(rr); continue
        if pr is None: rr['status']=pbo_info.get('status'); add('reference_build',n,pbo_info.get('status'),raw0); ref_reports.append(rr); continue
        if ce is None: add('reference_entry_catalog',n,'MISSING',rel)
        else:
            cok=(ce.get('sha256')==pr.get('sha256') and int(ce.get('size'))==int(pr['entry']['size']) and int(ce.get('mime'))==int(pr['entry']['mime']))
            add('reference_pbo_catalog',n,'MATCH' if cok else 'DIFFER',pr.get('sha256'))
        exp_sha=(ce or {}).get('sha256') or pr.get('sha256'); cand=inspect_build(canonical_root,n,trusted); st=classify(exp_sha,pr.get('format'),cand); rr['status']=st; rr['build']=cand; rr['expected_sha256']=exp_sha; rr['pbo_sha256']=pr.get('sha256'); add('reference_build',n,st,cand.get('sha256')); ref_reports.append(rr)
    final_contract=observe_file(cp,contract_sha256)
    if final_contract.get('status')!='MATCH': raise ValueError('contract_changed_before_output')
    for path in sorted(pins,key=lambda x: norm(x)):
        if observe_file(path,pins[path]).get('status')!='MATCH': raise ValueError('pin_changed_before_output:'+str(path))
    for it,o0 in zip(contract.get('prerequisites'),prereq):
        o1=observe_file(it.get('path'),it.get('sha256'))
        if (o1.get('status'),o1.get('sha256'),o1.get('stable'),o1.get('size'))!=(o0.get('status'),o0.get('sha256'),o0.get('stable'),o0.get('size')): raise ValueError('prerequisite_changed_before_output:'+str(it.get('path')))
    if sha_bytes(tool_path.read_bytes())!=tool_sha: raise ValueError('tool_changed_before_output')
    mapping_end=None
    try: mapping_end=query_dos_device(alias)
    except Exception as e: mapping_end=None; mapping_error=str(e)
    if (mapping_raw is None) != (mapping_end is None): raise ValueError('build_alias_changed_before_output')
    if mapping_raw is not None and win_norm(mapping_raw)!=win_norm(mapping_end): raise ValueError('build_alias_changed_before_output')
    if trusted and not (mapping_end is not None and win_norm(mapping_end)==win_norm(expected_mapping(build_root))): raise ValueError('build_alias_changed_before_output')
    if reparse_ancestor(canonical_root) is not None: raise ValueError('build_root_reparse_before_output')
    drift={'DIFFER'}; incomplete=[c for c in comparisons if c['status']!='MATCH']
    if comparisons and all(c['status']=='MATCH' for c in comparisons): agg='INPUTS_MATCH'
    elif any(c['status'] in drift for c in comparisons): agg='INPUTS_DIFFER'
    else: agg='INCONCLUSIVE_DISCOVERY'
    sources_stable=bool(all(o.get('stable') for o in pin_obs) and all(o.get('stable') for o in prereq) and cm_obs.get('stable') and ce_obs.get('stable') and (pbo_info.get('stable') if pbo_info.get('status')=='OK' else False))
    clean=lambda o: {k:v for k,v in o.items() if not k.startswith('_') and k!='sample'}
    report=dict(schema='road-build-discovery.v1.report',status=agg,aggregate=agg,build_ready=False,pivot='UNKNOWN',width='UNKNOWN',accesses='UNKNOWN',unknowns=dict(pivot='UNKNOWN',width='UNKNOWN',accesses='UNKNOWN'),contract_sha256=str(contract_sha256).lower(),tool_sha256=tool_sha,sources_stable=sources_stable,reference_count=len(refs),build_alias=dict(alias=alias,build_root=build_root,canonical_root=canonical_root,mapping_raw=mapping_raw,mapping_expected=expected_mapping(build_root),mapping_ok=mapping_ok,mapping_error=mapping_error,raw_alias=raw_alias_info,reparse_ancestor=bad_ancestor,trusted=trusted),pbo={k:v for k,v in pbo_info.items() if k!='entries'},pins=[clean(o) for o in pin_obs],prerequisites=[clean(o) for o in prereq],stage_paths=stages,catalog_models=clean(cm_obs),catalog_entries_source=clean(ce_obs),models=model_reports,references=ref_reports,comparisons=comparisons,incomplete_coverage=incomplete,limits=limits,limitations=['discovery_only_not_build_ready','pivot_unknown','width_unknown','accesses_unknown','no_geometry_redecode','no_transitive_rvmat_closure','manifest_integrity_is_not_semantic_acceptance','format_header_evidence_is_not_full_syntax_proof','pbo_unsupported_compression_is_inconclusive'])
    out.mkdir(parents=True)
    try:
        rb=canon(report); (out/'report.json').write_bytes(rb)
        manifest=dict(schema='road-build-discovery.v1.manifest',report_sha256=sha_bytes(rb),contract_sha256=report['contract_sha256'],tool_sha256=tool_sha,integrity_scope='manifest_hashes_only_not_semantic_acceptance')
        (out/'manifest.json').write_bytes(canon(manifest))
    except Exception:
        for fn in ('report.json','manifest.json'):
            try: (out/fn).unlink()
            except OSError: pass
        try: out.rmdir()
        except OSError: pass
        raise
    return report
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--contract',required=True); ap.add_argument('--contract-sha256',required=True); ap.add_argument('--out',required=True); a=ap.parse_args(argv)
    r=run_discovery(a.contract,a.contract_sha256,a.out); print(json.dumps(dict(status=r['status'],build_ready=False),sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
