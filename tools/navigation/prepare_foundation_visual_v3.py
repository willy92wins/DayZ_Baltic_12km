"""Preserve V2, remove its unlinked global FPS call and test bare capture names."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parent = ROOT/'evidence/overnight-2026-10-01/foundation-visual-v2/reference.json'
    ref = json.loads(parent.read_text())
    original = ROOT/'packages/foundation-visual-v2/baltic_foundation_visual_v2/scripts/5_Mission/BalticRenderProbe.c'
    assert sha(original) == ref['script_sha256']
    ev = ROOT/'evidence/overnight-2026-10-01/foundation-visual-v3'
    out = ROOT/'packages/foundation-visual-v3'
    mission = ROOT/'missions/BalticFoundationVisualV3.BalticTrial'
    deployed = Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    mod = Path('P:/Mods/@BalticFoundationVisualV3')
    for path in [ev, out, mission, deployed, mod]:
        if path.exists(): raise ValueError('Fresh output required: '+str(path))
    code = original.read_text().replace('visual_v2', 'visual_v3').replace('VISUAL_V2', 'VISUAL_V3').replace('METRICS_V2', 'METRICS_V3')
    anchor = ' + ";" + GetFPS()'
    assert code.count(anchor) == 1
    code = code.replace(anchor, '')
    anchor = 'string name = "$profile:baltic_foundation_visual_v3_" + m_BalticRenderPhase + ".dds";'
    assert code.count(anchor) == 1
    code = code.replace(anchor, 'string name = "baltic_foundation_visual_v3_" + m_BalticRenderPhase;')
    prefix = 'baltic_foundation_visual_v3'
    stage = out/prefix
    (stage/'scripts/5_Mission').mkdir(parents=True)
    ev.mkdir(parents=True)
    script = stage/'scripts/5_Mission/BalticRenderProbe.c'
    script.write_text(code)
    config = (ROOT/'packages/foundation-visual-v2/config.cpp').read_text().replace('baltic_foundation_visual_v2', prefix)
    (out/'config.cpp').write_text(config)
    addons = out/'Addons'; addons.mkdir()
    shutil.copytree(ROOT/'missions/BalticFoundationVisualV2.BalticTrial', mission)
    tools = Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
    for i, args in enumerate([[tools/'CfgConvert/CfgConvert.exe', '-bin', '-dst', stage/'config.bin', out/'config.cpp'],
                              [tools/'PboUtils/FileBank.exe', '-property', 'prefix='+prefix, '-property', 'product=dayz ugc', '-dst', addons, stage]]):
        result = subprocess.run(list(map(str, args)), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out/f'command-{i}.log').write_bytes(result.stdout)
        if result.returncode: raise RuntimeError('Probe packaging failed')
    pbo = addons/(prefix+'.pbo')
    _, properties, entries = read_pbo(pbo)
    assert properties['prefix'] == prefix
    assert entries == {p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    (mod/'Addons').mkdir(parents=True)
    shutil.copy2(pbo, mod/'Addons'/pbo.name)
    shutil.copytree(mission, deployed)
    assert sha(pbo) == sha(mod/'Addons'/pbo.name)
    assert sha(deployed/'init.c') == sha(mission/'init.c')
    ref.update(status='PREPARED_AFTER_V2_INSTRUMENTATION_FAILURE', parent_reference_sha256=sha(parent),
               script_sha256=sha(script), probe_pbo_sha256=sha(pbo),
               deployed_mod=str(mod), deployed_mission=str(deployed),
               camera_header='BALTIC_FOUNDATION_VISUAL_V3', metrics_header='BALTIC_FOUNDATION_CLIENT_METRICS_V3',
               metrics_columns=9, capture_name_mode='bare name; documented default $profile:ScreenShotes output; runtime confirmation pending',
               instrumentation_change='Global GetFPS is declared but runtime says Function not linked in V2. Remove that call and column; preserve native DayZGame last/avg/min/max counters. No camera/terrain/criteria changes.',
               capture_change='V2 recorded requests but found no DDS in checked output roots. V3 tests the documented bare-name form; file existence and visual inspection remain required.')
    (ev/'reference.json').write_text(json.dumps(ref, indent=2)+'\n')
    print(json.dumps({k:ref[k] for k in ['status','script_sha256','probe_pbo_sha256','deployed_mod','deployed_mission']}))


if __name__ == '__main__': main()
