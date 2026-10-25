"""Package EV87 over hash-verified EV82-B; publish to a fresh preview only."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys

B = Path(__file__).parent
RUN = B.parent
WORK = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
BASE = Path('P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons')
TARGET = Path('P:/Mods/@DayZ_Baltic_StrictBankPreviewV1/Addons')
sys.path.insert(0, str(WORK / 'tools/playtest'))
from attach_navmesh import read_pbo


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blob_sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    anchor = json.loads((B/'build-inputs.json').read_text())
    for path,digest in anchor['inputs'].items():
        assert sha(path) == digest, f'build input changed: {path}'
    review = json.loads((RUN/'selective/selective-review.json').read_text())
    assert review['status'] == 'PASS_INCREMENTAL_NONREGRESSION' and review['gates'] and all(review['gates'].values())
    assert review['global_representation_status']=='FAIL_WITH_INHERITED_OPEN'
    assert review['information']['global_contract_status']=='FAIL_WITH_INHERITED_OPEN' and review['information']['inherited_open']
    assert sha(RUN/'selective/candidate-terrain.npz') == anchor['candidate_sha256']
    reference = json.loads((B/'reference-inputs.json').read_text())
    surface = json.loads((B/'surface-verification.json').read_text())
    stage = json.loads((B/'stage.json').read_text())
    assert reference['status'] == 'PASS_EV82_COMPOSITE_REFERENCE'
    assert surface['status'] == 'PASS_EV87_AFFECTED_SURFACE' and surface['gates'] and all(surface['gates'].values())
    assert surface['terrain_sha256'] == stage['terrain_sha256'] == anchor['candidate_sha256']
    staged = B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    assert sha(staged) == stage['staged_wrp_sha256'] and stage['objects_and_materials_exact']
    assert sha(BASE/'narva_trial.pbo') == reference['world_sha256']
    assert sha(BASE/'baltic_water_v30.pbo') == reference['water_sha256']
    _,properties,entries = read_pbo(BASE/'narva_trial.pbo')
    assert len(entries) == reference['entries'] == 6827
    assert blob_sha(entries['baltic_trial.wrp']) == reference['compiled_wrp_sha256']
    for item in reference['textures'].values():
        assert sha(item['png']) == item['png_sha256']
        assert blob_sha(entries[item['pbo_entry']]) == item['paa_sha256']
    _,_,compiled = read_pbo(B/'package/world/out/narva_trial.pbo')
    wrp = compiled['baltic_trial.wrp']
    assert wrp.startswith(b'OPRW') and wrp != entries['baltic_trial.wrp']
    replacement = {'baltic_trial.wrp':wrp}
    for tile in surface['files']:
        a,b = tile['tile']
        for kind,suffix in [('s','lco'),('m','lca')]:
            stem = f'{kind}_{a:03d}_{b:03d}_{suffix}'
            path = B/'surface/layers'/(stem+'.paa')
            assert sha(path) == tile['files'][kind]['paa_sha256']
            replacement[reference['textures'][stem]['pbo_entry']] = path.read_bytes()
    assert len(replacement) == 1+2*len(surface['tiles'])
    destination = B/'distribution/narva_trial'
    destination.mkdir(parents=True,exist_ok=False)
    for name,data in entries.items():
        path = destination/name
        assert path.resolve().is_relative_to(destination.resolve()), 'Unsafe PBO entry path'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(replacement.get(name,data))
    out = B/'packed'
    out.mkdir(exist_ok=False)
    command = ['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
    for key,value in properties.items():
        command += ['-property',key+'='+value]
    done = subprocess.run(command+['-dst',str(out),str(destination)],capture_output=True,text=True)
    (B/'filebank.log').write_text(done.stdout+'\n'+done.stderr)
    assert done.returncode == 0
    pbo = out/'narva_trial.pbo'
    _,after_properties,after = read_pbo(pbo)
    assert properties == after_properties and entries.keys() == after.keys()
    assert all(after[key] == replacement.get(key,entries[key]) for key in entries)
    changed = sorted(key for key in entries if entries[key] != after[key])
    textures = [key for key in changed if key != 'baltic_trial.wrp']
    assert all(re.search(r'(?:^|/)[sm]_\d{3}_\d{3}_lc[oa]\.paa$',key,re.I) for key in textures)
    TARGET.mkdir(parents=True,exist_ok=False)
    for path in [pbo,BASE/'baltic_water_v30.pbo']:
        shutil.copyfile(path,TARGET/path.name)
        assert sha(path) == sha(TARGET/path.name)
    receipt = dict(status='DEPLOYED_EV87_PREVIEW_NATIVE_READBACK_PENDING',mod=str(TARGET.parent),
                   files={path.name:sha(path) for path in [pbo,BASE/'baltic_water_v30.pbo']},
                   terrain_sha256=sha(RUN/'selective/candidate-terrain.npz'),compiled_wrp_sha256=blob_sha(wrp),
                   baseline_world_sha256=reference['world_sha256'],changed_entries=changed,
                   changed_texture_entries=textures,unchanged_entries=len(entries)-len(changed),total_entries=len(entries),
                   surface_selected_tiles=len(surface['tiles']),all_expected_entries_exact=True,water_pbo_exact=True,
                   baseline_texture_identities_verified=2048,baseline_png_identities_verified=2048,
                   limits=['Native height readback pending. No visual/render/navigation acceptance. Existing navmesh retained until geometry freeze.'])
    (B/'deploy.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in receipt.items() if key not in ('changed_entries','changed_texture_entries')}))


if __name__ == '__main__':
    main()
