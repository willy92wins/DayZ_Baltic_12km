from pathlib import Path
import subprocess,json,hashlib,sys,time,os
R=Path(__file__).parent;O=R/'kit7-compiled-contact-20261026';O.mkdir(exist_ok=False)
source=R/'verify_kit7_compiled_contact.py';K=R/'river-kit7-midpoint-a-20261026'
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
inputs={str(p):sha(p) for p in [source,Path(__file__),K/'author-report.json',K/'records.json',K/'binary-review.json',K/'packed/baltic_stream_pilot.pbo',R/'kit7-midpoint-build-20261026/receipt.json']}
(O/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
args=[sys.executable,'-I',str(source)];began=time.time();timeout=False
with (O/'stdout.log').open('wb') as out,(O/'stderr.log').open('wb') as err:
 try:q=subprocess.run(args,env=env,stdout=out,stderr=err,timeout=1800,creationflags=0x08000000|0x00004000);code=q.returncode
 except subprocess.TimeoutExpired:timeout=True;code=None
same=all(sha(p)==h for p,h in inputs.items())
(O/'receipt.json').write_text(json.dumps(dict(returncode=code,timeout=timeout,seconds=time.time()-began,inputs_unchanged=same,args=args,limits='Read-only packed geometry validation; independent code review still required before acceptance/integration.'),indent=2)+'\n')
print('COMPILED_CONTACT_EXIT',code,'INPUTS_UNCHANGED',same);raise SystemExit(0 if code==0 and same and not timeout else 1)
