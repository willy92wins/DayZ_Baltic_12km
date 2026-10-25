"""Combine the frozen pier-avoiding Narva lane with the unchanged regional sectors."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ev=ROOT/'evidence/overnight-2026-10-01/regional-boat-v3'
    mission=ROOT/'missions/BalticRegionalBoatV3.BalticTrial'
    if ev.exists() or mission.exists():raise ValueError('Fresh outputs required')
    parent=ROOT/'evidence/overnight-2026-10-01/regional-boat-v2/reference.json'
    narva=ROOT/'evidence/overnight-2026-10-01/narva-boat-v3/reference.json'
    assert sha(parent)=='ec24583ac6f362de2b4b1b06a86f9eea809001ad2700f9892c128d717880e64e'
    assert sha(narva)=='2ccf0e902497f00a0a6f7cd85cd30b2d826f1c60ac69690473e57ea5e03bdd48'
    a,b=json.loads(parent.read_text()),json.loads(narva.read_text());ref=copy.deepcopy(a)
    assert a['criteria']==b['criteria'] and a['terrain_sha256']==b['terrain_sha256']
    ref['cases'][:2]=copy.deepcopy(b['cases']);assert [c['case'] for c in ref['cases']]==list(range(8))
    src=ROOT/'missions/BalticRegionalBoatV2.BalticTrial/init.c'
    assert sha(src)==a['mission'][str(src)]
    text=src.read_text();assert text.count('baltic_regional_boat_v2.log')==1
    text=text.replace('baltic_regional_boat_v2.log','baltic_regional_boat_v3.log')
    mission.mkdir(parents=True);ev.mkdir(parents=True);(mission/'init.c').write_text(text)
    rows=[]
    for case in ref['cases']:
        for i,(xz,y) in enumerate(zip(case['waypoints_xz'],case['water_levels'])):
            rows.append(f"{case['case']};{i};{xz[0]:.9g};{y:.9g};{xz[1]:.9g}")
    (mission/'routes.csv').write_text('\n'.join(rows)+'\n',encoding='ascii')
    ref.update(status='FROZEN_BEFORE_ENGINE',generation='V3_COMBINED_PRECISE_LOG_SCHEMA_V2',parents={str(p):sha(p) for p in (parent,narva)},
               mission={str(p):sha(p) for p in mission.iterdir()},world_deployment_binding='Native persisted V10; bind exact final PBO/NM in run receipt')
    ref['limits']=['Empty boat, independent spawns for reverse; no crew or full turn.',
                   'Four selected sectors only, not whole-river or medium-vessel acceptance.',
                   'Narva lane avoids projected piers; preserve failed previous routes.',
                   'Same criteria/controller as V2; six-decimal vector log schema2.']
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    print(json.dumps(dict(status='PREPARED_NOT_RUN',reference_sha256=sha(ev/'reference.json'),cases=len(ref['cases']),mission=str(mission)),indent=2))

if __name__=='__main__':main()
