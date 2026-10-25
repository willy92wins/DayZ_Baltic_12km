"""Structural inventory of deployed Q and installed Chernarus; never an FPS verdict.

OPRW locator adapted from package_visual_forest_ev112.compiled_arrays. It is a
heuristic, bounded by a unique runtime/source anchor, record validity, unique IDs
and the following map-info block. Native census coverage is additionally checked
against deterministic samples of an older engine survey (positions only).
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/playtest'))
from attach_navmesh import read_pbo

B = Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
Q = Path('P:/Mods/@DayZ_Baltic_EV112_VisualReviewQ/Addons')
CH = Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ/Addons/worlds_chernarusplus.pbo')
SURVEY = Path('E:/DayZ-Baltic-Build/vanilla-tricks-20261013/data/chernarus_objects.csv')
EXPECTED = {
    'narva_trial.pbo': 'f5ffc2affe67d739b51a26f723082389f41c6b94fdf160f93ba6548ae1fd8521',
    'baltic_stream_pilot.pbo': '742fcc8d076df39a8c54cb99f86c3099976219afe00bc62561794f7cc701bec7',
    'baltic_water_v30.pbo': '97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43',
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def locate(b, marker, anchor):
    assert b[:4] == b'OPRW'
    version = struct.unpack_from('<I', b, 4)[0]
    stride = {29: 60, 32: 64}[version]
    mark = re.search(marker, b, re.I).start()
    candidates = []
    for start in range(max(0, mark - 4000), mark - 3):
        count = struct.unpack_from('<I', b, start)[0]
        if not 0 < count < 200000:
            continue
        names, pos = [], start + 4
        try:
            for _ in range(count):
                end = b.index(b'\0', pos, pos + 300)
                name = b[pos:end].decode('ascii').lower()
                if not name.endswith('.p3d'):
                    raise ValueError('not a model table')
                names.append(name)
                pos = end + 1
            if start + 4 <= mark < pos and len(set(names)) == count:
                candidates.append((names, pos))
        except (ValueError, UnicodeDecodeError):
            pass
    assert len(candidates) == 1, ('unique model table', len(candidates))
    names, pos = candidates[0]
    count = len(names)
    mi = names.index(anchor['name'].lower())
    needle = struct.pack('<I', mi)
    p, hits = pos, []
    while True:
        p = b.find(needle, p)
        if p < 0:
            break
        if p + 52 <= len(b):
            xyz = np.array(struct.unpack_from('<3f', b, p + 40))
            if np.isfinite(xyz).all() and np.max(np.abs(xyz - anchor['xyz'])) < .002:
                hits.append(p - 4)
        p += 1
    assert len(hits) == 1, ('unique anchor', hits)
    dtype = np.dtype(dict(names=['id', 'mi', 'mat', 'shape'] + (['reserved'] if stride == 64 else []),
                         formats=['<u4', '<u4', ('<f4', 12), '<u4'] + (['<u4'] if stride == 64 else []),
                         offsets=[0, 4, 8, 56] + ([60] if stride == 64 else []), itemsize=stride))

    def valid(rows):
        m = rows['mat']
        with np.errstate(over='ignore', invalid='ignore'):
            lengths = np.linalg.norm(m[:, :9].reshape(-1, 3, 3), axis=2)
        ok = (rows['id'] > 0) & (rows['mi'] < count) & (rows['shape'] <= 64)
        ok &= np.isfinite(m).all(1) & (np.abs(m[:, 9:]).max(1) < 1e6)
        ok &= ((lengths > 1e-5).all(1) | (lengths == 0).all(1)) & (lengths < 100).all(1)
        if stride == 64:
            ok &= rows['reserved'] == 0
        return ok

    first = hits[0]
    while first - stride >= pos:
        n = min(65536, (first - pos) // stride)
        start = first - n * stride
        bad = np.flatnonzero(~valid(np.frombuffer(b, dtype, count=n, offset=start)))
        first = start + (int(bad[-1]) + 1) * stride if len(bad) else start
        if len(bad):
            break
    p = first
    while p + stride <= len(b):
        n = min(65536, (len(b) - p) // stride)
        bad = np.flatnonzero(~valid(np.frombuffer(b, dtype, count=n, offset=p)))
        p += (int(bad[0]) if len(bad) else n) * stride
        if len(bad):
            break
    rows = np.frombuffer(b, dtype, count=(p - first) // stride, offset=first)
    assert len(rows) and len(np.unique(rows['id'])) == len(rows)
    after = struct.unpack_from('<2I', b, p)
    assert after[0] <= 64 and after[1] in rows['id'], ('map-info boundary', after)
    return rows, names, dict(version=version, stride=stride, table=[first, p], after=list(after))


def category(name):
    if name.startswith(('dz\\plants\\', 'dz\\plants_bliss\\', 'dz\\plants_sakhal\\')):
        return 'vegetation'
    if name.startswith('baltic_stream_pilot\\'):
        return 'custom_stream'
    if name.startswith('baltic_water_v30\\'):
        return 'custom_water'
    if name.startswith('dz\\water\\'):
        return 'native_water'
    return 'other'


def inventory(rows, names, side):
    counts = np.bincount(rows['mi'], minlength=len(names))
    cats = np.array([category(n) for n in names])
    result = dict(objects=len(rows), unique_resources=int(np.count_nonzero(counts)),
                  declared_resources=len(names), square_area_km2=(side / 1000) ** 2,
                  groups={}, hotspots={})
    result['objects_per_square_km_including_sea'] = len(rows) / result['square_area_km2']
    for cat in sorted(set(cats)):
        result['groups'][cat] = dict(instances=int(counts[cats == cat].sum()),
                                    resources=int(np.count_nonzero(counts[cats == cat])))
    xyz = rows['mat'][:, 9:]
    inside = (xyz[:, 0] >= 0) & (xyz[:, 0] < side) & (xyz[:, 2] >= 0) & (xyz[:, 2] < side)
    result['outside_square'] = int((~inside).sum())
    for group in ('all', 'vegetation'):
        select = inside if group == 'all' else inside & (cats[rows['mi']] == 'vegetation')
        for cell in (128, 256, 512):
            # Only full cells; sea/empty cells included, so these are scouting
            # statistics, not matched-biome performance or land density.
            n = int(side // cell)
            xz = xyz[select][:, [0, 2]]
            indices = (xz / cell).astype(np.int64)
            indices = indices[(indices < n).all(1)]
            h = np.bincount(indices[:, 1] * n + indices[:, 0], minlength=n * n)
            order = np.argsort(-h, kind='stable')[:6]
            result['hotspots'][f'{group}_{cell}m'] = dict(
                grid_cells=n * n, partial_edge_width_m=side - n * cell,
                p50=float(np.percentile(h, 50)), p95=float(np.percentile(h, 95)), max=int(h.max()),
                top=[dict(x=float((i % n + .5) * cell), z=float((i // n + .5) * cell),
                          count=int(h[i])) for i in order])
    result['top_resources'] = [dict(model=names[i], instances=int(counts[i]))
                               for i in np.argsort(-counts, kind='stable')[:15]]
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('out', type=Path)
    a = ap.parse_args()
    assert not a.out.exists(), 'fresh evidence output required'
    result = dict(status='STATIC_INVENTORY_ONLY_RUNTIME_INCONCLUSIVE', inputs={}, worlds={})
    for name, expected in EXPECTED.items():
        p = Q / name
        digest = sha(p.read_bytes())
        assert digest == expected
        result['inputs'][name] = dict(path=str(p), sha256=digest, bytes=p.stat().st_size)
    records = list(csv.DictReader(SURVEY.open(newline='', encoding='utf-8-sig')))
    result['inputs']['old_filtered_runtime_survey'] = dict(path=str(SURVEY), sha256=sha(SURVEY.read_bytes()), rows=len(records))
    for label, pbo, side in [('Baltic_Q', Q / 'narva_trial.pbo', 12288), ('Chernarus_installed', CH, 15360)]:
        raw, props, entries = read_pbo(pbo)
        keys = [k for k in entries if k.lower().endswith('.wrp')]
        assert len(keys) == 1
        b = entries[keys[0]]
        result['inputs'][label] = dict(path=str(pbo), pbo_sha256=sha(raw), wrp_sha256=sha(b), wrp_bytes=len(b))
        if label == 'Baltic_Q':
            sys.path.insert(0, str(ROOT / 'tools/vegetation'))
            from prune_visual_forest_v31 import prefix, objects
            src = B / 'stage-visual-forest-20261024-b/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
            with src.open('rb') as f:
                prefix(f)
                ident, name, rec = next(objects(f))
            anchor = dict(name=name, xyz=struct.unpack_from('<3f', rec, 36))
            marker = rb'baltic_water_v30\\[^\x00]+\.p3d\x00'
        else:
            ref = records[0]
            anchor = dict(name=ref['shape'], xyz=[float(ref[k]) for k in ('x', 'y', 'z')])
            marker = rb'dz\\[^\x00]{1,200}\.p3d\x00'
        rows, names, reader = locate(b, marker, anchor)
        inv = inventory(rows, names, side)
        inv['reader'] = reader
        if label == 'Baltic_Q':
            receipt = json.loads((B / 'package-visual-forest-20261024-c/verification.json').read_text())
            assert result['inputs'][label]['wrp_sha256'] == receipt['wrp_sha256']
            assert len(rows) == receipt['objects']['objects']
        else:
            checks, planar, differences = [], [], []
            for i in np.linspace(0, len(records) - 1, 128, dtype=int):
                r = records[i]
                name = r['shape'].lower()
                assert name in names
                pts = rows['mat'][rows['mi'] == names.index(name), 9:]
                q = np.array([float(r[k]) for k in ('x', 'y', 'z')])
                dist, j = cKDTree(pts).query(q)
                checks.append(float(dist))
                planar.append(float(np.linalg.norm((pts[j] - q)[[0, 2]])))
                if dist >= .002:
                    differences.append(dict(index=int(i), model=name, old=q.tolist(),
                                            installed=pts[j].tolist(), distance_m=float(dist)))
            inv['older_engine_survey_spatial_check'] = dict(
                samples=128, within_2mm_3d=sum(d < .002 for d in checks), max_error_3d_m=max(checks),
                within_2mm_xz=sum(d < .002 for d in planar), max_error_xz_m=max(planar),
                three_dimensional_parity='FAIL' if differences else 'PASS', differences=differences)
            # Initial 3D parity check failed at five stone positions (Y only).
            # Retain that FAIL. XZ is a distinct census cross-check, not a relaxed
            # height acceptance. Neither old survey nor this inventory accepts Y.
            assert max(planar) < .002, 'installed world differs in XZ; investigate census before use'
        result['worlds'][label] = inv
        print(label, inv['objects'], inv['unique_resources'], flush=True)
        del rows, b, raw, entries
    result['limits'] = [
        'Heuristic OPRW object-table reader; not a complete WRP decoder. No height or navmesh decoding.',
        'Object counts and file bytes do not measure FPS, RAM residency, draw calls, LOD cost or player capacity.',
        '256/128/512m grids include sea and empty land; hotspot candidates require biome-matched client tests.',
        'WRP translations may be bounding centres rather than roots; no clearance or collision verdict.',
        'Chernarus includes urban content; Baltic remains before physical mapping. Repeat after roads/cities.',
        '128 old filtered engine controls cross-check spatial records, not independent completeness of the full inventory.',
        'Historical engine Y differs from installed WRP at 5/128 stone controls; mechanism unisolated, 3D parity FAIL retained. XZ check is separate.',
    ]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
