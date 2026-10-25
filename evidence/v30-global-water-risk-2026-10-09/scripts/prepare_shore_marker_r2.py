"""Keep native shoreline shader contracts while changing diagnostic colors only."""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys
B = Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E = W / 'evidence/v30-global-water-risk-2026-10-09'
sys.path.insert(0, str(W / 'tools/playtest'))
from attach_navmesh import read_pbo
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
archive = B / 'shore-material-marker'
archive.mkdir(exist_ok=True)
profiles = Path('P:/DayZ_MCP_dev/_client/profiles')
for name in ['DayZDiag_x64_2026-10-09_04-39-52.RPT', 'script_2026-10-09_04-39-54.log', 'baltic_shore_readback_v1.log']:
    shutil.copy2(profiles / name, archive / name)
root = B / 'shore-material-probe-r2'
src = root / 'baltic_shore_marker_r2'
src.mkdir(parents=True, exist_ok=True)
config = '''class CfgPatches { class BalticShoreMarkerR2 { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","BalticTrialWorld"}; }; };
class CfgMaterials
{
 class Shore;
 class ShoreWet;
 class BalticShoreMagentaR2: Shore
 {
  ambient[]={1,0,1,0.4}; diffuse[]={1,0,1,1}; forcedDiffuse[]={1,0,1,0}; emmisive[]={1,0,1,0}; specular[]={0,0,0,0};
 };
 class BalticShoreWetGreenR2: ShoreWet
 {
  ambient[]={0,1,0,0.4}; diffuse[]={0,1,0,1}; forcedDiffuse[]={0,1,0,0}; emmisive[]={0,1,0,0}; specular[]={0,0,0,0};
 };
};
class CfgWorlds { class CAWorld; class BalticTrial: CAWorld { shoreMaterial="#BalticShoreMagentaR2"; shoreWetMaterial="#BalticShoreWetGreenR2"; }; };
'''
(src / 'config.cpp').write_text(config)
cv = 'C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe'
bank = 'C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe'
subprocess.run([cv, '-bin', '-dst', str(src / 'config.bin'), str(src / 'config.cpp')], check=True, capture_output=True)
packed = root / 'packed'
packed.mkdir(exist_ok=True)
subprocess.run([bank, '-property', 'prefix=' + src.name, '-dst', str(packed), str(src)], check=True, capture_output=True)
pbo = packed / (src.name + '.pbo')
_, _, entries = read_pbo(pbo)
assert entries['config.bin'] == (src / 'config.bin').read_bytes()
assert entries['config.cpp'] == (src / 'config.cpp').read_bytes()
target = Path('P:/Mods/@BalticShoreMarkerR2/Addons')
target.mkdir(parents=True, exist_ok=True)
shutil.copy2(pbo, target / pbo.name)
assert sha(pbo) == sha(target / pbo.name)
missions = Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')
source = missions / 'BalticShoreDiagnosticV1.BalticTrial'
mission = missions / 'BalticShoreDiagnosticWind20.BalticTrial'
mission.mkdir(exist_ok=True)
for name in ['init.c', 'cfggameplay.json', 'cfgeconomycore.xml', 'cfgenvironment.xml', 'cfgweather.xml']:
    if (source / name).is_file():
        shutil.copy2(source / name, mission / name)
text = (source / 'init.c').read_text()
assert 'SetLimits(0.1, 0.1)' in text and 'GetWindMagnitude().Set(0.1, 0, 3600)' in text
text = text.replace('GetWindMagnitude().SetLimits(0.1, 0.1)', 'GetWindMagnitude().SetLimits(20, 20)')
text = text.replace('GetWindMagnitude().Set(0.1, 0, 3600)', 'GetWindMagnitude().Set(20, 0, 3600)')
(mission / 'init.c').write_text(text.rstrip() + '\n')
(root / 'wind20-init.c').write_bytes((mission / 'init.c').read_bytes())
report = dict(status='DIAGNOSTIC_ONLY_NOT_FOR_RELEASE', mod=str(target.parent), pbo_sha256=sha(pbo),
    mission=str(mission), mission_sha256=sha(mission / 'init.c'),
    source='P:/DZ/data/config.cpp:2098-2135',
    reason='R1 changed the native shore shader contract to Terrain and crashed; this is a suspected mechanism, not an isolated crash cause. R2 keeps Shore/ShoreWet shaders, stages, UVs and alpha.',
    budget='One contract repair R2; baseline wind20 followed by R2 if baseline reproduces. No material tuning loop.',
    gate='Native readback + visible real-shore marker positive control. No color/no baseline means inconclusive, not cleared.')
(root / 'reference.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
