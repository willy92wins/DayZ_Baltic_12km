"""Freeze short overlapping physical routes while preserving long-route failures."""
from pathlib import Path
import copy, hashlib, json, shutil
import numpy as np
import rasterio
from waterway_common import sample

ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parent=ROOT/'evidence/overnight-2026-10-01/regional-chase-v1/reference.json';ref=json.loads(parent.read_text())
    ev=ROOT/'evidence/overnight-2026-10-01/regional-chase-v3';mission=ROOT/'missions/BalticRegionalChaseV3.BalticTrial'
    deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    for p in (ev,mission,deployed):
        if p.exists():raise ValueError('Fresh output required: '+str(p))
    terrain=Path(ref['terrain']);assert sha(terrain)==ref['terrain_sha256']
    with rasterio.open(terrain) as ds:h=ds.read(1)
    bridge=ref['bridge'];center=np.array(bridge['center_xz']);axis=np.array(bridge['axis_xz'])
    def surface(xz,on_bridge=False):
        y=float(sample(h,np.array([xz[0]+200000]),np.array([xz[1]]))[0])
        if on_bridge and abs((xz-center)@axis)<=112.5:y=11
        return np.array([xz[0],y+.05,xz[1]],dtype='float32').astype(float).tolist()
    cases=[copy.deepcopy(ref['cases'][0])];cases[0]['source_case']=0
    coverage=[]
    for source in (8,10,12):
        original=ref['cases'][source];a=np.array(original['start'])[[0,2]];b=np.array(original['goal'])[[0,2]]
        length=float(np.linalg.norm(b-a));direction=(b-a)/length
        intervals=[(0,45),(40,85),(80,length)]
        assert 85<length<=125
        for part,(lo,hi) in enumerate(intervals):
            cases.append(dict(case=len(cases),source_case=source,name=original['name']+f'_short_{part}',reverse=True,kind='ground',
                start=surface(a+lo*direction),goal=surface(a+hi*direction),source_interval_m=[lo,hi]))
        coverage.append(dict(kind='ground',source_case=source,length_m=length,intervals_m=intervals,overlap_m=5))
    intervals=[]
    for lo in range(-135,111,35):
        hi=min(lo+40,135);intervals.append([lo,hi])
        for reverse in (False,True):
            start,goal=(hi,lo) if reverse else (lo,hi)
            cases.append(dict(case=len(cases),name=f'bridge_{lo}_{hi}',reverse=reverse,kind='bridge',source_interval_m=[lo,hi],
                start=surface(center+axis*start,True),goal=surface(center+axis*goal,True)))
    assert len(cases)==26 and intervals[0][0]==-135 and intervals[-1][1]==135
    coverage.append(dict(kind='bridge',domain_m=[-135,135],intervals_m=intervals,directions=2,overlap_m=5))
    original=ROOT/'missions/BalticRegionalChaseV1.BalticTrial/init.c';assert sha(original) in ref['mission'].values()
    code=original.read_text().replace('regional_chase_v1','regional_chase_v3').replace('REGIONAL_CHASE_V1','REGIONAL_CHASE_V3').replace('m_Starts.Count()!=19','m_Starts.Count()!=26')
    ev.mkdir(parents=True);mission.mkdir(parents=True);(mission/'init.c').write_text(code)
    rows=[str(c['case'])+';'+' '.join(f'{v:.9g}' for v in c['start'])+';'+' '.join(f'{v:.9g}' for v in c['goal']) for c in cases]
    (mission/'cases.csv').write_text('\n'.join(rows)+'\n',encoding='ascii');shutil.copytree(mission,deployed)
    for p in mission.iterdir():assert sha(p)==sha(deployed/p.name)
    ref.update(status='FROZEN_SHORT_OVERLAPPING_ROUTES_RUNTIME_PENDING',parent_reference_sha256=sha(parent),cases=cases,coverage=coverage,
        log_header='BALTIC_REGIONAL_CHASE_V3',mission={str(p):sha(p) for p in mission.iterdir()},deployed_mission=str(deployed),
        limits=['New actors on short overlapping routes, not one continuous long chase.','Original long-route failures remain failed; same physical/arrival criteria.','No motion overrides on infected.','One client; no capacity claim.','Final native V10 world unchanged.'])
    p=ev/'reference.json';p.write_text(json.dumps(ref,indent=2)+'\n');print(json.dumps(dict(reference_sha256=sha(p),cases=len(cases),mission=mission.name)))

if __name__=='__main__':main()
