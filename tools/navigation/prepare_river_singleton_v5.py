"""Resume one interrupted river case; preserve frozen physics and acceptance."""
from pathlib import Path
import argparse,datetime,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--case',type=int,choices=[6,10],required=True);a=ap.parse_args()
    parent=ROOT/'evidence/foundation-followup-2026-10-01/delta-isolated-v4/reference.json'
    source=ROOT/'missions/BalticDeltaIsolatedV4.BalticTrial/init.c'
    assert sha(source)=='5f85fd1223c1a675449b9f15be32efc1a1181a654f682f35b88c7086ee253a06'
    ref=json.loads(parent.read_text(encoding='utf-8'))
    allref=json.loads((ROOT/'evidence/foundation-followup-2026-10-01/full-river-v3/reference.json').read_text(encoding='utf-8'))
    name=f'BalticRiverSingle{a.case}V5.BalticTrial';mission=ROOT/'missions'/name
    deploy=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/name
    ev=ROOT/f'evidence/foundation-followup-2026-10-01/river-single-{a.case}-v5'
    assert not any(p.exists() for p in [mission,deploy,ev])
    for path,digest in {**ref['inputs'],**ref['deployment'],ref['terrain']:ref['terrain_sha256']}.items():assert sha(Path(path))==digest,path
    code=source.read_text(encoding='utf-8')
    edits={'m_Stage=0; m_Runner=new BalticFullRiverRunner;':'m_Stage=1; m_Runner=new BalticFullRiverRunner;','m_Runner.Start(8,0);':f'm_Runner.Start({a.case},0);','baltic_delta_isolated_v4_':f'baltic_river_single{a.case}_v5_','BALTIC_DELTA_ISOLATED_V4':f'BALTIC_RIVER_SINGLE_{a.case}_V5'}
    for old,new in edits.items():assert code.count(old)==1,old;code=code.replace(old,new)
    mission.mkdir(parents=True);ev.mkdir(parents=True)
    (mission/'init.c').write_text(code,encoding='utf-8');shutil.copy2(source.parent/'routes.csv',mission/'routes.csv');shutil.copytree(mission,deploy)
    ref.update(status='FROZEN_SINGLE_CASE_RUNTIME_PENDING',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=[next(c for c in allref['cases'] if c['case']==a.case)],selected_case_ids=[a.case],mission={str(p):sha(p) for p in mission.iterdir()},deployed_mission=str(deploy),log_prefix=f'baltic_river_single{a.case}_v5_',parent_reference_sha256=sha(parent),scope=f'Only unchanged case {a.case}, no other boat spawned; resume after interrupted V4/V3.',limits=['One empty boat on unchanged V10; no fleet, crew or medium-vessel acceptance.','Earlier full and interrupted results remain preserved.','All geometry, control logic and V3 physical/event gates unchanged.'])
    ref.pop('server_isolation',None)
    expected={**ref['inputs'],**ref['deployment'],**ref['mission'],ref['terrain']:ref['terrain_sha256']}
    for p,digest in ref['mission'].items():expected[str(deploy/Path(p).name)]=digest
    actual={p:sha(Path(p)) for p in expected};assert actual==expected
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
    (ev/'prelaunch.json').write_text(json.dumps(dict(status='PASS_FROZEN_IDENTITY_NOT_RUNTIME',files=actual,reference_sha256=sha(ev/'reference.json')),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(case=a.case,mission=str(deploy),reference_sha256=sha(ev/'reference.json'))))

if __name__=='__main__':main()
