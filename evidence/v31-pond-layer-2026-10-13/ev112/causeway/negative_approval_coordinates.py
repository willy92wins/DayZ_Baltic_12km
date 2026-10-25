"""Exercise the actual gate against the two review escapes. Synthetic approvals are fixture data only."""
from pathlib import Path
import copy,hashlib,json,subprocess,sys
import numpy as np
P=Path(__file__).resolve().parents[4]
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013')
O=Path(sys.argv[1]);O.mkdir(parents=True,exist_ok=False)
BASE=B/'ev112-wip/causeway/r2/final'
G=Path(__file__).with_name('gate_causeway.py')
SPEC=Path(__file__).with_name('acceptance-ev112.json')
spec=json.loads(SPEC.read_text()); report=json.loads((BASE/'causeway-report.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
results={}
for name,approval,shift in [('unapproved',None,False),('false',{'approved':False},False),('string',{'approved':'false'},False),('fixture-positive',{'approved':True},False),('shifted-centre',{'approved':True},True)]:
    d=O/name;d.mkdir();sp=copy.deepcopy(spec);rp=copy.deepcopy(report)
    for c in sp['clusters']:
        if c['id'] not in ('c0','c1'):c['approval']=approval
    terrain=BASE/'terrain-cw.npz'
    if shift:
        c=next(c for c in sp['clusters'] if c['id']=='c2');c['x']=c['z']=100
        src=np.load(terrain);a={k:src[k].copy() for k in src.files}
        a['heights'][465,1704]+=0.01  # (10224,9492), 94.64 m from the real c2 centre.
        a['v31_causeway'][465,1704]=True
        terrain=d/'changed.npz';np.savez(terrain,**a)
        rp['output']['terrain_sha256']=sha(terrain)
    (d/'spec.json').write_text(json.dumps(sp));rp['inputs']['spec_sha256']=sha(d/'spec.json')
    (d/'report.json').write_text(json.dumps(rp))
    args=[sys.executable,'-I',str(G),str(B/'ev110/terrain-ev110.npz'),str(B/'ev110/fp-ev110/footprint.npz'),str(terrain),str(B/'ev110/kit/cover-ev108.npy'),str(B/'ev110/bridges/envelope-br.npy'),str(d/'report.json'),str(d/'spec.json'),str(d/'work'),str(d/'gate.json'),'--tools',str(P/'tools')]
    with (d/'gate.log').open('w') as f:r=subprocess.run(args,cwd=P,stdout=f,stderr=subprocess.STDOUT)
    g=json.loads((d/'gate.json').read_text())
    if shift:
        ok=r.returncode==1 and any('coordinates' in s for s in g['G0']) and next(c for c in g['G8_clusters'] if c['id']=='c2')['changed_within_150m']>0
    else:ok=r.returncode==(0 if name=='fixture-positive' else 2) and not g['fails']
    results[name]=dict(passed=ok,rc=r.returncode,verdict=g['verdict'],fails=g['fails'],pending=g['pending'])
    print(name,ok,flush=True)
out=dict(passed=all(r['passed'] for r in results.values()),gate_sha256=sha(G),cases=results,note='Approvals exist only in synthetic fixture specs, not in the production acceptance spec.')
(O/'summary.json').write_text(json.dumps(out,indent=2));sys.exit(0 if out['passed'] else 1)
