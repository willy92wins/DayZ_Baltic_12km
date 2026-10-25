"""Integrate two independently verified seam additions; existing contents exact."""
from pathlib import Path
import json,shutil,subprocess,sys
import numpy as np
sys.path.insert(0,r'E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
from discover_native_turns import B12,W,sha
B=Path(r'E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009')
B13=Path(r'E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
sys.path.insert(0,str(B12))
from author_global_visual import read_pbo,read
from wrp0wzd import write,object_record

stage=json.loads((B/'stage.json').read_text());verify=json.loads((B/'seam-verification.json').read_text())
assert verify['status']=='PASS_COMPILED_EXACT_SEAMS' and not verify['failures']
oldwater=Path(r'E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009/package/water/packed/baltic_water_v30.pbo');patch=B/'compile-seams/out/baltic_water_v30.pbo'
assert sha(oldwater)==stage['water_sha256'] and sha(patch)==verify['patch_sha256']
_,props,old=read_pbo(oldwater);_,pp,extra=read_pbo(patch)
assert props==pp and old['config.bin']==extra['config.bin'] and set(old)&set(extra)=={'config.bin'}
merged=dict(old);merged.update(extra)
temp=B/'package/water/temp/baltic_water_v30';temp.mkdir(parents=True,exist_ok=False)
for name,data in merged.items():
    target=temp/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
out=B/'package/water/packed';out.mkdir(exist_ok=False)
command=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
for k,v in props.items():command+=['-property',k+'='+v]
command+=['-dst',str(out),str(temp)]
result=subprocess.run(command,capture_output=True);(B/'package/water/filebank.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0
_,gotprops,got=read_pbo(out/'baltic_water_v30.pbo');assert props==gotprops and got==merged
wp=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';assert sha(wp)==stage['world_source_sha256']
backup=B/'terrain-only.wrp';assert not backup.exists();shutil.copyfile(wp,backup)
before=read(wp);records=[o['bytes'] for o in before['objects']];ids={o['id'] for o in before['objects']}
for row in verify['checks']:
    assert all(row['gates'].values()) and row['object_id'] not in ids
    records.append(object_record(row['matrix'],row['object_id'],('baltic_water_v30\\'+row['model']).encode('ascii')))
write(wp,before['header'],before['heights'],before['materials'],records,before['terminator'])
after=read(wp)
assert [o['bytes'] for o in after['objects'][:len(before['objects'])]]==[o['bytes'] for o in before['objects']]
assert np.array_equal(before['heights'],after['heights']) and all(before[k]==after[k] for k in ('header','materials','terminator'))
assert str(B/'package/water/temp/baltic_water_v30') in (B/'compile_native_world.ps1').read_text()
report=dict(status='GLOBAL_CONTOUR_WITH_EXACT_SEAMS_STAGED',terrain_sha256=stage['terrain_sha256'],water_sha256=sha(out/'baltic_water_v30.pbo'),world_source_sha256=sha(wp),
            original_objects_exact=True,added_objects=len(verify['checks']),objects=len(after['objects']),old_water_contents_exact=True,packed_model_entries=sum(k.endswith('.p3d') for k in got),
            source_terrain_only_world_sha256=sha(backup),limits=['Whole-domain coverage rerun and compiled world required.'])
(B/'package-seams.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
