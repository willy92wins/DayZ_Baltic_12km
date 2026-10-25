"""Freeze and package a native moving-human pursuit; preserve previous failures."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
import numpy as np
import rasterio
from waterway_common import sample

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parent=ROOT/'evidence/overnight-2026-10-01/regional-chase-v1/reference.json'
    previous=json.loads(parent.read_text());terrain=Path(previous['terrain'])
    assert sha(terrain)==previous['terrain_sha256']
    with rasterio.open(terrain) as ds:height=ds.read(1)
    bridge=previous['bridge'];center=np.array(bridge['center_xz']);axis=np.array(bridge['axis_xz'])
    def position(xz):
        xz=np.asarray(xz,dtype='float32').astype(float)
        y=float(sample(height,np.array([xz[0]+200000]),np.array([xz[1]]))[0])+.05
        return np.asarray([xz[0],y,xz[1]],dtype='float32').astype(float).tolist()
    control=previous['cases'][0]
    start=np.array(control['start'])[[0,2]];goal=np.array(control['goal'])[[0,2]]
    direction=(goal-start)/np.linalg.norm(goal-start)
    cases=[dict(case=0,name='moving_local_control',kind='ground',start=position(start),prey_start=position(start+12*direction),goal=position(goal),timeout_s=90)]
    for reverse in (False,True):
        sign=-1 if reverse else 1
        cases.append(dict(case=len(cases),name='bridge_continuous_'+('west' if reverse else 'east'),kind='bridge',
            start=position(center-sign*160*axis),prey_start=position(center-sign*148*axis),goal=position(center+sign*148*axis),timeout_s=500))
    for c in cases:
        c['route_length_xz_m']=float(np.linalg.norm(np.array(c['goal'])[[0,2]]-np.array(c['start'])[[0,2]]))
    name='continuous-pursuit-v1';prefix='baltic_continuous_pursuit_v1'
    ev=ROOT/'evidence/overnight-2026-10-01'/name;out=ROOT/'packages'/name
    mission=ROOT/'missions/BalticContinuousPursuitV1.BalticTrial'
    deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    mod=Path('P:/Mods/@BalticContinuousPursuitV1')
    for p in (ev,out,mission,deployed,mod):
        if p.exists():raise ValueError('Fresh outputs required: '+str(p))
    ev.mkdir(parents=True);mission.mkdir();stage=out/prefix
    (stage/'scripts/4_World').mkdir(parents=True);(stage/'scripts/5_Mission').mkdir()
    sources=ROOT/'tools/navigation'
    player=stage/'scripts/4_World/BalticPursuitPlayer.c'
    client=stage/'scripts/5_Mission/BalticPursuitClient.c'
    shutil.copy2(sources/'continuous_pursuit_player.c',player)
    code=(sources/'continuous_pursuit_client.c').read_text()
    goals='\n'.join('        if (command == '+str(c['case']+1)+') return "'+' '.join(f'{n:.9g}' for n in c['goal'])+'";' for c in cases)
    assert code.count('// FROZEN_GOALS')==1
    client.write_text(code.replace('        // FROZEN_GOALS',goals))
    shutil.copy2(sources/'continuous_pursuit_init.c',mission/'init.c')
    rows=[str(c['case'])+';'+';'.join(' '.join(f'{v:.9g}' for v in c[key]) for key in ('start','prey_start','goal')) for c in cases]
    (mission/'cases.csv').write_text('\n'.join(rows)+'\n')
    config='''class CfgPatches
{
    class PREFIX { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","DZ_Scripts"}; };
};
class CfgMods
{
    class PREFIX
    {
        type="mod"; dependencies[]={"World","Mission"};
        class defs
        {
            class worldScriptModule { value=""; files[]={"PREFIX/scripts/4_World"}; };
            class missionScriptModule { value=""; files[]={"PREFIX/scripts/5_Mission"}; };
        };
    };
};
'''.replace('PREFIX',prefix)
    (out/'config.cpp').write_text(config);addons=out/'Addons';addons.mkdir()
    tools=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
    commands=[[tools/'CfgConvert/CfgConvert.exe','-bin','-dst',stage/'config.bin',out/'config.cpp'],
              [tools/'PboUtils/FileBank.exe','-property','prefix='+prefix,'-property','product=dayz ugc','-dst',addons,stage]]
    for index,command in enumerate(commands):
        result=subprocess.run(list(map(str,command)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/f'command-{index}.log').write_bytes(result.stdout)
        if result.returncode:raise RuntimeError('Build failed')
    pbo=addons/(prefix+'.pbo');_,properties,entries=read_pbo(pbo)
    expected={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    assert properties['prefix']==prefix and entries==expected and len(entries)==3
    assert entries['config.bin'].startswith(b'\0raP') and 'config.cpp' not in entries
    (mod/'Addons').mkdir(parents=True);shutil.copy2(pbo,mod/'Addons'/pbo.name);shutil.copytree(mission,deployed)
    assert sha(pbo)==sha(mod/'Addons'/pbo.name)
    for p in mission.iterdir():assert sha(p)==sha(deployed/p.name)
    api=[Path('P:/scripts/3_game/human.c'),Path('P:/scripts/3_game/entities/entityai.c'),Path('P:/scripts/3_game/entities/dayzinfectedinputcontroller.c'),Path('P:/scripts/3_game/entities/dayzcreatureaiinputcontroller.c'),Path('P:/scripts/1_core/proto/enconvert.c')]
    ref=dict(status='FROZEN_DEPLOYED_ENGINE_PENDING',parent_reference_sha256=sha(parent),terrain=str(terrain),terrain_sha256=sha(terrain),
        world_pbo_sha256='d1008dd6c882193706f06c5e7b8495ee1a357f5819a8574118784f7e90f18577',
        water_pbo_sha256='f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3',
        navmesh_sha256='e8348efc2f361d8aa82cbd69c4fc8ad72470a628abd2a10ca8411d7f40fc313c',
        probe_pbo_sha256=sha(pbo),deployed_mod=str(mod),deployed_mission=str(deployed),
        mission={str(p):sha(p) for p in mission.iterdir()},probe_files={str(p):sha(p) for p in stage.rglob('*') if p.is_file()},
        api_sha256={str(p):sha(p) for p in api},cases=cases,bridge=bridge,
        criteria=dict(settlement_s=20,settlement_drift_m=2,acquisition_timeout_s=30,session_timeout_s=1200,
            maximum_gap_s=1,actor_goal_radius_m=4.002,prey_goal_radius_m=2.002,maximum_lateral_m=4,
            physical_y_min_m=-.2,physical_y_max_m=.5,maximum_ground_error_m=.002,spawn_xz_error_m=.02,
            maximum_actor_step_speed_mps=12,maximum_prey_step_speed_mps=4,path_length_factor=3),
        input_contract='Client and server HumanInputController speed1/relative angle; synchronized phase; no infected movement overrides or per-frame pose writes.',
        limits=['Separate moving-target consumer; old stationary/noise failures remain preserved.','New infected per direction, each starts on dry ground before bridge.','No native perception root-cause claim.','No multiplayer capacity or populated-map acceptance.'])
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    (out/'verification.json').write_text(json.dumps(dict(status='PASS_SCRIPT_PBO_BYTE_PARITY',entries={k:hashlib.sha256(v).hexdigest() for k,v in entries.items()},probe_pbo_sha256=sha(pbo),engine='NOT_RUN'),indent=2)+'\n')
    print(json.dumps(dict(reference_sha256=sha(ev/'reference.json'),probe_pbo_sha256=sha(pbo),cases=len(cases),runtime='NOT_RUN')))


if __name__=='__main__':main()
