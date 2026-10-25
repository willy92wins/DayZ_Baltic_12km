"""Credit negative controls only after the same regional positive passes."""
from pathlib import Path
import sys,json,subprocess,time
O=Path(__file__).parent;G=O/'forest-final-tools-ae/gates';sys.path.insert(0,str(G));import gcfg as C;import recio
R=O/'forest-map-51ae';RAS=O/'forest-painted-rasters-ae';D=O/'forest-final-negatives-ae';D.mkdir(exist_ok=False)
assert [s['step'] for s in json.loads((O/'forest-painted-ae-steps.json').read_text())['steps']]==['g2g3','g8','g7','g2pilot','g3pilot']
assert all(s['rc']==0 for s in json.loads((O/'forest-painted-ae-steps.json').read_text())['steps'])
region='7600,4300,10800,7950';bbox=tuple(map(float,region.split(',')));models,midx,m,_=recio.load_records(R/'records.json',bbox=bbox);recio.write_records(D/'positive.json',models,midx,m);del m
bands=C.E/'ev112-wip/forest/gates-run/livonia-ev112-bands.json'
x0,z0,x1,z1=bbox;wins=';'.join(f'{wx},{wz}' for wz in range(0,11289,500) for wx in range(0,11289,500) if wx>=x0 and wx+1000<=x1 and wz>=z0 and wz+1000<=z1)
runs=[];rec=D/'positive.json'
steps=[('g1',[G/'g1_map.py',rec,D/'g1.json','--exclude',C.EXCLUSIONS]),('g4',[G/'g4g5_map.py',rec,'G4']),('g5',[G/'g4g5_map.py',rec,'G5']),('g2g3',[G/'g2g3_map.py',rec,RAS,bands,D/'g23.json','--windows',wins]),('g7',[G/'g7_map.py',rec,RAS,D/'g7.json','--livonia-bands',bands,'--bbox',region]),('g8',[G/'g8_agreement.py',rec,RAS,bands,D/'g8.json','--windows',wins]),('negatives',[G/'negatives_map.py',R/'records.json',RAS,bands,D/'mutations',region])]
for name,args in steps:
 cmd=[sys.executable,'-I',*map(str,args)];t=time.time()
 with (D/(name+'.log')).open('w',encoding='utf-8') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
 runs.append(dict(step=name,rc=rc,seconds=time.time()-t,cmd=cmd));(D/'steps.json').write_bytes((json.dumps(runs,indent=2)+'\n').encode());print(name,rc,flush=True)
 if rc:sys.exit(rc)
n=json.loads((D/'mutations/negatives.json').read_text());assert len(n)==25 and all(v['detected'] for v in n.values()),n
(D/'acceptance.json').write_bytes((json.dumps(dict(result='PASS',positive_gates=6,negative_controls=25,records=str(R/'records.json'),rasters=str(RAS)),indent=2)+'\n').encode());print('PASS: 6 positive gates, 25 detected negatives')
