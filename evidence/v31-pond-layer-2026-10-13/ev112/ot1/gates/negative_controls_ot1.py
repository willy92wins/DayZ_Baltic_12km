"""One independent mutation per directory; requires a passing positive gate.
Usage: negative_controls_ot1.py <run> <output-root> <stones-buried|seat-pair|seat-triangle|owner-gap>
"""
import json, os, pathlib, shutil, subprocess, sys
import numpy as np
from scipy.ndimage import binary_dilation
from scipy.spatial import cKDTree
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import gatelib as G
src, root, mode = pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3]
gate = 'g10' if mode=='stones-buried' else 'g9'
assert json.loads((src/f'gate-{gate}.json').read_text())['passed'], 'positive baseline must pass'
out=root/mode; out.mkdir(parents=True,exist_ok=False)
names=['terrain-kit.npz','kit-records.json','kit-report.json','envelope-ev108.npy','cover-ev108.npy']
for name in names:
    if (mode=='stones-buried' and name=='kit-records.json') or (mode!='stones-buried' and name=='terrain-kit.npz'):
        shutil.copyfile(src/name,out/name)
    else:
        os.link(src/name,out/name)
proof={}
if mode=='stones-buried':
    records=json.loads((out/'kit-records.json').read_text())
    for r in records:
        if r['piece']=='stones':r['matrix'][10]-=10
    (out/'kit-records.json').write_text(json.dumps(records),encoding='utf-8')
else:
    z=np.load(src/'terrain-kit.npz'); arrays={k:z[k].copy() for k in z.files}; H=arrays['heights']
    rep=json.loads((src/'kit-report.json').read_text())
    if mode=='owner-gap':
        owner=binary_dilation(arrays['v31_kit'],np.ones((3,3),bool),iterations=2)
        coords=np.argwhere(owner & ~arrays['reserve'] & ~arrays['platform'] & ~arrays['narva'])
        lines=[]
        for s in rep['sites']:
            if 'skipped' in s:continue
            V=np.array(s['lattice']); length=np.linalg.norm(np.diff(V,axis=0),axis=1).sum()
            lines.append(G.at(V,np.arange(0,length+.01,.5)))
        tree=cKDTree(np.vstack(lines)); world=np.c_[6.*coords[:,1],G.ZTOP-6.*coords[:,0]]
        d=tree.query(world)[0]; elig=np.flatnonzero((d>25)&(coords[:,0]>3)&(coords[:,0]<2044)&(coords[:,1]>3)&(coords[:,1]<2044))
        assert len(elig),'need a protected vertex beyond the old 24m band'
        k=int(elig[0]); r,c=map(int,coords[k]); shape=[(0,0)]
        proof['distance_to_lattice_m']=float(d[k])
    else:
        s=next(s for s in rep['sites'] if s.get('mode')=='reach' and 'skipped' not in s)
        V=np.array(s['lattice']); p=V[len(V)//2]; r,c=int(round((G.ZTOP-p[1])/6)),int(round(p[0]/6))
        shape=[(0,0),(0,1)] if mode=='seat-pair' else [(0,0),(0,1),(1,1)]
    target=float(H[r-2:r+4,c-2:c+4].max())+2
    for dr,dc in shape:H[r+dr,c+dc]=target
    proof.update(anchor_xz=[6*c,G.ZTOP-6*r],shape=shape,top=target)
    np.savez(out/'terrain-kit.npz',**arrays)
script='gate_g10_stones.py' if gate=='g10' else 'gate_g9_mounds.py'
cmd=[sys.executable,'-I',str(pathlib.Path(__file__).parent/script),str(out)]
p=subprocess.run(cmd,capture_output=True,text=True)
(out/'gate.log').write_text(p.stdout+p.stderr,encoding='utf-8')
result=json.loads((out/f'gate-{gate}.json').read_text())
caught=not result['passed'] and p.returncode==1
if mode=='stones-buried':
    caught &= result['failures'].get('visibility_below_25_percent',{}).get('n')==result['stones']
else:
    caught &= result['new_shapes']>0
proof.update(mode=mode,positive_run=str(src),caught=bool(caught),command=cmd)
(out/'negative.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps(proof)); print('NEGATIVE','PASS' if caught else 'FAIL')
sys.exit(0 if caught else 1)
