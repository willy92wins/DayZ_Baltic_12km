"""Freeze route/criteria and build the isolated vanilla driving input fixture."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
import numpy as np
import rasterio
from shapely.geometry import LineString
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ev=ROOT/'evidence/overnight-2026-10-01/foundation-drive-v1'
    mission=ROOT/'missions/BalticFoundationDriveV1.BalticTrial'
    out=ROOT/'packages/foundation-drive-v1'
    for p in (ev,mission,out):
        if p.exists():raise ValueError('Fresh output required: '+str(p))
    asc=ROOT/'tests/regional_foundation_combined_v10/baltic_regional_foundation_v10.asc'
    assert sha(asc)=='8e25fab25e8f0909fdda302ed4ba3db4c43884c523920f5ef3424db90780eb8b'
    source=ROOT/'tests/regional_foundation_combined_v10/solve.json'
    solve=json.loads(source.read_text());assert solve['spans']==9 and solve['deck_m']==11
    west,east=[v['coordinates'] for v in solve['routes']]
    line=LineString(west[::-1]+east)
    center=np.array([2417.1428225906,6889.8850822322]);axis=np.array([.98836436083,-.15210486594])
    with rasterio.open(asc) as ds:h=ds.read(1)
    cases=[]
    for name,lo,hi,reverse in [('calibration_west',20,100,False),('narva_full',10,line.length-10,False),('narva_full',10,line.length-10,True)]:
        stations=np.linspace(lo,hi,int(np.ceil((hi-lo)/2))+1)
        if reverse:stations=stations[::-1]
        xy=np.array([line.interpolate(s).coords[0] for s in stations]);y=sample(h,xy[:,0]+200000,xy[:,1])
        on=abs((xy-center)@axis)<=112.5;y[on]=11
        route=np.array(np.column_stack([xy[:,0],y,xy[:,1]]),dtype='float32').astype(float)
        cases.append(dict(case=len(cases),name=name,reverse=reverse,route_xyz=route.tolist(),length_m=hi-lo))
    mission.mkdir(parents=True);ev.mkdir(parents=True);out.mkdir(parents=True)
    (mission/'init.c').write_bytes((ROOT/'tools/navigation/foundation_drive_init.c').read_bytes())
    (mission/'routes.csv').write_text(''.join(f"{c['case']};{i};{p[0]:.9g};{p[1]:.9g};{p[2]:.9g}\n" for c in cases for i,p in enumerate(c['route_xyz'])),encoding='ascii')
    prefix='baltic_drive_input';stage=out/prefix;stage.mkdir();(stage/'scripts/4_World').mkdir(parents=True)
    code=ROOT/'tools/navigation/BalticDriveInput.c'
    (stage/'scripts/4_World/BalticDriveInput.c').write_bytes(code.read_bytes())
    config='''class CfgPatches { class baltic_drive_input { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","DZ_Scripts"}; }; };
class CfgMods { class baltic_drive_input { type="mod"; dependencies[]={"World"}; class defs { class worldScriptModule { value=""; files[]={"baltic_drive_input/scripts/4_World"}; }; }; }; };
'''
    (out/'config.cpp').write_text(config)
    dest=out/'Addons';dest.mkdir()
    tools=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
    commands=[[tools/'CfgConvert/CfgConvert.exe','-bin','-dst',stage/'config.bin',out/'config.cpp'],
              [tools/'PboUtils/FileBank.exe','-property','prefix='+prefix,'-property','product=dayz ugc','-dst',dest,stage]]
    for i,argv in enumerate(commands):
        result=subprocess.run(list(map(str,argv)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/f'command-{i}.log').write_bytes(result.stdout)
        if result.returncode:raise RuntimeError('Build failed')
    pbo=dest/(prefix+'.pbo');data,props,entries=read_pbo(pbo)
    expected={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    assert entries==expected and len(entries)==2 and props['prefix']==prefix
    ref=dict(status='FROZEN_BEFORE_ENGINE',terrain=str(asc),terrain_sha256=sha(asc),
             inputs={str(p):sha(p) for p in (source,code)},mission={str(p):sha(p) for p in mission.iterdir()},
             input_pbo_sha256=sha(pbo),cases=cases,
             bridge=dict(center_xz=center.tolist(),axis_xz=axis.tolist(),half_length_m=112.5,deck_y=11.,max_lateral_m=4.),
             criteria=dict(maximum_dt_s=.5,maximum_step_m=3,maximum_health_loss=1,maximum_axis_distance_m=3,
                           maximum_endpoint_distance_m=5,maximum_contact_error_m=.12,maximum_ground_error_m=.002,
                           maximum_no_contact_s=.4,minimum_cruise_speed_m_s=4,minimum_cruise_duration_s=5,
                           maximum_stopped_speed_m_s=.2,minimum_stop_duration_s=5,minimum_up_dot=.8660254),
             limits=['Empty vanilla sedan only. Terrain grades before physical road pieces.',
                     'Not human handling, traffic, crew or multiplayer capacity. Engine compilation pending.'])
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    (out/'verification.json').write_text(json.dumps(dict(status='PASS_PACKED_CONTENT_ONLY',pbo_sha256=sha(pbo),entries=list(entries)),indent=2)+'\n')
    print(json.dumps(dict(status='PREPARED_NOT_RUN',reference_sha256=sha(ev/'reference.json'),pbo_sha256=sha(pbo),cases=[{k:v for k,v in c.items() if k!='route_xyz'} for c in cases]),indent=2))

if __name__=='__main__':main()
