"""Independent semantic walk of prepared bytes and externally pinned receipts."""
from pathlib import Path
import argparse,hashlib,json,math,os,stat,sys,time
class Reject(Exception):pass
def require(x,code):
    if not x:raise Reject(code)
def fileid(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def pathcheck(p):
    p=Path(p)
    while True:
        s=p.lstat();require(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&1024,'REPARSE')
        if p.parent==p:break
        p=p.parent
def checkfile(p,want=None,cap=134217728,until=float('inf'),payload=False):
    p=Path(p);pathcheck(p);before=fileid(p.stat());require(stat.S_ISREG(p.stat().st_mode),'FILE_TYPE');require(before[2]<=cap,'CAP');digest=hashlib.sha256();size=0;data=[]
    with p.open('rb') as stream:
        require(fileid(os.fstat(stream.fileno()))==before,'IDENTITY')
        while True:
            require(time.monotonic()<until,'BUDGET');block=stream.read(min(524288,cap-size+1))
            if not block:break
            size+=len(block);require(size<=cap,'CAP');digest.update(block)
            if payload:data.append(block)
        require(fileid(os.fstat(stream.fileno()))==before,'IDENTITY')
    pathcheck(p);require(fileid(p.stat())==before and size==before[2],'IDENTITY');row={'bytes':size,'sha256':digest.hexdigest(),'identity':before}
    if want:
        require(type(want['bytes']) is int and want['bytes']>=0,'SCHEMA');require((size,row['sha256'])==(want['bytes'],want['sha256']),'PIN')
        if 'identity' in want:require(before==want['identity'],'IDENTITY')
    return (row,b''.join(data)) if payload else row
def pairs(items):
    out={}
    for k,v in items:require(k not in out,'SCHEMA');out[k]=v
    return out
def readjson(path,pin,until=float('inf'),code='PIN'):
    row,b=checkfile(path,cap=33554432,until=until,payload=True);require(row['sha256']==pin,code);return json.loads(b,object_pairs_hook=pairs)
def safe(name):
    require(isinstance(name,str) and name and '\\' not in name and ':' not in name and all(x not in ('','.','..') for x in name.split('/')) and all(32<=ord(x)<127 for x in name),'PATH');return name
def walk(base,files,until,complete=True):
    base=Path(base);pathcheck(base);found=set();folders=set();todo=[base];count=0
    while todo:
        directory=todo.pop()
        for p in directory.iterdir():
            require(time.monotonic()<until,'BUDGET');pathcheck(p);count+=1;require(count<=32768,'CAP');rel=p.relative_to(base).as_posix()
            if p.is_dir():folders.add(rel);todo.append(p)
            elif p.is_file():found.add(rel)
            else:raise Reject('FILE_TYPE')
    allowed=set()
    for name in files:
        q=Path(name).parent
        while str(q)!='.':allowed.add(q.as_posix());q=q.parent
    require(found<=set(files) and folders<=allowed,'INVENTORY')
    if complete:require(found==set(files) and folders==allowed,'INVENTORY')
    return found
def canonical(c,until):
    s=c['canonical_preflight'];a=s['alias'];p=Path(a['path'])
    for iteration in range(2):
        now=p.lstat();require((now.st_dev,now.st_ino,getattr(now,'st_reparse_tag',0),os.readlink(p))==(a['dev'],a['ino'],a['tag'],a['target']),'ALIAS_CHANGED');require(p.resolve()==Path(s['file']['path']).parent,'ALIAS_CHANGED')
        for item in s['ancestors']:
            q=Path(item['path']);pathcheck(q);st=q.lstat();require((st.st_dev,st.st_ino,q.is_dir())==(item['dev'],item['ino'],item['is_dir']),'IDENTITY')
        checkfile(s['file']['path'],s['file'],16384,until)
def current_inputs(c,until):
    require(len([r for r in c['evidence'] if r['path']==sys.executable])==1,'INTERPRETER_BINDING')
    canonical(c,until);result={}
    for item in [c['c1b'],c['c1b_consumer'],*c['tool_files'],*c['tools'].values(),c['include'],c['exclude'],c['preflight'],c['preflight_original'],c['os_helper'],*c['evidence']]:result[item['path']]=checkfile(item['path'],item,67108864,until)
    return result
def profiles(c,until):
    rows=[];count=0;total=0
    for directory in c['profile_roots']:
        base=Path(directory)
        if not base.exists():continue
        pathcheck(base)
        for app in base.glob('AddonBuilder*'):
            queue=[app]
            while queue:
                p=queue.pop();pathcheck(p);count+=1;require(count<=256,'CAP');require(time.monotonic()<until,'BUDGET')
                if p.is_dir():queue+=list(p.iterdir())
                elif p.name=='user.config':
                    row=checkfile(p,cap=4194304,until=until);total+=row['bytes'];require(total<=16777216,'CAP');rows.append({'path':str(p),**row})
    return sorted(rows,key=lambda r:r['path'])
def consume(c,pin,obs,until):
    require(c['schema']=='road-c1c2a-preparation.v1' and c['empty_directories']==[],'SCHEMA');require(obs['contract_sha256']==pin,'BINDING');root=Path(c['root']);receipt=obs['completion']
    require(obs['producer_code']['path']==obs['command'][4] and obs['command'][1:4]==['-I','-X','utf8'] and obs['command'][5:]==['--contract',obs['contract_path'],'--sha',pin],'BINDING');checkfile(obs['producer_code']['path'],obs['producer_code'],67108864,until)
    require(obs['command'][0]==sys.executable,'BINDING');require(obs['owned_retired'] is True and type(receipt['root_pid']) is int and type(receipt['root_birth']) in (float,int),'BINDING');require(type(receipt['rc']) is int,'RECEIPT_SCHEMA')
    for name in ['seconds','peak_rss','observed_disk_peak']:require(type(receipt[name]) in (float,int) and math.isfinite(receipt[name]) and receipt[name]>=0,'CAP')
    require(receipt['peak_rss']<=536870912 and receipt['observed_disk_peak']<=2147483648,'CAP')
    for stream in ['stdout','stderr']:checkfile(receipt[stream]['path'],receipt[stream],33554432,until)
    present={p.name for p in (root/'meta').iterdir() if p.is_file()};require(present==set(obs['meta']),'OBSERVATION_PIN')
    meta={}
    for name,expected in obs['meta'].items():
        require(name in ['marker.json','report.json',*[f'{p}.{e}.json' for p in ['source','copy','fixed'] for e in ['started','done']]],'INVENTORY')
        try:checkfile(root/'meta'/name,expected,33554432,until)
        except Reject as e:
            if str(e) in ['PIN','IDENTITY']:raise Reject('OBSERVATION_PIN') from e
            raise
        meta[name]=readjson(root/'meta'/name,expected['sha256'],until)
    require('marker.json' in meta and meta['marker.json']['contract_sha256']==pin and meta['marker.json']['no_retries'] is True,'BINDING')
    report=meta.get('report.json');full=report is not None and report.get('status')=='PREPARED_PAIR_BYTES_ONLY'
    if report:
        require(type(report) is dict and set(report)=={'contract_sha256','status','phase','reason','journals','marker','rows','claims','elapsed_ns'},'SCHEMA');require(type(report['rows']) is dict and type(report['journals']) is dict,'SCHEMA')
        require(report['contract_sha256']==pin and report['claims']==c['claims'] and report['status'] in ['PREPARED_PAIR_BYTES_ONLY','PREPARATION_STOPPED'],'BINDING')
        if full:require(set(report['rows'])=={'inputs','profile_before','profile_after','source','work','fixed'},'SCHEMA')
    sequence=0;last=-1;started={}
    for phase,budget in [('source',120),('copy',150),('fixed',80)]:
        for event in ['started','done']:
            name=phase+'.'+event+'.json'
            if name not in meta:
                require(not full,'JOURNAL');continue
            row=meta[name];sequence+=1;require(set(row)=={'phase','event','sequence','elapsed_ns'} and row['phase']==phase and row['event']==event and type(row['sequence']) is int and row['sequence']==sequence and type(row['elapsed_ns']) is int and last<=row['elapsed_ns']<=360000000000,'JOURNAL');last=row['elapsed_ns']
            if event=='started':started[phase]=last
            else:require(phase in started and last-started[phase]<=budget*1000000000,'JOURNAL')
            if report:require(report['journals'].get(name)==obs['meta'][name],'JOURNAL')
    if report:require(report['marker']==obs['meta']['marker.json'],'JOURNAL');require(set(report['journals'])==set(meta)-{'marker.json','report.json'},'JOURNAL')
    if full:
        require(sequence==6 and receipt['rc']==0 and receipt['reason'] is None and receipt['seconds']<=360 and report['phase']=='finalize' and report['reason'] is None,'JOURNAL')
        duration=report['elapsed_ns'];require(type(duration) is int and last<=duration<=360000000000 and duration-last<=10000000000 and duration<=int(receipt['seconds']*1000000000),'JOURNAL')
    else:require(receipt['rc']!=0 or receipt['reason'] is not None,'BINDING')
    now=current_inputs(c,until);historical=readjson(c['c1b']['path'],c['c1b']['sha256'],until);allowed={};source={}
    for arm in ['control','candidate']:
        entries={};folded=set()
        for item in historical['files']:
            if item['scope'] in ['common',arm]:
                name=safe(item['dest']);require(name not in entries and name.lower() not in folded,'PATH');entries[name]=item;folded.add(name.lower())
        source[arm]=entries
        for name,item in entries.items():allowed['work/'+arm+'/root/'+name]=item
    for item in c['tool_files']:name='tools/AddonBuilder/'+safe(item['dest']);require(name not in allowed,'PATH');allowed[name]=item
    require(c['fixed_destinations']=={'include':'fixed/include.lst','exclude':'fixed/exclude.lst','preflight':'fixed/preflight-local.py'},'SCHEMA')
    for key,name in c['fixed_destinations'].items():allowed[name]=c[key]
    if full:
        require(set(report['rows']['source'])==set(source)==set(report['rows']['work']),'SCHEMA')
        for arm,entries in source.items():require(set(report['rows']['source'][arm])==set(entries)==set(report['rows']['work'][arm]),'SCHEMA')
        require(set(report['rows']['fixed'])=={n for n in allowed if not n.startswith('work/')},'SCHEMA')
    entire={**allowed,**{'meta/'+name:v for name,v in obs['meta'].items()}};found=walk(root,entire,until,full)
    for arm,table in source.items():
        source_root=Path(c['source_stage'])/arm/'root';walk(source_root,table,until)
        for name,item in table.items():
            row=checkfile(source_root/name,item,134217728 if name.lower().endswith('.wrp') else 67108864,until)
            if full:require(row==report['rows']['source'][arm][name],'IDENTITY')
    for name in sorted(found-set('meta/'+n for n in obs['meta'])):
        row=checkfile(root/name,{'bytes':allowed[name]['bytes'],'sha256':allowed[name]['sha256']},134217728 if name.lower().endswith('.wrp') else 67108864,until)
        if full:
            if name.startswith('work/'):
                bits=name.split('/');want=report['rows']['work'][bits[1]]['/'.join(bits[3:])]
            else:want=report['rows']['fixed'][name]
            require(row==want,'IDENTITY')
    if full:
        require(now==report['rows']['inputs'],'IDENTITY');actual=profiles(c,until);require(actual==report['rows']['profile_before']==report['rows']['profile_after'],'PROFILE_CHANGED');require(current_inputs(c,until)==now,'IDENTITY')
    return {'status':'VERIFIED_PREPARED_PAIR_BYTES_ONLY' if full else 'INCONCLUSIVE_PREPARATION','contract_sha256':pin,'files':len(found),'claims':c['claims']}
def main():
    a=argparse.ArgumentParser();a.add_argument('--contract',required=True);a.add_argument('--sha',required=True);a.add_argument('--observation',required=True);a.add_argument('--observation-sha',required=True);a.add_argument('--output',required=True);v=a.parse_args();until=time.monotonic()+180
    try:r=consume(readjson(v.contract,v.sha,until),v.sha,readjson(v.observation,v.observation_sha,until,'OBSERVATION_PIN'),until);rc=0 if r['status'].startswith('VERIFIED') else 2
    except OSError as e:r={'status':'IO_INCONCLUSIVE','reason':type(e).__name__+':'+str(e)};rc=2
    except (Reject,KeyError,ValueError,TypeError) as e:r={'status':'REJECTED','reason':str(e)};rc=1
    data=(json.dumps(r,sort_keys=True)+'\n').encode();require(len(data)<=33554432,'CAP')
    with Path(v.output).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    print(data.decode().strip());return rc
if __name__=='__main__':sys.exit(main())
