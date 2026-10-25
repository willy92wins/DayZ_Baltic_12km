"""Isolate native screenshot calls from the unchanged twelve-camera tour."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parent=ROOT/'evidence/overnight-2026-10-01/foundation-visual-v3/reference.json'
    ref=json.loads(parent.read_text())
    original=ROOT/'packages/foundation-visual-v3/baltic_foundation_visual_v3/scripts/5_Mission/BalticRenderProbe.c'
    assert sha(original)==ref['script_sha256']
    ev=ROOT/'evidence/overnight-2026-10-01/foundation-visual-v4';out=ROOT/'packages/foundation-visual-v4'
    mission=ROOT/'missions/BalticFoundationVisualV4.BalticTrial'
    deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    mod=Path('P:/Mods/@BalticFoundationVisualV4')
    for path in [ev,out,mission,deployed,mod]:
        if path.exists():raise ValueError('Fresh output required: '+str(path))
    code=original.read_text().replace('visual_v3','visual_v4').replace('VISUAL_V3','VISUAL_V4').replace('METRICS_V3','METRICS_V4').replace('client_metrics_v2','client_metrics_v4')
    anchor='            MakeScreenshot(name);'
    assert code.count(anchor)==1
    code=code.replace(anchor,'            // No native screenshot request: visual evidence is observed through Computer Use.')
    code=code.replace('CAPTURE_REQUEST_','OBSERVATION_READY_')
    prefix='baltic_foundation_visual_v4';stage=out/prefix
    (stage/'scripts/5_Mission').mkdir(parents=True);ev.mkdir(parents=True)
    script=stage/'scripts/5_Mission/BalticRenderProbe.c';script.write_text(code)
    config=(ROOT/'packages/foundation-visual-v3/config.cpp').read_text().replace('baltic_foundation_visual_v3',prefix)
    (out/'config.cpp').write_text(config);addons=out/'Addons';addons.mkdir()
    shutil.copytree(ROOT/'missions/BalticFoundationVisualV3.BalticTrial',mission)
    tools=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
    for i,args in enumerate([[tools/'CfgConvert/CfgConvert.exe','-bin','-dst',stage/'config.bin',out/'config.cpp'],[tools/'PboUtils/FileBank.exe','-property','prefix='+prefix,'-property','product=dayz ugc','-dst',addons,stage]]):
        result=subprocess.run(list(map(str,args)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/f'command-{i}.log').write_bytes(result.stdout)
        if result.returncode:raise RuntimeError('Probe packaging failed')
    pbo=addons/(prefix+'.pbo');_,props,entries=read_pbo(pbo)
    assert props['prefix']==prefix and entries=={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    (mod/'Addons').mkdir(parents=True);shutil.copy2(pbo,mod/'Addons'/pbo.name);shutil.copytree(mission,deployed)
    assert sha(pbo)==sha(mod/'Addons'/pbo.name) and sha(mission/'init.c')==sha(deployed/'init.c')
    ref.update(status='FROZEN_NO_NATIVE_CAPTURE_CONTROL',parent_reference_sha256=sha(parent),script_sha256=sha(script),probe_pbo_sha256=sha(pbo),
               deployed_mod=str(mod),deployed_mission=str(deployed),camera_header='BALTIC_FOUNDATION_VISUAL_V4',metrics_header='BALTIC_FOUNDATION_CLIENT_METRICS_V4',
               capture_event='OBSERVATION_READY',capture_name_mode='No native capture; Computer Use evidence',
               instrumentation_change='Only native MakeScreenshot removed; identifiers/log names changed. Same cameras, times, player, metrics, world, profile and criteria.',
               capture_change='Native requests disabled to isolate V3 client crash at150s. This run cannot prove absence of causal relation from one non-reproduction.')
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n');print(json.dumps({k:ref[k] for k in ['script_sha256','probe_pbo_sha256','deployed_mission']}))
if __name__=='__main__':main()
