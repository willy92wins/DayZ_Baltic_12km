"""Compare EV82 native water-query inventories against the EV80 readback.

Run only after the EV80 baseline and EV82 candidate snapshots both pass verify_native.py. This compares
native diagnostics, not rendering or visual acceptance.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import math


EV82 = Path(__file__).parent
EV80 = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-constrained-20261010')
EV82_TERRAIN = EV82 / 'candidate/terrain.npz'
EV80_TERRAIN = EV80 / 'candidate/terrain.npz'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_snapshot(root, expected_header, expected_status):
    ref = json.loads((root / 'native-reference.json').read_text(encoding='utf-8'))
    verification = json.loads((root / 'native-verification.json').read_text(encoding='utf-8'))
    snapshot = root / 'native-snapshot.log'
    assert verification.get('status') == expected_status, f'{root.name}: verifier did not PASS'
    assert verification.get('runtime_sha256') == sha(snapshot), f'{root.name}: runtime snapshot hash mismatch'
    assert verification.get('terrain_sha256') == ref.get('terrain_sha256')
    lines = snapshot.read_text(encoding='utf-8-sig').splitlines()
    assert lines and lines[0] == f'{expected_header};BalticTrial;{ref["terrain_sha256"]}'
    records = {}
    for tag in ('A', 'Q', 'P', 'G', 'END', 'GRID_END', 'QUERY_END'):
        records[tag] = [line.split(';') for line in lines if line.startswith(tag + ';')]
    assert len(records['GRID_END']) == 1 and records['GRID_END'][0][1:4] == ['4194304', '0', 'true']
    assert len(records['END']) == 1 and records['END'][0][1] == '4194304'
    assert len(records['G']) == 2048
    assert len(records['P']) == len(ref['points']) == 1212
    assert len(records['QUERY_END']) == 1
    return ref, verification, records


def keyed(rows, tag):
    out = {}
    for row in rows:
        if tag == 'A':
            assert len(row) == 10
            key = (int(row[1]), int(row[2]))
        elif tag == 'Q':
            assert len(row) == 9
            key = (int(row[1]), int(row[2]))
        elif tag == 'P':
            assert len(row) >= 6
            key = int(row[1])
        else:
            raise ValueError(tag)
        assert key not in out, f'duplicate {tag} identity {key}'
        out[key] = row
    return out


def changed_payload(old, new, keys):
    return [dict(key=list(key) if isinstance(key, tuple) else key,
                 baseline=old[key], candidate=new[key])
            for key in sorted(keys, key=str)]


def main():
    old_ref, old_verification, old = load_snapshot(EV80, 'BALTIC_MIXEDBANK_FULLWATER_V1', 'PASS_COMPLETE_NATIVE_READBACK')
    new_ref, new_verification, new = load_snapshot(EV82, 'BALTIC_INCREMENTALBANK_FULLWATER_V1', 'PASS_COMPLETE_NATIVE_READBACK')
    assert old_ref['terrain_sha256'] == '0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'
    assert new_ref['terrain_sha256'] == 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
    assert old_verification.get('runtime_sha256') == '5e14a189d288fa4725c7343831bd973357c4b3a5ef4e8ee217f2fb14148239c3'
    assert old_verification.get('vertices') == new_verification.get('vertices') == 4194304
    assert old_verification.get('dry_vertices') == new_verification.get('dry_vertices')
    assert old_verification.get('wet_vertices') == new_verification.get('wet_vertices')

    old_a, new_a = keyed(old['A'], 'A'), keyed(new['A'], 'A')
    old_q, new_q = keyed(old['Q'], 'Q'), keyed(new['Q'], 'Q')
    old_p, new_p = keyed(old['P'], 'P'), keyed(new['P'], 'P')
    assert set(old_p) == set(new_p) == set(range(1212)), 'calibrated point identity changed'
    assert sum('expected_water' in q for q in old_ref['points']) == sum('expected_water' in q for q in new_ref['points']) == 1205

    added_a, removed_a = set(new_a) - set(old_a), set(old_a) - set(new_a)
    common_a = set(old_a) & set(new_a)
    changed_a = {key for key in common_a if old_a[key] != new_a[key]}
    added_q, removed_q = set(new_q) - set(old_q), set(old_q) - set(new_q)
    common_q = set(old_q) & set(new_q)
    changed_q = {key for key in common_q if old_q[key] != new_q[key]}

    point_ground_changes = []
    translated_water_changes = []
    for index in range(1212):
        oldrow, newrow = old_p[index], new_p[index]
        old_ground, new_ground = float(oldrow[2]), float(newrow[2])
        delta = new_ground - old_ground
        if abs(delta) > 1e-7:
            point_ground_changes.append(dict(index=index, role=old_ref['points'][index]['role'],
                                             baseline=old_ground, candidate=new_ground, delta=new_ground-old_ground))
        old_has_water = oldrow[4] == 'true'
        new_has_water = newrow[4] == 'true'
        old_water = float(oldrow[5]) if old_has_water else None
        new_water = float(newrow[5]) if new_has_water else None
        if old_has_water != new_has_water or (old_has_water and abs(old_water-new_water) > .001):
            translated_water_changes.append(dict(index=index, baseline_has_water=old_has_water,
                                                 candidate_has_water=new_has_water,
                                                 baseline_plane=old_water, candidate_plane=new_water))

    old_end, new_end = old['END'][0], new['END'][0]
    summary = {
        'status': 'COMPARED_NATIVE_INVENTORIES_NOT_RENDER_ACCEPTANCE',
        'baseline': {'terrain_sha256': old_ref['terrain_sha256'], 'runtime_sha256': old_verification['runtime_sha256']},
        'candidate': {'terrain_sha256': new_ref['terrain_sha256'], 'runtime_sha256': new_verification['runtime_sha256']},
        'coverage': {
            'vertices': {'baseline': int(old_end[1]), 'candidate': int(new_end[1])},
            'dry': {'baseline': int(old_end[5]), 'candidate': int(new_end[5])},
            'wet': {'baseline': int(old_end[6]), 'candidate': int(new_end[6])},
            'calibrated_points': {'baseline': len(old_p), 'candidate': len(new_p)},
            'translated_water_points': {'baseline': sum('expected_water' in p for p in old_ref['points']),
                                        'candidate': sum('expected_water' in p for p in new_ref['points'])}
        },
        'physical_anomalies_A': {
            'baseline': len(old_a), 'candidate': len(new_a), 'common': len(common_a),
            'added': changed_payload(new_a, new_a, added_a),
            'removed': changed_payload(old_a, old_a, removed_a),
            'changed_common_records': changed_payload(old_a, new_a, changed_a),
            'added_by_class': dict(Counter(int(new_a[k][3]) for k in added_a)),
            'removed_by_class': dict(Counter(int(old_a[k][3]) for k in removed_a))
        },
        'unflagged_scalar_Q': {
            'baseline': len(old_q), 'candidate': len(new_q), 'common': len(common_q),
            'added': changed_payload(new_q, new_q, added_q),
            'removed': changed_payload(old_q, old_q, removed_q),
            'changed_common_records': changed_payload(old_q, new_q, changed_q)
        },
        'calibrated_points_P': {
            'ground_changed_count_gt_1e-7m': len(point_ground_changes),
            'ground_changed_max_abs_m': max((abs(item['delta']) for item in point_ground_changes), default=0.0),
            'ground_changes': point_ground_changes,
            'translated_water_changes_gt_1mm': translated_water_changes
        },
        'limits': [
            'The EV80 baseline and EV82 candidate complete snapshots both passed their native readback verifier before comparison.',
            'A/Q differences are inventory deltas; they do not establish render, causality, or a visual fix.',
            'Native scalar and wave-related observations can vary with runtime phase; unchanged identity is stronger evidence than changed scalar payload.',
            'P/F identity is checked by prepare_probe.py; comparison does not infer visual exposure from native inventories.'
        ]
    }
    (EV82 / 'native-inventory-comparison.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'status': summary['status'],
        'A': {key: summary['physical_anomalies_A'][key] for key in ('baseline', 'candidate', 'common')},
        'A_added': len(added_a), 'A_removed': len(removed_a), 'A_changed_common': len(changed_a),
        'Q': {key: summary['unflagged_scalar_Q'][key] for key in ('baseline', 'candidate', 'common')},
        'Q_added': len(added_q), 'Q_removed': len(removed_q), 'Q_changed_common': len(changed_q),
        'point_ground_changed': len(point_ground_changes),
        'translated_water_changes': len(translated_water_changes)
    }, indent=2))


if __name__ == '__main__':
    main()
