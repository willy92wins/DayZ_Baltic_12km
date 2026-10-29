"""Independent inventory/source walk; standard-library I/O shared with author."""
import argparse,hashlib,json,os,re,stat,sys
from pathlib import Path

class Invalid(Exception):pass
def check(x,code):
    if not x:raise Invalid(code)
def obj(items):
    d={}
    for k,v in items:
        check(k not in d,'SCHEMA');d[k]=v
    return d
def ancestry(p):
    while True:
        s=p.lstat();check(not stat.S_ISLNK(s.st_mode) and (getattr(s,'st_file_attributes',0)&1024)==0,'REPARSE')
        if p.parent==p:return
        p=p.parent
def identity(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def hashed(p,limit,expected_id=None):
    p=Path(p);ancestry(p);before=identity(p.stat());check(stat.S_ISREG(p.stat().st_mode) and before[2]<=limit,'FILE_CAP')
    if expected_id is not None:check(before==expected_id,'SOURCE_PIN')
    h=hashlib.sha256();n=0
    with p.open('rb') as f:
        check(identity(os.fstat(f.fileno()))==before,'IDENTITY')
        while n<=limit:
            b=f.read(min(524288,limit-n+1))
            if not b:break
            n+=len(b);check(n<=limit,'FILE_CAP');h.update(b)
        check(identity(os.fstat(f.fileno()))==before,'IDENTITY')
    ancestry(p);check(identity(p.stat())==before and n==before[2],'IDENTITY');return n,h.hexdigest()
def load(p,pin):
    n,h=hashed(p,8388608);check(h==pin,'CONTRACT_PIN')
    # Parse a second bounded buffer, independently pin the exact parsed bytes.
    with open(p,'rb') as f:b=f.read(8388609)
    check(len(b)==n and hashlib.sha256(b).hexdigest()==pin,'CONTRACT_PIN');return json.loads(b,object_pairs_hook=obj)
def relative(s):
    check(type(s) is str and s and s.isascii() and s==s.lower(),'PATH')
    check(not any(ord(c)<32 or c in '\\:<>"|?*' for c in s),'PATH')
    for a in s.split('/'):
        check(a not in ('','.','..') and a[-1] not in '. ','PATH')
        check(a.split('.')[0] not in {'con','prn','aux','nul',*[f'com{i}' for i in range(1,10)],*[f'lpt{i}' for i in range(1,10)]},'PATH')
    return s
def read_contract(path,pin,binding_pin):
    c=load(path,pin);check(type(c) is dict and set(c)=={'schema','caps','bindings','files','output','claims','config_refs'},'SCHEMA')
    caps={'entries':8192,'file':33554432,'common':402653184,'pair':1073741824,'json':8388608}
    check(c['schema']=='road-c1b-stage.v1' and c['caps']==caps and all(type(v) is int for v in c['caps'].values()),'SCHEMA')
    check(c['claims']=={'build_ready':False,'dependency_closure':'NOT_EVALUATED','compiled_terrain_decoder':'NOT_VERIFIED'} and c['claims']['build_ready'] is False,'SCHEMA')
    check(type(c['bindings']) is dict and set(c['bindings'])=={'path','sha256'} and c['bindings']['sha256']==binding_pin,'BINDING')
    bind=load(c['bindings']['path'],binding_pin);check(type(bind) is list,'BINDING')
    check(type(c['files']) is list and len(c['files'])<=8194,'ENTRY_CAP');expected={'control':{},'candidate':{}};sources=[];bseen=[];keys=set();amount=0;common=0;arms={}
    for row in c['files']:
        check(type(row) is dict and set(row)=={'scope','dest','sha256','bytes','sources'},'SCHEMA')
        scope=row['scope'];check(scope in ('common','control','candidate'),'SCHEMA');dest=relative(row['dest']);check((scope,dest) not in keys,'COLLISION');keys.add((scope,dest))
        size=row['bytes'];digest=row['sha256'];check(type(size) is int and 0<=size<=33554432,'SIZE_TYPE');check(type(digest) is str and re.fullmatch('[0-9a-f]{64}',digest),'SCHEMA')
        aliases=row['sources'];check(type(aliases) is list and 1<=len(aliases)<=16,'SCHEMA')
        ids=[]
        for s in aliases:
            check(type(s) is dict and set(s)=={'path','identity','sha256','bytes','origin'},'SCHEMA')
            check(type(s['path']) is str and Path(s['path']).is_absolute() and type(s['origin']) is str,'SCHEMA')
            si=s['identity'];check(type(si) is list and len(si)==4 and all(type(i) is int and i>=0 for i in si),'SCHEMA')
            check(type(s['bytes']) is int and s['bytes']==size and si[2]==size and s['sha256']==digest,'SCHEMA');ids.append(si);sources.append(s)
        check(all(i==ids[0] for i in ids),'COLLISION');bseen.append({'scope':scope,'dest':dest,'sources':[s['path'] for s in aliases]})
        if scope=='common':common+=1;amount+=size;use=['control','candidate']
        else:check(scope not in arms,'WRP_PIN');arms[scope]=(dest,digest,size);use=[scope]
        for arm in use:check(dest not in expected[arm],'COLLISION');expected[arm][dest]=(size,digest)
    check(bseen==bind,'BINDING');check(common<=8192 and amount<=402653184,'TOTAL_CAP')
    check(set(arms)=={'control','candidate'} and arms['control'][0]==arms['candidate'][0] and arms['control'][1]!=arms['candidate'][1],'WRP_PIN')
    check(amount*2+arms['control'][2]+arms['candidate'][2]<=1073741824,'TOTAL_CAP')
    check(type(c['output']) is str and Path(c['output']).is_absolute(),'PATH');return c,expected,sources
def verify(c,expected,sources,pin):
    root=Path(c['output']);stage_errors=[];source_errors=[];count=0
    for arm in ('control','candidate'):
        base=root/arm/'root';seen=set()
        try:
            ancestry(base);check({p.name for p in (root/arm).iterdir()}=={'root'},'EXTRA')
            dirs=set();wanted_dirs={str(p).replace('\\','/') for name in expected[arm] for p in Path(name).parents if str(p)!='.'}
            stack=[base];nodes=0
            while stack:
                parent=stack.pop()
                for p in parent.iterdir():
                    nodes+=1;check(nodes<=32768,'TREE_CAP');ancestry(p)
                    if p.is_dir():dirs.add(p.relative_to(base).as_posix());stack.append(p);continue
                    name=p.relative_to(base).as_posix();check(name not in seen,'COLLISION');seen.add(name)
                    check(name in expected[arm],'EXTRA');n,h=hashed(p,expected[arm][name][0]);check((n,h)==expected[arm][name],'STAGE_HASH');count+=1
            check(seen==set(expected[arm]),'MISSING')
            check(dirs==wanted_dirs,'EXTRA')
        except (Invalid,OSError) as e:stage_errors.append({'arm':arm,'error':str(e)})
    for s in sources:
        try:check(hashed(s['path'],s['bytes'],s['identity'])==(s['bytes'],s['sha256']),'SOURCE_PIN')
        except (Invalid,OSError) as e:source_errors.append({'path':s['path'],'error':str(e)})
    good=not(stage_errors or source_errors)
    return {'status':'VERIFIED_LAB_STAGE_BYTES_ONLY' if good else 'REJECTED','contract_sha256':pin,'STAGE_BYTES':'MATCH' if not stage_errors else 'REJECTED','SOURCE_PIN_MATCH':'MATCH' if not source_errors else 'REJECTED','stage_errors':stage_errors,'source_errors':source_errors,'stage_files_verified':count,'source_aliases_checked':len(sources),'claims':c['claims'],'continuous_monitoring':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--sha',required=True);p.add_argument('--bindings-sha',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    try:
        c,expected,sources=read_contract(a.contract,a.sha,a.bindings_sha);r=verify(c,expected,sources,a.sha);b=json.dumps(r,indent=2).encode();check(len(b)<=8388608,'OUTPUT_CAP')
        with open(a.report,'xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
        print(json.dumps({k:r[k] for k in ['status','STAGE_BYTES','SOURCE_PIN_MATCH','stage_files_verified','source_aliases_checked']}));return 0 if r['status'].startswith('VERIFIED') else 2
    except Invalid as e:print('REJECTED:'+str(e));return 2
    except OSError as e:print('IO_ERROR:'+str(e));return 3
if __name__=='__main__':sys.exit(main())
