from pathlib import Path
import json,subprocess,sys,time,shutil,concurrent.futures
O=Path(__file__).parent;B=O.parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=O/'water-fix-b';K=D/'kit';(K/'bury-work/fp0').mkdir(parents=True,exist_ok=False)
for src,dst in [(D/'terrain.npz',K/'terrain-kit.npz'),(D/'terrain.npz',K/'terrain-ev108.npz'),(O/'fp-ev112-c/footprint.npz',K/'bury-work/fp0/footprint.npz'),(B/'ev112-ot1-20261018/run-l/kit-records.json',K/'kit-records.json'),(B/'ev112-ot1-20261018/run-l/kit-report.json',K/'kit-report.json')]:shutil.copyfile(src,dst)
G=P/'evidence/v31-pond-layer-2026-10-13/ev112/ot1/gates'
tasks=[(name,[G/(name+'.py'),K]) for name in ('gate_g2_width','gate_g3_continuity','gate_g4_engine_margin','gate_g7_probe','gate_g9_mounds','gate_g10_stones','gate_g11_junctions')]
tasks.append(('bury',[P/'tools/water/bury_edges_v31.py',D/'terrain.npz',O/'terrain-ev112-c.npz',O/'dam/cover-dam.npy',O/'dam/envelope-dam.npy',O/'fp-ev112-c/footprint-report.json',D/'terrain-buried.npz',D/'bury-work',D/'bury-report.json']))
def run(task):
 name,args=task;t=time.time();cmd=[sys.executable,'-I',*map(str,args)]
 with (D/(name+'.log')).open('w') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
 result=dict(step=name,rc=rc,seconds=time.time()-t,cmd=cmd);(D/(name+'-execution.json')).write_text(json.dumps(result,indent=2)+'\n');print(name,rc,round(time.time()-t,1),flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(run,tasks))
(D/'kit-and-bury-steps.json').write_text(json.dumps(r,indent=2)+'\n');sys.exit(0 if all(v['rc']==0 for v in r) else 1)
