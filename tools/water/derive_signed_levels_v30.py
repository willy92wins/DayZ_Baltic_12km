"""Level list for relevel_bodies_v30.py --bodies, derived on a terrain by the rule of the signed list
(evidence/v30-v3-candidate-2026-10-04/decisions/levels-signed.json, Guillermo 04-10), so a rebuilt chain keeps the
same policy on its own bodies.

The rule, on classify_perched_water_v30.py run on the terrain the list is for (the input of relevel_bodies_v30.py):
- lower_to_ring bodies go to max(proposed_level_m, --floor); review bodies (perched 0.3-0.5 m) to
  max(round(min(level, ring p25 - 0.05), 2), --floor), the same criterion; only when that is below their level;
- a body that has a signed level keeps it while the rule lands within --keep-signed-within of it (the ring measured on
  another terrain of the chain moves the rule by a few cm); beyond that the rule's level is taken and reported;
- bodies whose representative vertex lies in --river-box are left to the river section (relevel --with-river-box);
- connected bodies (lower_with_river) and moats carry the level signed for the same body: those were decided by hand
  (the river level at the contact; the moats at 2.45 m). A connected body without a signed level keeps its level;
- a body that has a signed level but that the classification no longer lowers (keep: perched under 0.30 m now, the
  ring having moved a few cm with a reshaped outline) keeps the signed level too, when it lies below its level: the
  signature is per body, not per classification;
- a signed entry belongs to the census body with most vertices within 18 m of its xz, as relevel_bodies_v30.py
  matches it.
Outputs: --out-list (the list, same format as the signed one) and --out-report (every signed entry: same level,
changed level, or body gone; every new entry; counts).
Usage: derive_signed_levels_v30.py --terrain T.npz --classification C.json --signed S.json --out-list L.json
       --out-report R.json [--river-box 10150,3700,10700,4600] [--floor 1.35] [--keep-signed-within 0.05]
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'terrain'))
from v30_common import grid_xz  # noqa: E402
from relevel_bodies_v30 import label_bodies  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--classification', type=Path, required=True)
    ap.add_argument('--signed', type=Path, required=True)
    ap.add_argument('--out-list', type=Path, required=True)
    ap.add_argument('--out-report', type=Path, required=True)
    ap.add_argument('--river-box', default='10150,3700,10700,4600')
    ap.add_argument('--floor', type=float, default=1.35)
    ap.add_argument('--keep-signed-within', type=float, default=0.05)
    a = ap.parse_args()
    for p in (a.out_list, a.out_report):
        assert not p.exists(), f'{p} exists'

    t = np.load(a.terrain)
    ids = label_bodies(t['cls'], t['level'])
    x, z = grid_xz()
    doc = json.load(open(a.classification, encoding='utf-8'))
    assert doc['inputs']['terrain']['sha256'] == sha(a.terrain), 'classification of another terrain'
    bodies = {b['id']: b for b in doc['bodies']}
    for b in bodies.values():
        r, c = int(round((12282 - b['rep_xz'][1]) / 6)), int(round(b['rep_xz'][0] / 6))
        assert ids[r, c] == b['id'], ('labelling differs from the classification', b['id'])

    def match(xz):
        near = (np.hypot(x - xz[0], z - xz[1]) <= 18.0) & (ids > 0)
        return int(np.bincount(ids[near]).argmax()) if near.any() else None

    signed = json.load(open(a.signed, encoding='utf-8'))
    prior = {}
    report = {'inputs': {str(p): sha(p) for p in (a.terrain, a.classification, a.signed, Path(__file__))},
              'params': {'river_box': a.river_box, 'floor': a.floor, 'keep_signed_within': a.keep_signed_within},
              'signed': [], 'new': []}
    for e in signed:
        k = match(e['xz'])
        if k is not None:
            assert k not in prior, ('two signed entries on one body', k)
            prior[k] = e

    bx0, bz0, bx1, bz1 = (float(v) for v in a.river_box.split(','))
    out = []
    for k in sorted(bodies):
        b = bodies[k]
        sx, sz = b['rep_xz']
        in_box = bx0 <= sx <= bx1 and bz0 <= sz <= bz1
        e = prior.get(k)
        level, basis, target = None, None, None
        if b['action'] in ('lower_to_ring', 'review') and not in_box:
            prop = b['proposed_level_m'] if b['action'] == 'lower_to_ring' else \
                round(min(b['level_m'], b['ring_p25_m'] - 0.05), 2)
            target = round(max(prop, a.floor), 2)
            if target < b['level_m'] - 0.005:
                level, basis = target, 'rule'
                if e is not None and abs(target - float(e['level'])) <= a.keep_signed_within + 1e-9:
                    level, basis = float(e['level']), 'signed'
        elif b['action'] in ('lower_with_river', 'exception_owner_decision') and e is not None:
            level, basis = float(e['level']), 'signed'
        elif e is not None and not in_box and float(e['level']) < b['level_m'] - 0.005:
            level, basis = float(e['level']), 'signed'
        if level is None:
            continue
        name = {'lower_to_ring': 'lower_to_ring', 'review': 'review', 'lower_with_river': 'connected',
                'exception_owner_decision': 'moat'}.get(b['action'], 'signed') + f'_{k}'
        entry = {'name': name, 'xz': list(e['xz']) if basis == 'signed' else list(b['rep_xz']), 'level': level,
                 'id': k, 'level_before': b['level_m'], 'basis': basis, 'rule_level': target}
        out.append(entry)
        if e is None:
            report['new'].append({**entry, 'category': b['category'], 'action': b['action'], 'vertices': b['vertices']})
    by_body = {o['id']: o for o in out}
    for e in signed:
        k = match(e['xz'])
        o = by_body.get(k) if k is not None else None
        row = {'name': e['name'], 'xz': e['xz'], 'signed_level': e['level'], 'body': k}
        if k is None:
            row['status'] = 'gone'
        elif o is None:
            b = bodies[k]
            row.update(status='not_lowered', level_now=b['level_m'], category=b['category'], action=b['action'])
        else:
            row.update(status='same' if abs(o['level'] - e['level']) < 0.005 else 'changed', level=o['level'],
                       level_before=o['level_before'], basis=o['basis'], rule_level=o['rule_level'])
        report['signed'].append(row)
    st = [r['status'] for r in report['signed']]
    report['counts'] = {'list': len(out), 'signed': len(signed), **{s: st.count(s) for s in sorted(set(st))},
                        'new': len(report['new'])}
    a.out_list.write_text(json.dumps([{k: v for k, v in o.items() if k in ('name', 'xz', 'level')} | {'id': o['id']}
                                      for o in out], indent=1) + '\n', encoding='utf-8')
    a.out_report.write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(report['counts']))


if __name__ == '__main__':
    main()
