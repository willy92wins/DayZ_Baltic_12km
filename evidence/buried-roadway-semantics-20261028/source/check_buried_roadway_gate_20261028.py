"""Read-only pre-FIFO gate. No DayZ process or MCP interaction."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/quality'))
from buried_roadway_semantics_ev112 import require,verify_frozen

def check(folder,expected_seal):
    read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
    accept=folder/'accepted.json'
    verify_frozen({str(accept):expected_seal})
    a=read(accept);require(a['status']=='REVIEWED_DIAGNOSTIC_READY','not_reviewed')
    required=[folder/x for x in ('deployment.json','prelaunch.json','points.json')]
    require(all(str(p) in a['inputs'] for p in required),'unsealed_deployment')
    verify_frozen(a['inputs'])
    d=read(required[0]);p=read(required[1]);q=read(required[2])
    require(d['status']=='PREPARED_DIAGNOSTIC_NOT_RUN' and d['count']==q['count']==16,'wrong_probe')
    verify_frozen(d['inputs']);verify_frozen(d['deployed'])
    verify_frozen({p['executable']:p['executable_sha256'],p['bridge_pbo']:p['bridge_sha256']})
    require(not (folder/'run/launch.json').exists(),'already_launched')
    return dict(status='PRE_FIFO_GATE_PASS',accepted_sha256=expected_seal,mission=d['mission'],mod=d['mod'])

if __name__=='__main__':
    require(len(sys.argv)==2,'expected_seal_required')
    print(json.dumps(check(R/'buried-roadway-semantics-20261028',sys.argv[1])))
