"""Stage only a real EV93 independently-PASSed height candidate over EV82 B.

Preparation only. Running this script performs offline WRP staging, but is not
part of the current task and is intentionally not invoked here.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np

from ev93_build_common import (BASE_SOURCE_WRP_SHA, BASE_TERRAIN_SHA, BASE_VISIBLE_FIELD_SHA,
    BASE_WATER_PLANE_SHA, EV82, EV87_BUILD, G, W, acceptance_args, add_acceptance_manifest,
    load_accepted_inputs, sha, verify_baseline_pbos, verify_baseline_reference_inputs)

B = Path(__file__).parent
sys.path.insert(0, str(W / 'tools/terrain'))
from wrp0wzd import read, write  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    acceptance_args(parser)
    args = parser.parse_args()
    accepted = load_accepted_inputs(args.authoring_receipt, args.consumer_report)
    verify_baseline_pbos()
    verify_baseline_reference_inputs()
    source = EV82 / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
    destination = B / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
    source_wrp = source / 'baltic_trial.wrp'
    assert sha(source_wrp) == BASE_SOURCE_WRP_SHA
    assert sha(EV82 / 'candidate/terrain.npz') == BASE_TERRAIN_SHA
    assert sha(EV82 / 'candidate/plane.npy') == BASE_WATER_PLANE_SHA
    assert sha(EV82 / 'candidate/visible-field.npy') == BASE_VISIBLE_FIELD_SHA
    baseline = read(source_wrp)
    with np.load(EV82 / 'candidate/terrain.npz', allow_pickle=False) as b:
        assert np.array_equal(baseline['heights'], b['heights'][::-1])
        baseline_arrays = {name: b[name].copy() for name in b.files}
    with np.load(accepted['candidate_path'], allow_pickle=False) as candidate:
        assert set(candidate.files) == set(baseline_arrays), 'EV93 candidate array schema changed from B'
        heights = candidate['heights'].copy()
        for name, before in baseline_arrays.items():
            if name != 'heights':
                assert np.array_equal(candidate[name], before), f'EV93 changed B metadata array: {name}'
    assert heights.shape == (2048, 2048) and heights.dtype == np.float32

    # Fresh output only; the exact B P/F fields are copied byte-for-byte.
    probe_inputs = B / 'candidate'
    if probe_inputs.exists() or destination.exists():
        raise FileExistsError('EV93 stage outputs must be fresh; refusing overwrite')
    sources = {
        'terrain.npz': accepted['candidate_path'],
        'plane.npy': EV82 / 'candidate/plane.npy',
        'visible-field.npy': EV82 / 'candidate/visible-field.npy',
    }
    expected = {
        'terrain.npz': accepted['candidate_sha256'],
        'plane.npy': BASE_WATER_PLANE_SHA,
        'visible-field.npy': BASE_VISIBLE_FIELD_SHA,
    }
    probe_inputs.mkdir(parents=True)
    for name, path in sources.items():
        if sha(path) != expected[name]:
            raise ValueError(f'input identity mismatch: {path}')
        shutil.copyfile(path, probe_inputs / name)
        assert sha(probe_inputs / name) == expected[name]

    if not destination.parent.exists():
        destination.parent.mkdir(parents=True)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    write(destination / 'baltic_trial.wrp', baseline['header'], heights[::-1], baseline['materials'],
          [obj['bytes'] for obj in baseline['objects']], baseline['terminator'])
    after = read(destination / 'baltic_trial.wrp')
    assert np.array_equal(after['heights'], heights[::-1])
    assert len(after['objects']) == len(baseline['objects']) == 18033
    assert all(baseline[key] == after[key] for key in ('header', 'materials', 'terminator'))
    assert [obj['bytes'] for obj in baseline['objects']] == [obj['bytes'] for obj in after['objects']]

    compile_script = (EV82 / 'compile_native_world.ps1').read_text(encoding='utf-8')
    old_root = str(EV82).replace('/', '\\')
    assert compile_script.count(old_root) == 1
    compile_script = compile_script.replace(old_root, str(B).replace('/', '\\'))
    (B / 'compile_native_world.ps1').write_text(compile_script, encoding='utf-8')
    receipt = add_acceptance_manifest({
        'status': 'STAGED_EV93_HEIGHTS_ONLY',
        'source_wrp_sha256': sha(source_wrp),
        'staged_wrp_sha256': sha(destination / 'baltic_trial.wrp'),
        'terrain_sha256': accepted['candidate_sha256'],
        'objects': 18033,
        'objects_and_materials_exact': True,
        'native_probe_inputs': {name: {'source': str(sources[name]),
            'destination': str(probe_inputs / name), 'sha256': digest} for name, digest in expected.items()},
    }, accepted)
    (B / 'stage.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
