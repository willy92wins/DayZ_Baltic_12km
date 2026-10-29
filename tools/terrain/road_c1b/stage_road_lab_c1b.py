"""One-shot byte stage. No DayZ tool, format or native acceptance."""
from pathlib import Path
import argparse, hashlib, json, os, re, stat, sys

CAPS={'entries':8192,'file':33554432,'common':402653184,'pair':1073741824,'json':8388608}
CLAIMS={'build_ready':False,'dependency_closure':'NOT_EVALUATED','compiled_terrain_decoder':'NOT_VERIFIED'}
class Rejected(Exception): pass
def need(ok,code):
    if not ok: raise Rejected(code)
def pairs(seq):
    d={}
    for k,v in seq:
        need(k not in d,'SCHEMA');d[k]=v
    return d
def safe_rel(s):
    need(type(s) is str and s and s.isascii() and s==s.lower() and '\\' not in s and ':' not in s,'PATH')
    for c in s.split('/'):
        need(c not in ('','.','..') and c[-1] not in '. ' and not any(ord(x)<32 or x in '<>"|?*' for x in c),'PATH')
        need(not re.fullmatch(r'(con|prn|aux|nul|com[1-9]|lpt[1-9])',c.split('.')[0]),'PATH')
    return s
def guard(p):
    for q in [p,*p.parents]:
        s=q.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&1024,'REPARSE')
