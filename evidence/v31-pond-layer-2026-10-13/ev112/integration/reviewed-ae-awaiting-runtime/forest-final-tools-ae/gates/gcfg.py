from pathlib import Path
import sys,json,hashlib
E=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013')
F111=E/'ev111-wip/forest'
TOOL_DIR=Path(__file__).resolve().parent.parent
doc=json.loads((TOOL_DIR/'final-inputs.json').read_text(encoding='utf-8'))
def bound(key):
 p=Path(doc[key]['path'])
 if not p.is_file():raise ValueError('missing final input: '+key)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=doc[key]['sha256']:raise ValueError('changed final input: '+key)
 return p
TERRAIN=bound('terrain');FOOTPRINT=bound('footprint');STAGE_WRP=bound('stage_wrp')
EXCLUSIONS=bound('exclusions')
PBO=str(bound('pbo'));LAYER_DIRS=doc['layer_dirs']
REFERENCE=F111/'ref-v2/livonia-reference-v31.json'
LAYERS=F111/'layers.npz';SECTORS=F111/'sectors.json';PINES=F111/'bog/livonia-pines.json'
R2_GATES=TOOL_DIR/'r2/gates'
LIVONIA=E/'handoff-20261018/deps/forest-livonia'
MAP,N,ZTOP=12288,2048,12282
sys.path.insert(0, str(TOOL_DIR.parent / "terrain"))
def tool():
 sys.path.insert(0,str(TOOL_DIR))
 import forest_v31
 return forest_v31
