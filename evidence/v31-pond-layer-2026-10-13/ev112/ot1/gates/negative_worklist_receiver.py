"""Replay the historical retained-receptor absorption bug; step 0 must reject it.
Usage: negative_worklist_receiver.py <fresh-output>
"""
import json,pathlib,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import gatelib as G
out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
tool=pathlib.Path(G.WT)/'tools/water/kit_worklist_v31.py'
source=tool.read_text()
guard='        if any(tuple(int(x) for x in v) in keep_seed for v in vv):\n            continue  # Explicit retained-water seeds must never be absorbed into a replacement body.\n'
assert source.count(guard)==1
source=source.replace(guard,'')
mutant=out/'worklist-absorbs-receiver.py';mutant.write_text(source,encoding='utf-8')
base=pathlib.Path(G.B)
cmd=[sys.executable,'-I',str(mutant),str(base/'ev112-wip/kit/census'),
     str(base/'bridges/terrain-ev107.npz'),str(base/'bridges/fp-ev107/footprint.npz'),str(base/'bridges/envelope-ev107.npy'),
     G.WT+'/evidence/v31-pond-layer-2026-10-13/bridges/ev110/sites-ev110.json',str(base/'ev108-kit/sites.json'),
     str(out/'sites.json'),str(out/'worklist.json'),str(base/'ev112-wip/kit/exclusions-ev112.json')]
p=subprocess.run(cmd,capture_output=True,text=True)
(out/'command.log').write_text(p.stdout+p.stderr,encoding='utf-8')
caught=p.returncode!=0 and 'AssertionError: retained water absorbed into a kit body:' in p.stderr
proof=dict(caught=bool(caught),returncode=p.returncode,command=cmd,mutation='remove only retained seed absorption protection')
(out/'negative.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print('RECEIVER ABSORPTION NEGATIVE','PASS' if caught else 'FAIL')
sys.exit(0 if caught else 1)
