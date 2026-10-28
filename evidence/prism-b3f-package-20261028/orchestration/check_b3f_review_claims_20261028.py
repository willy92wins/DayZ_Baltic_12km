from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025');O=R/'b3f-review-claims-20261028';O.mkdir(exist_ok=False)
sys.path.insert(0,str(W/'tools/quality'));import prism_b3f_package_ev112 as p
rows=[]
for path in [p.BASE,p.PAIR/'candidate/packed/baltic_stream_pilot.pbo']:
 data=path.read_bytes();rows.append(dict(path=str(path),sha256=p.digest(data),tail21hex=data[-21:].hex(),sha1_excluding_21=hashlib.sha1(data[:-21]).hexdigest(),sha1_excluding_20=hashlib.sha1(data[:-20]).hexdigest(),matches_excluding_21=data[-20:]==hashlib.sha1(data[:-21]).digest(),matches_excluding_20=data[-20:]==hashlib.sha1(data[:-20]).digest()))
probes=[]
for exe in [sys.executable,str(p.runtime.reads.interpreter_image())]:
 q=subprocess.run([exe,'-I','-c','import sys,numpy;print(sys.executable);print(numpy.__file__)'],capture_output=True,timeout=15);probes.append(dict(requested_executable=exe,returncode=q.returncode,stdout=q.stdout.decode('utf-8','replace'),stderr=q.stderr.decode('utf-8','replace')))
r=dict(footer_observations=rows,interpreter_probes=probes);(O/'report.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
