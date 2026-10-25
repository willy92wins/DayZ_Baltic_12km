"""Freeze regional camera groups with a nearby player; preserve the final world."""
from pathlib import Path
import copy, hashlib, json, shutil, subprocess, sys
import numpy as np
import rasterio
from shapely.geometry import Point, shape
from shapely.ops import unary_union
from waterway_common import sample

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
GROUPS={
    'narva':([0,1,2],[2000,6955]),
    'spb':([3,4,6],[8790,10097]),
    'neva':([5],[10745,10020]),
    'reserve':([7,8],[8322,6234]),
    'north':([9],[5050,7470]),
    'south':([10],[5540,250]),
    'overview':([11],[6144,1200]),
}

def main():
    parent=ROOT/'evidence/overnight-2026-10-01/foundation-visual-v4/reference.json'
    ref=json.loads(parent.read_text())
    original=ROOT/'packages/foundation-visual-v4/baltic_foundation_visual_v4/scripts/5_Mission/BalticRenderProbe.c'
    assert sha(original)==ref['script_sha256']
    terrain=ROOT/'tests/regional_foundation_combined_v10/baltic_regional_foundation_v10.asc'
    assert sha(terrain)==ref['terrain_sha256']
    with rasterio.open(terrain) as ds:height=ds.read(1)
    hydro=[ROOT/'evidence/regional-foundation-v1'/n for n in ['water-surfaces-contour-v2.geojson','ocean-game.json']]
    wet=unary_union([shape(f['geometry']) for p in hydro for f in json.loads(p.read_text())['features']])
    all_refs=[]
    for name,(indices,xz) in GROUPS.items():
        n=len(indices);stem=f'visual_g_{name}_v1';prefix='baltic_foundation_'+stem
        ev=ROOT/f'evidence/overnight-2026-10-01/foundation-{stem}'
        out=ROOT/f'packages/foundation-{stem}'
        mission=ROOT/f'missions/BalticFoundationVisualGroup{name.title()}V1.BalticTrial'
        deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
        mod=Path('P:/Mods')/('@BalticFoundationVisualGroup'+name.title()+'V1')
        for path in [ev,out,mission,deployed,mod]:
            if path.exists():raise ValueError('Fresh output required: '+str(path))
        ground=float(sample(height,np.array([xz[0]+200000]),np.array([xz[1]]))[0])
        distance=float(wet.distance(Point(*xz)))
        assert not wet.covers(Point(*xz)) and distance>10 and ground>1.25
        code=original.read_text()
        begin=code.index('        if (m_BalticRenderPhase == -1 &&')
        end=code.index('\n        BalticVisualMetrics();',begin)
        phases=[];timeline=[]
        for phase,index in enumerate(indices):
            pose=copy.deepcopy(ref['poses'][index]);pose.update(phase=phase,original_phase=index,start_s=15+45*phase,settled_s=18+45*phase,end_s=60+45*phase)
            phases.append(pose)
            vector=lambda v:' '.join(format(x,'.10g') for x in v)
            near=0 if pose['nearplane_requested']=='original' else pose['nearplane_requested']
            timeline.extend([f'        if (m_BalticRenderPhase == {phase-1} && m_BalticRenderTime >= {pose["start_s"]})',
                f'            BalticRenderPose({phase}, "{vector(pose["position"])}", "{vector(pose["target"])}", {pose["view_requested"]}, {near});'])
        restore=15+45*n
        timeline.extend([f'        if (m_BalticRenderPhase == {n-1} && m_BalticRenderTime >= {restore})',
            '        {',f'            BalticRenderRestore(); m_BalticRenderPhase={n}; m_BalticRenderNextRecord=-1;', '        }',
            f'        if (m_BalticRenderPhase == {n} && m_BalticRenderTime >= {restore+3})', '        {',
            '            BalticRenderRecord("COMPLETE_RESTORED_SETTLED", false);',f'            m_BalticRenderPhase={n+1}; return;','        }'])
        code=code[:begin]+'\n'.join(timeline)+'\n'+code[end:]
        code=code.replace('m_BalticRenderPhase < 12',f'm_BalticRenderPhase < {n}').replace('m_BalticRenderPhase > 12',f'm_BalticRenderPhase > {n}').replace('m_BalticRenderPhase >= 12',f'm_BalticRenderPhase >= {n}').replace('m_BalticRenderPhase = 13',f'm_BalticRenderPhase = {n+1}')
        code=code.replace('visual_v4',stem).replace('VISUAL_V4',stem.upper()).replace('client_metrics_v4',f'client_metrics_g_{name}_v1').replace('METRICS_V4',f'METRICS_G_{name.upper()}_V1')
        stage=out/prefix;(stage/'scripts/5_Mission').mkdir(parents=True);ev.mkdir(parents=True)
        script=stage/'scripts/5_Mission/BalticRenderProbe.c';script.write_text(code)
        config=(ROOT/'packages/foundation-visual-v4/config.cpp').read_text().replace('baltic_foundation_visual_v4',prefix)
        (out/'config.cpp').write_text(config);addons=out/'Addons';addons.mkdir()
        mission.mkdir()
        init=(ROOT/'missions/BalticFoundationVisualV4.BalticTrial/init.c').read_text()
        assert init.count('pos = "2025 0 6950";')==1
        init=init.replace('pos = "2025 0 6950";',f'pos = "{xz[0]} 0 {xz[1]}";').replace('// Western terrain approach of the 225m V10 bridge.','// Frozen dry anchor near this camera group; avoids player occlusion.')
        (mission/'init.c').write_text(init)
        tool=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
        for i,args in enumerate([[tool/'CfgConvert/CfgConvert.exe','-bin','-dst',stage/'config.bin',out/'config.cpp'],[tool/'PboUtils/FileBank.exe','-property','prefix='+prefix,'-property','product=dayz ugc','-dst',addons,stage]]):
            result=subprocess.run(list(map(str,args)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/f'command-{i}.log').write_bytes(result.stdout)
            if result.returncode:raise RuntimeError('Packaging failed')
        pbo=addons/(prefix+'.pbo');_,props,entries=read_pbo(pbo)
        assert props['prefix']==prefix and entries=={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
        (mod/'Addons').mkdir(parents=True);shutil.copy2(pbo,mod/'Addons'/pbo.name);shutil.copytree(mission,deployed)
        assert sha(pbo)==sha(mod/'Addons'/pbo.name) and sha(mission/'init.c')==sha(deployed/'init.c')
        record=copy.deepcopy(ref)
        record.update(status='FROZEN_REGIONAL_VISUAL_GROUP_RUNTIME_PENDING',parent_reference_sha256=sha(parent),poses=phases,finish_s=restore+3,
            script_sha256=sha(script),mission_sha256=sha(mission/'init.c'),probe_pbo_sha256=sha(pbo),deployed_mod=str(mod),deployed_mission=str(deployed),
            camera_header='BALTIC_FOUNDATION_'+stem.upper(),metrics_header=f'BALTIC_FOUNDATION_CLIENT_METRICS_G_{name.upper()}_V1',
            camera_log=f'baltic_foundation_{stem}.log',metrics_log=f'baltic_foundation_client_metrics_g_{name}_v1.log',
            anchor=dict(xz=xz,terrain_y=ground,minimum_water_distance_m=distance,water_sha256={p.name:sha(p) for p in hydro}),
            instrumentation_change='Same original poses, local timing restarted per group and dry player anchor nearby. No world or rendering material changes.',
            capture_api='Computer Use observed and saved original pixels',capture_change='Regional observations; does not isolate the precise mechanism of the original distant-camera crash.',
            limits=['Actual saved pixels require visual inspection.','Ground/medium original nearplane; selected aerials retain diagnostic nearplane10m.','Grouped sessions do not prove arbitrary long-distance free-camera transitions.','Temporary fixture, not gameplay or multiplayer capacity.'])
        target=ev/'reference.json';target.write_text(json.dumps(record,indent=2)+'\n')
        all_refs.append(dict(group=name,reference=str(target),sha256=sha(target),finish_s=restore+3,mission=mission.name,mod=str(mod)))
    index=ROOT/'evidence/overnight-2026-10-01/visual-groups-index.json'
    if index.exists():raise ValueError('Preserve prior index')
    index.write_text(json.dumps(all_refs,indent=2)+'\n');print(json.dumps(all_refs,indent=2))

if __name__=='__main__':main()
