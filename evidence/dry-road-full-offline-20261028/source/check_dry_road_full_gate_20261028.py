"""Read-only gate; the MCP launch must be conditional on its successful output."""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parent;O=R/'dry-road-full-native-20261028';W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');sys.path.insert(0,str(W/'tools/quality'))
from buried_roadway_semantics_ev112 import require,verify_frozen
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
require(len(sys.argv) in (3,4) and sys.argv[1] in ('calibration','probe'),'mode_and_seal_required')
mode=sys.argv[1];verify_frozen({str(O/'accepted.json'):sys.argv[2]});a=read(O/'accepted.json')
require(a['status']=='REVIEWED_FULL_NATIVE_READY','not_reviewed')
required=[O/n for n in ('deployment.json','prelaunch.json','points.json')]
require(all(str(p) in a['inputs'] for p in required),'unsealed_inputs');verify_frozen(a['inputs'])
d=read(required[0]);pre=read(required[1]);verify_frozen(d['inputs']);verify_frozen(d['deployed']);expected={**d['deployed'],pre['bridge_pbo']:pre['bridge_sha256']}
verify_frozen({pre['executable']:pre['executable_sha256'],pre['bridge_pbo']:pre['bridge_sha256']})
require(not (O/mode/'launch.json').exists(),'unit_already_launched')
if mode=='probe':
    require(len(sys.argv)==4,'calibration_hash_required');p=O/'calibration/result.json';verify_frozen({str(p):sys.argv[3]});ref=read(p)
    require(ref['status']=='CALIBRATION_PASS' and ref['identity_bound'] and ref['packages']==expected and ref['engine_sha256']==pre['executable_sha256'],'calibration_binding');verify_frozen(ref['inputs'])
print(json.dumps(dict(status='PRE_FIFO_GATE_PASS',mode=mode,mission=d['units'][mode]['mission'],mod=d['mod'],accepted_sha256=sys.argv[2],calibration_sha256=sys.argv[3] if mode=='probe' else None)))
