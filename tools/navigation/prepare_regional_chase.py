"""Freeze physical AI targets from prior regional queries and the V10 crossing."""
from pathlib import Path
import hashlib,json
import numpy as np
import rasterio
from waterway_common import sample

ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ev=ROOT/'evidence/overnight-2026-10-01/regional-chase-v1'
    mission=ROOT/'missions/BalticRegionalChaseV1.BalticTrial'
    assert not ev.exists() and not mission.exists()
    asc=ROOT/'tests/regional_foundation_combined_v10/baltic_regional_foundation_v10.asc'
    assert sha(asc)=='8e25fab25e8f0909fdda302ed4ba3db4c43884c523920f5ef3424db90780eb8b'
    bridge=ROOT/'tests/narva_bridge_v10/reference.json'
    assert sha(bridge)=='3845bcf4b2aef06ad222105fdccebf07184e8f28b8183d8631f0284006a53a86'
    native=ROOT/'tb/regional_foundation_v10/01_native_v10.wrp'
    assert sha(native)=='631736b53c0f2c0902e702431dc37d72ed51e62cdbba2dfc480bb08584ac912b'
    center=np.array([2417.1428225906,6889.8850822322])
    axis=np.array([.98836436083,-.15210486594])
    with rasterio.open(asc) as ds:h=ds.read(1)
    def surface(xz,bridge_route=False):
        y=float(sample(h,np.array([xz[0]+200000]),np.array([xz[1]]))[0])
        if bridge_route and abs(np.dot(np.array(xz)-center,axis))<=112.5: y=11.
        return [float(xz[0]),y+.05,float(xz[1])]
    cases=[dict(case=0,name='local_control',reverse=False,kind='ground',start=surface([5104,7644]),goal=surface([5129,7644]))]
    source=ROOT/'missions/BalticFoundationConsumerV5.BalticTrial/nav-points.csv'
    wanted={'summit_0_0','summit_1_0','summit_2_0','reserve_1','spb_1','regional_1'}
    for row in source.read_text().splitlines():
        fields=row.split(';')
        if fields[0]!='Q' or fields[1] not in wanted:continue
        a,b=[np.array(list(map(float,v.split())))[[0,2]] for v in fields[2:4]]
        for reverse in (False,True):
            start,goal=(b,a) if reverse else (a,b)
            cases.append(dict(case=len(cases),name=fields[1],reverse=reverse,kind='ground',start=surface(start),goal=surface(goal)))
    for name,lo,hi in [('bridge_west',-135,-50),('bridge_middle',-55,55),('bridge_east',50,135)]:
        a,b=center+axis*lo,center+axis*hi
        for reverse in (False,True):
            start,goal=(b,a) if reverse else (a,b)
            cases.append(dict(case=len(cases),name=name,reverse=reverse,kind='bridge',start=surface(start,True),goal=surface(goal,True)))
    assert len(cases)==19
    # All serialized Enforce vectors are float32, frozen before the engine run.
    for c in cases:
        c['start']=np.array(c['start'],dtype='float32').astype(float).tolist()
        c['goal']=np.array(c['goal'],dtype='float32').astype(float).tolist()
    mission.mkdir(parents=True);ev.mkdir(parents=True)
    fixture=ROOT/'tools/navigation/regional_chase_init.c'
    (mission/'init.c').write_bytes(fixture.read_bytes())
    rows=[str(c['case'])+';'+' '.join(f'{v:.9g}' for v in c['start'])+';'+' '.join(f'{v:.9g}' for v in c['goal']) for c in cases]
    (mission/'cases.csv').write_text('\n'.join(rows)+'\n',encoding='ascii')
    ref=dict(status='FROZEN_BEFORE_ENGINE',terrain=str(asc),terrain_sha256=sha(asc),
             inputs={str(p):sha(p) for p in (source,bridge,native,fixture)},
             mission={str(p):sha(p) for p in mission.iterdir()},cases=cases,
             bridge=dict(center_xz=center.tolist(),axis_xz=axis.tolist(),half_length_m=112.5,deck_y=11.,max_lateral_m=4.),
             criteria=dict(target_settlement_s=20,minimum_final_settle_samples=20,maximum_prey_drift_m=2,
                           maximum_sample_gap_s=1,stage_timeout_s=90,goal_radius_m=4.002,path_length_factor=3,
                           physical_y_min_m=-.2,physical_y_max_m=.5,maximum_ground_error_m=.002,
                           maximum_spawn_error_m=.02,minimum_active_samples=3,stimulus_multiplier=4),
             limits=['One infected at a time and one client; not server capacity.',
                     'Noise4x is diagnostic; not normal long-range perception.',
                     'Nineteen selected directional cases, not whole-region connectivity.',
                     'Client override affects only human test target. No infected motion override.',
                     'World remains diagnostic until real native reopen gate passes.'])
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    print(json.dumps(dict(status=ref['status'],cases=len(cases),reference_sha256=sha(ev/'reference.json'),mission=str(mission)),indent=2))

if __name__=='__main__':main()
