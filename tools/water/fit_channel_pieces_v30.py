"""Fit vanilla channel pieces to the pilot reaches of terrain V30 (BALTIC-015).

Plan: plans/v30-vanilla-channel-water-pilot.md. Per reach:
- Axis from the water design (tests/water_v3 profiles.npz or navigable_samples.npz), resampled every 2 m
  and oriented downstream; current level = the horizontal plane of the cell under each sample.
- New surface: the running minimum of the current level, interpolated between the foot of every step,
  so it never rises above the current water; the downstream anchor takes the lowest plane under the
  last skirt, so both end skirts slide under the horizontal water that stays.
- Pieces: vanilla straights and 10/30 degree curves chained edge to edge downstream (local -z points
  downstream, as in Chernarus), uniformly scaled to cover the wider wet side plus a margin, pitched so
  the flat level meets the new surface at both edges, without roll. The second half of a reach with
  'overlap_from' overlaps straights by one skirt pair (6 m x scale) instead of meeting edge to edge.
- Horizontal water: channel cells of the reach under a vanilla footprint leave their pieces; a piece
  that keeps other cells is re-meshed (tools/navigation/water_mesh.py) without them, and tile-border
  slivers that touch the removed cells go with them.
- Terrain: wet channel vertices of the removed cells drop by the level reduction, so each keeps its
  current depth; nothing rises; level follows the new surface there.
Also places a calibration pad of four pieces on flat dry ground (--no-pad leaves it out); --overlap-all makes
every reach overlap its straights. Writes <out>/terrain_pilot.npz,
<out>/water (source models + pieces.json for build_v30_package.ps1 -WaterSource), <out>/axes.json and
<out>/report.json with the offline gates. Usage:
  fit_channel_pieces_v30.py --terrain <npz> --water <dedup water folder> --library <library.json> --out <dir>
                            [--design <water design folder>] [--overlap-all] [--no-pad] [--sea-cut 0.80]
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import shutil
import sys

import numpy as np
from scipy.ndimage import binary_dilation, binary_erosion, gaussian_filter1d, uniform_filter, uniform_filter1d
from shapely import make_valid
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'terrain'))
sys.path.insert(0, str(ROOT / 'tools' / 'navigation'))
from v30_common import cell_planes  # noqa: E402
from water_mesh import write_water_mesh  # noqa: E402

DESIGN = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\tests\water_v3')
PREFIX = 'baltic_water_v30'
BAND, TILE, SEA_CUT = 0.025, 48, 0.80
CHANNEL, STILL = {3, 5, 6}, {2, 4, 7}
STEP = 2.0
REACHES = [
    # R1 moved from the Luga head (a lake/river level mismatch, not a slope) to the only monotone sloped
    # navigable window: Narva_28, 1.62 -> 0.95 m over 300 m, trimmed clear of its junctions.
    {'name': 'R1', 'source': 'navigable_samples.npz', 'key': 'Narva_28', 'box': (2150, 2285, 7105, 7290),
     'family': 'river', 'overlap_from': 0.5, 'smooth_m': 40.0, 'max_scale': 4.0},
    {'name': 'R2', 'source': 'profiles.npz', 'key': 'river_023', 'box': (8196, 8286, 8892, 9258),
     'family': 'stream', 'overlap_from': None, 'smooth_m': 15.0},
    {'name': 'R3', 'source': 'profiles.npz', 'key': 'stream_0255', 'box': (7176, 7446, 5598, 5862),
     'family': 'stream', 'overlap_from': None, 'smooth_m': 15.0},
]
PAD = [('river_24_24', 1.0, 0.0), ('river_24_24', 1.0, 2.0), ('stream_14_24', 0.5, 2.0), ('river_24_24', 2.0, 1.0)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bilinear(grid, x, z):
    c = np.clip(np.asarray(x, float) / 6.0, 0, grid.shape[1] - 1.0001)
    r = np.clip((12282 - np.asarray(z, float)) / 6.0, 0, grid.shape[0] - 1.0001)
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    fc, fr = c - c0, r - r0
    return (grid[r0, c0] * (1 - fc) * (1 - fr) + grid[r0, c0 + 1] * fc * (1 - fr)
            + grid[r0 + 1, c0] * (1 - fc) * fr + grid[r0 + 1, c0 + 1] * fc * fr)


def cell_rc(x, z):
    return int((12282 - z) // 6), int(x // 6)


def cell_centre(r, c):
    return 6 * c + 3.0, 12279.0 - 6 * r


def cell_box(r, c, pad=0.0):
    return box(6 * c - pad, 12276 - 6 * r - pad, 6 * c + 6 + pad, 12282 - 6 * r + pad)


class Axis:
    def __init__(self, pts):
        self.line = LineString(pts)
        n = int(self.line.length // STEP) + 1
        self.d = np.linspace(0, self.line.length, n)
        self.pts = np.array([self.line.interpolate(v).coords[0] for v in self.d])
        t = uniform_filter1d(np.gradient(self.pts, axis=0), size=min(7, n), axis=0, mode='nearest')
        self.tan = t / np.linalg.norm(t, axis=1, keepdims=True)
        self.nrm = np.column_stack([-self.tan[:, 1], self.tan[:, 0]])

    def project(self, p):
        s = self.line.project(Point(p))
        q = np.array(self.line.interpolate(s).coords[0])
        i = int(min(round(s / STEP), len(self.d) - 1))
        return s, float(np.linalg.norm(np.asarray(p) - q)), self.tan[i]


def levels_on(ax, plane):
    lv = np.array([plane[cell_rc(*p)] for p in ax.pts])
    ok = np.isfinite(lv)
    return np.interp(ax.d, ax.d[ok], lv[ok])


def make_axis(reach, plane):
    a = np.load(DESIGN / reach['source'])[reach['key']]
    x0, x1, z0, z1 = reach['box']
    idx = np.where((a[:, 1] >= x0) & (a[:, 1] <= x1) & (a[:, 2] >= z0) & (a[:, 2] <= z1))[0]
    # 150 m of design axis on each side of the box, for the end skirts
    i0 = int(np.searchsorted(a[:, 0], a[idx[0], 0] - 150.0))
    i1 = int(min(np.searchsorted(a[:, 0], a[idx[-1], 0] + 150.0), len(a) - 1))
    ax = Axis(a[i0:i1 + 1, 1:3])
    lv = levels_on(ax, plane)
    if lv[0] < lv[-1]:
        ax = Axis(ax.pts[::-1])
        lv = levels_on(ax, plane)
    core = np.where((ax.pts[:, 0] >= x0) & (ax.pts[:, 0] <= x1) & (ax.pts[:, 1] >= z0) & (ax.pts[:, 1] <= z1))[0]
    # keep 20 m of axis beyond each end of the reach for the end skirts (design axes may start in the box)
    return ax, lv, max(float(ax.d[core[0]]), 20.0), min(float(ax.d[core[-1]]), float(ax.d[-1]) - 20.0)


def wet_halfwidths(ax, lv, heights, reach_max=70.0):
    wl, wr = np.zeros(len(ax.d)), np.zeros(len(ax.d))
    steps = np.arange(0.5, reach_max, 0.5)
    for i, (p, n) in enumerate(zip(ax.pts, ax.nrm)):
        for sign, out in ((1, wl), (-1, wr)):
            q = p[None, :] + sign * steps[:, None] * n[None, :]
            dry = bilinear(heights, q[:, 0], q[:, 1]) >= lv[i]
            out[i] = steps[np.argmax(dry)] if dry.any() else reach_max
    return wl, wr


def piece_frames(p, s):
    e, st = p['end'], p['start']
    return (np.array(e['mid']) * s, math.radians(e['heading_deg']), np.array(st['mid']) * s, math.radians(st['heading_deg']))


def axes2(psi):
    return np.array([math.cos(psi), -math.sin(psi)]), np.array([math.sin(psi), math.cos(psi)])


def place(p, s, joint, down):
    """Put the piece's end edge (upstream) on the joint; return origin, yaw and the downstream joint."""
    E, aE, S, aS = piece_frames(p, s)
    psi = math.atan2(-down[0], -down[1]) - aE
    right, fwd = axes2(psi)
    origin = joint - (E[0] * right + E[1] * fwd)
    j2 = origin + S[0] * right + S[1] * fwd
    return origin, psi, j2, -np.array([math.sin(psi + aS), math.cos(psi + aS)])


