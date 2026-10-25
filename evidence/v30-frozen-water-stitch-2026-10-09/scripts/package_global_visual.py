"""Pack verified visible-only water and stage an isolated derived editable WRP."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
import numpy as np

B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(B))
from author_global_visual import B10,sha,read,read_pbo
from wrp0wzd import write,object_record

def main():
    check=json.loads((B/'compiled-verification-r2.json').read_text())
    assert check['status']=='PASS_COMPILED_VISIBLE_GEOMETRY' and not check['failed_models']
    proof=json.loads((B/'removal-proof.json').read_text());assert proof['status']=='PASS_ZERO_INTENDED_COVERAGE_REMOVAL'
    remove={r['object_id']:r for r in proof['instances']}
    author=json.loads((B/'authoring.json').read_text());auth={r['object_id']:r for r in author['models']}
    checks={r['object_id']:r for r in map(json.loads,(B/'compiled-checks-r2.jsonl').read_text().splitlines())}
    assert set(checks)==set(auth)-set(remove) and all(all(r['gates'].values()) for r in checks.values())
    oldwater=Path('P:/Mods/@DayZ_Baltic_HaloFixV3/Addons/baltic_water_v30.pbo')
    assert sha(oldwater)==check['old_water_sha256']==proof['water_sha256']
    _,props,old=read_pbo(oldwater);merged=dict(old)
    for folder,key in (('compile','patch_sha256'),('compile-r2','repaired_patch_sha256')):
        patch=B/folder/'out/baltic_water_v30.pbo';assert sha(patch)==check[key]
        _,pp,entries=read_pbo(patch);assert pp==props and entries['config.bin']==old['config.bin']
        merged.update({name:raw for name,raw in entries.items() if name in {r['model'] for r in checks.values()}})
    assert not ({r['model'] for r in checks.values()}&set(old))
    for row in checks.values():assert hashlib.sha256(merged[row['model']]).hexdigest()==row['compiled_sha256']
    dest=B/'water/temp/baltic_water_v30';dest.mkdir(parents=True,exist_ok=False)
    for name,raw in merged.items():
        path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    out=B/'water/packed';out.mkdir(parents=True,exist_ok=False)
    bank=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe')
    command=[str(bank)]
    for k,v in props.items():command.extend(['-property',k+'='+v])
    command.extend(['-dst',str(out),str(dest)])
    result=subprocess.run(command,capture_output=True);(B/'water/filebank.log').write_bytes(result.stdout+result.stderr)
    assert result.returncode==0
    _,packedprops,packed=read_pbo(out/'baltic_water_v30.pbo');assert packedprops==props and packed==merged
    src=B10/'halo-fix-v4/world/root/dayz_baltic_12km_dev/tb/narva_trial'
    assert sha(src/'baltic_trial.wrp')==proof['world_sha256']==author['world_sha256']
    before=read(src/'baltic_trial.wrp');records=[];removed=[]
    for obj in before['objects']:
        ident=obj['id']
        if ident in remove:
            assert hashlib.sha256(obj['bytes']).hexdigest()==remove[ident]['object_record_sha256']
            removed.append(ident);continue
        if ident not in checks:records.append(obj['bytes']);continue
        row=checks[ident];original=auth[ident]
        assert obj['name'].replace('\\','/').split('/')[-1]==row['old_model']
        assert np.array_equal(obj['matrix'],original['old_matrix'])
        matrix=obj['matrix'][:9]+row['new_position'];name=('baltic_water_v30\\'+row['model']).encode('ascii')
        if obj['raw_name'].endswith(b'\0'):name+=b'\0'
        records.append(object_record(matrix,ident,name))
    assert set(removed)==set(remove)
    stage=B/'world/root/dayz_baltic_12km_dev/tb/narva_trial'
    shutil.copytree(src,stage,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    write(stage/'baltic_trial.wrp',before['header'],before['heights'],before['materials'],records,before['terminator'])
    after=read(stage/'baltic_trial.wrp');oldid={o['id']:o for o in before['objects']};newid={o['id']:o for o in after['objects']}
    assert set(oldid)-set(newid)==set(removed) and not set(newid)-set(oldid)
    assert np.array_equal(after['heights'],before['heights']) and all(after[k]==before[k] for k in ('header','materials','terminator'))
    unchanged=[i for i in newid if i not in checks]
    assert all(newid[i]['bytes']==oldid[i]['bytes'] for i in unchanged)
    source_files={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file() and p.name!='baltic_trial.wrp'}
    assert all(sha(stage/name)==digest for name,digest in source_files.items())
    report=dict(status='VERIFIED_WATER_PACKED_DERIVED_WORLD_STAGED',water_sha256=sha(out/'baltic_water_v30.pbo'),
                world_source_sha256=sha(stage/'baltic_trial.wrp'),baseline_world_source_sha256=proof['world_sha256'],
                changed_visible_instances=len(checks),removed_instances=sorted(removed),unchanged_object_records=len(unchanged),
                objects_before=len(oldid),objects_after=len(newid),terrain_exact=True,materials_exact=True,
                bridges_and_engineering_exact=True,old_water_entries_exact=all(packed[k]==v for k,v in old.items()),
                source_files_exact=source_files,physical_max_error_m=check['max_physical_error_m'],
                limits=['World compilation, whole-domain coverage and runtime checks still required.',
                        'Navmesh copied exactly; it is not regenerated or accepted for final terrain.'])
    (B/'package.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_files_exact','removed_instances')},indent=2))

if __name__=='__main__':main()
