"""Inventory ALL three shared-edge families of the native NW-SE terrain mesh.

Read-only diagnosis, not an aesthetic acceptance gate. Counts dihedral angles
between adjacent triangles, including inter-cell edges; a planar ramp is zero.
Dry means every triangle corner is above sea 0.8 and its visual pond field.
Protection domains overlap deliberately. Output pins terrain and footprint.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def normals(H, step=6.0):
    if np.asarray(H).ndim!=2 or min(H.shape)<2 or not np.isfinite(H).all() or not np.isfinite(step) or step<=0:
        raise ValueError('finite 2D heightmap and positive step required')
    nw, ne, sw, se = H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]
    one = np.ones_like(nw)
    A = np.stack((-(ne-nw)/step, one, (se-ne)/step), -1)
    B = np.stack((-(se-sw)/step, one, (sw-nw)/step), -1)
    return A / np.linalg.norm(A, axis=-1)[..., None], B / np.linalg.norm(B, axis=-1)[..., None]


def tri_any(m):
    common = m[:-1, :-1] | m[1:, 1:]
    return common | m[:-1, 1:], common | m[1:, :-1]


def tri_dry(H, plane, field):
    # Float64 explicitly, matching the visual-field consumer, not cls/water flags.
    corner = np.stack((H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]), -1)
    visible = np.where(np.isfinite(plane)[..., None], field, -np.inf)
    dry = (corner >= 0.8) & (corner >= visible)
    return dry[..., [0, 1, 3]].all(-1), dry[..., [0, 2, 3]].all(-1)


def families(A, B):
    # A east edge meets B in the next column; B south edge meets A in next row.
    return {'diagonal': (A, B), 'east': (A[:, :-1], B[:, 1:]),
            'south': (B[:-1, :], A[1:, :])}


def angles(H):
    return {key: np.degrees(np.arccos(np.clip((a*b).sum(-1), -1, 1)))
            for key, (a, b) in families(*normals(H)).items()}


def pair_union(a, b):
    return {key: x | y for key, (x, y) in families(a, b).items()}


def pair_intersection(a, b):
    return {key: x & y for key, (x, y) in families(a, b).items()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('terrain'); p.add_argument('footprint'); p.add_argument('out')
    args = p.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=False)
    z = np.load(args.terrain); H = z['heights'].astype(np.float64)
    fp = np.load(args.footprint)
    assert H.shape == (2048, 2048)
    da, db = tri_dry(H, fp['plane'], fp['field'])
    dry = pair_intersection(da, db)
    zero = np.zeros_like(H, bool)
    domains = {n: z[n] if n in z.files else zero for n in
               ('reserve', 'platform', 'narva', 'v31_dam', 'v31_kit', 'v31_bridge_cut',
                'v31_bridge_fill', 'v31_shore_ramp', 'v31_causeway')}
    domains['kit_guard_12m'] = binary_dilation(domains['v31_kit'], iterations=2)
    domains['bridge_guard_18m'] = binary_dilation(domains['v31_bridge_cut'] | domains['v31_bridge_fill'], iterations=3)
    domain_edges = {name: pair_union(*tri_any(mask)) for name, mask in domains.items()}
    all_angles = angles(H)
    counts, rows = {}, []
    for key, a in all_angles.items():
        valid = dry[key]
        vals = a[valid]
        counts[key] = dict(dry_edges=int(valid.sum()), max_deg=float(vals.max()),
                           p50_p90_p99_deg=np.percentile(vals, [50, 90, 99]).tolist(),
                           above_deg={str(t): int((vals > t).sum()) for t in (5, 10, 20, 30, 45)},
                           domains_over_20={n: int((valid & (a > 20) & d[key]).sum()) for n, d in domain_edges.items()})
        for r, c in np.argwhere(valid & (a > 20)):
            x = 6*c + (6 if key == 'east' else 3)
            zz = 12282 - 6*r - (6 if key == 'south' else 3)
            tags = '|'.join(n for n, d in domain_edges.items() if d[key][r,c])
            rows.append(dict(edge=key, row=int(r), col=int(c), x=int(x), z=int(zz),
                             angle_deg=float(a[r,c]), domains=tags or 'other'))
    rows.sort(key=lambda d: -d['angle_deg'])
    with open(out/'creases-over-20.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['edge','row','col','x','z','angle_deg','domains'])
        w.writeheader(); w.writerows(rows)
    report = dict(schema='baltic-creases-v1', terrain=str(Path(args.terrain).resolve()),
                  terrain_sha256=sha(args.terrain), footprint_sha256=sha(args.footprint),
                  families=counts, total_edges_over_20=len(rows), worst=rows[:20],
                  limitations=['20 degrees is a descriptive bin, not visual acceptance.',
                               'Domains overlap; counts cannot be summed across domains.',
                               'Dry-only excludes water-crossing triangles, which require shoreline review.',
                               'Other is not permission to edit: records and 015-45 need extra guards.'])
    (out/'census.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('worst','limitations')}, indent=2))


if __name__ == '__main__':
    main()
