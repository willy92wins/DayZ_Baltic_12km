"""Vanilla Chernarus ponds from the water survey log: cluster pond pieces (within 80 m) and list the biggest and lowest."""
import collections
import sys

import numpy as np
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

LOG = sys.argv[1]
rows = []
for line in open(LOG, encoding='utf-8').read().splitlines():
    f = line.split(';')
    if f[0] != 'O' or len(f) < 4:
        continue
    model = f[2].lower()
    name = model.split(chr(92))[-1]
    if 'pond' not in name and not name.startswith('lake'):
        continue
    x, y, z = [float(v) for v in f[3].strip('<> ').split(',')]
    rows.append((name, x, y, z))
print('pond pieces', len(rows), collections.Counter(r[0] for r in rows).most_common(8))
P = np.array([[r[1], r[3]] for r in rows])
Y = np.array([r[2] for r in rows])
pairs = cKDTree(P).query_pairs(80.0, output_type='ndarray')
import scipy.sparse as sp
g = sp.coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(P), len(P)))
n, lab = connected_components(g, directed=False)
cl = []
for k in range(n):
    m = lab == k
    cl.append((int(m.sum()), P[m, 0].mean(), P[m, 1].mean(), float(np.median(Y[m])), P[m, 0].min(), P[m, 0].max(),
               P[m, 1].min(), P[m, 1].max()))
cl.sort(key=lambda c: -c[0])
print('clusters', n)
for c in cl[:15]:
    print('%3d pieces centre (%6.0f,%6.0f) level %6.2f  x %6.0f-%6.0f z %6.0f-%6.0f' % c)
low = [c for c in cl if c[3] < 6.0]
print('lowest big ones:')
for c in sorted(low, key=lambda c: -c[0])[:6]:
    print('%3d pieces centre (%6.0f,%6.0f) level %6.2f  x %6.0f-%6.0f z %6.0f-%6.0f' % c)
