from pathlib import Path
import json,time,hashlib
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c1-local-author-20261101';B=R/'road-c1c-local-author-20261029';start=json.loads((D/'author-start.json').read_bytes())['started'];assert time.time()-start<600
approval=json.loads((B/'approval.json').read_bytes())
for n in ['probe_road_compile_c1c.py','observe_road_compile_c1c.py','test_probe_road_compile_c1c.py']:assert hashlib.sha256((B/n).read_bytes()).hexdigest()==approval['files'][n]
s=(B/'probe_road_compile_c1c.py').read_text();s=s.replace("'REPARSE')","'REPARSE:'+str(q))",1)
addition='''def canonical_check(c):
    spec=c['canonical_preflight'];alias=spec['alias'];p=Path(alias['path']);s=p.lstat()
    need((s.st_dev,s.st_ino,getattr(s,'st_reparse_tag',0),os.readlink(p))==(alias['dev'],alias['ino'],alias['tag'],alias['target']),'ALIAS_CHANGED')
    need(p.resolve(strict=True)==Path(spec['file']['path']).parent,'ALIAS_CHANGED')
    for row in spec['ancestors']:
        q=Path(row['path']);s=q.lstat();need(not getattr(s,'st_file_attributes',0)&1024 and not stat.S_ISLNK(s.st_mode),'REPARSE:'+str(q))
        need((s.st_dev,s.st_ino,q.is_dir())==(row['dev'],row['ino'],row['is_dir']),'CANONICAL_IDENTITY:'+str(q))
    result=pincheck(spec['file']);need(result['identity']==spec['file']['identity'],'CANONICAL_IDENTITY')
    for row in spec['ancestors']:
        q=Path(row['path']);s=q.lstat();need(not getattr(s,'st_file_attributes',0)&1024 and (s.st_dev,s.st_ino)==(row['dev'],row['ino']),'CANONICAL_IDENTITY:'+str(q))
    z=p.lstat();need((z.st_dev,z.st_ino,getattr(z,'st_reparse_tag',0),os.readlink(p))==(alias['dev'],alias['ino'],alias['tag'],alias['target']),'ALIAS_CHANGED')
    return result
def native_graph(c,r):
    identities={str(k):v for k,v in r['identities'].items()};nodes={str(p['pid']):p for p in r['observed_processes']};need(set(nodes)==set(identities),'PROBE_INCONCLUSIVE_NOT_OBSERVED');root=str(r['root_pid']);need(root in nodes and identities[root]==r['root_birth'],'PROCESS_PARENT')
    for key,p in nodes.items():
        need(p['birth']==identities[key] and r['started']<=p['birth']<=p['observed_at']<=r['finished'],'PROCESS_WINDOW')
        if key!=root:
            parent=str(p.get('parent_pid'));need(parent in nodes and p.get('parent_birth')==identities[parent] and identities[parent]<=p['birth'],'PROCESS_PARENT')
            seen={key};cursor=parent
            while cursor!=root:
                need(cursor not in seen,'PROCESS_PARENT');seen.add(cursor);cursor=str(nodes[cursor].get('parent_pid'));need(cursor in nodes,'PROCESS_PARENT')
        helper=c.get('os_helper')
        if helper and p['image_path_sha256']==helper['sha256']:
            args=p['argv'];need(key!=root and p['exe'].casefold()==helper['path'].casefold(),'PROCESS_PARENT')
            need(len(args)==2 and args[0].replace('\\\\??\\\\','',1).casefold()==helper['path'].casefold() and re.fullmatch(r'0x[0-9a-fA-F]+',args[1]) is not None,'OS_HELPER_ARGV')

'''
s=s.replace('def mainrun(c,pin):',addition+'def mainrun(c,pin):')
s=s.replace("exe=p.exe();args=p.cmdline();r=read_hash(exe);images[p.pid]={'pid':p.pid,", "exe=p.exe();args=p.cmdline();r=read_hash(exe);parent_pid=p.ppid();parent_birth=owned.get(parent_pid);images[p.pid]={'parent_pid':parent_pid,'parent_birth':parent_birth,'pid':p.pid,")
s=s.replace("r={'rc':child.returncode", "r={'root_pid':child.pid,'root_birth':owned.get(child.pid),'rc':child.returncode")
s=s.replace("need(len(roots)==1 and roots[0]['argv']==receipt['command'],'ARG_BINDING')", "need(len(roots)==1 and roots[0]['argv']==receipt['command'] and roots[0]['pid']==receipt['root_pid'],'ARG_BINDING');native_graph(c,receipt)")
s=s.replace("report['profile_before']=profile_snapshot", "canonical_check(c);pincheck(c['os_helper']);report['profile_before']=profile_snapshot")
s=s.replace("trees(c,[c['source_stage']],until)\n        for arm", "trees(c,[c['source_stage']],until);report['checkpoints']={'source_checked':time.time()};save()\n        for arm")
s=s.replace("portable=root/'tools/AddonBuilder'", "report['checkpoints']['copy_complete']=time.time();save()\n        portable=root/'tools/AddonBuilder'")
oldline=next(x for x in s.splitlines() if x.strip().startswith('py=sys.executable;pre='))
new='''        report['checkpoints']['fixed_inputs']=time.time();save();canonical_check(c)
        py=sys.executable;pre_cmd=[py,'-I','-X','utf8',c['preflight']['path']];mark={'state':'STARTED','phase':'preflight','command':pre_cmd,'time':time.time()};dump(root/'phases/preflight.started.json',mark);report['phases']['preflight']={'state':'STARTED','start':mark};save()
        pre=proc_run(pre_cmd,root,root/'preflight',60,268435456);pre['state']='CLOSED';pre['start']=mark;dump(root/'phases/preflight.closed.json',pre);report['phases']['preflight']=pre;save();need(pre['rc']==0 and pre['reason'] is None,'PREFLIGHT')'''
