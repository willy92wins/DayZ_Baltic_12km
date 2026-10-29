# RoadB4A read-only build discovery. Stdlib only.
# Attribution: exact/string/pbo_table adapted from tools/quality/deployed_surface_inventory_ev112.py
# pinned helper sha256 b7a17598c68294622b4bf2ba8bb36afe74d91b24876b8451e10ab0425651bcb6
import argparse
import hashlib
import json
import os
import stat
import struct
from pathlib import Path
BUILD_ALIAS_MAP={}
REPARSE=0x400
CHUNK=1048576
TOKENS=('class','shader','pix','vertex','stage','texture')
PAA_TYPES={0xff01,0xff03,0xff05,0x4444,0x1555,0x8888,0x8080}
def require(c,m):
    if not bool(c): raise ValueError(m)
def exact(f,n):
    r=f.read(n); require(len(r)==n,'truncated_pbo'); return r
def string(f):
    r=bytearray()
    for _ in range(4096):
        c=exact(f,1)
        if c==bytes(1): return r.decode('utf-8')
        r.extend(c)
    raise ValueError('unbounded_pbo_string')
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
        key=name.replace(chr(92),'/').lower()
        require(not key.startswith('/') and ':' not in key and all(p not in ('','.','..') for p in key.split('/')),'unsafe_pbo_path')
        require(key not in seen,'duplicate_pbo_path'); seen.add(key)
        entries.append(dict(name=key,mime=mime,size=size)); require(len(entries)<=100000,'pbo_entry_budget')
    off=f.tell()
    for e in entries:
        e['offset']=off; off+=e['size']; require(off<=length,'truncated_pbo_payload')
    return properties,entries
def norm(v): return str(v).replace(chr(92),'/').strip('/').lower()
def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def stat_tuple(s): return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def attrs_of(s): return int(getattr(s,'st_file_attributes',0) or 0)
def tag_of(s): return int(getattr(s,'st_reparse_tag',0) or 0)
def is_link(s): return stat.S_ISLNK(s.st_mode) or bool(attrs_of(s)&REPARSE)
def link_info(path,s):
    t=None
    if stat.S_ISLNK(s.st_mode):
        try: t=os.readlink(path)
        except OSError: t=None
    return dict(attrs=attrs_of(s),reparse_tag=tag_of(s),is_link=bool(is_link(s)),readlink=t,mode=int(s.st_mode))
def detect_format(name,sample):
    ext=os.path.splitext(str(name))[1].lower(); s=bytes(sample or b'')
    if s[:4]==b'ODOL': return 'ODOL'
    if s[:4]==b'MLOD': return 'MLOD'
    if s[:4]==b'rap'+bytes(1): return 'RVMAT_RAP'
    if s[:8]==bytes([137,80,78,71,13,10,26,10]): return 'PNG'
    if ext=='.paa':
        if len(s)>=2 and struct.unpack('<H',s[:2])[0] in PAA_TYPES: return 'PAA'
        return 'UNKNOWN'
    if ext=='.rvmat':
        try: t=s.decode('utf-8')
        except Exception: return 'UNKNOWN'
        return 'RVMAT_TEXT' if any(x in t.lower() for x in TOKENS) else 'UNKNOWN'
    return 'UNKNOWN'
def hash_stream(f,total=None):
    h=hashlib.sha256(); sample=bytearray(); n=0
    while True:
        want=CHUNK if total is None else min(CHUNK,total-n)
        if want<=0: break
        b=f.read(want)
        if not b: break
        h.update(b); n+=len(b)
        if len(sample)<8192: sample.extend(b[:8192-len(sample)])
    return h.hexdigest(),bytes(sample),n
