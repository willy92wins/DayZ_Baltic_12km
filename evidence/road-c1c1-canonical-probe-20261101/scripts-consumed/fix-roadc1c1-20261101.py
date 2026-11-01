from pathlib import Path
import json,time,hashlib,importlib.util
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c1-local-author-20261101';start=json.loads((D/'correction-start.json').read_bytes())['started'];assert time.time()-start<180
p=D/'observe_road_compile_c1c1.py';s=p.read_text()
s=s.replace("if expected:require((size,digest)==(expected['bytes'],expected['sha256']),'ARTIFACT_PIN')","if expected is not None:\n        require(isinstance(expected,dict) and type(expected.get('bytes')) is int and expected['bytes']>=0 and isinstance(expected.get('sha256'),str) and re.fullmatch('[0-9a-f]{64}',expected['sha256']) is not None,'PIN_SCHEMA');require((size,digest)==(expected['bytes'],expected['sha256']),'ARTIFACT_PIN')")
a=s.index('def portable(c,phase):');b=s.index('def arm_check',a)
s=s[:a]+'''def phase_logger(c,phase):
    row=next(x for x in c['tool_files'] if x['dest']=='logger.xml');checkfile(row['path'],row,67108864);raw=Path(row['path']).read_bytes();require(hashlib.sha256(raw).hexdigest()==row['sha256'],'LOGGER_DELTA')
    if phase is None:return raw
    original=ET.fromstring(raw);nodes=original.findall('./appender/file');require(len(nodes)==3,'LOGGER_DELTA');values=[n.attrib['value'].encode() for n in nodes];require(len(set(values))==3 and all(raw.count(v)==1 for v in values),'LOGGER_DELTA')
    replacements={value:str(Path(c['root'])/'logs'/phase/name).encode() for value,name in zip(values,['AddonBuilder.rpt','AddonBuilderProcess.rpt','AddonBuilder.User.rpt'])}
    expression=re.compile(b'|'.join(re.escape(v) for v in sorted(values,key=len,reverse=True)));candidate=expression.sub(lambda m:replacements[m.group()],raw);tree=ET.fromstring(candidate)
    for n,value in zip(tree.findall('./appender/file'),values):n.attrib['value']=value.decode()
    require(ET.tostring(tree)==ET.tostring(original),'LOGGER_DELTA');return candidate

def portable(c,phase):
    folder=Path(c['root'])/'tools/AddonBuilder'
    for row in c['tool_files']:
        if row['dest']!='logger.xml':checkfile(folder/row['dest'],row,67108864)
        else:require(phase_logger(c,phase)==(folder/'logger.xml').read_bytes(),'LOGGER_DELTA')
    for k in ['include','exclude']:checkfile(Path(c['root'])/'fixed'/(k+'.lst'),c[k],33554432)

def receipt_limits(r,seconds,rss):
    for k in ['seconds','peak_rss','observed_disk_peak']:require(type(r.get(k)) in (float,int) and r[k]>=0,'RECEIPT_CAP')
    require(r['seconds']<=seconds+5 and r['peak_rss']<=rss and r['observed_disk_peak']<=2147483648,'RECEIPT_CAP')

def preflight_check(c,r):
    require(r['command']==[sys.executable,'-I','-X','utf8',c['preflight']['path']] and r['cwd']==c['root'],'ARG_BINDING');require(r['reason'] is None and r['rc']==0,'PREFLIGHT');receipt_limits(r,60,268435456);process_tree(c,r)
    nodes={p['pid']:p for p in r['observed_processes']};require({str(k) for k in nodes}==set(r['identities']),'PROCESS_PARENT');root=nodes[r['root_pid']];require(root['exe'].casefold()==sys.executable.casefold() and root['argv']==r['command'],'ARG_BINDING')
    for p in nodes.values():
        require(r['identities'].get(str(p['pid']))==p['birth'] and r['started']<=p['birth']<=p['observed_at']<=r['finished'],'PROCESS_WINDOW');q=checkfile(p['exe'],cap=67108864);require(q['sha256']==p['image_path_sha256'] and list(fileid(Path(p['exe']).stat()))==p['image_identity'],'IMAGE_CHANGED')
    # Preflight descendant images are observed/pinned to receipts, not a native-tool allowlist.

def prerequisite_check(c,r,states):
    require(all(states[x]=='CLOSED' for x in ['preflight','help','control','candidate']),'PREREQUISITE_INCOMPLETE');require(type(r.get('copy_seconds')) in (int,float) and 0<=r['copy_seconds']<=180 and type(r.get('seconds')) in (int,float) and 0<=r['seconds']<=930,'RECEIPT_CAP')
    preflight_check(c,r['phases']['preflight'])
    before=r.get('profile_before');after=r.get('profile_after');require(isinstance(before,list) and isinstance(after,list),'PROFILE_CHANGED')
    require([(x['path'],x['bytes'],x['sha256']) for x in before]==[(x['path'],x['bytes'],x['sha256']) for x in after] and 'profile_after_error' not in r,'PROFILE_CHANGED')
    for row in after:checkfile(row['path'],row,4194304)

'''+s[b:]
s=s.replace("return 'CLOSED'\n\ndef verify_invocation", "receipt=entry if name=='preflight' else entry['receipt'];require(start.get('command')==receipt.get('command') and type(start.get('time')) in (int,float) and start['time']<=receipt['started'],'PHASE_BINDING')\n    if name!='preflight':require(start.get('logger_sha256')==entry.get('logger_sha256')==hashlib.sha256(phase_logger(c,name)).hexdigest(),'LOGGER_DELTA')\n    return 'CLOSED'\n\ndef verify_invocation")
s=s.replace("r=phase['receipt'];verify_invocation(c,r,arm);", "r=phase['receipt'];receipt_limits(r,30 if arm=='help' else 300,536870912 if arm=='help' else 2147483648);verify_invocation(c,r,arm);")
s=s.replace("require(private,'LOG_NOT_OBSERVED')", "require(private,'LOG_NOT_OBSERVED')")
s=s.replace("require(marker,'NO_MARKER');require", "require(marker,'NO_MARKER');require(type(phase.get('envelope_seconds')) in (int,float) and r['seconds']<=phase['envelope_seconds']<=300,'RECEIPT_CAP');require")
s=s.replace("states={a:phase_state(c,r,a)", "states={a:phase_state(c,r,a)")
s=s.replace("if states['preflight']=='CLOSED':require(r['phases']['preflight']['rc']==0 and r['phases']['preflight']['reason'] is None,'PREFLIGHT')", "if states['preflight']=='CLOSED':preflight_check(c,r['phases']['preflight'])\n        if any(states[a]!='NOT_LAUNCHED' for a in ['control','candidate']):prerequisite_check(c,r,states)")
p.write_text(s,encoding='utf-8')
p=D/'probe_road_compile_c1c1.py';s=p.read_text().replace("need(time.monotonic()-tick<=300,'ARM_BUDGET')", "need(time.monotonic()-tick<=300,'ARM_BUDGET');report['phases'][arm]['envelope_seconds']=time.monotonic()-tick;dump(root/'phases'/(arm+'.closed.json'),report['phases'][arm]);save()")
p.write_text(s,encoding='utf-8')
p=D/'test_probe_road_compile_c1c1.py';s=p.read_text().replace("'tool_files':[{'dest':'AddonBuilder.exe','sha256':self.rh}]", "'tool_files':[{**rec(self.rootimage),'dest':'AddonBuilder.exe'}]")
s=s.replace("self.phase={'receipt':self.receipt,'logs':self.logs,'artifacts':[self.art]}","self.receipt.update(seconds=1,peak_rss=100,observed_disk_peak=0);self.phase={'receipt':self.receipt,'logs':self.logs,'artifacts':[self.art],'envelope_seconds':2}")
s=s.replace("entry={'state':'CLOSED','start':mark};r['phases']['help']=entry;A.dump(folder/'help.closed.json',entry);self.assertEqual(V.phase_state(self.c,r,'help'),'CLOSED')", "mark.update(command=['HELP'],logger_sha256='literal');A.dump(folder/'help.started.json',mark);entry={'state':'CLOSED','start':mark,'receipt':{'command':['HELP'],'started':2},'logger_sha256':'literal'};r['phases']['help']=entry;A.dump(folder/'help.closed.json',entry)\n  with patch.object(V,'phase_logger',return_value=b'literal'):\n   with self.assertRaisesRegex(V.Reject,'LOGGER_DELTA'):V.phase_state(self.c,r,'help')")
s=s.replace("if __name__=='__main__':unittest.main()",''' def test_journal_command_time_and_logger_comutations(self):
  folder=self.r/'phases';folder.mkdir();raw=(D/'logger-fixture.xml').read_bytes();self.c['tool_files'].append({**rec(D/'logger-fixture.xml'),'dest':'logger.xml'});lh=hashlib.sha256(V.phase_logger(self.c,'help')).hexdigest();mark={'state':'STARTED','phase':'help','command':['EXPECTED'],'time':1,'logger_sha256':lh};entry={'state':'CLOSED','start':mark,'receipt':{'command':['EXPECTED'],'started':2},'logger_sha256':lh};r={'phases':{'help':entry}}
  def save():A.dump(folder/'help.started.json',mark);A.dump(folder/'help.closed.json',entry)
  save();self.assertEqual(V.phase_state(self.c,r,'help'),'CLOSED')
  for key,value,code in [('command',['OTHER'],'PHASE_BINDING'),('time',3,'PHASE_BINDING'),('logger_sha256','0'*64,'LOGGER_DELTA')]:
   old=mark[key];mark[key]=value;save()
   with self.assertRaisesRegex(V.Reject,code):V.phase_state(self.c,r,'help')
   mark[key]=old
 def test_caps_missing_prerequisites_and_bad_pin(self):
  for key,value in [('seconds',306),('peak_rss',2147483649),('observed_disk_peak',2147483649)]:
   r=copy.deepcopy(self.receipt);r[key]=value
   with self.assertRaisesRegex(V.Reject,'RECEIPT_CAP'):V.receipt_limits(r,300,2147483648)
  with self.assertRaisesRegex(V.Reject,'PREREQUISITE_INCOMPLETE'):V.prerequisite_check(self.c,{},dict(preflight='NOT_LAUNCHED',help='NOT_LAUNCHED',control='CLOSED',candidate='CLOSED'))
  with self.assertRaisesRegex(V.Reject,'PIN_SCHEMA'):V.checkfile(self.rootimage,{'sha256':self.rh})
 def test_logger_independent_extra_change(self):
  row=rec(D/'logger-fixture.xml');self.c['tool_files'].append({**row,'dest':'logger.xml'});raw=Path(row['path']).read_bytes();paths=[self.r/'logs/help'/n for n in ['AddonBuilder.rpt','AddonBuilderProcess.rpt','AddonBuilder.User.rpt']];self.assertEqual(V.phase_logger(self.c,'help'),A.logger_bytes(raw,paths))
if __name__=='__main__':unittest.main()''')
p.write_text(s,encoding='utf-8')
files={}
for n in json.loads((D/'author-completion.json').read_bytes())['files']:
 p=D/n;compile(p.read_bytes(),str(p),'exec');files[n]=hashlib.sha256(p.read_bytes()).hexdigest()
sp=importlib.util.spec_from_file_location('probe',D/'probe_road_compile_c1c1.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);c=json.loads((D/'contract.json').read_bytes());check=m.canonical_check(c);(D/'canonical-frozen-contract-check.json').write_text(json.dumps({'result':'MATCH','file':check,'contract_unchanged':True,'real_alias_not_mocked':True},indent=2))
elapsed=time.time()-start;assert elapsed<180
(D/'correction-completion.json').write_text(json.dumps({'seconds':elapsed,'within_budget':True,'files':files,'postimage_external_rereview':False},indent=2));print(json.dumps({'seconds':elapsed,'files':files}))
