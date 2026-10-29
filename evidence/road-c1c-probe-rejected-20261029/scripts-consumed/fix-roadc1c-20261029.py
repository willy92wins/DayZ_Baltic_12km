from pathlib import Path
import json,hashlib,time,shutil
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c-local-author-20261029';start=time.time()
def dump(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf-8')
dump(D/'correction-start.json',{'started':start,'seconds':180,'closed_findings':'Muse1-8 adjudicated plus integration identity/argv repro; no cap expansion'})
old=D/'source-R0';old.mkdir(exist_ok=False)
for n in ['probe_road_compile_c1c.py','observe_road_compile_c1c.py','test_probe_road_compile_c1c.py']:shutil.copyfile(D/n,old/n)
delta={'schema':'road-c1c-delta-oracle.v1','unmapped_identity':'PROBE_INCONCLUSIVE_NOT_OBSERVED','wrong_command':'ARG_BINDING','help_unknown':'UNEXPECTED_CHILD','portable_changed':'PIN','include_changed':'PIN','control_rejected_launches':['preflight','help','control'],'work_mutated_launches':['preflight','help','control'],'original_syntax_error':213,'private_marker_required':True,'writer_cap_seconds':930,'observer_cap_seconds':120,'grandchild_test':'observable sustained lifetime; not orphan-proof claim','unchanged_contract':'e88e345a2e88a6c47b05091a40c1bdfbaab34353ad000f7b7b80d52b6104f1b6'}
dump(D/'delta-oracle.json',delta)
p=D/'probe_road_compile_c1c.py';s=p.read_text();s=s.replace("child.wait(timeout=5)","\n            try:child.wait(timeout=5)\n            except subprocess.TimeoutExpired:reason='MONITOR_ERROR:WAIT_TIMEOUT'")
s=s.replace("if help_mode:return 'HELP_OBSERVED' if syntax and tools_flag else 'NO_HELP'\n    if not marker:return 'NO_MARKER'\n    observed=receipt['observed_processes']", "observed=receipt['observed_processes']\n    if {str(x['pid']) for x in observed}!={str(x) for x in receipt['identities']}:return 'PROBE_INCONCLUSIVE_NOT_OBSERVED'")
s=s.replace("if not any(r['image_path_sha256']==binarize_sha for r in observed)","if help_mode:return 'HELP_OBSERVED' if syntax and tools_flag else 'NO_HELP'\n    if not marker:return 'NO_MARKER'\n    if not any(r['image_path_sha256']==binarize_sha for r in observed)")
s=s.replace("marker=marker or 'Build Successful' in text", "marker=marker or ('Build Successful' in text and re.fullmatch(r'AddonBuilder(?:Process|\\.User)?\\.rpt(?:\\.\\d+)?',Path(r['path']).name) is not None)")
insert='''def portable_check(c,portable,raw,phase):
    paths=[Path(c['root'])/'logs'/phase/n for n in ['AddonBuilder.rpt','AddonBuilderProcess.rpt','AddonBuilder.User.rpt']]
    for row in c['tool_files']:
        p=Path(portable)/row['dest']
        if row['dest']=='logger.xml':verify_logger(raw,p.read_bytes(),paths)
        else:pincheck({**row,'path':str(p)})
def args_for(c,arm):
    root=Path(c['root']);project=root/'work'/arm/'root';out=root/'output'/arm
    return [str(project/c['prefix']),str(out/'out'),'-prefix='+c['prefix'].replace('/','\\\\'),'-project='+str(project),'-temp='+str(out/'temp'),'-include='+str(root/'fixed/include.lst'),'-exclude='+str(root/'fixed/exclude.lst'),'-binarizeFullLogs','-toolsDirectory='+c['tool_root']]+['-'+k+'='+c['tools'][k]['path'] for k in ['binarize','cfgConvert','fileBank','dsSignFile']]
def command_check(c,receipt,phase):
    exe=str(Path(c['root'])/'tools/AddonBuilder/AddonBuilder.exe');args=['-help','-toolsDirectory='+c['tool_root']] if phase=='help' else args_for(c,phase)
    need(receipt['command']==[exe,*args] and receipt['cwd']==str(Path(exe).parent),'ARG_BINDING')
    roots=[p for p in receipt['observed_processes'] if p['exe'].lower()==exe.lower()]
    need(len(roots)==1 and roots[0]['argv']==receipt['command'],'ARG_BINDING')

'''
s=s.replace('def mainrun(c,pin):',insert+'def mainrun(c,pin):')
s=s.replace("deadline=begin+c['caps']['total_seconds']", "deadline=begin+c['caps']['total_seconds']-c['caps']['observe_seconds']")
s=s.replace("report['profile_before']=profile_snapshot(c['profile_roots']);until=time.monotonic()+180;work=root/'work'", "report['profile_before']=profile_snapshot(c['profile_roots']);until=time.monotonic()+180;work=root/'work';pincheck(c['c1b_consumer']);trees(c,[c['source_stage']],until)")
s=s.replace("report['copy_seconds']=", "trees(c,[work],until)\n        for k in ['include','exclude']:read_hash(c[k]['path'],max(c[k]['bytes'],1),until,root/'fixed'/(k+'.lst'))\n        report['copy_seconds']=")
s=s.replace("for v in env.values():Path(v).mkdir(parents=True)","for v in env.values():Path(v).mkdir(parents=True)\n            portable_check(c,portable,raw,phase)\n            for k in ['include','exclude']:pincheck({**c[k],'path':str(root/'fixed'/(k+'.lst'))})")
s=s.replace("logs=snapshot_logs(logdir,receipt);return receipt,logs,hashlib.sha256(lb).hexdigest()", "logs=snapshot_logs(logdir,receipt);portable_check(c,portable,raw,phase);command_check(c,receipt,phase);return receipt,logs,hashlib.sha256(lb).hexdigest()")
s=s.replace("c['tools']['binarize']['sha256'],[],True)","c['tools']['binarize']['sha256'],{next(x['sha256'] for x in c['tool_files'] if x['dest']=='AddonBuilder.exe')},True)")
line=next(x for x in s.splitlines() if x.strip().startswith('args=[str(src)'))
s=s.replace(line,"            args=args_for(c,arm)")
s=s.replace("paths=[Path(receipt[k]['path'])", "paths=[Path(receipt[k]['path'])")
s=s.replace("until=time.monotonic()+5;previous=None", "need(all(re.fullmatch(r'AddonBuilder(?:Process|\\.User)?\\.rpt(?:\\.\\d+)?',p.name) for p in paths[2:]),'LOG_BINDING')\n    until=time.monotonic()+5;previous=None")
p.write_text(s,encoding='utf-8')
p=D/'observe_road_compile_c1c.py';s=p.read_text().replace('import argparse,hashlib,json,os,re,stat,sys,time','import argparse,hashlib,json,os,re,stat,sys,time,xml.etree.ElementTree as ET')
insert='''def verify_invocation(c,r,arm):
    root=Path(c['root']);exe=root/'tools/AddonBuilder/AddonBuilder.exe';project=root/'work'/arm/'root';out=root/'output'/arm
    if arm=='help':args=['-help','-toolsDirectory='+c['tool_root']]
    else:args=[str(project/c['prefix']),str(out/'out'),'-prefix='+c['prefix'].replace('/','\\\\'),'-project='+str(project),'-temp='+str(out/'temp'),'-include='+str(root/'fixed/include.lst'),'-exclude='+str(root/'fixed/exclude.lst'),'-binarizeFullLogs','-toolsDirectory='+c['tool_root']]+['-'+k+'='+c['tools'][k]['path'] for k in ['binarize','cfgConvert','fileBank','dsSignFile']]
    require(r['command']==[str(exe),*args] and r['cwd']==str(exe.parent),'ARG_BINDING')
    roots=[p for p in r['observed_processes'] if p['exe'].lower()==str(exe).lower()];require(len(roots)==1 and roots[0]['argv']==r['command'],'ARG_BINDING')
def portable(c,phase):
    root=Path(c['root']);folder=root/'tools/AddonBuilder'
    for row in c['tool_files']:
        if row['dest']!='logger.xml':checkfile(folder/row['dest'],row,67108864)
        else:
            raw=Path(row['path']).read_bytes();a=ET.fromstring(raw);b=(folder/'logger.xml').read_bytes()
            for node,name in zip(a.findall('./appender/file'),['AddonBuilder.rpt','AddonBuilderProcess.rpt','AddonBuilder.User.rpt']):raw=raw.replace(node.attrib['value'].encode(),str(root/'logs'/phase/name).encode())
            require(raw==b,'LOGGER_DELTA')
    for k in ['include','exclude']:checkfile(root/'fixed'/(k+'.lst'),c[k],33554432)
'''
s=s.replace("def arm_check(c,phase,arm='control'):",insert+"def arm_check(c,phase,arm='control'):")
s=s.replace("r=phase['receipt'];require", "r=phase['receipt'];verify_invocation(c,r,arm);require")
s=s.replace("processes=r['observed_processes'];require", "processes=r['observed_processes'];require({str(p['pid']) for p in processes}==set(r['identities']),'PROBE_INCONCLUSIVE_NOT_OBSERVED');require")
s=s.replace("require(any(p['image_path_sha256']==c['tools']['binarize']['sha256'] for p in processes),'PROBE_INCONCLUSIVE_NOT_OBSERVED')", "require(arm=='help' or any(p['image_path_sha256']==c['tools']['binarize']['sha256'] for p in processes),'PROBE_INCONCLUSIVE_NOT_OBSERVED')\n    if arm=='help':require(all(p['image_path_sha256']==next(v['sha256'] for v in c['tool_files'] if v['dest']=='AddonBuilder.exe') for p in processes),'UNEXPECTED_CHILD')")
s=s.replace("marker=False;private=False", "marker=False;private=False;syntax=False;tools_flag=False")
s=s.replace("allowed_logs|=actual_logs", "require(all(re.fullmatch(r'AddonBuilder(?:Process|\\.User)?\\.rpt(?:\\.\\d+)?',p.name) for p in actual_logs),'LOG_BINDING');allowed_logs|=actual_logs")
s=s.replace("marker=marker or 'Build Successful' in text", "marker=marker or ('Build Successful' in text and Path(log['path']) in actual_logs);syntax=syntax or 'SYNTAX' in text;tools_flag=tools_flag or '-toolsDirectory' in text")
s=s.replace("require(private,'LOG_NOT_OBSERVED');require(marker", "require(private,'LOG_NOT_OBSERVED')\n    if arm=='help':require(syntax and tools_flag,'NO_HELP');return {'status':'HELP_OBSERVED'}\n    require(marker")
s=s.replace("c['preflight_original']]:", "c['preflight_original'],c['preflight'],c['c1b_consumer']]:")
s=s.replace("for arm in ['control','candidate']:\n        if arm not", "try:\n        phase=next((a for a in ['candidate','control','help'] if a in r['phases']),'help');portable(c,phase);arm_check(c,r['phases']['help'],'help');require(r['phases']['preflight']['rc']==0 and r['phases']['preflight']['reason'] is None,'PREFLIGHT')\n    except (Reject,OSError,KeyError) as e:findings.append({'kind':'LAUNCH_PREREQUISITES','error':str(e)})\n    for arm in ['control','candidate']:\n        if arm not")
p.write_text(s,encoding='utf-8')
dump(D/'correction-code-written.json',{'seconds':time.time()-start,'delta_sha256':hashlib.sha256((D/'delta-oracle.json').read_bytes()).hexdigest()})
print('code delta written; tests follow within same 180s budget')
