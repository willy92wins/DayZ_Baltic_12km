"""Probe the v10 terrain around a point: per vertex class, level, height, the inland-pass masks and the design
signed distance, to see why a body's visible water does not follow its outline.
Usage: probe_bodies_v10.py X Z [HALF]"""
import sys

import numpy as np

N = 'E:/DayZ-Baltic-Build/v30-v10'
t = np.load(f'{N}/inland/terrain_inland.npz')
m = np.load(f'{N}/inland/masks.npz')
s = np.load(f'{N}/22/sd_shape.npz')
x, z = float(sys.argv[1]), float(sys.argv[2])
half = int(sys.argv[3]) if len(sys.argv) > 3 else 5
r0, c0 = int(round((12282 - z) / 6)), int(round(x / 6))
rs, cs = slice(r0 - half, r0 + half + 1), slice(c0 - half, c0 + half + 1)
print('sd_shape keys', s.files, {k: s[k].shape for k in s.files})
print(f'centre r={r0} c={c0} x={c0 * 6} z={12282 - 6 * r0}')


def show(name, a, fmt):
    print(f'-- {name}')
    for r in range(rs.start, rs.stop):
        print(f'z={12282 - 6 * r:5d} ' + ' '.join(fmt(v) for v in a[r, cs]))


print('cols x=', ' '.join(f'{6 * c:5d}' for c in range(cs.start, cs.stop)))
show('cls', t['cls'], lambda v: f'{v:5d}')
show('level', t['level'], lambda v: f'{v:5.2f}')
show('height', t['heights'], lambda v: f'{v:5.2f}')
show('height-level (neg = under water)', t['heights'] - t['level'], lambda v: f'{v:5.2f}')
show('forced/editable/changed', (m['forced'] * 4 + m['editable'] * 2 + m['changed']).astype(int), lambda v: f'{v:5d}')
sd = s['sd']
show('sd (design signed distance, m)', sd, lambda v: f'{v:5.1f}')
