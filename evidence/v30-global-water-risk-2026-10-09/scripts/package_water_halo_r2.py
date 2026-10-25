from pathlib import Path
import json,hashlib,shutil,subprocess,sys
import numpy as np
import shapely
from shapely.geometry import Polygon,Point,box
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/halo-fix-v3');B9=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water'),str(W/'tools/playtest')]
from attach_navmesh import read_pbo
from wrp0wzd import read,write,object_record
from v30_common import cell_planes
from engine_water_model import ODOL
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=json.loads((E/'halo-fix-r2-authoring.json').read_text());changes={r['object_id']:r for r in ref['changes']}
water=Path('P:/Mods/@DayZ_Baltic_ValleySmoothC1R3P/Addons/baltic_water_v30.pbo');assert sha(water)==ref['old_water_sha256']
_,props,old=read_pbo(water);_,p2,patch=read_pbo(B/'compile/out/baltic_water_v30.pbo')
assert props==p2 and old['config.bin']==patch['config.bin']
names={c['new_model'] for c in changes.values() if c['new_model']};assert set(patch)==names|{'config.bin'} and not names.intersection(old)
merged=dict(old);merged.update(patch);dest=B/'water/temp/baltic_water_v30';dest.mkdir(parents=True,exist_ok=True)
for name,data in merged.items():
    p=dest/name;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==data
    else:p.write_bytes(data)
terrain_ref=json.loads((E/'targeted-pocket-removal-verification.json').read_text())
assert terrain_ref['status']=='PASS_OFFLINE_TARGETED_FLOOD_REMOVAL'
terrain=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/measured-bank-bed-r1/terrain.npz')
assert sha(terrain)==terrain_ref['terrain_sha256']
newheights=np.load(terrain)['heights']
baseheights=np.load(B9/'candidate-c1r3p/terrain_valley.npz')['heights']
water_source=np.load('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
planes=cell_planes(water_source['cls'],water_source['level'],sea_cut=.51)
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
    seam_length=0.;negative_old_seam=False
    if c['closed_micro_points']:
        oldgeom=shapely.from_geojson(c['old_geometry']);x0,z0,x1,z1=oldgeom.bounds
        same=[];higher=[]
        for row in range(max(0,int((12282-z1)//6)-1),min(2046,int((12282-z0)//6)+1)+1):
            for col in range(max(0,int(x0//6)-1),min(2046,int(x1//6)+1)+1):
                level=planes[row,col]
                if not np.isfinite(level):continue
                cell=box(col*6,12276-row*6,col*6+6,12282-row*6)
                if abs(level-c['origin'][1])<1e-5:same.append(cell)
                if c['origin'][1]-1e-5<=level<=c['origin'][1]+.02501:higher.append(cell)
        core=oldgeom.intersection(shapely.union_all(same))
        # Stop at the 1 mm authoring overlap limit near the exterior dry shore.
        # A margin test there would demand geometry outside the permitted water domain.
        seam=core.boundary.intersection(shapely.union_all(higher).buffer(-.001))
        # Continuous line containment after compilation, including float32 placement.
        uncovered=seam.difference(geom.buffer(-.0004))
        assert uncovered.length<1e-5,(ident,'whole seam',uncovered.length)
        seam_length=seam.length
        negative_old_seam=seam.difference(core.buffer(-.0004)).length>.01
        assert negative_old_seam and seam_length>.01

    visible=min(od.lods,key=lambda l:abs(l.resolution-1));vv=np.array([(q.x,q.y,q.z) for q in visible.vertices])+pos
    vg=shapely.union_all([Polygon(vv[f.vertex_indices][:,[0,2]]) for f in visible.faces])
    assert geom.symmetric_difference(vg).area<1e-8
    checks.append(dict(id=ident,model=c['new_model'],sha256=sha(dest/c['new_model']),compiled_footprint_hausdorff_m=err,
        nominal_level_m=float(v[0,1]),micro_points_strictly_inside=len(c['closed_micro_points']),continuous_seam_m=seam_length,unrepaired_seam_rejected=negative_old_seam))
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
assert np.array_equal(before['heights'],baseheights[::-1])
write(stage/'baltic_trial.wrp',before['header'],newheights[::-1],before['materials'],records,before['terminator'])
after=read(stage/'baltic_trial.wrp');oldid={o['id']:o for o in before['objects']};newid={o['id']:o for o in after['objects']}
assert np.array_equal(newheights[::-1],after['heights']) and all(before[k]==after[k] for k in ('header','materials','terminator'))
assert set(oldid)-set(newid)==set(removed) and not (set(newid)-set(oldid))
assert all(o['bytes']==oldid[i]['bytes'] for i,o in newid.items() if i not in changes)
report=dict(status='HALO_R2_AND_MEASURED_TERRAIN_PACKED_WORLD_STAGED',checks=checks,water_sha256=sha(out/'baltic_water_v30.pbo'),world_source_sha256=sha(stage/'baltic_trial.wrp'),
    source_terrain_sha256=ref['terrain_sha256'],terrain_sha256=sha(terrain),objects_before=len(oldid),objects_after=len(newid),removed_stale_sliver_instances=removed,
    terrain_exact=False,terrain_declared_vertices_exact=True,changed_terrain_vertices=int((newheights!=baseheights).sum()),terrain_acceptance_sha256=sha(E/'targeted-pocket-removal-verification.json'),materials_exact=True,bridges_and_unaffected_objects_exact=True,old_water_entries_exact=True,
    strictly_covered_micro_points=sum(c['micro_points_strictly_inside'] for c in checks),continuous_seam_m=sum(c['continuous_seam_m'] for c in checks),limits=['World must be compiled, independently audited and measured in the engine before use.'])
(E/'halo-fix-r2-package.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('checks','removed_stale_sliver_instances')},indent=2))
