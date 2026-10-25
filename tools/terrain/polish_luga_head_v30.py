"""Luga head polish (Guillermo, 04-10): the navigable Luga ends 140 m short of lake_014 and its last stretch steps
down because ponds touch it; the contour-v2 lakes round it are rectangles. Inside --box:
1. Ponds 8-adjacent to navigable water whose level differs by more than 0.30 m become land, and the design pond the
   connection replaces (the narrow strip the river end runs into) goes entirely. Navigable levels return to the
   builder's band levels (nav_lv): the 0.25 m per 6 m cap had lowered them towards those ponds.
2. Connection channel: --channel polyline (Chaikin-smoothed), --channel-width wide, navigable class, level in a ramp
   from the river level at the axis end to the lake level, bed at least --bed-depth below the water.
3. Contour-v2 lakes with their representative point in the box: straight-sided outlines lose their corners (opening by
   r = min(--round-r, 0.8 x the inscribed radius)), stepped ones are Chaikin-smoothed; a wet vertex more than
   --outside-tol outside the new outline becomes land when it lies on a lake bed and touches no other water.
4. Banks as the builder makes them: land within 8.5 m of water at least 0.35 m above the nearest level and above the
   planes of the cells round it; land never below 1.40 m.
5. Signed distance to the design outline (build_v30_water.py rule: nearest segment of every inland outline, sign by
   vertex rasterisation) recomputed in the box with the rounded lakes and the channel, after checking that the same
   code reproduces the base field there with the original outlines.
Usage: polish_luga_head_v30.py --terrain IN.npz --sd-base SD.npz --out OUTDIR [--box xmin,zmin,xmax,zmax] ..."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import shapely
from scipy.ndimage import binary_dilation, distance_transform_edt
from shapely.geometry import LineString, shape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v30_common import N, R, cell_planes, grid_xz, raster_vertices, vertex_plane_bounds  # noqa: E402

W_DIR = Path(R) / 'tests' / 'water_v3'
CONTOUR = Path(R) / 'evidence' / 'regional-foundation-v1' / 'water-surfaces-contour-v2.geojson'
STREAM_TIER = 2500
BANK_RADIUS, BANK_MARGIN, DRY_FLOOR, SEPARATION = 8.5, 0.35, 1.4, 0.30
# River end inside the navigable polygon, north along the replaced pond strip, across the 3.0 m flat to lake_014.
CHANNEL = '10530,4150;10531,4176;10525,4205;10524,4248;10540,4285;10580,4310;10603,4338'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def chaikin(pts, rounds=3):
    for _ in range(rounds):
        p = np.asarray(pts)
        q, r = 0.75 * p[:-1] + 0.25 * p[1:], 0.25 * p[:-1] + 0.75 * p[1:]
        pts = np.vstack([p[:1], np.column_stack([q, r]).reshape(-1, 2), p[-1:]])
    return pts


def chaikin_ring(xy, rounds=3):
    p = np.asarray(xy)[:-1]
    for _ in range(rounds):
        q = np.roll(p, -1, axis=0)
        p = np.column_stack([0.75 * p + 0.25 * q, 0.25 * p + 0.75 * q]).reshape(-1, 2)
    return np.vstack([p, p[:1]])


def signed_distance(polys, pts_x, pts_z, inside):
    segs = []
    for g in polys:
        for part in (g.geoms if hasattr(g, 'geoms') else [g]):
            for ring in [part.exterior] + list(part.interiors):
                xy = np.asarray(ring.coords)
                segs.append(np.stack([xy[:-1], xy[1:]], axis=1))
    tree = shapely.STRtree(shapely.linestrings(np.concatenate(segs)))
    _, dist = tree.query_nearest(shapely.points(pts_x, pts_z), return_distance=True, all_matches=False)
    return np.where(inside, -dist, dist)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--sd-base', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--design', type=Path, default=W_DIR)
    ap.add_argument('--contour', type=Path, default=CONTOUR, help='contour-v2 lakes (a smoothed copy for a smoothed design)')
    ap.add_argument('--box', default='10150,3700,10700,4600')
    ap.add_argument('--channel', default=CHANNEL)
    ap.add_argument('--channel-width', type=float, default=20.0)
    ap.add_argument('--bed-depth', type=float, default=0.35)
    ap.add_argument('--round-r', type=float, default=8.0)
    ap.add_argument('--outside-tol', type=float, default=1.5)
    a = ap.parse_args()
    assert not a.out.exists()
    bx0, bz0, bx1, bz1 = (float(v) for v in a.box.split(','))
    box = shapely.box(bx0, bz0, bx1, bz1)
    t = dict(np.load(a.terrain))
    cls, lev, h = t['cls'].copy(), t['level'].astype(np.float64), t['heights'].astype(np.float64)
    cls0, lev0, h0 = cls.copy(), lev.copy(), h.copy()
    x, z = grid_xz()
    inbox = (x >= bx0) & (x <= bx1) & (z >= bz0) & (z <= bz1)
    rep = {'box': a.box, 'design': str(a.design), 'contour': str(a.contour)}

    def nb8(m):
        p = np.pad(m, 1)
        out = np.zeros_like(m)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    out |= p[1 + dr:1 + dr + N, 1 + dc:1 + dc + N]
        return out

    # Design outlines, as build_v30_water.py reads them.
    contour = json.load(open(a.contour, encoding='utf-8'))['features']
    bodies = json.load(open(a.design / 'water_v3.geojson', encoding='utf-8'))['features']
    streams = [f for f in json.load(open(a.design / 'streams_candidates.geojson', encoding='utf-8'))['features']
               if f['properties']['tier_m'] >= STREAM_TIER]
    lakes = [(f['properties']['body'], shape(f['geometry']), f['properties']['level_m']) for f in contour
             if f['properties']['body'].startswith('lake')]
    bands = [(shape(f['geometry']), f['properties']['level_m']) for f in contour if f['properties']['body'].startswith('river')]
    nav = [shape(f['geometry']) for f in bodies if f['properties']['class'] == 'navigable']
    other = [shape(f['geometry']) for f in bodies if f['properties']['class'] not in ('navigable', 'pond')]
    ponds = [shape(f['geometry']) for f in bodies if f['properties']['class'] == 'pond']
    stream_g = [shape(f['geometry']) for f in streams]

    # Builder band levels for navigable water (build_v30_water.py: V29 bands, nearest band vertex).
    band_lv = raster_vertices([g for g, _ in bands], values=[v for _, v in bands], dtype='float32', all_touched=True)
    _, idx = distance_transform_edt(~(band_lv > 0), return_indices=True)
    nav_lv = band_lv[idx[0], idx[1]].astype(np.float64)

    # 2. Connection channel geometry and levels.
    pts = np.array([[float(v) for v in p.split(',')] for p in a.channel.split(';')])
    axis = LineString(chaikin(pts))
    chan_poly = axis.buffer(a.channel_width / 2, quad_segs=16)
    river_end = shapely.Point(pts[1])
    s_end = axis.project(river_end)
    lake_hit = [(n, g, lv) for n, g, lv in lakes if g.contains(shapely.Point(pts[-1]))]
    assert len(lake_hit) == 1, 'channel must end inside exactly one lake'
    lake_name, lake_g, lake_level = lake_hit[0]
    s_lake = axis.project(lake_g.exterior.intersection(axis).representative_point()) if axis.intersects(lake_g.exterior) else axis.length
    near_end = (cls == 3) & (np.hypot(x - pts[1][0], z - pts[1][1]) <= 20)
    start_level = float(np.median(nav_lv[near_end]))
    replaced_pond = [g for g in ponds if g.intersects(chan_poly) and g.intersection(chan_poly).area > 0.5 * g.area]

    # 1. Ponds that touch navigable water (or the channel) and the replaced strip become land.
    chan_m = raster_vertices([chan_poly]).astype(bool) & inbox
    new_chan = chan_m & ~np.isin(cls, (2, 3))
    strip = raster_vertices(replaced_pond).astype(bool) & (cls == 7) & inbox if replaced_pond else np.zeros_like(chan_m)
    cls[strip], lev[strip] = 0, np.nan
    s_chan = np.array([axis.project(shapely.Point(px, pz)) for px, pz in zip(x[new_chan], z[new_chan])])
    ramp = np.clip((s_chan - s_end) / max(s_lake - s_end, 1e-6), 0.0, 1.0)
    cls[new_chan] = 3
    lev[new_chan] = start_level + (lake_level - start_level) * ramp
    h[new_chan] = np.minimum(h[new_chan], lev[new_chan] - a.bed_depth)
    navm = (cls == 3) & inbox
    restored = navm & ~new_chan & (nav_lv - lev > 1e-6)
    lev[restored] = nav_lv[restored]
    navlv_pad = np.pad(np.where(cls == 3, lev, np.nan), 1, constant_values=np.nan)
    sep = np.zeros_like(chan_m)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr or dc:
                nb = navlv_pad[1 + dr:1 + dr + N, 1 + dc:1 + dc + N]
                with np.errstate(invalid='ignore'):
                    sep |= (cls == 7) & inbox & np.isfinite(nb) & (np.abs(nb - lev) > SEPARATION)
    cls[sep], lev[sep] = 0, np.nan
    rep['channel'] = {'axis_m': round(axis.length, 1), 'width_m': a.channel_width, 'lake': lake_name,
                      'level_start_m': round(start_level, 3), 'level_lake_m': lake_level, 'new_vertices': int(new_chan.sum()),
                      'from_land': int((new_chan & (cls0 == 0)).sum()), 'from_pond': int((new_chan & (cls0 == 7)).sum()),
                      'carved_vertices': int((h[new_chan] < h0[new_chan] - 1e-6).sum()),
                      'carve_max_m': round(float((h0 - h)[new_chan].max()), 3) if new_chan.any() else 0.0,
                      'depth_m_min_max': [round(float((lev - h)[new_chan].min()), 3), round(float((lev - h)[new_chan].max()), 3)]}
    rep['navigable_levels_restored'] = {'vertices': int(restored.sum()),
                                        'raise_max_m': round(float((lev - lev0)[restored].max()), 3) if restored.any() else 0.0}
    rep['ponds_to_land'] = {'replaced_strip_vertices': int(strip.sum()), 'replaced_strip_polygons': len(replaced_pond),
                            'separated_vertices': int(sep.sum())}

    # 3. Rounded lakes: straight-sided outlines lose their corners (opening by r, accepted when it stays one polygon
    #    within 0.6 r of the original, i.e. only corners went); stepped contour outlines are Chaikin-smoothed, which
    #    keeps their lobes. A wet vertex left outside goes to land only on a lake bed (not deeper than 2.05 m, the
    #    builder's lake depth) and only when all its wet neighbours belong to the same lake.
    sel = [(n, g, lv) for n, g, lv in lakes if box.contains(g.representative_point())]
    other_wet = np.pad((cls > 0), 1)
    rounded, rl = {}, {}
    for name, g, level in sel:
        r = min(a.round_r, 0.8 * shapely.maximum_inscribed_circle(g).length)
        gr = shapely.make_valid(g.buffer(-r, quad_segs=16).buffer(r, quad_segs=16))
        how = 'opening'
        if gr.geom_type != 'Polygon' or g.hausdorff_distance(gr) > 0.6 * r:
            gr = shapely.make_valid(shapely.Polygon(chaikin_ring(g.exterior.coords), [chaikin_ring(i.coords) for i in g.interiors]))
            how = 'chaikin'
        rounded[name] = gr
        lw = (x >= g.bounds[0] - 6) & (x <= g.bounds[2] + 6) & (z >= g.bounds[1] - 6) & (z <= g.bounds[3] + 6)
        rr, cc = np.nonzero(lw & (cls == 2) & np.isclose(lev, level, atol=1e-4))
        ins = shapely.contains_xy(g, x[rr, cc], z[rr, cc])
        rr, cc = rr[ins], cc[ins]
        d = shapely.distance(gr, shapely.points(x[rr, cc], z[rr, cc]))
        out = (d > a.outside_tol) & ~shapely.contains_xy(gr, x[rr, cc], z[rr, cc])
        foreign = np.zeros(len(rr), bool)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    nr, nc = rr + dr, cc + dc
                    foreign |= other_wet[nr + 1, nc + 1] & ~((cls[nr, nc] == 2) & np.isclose(lev[nr, nc], level, atol=1e-4))
        lakebed = h[rr, cc] >= level - 2.05
        go = out & ~foreign & lakebed & inbox[rr, cc]
        cls[rr[go], cc[go]], lev[rr[go], cc[go]] = 0, np.nan
        rl[name] = {'level_m': level, 'method': how, 'r_m': round(r, 2), 'area_m2': [round(g.area), round(gr.area)],
                    'hausdorff_m': round(g.hausdorff_distance(gr), 2), 'outside': int(out.sum()), 'to_land': int(go.sum()),
                    'kept_touching_other_water': int((out & foreign).sum()), 'kept_deep_bed': int((out & ~foreign & ~lakebed).sum())}
    rep['rounded_lakes'] = rl

    # 4. Banks where water changed (build_v30.py: level_near + 0.35 within 8.5 m, dry floor 1.40), and every such land
    #    vertex above the planes of the cells round it (the pieces gate); untouched banks keep their finish.
    water = cls > 0
    changed_water = water & ((cls != cls0) | ~np.isclose(lev, lev0, equal_nan=True))
    to_land = ~water & (cls0 > 0)
    dist_w, nidx = distance_transform_edt(~water, sampling=6.0, return_indices=True)
    near_lv = lev[nidx[0], nidx[1]]
    dist_c = distance_transform_edt(~(changed_water | to_land), sampling=6.0)
    _, pmax = vertex_plane_bounds(cell_planes(cls, lev, sea_cut=0.51))
    land = ~water & inbox & ((dist_c <= BANK_RADIUS) | to_land)
    floor = np.where(land, DRY_FLOOR, -np.inf)
    floor = np.where(land & (dist_w <= BANK_RADIUS) & np.isfinite(near_lv), np.maximum(floor, near_lv + BANK_MARGIN), floor)
    floor = np.where(land & np.isfinite(pmax), np.maximum(floor, pmax + 0.05), floor)
    raise_m = land & (h < floor)
    h[raise_m] = floor[raise_m]
    rep['banks'] = {'raised_vertices': int(raise_m.sum()), 'raise_max_m': round(float((h - h0)[raise_m].max()), 3) if raise_m.any() else 0.0}
    # Flowing water stays within the builder's cap towards its wet neighbours (0.25 m per 6 m).
    wet_lv = np.pad(np.where(water, lev, np.inf), 1, constant_values=np.inf)
    low = np.full((N, N), np.inf)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr or dc:
                low = np.minimum(low, wet_lv[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] + 0.25 * (1.4142 if dr and dc else 1.0))
    rep['cap_violations_in_box'] = int((np.isin(cls, (3, 5, 6)) & inbox & (lev > low + 1e-6)).sum())
    stand_pad = np.pad(np.where(np.isin(cls, (2, 7)), lev, np.nan), 1, constant_values=np.nan)
    gap = np.zeros_like(water)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr or dc:
                with np.errstate(invalid='ignore'):
                    gap |= (cls == 3) & inbox & (np.abs(stand_pad[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] - lev) > SEPARATION)
    rep['navigable_next_to_standing_over_0_30m'] = int(gap.sum())

    # 5. Signed distance in the box: reproduce the base with the original outlines, then the polished ones.
    sd = np.load(a.sd_base)['sd'].astype(np.float32).copy()
    sd0 = sd.copy()
    reach = box.buffer(200)
    lake_orig = [g for _, g, _ in lakes if g.intersects(reach)]
    keep = [g for g in nav + other + stream_g + ponds if g.intersects(reach)]
    orig = lake_orig + keep
    pol_lakes = [rounded.get(n, g) for n, g, _ in lakes if g.intersects(reach)]
    pol = pol_lakes + [g for g in keep if not any(g.equals(p) for p in replaced_pond)] + [chan_poly]
    win = inbox & np.isfinite(sd0)
    inside_o = raster_vertices(orig).astype(bool)
    rep_sd = signed_distance(orig, x[win], z[win], inside_o[win])
    diff = np.abs(rep_sd - sd0[win])
    rep['sd_reproduction'] = {'vertices': int(win.sum()), 'max_abs_m': round(float(diff.max()), 6),
                              'over_1mm': int((diff > 1e-3).sum())}
    assert rep['sd_reproduction']['over_1mm'] == 0, f"base sd not reproduced in the box: {rep['sd_reproduction']}"
    near_o = binary_dilation(inside_o | np.isin(cls0, (2, 3, 4, 5, 6, 7)), iterations=2)
    inside_p = raster_vertices(pol).astype(bool)
    near_p = binary_dilation(inside_p | np.isin(cls, (2, 3, 4, 5, 6, 7)), iterations=2)
    sup = inbox & (np.isfinite(sd0) | (near_p & ~near_o))
    sd[sup] = signed_distance(pol, x[sup], z[sup], inside_p[sup]).astype(np.float32)
    ch = sup & ~(np.isclose(sd, sd0, atol=1e-4) & np.isfinite(sd0))
    rep['sd'] = {'support_vertices': int(sup.sum()), 'new_support': int((sup & ~np.isfinite(sd0)).sum()),
                 'changed_vertices': int(ch.sum())}

    t['cls'], t['level'], t['heights'] = cls, lev.astype(np.float32), h.astype(np.float32)
    if 'water' in t:
        t['water'] = cls > 0
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out / 'terrain_pilot.npz', **t)
    np.savez_compressed(a.out / 'sd_polish.npz', sd=sd)
    rep['changed'] = {'class': int((cls != cls0).sum()), 'level': int((~np.isclose(lev, lev0, equal_nan=True)).sum()),
                      'heights': int((np.abs(h - h0) > 1e-6).sum()),
                      'outside_box': int(((cls != cls0) | (np.abs(h - h0) > 1e-6) | ~np.isclose(lev, lev0, equal_nan=True))[~inbox].sum())}
    rep['inputs'] = {'terrain_sha256': sha(a.terrain), 'sd_base_sha256': sha(a.sd_base)}
    rep['outputs'] = {'terrain_sha256': sha(a.out / 'terrain_pilot.npz'), 'sd_sha256': sha(a.out / 'sd_polish.npz')}
    rep['params'] = {'channel': a.channel, 'channel_width_m': a.channel_width, 'bed_depth_m': a.bed_depth,
                     'round_r_m': a.round_r, 'outside_tol_m': a.outside_tol}
    (a.out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
