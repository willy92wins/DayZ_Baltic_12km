"""Byte-only preparation. No native process invocation."""
from pathlib import Path
import argparse,hashlib,json,os,stat,shutil,time,sys
class Stop(Exception):pass
def need(ok,code):
    if not ok:raise Stop(code)
def ident(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def guard(p):
    for q in [Path(p),*Path(p).parents]:
        s=q.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&1024,'REPARSE')
def read_hash(p,cap=67108864,deadline=float('inf'),copy=None,collect=False):
    p=Path(p);guard(p);pre=ident(p.stat());need(stat.S_ISREG(p.stat().st_mode),'FILE_TYPE');need(pre[2]<=cap,'CAP')
    digest=hashlib.sha256();n=0;chunks=[];out=None
    try:
        if copy is not None:
            copy=Path(copy);copy.parent.mkdir(parents=True,exist_ok=True);guard(copy.parent);out=copy.open('xb')
        with p.open('rb') as f:
            need(ident(os.fstat(f.fileno()))==pre,'IDENTITY')
            while True:
                need(time.monotonic()<deadline,'BUDGET');b=f.read(min(1048576,cap-n+1))
                if not b:break
                n+=len(b);need(n<=cap,'CAP');digest.update(b)
                if collect:chunks.append(b)
                if out:need(out.write(b)==len(b),'WRITE')
            need(ident(os.fstat(f.fileno()))==pre,'IDENTITY')
        guard(p);need(ident(p.stat())==pre and n==pre[2],'IDENTITY')
        if out:out.flush();os.fsync(out.fileno())
    finally:
        if out:out.close()
    row={'bytes':n,'sha256':digest.hexdigest(),'identity':pre}
    return (row,b''.join(chunks)) if collect else row
def pincheck(row,deadline=float('inf')):
    got=read_hash(row['path'],max(row['bytes'],1),deadline);need((got['bytes'],got['sha256'])==(row['bytes'],row['sha256']),'PIN')
    if 'identity' in row:need(got['identity']==row['identity'],'IDENTITY')
    return got
def load(p,pin,deadline=float('inf')):
    row,b=read_hash(p,33554432,deadline,collect=True);need(row['sha256']==pin,'PIN');return json.loads(b)
def write_json(p,value):
    b=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode();need(len(b)<=33554432,'CAP')
    guard(Path(p).parent)
    with Path(p).open('xb') as f:need(f.write(b)==len(b),'WRITE');f.flush();os.fsync(f.fileno())
def relative(value):
    need(isinstance(value,str) and value and '\\' not in value and ':' not in value and all(x not in ('','.','..') for x in value.split('/')) and all(32<=ord(x)<127 for x in value),'PATH')
    return value
def dirs_for(files):return {p.as_posix() for x in files for p in Path(x).parents if str(p)!='.'}
def inventory(root,allowed,until):
    root=Path(root);guard(root);files=set();dirs=set();count=0
    for folder,sub,names in os.walk(root,followlinks=False):
        for name in sub+names:
            need(time.monotonic()<until,'BUDGET');p=Path(folder)/name;guard(p);count+=1;need(count<=32768,'CAP');rel=p.relative_to(root).as_posix()
            if p.is_dir():dirs.add(rel)
            elif p.is_file():files.add(rel)
            else:raise Stop('FILE_TYPE')
    need(files==set(allowed) and dirs==dirs_for(allowed),'INVENTORY')
    return files
def scan(root,expected,until,previous=None):
    inventory(root,expected,until);rows={}
    for name,pin in expected.items():
        row=read_hash(Path(root)/name,134217728 if name.lower().endswith('.wrp') else 67108864,until)
        need((row['bytes'],row['sha256'])==(pin['bytes'],pin['sha256']),'PIN')
        if previous is not None:need(row==previous[name],'IDENTITY')
        rows[name]=row
    return rows
def canonical(c,until):
    spec=c['canonical_preflight'];alias=spec['alias'];p=Path(alias['path'])
    def aliascheck():
        s=p.lstat();need((s.st_dev,s.st_ino,getattr(s,'st_reparse_tag',0),os.readlink(p))==(alias['dev'],alias['ino'],alias['tag'],alias['target']),'ALIAS_CHANGED');need(p.resolve(strict=True)==Path(spec['file']['path']).parent,'ALIAS_CHANGED')
    def ancestors():
        for row in spec['ancestors']:
            q=Path(row['path']);guard(q);s=q.lstat();need((s.st_dev,s.st_ino,q.is_dir())==(row['dev'],row['ino'],row['is_dir']),'IDENTITY')
    aliascheck();ancestors();pincheck(spec['file'],until);ancestors();aliascheck()
def profile(c,until):
    rows=[];count=0;total=0
    for base in map(Path,c['profile_roots']):
        if not base.exists():continue
        guard(base)
        for app in base.glob('AddonBuilder*'):
            pending=[app]
            while pending:
                p=pending.pop();guard(p);count+=1;need(count<=256,'CAP');need(time.monotonic()<until,'BUDGET')
                if p.is_dir():pending.extend(p.iterdir())
                elif p.name=='user.config':
                    row=read_hash(p,4194304,until);total+=row['bytes'];need(total<=16777216,'CAP');rows.append({'path':str(p),**row})
    return sorted(rows,key=lambda r:r['path'])
def mappings(c,until):
    old=load(c['c1b']['path'],c['c1b']['sha256'],until);arms={}
    for arm in ['control','candidate']:
        items=[r for r in old['files'] if r['scope'] in ('common',arm)];table={relative(r['dest']):{'bytes':r['bytes'],'sha256':r['sha256']} for r in items}
        need(len(table)==len(items),'PATH');need(len({x.lower() for x in table})==len(table),'PATH');arms[arm]=table
    fixed={}
    for r in c['tool_files']:fixed['tools/AddonBuilder/'+relative(r['dest'])]=r
    for key,dest in c['fixed_destinations'].items():need(dest in ['fixed/include.lst','fixed/exclude.lst','fixed/preflight-local.py'],'PATH');fixed[dest]=c[key]
    need(len(fixed)==len(c['tool_files'])+3,'PATH');return arms,fixed
