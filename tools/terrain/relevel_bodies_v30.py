"""Relevel water bodies of a V30 terrain (BALTIC-017 level policy, Guillermo 04-10).

Operations, in this order:
1. River section (--river KEY:S_MAX:LEVEL): the navigable component that holds the river head, restricted to vertices
   whose nearest axis sample (tests/water_v3/navigable_samples.npz[KEY]) lies at most S_MAX from the head, goes to
   the flat LEVEL. Standing bodies go with it when they touch the section within 0.05 m of its old level at the
   contact, or when most of their vertices lie in --with-river-box at or above its minimum level.
2. Bodies (--bodies JSON [{"name", "xz": [x, z], "level"}]): the census body (cls 2/7, centimetre level,
   8-connected, >= 4 vertices) with most vertices within 18 m of xz. --census-csv checks that the labelling of the
   input reproduces a census of the same terrain (ids and vertex counts).
3. Every lowered wet vertex keeps its depth: the bed moves down by the same amount. Levels never rise.
4. Flowing water (navigable outside the section, rivers, streams) 8-connected to lowered water is capped at 0.25 m per
   6 m (x1.4142 diagonally) towards it, as the builder caps flowing water, and its bed moves down by the same amount.
5. Banks: land within --bank-radius of lowered water that stands above the natural ground (relief V30, or V29 in the
   Narva mask) goes down to max(natural, nearest water level + --bank-margin, 1.40); never up; platforms, reserves
   and beach stay.
6. Separation: where lowered water touches other water whose level differs by more than 0.30 m, the contact vertex
   of the lower standing side (else of the higher standing side) becomes land at max(natural, highest adjacent level
   + --bank-margin, 1.40). Contacts between two flowing vertices are reported, not changed.
Output <out>/terrain_relevel.npz (same keys as the input) and <out>/report.json with the gates on the result:
wet <= level - 0.10, land within 8.5 m >= nearest level + 0.05, land >= 1.40 (counts, before and after).
Usage: relevel_bodies_v30.py --terrain IN.npz --out OUTDIR [--river Luga_0:4440:3.14]
       [--with-river-box xmin,zmin,xmax,zmax:minlevel] [--bodies B.json] [--census-csv bodies.csv]
"""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v30_common import N, R, grid_xz  # noqa: E402

STRUCT8 = np.ones((3, 3), dtype=int)
CAP = 0.25
SEPARATION = 0.30
FLOWING = (3, 5, 6)
STANDING = (2, 7)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def label_bodies(cls, level):
    """Census labelling (census_perched_water_v30.find_bodies): int32 ids, 0 elsewhere."""
    standing = np.isin(cls, STANDING)
    rounded = np.round(level.astype(np.float64) * 100.0) / 100.0
    ids = np.zeros(cls.shape, np.int32)
    rows = np.flatnonzero(standing.any(axis=1))
    cols = np.flatnonzero(standing.any(axis=0))
    r0, r1, c0, c1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
    st, rd = standing[r0:r1, c0:c1], rounded[r0:r1, c0:c1]
    out = ids[r0:r1, c0:c1]
    n_id = 0
    for lv in np.unique(rd[st]):
        lab, n = ndimage.label(st & (rd == lv), structure=STRUCT8)
        if n == 0:
            continue
        counts = np.bincount(lab.ravel())
        for i in range(1, n + 1):
            if counts[i] < 4:
                continue
            n_id += 1
            out[lab == i] = n_id
    return ids


def neighbours(a, fill):
    """The eight shifted copies of a (padded with fill), with their step lengths in vertices."""
    p = np.pad(a, 1, constant_values=fill)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr or dc:
                yield p[1 + dr:1 + dr + N, 1 + dc:1 + dc + N], (1.4142 if dr and dc else 1.0)