def matrix(psi, theta, s, pos):
    right = np.array([math.cos(psi), 0.0, -math.sin(psi)])
    fwd = np.array([math.sin(psi) * math.cos(theta), math.sin(theta), math.cos(psi) * math.cos(theta)])
    up = np.cross(fwd, right)
    assert up[1] > 0
    return [float(v) for v in (*(right * s), *(up * s), *(fwd * s), *pos)]


def footprint(p, s, origin, psi):
    v = np.array(p['mesh']['v'])
    left = sorted([q for q in v if q[0] < 0], key=lambda q: q[2])
    right_side = sorted([q for q in v if q[0] > 0], key=lambda q: -q[2])
    r, f = axes2(psi)
    return make_valid(Polygon([tuple(origin + q[0] * s * r + q[2] * s * f) for q in left + right_side]))


def surface_at(piece, lib, x, z):
    """World height of the piece surface over (x, z) from its LOD0 triangles; None outside."""
    p = lib[piece['type']]
    m = np.array(piece['matrix'][:9]).reshape(3, 3)
    pos = np.array(piece['matrix'][9:])
    right, up, fwd = m[0], m[1], m[2]
    lx, lz = np.linalg.solve(np.array([[right[0], fwd[0]], [right[2], fwd[2]]]), np.array([x - pos[0], z - pos[2]]))
    v = np.array(p['mesh']['v'])
    for t in p['mesh']['tri']:
        a, b, c = v[t[0]], v[t[1]], v[t[2]]
        d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
        if abs(d) < 1e-12:
            continue
        w1 = ((b[2] - c[2]) * (lx - c[0]) + (c[0] - b[0]) * (lz - c[2])) / d
        w2 = ((c[2] - a[2]) * (lx - c[0]) + (a[0] - c[0]) * (lz - c[2])) / d
        w3 = 1 - w1 - w2
        if min(w1, w2, w3) >= -1e-6:
            ly = w1 * a[1] + w2 * b[1] + w3 * c[1]
            return float(pos[1] + lx * right[1] + ly * up[1] + lz * fwd[1])
    return None


