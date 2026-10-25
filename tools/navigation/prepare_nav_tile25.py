"""Single-variable diagnostic: explicit tileWidth; exact WRP and other entries."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo, sha

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--tile-width', type=float, choices=[25,12.5], default=25)
args=ap.parse_args()
tile_text='25' if args.tile_width==25 else '12.5'
tile_label='tile25' if args.tile_width==25 else 'tile12p5'
out=ROOT/f'packages/baltic-regional-{tile_label}-v1'
if out.exists(): raise ValueError('Fresh trial destination required')
baseline=ROOT/'packages/baltic-regional-outline-v3/navigation/Addons/narva_trial.pbo'
raw,props,before=read_pbo(baseline)
if sha(raw)!='e5c6865acf9794b13d068f935e9e9774ab45341fb97506170374fe3d560c2078':
    raise ValueError('Frozen baseline changed')
cfg=(ROOT/'packages/baltic-regional-outline-v3/source/BalticTrialWorld/config.cpp').read_text()
if cfg.count('tileWidth=50;')!=1: raise ValueError('Config anchor changed')
out.mkdir(parents=True)
source=out/'config.cpp'; source.write_text(cfg.replace('tileWidth=50;',f'tileWidth={tile_text};'))
convert=Path(r'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\CfgConvert\CfgConvert.exe')
bank=Path(r'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\PboUtils\FileBank.exe')
def run(args,name):
    p=subprocess.run(list(map(str,args)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/name).write_bytes(p.stdout)
    if p.returncode: raise ValueError(f'{name}: {p.returncode}')
# Prove the source config reconstructs the current compiled configuration first.
original=out/'config_original.cpp'; original.write_text(cfg)
run([convert,'-bin','-dst',out/'config_original.bin',original],'original.log')
if (out/'config_original.bin').read_bytes()!=before['config.bin']:
    raise ValueError('Source config does not reproduce baseline bytes')
run([convert,'-bin','-dst',out/'config.bin',source],'convert.log')
stage=out/'compiled/narva_trial'; stage.mkdir(parents=True)
expected=dict(before); expected['config.bin']=(out/'config.bin').read_bytes()
for name,data in expected.items():
    p=stage/name; p.parent.mkdir(exist_ok=True,parents=True); p.write_bytes(data)
dest=out/'Addons'; dest.mkdir()
run([bank,'-property','prefix='+props['prefix'],'-property','product=dayz ugc','-dst',dest,stage],'filebank.log')
packed,afterprops,after=read_pbo(dest/'narva_trial.pbo')
if after!=expected or props['prefix']!=afterprops['prefix']:
    raise ValueError('Unexpected package delta')
result={'status':'DIAGNOSTIC_CONFIG_PACKED_NOT_NEW_NAVMESH', 'variable':'tileWidth', 'before':50,'after':args.tile_width,
        'pbo_sha256':sha(packed),'wrp_sha256':sha(after['baltic_trial.wrp']),
        'bootstrap_nm_sha256':sha(after['navmesh/baltic_trial.nm']),
        'other_entries_exact':len(before)-1,
        'acceptance':'Same frozen 279 points, six paths and 2m 3D gate. No tolerance change.',
        'limits':['Generate a fresh NM; bootstrap only until then.', 'Smaller tiles are a hypothesis for precision, not a demonstrated root cause.']}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
