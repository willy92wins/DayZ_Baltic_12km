"""Read-only identity gate for the frozen regional visual/pursuit fixtures."""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve prelaunch evidence')
    ref=json.loads(a.reference.read_text(encoding='utf-8'))
    world=Path('P:/Mods/@DayZ_Baltic_FoundationV10Native/Addons')
    expected={world/'narva_trial.pbo':ref['world_pbo_sha256'],
        world/'baltic_water.pbo':ref.get('water_pbo_sha256','f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3')}
    mod=Path(ref['deployed_mod']);mission=Path(ref['deployed_mission'])
    assert mission.parent==Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')
    assert mission.name.startswith(('BalticFoundationVisualGroup','BalticFoundationVisualNative','BalticContinuousPursuit'))
    assert mod.parent==Path('P:/Mods')
    assert mod.name.startswith(('@BalticFoundationVisualGroup','@BalticFoundationVisualNative','@BalticContinuousPursuit'))
    pbo=list((mod/'Addons').glob('*.pbo'));assert len(pbo)==1
    expected[pbo[0]]=ref['probe_pbo_sha256']
    if 'mission_sha256' in ref:
        expected[mission/'init.c']=ref['mission_sha256']
    else:
        for original,digest in ref['mission'].items():
            path=Path(original);expected[path]=digest;expected[mission/path.name]=digest
    actual={str(p):sha(p) for p in expected}
    failures=[str(p) for p,digest in expected.items() if actual[str(p)]!=digest]
    if failures:raise ValueError('Frozen fixture changed: '+str(failures))
    _,properties,entries=read_pbo(pbo[0])
    assert entries['config.bin'].startswith(b'\0raP') and not any(k.endswith('config.cpp') for k in entries)
    if 'script_sha256' in ref:
        scripts=[v for k,v in entries.items() if k.endswith('.c')]
        assert len(scripts)==1 and hashlib.sha256(scripts[0]).hexdigest()==ref['script_sha256']
    result=dict(status='PASS_FROZEN_FIXTURE_IDENTITY_NOT_RUNTIME',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        reference_sha256=sha(a.reference),files_sha256=actual,probe_prefix=properties['prefix'],
        launch=dict(project='DayZ_MCP',mode='all',mission=str(mission),
            extra_mods=[str(world.parent),str(mod)],no_base_mods=True,no_file_patching=True,
            auto_remediate_steam=True,player_name='Dev',width=1280,height=720))
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
