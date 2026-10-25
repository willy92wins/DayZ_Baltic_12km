"""Read final PBO textures through PNGs whose encoded PAA matches each packed entry."""
from pathlib import Path
import sys,json,hashlib,subprocess,time
O=Path(__file__).parent;D=O/'forest-final-tools-ae';G=D/'gates';sys.path.insert(0,str(G));import gcfg as C
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
package=O/'package-final-ae';receipt=json.loads((package/'package.json').read_text());pbo=package/'packed/narva_trial.pbo'
assert sha(pbo)==receipt['pbo_sha256'] and sha(O/'surface-final-ae/manifest.json')==receipt['manifest_sha256']
C.PBO=str(pbo);C.LAYER_DIRS=[str(O/'surface-final-ae/layers'),*C.LAYER_DIRS]
RAS=O/'forest-painted-rasters-ae';assert not RAS.exists()
import grasters
grasters.main(RAS)
BANDS=C.E/'ev112-wip/forest/gates-run/livonia-ev112-bands.json';R=O/'forest-map-51ae';runs=[]
steps=[('g2g3',[G/'g2g3_map.py',R/'records.json',RAS,BANDS,R/'g2g3-painted.json']),('g8',[G/'g8_agreement.py',R/'records.json',RAS,BANDS,R/'g8-painted.json']),('g7',[G/'g7_map.py',R/'records.json',RAS,R/'g7-painted.json','--livonia-bands',BANDS]),('g2pilot',[O/'run-painted-pilot-ae.py','G2']),('g3pilot',[O/'run-painted-pilot-ae.py','G3'])]
for name,args in steps:
 cmd=[sys.executable,'-I',*map(str,args)];t=time.time()
 with (O/f'forest-painted-ae-{name}.log').open('w',encoding='utf-8') as out:rc=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT).returncode
 runs.append(dict(step=name,rc=rc,seconds=time.time()-t,cmd=cmd));(O/'forest-painted-ae-steps.json').write_bytes((json.dumps(dict(pbo_sha256=sha(pbo),steps=runs),indent=2)+'\n').encode());print(name,rc,flush=True)
 if rc:sys.exit(rc)
