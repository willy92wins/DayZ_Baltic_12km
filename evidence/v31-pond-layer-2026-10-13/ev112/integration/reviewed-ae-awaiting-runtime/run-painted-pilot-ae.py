"""Run the unchanged strict pilot G2/G3 with textures bound to the final packed world."""
from pathlib import Path
import sys,json,hashlib,runpy
O=Path(__file__).parent;D=O/'forest-final-tools-ae';sys.path.insert(0,str(D/'gates'))
import gcfg as C
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
gate=sys.argv[1];assert gate in ('G2','G3')
pack=O/'package-final-ae';receipt=json.loads((pack/'package.json').read_text());pbo=pack/'packed/narva_trial.pbo'
assert sha(pbo)==receipt['pbo_sha256']
assert sha(O/'surface-final-ae/manifest.json')==receipt['manifest_sha256']
frozen=json.loads((O/'forest-ae-frozen.json').read_text())['files']
assert all(sha(p)==h for p,h in frozen.items())
C.PBO=str(pbo);C.LAYER_DIRS=[str(O/'surface-final-ae/layers'),*C.LAYER_DIRS]
R=O/'forest-map-51ae';script=D/'r2/gates/g2_g3.py'
sys.argv=[str(script),str(R/'pilot-subset.json'),gate,'--json',str(R/(gate.lower()+'pilot-painted.json'))]
if gate=='G2':sys.argv+=['--dense','A-reserva']
runpy.run_path(str(script),run_name='__main__')