def observe_file(path,expected=None,read_data=False):
    p=str(path); o=dict(path=p,expected_sha256=expected,status='MISSING',sha256=None,size=None,stable=False)
    try: before=os.stat(p)
    except FileNotFoundError: return o
    except OSError: o['status']='UNREADABLE'; return o
    if not stat.S_ISREG(before.st_mode): o['status']='UNREADABLE'; return o
    try:
        with open(p,'rb') as f:
            fb=stat_tuple(os.fstat(f.fileno())); h1,sample,n=hash_stream(f); f.seek(0); h2,_,_=hash_stream(f); fa=stat_tuple(os.fstat(f.fileno()))
            data=None
            if read_data:
                f.seek(0); data=f.read()
    except OSError: o['status']='UNREADABLE'; return o
    o.update(sha256=h1,size=n,stable=(fb==fa and stat_tuple(before)==fa and h1==h2),before=fb,after=fa,sample_format=None)
    if data is not None: o['_data']=data
    if not o['stable']: o['status']='SOURCE_UNSTABLE'
    elif expected is None: o['status']='UNPINNED'
    else: o['status']='MATCH' if h1==str(expected).lower() else 'DIFFER'
    return o
def stage_info(path):
    p=str(path)
    try: s=os.lstat(p)
    except FileNotFoundError: return dict(path=p,status='MISSING',exists=False)
    except OSError: return dict(path=p,status='UNREADABLE',exists=False)
    o=dict(path=p,status='LINK_OBSERVED' if is_link(s) else 'OBSERVED',exists=True); o.update(link_info(p,s)); o['size']=s.st_size; return o
def inspect_build(root,normalized,trusted=True):
    base=str(root); rel=normalized; o=dict(path=os.path.join(base,*rel.split('/')),normalized=rel,status='MISSING',sha256=None,format='UNKNOWN',prefix16=None,size=None,stable=False)
    if not trusted: o['status']='UNRESOLVED_LINK'; o['reason']='build_alias_mismatch'; return o
    try: rs=os.lstat(base)
    except FileNotFoundError: return o
    except OSError: o['status']='UNREADABLE'; return o
    if is_link(rs): o['status']='UNRESOLVED_LINK'; o.update(link_info(base,rs)); return o
    cur=base
    for part in rel.split('/'):
        cur=os.path.join(cur,part)
        try: s=os.lstat(cur)
        except FileNotFoundError: o['missing_component']=cur; return o
        except OSError: o['status']='UNREADABLE'; return o
        if is_link(s): o['status']='UNRESOLVED_LINK'; o['link_component']=cur; o.update(link_info(cur,s)); return o
    if not stat.S_ISREG(s.st_mode): o['status']='UNREADABLE'; return o
    try:
        with open(cur,'rb') as f:
            fb=stat_tuple(os.fstat(f.fileno())); h1,sample,n=hash_stream(f); f.seek(0); h2,_,_=hash_stream(f); fa=stat_tuple(os.fstat(f.fileno()))
    except OSError: o['status']='UNREADABLE'; return o
    o.update(status='OK',sha256=h1,size=n,stable=(fb==fa and h1==h2),format=detect_format(rel,sample),prefix16=sample[:16].hex(),sample_prefix16=sample[:16].hex())
    if not o['stable']: o['status']='SOURCE_UNSTABLE'
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
def _unsafe_raw(raw):
    r=str(raw).strip(); q=r.replace(chr(92),'/')
    if q.startswith('/') or q.startswith(chr(92)): return True
    if len(q)>=2 and q[1]==':' : return True
    return any(p in ('.','..') for p in q.split('/') if p=='..' or p=='.' and False) or '..' in q.split('/')
