from pathlib import Path
import shutil,json,subprocess,sys,concurrent.futures
O=Path(__file__).parent;D=O/'water-fix-b';P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');K=D/'baseline-kit';(K/'bury-work/fp0').mkdir(parents=True,exist_ok=False)
for src,dst in [(O/'terrain-ev112-c.npz',K/'terrain-kit.npz'),(O/'terrain-ev112-c.npz',K/'terrain-ev108.npz'),(O/'fp-ev112-c/footprint.npz',K/'bury-work/fp0/footprint.npz'),(D/'kit/envelope-ev108.npy',K/'envelope-ev108.npy'),(D/'kit/kit-records.json',K/'kit-records.json'),(D/'kit/kit-report.json',K/'kit-report.json')]:shutil.copyfile(src,dst)
G=P/'evidence/v31-pond-layer-2026-10-13/ev112/ot1/gates'
def run(item):
 number,script=item;cmd=[sys.executable,'-I',str(G/script),str(K)]
 with (D/f'baseline-g{number}.log').open('w') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
 before=json.loads((K/f'gate-g{number}.json').read_text());after=json.loads((D/f'kit/gate-g{number}.json').read_text());path_fields=['footprint'] if number==11 else []
 for k in path_fields:before.pop(k,None);after.pop(k,None)
 equal=before==after;out=dict(gate=number,baseline_rc=rc,baseline_passed=before['passed'],candidate_passed=after['passed'],all_measurements_identical=equal,ignored_path_fields=path_fields,differences={k:dict(baseline=before.get(k),candidate=after.get(k)) for k in set(before)|set(after) if before.get(k)!=after.get(k)})
 print(json.dumps(out),flush=True);return out
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(run,[(9,'gate_g9_mounds.py'),(11,'gate_g11_junctions.py')]))
(D/'phase-gate-comparison.json').write_text(json.dumps(r,indent=2)+'\n');sys.exit(0 if all(x['all_measurements_identical'] for x in r) else 1)
