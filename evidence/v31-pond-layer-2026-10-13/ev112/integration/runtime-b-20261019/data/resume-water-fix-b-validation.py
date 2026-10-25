from pathlib import Path
import json,shutil,subprocess,sys,time,hashlib,concurrent.futures
O=Path(__file__).parent;D=O/'water-fix-b';P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');K=D/'kit';assert not (K/'envelope-ev108.npy').exists()
env=O/'dam/envelope-dam.npy';shutil.copyfile(env,K/'envelope-ev108.npy')
src=O/'forest-final-tools-ae';target=O/'forest-water-fix-b';assert not target.exists();shutil.copytree(src,target,ignore=shutil.ignore_patterns('__pycache__'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs=json.loads((target/'final-inputs.json').read_text());before=inputs['terrain'];inputs['terrain']=dict(path=str(D/'terrain.npz'),sha256=sha(D/'terrain.npz'));(target/'final-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
binding=dict(reason='The first three consumers stopped on missing scratch envelope, before measuring. Originals are preserved. Resume with the real final dam envelope. Forest consumer source is byte-identical; only hash-bound terrain input changes, bridge geometry is unchanged.',envelope=dict(path=str(env),sha256=sha(env)),previous_terrain=before,new_terrain=inputs['terrain'],forest_source_identical=all(sha(p)==sha(target/p.relative_to(src)) for p in src.rglob('*.py')))
assert binding['forest_source_identical'];(D/'resume-input-binding.json').write_text(json.dumps(binding,indent=2)+'\n')
G=P/'evidence/v31-pond-layer-2026-10-13/ev112/ot1/gates';tasks=[(name,[G/(name+'.py'),K]) for name in ('gate_g9_mounds','gate_g10_stones','gate_g11_junctions')]
tasks.append(('forest-g1',[target/'gates/g1_map.py',O/'forest-map-51ae/records.json',D/'forest-g1.json','--exclude',O/'forest-exclusions-c.json']))
def run(task):
 name,args=task;t=time.time();cmd=[sys.executable,'-I',*map(str,args)]
 with (D/(name+'-resume.log')).open('w') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
 result=dict(step=name,rc=rc,seconds=time.time()-t,cmd=cmd);(D/(name+'-resume-execution.json')).write_text(json.dumps(result,indent=2)+'\n');print(name,rc,round(time.time()-t,1),flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(run,tasks))
(D/'resume-steps.json').write_text(json.dumps(r,indent=2)+'\n');sys.exit(0 if all(x['rc']==0 for x in r) else 1)
