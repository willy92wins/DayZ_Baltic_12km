"""One isolated terrain-underlay diagnostic; never changes production or water."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
BUILD = HERE / 'build'
WORK = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
BASE = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010')
SOURCE = BASE / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
ADDONS = Path(r'P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons')
DEST = Path(r'P:/Mods/@DayZ_Baltic_UnderlayDiagnosticV1/Addons')
STAGE = BUILD / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
PINS = {
    BASE / 'candidate/terrain.npz': 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    SOURCE / 'baltic_trial.wrp': '3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6',
    ADDONS / 'narva_trial.pbo': 'b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c',
    ADDONS / 'baltic_water_v30.pbo': '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14',
    WORK / 'tools/terrain/wrp0wzd.py': '8b85cec46ba72851a4ec829c5b0adcc88727ee852c3f699ab7a15e31b50fee2a',
    WORK / 'tools/playtest/attach_navmesh.py': '717b81469e0a799690d1586cd7a4492f079c3b2db626eec7e2815cd15896e062',
    HERE.parent / 'PLAN-v2.md': '9152a877859b58cd0c53db38b9b1bb80b55d7e43ba61c06906e159b46de0f5d6',
    HERE / 'exact-clearance.json': '2128e6c303eb48c0ddd41d00cb1b71dee69b73a590e95e27b9786b50d48df005',
}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4*1024*1024), b''): h.update(block)
    return h.hexdigest()

def check_pins():
    for path, digest in PINS.items():
        if sha(path) != digest: raise ValueError(f'Pinned input changed: {path}')

def write_json(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2); f.write('\n')

def stage():
    check_pins()
    if BUILD.exists() or DEST.parent.exists(): raise FileExistsError('Fresh diagnostic paths required')
    sys.path.insert(0, str(WORK / 'tools/terrain'))
    from wrp0wzd import read, write
    before = read(SOURCE / 'baltic_trial.wrp')
    with np.load(BASE / 'candidate/terrain.npz', allow_pickle=False) as z:
        arrays = {k:z[k].copy() for k in z.files}
    original = arrays['heights'].copy()
    if original.dtype != np.float32 or not np.array_equal(before['heights'], original[::-1]):
        raise ValueError('Baseline native WRP/NPZ mismatch')
    arrays['heights'][864:897,384:417] = (original[864:897,384:417].astype(np.float64)-6.10).astype(np.float32)
    mask = np.zeros(original.shape,dtype=bool); mask[864:897,384:417] = True
    if not np.array_equal(arrays['heights'][~mask], original[~mask]): raise ValueError('Outside patch changed')
    if np.count_nonzero(arrays['heights'] != original) != 1089: raise ValueError('Patch count mismatch')
    BUILD.mkdir()
    np.savez_compressed(BUILD / 'terrain.npz', **arrays)
    # Materials and objects remain identical. Satellite maps are retained at packaging.
    shutil.copytree(SOURCE, STAGE, ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    write(STAGE / 'baltic_trial.wrp', before['header'], arrays['heights'][::-1],
          before['materials'], [o['bytes'] for o in before['objects']], before['terminator'])
    after = read(STAGE / 'baltic_trial.wrp')
    if not np.array_equal(after['heights'], arrays['heights'][::-1]): raise ValueError('Staged heights mismatch')
    if any(before[k] != after[k] for k in ('header','materials','terminator')): raise ValueError('WRP structure changed')
    if [o['bytes'] for o in before['objects']] != [o['bytes'] for o in after['objects']]: raise ValueError('Objects changed')
    template = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/build-wide-slope/compile_native_world.ps1')
    if sha(template) != 'b7025af606d02d99cf9f8a88fa8b2990e4928874b8b8c3515cb6ddaa022f97ec': raise ValueError('Compile runner drift')
    text = template.read_text(encoding='utf-8')
    old = r"$buildRoot='E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\build-wide-slope\package'"
    if text.count(old) != 1: raise ValueError('Compile runner root assignment changed')
    runner = BUILD / 'compile_native_world.ps1'
    runner.write_text(text.replace(old, "$buildRoot='" + str(BUILD / 'package') + "'"), encoding='utf-8')
    check_pins()
    write_json(BUILD / 'stage.json', {'status':'DIAGNOSTIC_HEIGHTS_ONLY_STAGED','production_accepted':False,
        'source_pins':{str(p):d for p,d in PINS.items()},'terrain_sha256':sha(BUILD/'terrain.npz'),
        'staged_wrp_sha256':sha(STAGE/'baltic_trial.wrp'),'changed_vertices':1089,
        'objects_materials_exact':True,'compile_runner_sha256':sha(runner),'builder_sha256':sha(__file__)})
    print('DIAGNOSTIC_HEIGHTS_ONLY_STAGED', flush=True)

def package():
    check_pins()
    info = json.loads((BUILD/'stage.json').read_text())
    if info['staged_wrp_sha256'] != sha(STAGE/'baltic_trial.wrp'): raise ValueError('Staged WRP drift')
    if info['terrain_sha256'] != sha(BUILD/'terrain.npz'): raise ValueError('Terrain drift')
    sys.path.insert(0, str(WORK / 'tools/playtest'))
    from attach_navmesh import read_pbo
    _, props, base = read_pbo(ADDONS/'narva_trial.pbo')
    _, _, compiled = read_pbo(BUILD/'package/world/out/narva_trial.pbo')
    wrp = compiled['baltic_trial.wrp']
    if not wrp.startswith(b'OPRW') or wrp == base['baltic_trial.wrp']: raise ValueError('New compiled WRP required')
    expected = dict(base); expected['baltic_trial.wrp'] = wrp
    distribution = BUILD/'distribution/narva_trial'
    distribution.mkdir(parents=True,exist_ok=False)
    for name,data in expected.items():
        target=distribution/name
        if not target.resolve().is_relative_to(distribution.resolve()): raise ValueError('Unsafe archive entry')
        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(data)
    packed=BUILD/'packed'; packed.mkdir(exist_ok=False)
    cmd=[r'C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
    for key,value in props.items(): cmd += ['-property',key+'='+value]
    result=subprocess.run(cmd+['-dst',str(packed),str(distribution)],capture_output=True)
    (BUILD/'filebank.log').write_bytes(result.stdout+b'\n'+result.stderr)
    if result.returncode: raise RuntimeError('FileBank failed')
    _, after_props, after=read_pbo(packed/'narva_trial.pbo')
    if after_props != props or after != expected: raise ValueError('Packed payload mismatch')
    changed=sorted(k for k in base if base[k]!=after[k])
    if changed != ['baltic_trial.wrp']: raise ValueError('Changed non-WRP resource')
    DEST.mkdir(parents=True,exist_ok=False)
    for src in (packed/'narva_trial.pbo',ADDONS/'baltic_water_v30.pbo'):
        shutil.copyfile(src,DEST/src.name)
        if sha(src)!=sha(DEST/src.name): raise ValueError('Deploy copy mismatch')
    check_pins()
    write_json(BUILD/'deploy.json',{'status':'DIAGNOSTIC_ONLY_PACKAGED_NOT_RUNTIME_VERIFIED',
        'production_accepted':False,'mod':str(DEST.parent),'terrain_sha256':info['terrain_sha256'],
        'source_pins':{str(p):d for p,d in PINS.items()},'changed_entries':changed,
        'unchanged_entries':len(base)-1,'world_sha256':sha(DEST/'narva_trial.pbo'),
        'water_sha256':sha(DEST/'baltic_water_v30.pbo'),'compiled_wrp_sha256':hashlib.sha256(wrp).hexdigest(),
        'builder_sha256':sha(__file__),'limits':['Diagnostic only. Shore/bank floor contracts deliberately inapplicable to disposable intervention. Native heights and runtime causal test pending.']})
    print('DIAGNOSTIC_ONLY_PACKAGED',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['stage','package']); args=p.parse_args()
    if not __debug__: raise RuntimeError('Assertions must remain enabled')
    globals()[args.action]()
