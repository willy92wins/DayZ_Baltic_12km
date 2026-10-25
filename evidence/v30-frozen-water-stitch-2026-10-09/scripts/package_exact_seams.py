"""Add verified exact-centre seam pieces to the isolated global water candidate."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
import numpy as np

B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(B))
from author_global_visual import sha,read,read_pbo
from wrp0wzd import write,object_record

def main():
    base=json.loads((B/'package.json').read_text());check=json.loads((B/'seam-verification.json').read_text())
    assert check['status']=='PASS_COMPILED_EXACT_SEAMS' and not check['failures']
    water=B/'water/packed/baltic_water_v30.pbo';patch=B/'compile-seams/out/baltic_water_v30.pbo'
    assert sha(water)==base['water_sha256'] and sha(patch)==check['patch_sha256']
    _,props,old=read_pbo(water);_,pp,extra=read_pbo(patch)
    assert pp==props and old['config.bin']==extra['config.bin']
    assert (set(old)&set(extra))=={'config.bin'}
    merged=dict(old);merged.update(extra)
    dest=B/'final/water/temp/baltic_water_v30';dest.mkdir(parents=True,exist_ok=False)
    for name,raw in merged.items():
        path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    out=B/'final/water/packed';out.mkdir(parents=True,exist_ok=False)
    command=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
    for k,v in props.items():command.extend(['-property',k+'='+v])
    command.extend(['-dst',str(out),str(dest)])
    result=subprocess.run(command,capture_output=True);(B/'final/water/filebank.log').write_bytes(result.stdout+result.stderr)
    assert result.returncode==0
    _,packedprops,packed=read_pbo(out/'baltic_water_v30.pbo');assert packedprops==props and packed==merged
    src=B/'world/root/dayz_baltic_12km_dev/tb/narva_trial';assert sha(src/'baltic_trial.wrp')==base['world_source_sha256']
    before=read(src/'baltic_trial.wrp');records=[o['bytes'] for o in before['objects']];oldids={o['id'] for o in before['objects']}
    for row in check['checks']:
        assert row['object_id'] not in oldids and all(row['gates'].values())
        assert hashlib.sha256(packed[row['model']]).hexdigest()==row['compiled_sha256']
        records.append(object_record(row['matrix'],row['object_id'],('baltic_water_v30\\'+row['model']).encode('ascii')))
    stage=B/'final/world/root/dayz_baltic_12km_dev/tb/narva_trial'
    shutil.copytree(src,stage,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    write(stage/'baltic_trial.wrp',before['header'],before['heights'],before['materials'],records,before['terminator'])
    after=read(stage/'baltic_trial.wrp')
    assert [o['bytes'] for o in after['objects'][:len(before['objects'])]]==[o['bytes'] for o in before['objects']]
    assert np.array_equal(after['heights'],before['heights']) and all(before[k]==after[k] for k in ('header','materials','terminator'))
    report=dict(status='EXACT_SEAMS_PACKED_WORLD_STAGED',water_sha256=sha(out/'baltic_water_v30.pbo'),
                world_source_sha256=sha(stage/'baltic_trial.wrp'),base_package_sha256=sha(B/'package.json'),
                added_instances=len(check['checks']),objects_before=len(before['objects']),objects_after=len(after['objects']),
                existing_objects_exact=True,terrain_exact=True,materials_exact=True,old_water_entries_exact=True,
                limits=['Compiled whole-domain coverage and native runtime remain gates; not base acceptance.'])
    (B/'package-final.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
