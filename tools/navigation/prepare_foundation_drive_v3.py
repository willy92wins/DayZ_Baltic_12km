"""Make initial sedan placement explicit before settlement; keep motion criteria intact."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parent=ROOT/'evidence/overnight-2026-10-01/foundation-drive-v2/reference.json'
    source=ROOT/'missions/BalticFoundationDriveV2.BalticTrial'
    assert sha(source/'init.c')=='f3376e62cc8964664d650b8ef4643e924f857e91eff33261987e5001d72aaf9a'
    out=ROOT/'missions/BalticFoundationDriveV3.BalticTrial'
    ev=ROOT/'evidence/overnight-2026-10-01/foundation-drive-v3'
    destination=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/out.name
    for p in (out,ev,destination):
        if p.exists():raise ValueError('Fresh outputs required')
    code=(source/'init.c').read_text().replace('baltic_foundation_drive_v2.log','baltic_foundation_drive_v3.log')
    anchor='        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginNext,30000,false);'
    code=code.replace(anchor,'''        FileHandle placement=OpenFile("$profile:baltic_foundation_drive_v3_placement.log",FileMode.WRITE);
        if (placement) { FPrintln(placement,"BALTIC_INITIAL_SEDAN_PLACEMENT_V3"); CloseFile(placement); }
'''+anchor)
    anchor='    void BeginNext()'
    method='''    void PlacementRecord(string stage,vector wanted)
    {
        FileHandle f=OpenFile("$profile:baltic_foundation_drive_v3_placement.log",FileMode.APPEND);
        if (!f) return;
        FPrintln(f,"P;"+m_Case+";"+stage+";"+wanted.ToString()+";"+m_Car.GetPosition().ToString()+";"+m_Car.GetOrientation().ToString());
        CloseFile(f);
    }

'''
    code=code.replace(anchor,method+anchor)
    anchor='        if (!m_Car) { EndCase("SPAWN_FAILED"); return; }'
    code=code.replace(anchor,anchor+'\n        PlacementRecord("CREATED",spawn);')
    anchor='        m_Car.SetOrientation(orientation);'
    code=code.replace(anchor,anchor+'\n        PlacementRecord("ORIENTED",spawn);')
    anchor='        m_HealthStart=m_Car.GetHealth("","Health");'
    assert code.count(anchor)==1
    code=code.replace(anchor,'''        PlacementRecord("ASSEMBLED",spawn);
        // Initial setup only, before the15s settlement and all physical motion.
        m_Car.SetPosition(spawn);
        PlacementRecord("PLACED",spawn);
'''+anchor)
    out.mkdir();ev.mkdir()
    (out/'init.c').write_text(code);shutil.copy2(source/'routes.csv',out/'routes.csv');shutil.copytree(out,destination)
    ref=json.loads(parent.read_text());ref.update(status='FROZEN_BEFORE_ENGINE_PLACEMENT_CORRECTION',
        parent_reference_sha256=sha(parent),parent_mission_sha256=sha(source/'init.c'),
        mission={str(p.resolve()):sha(p) for p in out.iterdir()},
        revision='Align only initial spawn after orientation/attachments. Four placement observations in separate log. No position/velocity changes during settlement or driving; same routes, movement controller and criteria.',
        placement_api='P:/scripts/3_game/entities/object.c:300 proto native void SetPosition(vector vPos)')
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    print(json.dumps(dict(mission_sha256=sha(out/'init.c'),reference_sha256=sha(ev/'reference.json'))))

if __name__=='__main__':main()
