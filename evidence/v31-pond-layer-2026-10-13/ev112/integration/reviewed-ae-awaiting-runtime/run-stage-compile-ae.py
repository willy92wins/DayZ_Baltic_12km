from pathlib import Path
import sys,json,subprocess,time,hashlib
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=O/'forest-map-51ae';stage=O/'stage-forest-ae/root/dayz_baltic_12km_dev/tb/narva_trial';assert not stage.exists()
steps=json.loads((O/'forest-map-51ae-steps.json').read_text())['steps'];assert len(steps)==13 and all(s['rc']==0 for s in steps if s['step']!='g8-unpainted'),[(s['step'],s['rc']) for s in steps]
frozen=json.loads((O/'forest-ae-frozen.json').read_text())['files'];assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in frozen.items())
stage.parent.mkdir(parents=True,exist_ok=True);runs=[]
cmds=[('stage',[sys.executable,'-I',str(P/'tools/terrain/stage_bridges_v31.py'),str(O/'stage-nonforest-c/root/dayz_baltic_12km_dev/tb/narva_trial'),str(O/'terrain-ev112-c.npz'),str(R/'records.json'),str(stage),str(O/'stage-forest-ae-report.json')]),('compile',['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(O/'compile_world_ev112_ae.ps1')])]
for name,cmd in cmds:
 t=time.time()
 with (O/f'final-ae-{name}.log').open('w',encoding='utf-8') as f:rc=subprocess.run(cmd,cwd=P,stdout=f,stderr=subprocess.STDOUT).returncode
 runs.append(dict(step=name,rc=rc,seconds=time.time()-t,cmd=cmd));(O/'final-ae-stage-compile.json').write_bytes((json.dumps(runs,indent=2)+'\n').encode());print(name,rc,round(time.time()-t,1),flush=True)
 if rc:sys.exit(rc)
