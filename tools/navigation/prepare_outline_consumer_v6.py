"""Bind the unchanged V5 consumer locations and criteria to accepted outline heights."""
from pathlib import Path
import argparse, copy, csv, hashlib, json
import numpy as np
import rasterio
from waterway_common import sample

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / 'evidence/regional-foundation-v1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', required=True, type=Path)
    args = parser.parse_args()
    parent = EV / 'consumer-reference-v5.json'
    assert sha(parent) == '78fd406f340efcc8b3de2218ee8b8ae14b25b36ef8bf13eb9d3c206078d21b0c'
    ref = json.loads(parent.read_text())
    old = ROOT / 'missions/BalticFoundationConsumerV5.BalticTrial'
    dest = ROOT / 'missions/BalticFoundationConsumerV6.BalticTrial'
    manifest = EV / 'consumer-reference-v6.json'
    navdest = EV / 'foundation-nav-reference-v6.json'
    assert not any(p.exists() for p in (dest, manifest, navdest))
    paths = {'water_file': old / 'water-points.csv', 'nav_file': old / 'nav-points.csv',
             'mission': old / 'init.c', 'nav_reference': EV / 'foundation-nav-reference-v5.json'}
    for key, path in paths.items():
        assert sha(path) == ref[key + '_sha256'], key
    proof = args.candidate.parent / 'independent-consumer.json'
    gate = json.loads(proof.read_text())
    assert gate['status'] == 'PASS_OFFLINE_OUTLINE_GEOMETRY'
    assert all(value is True for value in gate['checks'].values())
    assert gate['checks']['frozen_v5_runtime_samples'] is True
    assert gate['candidate_sha256'] == sha(args.candidate)
    with rasterio.open(args.candidate) as ds:
        h = ds.read(1)
    original_rows = list(csv.reader(paths['water_file'].read_text().splitlines(), delimiter=';'))
    rows = copy.deepcopy(original_rows)
    coords = np.array([[float(v) for v in r[2].split()] for r in rows], dtype='float32').astype(float)
    ground = sample(h, coords[:, 0] + 200000, coords[:, 2])
    changed = 0
    for row, bottom in zip(rows, ground):
        value = f'{bottom:.9g}'
        changed += row[3] != value
        row[3] = value
        if row[0] == 'W':
            assert float(row[4]) - bottom >= float(row[5]) - 1e-5
        else:
            assert bottom >= 1.25 - 1e-5
    assert len(rows) == 81212
    assert all(a[:3] + a[4:] == b[:3] + b[4:] for a, b in zip(original_rows, rows))
    original_nav = json.loads(paths['nav_reference'].read_text())
    nav = copy.deepcopy(original_nav)
    assert len(nav['points']) == 314 and len(nav['routes']) == 15
    for point in nav['points']:
        point['y'] = float(sample(h, point['x'] + 200000, point['z']))
    for route in nav['routes']:
        for name in ('start', 'end'):
            v = route[name]
            v[1] = float(sample(h, v[0] + 200000, v[2]))
    nav['header'] = 'BALTIC_FOUNDATION_NAV_V6'
    # Prove that no criterion or coordinate outside expected Y/header changed.
    restored = copy.deepcopy(nav)
    restored['header'] = original_nav['header']
    for point, original in zip(restored['points'], original_nav['points']):
        point['y'] = original['y']
    for route, original in zip(restored['routes'], original_nav['routes']):
        for name in ('start', 'end'):
            route[name][1] = original[name][1]
    assert restored == original_nav
    original_navrows = list(csv.reader(paths['nav_file'].read_text().splitlines(), delimiter=';'))
    navrows = copy.deepcopy(original_navrows)
    routes = {r['name']: r for r in nav['routes']}
    for row in navrows:
        if row[0] == 'Q' and row[1] != 'negative':
            route = routes[row[1]]
            row[2] = ' '.join(map(str, route['start']))
            row[3] = ' '.join(map(str, route['end']))
    for before, after in zip(original_navrows, navrows):
        assert before[:2] == after[:2]
        for left, right in zip(before[2:], after[2:]):
            a, b = list(map(float, left.split())), list(map(float, right.split()))
            assert a[0] == b[0] and a[2] == b[2]
    old_code = paths['mission'].read_text()
    code = old_code.replace('_V5', '_V6').replace('_v5.log', '_v6.log')
    assert code.replace('_V6', '_V5').replace('_v6.log', '_v5.log') == old_code
    dest.mkdir()
    for filename, content in [('water-points.csv', rows), ('nav-points.csv', navrows)]:
        with (dest / filename).open('w', newline='', encoding='utf-8') as f:
            csv.writer(f, delimiter=';', lineterminator='\n').writerows(content)
    (dest / 'init.c').write_text(code)
    navdest.write_text(json.dumps(nav, indent=2) + '\n')
    ref.update(asc_sha256=sha(args.candidate), terrain_version=args.candidate.parent.name,
               probe_version='v6', parent_reference_sha256=sha(parent),
               query_coordinates_unchanged=True, height_fields_changed=changed,
               water_file_sha256=sha(dest / 'water-points.csv'),
               nav_file_sha256=sha(dest / 'nav-points.csv'),
               nav_reference_sha256=sha(navdest), mission_sha256=sha(dest / 'init.c'),
               offline_proof_sha256=sha(proof))
    manifest.write_text(json.dumps(ref, indent=2) + '\n')
    print(json.dumps(dict(status='FROZEN_BEFORE_ENGINE', manifest_sha256=sha(manifest),
                          unchanged_samples=len(rows), height_fields_changed=changed), indent=2))


if __name__ == '__main__':
    main()
