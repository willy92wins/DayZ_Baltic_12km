"""How the signed level list (levels-signed.json) follows from the v2 classification: which bodies were selected,
by category and action, and which levels equal max(round(ring_p25 - 0.05, 2), 1.35)."""
import collections
import json
import sys

CLS = sys.argv[1] if len(sys.argv) > 1 else (r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev'
                                             r'\evidence\v30-v3-candidate-2026-10-04\classification\classification.json')
SIGNED = 'E:/DayZ-Baltic-Build/v30-v3/bodies-v3b.json'

bodies = json.load(open(CLS, encoding='utf-8'))['bodies']
signed = json.load(open(SIGNED, encoding='utf-8'))
by_rep = {tuple(b['rep_xz']): b for b in bodies}


def rule(b):
    t = max(round(b['ring_p25_m'] - 0.05, 2), 1.35)
    if b['action'] == 'lower_with_river' and b['contact_flowing_level_max'] is not None:
        t = max(t, round(b['contact_flowing_level_max'], 2))
    return t


sel = collections.Counter()
rows = []
for e in signed:
    b = by_rep.get(tuple(e['xz']))
    if b is None:
        rows.append((e['name'], None, e['level'], None, 'no rep_xz match'))
        continue
    sel[(b['category'], b['action'])] += 1
    r = rule(b)
    rows.append((e['name'], b['id'], e['level'], r, '' if abs(r - e['level']) < 0.005 else 'DIFF'))
print('selected:', dict(sel))
print('rule matches:', sum(1 for r in rows if r[4] == ''), 'of', len(rows))
for r in rows:
    if r[4]:
        b = by_rep.get(tuple([e for e in signed if e['name'] == r[0]][0]['xz']))
        extra = {k: b[k] for k in ('level_m', 'ring_p10_m', 'ring_p25_m', 'ring_median_m', 'category', 'action',
                                    'contact_flowing_level_max', 'proposed_level_m')} if b else {}
        print('  ', r, extra)
# candidates the rule would add: bodies of the selectable actions that are not in the list and would go down
listed = {tuple(e['xz']) for e in signed}
for b in bodies:
    if b['action'] in ('lower_to_ring', 'review', 'lower_with_river') and tuple(b['rep_xz']) not in listed:
        print('  not listed', b['id'], b['category'], b['action'], 'level', b['level_m'], 'rule', rule(b),
              'p25', b['ring_p25_m'], 'flow', b['contact_flowing_level_max'])
