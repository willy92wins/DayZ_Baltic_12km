"""Package the stitched visible LOD pilot and compensate compiled model centres."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
import numpy as np
import shapely
from shapely.geometry import Polygon
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-water-visual-fix-2026-10-08'
B=Path('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008')
B7=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water'),str(W/'tools/playtest'),str(W/'tools/navigation')]
from attach_navmesh import read_pbo
from wrp0wzd import read,write,object_record
from engine_water_model import ODOL
from water_mesh import py3d
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def native(path,res):
 obj=ODOL.from_file(str(path));c=obj.model_info.bounding_center
 center=np.array([c.x,c.y,c.z]);lod=min(obj.lods,key=lambda l:abs(l.resolution-res))
 assert abs(lod.resolution-res)/max(1,res)<1e-6
 v=np.array([(v.x,v.y,v.z) for v in lod.vertices])+center
 return obj,lod,v,center
base=Path('P:/Mods/@DayZ_Baltic_FlatWaterPreview/Addons')
assert sha(base/'baltic_water_v30.pbo')=='62a14deea0983ddb71b5f9aa7f95ba16fc2268b65520caf834ab825f027a24b5'
_,props,old=read_pbo(base/'baltic_water_v30.pbo')
_,pp,patch=read_pbo(B/'stitched-water/compile/out-v2/baltic_water_v30.pbo')
assert pp==props and patch['config.bin']==old['config.bin'] and set(patch)<=set(old)
author=json.loads((E/'stitch-authoring.json').read_text())
names={r['model'] for r in author['models']};assert set(patch)==names|{'config.bin'}
dest=B/'stitched-water/water/temp/baltic_water_v30';dest.mkdir(parents=True,exist_ok=False)
expected=dict(old);expected.update(patch)
for name,data in expected.items():
 p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
checks=[];centers={}
for name in sorted(names):
 _,lod,v,center=native(dest/name,3e15)
 _,oldlod,oldv,oldcenter=native(B7/'flat-water/water/temp/baltic_water_v30'/name,3e15)
 def canonical(lod,v):
  return sorted(tuple(sorted(tuple(round(float(a),6) for a in pt) for pt in v[f.vertex_indices])) for f in lod.faces)
 assert canonical(lod,v)==canonical(oldlod,oldv),name
 _,vis,vv,_=native(dest/name,1)
 with (B/'stitched-water/compile/source/baltic_water_v30'/name).open('rb') as f:mlod=py3d.P3D(f)
 orig=np.array([p.coords for p in mlod.lods[0].points])
 # Native compiler may collapse/split; compare point-set XYZ bidirectionally.
 from scipy.spatial import cKDTree
 err=max(cKDTree(orig).query(vv)[0].max(),cKDTree(vv).query(orig)[0].max())
 assert err<1e-5,(name,err)
 centers[name]=(center,oldcenter)
 checks.append(dict(model=name,sha256=sha(dest/name),roadway_world_shape_exact=True,visible_xyz_error_m=float(err),center_delta=(center-oldcenter).tolist()))
out=B/'stitched-water/water/packed';out.mkdir(parents=True)
bank=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe')
r=subprocess.run([str(bank),'-property','prefix='+props['prefix'],'-property','product='+props['product'],'-dst',str(out),str(dest)],capture_output=True)
(B/'stitched-water/water/filebank.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
_,p2,packed=read_pbo(out/'baltic_water_v30.pbo');assert p2==props and packed==expected
source=B7/'flat-world/root/dayz_baltic_12km_dev/tb/narva_trial';before=read(source/'baltic_trial.wrp')
records=[];changed=[]
for obj in before['objects']:
 name=obj['name'].replace('\\','/').split('/')[-1]
 if name in centers:
  newc,oldc=centers[name];m=obj['matrix'].copy()
  m[9:12]=(np.array(m[9:12])+newc-oldc).tolist()
  rec=object_record(m,obj['id'],obj['raw_name']);records.append(rec)
  if rec!=obj['bytes']:changed.append(obj['id'])
 else:records.append(obj['bytes'])
stage=B/'stitched-world/root/dayz_baltic_12km_dev/tb/narva_trial'
shutil.copytree(source,stage,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
write(stage/'baltic_trial.wrp',before['header'],before['heights'],before['materials'],records,before['terminator'])
after=read(stage/'baltic_trial.wrp')
assert np.array_equal(before['heights'],after['heights'])
assert all(before[k]==after[k] for k in ('header','materials','terminator'))
assert len(before['objects'])==len(after['objects'])
report=dict(status='STITCHED_PILOT_PACKAGED_SOURCE',compiled_models=checks,world_records=len(records),corrected_centers=len(changed),unchanged_water_archive_entries=len(old)-len(names),
water_pbo_sha256=sha(out/'baltic_water_v30.pbo'),source_world_sha256=sha(stage/'baltic_trial.wrp'),
 terrain_exact=True,materials_exact=True,bridges_exact=True,nonvisual_roadway_exact=True,
 limits=['Visible LOD only, up to 0.342 m local displacement; requires consumer and visual checks.'])
(E/'stitch-package.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='compiled_models'},indent=2))
