"""Verify a native texture-grid-only change; optionally omit the diagnostic pond.

Native 0WZD layout already consumed by tools/narva/inspect_wrp.py. No mutation of
either source WRP. Geometry/object invariants are compared to the baseline,
not reconstructed from the candidate's own transformation.
"""
from pathlib import Path
import argparse, hashlib, json, struct


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(path):
    b = path.read_bytes()
    magic, tx, tz, nx, nz, cell = struct.unpack_from('<4s4If', b)
    if magic != b'0WZD' or nx != 2048 or nz != 2048 or tx * cell != 12288 or tz * cell != 12288:
        raise ValueError('Wrong native world extent or geometry grid')
    heights = b[24:24 + nx*nz*4]
    o = 24 + len(heights)
    indices = struct.unpack_from('<' + str(tx*tz) + 'H', b, o)
    o += tx*tz*2
    def u32():
        nonlocal o
        n = struct.unpack_from('<I', b, o)[0]
        o += 4
        return n
    count = u32()
    # Material indices in this native format are uint16. A finer satellite
    # creates more variants without changing the terrain geometry.
    if not 1 < count <= 65536:
        raise ValueError('Unexpected native materials count')
    materials = []
    for _ in range(count):
        names = []
        while True:
            size = u32()
            if size == 0:
                break
            if size >= 1024:
                raise ValueError('Invalid material name size')
            names.append(b[o:o+size].decode('ascii').rstrip('\0'))
            o += size
        materials.append(names)
    if min(indices) <= 0 or max(indices) >= count:
        raise ValueError('Native material index outside table')
    objects_start = o
    objects = []
    while True:
        start = o
        matrix = b[o:o+48]
        o += 48
        ident, size = u32(), u32()
        if not size:
            break
        if size >= 1024:
            raise ValueError('Invalid object name size')
        name = b[o:o+size].decode('ascii').rstrip('\0')
        o += size
        objects.append({'name':name, 'id':ident, 'matrix':matrix.hex(), 'start':start, 'end':o})
    if o != len(b):
        raise ValueError('Unparsed native bytes')
    return dict(bytes=b, heights=heights, objects=objects, texture_grid=[tx,tz],
                texture_cell=cell, materials=count, objects_start=objects_start)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--expected-cell', type=float, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--without-diagnostic-pond', type=Path)
    a = p.parse_args()
    if a.out.exists() or (a.without_diagnostic_pond and a.without_diagnostic_pond.exists()):
        raise ValueError('Fresh outputs required')
    old, new = read(a.baseline), read(a.candidate)
    key = lambda o: (o['name'].lower(), o['id'], o['matrix'])
    checks = {'all_height_bytes_identical': old['heights'] == new['heights'],
              'all_object_records_identical_ignoring_order': sorted(map(key,old['objects'])) == sorted(map(key,new['objects'])),
              'expected_texture_cell': new['texture_cell'] == a.expected_cell,
              'expected_two_original_objects': len(new['objects']) == 2}
    report = {'status':'PASS_GEOMETRY_OBJECTS_PRESERVED' if all(checks.values()) else 'FAIL',
              'checks':checks, 'baseline_sha256':sha(old['bytes']), 'candidate_sha256':sha(new['bytes']),
              'height_sha256':sha(new['heights']), 'texture_grid':new['texture_grid'],
              'texture_cell_m':new['texture_cell'], 'materials':new['materials'],
              'limit':'Native content only; compiled WRP and render still require verification.'}
    if a.without_diagnostic_pond and all(checks.values()):
        ponds = [o for o in new['objects'] if o['name'].lower() == 'dz\\water\\ponds\\pond_50x50.p3d']
        if len(ponds) != 1:
            raise ValueError('Expected exactly one diagnostic pond')
        pond = ponds[0]
        filtered = new['bytes'][:pond['start']] + new['bytes'][pond['end']:]
        if filtered[:new['objects_start']] != new['bytes'][:new['objects_start']]:
            raise ValueError('Filter changed terrain/material data')
        a.without_diagnostic_pond.parent.mkdir(parents=True, exist_ok=True)
        a.without_diagnostic_pond.write_bytes(filtered)
        report['filtered'] = {'path':str(a.without_diagnostic_pond), 'sha256':sha(filtered), 'removed_bytes':pond['end']-pond['start']}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == '__main__':
    main()
