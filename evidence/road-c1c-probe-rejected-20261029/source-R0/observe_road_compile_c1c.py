"""Read only artifact and input observer; not a terrain decoder."""
from pathlib import Path
import argparse,hashlib,json,os,re,stat,sys,time
class Reject(Exception):pass
def require(x,s):
    if not x:raise Reject(s)
def pathcheck(p):
    p=Path(p)
    while True:
        s=p.lstat();require(not stat.S_ISLNK(s.st_mode) and not(getattr(s,'st_file_attributes',0)&1024),'REPARSE')
        if p.parent==p:break
        p=p.parent
def fileid(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
def checkfile(p,expected=None,cap=134217728,until=float('inf')):
    p=Path(p);pathcheck(p);before=fileid(p.stat());require(before[2]<=cap,'SIZE');h=hashlib.sha256();size=0
    with p.open('rb') as f:
        require(fileid(os.fstat(f.fileno()))==before,'IDENTITY')
        while True:
            require(time.monotonic()<until,'BUDGET');b=f.read(min(524288,cap-size+1))
            if not b:break
            size+=len(b);require(size<=cap,'SIZE');h.update(b)
        require(fileid(os.fstat(f.fileno()))==before,'IDENTITY')
    pathcheck(p);require(fileid(p.stat())==before and size==before[2],'IDENTITY');digest=h.hexdigest()
    if expected:require((size,digest)==(expected['bytes'],expected['sha256']),'ARTIFACT_PIN')
    return {'bytes':size,'sha256':digest,'mtime':before[3]/1e9}
def readjson(p,pin):
    r=checkfile(p,cap=33554432);require(r['sha256']==pin,'PIN');b=Path(p).read_bytes();require(hashlib.sha256(b).hexdigest()==pin,'PIN');return json.loads(b)
def stage_check(base,expected,until):
    base=Path(base);pathcheck(base);files=set();dirs=set()
    for folder,subdirs,names in os.walk(base,followlinks=False):
        for name in subdirs:pathcheck(Path(folder)/name);dirs.add((Path(folder)/name).relative_to(base).as_posix())
        for name in names:
            p=Path(folder)/name;rel=p.relative_to(base).as_posix();require(rel in expected,'EXTRA');size,digest=expected[rel];checkfile(p,{'bytes':size,'sha256':digest},size,until);files.add(rel)
    require(files==set(expected),'MISSING');allowed=set()
    for key in files:
        p=Path(key).parent
        while str(p)!='.':allowed.add(p.as_posix());p=p.parent
    require(dirs==allowed,'EXTRA');return len(files)
def arm_check(c,phase,arm='control'):
    r=phase['receipt'];require(r['reason'] is None and r['rc']==0,'PROCESS_REJECTED');allowed={v['sha256'] for k,v in c['tools'].items() if k in ('binarize','cfgConvert','fileBank')};allowed.add(next(v['sha256'] for v in c['tool_files'] if v['dest']=='AddonBuilder.exe'))
    processes=r['observed_processes'];require(all(p['image_path_sha256'] in allowed for p in processes),'UNEXPECTED_CHILD');require(any(p['image_path_sha256']==c['tools']['binarize']['sha256'] for p in processes),'PROBE_INCONCLUSIVE_NOT_OBSERVED')
    for p in processes:
        require(str(p['pid']) in r['identities'] and r['identities'][str(p['pid'])]==p['birth'] and r['started']<=p['birth']<=p['observed_at']<=r['finished'],'PROCESS_WINDOW')
        q=checkfile(p['exe'],cap=67108864);require(q['sha256']==p['image_path_sha256'],'IMAGE_CHANGED')
    marker=False;private=False;root=Path(c['root']);allowed_logs={root/'process'/arm/n for n in ['stdout','stderr']};logdir=root/'logs'/arm;actual_logs={p for p in logdir.iterdir() if p.is_file()} if logdir.exists() else set();require(len(actual_logs)<=62,'LOG_COUNT');allowed_logs|=actual_logs
    require({Path(log['path']) for log in phase['logs']}==allowed_logs,'LOG_BINDING')
    for log in phase['logs']:
        now=checkfile(log['path'],log,33554432);require(r['started']<=now['mtime']<=r['finished'],'LOG_WINDOW');private=private or Path(log['path']).suffix=='.rpt';text=Path(log['path']).read_text(encoding='utf-8',errors='replace');require(not re.search(r'\b(ERROR|FATAL)\b',text,re.I),'LOG_ERROR');marker=marker or 'Build Successful' in text
    require(private,'LOG_NOT_OBSERVED');require(marker,'NO_MARKER');require(len(phase['artifacts'])==1,'WRP_COUNT');a=phase['artifacts'][0]
    wrps=list((root/'output'/arm/'temp').rglob('*.wrp'));require(len(wrps)==1 and Path(a['path'])==wrps[0],'WRP_COUNT')
    q=checkfile(a['path'],a);require(r['started']<=q['mtime']<=r['finished'],'ARTIFACT_WINDOW')
    with open(a['path'],'rb') as f:header=f.read(8)
    require(len(header)==8 and header[:4]==b'OPRW','WRP_MAGIC');require(header.hex()==a['header_hex'],'ARTIFACT_PIN')
    return {'path':a['path'],'sha256':q['sha256'],'bytes':q['bytes'],'raw_header_hex':header.hex(),'semantic_status':'NOT_EVALUATED'}
def observe(c,r,until):
    findings=[];arms={};input_rows=[];old=readjson(c['c1b']['path'],c['c1b']['sha256']);root=Path(c['root'])
    for role,target in [('SEALED_SOURCE',Path(c['source_stage'])),('WORK',root/'work')]:
        for arm in ['control','candidate']:
            expected={x['dest']:(x['bytes'],x['sha256']) for x in old['files'] if x['scope'] in ('common',arm)}
            try:input_rows.append({'kind':role,'arm':arm,'files':stage_check(target/arm/'root',expected,until),'state':'MATCH'})
            except (Reject,OSError) as e:findings.append({'kind':role,'arm':arm,'error':str(e)});input_rows.append({'kind':role,'arm':arm,'state':'NOT_MATCHED'})
    for item in [*c['tool_files'],*c['tools'].values(),c['include'],c['exclude'],c['preflight_original']]:
        try:checkfile(item['path'],item,67108864,until)
        except (Reject,OSError) as e:findings.append({'kind':'INSTALLED_OR_FIXED_INPUT','path':item['path'],'error':str(e)})
    for arm in ['control','candidate']:
        if arm not in r['phases']:arms[arm]={'status':'NOT_LAUNCHED'};continue
        try:arms[arm]={'status':'ARTIFACT_OBSERVED_ONLY','artifact':arm_check(c,r['phases'][arm],arm)}
        except (Reject,OSError) as e:arms[arm]={'status':'NOT_VERIFIED','reason':str(e)}
    complete=not findings and all(x['status']=='ARTIFACT_OBSERVED_ONLY' for x in arms.values())
    require(not complete or r['status']=='COMPILE_PROBE_OBSERVED_ONLY','REPORT_STATUS')
    return {'status':'VERIFIED_COMPILE_PROBE_ONLY' if complete else 'INCONCLUSIVE_PROBE_DIAGNOSTIC','arms':arms,'inputs':input_rows,'findings':findings,'producer_status':r['status'],'producer_reason':r.get('reason'),'claims':c['claims'],'decoder':'NOT_IMPLEMENTED','continuous_identity':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--sha',required=True);p.add_argument('--report',required=True);p.add_argument('--report-sha',required=True);p.add_argument('--out',required=True);a=p.parse_args();start=time.monotonic()
    try:
        c=readjson(a.contract,a.sha);r=readjson(a.report,a.report_sha);require(r['contract_sha256']==a.sha,'BINDING');result=observe(c,r,start+120);result['report_sha256']=a.report_sha;result['contract_sha256']=a.sha;result['seconds']=time.monotonic()-start;b=json.dumps(result,indent=2).encode();require(len(b)<=33554432,'OUTPUT_CAP')
        with open(a.out,'xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
        print(json.dumps({'status':result['status'],'arms':result['arms']}));return 0 if result['status'].startswith('VERIFIED') else 2
    except (Reject,OSError) as e:print('REJECTED:'+str(e));return 3
if __name__=='__main__':sys.exit(main())