s=s.replace(oldline,new)
oldline=next(x for x in s.splitlines() if x.strip().startswith('logdir=root/'))
new='''            canonical_check(c);pincheck(c['os_helper']);logdir=root/'logs'/phase;logdir.mkdir(parents=True);paths=[logdir/n for n in ['AddonBuilder.rpt','AddonBuilderProcess.rpt','AddonBuilder.User.rpt']];lb=logger_bytes(raw,paths)
            mark={'state':'STARTED','phase':phase,'command':[str(exe),*args],'logger_sha256':hashlib.sha256(lb).hexdigest(),'time':time.time()};dump(root/'phases'/(phase+'.started.json'),mark);report['phases'][phase]={'state':'STARTED','start':mark};save();(portable/'logger.xml').write_bytes(lb)'''
s=s.replace(oldline,new)
s=s.replace("return receipt,logs,hashlib.sha256(lb).hexdigest()", "return receipt,logs,hashlib.sha256(lb).hexdigest(),mark")
s=s.replace("helper,logs,lh=launch", "helper,logs,lh,mark=launch").replace("receipt,logs,lh=launch", "receipt,logs,lh,mark=launch")
s=s.replace("if x['dest']=='AddonBuilder.exe')},True)", "if x['dest']=='AddonBuilder.exe'),c['os_helper']['sha256']},True)")
s=s.replace("report['phases']['help']={'receipt':helper,", "report['phases']['help']={'state':'CLOSED','start':mark,'receipt':helper,")
s=s.replace("'status':st};save();need(st=='HELP_OBSERVED'", "'status':st};dump(root/'phases/help.closed.json',report['phases']['help']);save();need(st=='HELP_OBSERVED'")
s=s.replace("if x['dest']=='AddonBuilder.exe')}\n        for arm", "if x['dest']=='AddonBuilder.exe'),c['os_helper']['sha256']}\n        for arm")
s=s.replace("report['phases'][arm]={'status':st", "report['phases'][arm]={'state':'CLOSED','start':mark,'status':st")
s=s.replace("'argv_binding':'OBSERVED_NOT_INTERPRETED'};save()", "'argv_binding':'OBSERVED_NOT_INTERPRETED'};dump(root/'phases'/(arm+'.closed.json'),report['phases'][arm]);save()")
s=s.replace("c['schema']=='road-c1c-probe.v1'", "c['schema']=='road-c1c1-probe.v1'")
(D/'probe_road_compile_c1c1.py').write_text(s,encoding='utf-8')
v=(B/'observe_road_compile_c1c.py').read_text()
insert='''def canonical(c):
    spec=c['canonical_preflight'];link=spec['alias'];p=Path(link['path']);a=p.lstat();require((a.st_dev,a.st_ino,getattr(a,'st_reparse_tag',0),os.readlink(p))==(link['dev'],link['ino'],link['tag'],link['target']),'ALIAS_CHANGED');require(p.resolve()==Path(spec['file']['path']).parent,'ALIAS_CHANGED')
    for item in spec['ancestors']:
        q=Path(item['path']);pathcheck(q);z=q.lstat();require((z.st_dev,z.st_ino,q.is_dir())==(item['dev'],item['ino'],item['is_dir']),'CANONICAL_IDENTITY')
    checkfile(spec['file']['path'],spec['file'],16384);require(list(fileid(Path(spec['file']['path']).stat()))==spec['file']['identity'],'CANONICAL_IDENTITY')
    for item in spec['ancestors']:
        q=Path(item['path']);pathcheck(q);z=q.lstat();require((z.st_dev,z.st_ino)==(item['dev'],item['ino']),'CANONICAL_IDENTITY')
    a=p.lstat();require((a.st_dev,a.st_ino,getattr(a,'st_reparse_tag',0),os.readlink(p))==(link['dev'],link['ino'],link['tag'],link['target']),'ALIAS_CHANGED')
def process_tree(c,r):
    rows=r['observed_processes'];byid={p['pid']:p for p in rows};root=r['root_pid'];require(root in byid and byid[root]['birth']==r['root_birth'],'PROCESS_PARENT')
    for p in rows:
        cursor=p;visited=set()
        while cursor['pid']!=root:
            require(cursor['pid'] not in visited,'PROCESS_PARENT');visited.add(cursor['pid']);parent=byid.get(cursor.get('parent_pid'));require(parent is not None and parent['birth']==cursor.get('parent_birth') and parent['birth']<=cursor['birth'],'PROCESS_PARENT');cursor=parent
        h=c.get('os_helper')
        if h and p['image_path_sha256']==h['sha256']:
            args=p['argv'];require(p['pid']!=root and p['exe'].casefold()==h['path'].casefold(),'PROCESS_PARENT');require(len(args)==2 and args[0].replace('\\\\??\\\\','',1).casefold()==h['path'].casefold() and re.fullmatch('0x[0-9a-fA-F]+',args[1]) is not None,'OS_HELPER_ARGV')
def phase_state(c,r,name):
    folder=Path(c['root'])/'phases';a=folder/(name+'.started.json');b=folder/(name+'.closed.json');entry=r['phases'].get(name)
    if not a.exists() and not b.exists() and entry is None:return 'NOT_LAUNCHED'
    require(a.is_file() and b.is_file() and entry is not None and entry['state']=='CLOSED','INCOMPLETE_PHASE')
    for p in [a,b]:checkfile(p,cap=33554432)
    start=json.loads(a.read_bytes());end=json.loads(b.read_bytes());require(start==entry['start'] and end==entry and start['state']=='STARTED' and start['phase']==name,'PHASE_BINDING')
    return 'CLOSED'
'''
v=v.replace('def verify_invocation(c,r,arm):',insert+'def verify_invocation(c,r,arm):')
v=v.replace("roots[0]['argv']==r['command'],'ARG_BINDING')", "roots[0]['argv']==r['command'] and roots[0]['pid']==r['root_pid'],'ARG_BINDING');process_tree(c,r)")
v=v.replace("require(raw==b,'LOGGER_DELTA')", "require(raw==b,'LOGGER_DELTA')")
v=v.replace("for node,name in zip(a.findall('./appender/file'),['AddonBuilder.rpt','AddonBuilderProcess.rpt','AddonBuilder.User.rpt']):raw=raw.replace(node.attrib['value'].encode(),str(root/'logs'/phase/name).encode())", "if phase is not None:\n                for node,name in zip(a.findall('./appender/file'),['AddonBuilder.rpt','AddonBuilderProcess.rpt','AddonBuilder.User.rpt']):raw=raw.replace(node.attrib['value'].encode(),str(root/'logs'/phase/name).encode())")
v=v.replace("allowed.add(next(v['sha256'] for v in c['tool_files'] if v['dest']=='AddonBuilder.exe'))", "allowed.add(next(v['sha256'] for v in c['tool_files'] if v['dest']=='AddonBuilder.exe'));allowed.update([c['os_helper']['sha256']] if c.get('os_helper') else [])")
v=v.replace("==next(v['sha256'] for v in c['tool_files'] if v['dest']=='AddonBuilder.exe') for p in processes", "in ({next(v['sha256'] for v in c['tool_files'] if v['dest']=='AddonBuilder.exe')}|({c['os_helper']['sha256']} if c.get('os_helper') else set())) for p in processes")
v=v.replace("findings=[];arms={};input_rows=[];", "findings=[];arms={};input_rows=[];canonical(c);")
v=v.replace("c['c1b_consumer']]:", "c['c1b_consumer'],c['os_helper']]:")
oldline=next(x for x in v.splitlines() if x.strip().startswith("phase=next((a for a in ['candidate'"))
v=v.replace(oldline,"""        states={a:phase_state(c,r,a) for a in ['preflight','help','control','candidate']};phase=next((a for a in ['candidate','control','help'] if states[a]!='NOT_LAUNCHED'),None);portable(c,phase)
        if states['help']=='CLOSED':arm_check(c,r['phases']['help'],'help')
        if states['preflight']=='CLOSED':require(r['phases']['preflight']['rc']==0 and r['phases']['preflight']['reason'] is None,'PREFLIGHT')""")
