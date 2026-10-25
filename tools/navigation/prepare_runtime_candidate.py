"""Explicit derived0WZD for a geometry-only runtime experiment, not a TB export."""
from pathlib import Path
import argparse
import json
import shutil
import struct
import sys
import numpy as np
import rasterio
from waterway_common import ROOT, BASE_SHA, read_base, sha

sys.path.insert(0, str(ROOT/'tools/playtest'))
from verify_texture_grid_change import read


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    if args.package.exists():
        raise ValueError('Fresh package required')
    verification = json.loads((args.candidate/'verification.json').read_text())
    design = json.loads((args.candidate/'design.json').read_text())
    asc = args.candidate/'narva_navigation_v1.asc'
    if (verification['status'] != 'PASS_OFFLINE_ONLY'
            or sha(asc) != verification['candidate_sha256']
            or sha(args.candidate/'design.json') != verification['design_sha256']
            or design['source_sha256'] != BASE_SHA):
        raise ValueError('Offline gates must pass for this exact candidate')
    native = ROOT/'tb/regional_clearance_v1/baltic_regional_objects_restored_v1.wrp'
    if sha(native) != '313600cbbe77f161368133acfd9c7347a683dacadc695bc2149db6388a0552ef':
        raise ValueError('Canonical native baseline drift')
    old = read(native)
    base = read_base()
    before_heights = np.frombuffer(old['heights'],dtype='<f4').reshape(2048,2048)[::-1]
    if np.max(abs(before_heights-base)) > 1e-6:
        raise ValueError('Native baseline does not match frozen ASC')
    bridges = [o for o in old['objects'] if o['name'].endswith('bridge_metal_25.p3d')]
    ponds = [o for o in old['objects'] if o['name'].endswith('pond_50x50.p3d')]
    if len(bridges)!=1 or len(ponds)!=1 or len(old['objects'])!=2:
        raise ValueError('Unexpected baseline objects')
    with rasterio.open(asc) as ds:
        heights=ds.read(1)
    hb = heights[::-1].astype('<f4').tobytes()
    template = bridges[0]
    matrix0 = np.array(struct.unpack('<12f',bytes.fromhex(template['matrix'])))
    records=[]
    for i,obj in enumerate(design['bridge_objects']):
        matrix=matrix0.copy()
        matrix[9:] = [obj['x'], obj['engine_origin_y_candidate'],obj['z']]
        name = template['name'].encode('ascii')+b'\0'
        records.append(struct.pack('<12fII',*matrix,template['id']+i,len(name))+name)
    terminal = old['bytes'][old['objects'][-1]['end']:]
    if len(terminal)!=56:
        raise ValueError('Unexpected native sentinel')
    derived = old['bytes'][:24]+hb+old['bytes'][24+len(hb):old['objects_start']]+b''.join(records)+terminal
    args.package.mkdir(parents=True)
    wrp=args.package/'narva_navigation_derived.wrp'
    wrp.write_bytes(derived)
    reread=read(wrp)
    decoded=np.frombuffer(reread['heights'],dtype='<f4').reshape(2048,2048)[::-1]
    checks={'all_heights_equal_ASC':np.array_equal(decoded,heights),
            'header_unchanged':reread['bytes'][:24]==old['bytes'][:24],
            'all_texture_assignments_and_materials_unchanged':reread['bytes'][24+len(hb):reread['objects_start']]==old['bytes'][24+len(hb):old['objects_start']],
            'exactly_three_bridges':len(reread['objects'])==3 and all(o['name']==template['name'] for o in reread['objects'])}
    poses=[]
    for obj,target in zip(reread['objects'],design['bridge_objects']):
        matrix=np.array(struct.unpack('<12f',bytes.fromhex(obj['matrix'])))
        pose=[target['x'],target['engine_origin_y_candidate'],target['z']]
        poses.append({'id':obj['id'],'xyz':matrix[9:].tolist(),
                      'position_float32_error_m':float(np.max(abs(matrix[9:]-pose))),
                      'rotation_scale_unchanged':bool(np.array_equal(matrix[:9],matrix0[:9]))})
    checks['all_object_poses_match'] = all(p['position_float32_error_m']<=.0005 and p['rotation_scale_unchanged'] for p in poses)
    if not all(checks.values()):
        raise ValueError(checks)
    source=ROOT/'build-isolated/regional_clearance_v1/dayz_baltic_12km_dev/tb/narva_trial'
    if any(p.is_symlink() or p.is_junction() for p in source.rglob('*')):
        raise ValueError('Source package contains a reparse point')
    stage=args.package/'source/BalticTrialWorld'
    shutil.copytree(source,stage)
    shutil.copyfile(wrp,stage/'baltic_trial.wrp')
    # Bootstrap only; explicitly not valid navigation for the changed world.
    nav=ROOT/'tb/regional_clearance_v1/navmesh/baltic_regional_v1.nm'
    if sha(nav)!='0fc26281e3cf2908b9f95f937521d758808007a83f9f837e4e81a034a5b161fe':
        raise ValueError('Own bootstrap navigation drift')
    shutil.copyfile(nav,stage/'navmesh/baltic_trial.nm')
    (args.package/'tools').mkdir()
    shutil.copyfile(ROOT/'packages/baltic-playtest/tools/include.lst',args.package/'tools/include.lst')
    report={'status':'PASS_DERIVED_NATIVE_FORMAT_NOT_EDITOR_EXPORT','checks':checks,
            'baseline_wrp_sha256':sha(native),'candidate_asc_sha256':sha(asc),'derived_wrp_sha256':sha(wrp),
            'poses':poses,'materials':reread['materials'],
            'limits':['Terrain Builder import/save/reopen still pending.',
                      'Bootstrap navmesh is stale for this candidate; no AI acceptance.',
                      'Satellite water/road artwork not updated. Geometry trial only.']}
    (args.package/'derived-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
