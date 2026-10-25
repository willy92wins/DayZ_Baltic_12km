"""Install a fresh full-forest review mod and prepare server/personal requests.

No process is launched. Previous mods, mission storage and production are left
alone; the personal mission copies only the 16 explicitly hashed input files.
"""
import argparse,hashlib,json,shutil
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('build');a=ap.parse_args();B=Path(a.build)
    package=B/'package-visual-forest-20261024-c';pilot=B/'visual-pilot-collision-20261024-q/collision-package'
    wr=json.loads((package/'verification.json').read_text());pr=json.loads((pilot/'verification.json').read_text())
    assert wr['status']=='OFFLINE_PACKAGE_PASS' and wr['forest'] and pr['status']=='BINARY_COLLISION_DELTA_PASS'
    out=B/'personal-view-visual-20261024-q';mod=Path('P:/Mods/@DayZ_Baltic_EV112_VisualReviewQ')
    mission=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticBasicEV112VisualQ.BalticTrial')
    assert not out.exists() and not mod.exists() and not mission.exists(),'fresh paths required'
    sources={package/'Addons/narva_trial.pbo':wr['pbo_sha256'],pilot/'Addons/baltic_stream_pilot.pbo':pr['pbo_sha256'],
             Path('P:/Mods/@DayZ_Baltic_EV112_RuntimeMarginsV2/Addons/baltic_water_v30.pbo'):'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'}
    previous=json.loads((B/'personal-view-runtime-b/route.json').read_text());old=Path(previous['mission'])
    assert len(previous['live_files'])==16
    for p,h in sources.items():assert sha(p)==h
    for name,h in previous['live_files'].items():assert sha(old/name)==h
    probe=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticVisualProbeV1.BalticTrial')
    assert sha(probe/'init.c')=='0316951010ac00ab1309f72d8b48c3bbb8a5412a741f3d2bf82c652fd8f47011'
    assert sha(probe/'points.csv')=='c2fdc7f806d65ce1680ece5e63f38d5de33f4541f14318283d0941cc1981a4e6'
    out.mkdir();(mod/'Addons').mkdir(parents=True);mission.mkdir();checks=[]
    for src,digest in sources.items():
        dest=mod/'Addons'/src.name;shutil.copy2(src,dest);assert sha(dest)==digest;checks.append(dict(path=str(dest),sha256=digest))
    for name,digest in previous['live_files'].items():
        dest=mission/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/name,dest);assert sha(dest)==digest
    common=dict(project='DayZ_MCP',extra_mods=[mod.name],base_mods=[],no_base_mods=True,no_file_patching=True,build=False,takeover=False,wait_for_box_s=0)
    personal=dict(common,mode='all',mission=str(mission));server=dict(common,mode='server',mission=str(probe))
    (out/'launch-personal.json').write_text(json.dumps(personal,indent=2));(out/'launch-server.json').write_text(json.dumps(server,indent=2))
    route=[{k:v for k,v in p.items() if k!='offline_ground_y'} for p in previous['route']]
    route[0]['purpose']='Mar al pie de la presa y apoyos laterales; revisar también el pico protegido, aún pendiente.'
    route[1]['purpose']='Piloto continuo, ambos extremos, orillas y caminar sobre las dos juntas corregidas.'
    points=json.loads((B/'probe-visual-20261024-d/points.json').read_text())['points']
    dry=[p for p in points if p.get('site')=='65.0-0' and p['kind']=='dry_bank'];p=dry[len(dry)//2]
    route.insert(2,dict(id='continuous-65.0-0',x=p['x'],z=p['z'],purpose='Segundo piloto continuo, orientación NE/SW y ambos extremos.'))
    route.append(dict(id='road-49-pending',x=5295.7,z=5999.9,purpose='11 fallos transversales heredados; reparaciones rechazadas por nuevos pliegues, no integradas.'))
    for p in route:p['runtime_placement']='Recheck place_safely/surface in engine; coordinates are review targets, not guaranteed safe placements.'
    receipt=dict(status='DEPLOYED_FOR_SERVER_AND_LATER_PERSONAL_REVIEW',mod=str(mod),checks=checks,mission=str(mission),mission_files=previous['live_files'],
                 probe_mission=str(probe),probe_files={name:sha(probe/name) for name in ('init.c','points.csv')},route=route,
                 terrain_sha256='bc41bd8314affc5787e827b75fd7d03b7de454c0ffaae3a7476ccc7b609fd508',
                 forest_instances=wr['forest_instances'],human_focus_required=True,personal_launched=False,production_replaced=False)
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({k:v for k,v in receipt.items() if k not in ('route','mission_files')},indent=2))

if __name__=='__main__':main()
