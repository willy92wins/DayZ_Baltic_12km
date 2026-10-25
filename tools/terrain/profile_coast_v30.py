"""Coast profile for the sea and the delta, and no flats at the land floor (BALTIC-007, BALTIC-016).

The DayZ sea is a global swell, MaxTide/2 + MaxWave*sin(2*pi*t/12.5 s): 0.75 +- 0.10 m with the world config of 04-10
(tools/terrain/derive_world_v30.py). Its waterline is where the native terrain (6 m grid, NW-SE diagonals) crosses the
sea level. The coast kept wet <= 0.45 and land >= 1.40, so the crossing falls at a fraction of each edge that the grid
sets, and the coast reads serrated; land clamped to the 1.40 floor left coplanar flats that turn dark in the engine.
1. Outline: signed distance to the sea/delta (sd_sea of water_v30 where finite, the class boundary elsewhere; pond
   water counts as land), Gaussian-smoothed (--sigma m) and clamped so the zero line moves at most --max-shift; then the
   exact distance to its zero contour, signed by the smoothed field (positive on land).
2. Profile: target = --sea + --slope * sd within --band. A vertex ending a native edge (east, south, NW-SE diagonal)
   whose ends lie on opposite sides takes the target, so the waterline at every swell level follows the outline,
   within the gates of tools/terrain/verify_terrain_v30.py: wet at most --sea - 0.10, land at least the beach floor
   (0.80), and each move capped (--max-raise for a bed, --max-lower for land). Elsewhere in the band land never drops
   and is raised to min(target, --floor); the bed never rises and is deepened to the target.
3. Classes and levels follow the heights inside the band: sea or delta (level --sea) below --sea, land above. The
   'beach' mask becomes every land vertex below the verifier's land floor of 1.40 m (the strip the land-floor gate
   checks at 0.80 m).
4. Floor and flats: with --raise-land, free land below --floor outside the band rises to --floor before the face
   check (the engine shades land at 1.40-1.55 m intermittently, evidence/v30-v4-candidate-2026-10-05, so 1.60 keeps
   land out of it). Land within 2 mm of --floor and outside the band then gets a smooth micro-relief of up to
   --flat-amp (seeded noise of --flat-wavelength), tapered to zero over --flat-taper from the flat's edge.
Fixed: platforms, reserves, the nature envelope, the 24 m navigable and delta corridors (with their margin), pond-class
water, every vertex of a cell with a pond plane, the 480 m Narva identity zone, the map border. The old beach strip is
re-authored, not kept. Edits that make a land face steeper than 35 degrees (or than it was) are undone.
Usage: profile_coast_v30.py --terrain IN.npz --out OUTDIR [--sea 0.75] [--slope 0.15] [--band 12] [--sigma 12]
                            [--floor 1.40] [--raise-land]
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import contourpy
import numpy as np
import shapely
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'terrain'))
from v30_common import N, POND_CLASSES, R, cell_planes, grid_xz, vertex_plane_bounds  # noqa: E402
from finish_shores_v30 import discard_steeper_land_faces, protect_corridors  # noqa: E402

WATER = Path(R) / 'tests/terrain_v30/water_v30.npz'
NATURE = Path(R) / 'tests/regional_outline_v1/reference.npz'
SEA_CLASSES = (1, 4)
EDGES = ((0, 1), (1, 0), (1, 1))
NARVA = (2417.1428225906, 6889.8850822322)
GATES = dict(depth_min_m=0.10, land_floor_m=1.40, beach_floor_m=0.80, narva_radius_m=480.0)   # verify_terrain_v30.py:30


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def zero_lines(field, mask=None):
    z = np.ma.masked_invalid(np.where(mask, field, np.nan)) if mask is not None else np.ma.masked_invalid(field)
    gen = contourpy.contour_generator(x=np.arange(N) * 6.0, y=12282.0 - np.arange(N) * 6.0, z=z,
                                      line_type=contourpy.LineType.Separate)
    return [ln for ln in gen.lines(0.0) if len(ln) >= 3]


def turning(lines, scale=12.0):
    vals = []
    for ln in lines:
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ln, axis=0), axis=1))]
        if s[-1] < 4 * scale:
            continue
        q = np.arange(0, s[-1], scale)
        p = np.column_stack([np.interp(q, s, ln[:, 0]), np.interp(q, s, ln[:, 1])])
        a = np.degrees(np.arctan2(*np.diff(p, axis=0).T[::-1]))
        vals.append(np.abs((np.diff(a) + 180) % 360 - 180))
    v = np.concatenate(vals) if vals else np.array([np.nan])
    return {'n': int(v.size), 'p50': round(float(np.nanpercentile(v, 50)), 1), 'p90': round(float(np.nanpercentile(v, 90)), 1),
            'p95': round(float(np.nanpercentile(v, 95)), 1)}


def crossing_offsets(h, sd, level, edges):
    """Distance (m) between the terrain crossing of the sea level and the outline crossing, per crossing edge."""
    out, nocross = [], 0
    for (ra, ca, rb, cb, length) in edges:
        sa, sb = sd[ra, ca], sd[rb, cb]
        tstar = sa / (sa - sb)
        ha, hb = h[ra, ca] - level, h[rb, cb] - level
        ok = ha * hb < 0
        t = np.where(ok, ha / np.where(ok, ha - hb, 1.0), np.nan)
        nocross += int((~ok).sum())
        out.append(np.abs(t - tstar)[ok] * length)
    v = np.concatenate(out) if out else np.array([])
    return {'edges': int(v.size + nocross), 'no_crossing': nocross,
            **({k: round(float(np.percentile(v, q)), 3) for k, q in (('p50', 50), ('p90', 90), ('p99', 99))} if v.size else {})}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--sea', type=float, default=0.75)
    ap.add_argument('--slope', type=float, default=0.15)
    ap.add_argument('--band', type=float, default=12.0)
    ap.add_argument('--sigma', type=float, default=12.0)
    ap.add_argument('--max-shift', type=float, default=4.0)
    ap.add_argument('--floor', type=float, default=1.40)
    ap.add_argument('--max-raise', type=float, default=2.0)
    ap.add_argument('--max-lower', type=float, default=1.5)
    ap.add_argument('--flat-amp', type=float, default=0.12)
    ap.add_argument('--flat-wavelength', type=float, default=36.0)
    ap.add_argument('--flat-taper', type=float, default=12.0)
    ap.add_argument('--seed', type=int, default=20261004)
    ap.add_argument('--raise-land', action='store_true',
                    help='free land below --floor outside the coast band rises to --floor (before the face check)')
    a = ap.parse_args()
    assert not a.out.exists(), 'fresh output required'
    t0 = time.time()
    t = dict(np.load(a.terrain))
    h0 = t['heights'].astype(np.float64)
    cls0 = t['cls'].copy()
    level0 = t['level'].astype(np.float64)
    x, z = grid_xz()
    sea0 = np.isin(cls0, SEA_CLASSES)
    land0 = cls0 == 0
    planes = cell_planes(cls0, level0)
    _, corridor, entries, _ = protect_corridors(planes)
    pmin, pmax = vertex_plane_bounds(planes)
    nature = np.load(NATURE)['reserve'].astype(bool)
    narva_zone = np.hypot(x - NARVA[0], z - NARVA[1]) <= GATES['narva_radius_m']
    fixed = (t['platform'] | t['reserve'] | nature | corridor | np.isin(cls0, POND_CLASSES) | np.isfinite(pmin)
             | np.isfinite(pmax) | narva_zone | (x < 12) | (z < 12) | (x > 12270) | (z > 12270))

    # 1. smoothed coast outline and its signed distance (positive on land)
    sd_sea = np.load(WATER)['sd_sea'].astype(np.float64)
    # distance_transform_edt measures, at each non-zero cell, the distance to the nearest zero cell
    class_sd = np.where(sea0, -ndimage.distance_transform_edt(sea0), ndimage.distance_transform_edt(~sea0)) * 6.0
    agree = np.isfinite(sd_sea) & (np.sign(sd_sea) == np.sign(class_sd))
    base = np.where(np.isfinite(sd_sea) & agree, sd_sea, class_sd)
    smooth = ndimage.gaussian_filter(base, a.sigma / 6.0)
    smooth = np.clip(smooth, base - a.max_shift, base + a.max_shift)
    near = np.abs(base) <= a.band + a.max_shift + 9.0
    lines = zero_lines(smooth, near)
    segs = np.concatenate([np.stack([ln[:-1], ln[1:]], axis=1) for ln in lines if len(ln) >= 2])
    tree = shapely.STRtree(shapely.linestrings(segs))
    _, dist = tree.query_nearest(shapely.points(x[near], z[near]), return_distance=True, all_matches=False)
    sd = np.full((N, N), np.nan)
    sd[near] = np.where(smooth[near] < 0, -dist, dist)

    # 2. profile
    target = a.sea + a.slope * sd
    band = near & np.isfinite(sd) & (np.abs(sd) <= a.band)
    editable = band & (land0 | sea0) & ~fixed
    forced = np.zeros((N, N), bool)
    edges = []
    for dr, dc in EDGES:
        ra, ca = np.meshgrid(np.arange(N - dr), np.arange(N - dc), indexing='ij')
        rb, cb = ra + dr, ca + dc
        sa, sb = sd[ra, ca], sd[rb, cb]
        cross = np.isfinite(sa) & np.isfinite(sb) & (sa * sb < 0) & (land0[ra, ca] | sea0[ra, ca]) & (land0[rb, cb] | sea0[rb, cb])
        forced[ra[cross], ca[cross]] = True
        forced[rb[cross], cb[cross]] = True
        edges.append((ra[cross], ca[cross], rb[cross], cb[cross], 6.0 * (2 ** 0.5 if dr and dc else 1.0)))
    forced &= editable
    land_side = sd > 0
    with np.errstate(invalid='ignore'):
        want = np.where(forced, target, np.where(land_side, np.maximum(h0, np.minimum(target, a.floor)),
                                                 np.minimum(h0, target)))
        # gates: land side at least the beach floor, water side at least 0.10 m deep
        want = np.where(land_side, np.maximum(want, GATES['beach_floor_m']), np.minimum(want, a.sea - GATES['depth_min_m']))
        # move caps keep quays and drop-offs; a capped vertex may stay on its old side of the outline
        capped_mask = editable & ((want > h0 + a.max_raise) | (want < h0 - a.max_lower))
        want = np.clip(want, h0 - a.max_lower, h0 + a.max_raise)
        # no vertex may end between the two gates (too shallow for water, too low for beach)
        dead = (want > a.sea - GATES['depth_min_m']) & (want < GATES['beach_floor_m'])
        want = np.where(dead, np.where(want >= (a.sea - GATES['depth_min_m'] + GATES['beach_floor_m']) / 2,
                                       GATES['beach_floor_m'], a.sea - GATES['depth_min_m']), want)
    capped = int(capped_mask.sum())
    h1 = h0.copy()
    h1[editable] = want[editable]
    raise_mask = np.zeros((N, N), bool)
    if a.raise_land:
        raise_mask = land0 & ~fixed & ~band & (h1 < a.floor)
        h1[raise_mask] = a.floor

    # 3. classes and levels follow the heights inside the band
    cls1, level1 = cls0.copy(), level0.copy()
    _, idx = ndimage.distance_transform_edt(~sea0, return_indices=True)
    near_sea_cls = cls0[idx[0], idx[1]]
    to_sea = editable & (h1 < a.sea) & land0
    to_land = editable & (h1 >= a.sea) & sea0
    cls1[to_sea] = near_sea_cls[to_sea]
    level1[to_sea] = a.sea
    cls1[to_land] = 0
    level1[to_land] = np.nan

    # undo edits that steepen land faces beyond 35 degrees (classes of reverted vertices go back too)
    h2, faces = discard_steeper_land_faces(h1, h0, cls1)
    reverted = (h2 != h1.astype('float32').astype(float)) & (h2 == h0.astype('float32').astype(float))
    cls1[reverted], level1[reverted] = cls0[reverted], level0[reverted]

    # 4. micro-relief on the flats left at the floor, outside the band
    flat = (cls1 == 0) & (np.abs(h2 - a.floor) < 0.002) & ~fixed & ~band
    rng = np.random.default_rng(a.seed)
    noise = ndimage.gaussian_filter(rng.standard_normal((N, N)), a.flat_wavelength / 6.0 / 2.0)
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    taper = np.clip(ndimage.distance_transform_edt(flat) * 6.0 / a.flat_taper, 0, 1)
    h3 = h2.copy()
    h3[flat] = a.floor + a.flat_amp * noise[flat] * taper[flat]
    h3 = h3.astype('float32').astype(np.float64)
    beach1 = (t['beach'] | ((cls1 == 0) & (h3 < GATES['land_floor_m'] - 1e-6))) & (cls1 == 0) & ~narva_zone

    # report
    changed = h3 != h0.astype('float32').astype(np.float64)
    assert not np.any(changed & fixed), 'protected height changed'
    d = h3 - h0
    flat_after = (cls1 == 0) & (np.abs(h3 - a.floor) < 0.002)
    wl_before = turning(zero_lines(h0 - a.sea, near))
    wl_after = turning(zero_lines(h3 - a.sea, near))
    out = dict(t)
    out['heights'] = h3.astype(t['heights'].dtype)
    out['cls'] = cls1
    out['level'] = level1.astype(t['level'].dtype)
    out['water'] = cls1 > 0
    out['beach'] = beach1
    sea1 = np.isin(cls1, SEA_CLASSES) & (np.hypot(x - NARVA[0], z - NARVA[1]) > 600.0)   # verifier's Narva zone
    gate_check = {'sea_too_shallow': int((sea1 & (level1 - h3 < GATES['depth_min_m'] - 1e-6)).sum()),
                  'beach_below_floor': int((beach1 & (h3 < GATES['beach_floor_m'] - 1e-6)).sum()),
                  'land_below_floor_outside_beach': int(((cls1 == 0) & ~beach1 & ~narva_zone
                                                         & (h3 < GATES['land_floor_m'] - 1e-6)).sum())}
    gate_to_floor = (cls1 == 0) & (h3 >= GATES['land_floor_m'] - 1e-6) & (h3 < a.floor - 1e-6)
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out / 'terrain_coast.npz', **out)
    np.savez_compressed(a.out / 'sd_coast.npz', sd=sd.astype(np.float32))
    np.savez_compressed(a.out / 'masks.npz', band=band, forced=forced, editable=editable, flat=flat, changed=changed)
    rep = {
        'status': 'BUILT_PENDING_GATES_AND_ENGINE_VIEWS',
        'params': {k: v for k, v in vars(a).items() if k not in ('terrain', 'out')},
        'outline': {'lines': len(lines), 'sd_sea_agrees_with_classes': int(agree.sum()),
                    'shift_m_p95': round(float(np.percentile(np.abs(smooth - base)[near], 95)), 2)},
        'vertices': {'band': int(band.sum()), 'editable': int(editable.sum()), 'forced': int(forced.sum()),
                     'changed': int(changed.sum()), 'to_sea': int(to_sea.sum()), 'to_land': int(to_land.sum()),
                     'forced_at_move_cap': capped, 'beach_before_after': [int(t['beach'].sum()), int(beach1.sum())],
                     'face_recovery': faces, 'flat_micro_relief': int(flat.sum()),
                     'raised_to_floor': int((raise_mask & changed).sum())},
        'land_between_gate_and_floor_after': {'free_outside_band': int((gate_to_floor & ~fixed & ~band).sum()),
                                              'fixed': int((gate_to_floor & fixed).sum()),
                                              'in_band': int((gate_to_floor & band & ~fixed).sum())},
        'change_m': {'raise_max': round(float(d.max()), 3), 'lower_max': round(float(-d.min()), 3),
                     'abs_p50_p90': [round(float(np.percentile(np.abs(d[changed]), q)), 3) for q in (50, 90)] if changed.any() else None},
        'crossing_offset_m_vs_smoothed_outline': {'before': crossing_offsets(h0, sd, a.sea, edges),
                                                  'after': crossing_offsets(h3, sd, a.sea, edges)},
        'waterline_turn_deg_per_12m_at_sea': {'before': wl_before, 'after': wl_after},
        'land_at_floor_vertices': {'before': int(((cls0 == 0) & (np.abs(h0 - a.floor) < 0.002)).sum()),
                                   'after': int(flat_after.sum())},
        'land_below_m_after': {str(s): int(((cls1 == 0) & (h3 < s)).sum()) for s in (0.85, 1.0, 1.10, 1.25)},
        'gate_check': gate_check,
        'protected_corridors': len(entries),
        'inputs': {str(p): sha(p) for p in (a.terrain, WATER, NATURE, Path(__file__))},
        'output_sha256': sha(a.out / 'terrain_coast.npz'), 'seconds': round(time.time() - t0, 1),
        'limits': ['Heights, classes and levels inside the coast band; pond-class water untouched.',
                   'Engine views and the grouped gates decide acceptance.']}
    (a.out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in rep.items() if k not in ('inputs',)}, indent=1))


if __name__ == '__main__':
    main()
