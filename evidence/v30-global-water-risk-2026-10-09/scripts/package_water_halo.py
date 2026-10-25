from pathlib import Path
import json,hashlib,shutil,subprocess,sys
import numpy as np
import shapely
from shapely.geometry import Polygon,Point
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/halo-fix-v2');B9=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water'),str(W/'tools/playtest')]
from attach_navmesh import read_pbo
from wrp0wzd import read,write,object_record
from engine_water_model import ODOL
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=json.loads((E/'halo-fix-authoring.json').read_text());changes={r['object_id']:r for r in ref['changes']}
water=Path('P:/Mods/@DayZ_Baltic_ValleySmoothC1R3P/Addons/baltic_water_v30.pbo');assert sha(water)==ref['old_water_sha256']
_,props,old=read_pbo(water);_,p2,patch=read_pbo(B/'compile/out/baltic_water_v30.pbo')
assert props==p2 and old['config.bin']==patch['config.bin']
names={c['new_model'] for c in changes.values() if c['new_model']};assert set(patch)==names|{'config.bin'} and not names.intersection(old)
merged=dict(old);merged.update(patch);dest=B/'water/temp/baltic_water_v30';dest.mkdir(parents=True,exist_ok=True)
for name,data in merged.items():
    p=dest/name;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==data
    else:p.write_bytes(data)
checks=[]
for ident,c in changes.items():
    if c['new_model'] is None:continue
    od=ODOL.from_file(str(dest/c['new_model']));q=od.model_info.bounding_center;center=np.array([q.x,q.y,q.z])
    pos=np.asarray(np.array(c['origin'])+center,dtype=np.float32).astype(float);c['matrix']=np.eye(3).ravel().tolist()+pos.tolist()
    lod=min(od.lods,key=lambda l:abs(l.resolution-3e15));v=np.array([(q.x,q.y,q.z) for q in lod.vertices])+pos
    assert np.ptp(v[:,1])<1e-6 and abs(v[0,1]-c['origin'][1])<1e-5
    geom=shapely.union_all([Polygon(v[f.vertex_indices][:,[0,2]]) for f in lod.faces]);authored=shapely.from_geojson(c['geometry'])
    err=geom.hausdorff_distance(authored);assert err<.0006,(ident,err)
    for x,z in c['closed_micro_points']:assert geom.contains(Point(x,z)),(ident,x,z,'compiled microgap remains')
    visible=min(od.lods,key=lambda l:abs(l.resolution-1));vv=np.array([(q.x,q.y,q.z) for q in visible.vertices])+pos
    vg=shapely.union_all([Polygon(vv[f.vertex_indices][:,[0,2]]) for f in visible.faces])
    assert geom.symmetric_difference(vg).area<1e-8
    checks.append(dict(id=ident,model=c['new_model'],sha256=sha(dest/c['new_model']),compiled_footprint_hausdorff_m=err,
        nominal_level_m=float(v[0,1]),micro_points_strictly_inside=len(c['closed_micro_points'])))
out=B/'water/packed';out.mkdir(parents=True,exist_ok=True)
bank=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe')
if not (out/'baltic_water_v30.pbo').exists():
    r=subprocess.run([str(bank),'-property','prefix='+props['prefix'],'-property','product='+props['product'],'-dst',str(out),str(dest)],capture_output=True)
    (B/'water/filebank.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
_,pp,packed=read_pbo(out/'baltic_water_v30.pbo');assert pp==props and packed==merged
src=B9/'world-c1r3p/root/dayz_baltic_12km_dev/tb/narva_trial';before=read(src/'baltic_trial.wrp');records=[];removed=[]
for obj in before['objects']:
    c=changes.get(obj['id'])
    if c is None:records.append(obj['bytes']);continue
    assert obj['name'].split('\\')[-1]==c['old_model']
    if c['new_model'] is None:removed.append(obj['id']);continue
    raw=('baltic_water_v30\\'+c['new_model']).encode('ascii')
    if obj['raw_name'].endswith(b'\0'):raw+=b'\0'
    records.append(object_record(c['matrix'],obj['id'],raw))
stage=B/'world/root/dayz_baltic_12km_dev/tb/narva_trial';shutil.copytree(src,stage,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
write(stage/'baltic_trial.wrp',before['header'],before['heights'],before['materials'],records,before['terminator'])
after=read(stage/'baltic_trial.wrp');oldid={o['id']:o for o in before['objects']};newid={o['id']:o for o in after['objects']}
assert np.array_equal(before['heights'],after['heights']) and all(before[k]==after[k] for k in ('header','materials','terminator'))
assert set(oldid)-set(newid)==set(removed) and not (set(newid)-set(oldid))
assert all(o['bytes']==oldid[i]['bytes'] for i,o in newid.items() if i not in changes)
report=dict(status='HALO_WATER_PACKED_WORLD_STAGED',checks=checks,water_sha256=sha(out/'baltic_water_v30.pbo'),world_source_sha256=sha(stage/'baltic_trial.wrp'),
    source_terrain_sha256=ref['terrain_sha256'],objects_before=len(oldid),objects_after=len(newid),removed_stale_sliver_instances=removed,
    terrain_exact=True,materials_exact=True,bridges_and_unaffected_objects_exact=True,old_water_entries_exact=True,
    strictly_covered_micro_points=sum(c['micro_points_strictly_inside'] for c in checks),limits=['World must be compiled, independently audited and measured in the engine before use.'])
(E/'halo-fix-package.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('checks','removed_stale_sliver_instances')},indent=2))
