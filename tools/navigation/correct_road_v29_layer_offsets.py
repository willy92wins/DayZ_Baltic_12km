"""Restore the two measured V29 import shifts in the isolated editable layer.

ALB1 layout evidence: correct_outline_v33_layer_offsets.py:10-43 and its
native save/reopen consumer. This remains a bounded local format experiment;
only new native exports can accept the edit. No WRP is mutated here.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/playtest'))
from verify_texture_grid_change import read

SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ALLOWED = {16784304: 'baltic_water\\edge_03147.p3d',
           16785498: 'baltic_water\\edge_04335.p3d'}


def derive(layer, baseline, observed):
    assert layer[:4] == b'ALB1'
    old = {o['id']: o for o in baseline['objects']}
    new = {o['id']: o for o in observed['objects']}
    assert len(old) == len(new) == len(observed['objects']) == 10161
    assert old.keys() == new.keys()
    result = bytearray(layer)
    patches = []
    touched = set()
    for ident, b in old.items():
        n = new[ident]
        assert b['name'] == n['name']
        before, after = bytes.fromhex(b['matrix']), bytes.fromhex(n['matrix'])
        assert before[:40] == after[:40] and before[44:] == after[44:], 'Nonvertical pose change'
        y0, y1 = struct.unpack_from('<f', before, 40)[0], struct.unpack_from('<f', after, 40)[0]
        delta = y0-y1
        assert math.isfinite(delta)
        if not delta:
            continue
        assert ALLOWED.get(ident) == b['name'] and abs(delta) <= .062, 'Unapproved object or Y shift'
        local = ident & 0xffffff
        needle, pos, candidates = struct.pack('<I', local), 0, []
        while (pos := layer.find(needle, pos)) >= 0:
            if pos >= 36 and pos+4 <= len(layer):
                v = struct.unpack_from('<dd5fI', layer, pos-36)
                if (all(math.isfinite(x) for x in v) and 200000 <= v[0] <= 212288
                        and 0 <= v[1] <= 12288 and .5 <= v[5] <= 2 and abs(v[6]) < 200):
                    candidates.append((pos, v))
            pos += 4
        assert len(candidates) == 1, ('Ambiguous layer record', ident, len(candidates))
        pos, v = candidates[0]
        native = struct.unpack('<12f', before)
        assert abs(v[0]-200000-native[9]) <= 16 and abs(v[1]-native[11]) <= 16
        assert v[7] == local
        replacement = struct.pack('<f', v[6]+delta)
        assert math.isfinite(struct.unpack('<f', replacement)[0])
        span = set(range(pos-4, pos))
        assert not touched & span
        touched |= span
        result[pos-4:pos] = replacement
        patches.append(dict(id=ident, model=b['name'], offset=pos-4, old=v[6],
                            new=struct.unpack('<f', replacement)[0], observed_delta_y=y1-y0))
    assert {p['id'] for p in patches} == set(ALLOWED)
    changed = {i for i, (a, b) in enumerate(zip(layer, result)) if a != b}
    assert len(result) == len(layer) and changed <= touched
    return bytes(result), patches, len(changed)


def negative_controls(layer, baseline, observed):
    results = {}
    for label, ident, offset, delta in (
            ('horizontal_pose', 16784304, 36, 1.),
            ('excessive_vertical_shift', 16784304, 40, 1.),
            ('third_unapproved_object', next(i for i in (o['id'] for o in observed['objects']) if i not in ALLOWED), 40, .01)):
        bad = copy.deepcopy(observed)
        obj = next(o for o in bad['objects'] if o['id'] == ident)
        matrix = bytearray.fromhex(obj['matrix'])
        struct.pack_into('<f', matrix, offset, struct.unpack_from('<f', matrix, offset)[0]+delta)
        obj['matrix'] = matrix.hex()
        try:
            derive(layer, baseline, bad)
        except AssertionError:
            results[label] = 'REJECTED'
        else:
            raise AssertionError('Negative accepted: '+label)
    return results


def main():
    ev = ROOT / 'evidence/foundation-followup-2026-10-01/road-v29-native'
    layer = ROOT / 'tb/regional_road_network_v29/road_v29.Layers/default.tv4l'
    parent = ROOT / 'tb/regional_outline_smoothing_v33/6.wrp'
    observed = ROOT / 'tb/regional_road_network_v29/r1.wrp'
    assert SHA(layer) == 'f7b8903aa3e491c08e34e29b2b1d9e76c3fbc9c4cf65a370c2e47299976d1a5f'
    assert SHA(parent) == 'cbe04e06043a7136ce754e265d3da04a93257d6b321060fdc79bbb91afb9e492'
    assert SHA(observed) == '81d46989b15f9f1df912b2d5d9997a0cbd2911a95b9020af51bb87d3286fa721'
    original = layer.read_bytes()
    old, new = read(parent), read(observed)
    result, patches, changed = derive(original, old, new)
    controls = negative_controls(original, old, new)
    backup = ev / 'before-relative-offset-correction.tv4l'
    receipt = ev / 'relative-offset-correction.json'
    assert not backup.exists() and not receipt.exists()
    backup.write_bytes(original)
    assert backup.read_bytes() == original and layer.read_bytes() == original
    layer.write_bytes(result)
    assert layer.read_bytes() == result
    report = dict(status='TWO_LAYER_OFFSETS_CORRECTED_PENDING_NATIVE_CONSUMER', layer=str(layer),
                  parent_sha256=SHA(parent), observed_sha256=SHA(observed),
                  before_sha256=SHA(backup), after_sha256=SHA(layer), changed_bytes=changed,
                  fields=len(patches), patches=patches, negative_controls=controls,
                  limits=['Original 670 sub-micrometre V33 water residues untouched.',
                          'Actual native export, save/reopen persistence and runtime required.'])
    receipt.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
