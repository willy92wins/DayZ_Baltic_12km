from pathlib import Path
import sys,json,subprocess,time,hashlib
O=Path(__file__).parent;D=O/'forest-final-tools-ae';sys.path.insert(0,str(D/'gates'));import gcfg as C
P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=O/'forest-map-51ae';assert not R.exists()
RAS=O/'forest-final-rasters-c';BANDS=C.E/'ev112-wip/forest/gates-run/livonia-ev112-bands.json';source=hashlib.sha256((D/'forest_v31.py').read_bytes()).hexdigest();assert source=='0fef87eec16f4a609b33482ac438fc33f07e48c1db3d12810a3d0bd7501c658a'
a=[D/'forest_v31.py','--terrain',C.TERRAIN,'--footprint',C.FOOTPRINT,'--stage-wrp',C.STAGE_WRP,'--pbo',C.PBO,'--exclude',C.EXCLUSIONS]
for ld in C.LAYER_DIRS:a+=['--layer-dir',ld]
a+=['--cover',C.LAYERS,'--reference',C.REFERENCE,'--seed','51','--out',R,'--workers','8']
steps=[('place',a,P),('subset',[D/'gates/pilot_subset.py',R/'records.json',R/'pilot-subset.json'],P),('g2pilot',[C.R2_GATES/'g2_g3.py',R/'pilot-subset.json','G2','--dense','A-reserva','--json',R/'g2pilot.json'],C.R2_GATES),('g3pilot',[C.R2_GATES/'g2_g3.py',R/'pilot-subset.json','G3','--json',R/'g3pilot.json'],C.R2_GATES),('g7pilot',[C.R2_GATES/'g7_bog.py',R/'pilot-subset.json','--json',R/'g7pilot.json'],C.R2_GATES),('g1',[D/'gates/g1_map.py',R/'records.json',R/'g1.json','--exclude',C.EXCLUSIONS],P),('g4',[D/'gates/g4g5_map.py',R/'records.json','G4'],P),('g5',[D/'gates/g4g5_map.py',R/'records.json','G5'],P),('g2g3',[D/'gates/g2g3_map.py',R/'records.json',RAS,BANDS,R/'g2g3.json'],P),('g8-unpainted',[D/'gates/g8_agreement.py',R/'records.json',RAS,BANDS,R/'g8-unpainted.json'],P),('g9',[D/'gates/g9_seams.py',R/'records.json','500',R/'g9.json'],P),('g7map',[D/'gates/g7_map.py',R/'records.json',RAS,R/'g7map.json','--livonia-bands',BANDS],P),('counts',[D/'gates/counts_map.py',R/'records.json',RAS,R/'counts.json'],P)]
frozen=json.loads((O/'forest-ae-frozen.json').read_text(encoding='utf-8'))['files']
rec=[]
for name,args,cwd in steps:
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in frozen.items())
 cmd=[sys.executable,'-I',*map(str,args)];t=time.time()
 with (O/('forest-map-51ae-'+name+'.log')).open('w',encoding='utf-8') as f:rc=subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT).returncode
 rec.append(dict(step=name,rc=rc,seconds=time.time()-t,cmd=cmd));(O/'forest-map-51ae-steps.json').write_text(json.dumps(dict(source_sha256=source,steps=rec),indent=2),encoding='utf-8');print(name,rc,round(time.time()-t,1),flush=True)
 if rc and name in ('place','rasters','subset'):sys.exit(rc)