def plane_at(piece, flat_y, x, z):
    """Height of the piece's flat plane (model y = flat_y) over (x, z)."""
    m = np.array(piece['matrix'][:9]).reshape(3, 3)
    pos = np.array(piece['matrix'][9:])
    right, up, fwd = m[0], m[1], m[2]
    lx, lz = np.linalg.solve(np.array([[right[0], fwd[0]], [right[2], fwd[2]]]), np.array([x - pos[0], z - pos[2]]))
    return float(pos[1] + flat_y * up[1] + lz * fwd[1])


def fit_reach(reach, lib, plane, heights, cls, cb):
    ax, lv, s_lo, s_hi = make_axis(reach, plane)
    assert s_lo > 6 and s_hi < ax.d[-1] - 6, ('axis margin too short', reach['name'], s_lo, s_hi, ax.d[-1])
    wl, wr = wet_halfwidths(ax, lv, heights)
    tol = np.maximum(1.0, 0.05 * (wl + wr))
    fam = {k: v for k, v in lib.items() if v['family'] == reach['family'] and v['turn_deg'] == 0}
    length = {k: v['end']['mid'][1] - v['start']['mid'][1] for k, v in fam.items()}
    # 24 and 12 m straights: the 6 m piece is skirt only (its flat part is a single line)
    straights = sorted([k for k in fam if length[k] > 10], key=lambda k: -length[k])
    width = max(v['width'] for v in fam.values())

    # reach cells: channel cells in the wet corridor of the design axis between s_lo and s_hi
    corner = lambda r, c: {int(cls[r, c]), int(cls[r, c + 1]), int(cls[r + 1, c]), int(cls[r + 1, c + 1])}
    cells = set()
    for i in range(int(s_lo // STEP), int(math.ceil(s_hi / STEP)) + 1):
        for off in np.arange(-wr[i] - tol[i], wl[i] + tol[i] + 0.01, 1.0):
            r, c = cell_rc(*(ax.pts[i] + off * ax.nrm[i]))
            if not (0 <= r < cb.shape[0] and 0 <= c < cb.shape[1]) or cb[r, c] < 0 or (r, c) in cells:
                continue
            cc = corner(r, c)
            if cc & CHANNEL and not cc & STILL and s_lo <= ax.project(cell_centre(r, c))[0] <= s_hi:
                cells.add((r, c))
    cells = sorted(cells)

    # new surface: running minimum, interpolated between the feet of the steps
    mono = np.minimum.accumulate(lv)
    i_lo, i_hi = int(s_lo // STEP), int(math.ceil(s_hi / STEP))
    i_tail = min(len(lv) - 1, i_hi + int(math.ceil((3 * 3.0 + 2) / STEP)))
    anchors = sorted({i_lo, i_hi, *[i for i in range(i_lo + 1, i_hi + 1) if mono[i] < mono[i - 1] - 1e-9]})
    vals = [float(mono[i]) for i in anchors]
    vals[-1] = float(mono[i_tail])
    ls = np.interp(ax.d, ax.d[anchors], vals)
    ls[:i_lo] = mono[i_lo]
    ls[i_hi:] = vals[-1]
    assert (ls[:i_tail + 1] <= lv[:i_tail + 1] + 1e-9).all()

    # smoothed axis; half-width each piece must cover = farthest reach cell centre + 1 m
    sm = Axis(np.column_stack([gaussian_filter1d(ax.pts[:, k], reach['smooth_m'] / STEP, mode='nearest') for k in (0, 1)]))
    hw = np.zeros(len(sm.d))
    for r, c in cells:
        s, lat, _ = sm.project(cell_centre(r, c))
        k = min(int(round(s / STEP)), len(hw) - 1)
        hw[max(k - 1, 0):k + 2] = np.maximum(hw[max(k - 1, 0):k + 2], lat + 1.0)
    hw = np.maximum(hw, 2.0)
    head = np.degrees(np.unwrap(np.arctan2(sm.tan[:, 0], sm.tan[:, 1])))
    sm_lo = sm.project(ax.pts[i_lo])[0]
    sm_hi = sm.project(ax.pts[min(i_hi, len(ax.pts) - 1)])[0]

    def span_scale(a, b):
        ia, ib = max(int(a // STEP), 0), min(int(math.ceil(b / STEP)), len(hw) - 1)
        turn = float(np.ptp(head[ia:ib + 1])) if ib > ia else 0.0
        return float(np.clip(2 * hw[ia:ib + 1].max() / width, 0.15, reach.get('max_scale', 3.0))), turn

    pieces = []
    sc0 = span_scale(sm_lo, sm_lo + 24)[0]
    s_cur = max(0.0, sm_lo - 3 * sc0)
    while s_cur < sm_hi + 3 * sc0 - 1.0:
        assert len(pieces) < 600
        overlap = reach['overlap_from'] is None or s_cur >= sm_lo + reach['overlap_from'] * (sm_hi - sm_lo)
        for k in straights:
            sc = span_scale(s_cur, s_cur + length[k] * 3.0)[0]
            for _ in range(3):
                sc, turn = span_scale(s_cur, s_cur + length[k] * sc)
            if turn <= 8.0 or k == straights[-1]:
                break
        span = length[k] * sc
        s_c = min(s_cur + span / 2, sm.d[-1])
        centre = np.array(sm.line.interpolate(s_c).coords[0])
        tdir = sm.tan[min(int(round(s_c / STEP)), len(sm.d) - 1)]
        psi = math.atan2(-tdir[0], -tdir[1])           # local +z points upstream, -z downstream
        pieces.append({'reach': reach['name'], 'type': k, 'scale': sc, 'origin_xz': centre.tolist(), 'yaw': psi,
                       'span_m': span, 'turn_deg': turn, 'overlap': bool(overlap),
                       'lat_mid': float(ax.project(centre)[1])})
        s_cur += (length[k] - 6.0) * sc if overlap else span
        sc0 = sc

    # vertical: flat plane through both ends at the new surface
    for p in pieces:
        r_, f_ = axes2(p['yaw'])
        half = p['span_m'] / 2
        up_xz = np.array(p['origin_xz']) + half * f_
        dn_xz = np.array(p['origin_xz']) - half * f_
        l_up = float(np.interp(ax.project(up_xz)[0], ax.d, ls))
        l_dn = float(np.interp(ax.project(dn_xz)[0], ax.d, ls))
        theta = math.asin(max(-0.7, min(0.7, (l_up - l_dn) / p['span_m'])))
        flat = fam[p['type']]['flat_y'] * p['scale']
        y0 = l_up - flat * math.cos(theta) - half * math.sin(theta)
        p.update(level_up=l_up, level_down=l_dn, pitch_deg=math.degrees(theta), y=y0, model=fam[p['type']]['model'],
                 up_xz=up_xz.tolist(), dn_xz=dn_xz.tolist(),
                 matrix=matrix(p['yaw'], theta, p['scale'], [p['origin_xz'][0], y0, p['origin_xz'][1]]))
    # visible step where a piece starts over its upstream neighbour: neighbour's flat plane vs this piece's
    for a_, b_ in zip(pieces, pieces[1:]):
        x, z = b_['up_xz']
        b_['step_m'] = abs(plane_at(a_, fam[a_['type']]['flat_y'], x, z) - b_['level_up'])
    return {'axis': ax, 'smooth': sm, 'level': lv, 'surface': ls, 'mono': mono, 'wl': wl, 'wr': wr, 'tol': tol,
            'hw': hw, 's_lo': s_lo, 's_hi': s_hi, 'pieces': pieces, 'anchors': anchors, 'reach_cells': cells}


def main():
    global DESIGN
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--water', type=Path, required=True)
    ap.add_argument('--library', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--design', type=Path, default=DESIGN, help='water design folder (reach axes)')
    ap.add_argument('--overlap-all', action='store_true', help='overlap the straights of every reach (no edge-to-edge half)')
    ap.add_argument('--no-pad', action='store_true', help='leave the calibration pad out')
    ap.add_argument('--sea-cut', type=float, default=SEA_CUT, help='pond planes only above this level (default 0.80)')
    a = ap.parse_args()
    DESIGN = a.design
    if a.overlap_all:
        for r in REACHES:
            r['overlap_from'] = None
    assert not a.out.exists(), 'fresh output required'
    t = dict(np.load(a.terrain))
    cls, level, heights = t['cls'], t['level'].astype(float), t['heights'].astype(float)
    plane = cell_planes(cls, level, band=BAND, sea_cut=a.sea_cut)
    cb = np.where(np.isfinite(plane), np.rint(np.nan_to_num(plane) / BAND), -1).astype(np.int32)
    water = json.loads((a.water / 'pieces.json').read_text(encoding='utf-8'))
    lib = json.loads(a.library.read_text(encoding='utf-8'))['pieces']
    models = {m['name']: m for m in water['model_list']}
    pose_of, pose_key = {}, {}
    for k, pose in enumerate(water['poses']):
        key = (int((pose['origin'][0] - 24) // TILE), int((pose['origin'][2] - 24) // TILE), int(pose['band']))
        pose_of[key], pose_key[k] = k, key

    results = [fit_reach(r, lib, plane, heights, cls, cb) for r in REACHES]

    # horizontal water: reach cells under a vanilla footprint leave their pieces
    removed_cells = {}
    for res, reach in zip(results, REACHES):
        res['polys'] = [footprint(lib[p['type']], p['scale'], np.array(p['origin_xz']), p['yaw']) for p in res['pieces']]
        cover = unary_union(res['polys'])
        res['cells'] = [rc for rc in res['reach_cells'] if cover.contains(Point(*cell_centre(*rc)))]
        for rc in res['cells']:
            removed_cells[rc] = reach['name']

    affected = {}
    for (r, c) in removed_cells:
        x, z = cell_centre(r, c)
        affected.setdefault(pose_of[(int(x // TILE), int(z // TILE), int(cb[r, c]))], []).append((r, c))
    out_water = a.out / 'water'
    src = out_water / 'source' / PREFIX
    a.out.mkdir(parents=True)
    shutil.copytree(a.water / 'source' / PREFIX, src)
    new_poses, new_models, removed_poses, clipped = [], [], set(), {}
    for k, rcs in sorted(affected.items()):
        tx, tz, band = pose_key[k]
        own = [(r, c) for r in range(2039 - 8 * tz, 2047 - 8 * tz) for c in range(8 * tx, 8 * tx + 8)
               if 0 <= r < cb.shape[0] and 0 <= c < cb.shape[1] and cb[r, c] == band]
        keep = [rc for rc in own if rc not in removed_cells]
        removed_poses.add(k)
        if not keep:
            continue
        tile = box(tx * TILE - .01, tz * TILE - .01, (tx + 1) * TILE + .01, (tz + 1) * TILE + .01)
        g = make_valid(unary_union([cell_box(r, c) for r, c in keep]).intersection(tile))
        name = f'pilot_{len(new_models):05d}'
        origin = (tx * TILE + 24, tz * TILE + 24)
        rep = write_water_mesh(g, str(src / (name + '.p3d')), origin, uv_local=True)
        b = g.bounds
        rep.update(name=name, sha256=sha(src / (name + '.p3d')),
                   bounds_rel=[b[0] - origin[0], b[1] - origin[1], b[2] - origin[0], b[3] - origin[1]])
        new_models.append(rep)
        new_poses.append({'model': f'{PREFIX}\\{name}.p3d', 'origin': list(water['poses'][k]['origin']), 'band': band,
                          'area_m2': round(g.area, 3), 'clipped_from': k})
        clipped[k] = name
    # tile-border slivers (< 1 m2) of the same band that touch removed cells
    removed_boxes = unary_union([cell_box(r, c, 0.05) for r, c in removed_cells])
    slivers = set()
    for k, pose in enumerate(water['poses']):
        if pose['area_m2'] >= 1.0 or k in removed_poses:
            continue
        b = models[pose['model'].split('\\')[-1][:-4]]['bounds_rel']
        ox, oz = pose['origin'][0], pose['origin'][2]
        if removed_boxes.intersects(box(ox + b[0], oz + b[1], ox + b[2], oz + b[3])) and \
                any(pose_key[k][2] == int(cb[r, c]) for r, c in removed_cells
                    if abs(cell_centre(r, c)[0] - ox) < 60 and abs(cell_centre(r, c)[1] - oz) < 60):
            slivers.add(k)
    removed_poses |= slivers

    # terrain: lower wet channel vertices of the removed cells by the level reduction
    new_h, new_level = heights.copy(), level.copy()
    changed = {}
    for res, reach in zip(results, REACHES):
        ax = res['axis']
        verts = {(r + dr, c + dc) for r, c in res['cells'] for dr in (0, 1) for dc in (0, 1)}
        n, drop_max = 0, 0.0
        for r, c in verts:
            if int(cls[r, c]) not in CHANNEL:
                continue
            s = ax.project((6.0 * c, 12282.0 - 6.0 * r))[0]
            l_old = float(np.interp(s, ax.d, res['mono']))
            l_new = float(np.interp(s, ax.d, res['surface']))
            if heights[r, c] >= l_old:
                continue
            if l_old - l_new > 1e-6:
                new_h[r, c] = heights[r, c] - (l_old - l_new)
                n += 1
                drop_max = max(drop_max, l_old - l_new)
            new_level[r, c] = l_new
        changed[reach['name']] = {'vertices_lowered': n, 'max_drop_m': round(drop_max, 3)}

    # calibration pad on flat dry ground
    flat = np.abs(uniform_filter(heights, 15) - heights) < 0.05
    cand = binary_erosion(cls == 0, iterations=25) & flat & (heights > 5)
    rr, cc = np.nonzero(cand[400:1600:4, 400:1600:4])
    r0, c0 = 400 + 4 * int(rr[len(rr) // 2]), 400 + 4 * int(cc[len(cc) // 2])
    px, pz = 6.0 * c0, 12282.0 - 6.0 * r0
    pad = []
    for n, (k, s, deg) in enumerate([] if a.no_pad else PAD):
        x, z = px + 60.0 * n, pz
        g = float(bilinear(new_h, x, z))
        theta = math.radians(deg)
        y = g + 0.5 - lib[k]['flat_y'] * s * math.cos(theta)
        pad.append({'reach': 'PAD', 'type': k, 'model': lib[k]['model'], 'scale': s, 'pitch_deg': deg, 'yaw': 0.0,
                    'origin_xz': [x, z], 'y': y, 'ground': g, 'matrix': matrix(0.0, theta, s, [x, y, z])})

    # offline gates
    near_wet = binary_dilation(np.isfinite(plane), iterations=1)
    report = {'status': None, 'reaches': {}, 'terrain_changes': changed, 'pad': pad,
              'options': {'overlap_all': bool(a.overlap_all), 'no_pad': bool(a.no_pad), 'sea_cut': a.sea_cut,
                          'design': str(a.design)},
              'horizontal': {'affected_pieces': len(affected), 'clipped_pieces': len(clipped),
                             'removed_pieces_without_remainder': len(removed_poses) - len(clipped) - len(slivers),
                             'slivers_removed': len(slivers), 'removed_cells': len(removed_cells)}}
    all_ok = True
    for res, reach in zip(results, REACHES):
        ps, polys = res['pieces'], res['polys']
        covered = set(res['cells'])
        uncovered = [rc for rc in res['reach_cells'] if rc not in covered]
        # depth where there is water today: corner vertices of the removed cells below the current level
        exposed, dry_cover = [], []
        verts = sorted({(r + dr, c + dc) for r, c in res['cells'] for dr in (0, 1) for dc in (0, 1)})
        for r, c in verts:
            if int(cls[r, c]) not in CHANNEL:
                continue
            x, z = 6.0 * c, 12282.0 - 6.0 * r
            s = res['axis'].project((x, z))[0]
            if heights[r, c] >= float(np.interp(s, res['axis'].d, res['mono'])):
                continue
            hs = [surface_at(p, lib, x, z) for p, poly in zip(ps, polys) if poly.contains(Point(x, z))]
            hs = [h for h in hs if h is not None]
            if not hs:
                dry_cover.append((r, c))
            elif max(hs) - new_h[r, c] <= 0:
                exposed.append((r, c, round(max(hs) - float(new_h[r, c]), 3)))
        shallow = exposed
        overflow = 0
        for p, poly in zip(ps, polys):
            x0, z0, x1, z1 = poly.bounds
            for x in np.arange(math.floor(x0), x1, 2.0):
                for z in np.arange(math.floor(z0), z1, 2.0):
                    if not poly.contains(Point(x, z)):
                        continue
                    h = surface_at(p, lib, x, z)
                    if h is not None and bilinear(new_h, x, z) < h and not near_wet[cell_rc(x, z)]:
                        overflow += 1
        joints = [p['step_m'] for p in ps[1:]]
        types = {}
        for p in ps:
            types[p['type']] = types.get(p['type'], 0) + 1
        steps = [(p['step_m'], 0.14 * p['scale']) for p in ps[1:]]
        visible = [round(m, 3) for m, skirt in steps if m > skirt]
        gates = {'all_reach_cells_covered': not uncovered, 'wet_vertices_covered': not dry_cover,
                 'positive_depth_at_wet_vertices': not exposed,
                 'no_water_over_land_beyond_6m': overflow == 0,
                 'joint_step_within_skirt_depth': not visible}
        all_ok &= all(gates.values())
        lv, ls = res['level'], res['surface']
        i_lo, i_hi = int(res['s_lo'] // STEP), int(math.ceil(res['s_hi'] / STEP))
        report['reaches'][reach['name']] = {
            'gates': gates, 'axis_length_m': round(float(res['axis'].d[-1]), 1),
            'reach_s_m': [round(res['s_lo'], 1), round(res['s_hi'], 1)],
            'level_m': [round(float(lv[i_lo]), 3), round(float(lv[i_hi]), 3)],
            'max_level_reduction_m': round(float((res['mono'] - ls)[i_lo:i_hi + 1].max()), 3),
            'steps_in_reach': len(res['anchors']) - 2, 'reach_cells': len(res['reach_cells']),
            'removed_cells': len(res['cells']),
            'uncovered_count': len(uncovered), 'uncovered_cells': uncovered[:20],
            'wet_vertices_uncovered': len(dry_cover), 'wet_vertices_exposed': len(exposed), 'exposed_sample': exposed[:20],
            'joint_steps_beyond_skirt': visible[:20], 'overflow_points_2m_grid': overflow,
            'pieces': len(ps), 'types': types,
            'scale_range': [round(min(p['scale'] for p in ps), 3), round(max(p['scale'] for p in ps), 3)],
            'pitch_deg_range': [round(min(p['pitch_deg'] for p in ps), 3), round(max(p['pitch_deg'] for p in ps), 3)],
            'max_axis_offset_m': round(max(p['lat_mid'] for p in ps), 2),
            'max_turn_per_piece_deg': round(max(p['turn_deg'] for p in ps), 2),
            'overlap_pieces': sum(p['overlap'] for p in ps),
            'max_joint_level_mismatch_m': round(max(joints) if joints else 0.0, 4),
            'wet_halfwidth_m_median': [round(float(np.median(res['wl'][i_lo:i_hi + 1])), 2),
                                       round(float(np.median(res['wr'][i_lo:i_hi + 1])), 2)]}
    report['status'] = 'PASS_OFFLINE_FIT' if all_ok else 'FAIL_OFFLINE_FIT'
    report['vertices_changed_total'] = int((new_h != heights).sum())
    report['heights_never_raised'] = bool((new_h <= heights + 1e-9).all())
    report['changed_vertices_channel_only'] = bool(np.isin(cls[new_h != heights], list(CHANNEL)).all())

    # outputs
    t2 = dict(t)
    t2['heights'] = new_h.astype(t['heights'].dtype)
    t2['level'] = new_level.astype(t['level'].dtype)
    np.savez_compressed(a.out / 'terrain_pilot.npz', **t2)
    poses = [p for k, p in enumerate(water['poses']) if k not in removed_poses] + new_poses
    vanilla = [{k: p[k] for k in ('reach', 'type', 'model', 'scale', 'pitch_deg', 'yaw', 'matrix', 'overlap') if k in p}
               for res in results for p in res['pieces']] + \
              [{k: p[k] for k in ('reach', 'type', 'model', 'scale', 'pitch_deg', 'yaw', 'matrix')} for p in pad]
    doc = dict(water)
    doc.update(status='PILOT_VANILLA_CHANNELS_NOT_PACKED', poses=poses + vanilla, model_list=water['model_list'] + new_models,
               instances=len(poses) + len(vanilla), models=len(water['model_list']) + len(new_models),
               triangles=water['triangles'] + sum(m['triangles'] for m in new_models),
               pilot={'removed_poses': sorted(removed_poses), 'clipped': {str(k): v for k, v in clipped.items()},
                      'vanilla_instances': len(vanilla), 'source_pieces_sha256': sha(a.water / 'pieces.json')})
    (out_water / 'pieces.json').write_text(json.dumps(doc) + '\n', encoding='utf-8')
    report['terrain_pilot_sha256'] = sha(a.out / 'terrain_pilot.npz')
    report['water_pieces_sha256'] = sha(out_water / 'pieces.json')
    report['inputs'] = {str(a.terrain): sha(a.terrain), str(a.water / 'pieces.json'): sha(a.water / 'pieces.json'),
                        str(a.library): sha(a.library), str(a.design / 'navigable_samples.npz'): sha(a.design / 'navigable_samples.npz'),
                        str(a.design / 'profiles.npz'): sha(a.design / 'profiles.npz'), str(Path(__file__)): sha(__file__)}
    axes = {reach['name']: {'s': res['axis'].d.round(2).tolist(), 'x': res['axis'].pts[:, 0].round(2).tolist(),
                            'z': res['axis'].pts[:, 1].round(2).tolist(), 'level': res['level'].round(3).tolist(),
                            'surface': res['surface'].round(3).tolist(), 'wl': res['wl'].tolist(), 'wr': res['wr'].tolist(),
                            's_lo': res['s_lo'], 's_hi': res['s_hi'], 'removed_cells': [list(rc) for rc in res['cells']],
                            'smooth_x': res['smooth'].pts[:, 0].round(2).tolist(), 'smooth_z': res['smooth'].pts[:, 1].round(2).tolist(),
                            'pieces': [{k: p[k] for k in ('type', 'scale', 'matrix', 'level_up', 'level_down', 'pitch_deg', 'overlap', 'up_xz', 'dn_xz')}
                                       for p in res['pieces']]}
            for res, reach in zip(results, REACHES)}
    (a.out / 'axes.json').write_text(json.dumps(axes) + '\n', encoding='utf-8')
    (a.out / 'report.json').write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('pad', 'inputs')}, indent=1)[:7000])


if __name__ == '__main__':
    main()
