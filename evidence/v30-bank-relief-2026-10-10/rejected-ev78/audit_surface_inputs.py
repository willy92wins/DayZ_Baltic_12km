"""Independently compare every affected 1 m sample consumed by the saved surface layout."""
from pathlib import Path
import hashlib, json, time
import numpy as np
from scipy.ndimage import distance_transform_edt

B = Path(__file__).parent
S = B.parent / 'v30-remaining-exact-dry-support-20261009/candidate'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
t = dict(np.load(S / 'terrain.npz'))
n = dict(np.load(B / 'candidate/terrain.npz'))
h, v = t['heights'].astype(float), n['heights'].astype(float)
assert all(np.array_equal(t[k], n[k], equal_nan=True) for k in t if k != 'heights')
p = np.load(S / 'plane.npy')
assert np.array_equal(p, np.load(B / 'candidate/plane.npy'), equal_nan=True)
water = t['cls'] > 0
dist, idx = distance_transform_edt(~water, return_indices=True)
levels = t['level'][idx[0], idx[1]].astype(float)
standing = np.isin(t['cls'][idx[0], idx[1]], (2, 7))
changed = h != v
cells = changed[:-1,:-1] | changed[:-1,1:] | changed[1:,:-1] | changed[1:,1:]
uv = (np.arange(6) + .5) / 6
u, w = np.meshgrid(uv, uv)
u, w = u.ravel()[None,:], w.ravel()[None,:]
dc, dr = (u > .5).astype(int), (w > .5).astype(int)

def native(a, rr, cc):
    nw,ne,sw,se = [a[rr+dy,cc+dx][:,None] for dy,dx in ((0,0),(0,1),(1,0),(1,1))]
    return np.where(u>=w,(1-u)*nw+(u-w)*ne+w*se,(1-w)*nw+(w-u)*sw+u*se)

assert np.array_equal(np.where(np.array([.75,.25])>=np.array([.25,.75]),[9,0],[0,12]),[9,12])
counts = dict(changed_cells=int(cells.sum()), sampled_pixels=0, water_class_changes=0,
              shore_class_changes=0, wet_depth_changes=0)
examples = []
started = time.monotonic()
for r0 in range(0, 2047, 64):
    rr, cc = np.nonzero(cells[r0:r0+64]); rr += r0
    if not len(rr): continue
    old, new = native(h,rr,cc), native(v,rr,cc)
    field = p[rr,cc][:,None]
    sr,sc = rr[:,None]+dr,cc[:,None]+dc
    lvl = np.where(np.isfinite(field),field,levels[sr,sc])
    near = (dist[sr,sc]*6 <= 15) & ~standing[sr,sc]
    wet0 = (np.isfinite(field) & (old<field)) | (old<.75)
    wet1 = (np.isfinite(field) & (new<field)) | (new<.75)
    shore0,shore1 = (~wet0 & (old<lvl+.3) & near), (~wet1 & (new<lvl+.3) & near)
    counts['sampled_pixels'] += old.size
    counts['water_class_changes'] += int((wet0!=wet1).sum())
    counts['shore_class_changes'] += int((shore0!=shore1).sum())
    counts['wet_depth_changes'] += int(((wet0|wet1) & (old!=new)).sum())
    for i,j in np.argwhere(shore0!=shore1)[:max(0,10-len(examples))]:
        examples.append(dict(x=float(6*cc[i]+6*u[0,j]),z=float(12282-6*rr[i]-6*w[0,j]),
                             source_height=float(old[i,j]),candidate_height=float(new[i,j]),
                             water_level=float(lvl[i,j]),source_shore=bool(shore0[i,j]),candidate_shore=bool(shore1[i,j])))
report = dict(status='UNCHANGED_SURFACE_INPUTS' if not any(counts[k] for k in ('water_class_changes','shore_class_changes','wet_depth_changes')) else 'REGENERATE_SURFACE_REQUIRED',
              counts=counts, examples=examples, source_sha256=sha(S/'terrain.npz'),
              candidate_sha256=sha(B/'candidate/terrain.npz'), seconds=time.monotonic()-started,
              proof='All changed native cells at the 36 exact 1 m pixel centres; all other cells and metadata byte-identical. Both outermost terrain rows are unchanged, so clamped tile padding is unchanged.',
              limits=['Comparison of physical water class, shore class and water depth, not renderer appearance.'])
assert not changed[:2].any() and not changed[-2:].any() and not changed[:,:2].any() and not changed[:,-2:].any()
(B/'surface-input-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