def run_discovery(contract_path,contract_sha256,out_dir,alias_map=None):
    out=Path(out_dir)
    if out.exists(): raise ValueError('output_exists')
    cp=str(contract_path)
    try:
        with open(cp,'rb') as f:
            fb=stat_tuple(os.fstat(f.fileno())); ch,_,_=hash_stream(f)
            if ch!=str(contract_sha256).lower(): raise ValueError('contract_hash_mismatch')
            fa0=stat_tuple(os.fstat(f.fileno())); f.seek(0); contract_bytes=f.read(); fa=stat_tuple(os.fstat(f.fileno()))
    except FileNotFoundError: raise ValueError('contract_missing')
    require(fb==fa0==fa,'contract_unstable')
    contract=json.loads(contract_bytes.decode('utf-8'))
    require(contract.get('schema')=='road-build-discovery.v1','bad_contract_schema')
    models=contract.get('models') or []; pins=contract.get('pins') or {}; pbo_c=contract.get('pbo') or {}
    require(isinstance(models,list) and len(models)==3,'models_exactly_three')
    require(isinstance(pins,dict),'bad_pins')
    entries_model=[]; seenm=set()
    for m in models:
        require(isinstance(m,dict) and m.get('name') and m.get('entry'),'bad_model')
        k=norm(m['entry']); require(k not in seenm,'duplicate_contract_model'); seenm.add(k); entries_model.append(m)
    tool_path=Path(__file__); tool_sha=sha_bytes(tool_path.read_bytes())
    pin_obs=[]
    for path in sorted(pins,key=lambda x: norm(x)): pin_obs.append(observe_file(path,pins[path]))
    prereq=[]
    for it in contract.get('prerequisites') or []:
        sha=it.get('sha256') if isinstance(it,dict) else None; path=it.get('path') if isinstance(it,dict) else None
        if sha is None:
            o=observe_file(path,None); o['status']='UNPINNED'; o['pin_status']='UNPINNED/MISSING'; prereq.append(o)
        else: prereq.append(observe_file(path,sha))
    stages=[stage_info(p) for p in contract.get('stage_paths') or []]
    amap=alias_map if alias_map is not None else BUILD_ALIAS_MAP
    alias=contract.get('build_alias') or ''; build_root=contract.get('build_root') or ''
    canonical_raw=amap.get(alias) or amap.get(str(alias).rstrip('/')) or amap.get(str(alias).rstrip(chr(92))) or os.path.realpath(str(alias))
    canonical_root=os.path.normpath(str(canonical_raw)); expected_root=os.path.normpath(str(build_root))
    alias_ok=os.path.normcase(canonical_root)==os.path.normcase(expected_root)
    try: root_st=os.lstat(canonical_root); root_link=bool(is_link(root_st)); root_info=link_info(canonical_root,root_st)
    except OSError: root_link=False; root_info=dict(attrs=0,reparse_tag=0,is_link=False,readlink=None)
    trusted=bool(alias_ok and not root_link)
    cat_models_path=contract.get('catalog_models'); cat_entries_path=contract.get('catalog_entries')
    cm_obs=observe_file(cat_models_path,pins.get(cat_models_path),read_data=True) if cat_models_path else dict(status='MISSING',sha256=None)
    ce_obs=observe_file(cat_entries_path,pins.get(cat_entries_path),read_data=True) if cat_entries_path else dict(status='MISSING',sha256=None)
    catalog=[]
    if cm_obs.get('_data') is not None:
        for line in cm_obs['_data'].decode('utf-8').splitlines():
            if line.strip(): catalog.append(json.loads(line))
    entries_cat=[]
    if ce_obs.get('_data') is not None: entries_cat=json.loads(ce_obs['_data'].decode('utf-8'))
    require(isinstance(entries_cat,list),'entries_not_list')
    cat_by={}; 
    for row in catalog:
        require(isinstance(row,dict) and row.get('name'),'bad_catalog_row'); k=norm(row['name']); require(k not in cat_by,'duplicate_catalog_model'); cat_by[k]=row
    entry_by={}
    for e in entries_cat:
        require(isinstance(e,dict) and e.get('name') and e.get('normalized_name') and 'size' in e and 'mime' in e and e.get('sha256'),'bad_entry')
        nn=norm(e['normalized_name']); require(nn==norm(e['name']) or True,'entry_norm')
        require(not _unsafe_raw(e['normalized_name']),'unsafe_entry_path'); require(nn not in entry_by,'duplicate_entry'); entry_by[nn]=e
    def find_catalog(m):
        en=norm(m['entry']); full=norm(m['name'])
        if en in cat_by: return cat_by[en]
        for k,v in cat_by.items():
            if full.endswith('/'+k) or k==full: return v
        return None
    selected=set(norm(m['entry']) for m in models)
    refs={}
    model_rows={}
    for m in models:
        row=find_catalog(m); model_rows[norm(m['entry'])]=row
        if not row: continue
        for lod in ((row.get('measurement') or {}).get('lods') or []):
            vals=[]
            for key in ('textures','materials'):
                v=lod.get(key) or []; vals.extend(v if isinstance(v,list) else [v])
            for sec in lod.get('sections') or []:
                for key in ('material_raw','texture_raw'):
                    if key in sec: vals.append(sec.get(key))
            for raw in vals:
                if raw is None or str(raw)=='' : continue
                raw_s=str(raw); n=norm(raw_s)
                rec=refs.setdefault(n,dict(normalized=n,raws=[],models=[],lod_indexes=[]))
                if raw_s not in rec['raws']: rec['raws'].append(raw_s)
                if m['name'] not in rec['models']: rec['models'].append(m['name'])
                if lod.get('index') not in rec['lod_indexes']: rec['lod_indexes'].append(lod.get('index'))
    prefix_norm=norm(pbo_c.get('prefix') or '')
    for n in list(refs):
        if n==prefix_norm or n.startswith(prefix_norm+'/'): selected.add(n[len(prefix_norm)+1:])
    pbo_path=pbo_c.get('path'); pbo_info=dict(path=pbo_path,expected_sha256=pbo_c.get('sha256'),expected_bytes=pbo_c.get('bytes'),prefix=pbo_c.get('prefix'),status='MISSING',sha256=None,stable=False,properties={},prefix_status='UNKNOWN',entries={})
    pbo_ranges={}
    if pbo_path and os.path.exists(str(pbo_path)):
        with open(str(pbo_path),'rb') as f:
            before=stat_tuple(os.fstat(f.fileno())); length=before[2]; h1,_,_=hash_stream(f)
            f.seek(0); props,entries=pbo_table(f,length); by={e['name']:e for e in entries}
            for name in sorted(selected):
                e=by.get(name)
                if not e: continue
                if e['mime']!=0: pbo_ranges[name]=dict(entry=e,status='UNSUPPORTED_COMPRESSION',sha256=None,format='UNKNOWN',sample=b'')
                else:
                    rh,sample=hash_range(f,e); pbo_ranges[name]=dict(entry=e,status='OK',sha256=rh,format=detect_format(name,sample),sample=sample)
            f.seek(0); h2,_,_=hash_stream(f); after=stat_tuple(os.fstat(f.fileno()))
        pref=None
        for k,v in props.items():
            if k.lower()=='prefix': pref=v
        pbo_info.update(status='OK',sha256=h1,sha256_after=h2,size=length,stable=(before==after and h1==h2),properties=props,prefix_value=pref,prefix_status='MATCH' if pref==(pbo_c.get('prefix')) else 'PREFIX_MISMATCH',entry_count=len(entries))
        if pbo_c.get('sha256') and h1!=str(pbo_c['sha256']).lower(): pbo_info['global_status']='DIFFER'
        else: pbo_info['global_status']='MATCH' if pbo_c.get('sha256') else 'UNPINNED'
        if pbo_c.get('bytes') is not None and int(pbo_c['bytes'])!=length: pbo_info['size_status']='DIFFER'
        else: pbo_info['size_status']='MATCH'
    comparisons=[]; ref_reports=[]; model_reports=[]
    def add(kind,name,status,detail): comparisons.append(dict(kind=kind,name=name,status=status,detail=detail))
    for o in pin_obs: add('pin',o['path'],o['status'],o.get('sha256'))
    for o in prereq: add('prerequisite',o['path'],o['status'],o.get('sha256'))
    if not alias_ok or root_link: add('build_alias',str(alias),'UNRESOLVED_LINK',canonical_root)
    else: add('build_alias',str(alias),'MATCH',canonical_root)
    if pbo_info['status']!='OK': add('pbo',str(pbo_path),pbo_info['status'],None)
    else:
        add('pbo_prefix',str(pbo_c.get('prefix')),pbo_info['prefix_status'],pbo_info.get('prefix_value'))
        add('pbo_global',str(pbo_path),pbo_info.get('global_status','UNPINNED'),pbo_info.get('sha256'))
        if not pbo_info.get('stable'): add('pbo_stability',str(pbo_path),'SOURCE_UNSTABLE',None)
    for m in models:
        en=norm(m['entry']); row=model_rows.get(en); full=norm(m['name'])
        mr=dict(model=m['name'],entry=m['entry'],catalog_status='MISSING',pbo_status='MISSING',build_status='MISSING',catalog_sha256=None)
        if not row: add('model_catalog',m['name'],'MISSING',None); model_reports.append(mr); continue
        mr['catalog_sha256']=row.get('sha256'); mr['catalog_status']=row.get('status') or 'UNKNOWN'
        if row.get('status')!='READ_STRICT': add('model_catalog',m['name'],'UNREADABLE',row.get('status'))
        ce=entry_by.get(en); pr=pbo_ranges.get(en)
        exp_fmt=pr.get('format') if pr else 'UNKNOWN'
        if ce is None: add('model_entry_catalog',m['name'],'MISSING',en)
        elif pr is None:
            st='UNSUPPORTED_COMPRESSION' if (en in [x for x in selected] and False) else 'MISSING'; add('model_pbo',m['name'],'MISSING',en); mr['pbo_status']='MISSING'
        elif pr.get('status')=='UNSUPPORTED_COMPRESSION': add('model_pbo',m['name'],'UNSUPPORTED_COMPRESSION',en); mr['pbo_status']='UNSUPPORTED_COMPRESSION'
        else:
            ok=(ce.get('sha256')==pr.get('sha256') and int(ce.get('size'))==int(pr['entry']['size']) and int(ce.get('mime'))==int(pr['entry']['mime']) and row.get('sha256')==pr.get('sha256'))
            st='MATCH' if ok else 'DIFFER'; add('model_pbo',m['name'],st,pr.get('sha256')); mr['pbo_status']=st; mr['pbo_sha256']=pr.get('sha256')
        cand=inspect_build(canonical_root,full,trusted)
        bst=classify(row.get('sha256'),exp_fmt,cand); mr['build']=cand; mr['build_status']=bst; add('model_build',m['name'],bst,cand.get('sha256'))
        model_reports.append(mr)
    for n in sorted(refs):
        rec=refs[n]; raw0=rec['raws'][0]; rr=dict(normalized=n,raws=rec['raws'],models=rec['models'],lod_indexes=rec['lod_indexes'],status='UNKNOWN')
        if raw0.lstrip().startswith('#'): rr['status']='PROCEDURAL'; ref_reports.append(rr); continue
        if any(_unsafe_raw(r) for r in rec['raws']): rr['status']='UNSAFE_PATH'; add('reference_build',n,'UNSAFE_PATH',raw0); ref_reports.append(rr); continue
        if not (n==prefix_norm or n.startswith(prefix_norm+'/')): rr['status']='UNRESOLVED_EXTERNAL'; add('reference_build',n,'UNRESOLVED_EXTERNAL',raw0); ref_reports.append(rr); continue
        rel=n[len(prefix_norm)+1:]; ce=entry_by.get(rel); pr=pbo_ranges.get(rel); rr['entry']=rel
        if pr and pr.get('status')=='UNSUPPORTED_COMPRESSION': rr['status']='UNSUPPORTED_COMPRESSION'; add('reference_build',n,'UNSUPPORTED_COMPRESSION',raw0); ref_reports.append(rr); continue
        if pr is None: rr['status']='MISSING'; add('reference_build',n,'MISSING',raw0); ref_reports.append(rr); continue
        if ce is None: add('reference_entry_catalog',n,'MISSING',rel)
        elif not (ce.get('sha256')==pr.get('sha256') and int(ce.get('size'))==int(pr['entry']['size']) and int(ce.get('mime'))==int(pr['entry']['mime'])): add('reference_pbo_catalog',n,'DIFFER',pr.get('sha256'))
        exp_sha=(ce or {}).get('sha256') or pr.get('sha256'); cand=inspect_build(canonical_root,n,trusted); st=classify(exp_sha,pr.get('format'),cand); rr['status']=st; rr['build']=cand; rr['expected_sha256']=exp_sha; rr['pbo_sha256']=pr.get('sha256'); add('reference_build',n,st,cand.get('sha256')); ref_reports.append(rr)
    for o,c in ((cm_obs,'catalog_models'),(ce_obs,'catalog_entries')):
        if not o.get('stable') and o.get('status')!='MISSING': add(c,str(o.get('path')), 'SOURCE_UNSTABLE',o.get('sha256'))
    drift={'DIFFER','FORMAT_DIFFERS'}; incomplete=[c for c in comparisons if c['status']!='MATCH']
    if comparisons and all(c['status']=='MATCH' for c in comparisons): agg='INPUTS_MATCH'
    elif any(c['status'] in drift for c in comparisons): agg='INPUTS_DIFFER'
    else: agg='INCONCLUSIVE_DISCOVERY'
    sources_stable=bool(all(o.get('stable') for o in pin_obs if o.get('status') not in ('MISSING','UNREADABLE')) and pbo_info.get('stable',False) and cm_obs.get('stable',False) and ce_obs.get('stable',False))
    clean=lambda o: {k:v for k,v in o.items() if not k.startswith('_') and k!='sample'}
    report=dict(schema='road-build-discovery.v1.report',status=agg,aggregate=agg,build_ready=False,pivot='UNKNOWN',width='UNKNOWN',accesses='UNKNOWN',unknowns=dict(pivot='UNKNOWN',width='UNKNOWN',accesses='UNKNOWN'),contract_sha256=str(contract_sha256).lower(),tool_sha256=tool_sha,sources_stable=sources_stable,build_alias=dict(alias=alias,build_root=build_root,canonical_root=canonical_root,alias_ok=alias_ok,root=root_info),pbo={k:v for k,v in pbo_info.items() if k!='entries'},pins=[clean(o) for o in pin_obs],prerequisites=[clean(o) for o in prereq],stage_paths=stages,catalog_models=clean(cm_obs),catalog_entries_source=clean(ce_obs),models=model_reports,references=ref_reports,comparisons=comparisons,incomplete_coverage=incomplete,limits=contract.get('limits') or {},limitations=['discovery_only_not_build_ready','pivot_unknown','width_unknown','accesses_unknown','no_geometry_redecode','no_transitive_rvmat_closure','manifest_integrity_is_not_geometric_verification'])
    out.mkdir(parents=True)
    try:
        rb=canon(report); (out/'report.json').write_bytes(rb)
        manifest=dict(schema='road-build-discovery.v1.manifest',report_sha256=sha_bytes(rb),report_sha=sha_bytes(rb),contract_sha256=report['contract_sha256'],contract_sha=report['contract_sha256'],tool_sha256=tool_sha,tool_sha=tool_sha)
        (out/'manifest.json').write_bytes(canon(manifest))
    except Exception:
        for fn in ('report.json','manifest.json'):
            try: (out/fn).unlink()
            except OSError: pass
        raise
    return report
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--contract',required=True); ap.add_argument('--contract-sha256',required=True); ap.add_argument('--out',required=True); a=ap.parse_args(argv)
    r=run_discovery(a.contract,a.contract_sha256,a.out); print(json.dumps(dict(status=r['status'],build_ready=False),sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
