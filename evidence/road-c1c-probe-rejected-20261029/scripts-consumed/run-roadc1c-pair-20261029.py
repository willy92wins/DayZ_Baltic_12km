from pathlib import Path
import sys,json,hashlib,time,importlib.util
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c-local-author-20261029';O=R/'road-c1c-real-20261029';O.mkdir(exist_ok=False)
approval=json.loads((D/'approval.json').read_bytes())
for name,pin in approval['files'].items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==pin
assert approval['status']=='INTEGRATED_FOR_ONE_COMPILE_PROBE' and not Path(json.loads((D/'contract.json').read_bytes())['root']).exists()
s=importlib.util.spec_from_file_location('runner',D/'probe_road_compile_c1c.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
started=time.monotonic();deadline=started+1050;py=sys.executable;sha=hashlib.sha256((D/'contract.json').read_bytes()).hexdigest()
m.dump(O/'started.json',{'utc':time.time(),'budget_seconds':1050,'producer_envelope':930,'consumer_envelope':120,'approval_sha':hashlib.sha256((D/'approval.json').read_bytes()).hexdigest()})
producer=m.proc_run([py,'-I','-X','utf8',str(D/'probe_road_compile_c1c.py'),'--contract',str(D/'contract.json'),'--sha',sha],D,O/'producer',930,2147483648)
report=R/'road-c1c-probe-20261029/report.json';result={'producer':producer,'observer':None}
if report.exists() and producer['reason'] is None:
 pin=m.read_hash(report,33554432);m.dump(O/'report-external-pin.json',pin);remaining=deadline-time.monotonic()
 if remaining>=120:
  observer=m.proc_run([py,'-I','-X','utf8',str(D/'observe_road_compile_c1c.py'),'--contract',str(D/'contract.json'),'--sha',sha,'--report',str(report),'--report-sha',pin['sha256'],'--out',str(O/'observer.json')],D,O/'observer',120,268435456)
  result['observer']=observer
 else:result['observer_skip']='TOTAL_BUDGET'
else:result['observer_skip']='NO_SEALED_REPORT_OR_PRODUCER_TIMEOUT'
result['seconds']=time.monotonic()-started;m.dump(O/'result.json',result);print(json.dumps({'seconds':result['seconds'],'producer_rc':producer['rc'],'producer_reason':producer['reason'],'observer_rc':result['observer']['rc'] if result['observer'] else None}))
