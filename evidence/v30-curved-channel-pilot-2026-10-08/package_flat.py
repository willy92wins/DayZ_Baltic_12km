"""Package additive flat models; preserve unrelated archive entries/WRP records."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
import numpy as np
import shapely
from shapely.geometry import Polygon,box
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008')
E=W/'evidence/v30-curved-channel-pilot-2026-10-08'
FIT=Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water'),str(W/'tools/playtest')]
from attach_navmesh import read_pbo
from wrp0wzd import read,write,object_record
from verify_channel_reaches_v30 import retained_pond_faces
import engine_water_model as ewm
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    assert json.loads((E/'flat-verification-r2.json').read_text())['status']=='PASS_OFFLINE_FLAT_FALLBACK'
    author=json.loads((E/'flat-water-authoring.json').read_text())
    models={m['name']:m for m in author['new_models']}
    oldmanifest=json.loads((FIT/'water/pieces.json').read_text())
    baseline=Path('P:/Mods/@DayZ_Baltic_Floor095Preview/Addons/baltic_water_v30.pbo')
    assert sha(baseline)=='992000c42964ff45017488bbb62bab5ae5b146999712c9108b9ccc722e464702'
    _,props,old=read_pbo(baseline)
    _,patchprops,patch=read_pbo(B/'flat-water/compile/out-v2/baltic_water_v30.pbo')
    assert patchprops==props and patch['config.bin']==old['config.bin']
    assert set(patch)==set(m+'.p3d' for m in models)|{'config.bin'}
    assert not set(m+'.p3d' for m in models).intersection(old)
    temp=B/'flat-water/water/temp/baltic_water_v30';temp.mkdir(parents=True)
    expected=dict(old);expected.update(patch)
    for name,data in expected.items():
        dest=temp/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    checks=[];centers={}
    for pose in author['new_poses']:
        name=Path(pose['model'].replace('\\','/')).stem
        o=ewm.ODOL.from_file(str(temp/(name+'.p3d')))
        lod=next(l for l in o.lods if 2.9e15<l.resolution<3.1e15)
        center=o.model_info.bounding_center;cv=np.array([center.x,center.y,center.z]);centers[name]=cv
        v=np.array([(p.x,p.y,p.z) for p in lod.vertices])+cv
        native=shapely.union_all([Polygon(v[f.vertex_indices][:,[0,2]]) for f in lod.faces])
        ox,oy,oz=pose['origin'];bb=models[name]['bounds_rel']
        source=shapely.union_all([f[0] for f in retained_pond_faces(B/'flat-water',dict(poses=[pose],model_list=[models[name]]),box(ox+bb[0],oz+bb[1],ox+bb[2],oz+bb[3]))])
        world=shapely.transform(native,lambda a:a+np.array([ox,oz]))
        error=world.hausdorff_distance(source)
        assert error<1e-5 and np.max(np.abs(v[:,1]))<1e-6,(name,error)
        checks.append(dict(model=name,compiled_sha256=sha(temp/(name+'.p3d')),geometry_error_m=error))
    packed=B/'flat-water/water/packed';packed.mkdir()
    bank=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe')
    run=subprocess.run([str(bank),'-property','prefix='+props['prefix'],'-property','product='+props['product'],'-dst',str(packed),str(temp)],capture_output=True)
    (B/'flat-water/water/filebank.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0
    _,newprops,entries=read_pbo(packed/'baltic_water_v30.pbo');assert newprops==props and entries==expected
    source=Path('E:/DayZ-Baltic-Build/v30-navigation-contract-20261008/world/root/dayz_baltic_12km_dev/tb/narva_trial')
    assert sha(source/'baltic_trial.wrp')=='81b942977d4442a5316e6203a2f2c4343494904eaf9a0d31ef9714f45de89813'
    before=read(source/'baltic_trial.wrp')
    iswater=lambda o:o['name'].lower().startswith(('baltic_water_v30\\','dz\\water\\streams\\'))
    water=[o for o in before['objects'] if iswater(o)]
    keep_other=[o for o in before['objects'] if not iswater(o)]
    assert len(keep_other)==9 and all(o['name'].endswith('bridge_metal_25.p3d') for o in keep_other)
    assert len(water)==len(oldmanifest['poses'])
    remove_ids=set()
    for obj,pose in zip(water,oldmanifest['poses']):
        assert obj['name'].lower()==pose['model'].lower(),(obj['name'],pose['model'])
        if pose in author['removed_poses']:remove_ids.add(obj['id'])
    assert len(remove_ids)==len(author['removed_poses'])
    records=[o['bytes'] for o in before['objects'] if o['id'] not in remove_ids]
    next_id=max(o['id'] for o in before['objects'])+1
    for i,pose in enumerate(author['new_poses']):
        name=Path(pose['model'].replace('\\','/')).stem
        pos=np.asarray(pose['origin'])+centers[name]
        records.append(object_record([1,0,0,0,1,0,0,0,1,*pos],next_id+i,pose['model'].encode('ascii')))
    stage=B/'flat-world/root/dayz_baltic_12km_dev/tb/narva_trial'
    shutil.copytree(source,stage,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    h=np.load(B/'r3-transition-proposal/terrain_flat.npz')['heights'][::-1,:]
    write(stage/'baltic_trial.wrp',before['header'],h,before['materials'],records,before['terminator'])
    after=read(stage/'baltic_trial.wrp');unchanged={o['id']:o['bytes'] for o in before['objects'] if o['id'] not in remove_ids}
    assert np.array_equal(after['heights'],h) and all(before[k]==after[k] for k in ('header','materials','terminator'))
    assert all(o['bytes']==unchanged[o['id']] for o in after['objects'] if o['id'] in unchanged)
    assert len({o['id'] for o in after['objects']})==len(after['objects'])
    report=dict(status='PACKED_FLAT_WATER_STAGED_WORLD',water_pbo_sha256=sha(packed/'baltic_water_v30.pbo'),
                unchanged_archive_entries=len(old),added_archive_entries=len(models),compiled_models=checks,
                unchanged_world_records=len(unchanged),removed_world_records=len(remove_ids),new_world_records=len(author['new_poses']),
                world_objects=len(after['objects']),world_source_sha256=sha(stage/'baltic_trial.wrp'),bridges_exact=True,
                header_materials_terminator_exact=True,terrain_exact=True)
    (E/'flat-package-stage.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='compiled_models'},indent=2),flush=True)

if __name__=='__main__':main()
