"""One consumed compile probe, no semantic WRP acceptance."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,stat,subprocess,sys,time,xml.etree.ElementTree as ET
sys.path.insert(0,'E:/DayZ-Baltic-Build/shape-repair-20261025/dry-road-build-dependencies-20261028')
import psutil

class Stop(Exception):pass
def need(x,code):
    if not x:raise Stop(code)
def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);b=json.dumps(v,indent=2).encode();need(len(b)<=33554432,'METADATA_CAP')
    with p.open('wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def guard(p):
    p=Path(p)
    for q in [p,*p.parents]:
        s=q.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&1024,'REPARSE')
def ident(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def read_hash(p,cap=67108864,deadline=float('inf'),copy=None):
    p=Path(p);guard(p);pre=ident(p.stat());need(pre[2]<=cap,'FILE_CAP');h=hashlib.sha256();n=0;out=None
    try:
        if copy is not None:copy.parent.mkdir(parents=True,exist_ok=True);guard(copy.parent);out=copy.open('xb')
        with p.open('rb') as f:
            need(ident(os.fstat(f.fileno()))==pre,'IDENTITY')
            while True:
                need(time.monotonic()<deadline,'BUDGET');b=f.read(min(1048576,cap-n+1))
                if not b:break
                n+=len(b);need(n<=cap,'FILE_CAP');h.update(b)
                if out:need(out.write(b)==len(b),'WRITE')
            need(ident(os.fstat(f.fileno()))==pre,'IDENTITY')
        guard(p);need(ident(p.stat())==pre and n==pre[2],'IDENTITY')
        if out:out.flush();os.fsync(out.fileno())
    finally:
        if out:out.close()
    return {'path':str(p),'bytes':n,'sha256':h.hexdigest(),'identity':pre}
def pincheck(record,deadline=float('inf')):
    got=read_hash(record['path'],max(record['bytes'],1),deadline);need((got['bytes'],got['sha256'])==(record['bytes'],record['sha256']),'PIN');return got
def load(p,pin):
    p=Path(p);need(p.stat().st_size<=33554432,'METADATA_CAP');b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==pin,'CONTRACT_PIN');return json.loads(b)
def logger_bytes(raw,paths):
    tree=ET.fromstring(raw);nodes=tree.findall('./appender/file');need(len(nodes)==3 and len(paths)==3,'LOGGER_DELTA')
    # Byte replacements preserve every token except the three file values.
    out=raw
    for node,dest in zip(nodes,paths):
        before=node.attrib['value'].encode();need(out.count(before)==1,'LOGGER_DELTA');out=out.replace(before,str(dest).encode())
    a=ET.fromstring(raw);b=ET.fromstring(out)
    for x,y in zip(a.findall('./appender/file'),b.findall('./appender/file')):y.attrib['value']=x.attrib['value']
    need(ET.tostring(a)==ET.tostring(b),'LOGGER_DELTA');return out
def verify_logger(raw,candidate,paths):
    need(candidate==logger_bytes(raw,paths),'LOGGER_DELTA')
def profile_snapshot(roots):
    rows=[];count=0;total=0
    for root in map(Path,roots):
        if not root.exists():continue
        guard(root)
        for app in root.glob('AddonBuilder*'):
            stack=[app]
            while stack:
                p=stack.pop();guard(p);count+=1;need(count<=256,'PROFILE_CAP')
                if p.is_dir():stack.extend(p.iterdir())
                elif p.name=='user.config':
                    row=read_hash(p,4194304);total+=row['bytes'];need(total<=16777216,'PROFILE_CAP');rows.append(row)
    return rows
def proc_run(command,cwd,out,seconds,rss_cap,diskroot=None,env_extra=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);started=time.time();tick=time.monotonic();owned={};images={};reason=None;peak=0;disk_peak=0
    env=os.environ.copy();env.update(env_extra or {});env.pop('PWD',None)
    def live():
        result=[]
        for pid,birth in list(owned.items()):
            try:
                p=psutil.Process(pid)
                if p.create_time()==birth and p.is_running():result.append(p)
            except psutil.NoSuchProcess:pass
        return result
    with (out/'stdout').open('wb') as stdout,(out/'stderr').open('wb') as stderr:
        child=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,creationflags=0x08000000)
        try:p=psutil.Process(child.pid);owned[p.pid]=p.create_time()
        except psutil.NoSuchProcess:pass
        dump(out/'running.json',{'pid':child.pid,'birth':owned.get(child.pid),'started':started,'command':command,'budget':seconds})
        next_disk=0
        try:
            while True:
                for p in live():
                    try:
                        for q in p.children(recursive=True):owned[q.pid]=q.create_time()
                    except (psutil.NoSuchProcess,psutil.AccessDenied):pass
                now=live();rss=0
                for p in now:
                    try:
                        rss+=p.memory_info().rss
                        if p.pid not in images:
                            exe=p.exe();args=p.cmdline();r=read_hash(exe);images[p.pid]={'pid':p.pid,'birth':owned[p.pid],'exe':exe,'argv':args,'observed_at':time.time(),'image_path_sha256':r['sha256'],'image_identity':r['identity']}
                    except (psutil.NoSuchProcess,psutil.AccessDenied,OSError,Stop):pass
                peak=max(peak,rss);elapsed=time.monotonic()-tick
                if elapsed>seconds:reason='TIMEOUT';break
                if rss>rss_cap:reason='MEMORY_LIMIT';break
                if diskroot and elapsed>=next_disk:
                    count=0;size=0
                    roots=diskroot if isinstance(diskroot,list) else [diskroot]
                    for base in roots:
                        for p in Path(base).rglob('*'):
                            count+=1;need(count<=32768,'OUTPUT_ENTRY_CAP')
                            if p.is_file():
                                amount=p.stat().st_size;size+=amount
                                if Path(base).name in ('help','control','candidate') and Path(base).parent.name=='logs':need(amount<=33554432,'LOG_LIMIT')
                    disk_peak=max(disk_peak,size);next_disk=elapsed+1
                    if size>2147483648:reason='DISK_LIMIT';break
                if any((out/n).stat().st_size>33554432 for n in ['stdout','stderr']):reason='LOG_LIMIT';break
                if child.poll() is not None and not now:break
                time.sleep(.15)
        except Exception as e:reason='MONITOR_ERROR:'+type(e).__name__
        finally:
            # Stop the owned root first; never match by executable name.
            for pid in [child.pid,*reversed(list(owned))]:
                if pid not in owned:continue
                try:
                    p=psutil.Process(pid)
                    if p.create_time()==owned[pid] and p.is_running():p.kill()
                except psutil.NoSuchProcess:pass
            child.wait(timeout=5)
    r={'rc':child.returncode,'reason':reason,'started':started,'finished':time.time(),'seconds':time.monotonic()-tick,'peak_rss':peak,'observed_disk_peak':disk_peak,'identities':owned,'observed_processes':list(images.values()),'command':command,'cwd':str(cwd),'stdout':read_hash(out/'stdout',33554432),'stderr':read_hash(out/'stderr',33554432),'sampling_seconds':.15,'loaded_image_attestation':False}
    dump(out/'completion.json',r);return r
def snapshot_logs(folder,receipt):
    paths=[Path(receipt[k]['path']) for k in ['stdout','stderr']]+sorted(p for p in Path(folder).iterdir() if p.is_file());need(len(paths)<=64,'LOG_COUNT')
    until=time.monotonic()+5;previous=None
    while True:
        state=[(str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in paths]
        if state==previous:break
        need(time.monotonic()<until,'LOG_UNSTABLE');previous=state;time.sleep(.15)
    return [read_hash(p,33554432) for p in paths]
def gate(receipt,logs,wrps,binarize_sha,allowed_images,help_mode=False):
    if receipt['reason']:return receipt['reason']
    if receipt['rc']!=0:return 'PROCESS_REJECTED'
    if not any(Path(r['path']).suffix=='.rpt' for r in logs):return 'LOG_NOT_OBSERVED'
    marker=False;syntax=False;tools_flag=False
    for r in logs:
        if not(receipt['started']<=r['identity'][3]/1e9<=receipt['finished']):return 'LOG_WINDOW'
        pincheck(r);text=Path(r['path']).read_text(encoding='utf-8',errors='replace')
        if re.search(r'\b(?:ERROR|FATAL)\b',text,re.I):return 'LOG_ERROR'
        marker=marker or 'Build Successful' in text;syntax=syntax or 'SYNTAX' in text;tools_flag=tools_flag or '-toolsDirectory' in text
    if help_mode:return 'HELP_OBSERVED' if syntax and tools_flag else 'NO_HELP'
    if not marker:return 'NO_MARKER'
    observed=receipt['observed_processes']
    if any(r['image_path_sha256'] not in allowed_images for r in observed):return 'UNEXPECTED_CHILD'
    if not any(r['image_path_sha256']==binarize_sha for r in observed):return 'PROBE_INCONCLUSIVE_NOT_OBSERVED'
    if len(wrps)!=1:return 'WRP_COUNT'
    p=Path(wrps[0]);r=read_hash(p,134217728)
    if not(receipt['started']<=r['identity'][3]/1e9<=receipt['finished']):return 'ARTIFACT_WINDOW'
    with p.open('rb') as f:b=f.read(8)
    return 'ARTIFACT_OBSERVED_ONLY' if len(b)==8 and b[:4]==b'OPRW' else 'WRP_MAGIC'
def expected(c):
    old=load(c['c1b']['path'],c['c1b']['sha256']);return {arm:{e['dest']:(e['bytes'],e['sha256']) for e in old['files'] if e['scope'] in ('common',arm)} for arm in ['control','candidate']}
def trees(c,targets,deadline):
    ex=expected(c);rows=[]
    for target in targets:
        for arm in ['control','candidate']:
            base=Path(target)/arm/'root';seen=set();seen_dirs=set();guard(base)
            for p in base.rglob('*'):
                need(time.monotonic()<deadline,'BUDGET');guard(p)
                if p.is_file():
                    rel=p.relative_to(base).as_posix();need(rel in ex[arm],'EXTRA');r=read_hash(p,ex[arm][rel][0],deadline);need((r['bytes'],r['sha256'])==ex[arm][rel],'SOURCE_CHANGED');seen.add(rel)
                elif p.is_dir():seen_dirs.add(p.relative_to(base).as_posix())
            need(seen==set(ex[arm]),'MISSING');rows.append({'tree':str(base),'files':len(seen)})
            wanted_dirs={p.as_posix() for name in ex[arm] for p in Path(name).parents if str(p)!='.'};need(seen_dirs==wanted_dirs,'EXTRA')
    return rows
def mainrun(c,pin):
    root=Path(c['root']);need(not root.exists(),'EXISTS');guard(root.parent);need(shutil.disk_usage(root.parent).free>3221225472,'DISK_FREE');root.mkdir();dump(root/'consumed.json',{'contract_sha256':pin,'started':time.time(),'no_retries':True});begin=time.monotonic();deadline=begin+c['caps']['total_seconds'];report={'contract_sha256':pin,'status':'IN_PROGRESS','claims':c['claims'],'phases':{}}
    def save():dump(root/'report.json',report)
    try:
        report['profile_before']=profile_snapshot(c['profile_roots']);until=time.monotonic()+180;work=root/'work'
        for arm,files in expected(c).items():
            for rel,(size,h) in files.items():
                source=Path(c['source_stage'])/arm/'root'/rel;dest=work/arm/'root'/rel;r=read_hash(source,size,until,dest);need(r['sha256']==h,'SOURCE_CHANGED');need(read_hash(dest,size,until)['sha256']==h,'WRITE')
        portable=root/'tools/AddonBuilder'
        for row in c['tool_files']:
            pincheck(row,until);r=read_hash(row['path'],67108864,until,portable/row['dest']);need(r['sha256']==row['sha256'],'PIN')
        for row in c['tools'].values():pincheck(row,until)
        for k in ['include','exclude','preflight','preflight_original']:pincheck(c[k],until)
        report['copy_seconds']=time.monotonic()-begin;need(report['copy_seconds']<=180,'BUDGET');save()
        py=sys.executable;pre=proc_run([py,'-I','-X','utf8',c['preflight']['path']],root,root/'preflight',60,268435456);report['phases']['preflight']=pre;save();need(pre['rc']==0 and pre['reason'] is None,'PREFLIGHT')
        exe=portable/'AddonBuilder.exe';raw=(portable/'logger.xml').read_bytes();need(hashlib.sha256(raw).hexdigest()==next(x['sha256'] for x in c['tool_files'] if x['dest']=='logger.xml'),'PIN')
        def launch(phase,args,seconds,rss,output=None):
            logdir=root/'logs'/phase;logdir.mkdir(parents=True);paths=[logdir/n for n in ['AddonBuilder.rpt','AddonBuilderProcess.rpt','AddonBuilder.User.rpt']];lb=logger_bytes(raw,paths);(portable/'logger.xml').write_bytes(lb)
            env={n:str(root/'profile'/phase/n) for n in ['APPDATA','LOCALAPPDATA','TEMP','TMP']}
            for v in env.values():Path(v).mkdir(parents=True)
            remain=deadline-time.monotonic();need(remain>=seconds,'TOTAL_BUDGET')
            receipt=proc_run([str(exe),*args],portable,root/'process'/phase,seconds,rss,[output,logdir] if output else [logdir],env);logs=snapshot_logs(logdir,receipt);return receipt,logs,hashlib.sha256(lb).hexdigest()
        helper,logs,lh=launch('help',['-help','-toolsDirectory='+c['tool_root']],30,536870912);st=gate(helper,logs,[],c['tools']['binarize']['sha256'],[],True);report['phases']['help']={'receipt':helper,'logs':logs,'logger_sha256':lh,'status':st};save();need(st=='HELP_OBSERVED',st)
        allowed={row['sha256'] for key,row in c['tools'].items() if key in ['binarize','cfgConvert','fileBank']}|{next(x['sha256'] for x in c['tool_files'] if x['dest']=='AddonBuilder.exe')}
        for arm in ['control','candidate']:
            tick=time.monotonic();out=root/'output'/arm;out.mkdir(parents=True);(out/'out').mkdir();project=work/arm/'root';src=project/c['prefix']
            args=[str(src),str(out/'out'),'-prefix='+c['prefix'].replace('/','\\'),'-project='+str(project),'-temp='+str(out/'temp'),'-include='+c['include']['path'],'-exclude='+c['exclude']['path'],'-binarizeFullLogs','-toolsDirectory='+c['tool_root']]+['-'+k+'='+c['tools'][k]['path'] for k in ['binarize','cfgConvert','fileBank','dsSignFile']]
            receipt,logs,lh=launch(arm,args,300,2147483648,out);wrps=list((out/'temp').rglob('*.wrp')) if (out/'temp').exists() else [];st=gate(receipt,logs,wrps,c['tools']['binarize']['sha256'],allowed)
            artifacts=[]
            for p in wrps[:2]:
                a=read_hash(p,134217728)
                with p.open('rb') as f:a['header_hex']=f.read(8).hex()
                artifacts.append(a)
            report['phases'][arm]={'status':st,'receipt':receipt,'logs':logs,'logger_sha256':lh,'artifacts':artifacts,'argv_binding':'OBSERVED_NOT_INTERPRETED'};save()
            need(st=='ARTIFACT_OBSERVED_ONLY',st)
            # Full gates are inside the arm envelope, before authorizing the next arm.
            trees(c,[c['source_stage']],min(tick+300,deadline))
            try:trees(c,[work],min(tick+300,deadline))
            except Stop as e:raise Stop('WORK_INPUT_MUTATED:'+str(e))
            for row in c['tools'].values():pincheck(row,min(tick+300,deadline))
            for row in c['tool_files']:pincheck(row,min(tick+300,deadline))
            need(time.monotonic()-tick<=300,'ARM_BUDGET')
        report['status']='COMPILE_PROBE_OBSERVED_ONLY'
    except (Stop,OSError) as e:report['status']='PROBE_STOPPED';report['reason']=str(e)
    finally:
        try:report['profile_after']=profile_snapshot(c['profile_roots'])
        except Exception as e:report['profile_after_error']=type(e).__name__
        report['seconds']=time.monotonic()-begin;save()
    return report
def main():
    a=argparse.ArgumentParser();a.add_argument('--contract',required=True);a.add_argument('--sha',required=True);x=a.parse_args();c=load(x.contract,x.sha);need(c['schema']=='road-c1c-probe.v1','SCHEMA');r=mainrun(c,x.sha);print(json.dumps({'status':r['status'],'reason':r.get('reason'),'seconds':r['seconds']}));return 0 if r['status']=='COMPILE_PROBE_OBSERVED_ONLY' else 2
if __name__=='__main__':sys.exit(main())
