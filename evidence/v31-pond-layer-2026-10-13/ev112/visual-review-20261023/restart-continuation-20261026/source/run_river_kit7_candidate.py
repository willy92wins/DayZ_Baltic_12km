from pathlib import Path
import hashlib,json,os,subprocess,sys,datetime
R=Path(__file__).parent;D=R/'river-kit7-a-run-20261026';O=R/'river-kit7-a-on-f-20261026'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
base=R/'rectangle-pilot-f-merged'
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
inputs={str(W/'tools/water/continuous_stream_pilot_v31.py'):'8b340a2ab4e25d69ff9baf46f71c8f843c9da2c02137c32fa356a0bb9deb9169',str(base/'terrain-buried.npz'):'caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc',str(base/'bury-work/fp0/footprint.npz'):'95f7a26304e88c726679ec69ef076bb149ec1f1f8bdf4a6cd1e83e40f3b6be83'}
for p,h in inputs.items():assert sha(p)==h
assert json.loads((R/'river-bounds-next-20261026/kit-7/report.json').read_text())['conflicts']==0
D.mkdir(exist_ok=False);assert not O.exists()
args=[sys.executable,'-I',str(W/'tools/water/continuous_stream_pilot_v31.py'),str(B),str(O),'--sites','kit-7','--candidate-base',str(base),'--expected-terrain-sha256',inputs[str(base/'terrain-buried.npz')],'--expected-footprint-sha256',inputs[str(base/'bury-work/fp0/footprint.npz')]]
env=dict(os.environ);env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
receipt=dict(status='AUTHOR_STARTED',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),args=args,inputs=inputs,timeout_s=1800)
(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
with (D/'stdout.log').open('wb') as out,(D/'stderr.log').open('wb') as err:
 try:
  q=subprocess.run(args,cwd=W,env=env,stdout=out,stderr=err,timeout=1800,creationflags=0x08000000|0x00004000)
  receipt.update(status='AUTHOR_EXIT_ZERO_PENDING_INDEPENDENT_REVIEW' if q.returncode==0 else 'AUTHOR_FAILED',returncode=q.returncode)
 except subprocess.TimeoutExpired:receipt.update(status='AUTHOR_TIMEOUT',returncode=None)
receipt['inputs_unchanged']=all(sha(p)==h for p,h in inputs.items())
receipt['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('args','inputs')},indent=2))
raise SystemExit(0 if receipt['returncode']==0 and receipt['inputs_unchanged'] else 1)

