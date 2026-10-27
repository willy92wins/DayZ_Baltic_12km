from pathlib import Path
import sys,subprocess,json,tempfile,hashlib
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=R/'kit7-nav8load1-consumer-20261027'
probe='68006643-4412-467a-b437-734168f3f1e0'
old=(W/'evidence/navigation/kit7-native-config-types-20261027/runtime.log').read_text(encoding='utf-8-sig');good=old.replace('OnLoad;true;2;true;true;0;0','OnLoad;true;0;true;1;1;1');assert good!=old
source=(R/'recover_kit7_nav8load1_config_consumer.py').read_text();line=next(s for s in source.splitlines() if s.startswith('bootstrap='));scope={};exec(line,scope);bootstrap=scope['bootstrap'];checks=[]
with tempfile.TemporaryDirectory() as folder:
 d=Path(folder)
 for name,text,uuid,expected in [('positive',good,probe,0),('old_flag',old,probe,1),('wrong_uuid',good,'wrong',1)]:
  log=d/(name+'.log');out=d/(name+'.json');log.write_text(text)
  p=subprocess.run([sys.executable,'-I','-c',bootstrap,str(W/'tools/navigation'),'--probe-id',uuid,'--log',str(log),'--out',str(out)],capture_output=True)
  assert p.returncode==expected,(name,p.stderr.decode());result=json.loads(out.read_text());assert (result['status']=='PASS_NATIVE_LOAD1_CONFIG')==(expected==0)
  checks.append(dict(case=name,returncode=p.returncode,status=result['status']))
report=dict(status='PASS_ISOLATED_CLI_WRAPPER',checks=checks,consumer_sha256=hashlib.sha256((W/'tools/navigation/verify_nav8_load1_config_ev112.py').read_bytes()).hexdigest(),native_measurement=False)
(D/'isolated-wrapper-controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
