"""Raise an actual junction's native terrain and require its continuous-gap failure.
Usage: negative_junction_cut.py <passing-run> <fresh-output>
An unrelated failed gate is insufficient: the mutated site's end must exceed 6 m.
"""
import json, os, pathlib, subprocess, sys
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import gatelib as G

src,out=map(pathlib.Path,sys.argv[1:3])
positive=json.loads((src/'gate-g11.json').read_text())
assert positive['passed'],'a passing positive is required'
out.mkdir(parents=True,exist_ok=False)
for name in ('kit-records.json','kit-report.json','envelope-ev108.npy','cover-ev108.npy'):
    os.link(src/name,out/name)
fps=sorted((src/'bury-work').glob('fp*/footprint.npz'),key=lambda p:int(p.parent.name[2:]))
assert fps
(out/'bury-work/fp0').mkdir(parents=True)
os.link(fps[-1],out/'bury-work/fp0/footprint.npz')
rep=json.loads((src/'kit-report.json').read_text())
by_site={s['site']:s for s in rep['sites'] if 'skipped' not in s}
chosen=next(j for j in positive['junctions'] if j['passed'] and j['path_m']>=12 and j['type'] in ('pond','bridge'))
s=by_site[chosen['site']];V=np.array(s['lattice']);end=chosen['end']
station=s['wet_span'][0 if end=='up' else 1]
inner=np.clip(station+(12 if end=='up' else -12),*s['wet_span'])
Q=G.at(V,np.linspace(station,inner,121))
rr=np.floor((G.ZTOP-Q[:,1])/6).astype(int);cc=np.floor(Q[:,0]/6).astype(int)
vertices=sorted({(int(r+dr),int(c+dc)) for r,c in zip(rr,cc) for dr in (0,1) for dc in (0,1)})
z=np.load(src/'terrain-kit.npz');arrays={k:z[k].copy() for k in z.files};H=arrays['heights']
height=max(float(H[v]) for v in vertices)+30
for v in vertices:H[v]=height
np.savez(out/'terrain-kit.npz',**arrays)
cmd=[sys.executable,'-I',str(pathlib.Path(__file__).with_name('gate_g11_junctions.py')),str(out)]
p=subprocess.run(cmd,capture_output=True,text=True)
(out/'gate.log').write_text(p.stdout+p.stderr,encoding='utf-8')
result=json.loads((out/'gate-g11.json').read_text())
row=next(j for j in result['junctions'] if j['site']==chosen['site'] and j['end']==end)
caught=p.returncode==1 and not result['passed'] and not row['passed'] and row.get('max_dry_m',0)>6
proof=dict(positive_run=str(src),positive=chosen,mutation=dict(vertices=vertices,height_m=height),
           targeted_result=row,caught=bool(caught),command=cmd)
(out/'negative.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print('JUNCTION CUT NEGATIVE','PASS' if caught else 'FAIL',row)
sys.exit(0 if caught else 1)
