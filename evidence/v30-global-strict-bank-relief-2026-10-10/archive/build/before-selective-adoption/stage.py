"""Stage only independently accepted EV87 heights over exact EV82-B objects."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import numpy as np

B = Path(__file__).parent
RUN = B.parent
PREV = RUN.parent / 'v30-mixed-bank-incremental-fixed-20261010'
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0, str(W / 'tools/terrain'))
from wrp0wzd import read, write


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    anchor = json.loads((B / 'build-inputs.json').read_text())
    for path, digest in anchor['inputs'].items():
        assert sha(path) == digest, f'build input changed: {path}'
    review = json.loads((RUN / 'review-independent/ev87-review.json').read_text())
    assert review['status'] == 'PASS_EV87_GLOBAL_CONSUMER'
    assert review['gates'] and all(review['gates'].values())
    terrain = RUN / 'candidate-terrain.npz'
    assert sha(terrain) == anchor['candidate_sha256']
    src = PREV / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
    dst = B / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial'
    assert sha(src / 'baltic_trial.wrp') == '3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6'
    before = read(src / 'baltic_trial.wrp')
    with np.load(PREV / 'candidate/terrain.npz') as arrays:
        assert np.array_equal(before['heights'], arrays['heights'][::-1])
    with np.load(terrain) as arrays:
        heights = arrays['heights']
    assert heights.shape == (2048,2048) and heights.dtype == np.float32
    # Native probe consumes a self-contained, byte-identical input snapshot.
    probe_inputs = B/'candidate'
    assert not probe_inputs.exists(), 'Fresh native probe inputs required'
    sources = {'terrain.npz': terrain, 'plane.npy': PREV/'candidate/plane.npy',
               'visible-field.npy': PREV/'candidate/visible-field.npy'}
    expected = {'terrain.npz': anchor['candidate_sha256'],
                'plane.npy': '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
                'visible-field.npy': 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'}
    assert all(sha(path) == expected[name] for name,path in sources.items())
    assert not dst.exists(), 'Fresh stage required'
    probe_inputs.mkdir()
    for name,path in sources.items():
        shutil.copyfile(path,probe_inputs/name)
        assert sha(probe_inputs/name) == expected[name]
    shutil.copytree(src,dst,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
    write(dst/'baltic_trial.wrp',before['header'],heights[::-1],before['materials'],
          [obj['bytes'] for obj in before['objects']],before['terminator'])
    after = read(dst/'baltic_trial.wrp')
    assert np.array_equal(after['heights'],heights[::-1])
    assert len(after['objects']) == len(before['objects']) == 18033
    assert all(before[key] == after[key] for key in ('header','materials','terminator'))
    assert [obj['bytes'] for obj in before['objects']] == [obj['bytes'] for obj in after['objects']]
    script = (PREV/'compile_native_world.ps1').read_text()
    old_root = str(PREV).replace('/','\\')
    assert script.count(old_root) == 1
    script = script.replace(old_root,str(B).replace('/','\\'))
    (B/'compile_native_world.ps1').write_text(script,encoding='utf-8')
    receipt = dict(status='STAGED_EV87_HEIGHTS_ONLY',source_wrp_sha256=sha(src/'baltic_trial.wrp'),
                   staged_wrp_sha256=sha(dst/'baltic_trial.wrp'),terrain_sha256=sha(terrain),
                   objects=18033,objects_and_materials_exact=True,
                   native_probe_inputs={name:dict(source=str(sources[name]),destination=str(probe_inputs/name),sha256=digest)
                                        for name,digest in expected.items()})
    (B/'stage.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
