"""Restore known baseline poses after the observed millimetric TB export drift.

Never edit either input. Reject every difference except <=1.1mm in object Y.
Use the independent native verifier on the resulting artifact before building.
"""
import argparse
import json
import math
import struct
from pathlib import Path
from verify_texture_grid_change import read, sha


def restore(old, new):
    key = lambda o: (o['name'], o['id'])
    objects = {key(o): o for o in old['objects']}
    if len(objects) != 2 or len(new['objects']) != 2 or set(objects) != {key(o) for o in new['objects']}:
        raise ValueError('Expected identical two-object identity sets')
    result = bytearray(new['bytes'])
    changes = []
    for obj in new['objects']:
        baseline = objects[key(obj)]
        before = bytes.fromhex(baseline['matrix'])
        current = bytes.fromhex(obj['matrix'])
        # Translation Y is float index10 in the verified native 3x4 matrix.
        if before[:40] != current[:40] or before[44:] != current[44:]:
            raise ValueError('Object changed outside translation Y')
        old_y = struct.unpack_from('<f', before, 40)[0]
        new_y = struct.unpack_from('<f', current, 40)[0]
        if not math.isfinite(new_y) or abs(new_y-old_y) > .0011:
            raise ValueError('Unexpected vertical displacement')
        old_record = old['bytes'][baseline['start']:baseline['end']]
        new_record = new['bytes'][obj['start']:obj['end']]
        if old_record[48:] != new_record[48:]:
            raise ValueError('Object record identity changed')
        result[obj['start']:obj['end']] = old_record
        changes.append(dict(name=obj['name'], baseline_y=old_y, exported_y=new_y,
                            removed_delta_m=new_y-old_y))
    if result[:new['objects_start']] != new['bytes'][:new['objects_start']]:
        raise ValueError('Terrain/material bytes changed')
    return bytes(result), changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'candidate', 'output', 'report'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.report.exists():
        raise ValueError('Fresh outputs required')
    old, new = read(args.baseline), read(args.candidate)
    output, changes = restore(old, new)
    args.output.write_bytes(output)
    report = dict(baseline_sha256=sha(old['bytes']), raw_candidate_sha256=sha(new['bytes']),
                  normalized_sha256=sha(output), objects=changes,
                  terrain_material_bytes_unchanged=True,
                  limitation='Derived build input; raw native project still has reported Y drift.')
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
