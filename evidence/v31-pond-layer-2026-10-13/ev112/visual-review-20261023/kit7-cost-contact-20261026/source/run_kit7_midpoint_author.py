from pathlib import Path
import subprocess,json,hashlib,sys,time,os,datetime
R=Path(__file__).parent;O=R/'kit7-midpoint-author-run-20261026';O.mkdir(exist_ok=False)
source=R/'author_kit7_midpoint_collision.py';receipt=R/'kit7-midpoint-review/accepted.json'
accepted=json.loads(receipt.read_text());assert accepted['status']=='ACCEPTED_FOR_ONE_AUTHOR'
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
assert all(sha(p)==d for p,d in accepted['inputs'].items())
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
start=time.time();timeout=False;args=[sys.executable,'-I',str(source)]
with (O/'stdout.log').open('wb') as out,(O/'stderr.log').open('wb') as err:
 try:q=subprocess.run(args,env=env,stdout=out,stderr=err,timeout=1800,creationflags=0x08000000|0x00004000);code=q.returncode
 except subprocess.TimeoutExpired:code=None;timeout=True
same=all(sha(p)==d for p,d in accepted['inputs'].items())
data=dict(returncode=code,timeout=timeout,seconds=time.time()-start,inputs_unchanged=same,accepted_sha256=sha(receipt),source_sha256=sha(source),finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),args=args,limits='Isolated author only; independent saved costs and full overlay, compilation and native gates remain separate.')
(O/'receipt.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2));assert same;raise SystemExit(2 if timeout else code)
