"""Freeze one bounded terminal-throttle experiment; retain terrain and physical gates."""
from pathlib import Path
import copy, hashlib, json, shutil, subprocess, sys
from verify_foundation_drive import verify_mission_identity
ROOT = Path(__file__).resolve().parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    previous = ROOT/'evidence/foundation-followup-2026-10-01/regional-drive-v3/reference.json'
    assert sha(previous) == 'b55bd8942529e0dbd2b4b329c68c931b30453909492c861e5b86f6eaec354604'
    before = json.loads(previous.read_text()); verify_mission_identity(before)
    result = json.loads((previous.parent/'runtime-complete/verification.json').read_text())
    assert all(c['status']=='PASS' for c in result['cases'][:5])
    assert {k for k,v in result['cases'][5]['checks'].items() if not v} == {'terminal','one_arrival'}
    source = ROOT/'missions/BalticRegionalDriveV3.BalticTrial/init.c'
    assert sha(source) == '904eb01741a47067d2e702e8d8d744945af140f290d9e2f8aba5dccfdc1c6d95'
    ref = copy.deepcopy(before); cases = ref['cases'][4:6]
    for i,c in enumerate(cases):
        c['original_case']=c['case']; c['case']=i
        assert c['route_xyz'] == before['cases'][i+4]['route_xyz']
    code = source.read_text()
    assert code.count('m_Case>=6') == 1
    code = code.replace('baltic_regional_drive_v3','baltic_regional_drive_v4').replace('m_Case>=6','m_Case>=2')
    coast = '                if (m_Case<2) desiredSpeed=6.944444;\n'
    assert code.count(coast)==1; code=code.replace(coast,'')
    anchor='                throttle=Math.Clamp(0.1+(desiredSpeed - speed)*0.25,0,0.5);'
    assert code.count(anchor)==1
    code=code.replace(anchor,anchor+'\n                if (remaining.Length()<8 && speed<0.2) throttle=0.5;')
    mission=ROOT/'missions/BalticRegionalDriveV4.BalticTrial'
    deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    out=previous.parent.with_name('regional-drive-v4')
    assert not any(p.exists() for p in [mission,deployed,out])
    mission.mkdir();out.mkdir();(mission/'init.c').write_text(code,encoding='utf-8')
    (mission/'routes.csv').write_text(''.join(f"{c['case']};{i};{p[0]:.9g};{p[1]:.9g};{p[2]:.9g}\n" for c in cases for i,p in enumerate(c['route_xyz'])),encoding='ascii')
    lint=subprocess.run([sys.executable,'-X','utf8','C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(mission)],capture_output=True,text=True)
    (out/'lint.json').write_text(lint.stdout,encoding='utf-8');check=json.loads(lint.stdout)
    assert lint.returncode==0 and check['status']=='PASS' and check['info']['files_scanned']==1
    shutil.copytree(mission,deployed)
    ref.update(status='FROZEN_ROAD_V29_TERMINAL_RECOVERY_NOT_RUN',cases=cases,
               mission={str(p.resolve()):sha(p) for p in mission.iterdir()},
               deployed_mission=str(deployed),log_name='baltic_regional_drive_v4.log',
               parent_reference_sha256=sha(previous),scope='Two unchanged southern journeys, V29, 35kmh target.',
               route_geometry=[dict(c,case=i) for i,c in enumerate(before['route_geometry'][4:6])],
               revision='Only below0.2mps within8m of goal, request existing maximum throttle0.5; unchanged braking, arrival and acceptance.',
               limits=['V3 terminal FAIL retained; two empty-sedan journeys only.',
                       'No map/probe-PBO edits or post-spawn pose/velocity forcing.'])
    assert ref['criteria']==before['criteria'] and ref['terrain_sha256']==before['terrain_sha256']
    world=Path('P:/Mods/@DayZ_Baltic_RoadV29/Addons/narva_trial.pbo')
    expected={**ref['inputs'],**ref['mission'],ref['terrain']:ref['terrain_sha256']}
    expected.update({str(deployed/Path(p).name):digest for p,digest in ref['mission'].items()})
    expected.update({str(world):'b3418f927f6cc4adf8ba03b86de0ce1491f32adf87f3a124120c62eff20f856e',
                     str(world.with_name('baltic_water.pbo')):'f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3',
                     'P:/Mods/@BalticDriveInputProbe/Addons/baltic_drive_input.pbo':ref['input_pbo_sha256']})
    actual={p:sha(Path(p)) for p in expected};assert actual==expected
    (out/'reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
    (out/'preflight.json').write_text(json.dumps(dict(status='PASS_FROZEN_IDENTITY_NOT_RUNTIME',files=actual,reference_sha256=sha(out/'reference.json')),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=ref['status'],reference_sha256=sha(out/'reference.json'),mission_sha256=sha(mission/'init.c'))))


if __name__ == '__main__':main()
