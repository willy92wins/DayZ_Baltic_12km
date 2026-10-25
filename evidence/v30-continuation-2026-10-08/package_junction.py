"""Preserve archive entries and compensate the changed model's Binarize centre."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2')
BASE=Path('E:/DayZ-Baltic-Build/v30-v11/24')
sys.path[:0]=[str(ROOT/'tools/playtest'),str(ROOT/'tools/terrain'),str(ROOT/'tools/water')]
from attach_navmesh import read_pbo
from wrp0wzd import read,write,object_record
import engine_water_model as ewm
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
baseline=Path('P:/Mods/@DayZ_Baltic_BugRecheckPreview/Addons/baltic_water_v30.pbo')
assert sha(baseline)=='07c5295f112746d621e96324467b1d54fccc415a785c227feb245f59adff503f'
_,props,old=read_pbo(baseline)
_,patch_props,patch=read_pbo(OUT/'compile/baltic_water_v30.pbo')
assert props==patch_props and patch['config.bin']==old['config.bin']
name='pilot_00001.p3d';assert set(patch)=={'config.bin',name}
expected=dict(old);expected[name]=patch[name]
temp=OUT/'water/temp/baltic_water_v30';temp.mkdir(parents=True,exist_ok=True)
for k,data in expected.items():
    dest=temp/k;dest.parent.mkdir(parents=True,exist_ok=True)
    assert not dest.exists() or dest.read_bytes()==data
    dest.write_bytes(data)
bank=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe')
assert bank.is_file()
dest=OUT/'water/packed';dest.mkdir(exist_ok=True)
assert not (dest/'baltic_water_v30.pbo').exists()
result=subprocess.run([str(bank),'-property','prefix='+props['prefix'],'-property','product='+props['product'],'-dst',str(dest),str(temp)],capture_output=True)
(OUT/'water/filebank.log').write_bytes(result.stdout+result.stderr)
assert result.returncode==0
_,actual_props,actual=read_pbo(dest/'baltic_water_v30.pbo')
assert actual_props==props and actual==expected
shutil.copyfile(dest/'baltic_water_v30.pbo',OUT/'water/baltic_water_v30.pbo')
# The engine uses centred ODOL vertices. The source WRP must use the new centre,
# exactly as derive_world_v30.py:76-80 does; authored world coordinates stay fixed.
native=ewm.ODOL.from_file(str(temp/name))
center=native.model_info.bounding_center
new_center=np.array([center.x,center.y,center.z])
manifest=json.loads((OUT/'water/pieces.json').read_text())
model=next(m for m in manifest['model_list'] if m['name']==name[:-4]);b=model['bounds_rel']
assert np.max(np.abs(new_center-np.array([(min(b[0],0)+max(b[2],0))/2,0,(min(b[1],0)+max(b[3],0))/2])))<1e-5
source=Path('E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/package-wave-banks/world/stage/BalticTrialWorld')
stage=OUT/'world/root/dayz_baltic_12km_dev/tb/narva_trial'
shutil.copytree(source,stage)
wrp=read(source/'baltic_trial.wrp')
target=[o for o in wrp['objects'] if o['name']=='baltic_water_v30\\'+name]
assert len(target)==1
pose=next(p for p in manifest['poses'] if p['model']==target[0]['name'])
matrix=target[0]['matrix'].copy();matrix[9:]=list(np.asarray(pose['origin'])+new_center)
records=[object_record(matrix,o['id'],o['raw_name']) if o['id']==target[0]['id'] else o['bytes'] for o in wrp['objects']]
write(stage/'baltic_trial.wrp',wrp['header'],wrp['heights'],wrp['materials'],records,wrp['terminator'])
back=read(stage/'baltic_trial.wrp')
assert all(wrp[k]==back[k] for k in ['header','materials','terminator'])
assert np.array_equal(wrp['heights'],back['heights'])
assert sum(a['bytes']!=b['bytes'] for a,b in zip(wrp['objects'],back['objects']))==1
report=dict(status='PACKED_WATER_AND_STAGED_WORLD',water_pbo_sha256=sha(OUT/'water/baltic_water_v30.pbo'),
            unchanged_water_entries=len(old)-1,changed_water_entries=[name],
            world_source_sha256=sha(stage/'baltic_trial.wrp'),heights_exact=True,materials_exact=True,
            authored_origin=pose['origin'],old_wrp_matrix=target[0]['matrix'],new_wrp_matrix=back['objects'][wrp['objects'].index(target[0])]['matrix'],
            centre_compensation_required=True,other_world_records_exact=len(wrp['objects'])-1)
(OUT/'package-stage.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=1))
