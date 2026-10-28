from pathlib import Path
import hashlib,json,subprocess,sys,time,re
W=Path(sys.argv[1]);O=Path(sys.argv[2]);O.mkdir(exist_ok=False)
files=[W/'tools/quality'/n for n in ('build_prism_b3e2_ev112.py','preflight_b3e2_ev112.py','consume_prism_b3e2_ev112.py','test_prism_b3e2_ev112.py')]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={str(p):sha(p) for p in files};t=time.monotonic();timeout=False
with (O/'stdout.log').open('wb') as out,(O/'stderr.log').open('wb') as err:
 p=subprocess.Popen([sys.executable,'-I',str(files[-1]),'-v'],cwd=W,stdout=out,stderr=err,creationflags=0x08000000)
 (O/'running.json').write_text(json.dumps(dict(pid=p.pid,max_seconds=120)),encoding='utf-8')
 try:p.wait(timeout=120)
 except subprocess.TimeoutExpired:timeout=True;p.terminate();p.wait(timeout=10)
elapsed=time.monotonic()-t;text=(O/'stderr.log').read_text(encoding='utf-8');match=re.search(r'Ran (\d+) tests?',text);count=int(match[1]) if match else 0
r=dict(status='TESTS_PASS' if p.returncode==0 and not timeout and elapsed<=120 and count>0 and all(sha(Path(p))==h for p,h in pins.items()) else 'TESTS_FAIL',tests=count,seconds=elapsed,returncode=p.returncode,timeout=timeout,postimages=pins)
(O/'report.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r));raise SystemExit(0 if r['status']=='TESTS_PASS' else 1)
