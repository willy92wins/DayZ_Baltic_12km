"""Freeze terminal deceleration on the two unchanged hilly sedan routes."""
from pathlib import Path
import copy,hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    previous=ROOT/'evidence/foundation-followup-2026-10-01/regional-drive-v1/reference.json'
    assert sha(previous)=='da2ee73678e31ec46c87faaf4e52e5320c4f0f65265e4ff5b9a15db7ccefccad'
    ref=json.loads(previous.read_text(encoding='utf-8'));source=ROOT/'missions/BalticRegionalDriveV1.BalticTrial/init.c'
    assert sha(source)=='d099f1a1ed3042051813ecfe1fc35f9a9e14808cece95df972d54a7cf5192e4f'
    ev=ROOT/'evidence/foundation-followup-2026-10-01/regional-drive-v2';mission=ROOT/'missions/BalticRegionalDriveV2.BalticTrial'
    deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    assert not any(p.exists() for p in [ev,mission,deployed])
    cases=copy.deepcopy(ref['cases'][2:4])
    for i,c in enumerate(cases):c['original_case']=c['case'];c['case']=i
    code=source.read_text(encoding='utf-8').replace('baltic_regional_drive_v1','baltic_regional_drive_v2').replace('m_Case>=6','m_Case>=2')
    before='remaining.Length()<=5 && m_Nearest>=last - 6';assert code.count(before)==1
    code=code.replace(before,'remaining.Length()<=1.5 && speed<=0.8 && m_Nearest>=last - 6')
    before='                if (m_Case<2) desiredSpeed=6.944444;';assert code.count(before)==1
    code=code.replace(before,'                if (remaining.Length()<50) desiredSpeed=4;\n                if (remaining.Length()<20) desiredSpeed=2;\n                if (remaining.Length()<8) desiredSpeed=0.6;')
    before='                brake=Math.Clamp((speed - desiredSpeed - 0.455556)*0.2,0,0.5);';assert code.count(before)==1
    code=code.replace(before,before+'\n                if (remaining.Length()<50) brake=Math.Clamp((speed - desiredSpeed)*0.8,0,1);')
    before='        m_Car.BalticDriveInput(throttle,steering,brake,gear);';assert code.count(before)==1
    code=code.replace(before,'        if (m_Arrived<0) m_Car.BalticDriveInput(throttle,steering,brake,gear);\n        else m_Car.BalticDriveStop();')
    ev.mkdir();mission.mkdir();(mission/'init.c').write_text(code,encoding='utf-8')
    (mission/'routes.csv').write_text(''.join(f"{c['case']};{i};{p[0]:.9g};{p[1]:.9g};{p[2]:.9g}\n" for c in cases for i,p in enumerate(c['route_xyz'])),encoding='ascii')
    lint=subprocess.run([sys.executable,'-X','utf8','C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(mission)],capture_output=True,text=True)
    (ev/'lint.json').write_text(lint.stdout,encoding='utf-8');result=json.loads(lint.stdout);assert lint.returncode==0 and result['status']=='PASS' and result['info']['files_scanned']==1
    shutil.copytree(mission,deployed)
    ref.update(status='FROZEN_TERMINAL_REVISION_NOT_RUN',cases=cases,mission={str(p.resolve()):sha(p) for p in mission.iterdir()},deployed_mission=str(deployed),
               log_name='baltic_regional_drive_v2.log',parent_reference_sha256=sha(previous),scope='Two hilly routes from V1, same terrain and gates; earlier terminal braking and stopped observation.',
               revision='50/20/8m target4/2/0.6mps; arrival within1.5m at<=0.8mps, native stop then5.5s observation.',
               limits=['No terrain or input-PBO changes; no post-spawn pose or velocity forcing.',
                       'Two hilly journeys only, empty sedan. No whole-network, physical road pieces or multiplayer claim.',
                       'V1 aggregate FAIL and full-width geometry failure remain preserved.'])
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(status='PREPARED_NOT_RUN',reference_sha256=sha(ev/'reference.json'),mission_sha256=sha(mission/'init.c'))))

if __name__=='__main__':main()
