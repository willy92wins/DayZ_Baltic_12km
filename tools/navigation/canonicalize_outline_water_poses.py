"""V33 build derivative: restore only sub-micrometre water Y to frozen V10.

Literal native exports remain unchanged and retain their strict FAIL against V10.
The two literals must themselves persist exactly across editor reopen.
"""
from pathlib import Path
import argparse, hashlib, json, math, struct, sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/playtest'))
from verify_texture_grid_change import read

BASELINE = ROOT / 'tb/regional_foundation_v10/02_reopened_v10.wrp'
BASELINE_SHA = 'cdd6838f522a5b66b729db7c6bda39b0a5a41eb256fb26804eb39f5479ef905a'
FIRST_SHA = '21144e07da7b09d05b8cd7f48f0d1700b972eb28c6503bd63b3cad98d2baf871'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
key = lambda o: (o['id'], o['name'], o['matrix'])


def restore(old, new):
    base = {o['id']: o for o in old['objects']}
    current = {o['id']: o for o in new['objects']}
    if len(base) != 10161 or len(current) != 10161 or len(new['objects']) != 10161 or base.keys() != current.keys():
        raise ValueError('Object identity set changed')
    result = bytearray(new['bytes'])
    changes = []
    for ident, obj in current.items():
        origin = base[ident]
        before, after = bytes.fromhex(origin['matrix']), bytes.fromhex(obj['matrix'])
        if origin['name'] != obj['name'] or before[:40] != after[:40] or before[44:] != after[44:]:
            raise ValueError('Nonvertical pose or model changed')
        if old['bytes'][origin['start'] + 48:origin['end']] != new['bytes'][obj['start'] + 48:obj['end']]:
            raise ValueError('Object metadata changed')
        if before == after:
            continue
        y0, y1 = struct.unpack_from('<f', before, 40)[0], struct.unpack_from('<f', after, 40)[0]
        if not obj['name'].startswith('baltic_water\\') or not math.isfinite(y1) or abs(y1 - y0) > 1e-6:
            raise ValueError('Only sub-micrometre water Y restitution is permitted')
        offset = obj['start'] + 40
        result[offset:offset + 4] = before[40:44]
        changes.append(dict(id=ident, model=obj['name'], offset=offset, old_y=y0, raw_y=y1, delta_m=y1-y0))
    if result[:new['objects_start']] != new['bytes'][:new['objects_start']]:
        raise ValueError('Terrain or materials changed')
    return bytes(result), changes


def native_pair(first, second):
    if first['bytes'][:first['objects_start']] != second['bytes'][:second['objects_start']]:
        raise ValueError('Literal height/material persistence failed')
    if sorted(map(key, first['objects'])) != sorted(map(key, second['objects'])):
        raise ValueError('Literal object persistence failed')


def verify_receipt(path):
    receipt = json.loads(path.read_text())
    assert receipt['status'] == 'PASS_EXPLICIT_DERIVED_WATER_POSES'
    assert sha(BASELINE) == BASELINE_SHA
    items = receipt['files']
    assert len(items) == 2 and Path(items[0]['raw']).resolve() != Path(items[1]['raw']).resolve()
    assert items[0]['raw_sha256'] == FIRST_SHA
    raws = []
    for item in items:
        raw, derived = Path(item['raw']), Path(item['derived'])
        assert sha(raw) == item['raw_sha256'] and sha(derived) == item['derived_sha256']
        parsed = read(raw)
        expected, changes = restore(read(BASELINE), parsed)
        assert len(changes) == 670 and changes == item['changes']
        assert expected == derived.read_bytes()
        raws.append(parsed)
    native_pair(*raws)
    native_pair(*(read(Path(i['derived'])) for i in items))
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--first', type=Path)
    p.add_argument('--reopened', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--verify-receipt', type=Path)
    a = p.parse_args()
    if a.verify_receipt:
        r = verify_receipt(a.verify_receipt)
        print(json.dumps({'status': r['status'], 'literal_persistence': True, 'files': len(r['files'])}))
        return
    assert a.first and a.reopened and a.out and not a.out.exists()
    assert a.first.resolve() != a.reopened.resolve()
    assert sha(BASELINE) == BASELINE_SHA and sha(a.first) == FIRST_SHA
    old, first, reopened = read(BASELINE), read(a.first), read(a.reopened)
    native_pair(first, reopened)
    results = [restore(old, raw) for raw in (first, reopened)]
    assert all(len(changes) == 670 for _, changes in results)
    a.out.mkdir(parents=True)
    items = []
    for name, raw, (data, changes) in zip(('first', 'reopened'), (a.first, a.reopened), results):
        dest = a.out / (name + '-derived.wrp')
        dest.write_bytes(data)
        items.append(dict(raw=str(raw.resolve()), raw_sha256=sha(raw), derived=str(dest.resolve()),
                          derived_sha256=sha(dest), changes=changes))
    report = dict(status='PASS_EXPLICIT_DERIVED_WATER_POSES', baseline_sha256=BASELINE_SHA,
                  raw_native_persistence_exact=True, files=items,
                  limit='Derived build inputs, not literal native equality against V10. Raw FAIL retained.')
    receipt = a.out / 'restoration.json'
    receipt.write_text(json.dumps(report, indent=2)+'\n')
    verify_receipt(receipt)
    print(json.dumps({'status': report['status'], 'restored_fields_per_file': 670, 'receipt': str(receipt)}))


if __name__ == '__main__':
    main()
