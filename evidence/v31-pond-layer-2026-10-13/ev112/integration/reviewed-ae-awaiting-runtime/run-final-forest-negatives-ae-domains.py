"""Paired controls on the actual domains of the unchanged acceptance predicates.

G1/G4/G5 are per-instance and use the original regional pool (16 mutations).
G2/G3/G7/G8 aggregate distributions and use the entire map pool (9 mutations).
Both pools must pass their exact positive commands before any mutation is credited.
This is one fixed domain correction, never a search for a passing subregion.
"""
from pathlib import Path
import concurrent.futures,gc,hashlib,json,subprocess,sys,threading,time
import numpy as np
O=Path(__file__).parent;TOOLS=O/'forest-final-tools-ae';G=TOOLS/'gates'
sys.path.insert(0,str(TOOLS));sys.path.insert(0,str(G));import recio,glib,gcfg as C
R=O/'forest-map-51ae';RAS=O/'forest-painted-rasters-ae';D=O/'forest-final-negatives-ae'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
read=lambda p:json.loads(Path(p).read_text())
frozen=read(O/'forest-ae-frozen.json')['files'];inputs=read(O/'forest-validation-inputs.json')['files']
report=read(R/'report.json');assert sha(R/'records.json')==report['records_sha256']
prior=read(D/'steps.json');assert len(prior)==4 and all(v['rc']==0 for v in prior[:3]) and prior[-1]['step']=='g2g3' and prior[-1]['rc']==1
old=read(D/'g23.json');assert old['summary']['judged_windows']==19 and old['summary']['G2']['verdict']==old['summary']['G3']['verdict']=='FAIL'
backup=D/'attempt2-regional-steps.json';assert not backup.exists();backup.write_bytes((D/'steps.json').read_bytes())
assert not (D/'acceptance.json').exists() and not (D/'domain-plan.json').exists()
physical=['n01','n02','n03','n04','n05','n06','n21','n30','n12','n13','n14','n15','n16','n17','n18','n19']
distribution=['n07','n22','n11','n40','n41','n42','n43','n44','n45']
assert len(physical)==16 and len(distribution)==9 and not set(physical)&set(distribution)
bbox=(7600,4300,10800,7950);world=(0,0,12288,12288)
wins=[(x,z) for z in glib.WIN_X0 for x in glib.WIN_X0 if x>=0 and z>=0 and x+1000<=12288 and z+1000<=12288]
assert len(wins)==576 and wins==[(x,z) for z in glib.WIN_X0 for x in glib.WIN_X0]
plan=dict(scope=__doc__,status='DECLARED_BEFORE_EXECUTION',runner_sha256=sha(__file__),source_sha256=report['tool_sha256'],records_sha256=report['records_sha256'],frozen_manifest_sha256=sha(O/'forest-ae-frozen.json'),negative_generator_sha256=sha(G/'negatives_map.py'),regional_failure_sha256=sha(D/'g23.json'),regional_steps_sha256=sha(backup),physical_domain=bbox,distribution_domain=world,distribution_windows=wins,physical_cases=physical,distribution_cases=distribution,acceptance_rules_changed=False,production_sources_changed=False,limits='Global distribution controls demonstrate rejection of the stated map-wide mutations; they do not claim every local window passes or every isolated local defect is rejected.')
(D/'domain-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
positive=D/'domain-positive';positive.mkdir(exist_ok=False)
pools={}
for name,box in [('physical',bbox),('distribution',world)]:
 mo,mi,m,keys=recio.load_records(R/'records.json',bbox=box);assert keys.all()
 p=positive/(name+'.json');recio.write_records(p,mo,mi,m)
 pools[name]=dict(path=str(p),sha256=sha(p),records=len(mi),matrix_sha256=hashlib.sha256(m.tobytes()).hexdigest(),model_index_sha256=hashlib.sha256(mi.tobytes()).hexdigest())
 del mo,mi,m,keys;gc.collect()
bands=C.E/'ev112-wip/forest/gates-run/livonia-ev112-bands.json';winarg=';'.join(f'{x},{z}' for x,z in wins)
rows=[];lock=threading.Lock()
def check():
 assert all(sha(p)==h for p,h in frozen.items())
 assert all(sha(p)==h for p,h in inputs.items())
def run(name,args):
 check();cmd=[sys.executable,'-I',*map(str,args)];start=time.time();print('START',name,flush=True)
 with (D/('domain-'+name+'.log')).open('w',encoding='utf-8') as f:
  rc=subprocess.run(cmd,cwd=O,stdout=f,stderr=subprocess.STDOUT).returncode
 row=dict(step=name,rc=rc,seconds=time.time()-start,cmd=cmd)
 with lock:
  rows.append(row);(D/'steps.json').write_text(json.dumps(rows,indent=2)+'\n')
 print('END',name,rc,flush=True);assert rc==0,row
 return row
pr=Path(pools['physical']['path']);full=Path(pools['distribution']['path'])
positives=[('g1',[G/'g1_map.py',pr,positive/'g1.json','--exclude',C.EXCLUSIONS]),('g4',[G/'g4g5_map.py',pr,'G4']),('g5',[G/'g4g5_map.py',pr,'G5']),('g2g3',[G/'g2g3_map.py',full,RAS,bands,positive/'g23.json','--windows',winarg]),('g7',[G/'g7_map.py',full,RAS,positive/'g7.json','--livonia-bands',bands,'--bbox','0,0,12288,12288']),('g8',[G/'g8_agreement.py',full,RAS,bands,positive/'g8.json','--windows',winarg])]
for name,args in positives:run(name,args)
assert len(rows)==6 and all(v['rc']==0 for v in rows)
assert read(positive/'g23.json')['summary']['windows']==576
mut=D/'mutations';mut.mkdir(exist_ok=False)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 jobs=[pool.submit(run,'negatives-physical',[G/'negatives_map.py',pr,RAS,bands,mut/'physical',','.join(map(str,bbox)),'--only',','.join(physical)]),pool.submit(run,'negatives-distribution',[G/'negatives_map.py',full,RAS,bands,mut/'distribution',','.join(map(str,world)),'--only',','.join(distribution)])]
 for job in jobs:job.result()
a=read(mut/'physical/negatives.json');b=read(mut/'distribution/negatives.json')
assert set(a)==set(physical) and set(b)==set(distribution)
combined={**a,**b};assert len(combined)==25 and all(v['detected'] for v in combined.values()),combined
(mut/'negatives.json').write_text(json.dumps(combined,indent=2)+'\n')
check();assert sha(R/'records.json')==report['records_sha256']
binding=dict(status='PASS',scope=__doc__,plan_sha256=sha(D/'domain-plan.json'),runner_sha256=sha(__file__),pools=pools,positive_steps=rows[:6],negative_steps=rows[6:],negative_generating_source_sha256=sha(G/'negatives_map.py'),negative_results_sha256={str(p):sha(p) for p in (mut/'physical/negatives.json',mut/'distribution/negatives.json',mut/'negatives.json')},source_sha256=report['tool_sha256'],records_sha256=report['records_sha256'],bands_sha256=sha(bands),frozen_manifest_sha256=sha(O/'forest-ae-frozen.json'),regional_failures_preserved=True,acceptance_rules_changed=False,production_sources_changed=False,limits=plan['limits'])
(D/'domain-binding.json').write_text(json.dumps(binding,indent=2)+'\n')
(D/'acceptance.json').write_text(json.dumps(dict(result='PASS',positive_gates=6,negative_controls=25,records=str(R/'records.json'),rasters=str(RAS)),indent=2)+'\n')
print('PASS:6 paired-domain positives and25 detected negatives; original regional FAIL preserved.',flush=True)
