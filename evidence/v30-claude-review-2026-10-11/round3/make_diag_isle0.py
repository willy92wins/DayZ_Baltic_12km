"""Judge diagnostic (NOT a candidate): pond-edge cand3 with the base height restored at the 54 lone dry vertices it
drowned (dry in the base vertex model, all six edge neighbours wet in the base, wet in the candidate). Every other
array is copied from the candidate. Usage: python -I -B make_diag_isle0.py"""
import sys
sys.dont_write_bytecode = True
import numpy as np
R = 'E:/DayZ-Baltic-Build/v30-shore-sdf-20261011'
b = np.load('E:/DayZ-Baltic-Build/v31-ev99-shore-lakes-20261012/terrain-ev99.npz')
c = np.load(R + '/round3/pond-edge/cand-pond-edge-3.npz')
cov = np.load(R + '/cover-level-ev98.npy')
p = np.full((2048, 2048), -np.inf); cc = np.where(np.isfinite(cov), cov, -np.inf)
for a, s in ((slice(None, -1), slice(None, -1)), (slice(None, -1), slice(1, None)), (slice(1, None), slice(None, -1)), (slice(1, None), slice(1, None))):
    p[a, s] = np.maximum(p[a, s], cc)
pondv = np.isfinite(p); vpl = np.where(pondv, p, 0.75)
H0 = b['heights']; H1 = c['heights']
wet0 = H0.astype(np.float64) < vpl; wet1 = H1.astype(np.float64) < vpl
Wp = np.pad(wet0, 1); allw = np.ones((2048, 2048), bool)
for dr, dc in ((0, 1), (1, 1), (1, 0), (0, -1), (-1, -1), (-1, 0)):
    allw &= Wp[1 + dr:1 + dr + 2048, 1 + dc:1 + dc + 2048]
lone = allw & ~wet0 & wet1 & pondv
H = H1.copy(); H[lone] = H0[lone]
arrs = {k: c[k] for k in c.files}; arrs['heights'] = H
np.savez(R + '/round3/judge/diag-pond-edge-isle0.npz', **arrs)
print('restored', int(lone.sum()))