def ident(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def blob(path,sha):
    p=Path(path);guard(p);need(p.stat().st_size<=CAPS['json'],'JSON_CAP')
    with p.open('rb') as f:b=f.read(CAPS['json']+1)
    need(len(b)<=CAPS['json'] and hashlib.sha256(b).hexdigest()==sha,'CONTRACT_PIN')
    return json.loads(b,object_pairs_hook=pairs)
def contract(path,pin,binding_pin):
    c=blob(path,pin);need(type(c) is dict and set(c)=={'schema','caps','bindings','files','output','claims','config_refs'},'SCHEMA')
    need(c['schema']=='road-c1b-stage.v1' and c['caps']==CAPS and all(type(v) is int for v in c['caps'].values()),'SCHEMA')
    need(c['claims']==CLAIMS and c['claims']['build_ready'] is False,'SCHEMA')
    need(type(c['bindings']) is dict and set(c['bindings'])=={'path','sha256'} and c['bindings']['sha256']==binding_pin,'BINDING')
    binding=blob(c['bindings']['path'],binding_pin)
    fs=c['files'];need(type(fs) is list and 2<=len(fs)<=CAPS['entries']+2,'ENTRY_CAP')
    seen=set();common=0;cb=0;branches={'control':[],'candidate':[]};observed=[]
    for e in fs:
        need(type(e) is dict and set(e)=={'scope','dest','sha256','bytes','sources'},'SCHEMA')
        need(e['scope'] in ('common','control','candidate'),'SCHEMA');d=safe_rel(e['dest']);key=(e['scope'],d)
        need(key not in seen,'COLLISION');seen.add(key)
        need(type(e['bytes']) is int and 0<=e['bytes']<=CAPS['file'],'SIZE_TYPE')
        need(type(e['sha256']) is str and re.fullmatch('[0-9a-f]{64}',e['sha256']),'SCHEMA')
        ss=e['sources'];need(type(ss) is list and 1<=len(ss)<=16,'SCHEMA')
        for s in ss:
            need(type(s) is dict and set(s)=={'path','identity','sha256','bytes','origin'},'SCHEMA')
            need(type(s['path']) is str and Path(s['path']).is_absolute() and type(s['origin']) is str,'SCHEMA')
            need(type(s['identity']) is list and len(s['identity'])==4 and all(type(i) is int and i>=0 for i in s['identity']),'SCHEMA')
            need(type(s['bytes']) is int and s['bytes']==e['bytes'] and s['sha256']==e['sha256'] and s['identity'][2]==e['bytes'],'SCHEMA')
            need(s['identity']==ss[0]['identity'],'COLLISION')
        observed.append({'scope':e['scope'],'dest':d,'sources':[s['path'] for s in ss]})
        if e['scope']=='common':common+=1;cb+=e['bytes']
        else:branches[e['scope']].append(e)
    need(observed==binding,'BINDING')
    need(common<=CAPS['entries'] and cb<=CAPS['common'],'TOTAL_CAP')
    need(all(len(v)==1 for v in branches.values()),'WRP_PIN')
    x,y=branches['control'][0],branches['candidate'][0]
    need(x['dest']==y['dest'] and x['sha256']!=y['sha256'] and ('common',x['dest']) not in seen,'WRP_PIN')
    need(2*cb+x['bytes']+y['bytes']<=CAPS['pair'],'TOTAL_CAP')
    for arm in ('control','candidate'):
        names={e['dest'] for e in fs if e['scope'] in ('common',arm)}
        for name in names:
            need(not any('/'.join(name.split('/')[:i]) in names for i in range(1,len(name.split('/')))),'COLLISION')
    refs=c['config_refs'];need(type(refs) is list and len(refs)<=32,'CONFIG_REF');ref_seen=set()
    commons={e['dest']:e for e in fs if e['scope']=='common'}
    for ref in refs:
        need(type(ref) is dict and set(ref)=={'raw','source','dest'},'CONFIG_REF')
        need(all(type(v) is str for v in ref.values()),'CONFIG_REF');dest=safe_rel(ref['dest'])
        need(ref['raw'].replace('\\','/').lower()==dest and dest not in ref_seen and dest in commons,'CONFIG_REF');ref_seen.add(dest)
        need(ref['source'] in [s['path'] for s in commons[dest]['sources']],'CONFIG_REF')
    need(type(c['output']) is str and Path(c['output']).is_absolute(),'PATH')
    return c
def transfer(s,targets):
    p=Path(s['path']);guard(p);need(ident(p.stat())==s['identity'],'SOURCE_PIN')
    streams=[];h=hashlib.sha256();n=0
    try:
        for t in targets:
            t.parent.mkdir(parents=True,exist_ok=True);guard(t.parent);streams.append(t.open('xb'))
        with p.open('rb') as f:
            need(ident(os.fstat(f.fileno()))==s['identity'],'SOURCE_PIN')
            while True:
                b=f.read(min(1048576,s['bytes']-n+1))
                if not b:break
                n+=len(b);need(n<=s['bytes'],'SOURCE_PIN');h.update(b)
                for out in streams:need(out.write(b)==len(b),'WRITE')
            need(ident(os.fstat(f.fileno()))==s['identity'],'SOURCE_PIN')
        guard(p);need(ident(p.stat())==s['identity'] and n==s['bytes'] and h.hexdigest()==s['sha256'],'SOURCE_PIN')
        for out in streams:out.flush();os.fsync(out.fileno())
    finally:
        for out in streams:out.close()
    for t in targets:
        h2=hashlib.sha256();count=0;guard(t)
        with t.open('rb') as f:
            for b in iter(lambda:f.read(1048576),b''):count+=len(b);need(count<=s['bytes'],'WRITE');h2.update(b)
        need(count==s['bytes'] and h2.hexdigest()==s['sha256'],'WRITE')
def run(c,pin):
    out=Path(c['output']);guard(out.parent);need(not out.exists(),'EXISTS');out.mkdir()
    (out/'consumed.json').write_text(json.dumps({'contract_sha256':pin,'retry':False}),encoding='utf-8')
    receipts=[]
    for e in c['files']:
        arms=('control','candidate') if e['scope']=='common' else (e['scope'],)
        targets=[out/a/'root'/e['dest'] for a in arms]
        transfer(e['sources'][0],targets)
        for s in e['sources'][1:]:transfer(s,[])
        receipts.append({k:e[k] for k in ('scope','dest','bytes','sha256')})
    result={'status':'LAB_STAGE_WRITTEN_ONLY','contract_sha256':pin,'claims':CLAIMS,'files':receipts}
    b=json.dumps(result,indent=2).encode();need(len(b)<=CAPS['json'],'OUTPUT_CAP');(out/'producer.json').write_bytes(b);return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--sha',required=True);p.add_argument('--bindings-sha',required=True);a=p.parse_args()
    try:
        c=contract(a.contract,a.sha,a.bindings_sha);r=run(c,a.sha);print(json.dumps({'status':r['status'],'entries':len(r['files'])}));return 0
    except Rejected as e:print('REJECTED:'+str(e));return 2
    except OSError as e:print('IO_ERROR:'+str(e));return 3
if __name__=='__main__':sys.exit(main())