v=v.replace("if arm not in r['phases']:arms[arm]={'status':'NOT_LAUNCHED'};continue", "if arm not in r['phases'] and not (root/'phases'/(arm+'.started.json')).exists():arms[arm]={'status':'NOT_LAUNCHED'};continue\n        if r['phases'].get(arm,{}).get('state')!='CLOSED':arms[arm]={'status':'INCOMPLETE_PHASE'};continue")
(D/'observe_road_compile_c1c1.py').write_text(v,encoding='utf-8')
t=(B/'test_probe_road_compile_c1c.py').read_text().replace("A=mod('probe_road_compile_c1c');V=mod('observe_road_compile_c1c')", "A=mod('probe_road_compile_c1c1');V=mod('observe_road_compile_c1c1')")
t=t.replace("self.phase={'receipt':self.receipt", "self.receipt.update(root_pid=122,root_birth=now-1);self.receipt['observed_processes'][0].update(parent_pid=122,parent_birth=now-1)\n  self.phase={'receipt':self.receipt")
t=t.replace("with patch.object(A,'expected',", "with patch.object(A,'canonical_check'),patch.object(A,'expected',")
t=t.replace("'c1b_consumer':row(pre),", "'c1b_consumer':row(pre),'os_helper':row(self.image),")
(D/'test_probe_road_compile_c1c1.py').write_text(t,encoding='utf-8')
print(json.dumps({'code_written_seconds':time.time()-start,'remaining':600-(time.time()-start)}))
