"""Prepare the four bounded V3 river checks on the unchanged V10 world."""
from pathlib import Path
import datetime, hashlib, json, shutil

ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ev=ROOT/'evidence/foundation-followup-2026-10-01/full-river-v3'
    mission=ROOT/'missions/BalticFullRiverV3.BalticTrial'
    dest=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    assert not ev.exists() and not mission.exists() and not dest.exists(), 'Fresh outputs required'
    parent=ROOT/'evidence/overnight-2026-10-01/full-river-v2/reference.json'
    ref=json.loads(parent.read_text(encoding='utf-8'))
    source=ROOT/'missions/BalticFullRiverV2.BalticTrial/init.c'
    assert sha(source)=='2b47bdc8613139f3e0992a85d7ad5b741e04f1bb8f4eb3e2a65c447233f7617c'
    for path,digest in {**ref['inputs'],**ref['deployment'],ref['terrain']:ref['terrain_sha256']}.items():
        assert sha(Path(path))==digest, path
    code=source.read_text(encoding='utf-8')
    def change(old,new):
        nonlocal code
        assert code.count(old)==1, old
        code=code.replace(old,new,1)
    change('void Start(int caseIndex)','void Start(int caseIndex, int startSlot)')
    change('30000+60000*m_Case','30000+60000*startSlot')
    change('baltic_fullriver_v2_', 'baltic_fullriver_v3_')
    change('BALTIC_FULL_RIVER_V2', 'BALTIC_FULL_RIVER_V3')
    change('float steer=0; float throttle=0;', 'bool targetChanged=false; bool arrivalChanged=false;\n        float steer=0; float throttle=0;')
    change('''                    m_Arrived=seconds;
                    m_Boat.BalticProbeStop();
                    FPrintln(m_Log,"ARRIVED;"+m_Case+";"+seconds+";"+pos);''', '''                    if (delta.Length() < 1.5 && speed <= 0.8)
                    {
                        m_Arrived=seconds; arrivalChanged=true;
                        m_Boat.BalticProbeStop();
                        FPrintln(m_Log,"ARRIVED;"+m_Case+";"+seconds+";"+pos);
                    }''')
    change('''                    m_Target++;
                    delta=m_Route[m_Target] - pos;delta[1]=0;''', '''                    int previousTarget=m_Target;
                    float targetDistance=delta.Length();
                    m_Target++;
                    targetChanged=true;
                    FPrintln(m_Log,"T;"+m_Case+";"+seconds+";"+previousTarget+";"+m_Target+";"+pos.ToString()+";"+targetDistance);
                    delta=m_Route[m_Target] - pos;delta[1]=0;''')
    change('if (seconds>=20 && speed<=2.5) throttle=0.22;', '''float speedLimit=2.5;
                vector endpointDelta=m_Route[m_Route.Count() - 1] - pos;
                endpointDelta[1]=0;
                if (m_Target >= m_Route.Count() - 8 && endpointDelta.Length() < 20) speedLimit=0.8;
                if (m_Target >= m_Route.Count() - 4 && endpointDelta.Length() < 8) speedLimit=0.5;
                if (seconds>=20 && speed<=speedLimit) throttle=0.22;''')
    change('if (m_Tick%5==0)', 'if (m_Tick%5==0 || targetChanged || arrivalChanged)')
    change('for (int i=0;i<12;i++)','for (int i=0;i<4;i++)')
    change('m_Runners.Insert(runner); runner.Start(i);', '''m_Runners.Insert(runner);
            int caseId=11;
            if (i==1) caseId=6;
            else if (i==2) caseId=8;
            else if (i==3) caseId=10;
            runner.Start(caseId,i);''')
    mission.mkdir(parents=True);ev.mkdir(parents=True)
    (mission/'init.c').write_text(code,encoding='utf-8')
    shutil.copy2(source.parent/'routes.csv',mission/'routes.csv')
    shutil.copytree(mission,dest)
    selected=[11,6,8,10]
    ref['cases']=[next(c for c in ref['cases'] if c['case']==i) for i in selected]
    ref['channels']=[]
    ref.update(status='FROZEN_DEPLOYED_ENGINE_PENDING',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        mission={str(p):sha(p) for p in mission.iterdir()},deployed_mission=str(dest),
        parent_reference_sha256=sha(parent),parent_mission_sha256=sha(source),
        log_prefix='baltic_fullriver_v3_',event_version=1,
        selected_case_ids=selected,scope='Unchanged V2 geometry: one control and three previously failing segments.',
        event_criteria=dict(max_transition_distance_m=4.,max_transition_sample_dt_s=.002,arrival_distance_m=1.5,arrival_speed_mps=.8,engine_off_observation_s=9.),
        limits=['Four selected original segments only; original V2 failures preserved.',
            'Empty boats with engine input; no crew or medium-vessel acceptance.',
            'Legacy ARRIVED_AND_STOPPED means arrival and engine release, not zero speed.',
            'All previous physical tolerances unchanged; added event checks and tighter arrival control.'])
    world=Path('P:/Mods/@DayZ_Baltic_FoundationV10Native/Addons')
    for name,expected in [('narva_trial.pbo','d1008dd6c882193706f06c5e7b8495ee1a357f5819a8574118784f7e90f18577'),('baltic_water.pbo','f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3')]:
        assert sha(world/name)==expected
        ref['deployment'][str(world/name)]=expected
    for p in mission.iterdir():assert sha(dest/p.name)==sha(p)
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=ref['status'],cases=selected,mission_sha256=sha(mission/'init.c'),reference=str(ev/'reference.json'))))

if __name__=='__main__':main()
