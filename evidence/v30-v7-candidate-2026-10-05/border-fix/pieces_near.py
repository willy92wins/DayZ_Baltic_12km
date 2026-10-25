"""Water pieces of the v3b fit near a world point, and any piece whose origin or extent leaves the map."""
import json
import sys

x0, x1, z0, z1 = (float(v) for v in sys.argv[1:5])
p = json.load(open('E:/DayZ-Baltic-Build/v30-v3/fit-v3b/water/pieces.json', encoding='utf-8'))
models = {m['name']: m for m in p['model_list']}
near, outside = [], []
for q in p['poses']:
    name = q['model'].replace(chr(92), '/').split('/')[-1][:-4]
    if 'origin' in q:
        x, y, z = q['origin']
    else:
        m = q['matrix']
        x, y, z = m[9], m[10], m[11]
    if x0 <= x <= x1 and z0 <= z <= z1:
        near.append((x, z, round(y, 3), name, models.get(name, {}).get('bounds_rel'), q.get('area_m2'), 'matrix' in q))
    if not (0 <= x <= 12288 and 0 <= z <= 12288):
        outside.append((x, z, name))
print('poses near:', len(near))
for r in sorted(near):
    print('  ', r)
print('poses with origin outside the map:', len(outside), outside[:10])
print('full_48 model:', {k: v for k, v in models.get('full_48', {}).items() if k != 'sha256'})
