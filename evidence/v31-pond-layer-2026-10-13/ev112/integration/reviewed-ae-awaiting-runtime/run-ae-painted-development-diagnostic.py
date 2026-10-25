"""AE records against hash-bound AD painted surface, only after exact nonbush/mask identity.

AD WRP is not an AE release. This diagnostic cannot authorize deployment and
all consumers must repeat against the compiled AE world for final acceptance.
"""
from pathlib import Path
import sys,json,hashlib,subprocess,time,runpy
O=Path(__file__).parent;D=O/'forest-final-tools-ae';G=D/'gates';R=O/'forest-map-51ae';ROOT=O/'forest-painted-development-ae'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
frozen=json.loads((O/'forest-ae-frozen.json').read_text())['files'];assert all(sha(p)==h for p,h in frozen.items())
identity=json.loads((O/'forest-ae-map-nonbush-identity.json').read_text());assert identity['status']=='NON_BUSH_IDENTICAL'
report=json.loads((R/'report.json').read_text());assert identity['b']['records_sha256']==report['records_sha256']==sha(R/'records.json')
package=json.loads((O/'package-final-ad/package.json').read_text());pbo=Path(package['pbo']);assert sha(pbo)==package['pbo_sha256']
assert sha(package['manifest'])==package['manifest_sha256']
sys.path.insert(0,str(G));import gcfg as C
C.PBO=str(pbo);C.LAYER_DIRS=[str(O/'surface-final-ad/layers'),*C.LAYER_DIRS]
if len(sys.argv)>1:
    gate=sys.argv[1];assert gate in ('G2','G3');script=D/'r2/gates/g2_g3.py'
    sys.argv=[str(script),str(R/'pilot-subset.json'),gate,'--json',str(ROOT/(gate+'pilot.json'))]
    if gate=='G2':sys.argv+=['--dense','A-reserva']
    runpy.run_path(str(script),run_name='__main__');raise SystemExit(0)
assert not ROOT.exists();ROOT.mkdir();runs=[]
def run(name,args):
    assert all(sha(p)==h for p,h in frozen.items())
    cmd=[sys.executable,'-I',*map(str,args)];t=time.time()
    with (ROOT/(name+'.log')).open('w',encoding='utf-8') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
    runs.append(dict(step=name,rc=rc,seconds=time.time()-t,cmd=cmd));(ROOT/'steps.json').write_text(json.dumps(dict(scope=__doc__,steps=runs),indent=2)+'\n')
    print(name,rc,round(time.time()-t,1),flush=True);return rc
exporter=O/'surface-trial-clearings400/make_forest_clearings_v31.py'
assert sha(exporter)=='59c493791bac9542ccc43bf6c36a08da551e48d54216639ccc1c12d0c1a273d4'
assert run('clearings',[exporter,R/'records.json',C.REFERENCE,O/'forest-final-rasters-c',ROOT/'clearings','--moss',R/'work/moss1m.npy','--moss-sha256',report['work_sha256']['moss1m.npy']])==0
m=json.loads((ROOT/'clearings/manifest.json').read_text());old=json.loads((O/'clearings-final-ad/manifest.json').read_text());planned=report['planned_clearings']
assert m['mask_sha256']==sha(m['mask'])==old['mask_sha256']==sha(old['mask'])==planned['sha256']==sha(planned['path'])
assert planned['points_sha256']==report['accepted_canopy']['points']['sha256']
assert m['moss']['sha256']==old['moss']['sha256']==report['work_sha256']['moss1m.npy']
ras=O/'forest-painted-rasters-ad';meta=json.loads((ras/'grasters.json').read_text())
assert all(sha(ras/n)==h for n,h in meta['files'].items())
assert meta['inputs']['terrain_sha256']==sha(C.TERRAIN) and meta['inputs']['footprint_sha256']==sha(C.FOOTPRINT) and Path(meta['inputs']['pbo'])==pbo
bands=C.E/'ev112-wip/forest/gates-run/livonia-ev112-bands.json'
for name,script in [('g2g3','g2g3_map.py'),('g8','g8_agreement.py')]:run(name,[G/script,R/'records.json',ras,bands,ROOT/(name+'.json')])
run('g7',[G/'g7_map.py',R/'records.json',ras,ROOT/'g7.json','--livonia-bands',bands])
for gate in ('G2','G3'):run(gate+'pilot',[Path(__file__),gate])
ok=all(r['rc']==0 for r in runs)
(ROOT/'binding.json').write_text(json.dumps(dict(scope=__doc__,records_sha256=sha(R/'records.json'),source_sha256=sha(D/'forest_v31.py'),surface_pbo_sha256=sha(pbo),clearings_mask_sha256=m['mask_sha256'],planned_mask_matches_independent=True,nonbush_identity_sha256=sha(O/'forest-ae-map-nonbush-identity.json'),frozen_manifest_sha256=sha(O/'forest-ae-frozen.json'),all_gates_pass=ok,release_acceptance=False),indent=2)+'\n')
raise SystemExit(0 if ok else 1)