def inputs(c,until):
    canonical(c,until);rows={}
    for row in [c['c1b'],c['c1b_consumer'],*c['tool_files'],*c['tools'].values(),c['include'],c['exclude'],c['preflight'],c['preflight_original'],c['os_helper'],*c['evidence']]:rows[row['path']]=pincheck(row,until)
    return rows
def validate(c):
    need(c['schema']=='road-c1c2a-preparation.v1' and c['empty_directories']==[],'SCHEMA')
    need(c['caps']=={'source':120,'copy':150,'fixed':80,'finalize':10,'producer':360,'consumer':180,'total':540,'producer_rss':536870912,'consumer_rss':268435456,'disk':2147483648,'free_min':3221225472,'file':67108864,'wrp':134217728,'json':33554432,'entries':32768},'SCHEMA')
    need(c['fixed_destinations']=={'include':'fixed/include.lst','exclude':'fixed/exclude.lst','preflight':'fixed/preflight-local.py'},'SCHEMA')
def prepare(c,pin):
    validate(c);root=Path(c['root']);need(not root.exists(),'EXISTS');guard(root.parent);need(shutil.disk_usage(root.parent).free>3221225472,'DISK_FREE');root.mkdir();(root/'meta').mkdir()
    start=time.monotonic_ns();global_end=time.monotonic()+360;phase='source';sequence=0;rows={};journals={};status='IN_PROGRESS';reason=None
    marker={'contract_sha256':pin,'started_wall':time.time(),'no_retries':True};write_json(root/'meta/marker.json',marker)
    def event(which,until):
        nonlocal sequence
        need(time.monotonic()<until,'BUDGET');sequence+=1;name=phase+'.'+which+'.json';v={'phase':phase,'event':which,'sequence':sequence,'elapsed_ns':time.monotonic_ns()-start};write_json(root/'meta'/name,v);journals[name]=read_hash(root/'meta'/name,33554432,until)
    try:
        until=min(global_end,time.monotonic()+120);event('started',until);baseinputs=inputs(c,until);before=profile(c,until);arms,fixed=mappings(c,until)
        source={arm:scan(Path(c['source_stage'])/arm/'root',table,until) for arm,table in arms.items()};rows.update(inputs=baseinputs,profile_before=before,source=source);event('done',until)
        phase='copy';until=min(global_end,time.monotonic()+150);event('started',until);work={}
        expected_output=sum(r['bytes'] for t in arms.values() for r in t.values())+sum(r['bytes'] for r in fixed.values());need(expected_output+33554432<2147483648,'CAP')
        for arm,table in arms.items():
            work[arm]={}
            for name,want in table.items():
                src=Path(c['source_stage'])/arm/'root'/name;dst=root/'work'/arm/'root'/name;got=read_hash(src,134217728 if name.lower().endswith('.wrp') else 67108864,until,dst);need(got==source[arm][name],'IDENTITY');again=read_hash(dst,max(want['bytes'],1),until);need((again['bytes'],again['sha256'])==(want['bytes'],want['sha256']),'PIN');work[arm][name]=again
        rows['work']=work;event('done',until)
        phase='fixed';until=min(global_end,time.monotonic()+80);event('started',until);fixedrows={}
        for name,want in fixed.items():
            got=read_hash(want['path'],67108864,until,root/name);need(got==baseinputs[want['path']],'IDENTITY');again=read_hash(root/name,67108864,until);need((again['bytes'],again['sha256'])==(want['bytes'],want['sha256']),'PIN');fixedrows[name]=again
        for arm,table in arms.items():scan(root/'work'/arm/'root',table,until,work[arm])
        for name,row in fixedrows.items():need(read_hash(root/name,67108864,until)==row,'IDENTITY')
        need(inputs(c,until)==baseinputs,'IDENTITY');need(profile(c,until)==before,'PROFILE_CHANGED');rows['profile_after']=before;rows['fixed']=fixedrows
        allfiles={f'work/{a}/root/{n}' for a,t in arms.items() for n in t}|set(fixed)|{'meta/marker.json'}|{'meta/'+n for n in journals}
        inventory(root,allfiles,until);event('done',until)
        phase='finalize';until=min(global_end,time.monotonic()+10);need(time.monotonic()<until,'BUDGET');status='PREPARED_PAIR_BYTES_ONLY'
    except Stop as e:status='PREPARATION_STOPPED';reason=str(e)
    except OSError as e:status='PREPARATION_STOPPED';reason='IO:'+type(e).__name__+':'+str(e)
    report={'contract_sha256':pin,'status':status,'phase':phase,'reason':reason,'journals':journals,'marker':read_hash(root/'meta/marker.json',33554432,global_end),'rows':rows,'claims':c['claims'],'elapsed_ns':time.monotonic_ns()-start}
    need(time.monotonic()<global_end,'BUDGET');write_json(root/'meta/report.json',report)
    return report
def main():
    p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--sha',required=True);a=p.parse_args()
    try:r=prepare(load(a.contract,a.sha),a.sha);print(json.dumps({'status':r['status'],'reason':r['reason']}));return 0 if r['status']=='PREPARED_PAIR_BYTES_ONLY' else 2
    except (Stop,OSError) as e:print(json.dumps({'status':'REJECTED','reason':str(e)}));return 1
if __name__=='__main__':sys.exit(main())
