"""Deploy isolated R (Q plus H road layer); prepare, never launch, both visits."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools/water'),str(ROOT/'tools/terrain')]
from streambed_kit_v31 import tri_h
import repair_roads_v30 as R


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build',type=Path);a=ap.parse_args();B=a.build
    package=B/'package-visual-road-20261024-h';report=json.loads((package/'verification.json').read_text())
    assert report['status']=='OFFLINE_PACKAGE_PASS' and report['forest_instances']==2560922
    old=json.loads((B/'personal-view-visual-20261024-q/receipt.json').read_text())
    mod=Path('P:/Mods/@DayZ_Baltic_EV112_VisualReviewR');out=B/'personal-view-visual-20261024-r'
    base=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')
    personal=base/'BalticBasicEV112VisualR.BalticTrial';probe=base/'BalticVisualRoadR.BalticTrial'
    assert all(not p.exists() for p in (mod,out,personal,probe))
    sources={Path(c['path']):c['sha256'] for c in old['checks'] if Path(c['path']).name!='narva_trial.pbo'}
    sources[package/'Addons/narva_trial.pbo']=report['pbo_sha256']
    for p,h in sources.items():assert sha(p)==h
    mission=Path(old['mission'])
    for name,h in old['mission_files'].items():assert sha(mission/name)==h
    original_probe=Path(old['probe_mission']);assert sha(original_probe/'init.c')==old['probe_files']['init.c']
    points=json.loads((B/'probe-visual-20261024-d/points.json').read_text())
    assert len(points['points'])==786
    H=np.load(B/'road-merged-20261024-h/terrain-buried.npz')['heights']
    for p in points['points']:
        assert abs(float(tri_h(H,np.array([p['x']]),np.array([p['z']]))[0])-p['ground'])<1e-6,'prior probe ground changed'
    seen={}
    def add(x,z,kind,expect):
        x,z=round(float(x),6),round(float(z),6)
        if (x,z) in seen:return seen[(x,z)]
        h=float(tri_h(H,np.array([x]),np.array([z]))[0])
        p=dict(id=len(points['points']),kind=kind,site='road-49',x=x,z=z,ground=h,expect=expect)
        if expect=='dry':p.update(bed=h,collision_pilot=False,water_ext=None)
        points['points'].append(p)
        seen[(x,z)]=p['id']
        return p['id']
    for p in json.loads((B/'road-repair-20261024-h/review.json').read_text())['changes']:
        add(p['col']*6,12282-p['row']*6,'road_changed_vertex','ground')
    s,q,n,_=R.stations(R.road_chains()[49])
    prior=json.loads((B/'roads-visual-review-20261024-c/current.json').read_text())
    # All 17 native interpolation samples at each formerly failing cross-section.
    fails=[p for p in prior['fail_list'] if p['chain']==49 and p['check']=='cross']
    assert len(fails)==11
    sections=[]
    for f in fails:
        j=int(np.argmin(abs(s-f['station_m'])))
        section=dict(station_m=float(s[j]),ids=[])
        for offset in R.OFFSETS:
            x,z=q[j]+offset*n[j];section['ids'].append(add(x,z,'road_previous_cross_failure','dry'))
        sections.append(section)
    points['road_sections']=sections
    points['counts']=dict(Counter(p['kind'] for p in points['points']))
    points['scope']='Q server controls plus every changed native vertex and all 17 samples at the 11 former road failures; no driving or visual acceptance.'
    (mod/'Addons').mkdir(parents=True);out.mkdir();personal.mkdir();probe.mkdir();checks=[]
    for p,h in sources.items():
        dest=mod/'Addons'/p.name;shutil.copy2(p,dest);assert sha(dest)==h;checks.append(dict(path=str(dest),sha256=h))
    for name,h in old['mission_files'].items():
        dest=personal/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(mission/name,dest);assert sha(dest)==h
    shutil.copy2(original_probe/'init.c',probe/'init.c')
    (probe/'points.csv').write_text(''.join(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n" for p in points['points']),encoding='ascii')
    points['inputs']={str(p):sha(p) for p in (B/'road-merged-20261024-h/terrain-buried.npz',probe/'init.c',probe/'points.csv')}
    points['deployed_pbos']=checks
    (out/'points.json').write_text(json.dumps(points,indent=2))
    common=dict(project='DayZ_MCP',extra_mods=[mod.name],base_mods=[],no_base_mods=True,no_file_patching=True,build=False,takeover=False,wait_for_box_s=0)
    (out/'launch-personal.json').write_text(json.dumps(dict(common,mode='all',mission=str(personal)),indent=2))
    (out/'launch-server.json').write_text(json.dumps(dict(common,mode='server',mission=str(probe)),indent=2))
    route=old['route']
    for p in route:
        if p['id']=='road-49-pending':p['purpose']='Capa H: calzada y transiciones pasan offline; comprobar en juego y conducir. No validado en motor.'
    receipt=dict(status='DEPLOYED_ISOLATED_PENDING_RUNTIME',checks=checks,source_package_sha256=sha(package/'verification.json'),
                 terrain_sha256=sha(B/'road-merged-20261024-h/terrain-buried.npz'),mission=str(personal),probe_mission=str(probe),
                 mission_files=old['mission_files'],probe_files={n:sha(probe/n) for n in ('init.c','points.csv')},
                 points=len(points['points']),route=route,launched=False,production_replaced=False,Q_preserved=True,
                 navigation='UNCHANGED_PENDING_REGENERATION_NOT_ACCEPTED',server_probe='NOT_RUN')
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({k:v for k,v in receipt.items() if k not in ('route','mission_files')},indent=2))


if __name__=='__main__':main()