def gates(h, cls, level, protected):
    wet = cls > 0
    lv = np.where(wet, level, np.nan)
    _, idx = ndimage.distance_transform_edt(~wet, return_indices=True)
    near_lv = lv[idx[0], idx[1]]
    dist = ndimage.distance_transform_edt(~wet) * 6.0
    inland = wet & (cls != 1)
    land = ~wet
    return {'wet_too_shallow': int((inland & (h > level - 0.10 + 1e-6)).sum()),
            'bank_below_level_0.05': int((land & (dist <= 8.5) & np.isfinite(near_lv) & (cls[idx[0], idx[1]] != 1)
                                          & (h < near_lv + 0.05 - 1e-6) & ~protected).sum()),
            'land_below_1.40': int((land & (h < 1.40 - 1e-6) & ~protected).sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--river', default=None, help='KEY:S_MAX:LEVEL')
    ap.add_argument('--with-river-box', default=None, help='xmin,zmin,xmax,zmax:minlevel')
    ap.add_argument('--bodies', type=Path, default=None)
    ap.add_argument('--census-csv', type=Path, default=None)
    ap.add_argument('--design', type=Path, default=Path(R) / 'tests' / 'water_v3')
    ap.add_argument('--relief', type=Path, default=Path(R) / 'tests' / 'relief_v30' / 'relief_v30_mix.npz')
    ap.add_argument('--v29', type=Path,
                    default=Path(R) / 'tests' / 'regional_road_network_v29' / 'baltic_road_network_v29.asc')
    ap.add_argument('--bank-radius', type=float, default=24.0)
    ap.add_argument('--bank-margin', type=float, default=0.10)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)

    t = dict(np.load(a.terrain))
    h = t['heights'].astype(np.float64)
    cls = t['cls'].copy()
    level = t['level'].astype(np.float64)
    h0, cls0, level0 = h.copy(), cls.copy(), level.copy()
    protected = t['platform'] | t['reserve'] | t['beach']
    natural = np.load(a.relief)['new'].astype(np.float64)
    with rasterio.open(a.v29) as ds:
        h29 = ds.read(1).astype(np.float64)
    natural = np.where(t['narva'], h29, natural)
    x, z = grid_xz()
    ids = label_bodies(cls, level)
    rep = {'inputs': {'terrain': str(a.terrain), 'terrain_sha256': sha(a.terrain), 'relief': str(a.relief),
                      'v29': str(a.v29), 'design': str(a.design)},
           'params': {'river': a.river, 'with_river_box': a.with_river_box, 'bodies': str(a.bodies) if a.bodies else None,
                      'bank_radius_m': a.bank_radius, 'bank_margin_m': a.bank_margin},
           'gates_before': gates(h, cls, level, protected)}
    if a.census_csv:
        counts = np.bincount(ids.ravel())
        bad = [r['id'] for r in csv.DictReader(open(a.census_csv, encoding='utf-8'))
               if int(r['id']) >= len(counts) or counts[int(r['id'])] != int(r['vertices'])]
        assert not bad, f'labelling differs from the census for ids {bad[:10]}'
        rep['census_ids_checked'] = int(len(counts) - 1)

    new_level = level.copy()
    lowered = np.zeros((N, N), bool)

    # 1. River section and the standing bodies that go with it.
    if a.river:
        key, s_max, lv_new = a.river.split(':')
        s_max, lv_new = float(s_max), float(lv_new)
        smp = np.load(a.design / 'navigable_samples.npz')[key]
        tree = cKDTree(smp[:, 1:3])
        nav = cls == 3
        lab, _ = ndimage.label(nav, structure=STRUCT8)
        hr, hc = int(round((12282 - smp[0, 2]) / 6)), int(round(smp[0, 1] / 6))
        win = lab[hr - 3:hr + 4, hc - 3:hc + 4]
        head_lab = np.bincount(win[win > 0]).argmax()
        comp = lab == head_lab
        rr, cc = np.nonzero(comp)
        _, j = tree.query(np.column_stack([x[rr, cc], z[rr, cc]]))
        keep = smp[j, 0] <= s_max
        section = np.zeros((N, N), bool)
        section[rr[keep], cc[keep]] = True
        section &= level > lv_new
        new_level[section] = lv_new
        lowered |= section
        # standing bodies touching the section within 0.05 m of its old level at the contact
        sec_old = np.where(section, level, np.nan)
        with_river = set()
        for nb, _ in neighbours(sec_old, np.nan):
            m = (ids > 0) & np.isfinite(nb) & (np.abs(level - nb) <= 0.05)
            with_river |= set(np.unique(ids[m]).tolist())
        if a.with_river_box:
            box, minlv = a.with_river_box.split(':')
            x0, z0, x1, z1 = map(float, box.split(','))
            inbox = (x >= x0) & (x <= x1) & (z >= z0) & (z <= z1)
            n_all = np.bincount(ids.ravel())
            n_in = np.bincount(ids[inbox].ravel(), minlength=len(n_all))
            for i in np.flatnonzero((n_in * 2 > n_all) & (np.arange(len(n_all)) > 0)):
                if np.nanmedian(level[ids == i]) >= float(minlv):
                    with_river.add(int(i))
        with_river.discard(0)
        for i in sorted(with_river):
            m = ids == i
            if np.nanmedian(level[m]) > lv_new:
                new_level[m] = lv_new
                lowered |= m
        rep['river'] = {'key': key, 's_max_m': s_max, 'level': lv_new, 'section_vertices': int(section.sum()),
                        'lowering_max_m': round(float(np.nanmax(level[section] - lv_new)), 3) if section.any() else 0,
                        'bodies_with_river': sorted(int(i) for i in with_river)}

    # 2. Listed bodies: [{"name": .., "xz": [x, z], "level": L}], the body with most vertices within 18 m of xz.
    if a.bodies:
        done = []
        for e in json.load(open(a.bodies, encoding='utf-8')):
            near = (np.hypot(x - e['xz'][0], z - e['xz'][1]) <= 18.0) & (ids > 0)
            assert near.any(), f'no body near {e}'
            k = int(np.bincount(ids[near]).argmax())
            m = ids == k
            old = float(np.nanmedian(level[m]))
            if old > float(e['level']):
                new_level[m] = float(e['level'])
                lowered |= m
            done.append({'name': e.get('name'), 'id': k, 'vertices': int(m.sum()), 'old_level': round(old, 2),
                         'new_level': float(e['level'])})
        rep['bodies'] = done

    # 3. Beds keep their depth.
    drop = np.where(lowered, level - new_level, 0.0)
    h[lowered] -= drop[lowered]
    level[lowered] = new_level[lowered]

    # 4. Cap connected flowing water towards the lowered water.
    capped = np.zeros((N, N), bool)
    flowing = np.isin(cls, FLOWING) & ~lowered
    for it in range(4000):
        # only water that this tool changed pulls its neighbours down; the input already met the builder's cap
        cur = np.where((lowered | capped) & np.isfinite(level), level, np.inf)
        low = np.full((N, N), np.inf)
        for nb, f in neighbours(cur, np.inf):
            low = np.minimum(low, nb + CAP * f)
        new = np.where(flowing, np.minimum(level, low), level)
        ch = flowing & (new < level - 1e-6)
        if not ch.any():
            break
        d = level[ch] - new[ch]
        h[ch] -= d
        level[ch] = new[ch]
        capped |= ch
    rep['cap'] = {'vertices': int(capped.sum()), 'iterations': it + 1,
                  'drop_max_m': round(float(np.nanmax(level0[capped] - level[capped])), 3) if capped.any() else 0}
    changed_water = lowered | capped

    # 6. Separation of lowered water from other water more than 0.30 m apart (before the banks, which read it).
    sep = np.zeros((N, N), bool)
    flagged = 0
    lvw = np.where(cls > 0, level, np.nan)
    chg = np.where(changed_water, 1, 0)
    for (nb_lv, f), (nb_chg, _), (nb_cls, _) in zip(neighbours(lvw, np.nan), neighbours(chg, 0),
                                                    neighbours(cls.astype(np.int16), 0)):
        contact = (cls > 0) & (nb_cls > 0) & np.isfinite(nb_lv) & ((chg == 1) | (nb_chg == 1)) \
            & (np.abs(lvw - nb_lv) > SEPARATION) & (cls != 1) & (nb_cls != 1)
        lower_here = contact & (lvw < nb_lv)
        higher_here = contact & (lvw > nb_lv)
        st_here = np.isin(cls, STANDING)
        st_nb = np.isin(nb_cls, STANDING)
        sep |= lower_here & st_here                       # this vertex is the lower standing side
        sep |= higher_here & st_here & ~st_nb             # the higher side is standing and the other is flowing
        flagged += int((contact & ~np.isin(cls, STANDING) & ~st_nb).sum())
    if sep.any():
        hi = np.full((N, N), -np.inf)
        for nb, _ in neighbours(np.where(cls > 0, level, -np.inf), -np.inf):
            hi = np.maximum(hi, nb)
        h[sep] = np.maximum.reduce([natural[sep], hi[sep] + a.bank_margin, np.full(sep.sum(), 1.40)])
        cls[sep] = 0
        level[sep] = np.nan
    rep['separation'] = {'vertices_to_land': int(sep.sum()), 'flowing_contacts_flagged': flagged}

    # 5. Banks down towards the natural ground.
    wet = cls > 0
    dist_low = ndimage.distance_transform_edt(~changed_water) * 6.0
    _, idx = ndimage.distance_transform_edt(~wet, return_indices=True)
    near_lv = np.where(wet, level, np.nan)[idx[0], idx[1]]
    cand = ~wet & (dist_low <= a.bank_radius) & ~protected & (h > natural + 0.02)
    target = np.maximum.reduce([natural, np.nan_to_num(near_lv, nan=-1e9) + a.bank_margin, np.full((N, N), 1.40)])
    down = cand & (h > target + 1e-6)
    rep['banks'] = {'vertices_lowered': int(down.sum()),
                    'lowering_max_m': round(float((h - target)[down].max()), 3) if down.any() else 0,
                    'lowering_median_m': round(float(np.median((h - target)[down])), 3) if down.any() else 0}
    h[down] = target[down]

    rep['totals'] = {'water_vertices_lowered': int(changed_water.sum()),
                     'level_drop_max_m': round(float(np.nanmax(level0[changed_water] - level[changed_water])), 3)
                     if changed_water.any() else 0,
                     'heights_changed': int((np.abs(h - h0) > 1e-6).sum()),
                     'cls_changed': int((cls != cls0).sum())}
    rep['gates_after'] = gates(h, cls, level, protected)
    out = dict(t)
    out['heights'] = h.astype(t['heights'].dtype)
    out['cls'] = cls
    out['level'] = level.astype(t['level'].dtype)
    out['water'] = cls > 0
    np.savez_compressed(a.out / 'terrain_relevel.npz', **out)
    rep['output_sha256'] = sha(a.out / 'terrain_relevel.npz')
    (a.out / 'report.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in rep.items() if k != 'inputs'}, indent=1))


if __name__ == '__main__':
    main()
