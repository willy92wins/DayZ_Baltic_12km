"""Create an isolated WRP import fixture; no deployment or binary project editing."""
from pathlib import Path
import hashlib
import json
import shutil
import struct

import numpy as np
from wrp0wzd import read, write

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('E:/DayZ-Baltic-Build/v30-delta-preview/world/stage/BalticTrialWorld')
OUT = Path('E:/DayZ-Baltic-Build/editor-v30-delta')
EV = ROOT / 'evidence/v30-native-editor-2026-10-02'
OLD = b'dayz_baltic_12km_dev\\tb\\narva_trial'
NEW = b'baltic_editor_v30_delta'
WRP_SHA = '3e7d298fef1e530bcfdbb94a317ea80dfa72ff276d4a0df019dcf5f845bd671f'
NM = Path('E:/DayZ-Baltic-Build/navmesh-v30-delta/baltic_trial.nm')
NM_SHA = 'eece8e5ea40c8a11856b44a90c4569c0026ca255cfef5e40db1d547e4c0eb2f7'


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def relocate_materials(w):
    b = w['materials']
    offset = w['dims'][0] * w['dims'][1] * 2
    count = struct.unpack_from('<I', b, offset)[0]
    out = bytearray(b[:offset + 4])
    offset += 4
    replacements = 0
    for _ in range(count):
        while True:
            length = struct.unpack_from('<I', b, offset)[0]
            offset += 4
            if not length:
                out.extend(struct.pack('<I', 0))
                break
            raw = b[offset:offset + length]
            offset += length
            assert raw.startswith(OLD + b'\\data\\layers\\'), raw
            new = NEW + raw[len(OLD):]
            out.extend(struct.pack('<I', len(new)))
            out.extend(new)
            replacements += 1
    assert offset == len(b) and replacements == 4775
    return bytes(out), replacements


def main():
    assert not OUT.exists() and not EV.exists(), 'Fresh destination required'
    assert sha(SOURCE / 'baltic_trial.wrp') == WRP_SHA
    assert sha(NM) == NM_SHA
    paths = list(SOURCE.rglob('*'))
    assert not any(p.is_symlink() or p.is_junction() for p in paths)
    before = {p.relative_to(SOURCE).as_posix(): sha(p) for p in paths if p.is_file()}
    source = read(SOURCE / 'baltic_trial.wrp')
    assert np.array_equal(source['heights'][::-1], np.load(
        'E:/DayZ-Baltic-Build/v30-delta-candidate/terrain_v30.npz')['heights'])
    assert len(source['objects']) == 17631
    OUT.mkdir()
    shutil.copytree(SOURCE, OUT / 'world')
    assert all(sha(OUT / 'world' / k) == v for k, v in before.items())
    changed = []
    for p in (OUT / 'world/data/layers').glob('*.rvmat'):
        data = p.read_bytes()
        assert data.count(OLD) == 2, p
        p.write_bytes(data.replace(OLD, NEW))
        assert p.read_bytes().replace(NEW, OLD) == data
        changed.append(p.relative_to(OUT / 'world').as_posix())
    materials, material_refs = relocate_materials(source)
    wrp = OUT / 'world/baltic_trial.wrp'
    write(wrp, source['header'], source['heights'], materials,
          [o['bytes'] for o in source['objects']], source['terminator'])
    back = read(wrp)
    assert back['header'] == source['header']
    assert np.array_equal(back['heights'], source['heights'])
    assert [o['bytes'] for o in back['objects']] == [o['bytes'] for o in source['objects']]
    assert back['materials'] == materials
    shutil.copyfile(NM, OUT / 'world/navmesh/baltic_trial.nm')
    assert sha(OUT / 'world/navmesh/baltic_trial.nm') == NM_SHA
    assert all(sha(SOURCE / k) == v for k, v in before.items()), 'Source changed'
    EV.mkdir()
    report = dict(status='PREPARED_NOT_IMPORTED', source=str(SOURCE), output=str(OUT),
        source_wrp_sha256=WRP_SHA, import_wrp_sha256=sha(wrp),
        old_material_prefix=OLD.decode(), editor_material_prefix=NEW.decode(),
        relocated_materials=len(changed), relocated_wrp_material_references=material_refs,
        heights_and_object_records_exact=True, objects=17631, source_files=len(before),
        source_hashes=before, navmesh_sha256=NM_SHA,
        mounts_needed={str(Path('P:/') / NEW.decode()): str(OUT / 'world'),
            'P:/baltic_water_v30': 'E:/DayZ-Baltic-Build/v30-preview6/water/source/baltic_water_v30'},
        limits=['Native import/export and persistence still untested.',
                'config.cpp and prefix retain the source build contract; this editor fixture is not a build/deployment source.'])
    (EV / 'prepare.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'source_hashes'}))


if __name__ == '__main__':
    main()
