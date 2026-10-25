"""Freeze one perception discriminator for eligible failures of the completed V1."""
from pathlib import Path
import copy, hashlib, json, shutil

ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parent=ROOT/'evidence/overnight-2026-10-01/regional-chase-v1/reference.json'
    result=ROOT/'evidence/overnight-2026-10-01/regional-chase-v1/runtime-complete/verification.json'
    ref=json.loads(parent.read_text());report=json.loads(result.read_text())
    if not all(report['global_checks'].values()):raise ValueError('Completed parseable V1 required')
    if report['cases'][0]['status']!='PASS':raise ValueError('Passing local control required')
    allowed={'reached_terminal','reacted','actual_goal_distance','within_timeout'}
    selected=[0]
    for case in report['cases'][1:]:
        failed={k for k,v in case.get('checks',{}).items() if not v}
        eligible=allowed
        terminals=[['TIMEOUT']]
        if ref['cases'][case['case']]['kind']=='bridge':
            eligible=allowed|{'bridge_corridor','physical_surface','bounded_path'}
            terminals.append(['REACHED'])
        if case['status']=='FAIL' and failed and failed<=eligible and case['terminal'] in terminals:
            selected.append(case['case'])
    if len(selected)==1:raise ValueError('No eligible perception failures')
    ev=ROOT/'evidence/overnight-2026-10-01/regional-chase-v2'
    mission=ROOT/'missions/BalticRegionalChaseV2.BalticTrial'
    deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    for p in (ev,mission,deployed):
        if p.exists():raise ValueError('Fresh output required: '+str(p))
    original=ROOT/'missions/BalticRegionalChaseV1.BalticTrial/init.c'
    if sha(original) not in ref['mission'].values():raise ValueError('Parent mission identity mismatch')
    code=original.read_text()
    before='GetGame().GetNoiseSystem().AddNoisePos(m_Prey,m_Prey.GetPosition(),m_Noise,4);'
    assert code.count(before)==1
    code=code.replace(before,'GetGame().GetNoiseSystem().AddNoiseTarget(m_Prey.GetPosition(),5,m_Noise,4);')
    code=code.replace('regional_chase_v1','regional_chase_v2').replace('REGIONAL_CHASE_V1','REGIONAL_CHASE_V2')
    assert code.count('m_Starts.Count()!=19')==1
    code=code.replace('m_Starts.Count()!=19',f'm_Starts.Count()!={len(selected)}')
    cases=[]
    for idx,source in enumerate(selected):
        c=copy.deepcopy(ref['cases'][source]);c.update(case=idx,source_case=source);cases.append(c)
    ev.mkdir(parents=True);mission.mkdir(parents=True)
    (mission/'init.c').write_text(code)
    lines=[str(c['case'])+';'+' '.join(f'{v:.9g}' for v in c['start'])+';'+' '.join(f'{v:.9g}' for v in c['goal']) for c in cases]
    (mission/'cases.csv').write_text('\n'.join(lines)+'\n',encoding='ascii')
    shutil.copytree(mission,deployed)
    for p in mission.iterdir():assert sha(p)==sha(deployed/p.name)
    ref.update(status='FROZEN_PERCEPTION_DISCRIMINATOR_RUNTIME_PENDING',cases=cases,
        parent_reference_sha256=sha(parent),parent_result_sha256=sha(result),log_header='BALTIC_REGIONAL_CHASE_V2',
        mission={str(p):sha(p) for p in mission.iterdir()},deployed_mission=str(deployed),
        stimulus=dict(api='AddNoiseTarget',lifetime_s=5,multiplier=4,interval_s=3),
        changes=['Same frozen points, movement/contact/arrival criteria and90s timeout.','Only sound target lifetime/binding differs; selected failing cases renumbered with source_case preserved.'],
        limits=['Locomotion under persistent diagnostic noise; not ordinary perception range.','Original V1 failures remain failed.','One infected and one human; no capacity claim.','No world/NM/terrain/object change; final native world remains d1008dd6.'])
    out=ev/'reference.json';out.write_text(json.dumps(ref,indent=2)+'\n')
    print(json.dumps(dict(reference_sha256=sha(out),source_cases=selected,mission=str(deployed))))

if __name__=='__main__':main()
