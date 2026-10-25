"""Rebuild all step-1 outputs in a fresh interpreter and compare exact bytes.
Usage: verify_step1.py baseline_dir fresh_repeat_dir
Step 0 has its separate fresh-process check; this consumes that verified sites file.
"""
import hashlib,json,pathlib,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import gatelib as G
baseline,repeat=map(pathlib.Path,sys.argv[1:3])
assert not repeat.exists(),'repeat directory must be fresh'
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
sources=[pathlib.Path(G.WT)/'tools/water/streambed_kit_v31.py',pathlib.Path(G.GEOM),
         pathlib.Path(G.WT)/'tools/water/streambed_stones_geometry_v31.json']
inputs=[pathlib.Path(x) if pathlib.Path(x).is_absolute() else pathlib.Path(G.B)/x for x in G.chain()['args'][1:6]]
before={str(p):sha(p) for p in sources+inputs}
cmd=[sys.executable,'-I',str(pathlib.Path(__file__).with_name('gate_g1_cli.py')),str(repeat)]
proc=subprocess.run(cmd,capture_output=True,text=True)
repeat.mkdir(exist_ok=True)
(repeat/'determinism-command.log').write_text(proc.stdout+proc.stderr)
checks={'fresh_process_exit':proc.returncode==0,'sources_and_inputs_unchanged':before=={str(p):sha(p) for p in sources+inputs}}
outputs={}
for name in ('terrain-kit.npz','cover-ev108.npy','envelope-ev108.npy','kit-records.json','kit-report.json'):
    hashes=[sha(p/name) if (p/name).exists() else None for p in (baseline,repeat)]
    checks[name]=bool(hashes[0] and hashes[0]==hashes[1]);outputs[name]=hashes
result=dict(passed=all(checks.values()),checks=checks,inputs_and_sources=before,output_sha256=outputs,command=cmd)
(repeat/'determinism.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));print('STEP1','PASS' if result['passed'] else 'FAIL')
sys.exit(0 if result['passed'] else 1)
