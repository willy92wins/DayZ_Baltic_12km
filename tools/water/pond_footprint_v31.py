"""Pond layer v31, steps S2 and S4 of the 2026-10-11 judge plan: envelope, footprint and visual field.

Cells are the 2047 x 2047 native 6 m cells; cell (r, c) has corners (r, c), (r, c+1), (r+1, c), (r+1, c+1), row 0 north.
Envelope: the base cover cells (cover-level-ev98.npy, pieces unchanged since EV98) plus cells reached in up to two
8-connected geodesic steps whose four corners stand >= P + ENV_CLEAR above the nearest base plane P and touch no
reserve/platform/narva vertex; an added cell takes that nearest plane. It is the freedom domain of a later shoreline pass.
Footprint, a function of the terrain: envelope cells with a corner below their plane (visible), plus up to CLOSE_RINGS
rings of envelope cells incident to a footprint border vertex lying below the highest incident plane + CLOSE_CLEAR, so
the piece edge stays buried. Field: F = make_field(H, plane) per cell corner (copied from Astra's
derive_connected_visual_field.py:12-44 with its submerged_fraction, audit_water_connections.py:14-17): joins planes
across submerged shared edges, keeps dry divides distinct.
Usage: pond_footprint_v31.py <terrain.npz> <cover.npy> <out_dir> [envelope.npy]   (out_dir must not exist)
A given envelope (e.g. with lagoon seals) replaces the computed one; its cells must include every base cover cell.
Writes footprint.npz (env_plane, plane, field[2047,2047,4], visible) and footprint-report.json.
"""
import hashlib, json, os, sys
import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt

ENV_CLEAR, ENV_STEPS = 0.30, 2
CLOSE_RINGS, CLOSE_CLEAR, EDGE_MARGIN = 2, 0.30, 0.05
FIELD_MAX_DEV, SEA_CREST, BED_MIN = 0.35, 0.95, 1.0
N8 = np.ones((3, 3), bool)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def corners(a):
    return a[:-1, :-1], a[:-1, 1:], a[1:, :-1], a[1:, 1:]          # NW, NE, SW, SE


def cells_to_vertices_max(val):
    """Max over the (up to 4) cells incident to each vertex; -inf where none."""
    out = np.full((val.shape[0] + 1, val.shape[1] + 1), -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            sl = (slice(dr, dr + val.shape[0]), slice(dc, dc + val.shape[1]))
            out[sl] = np.maximum(out[sl], val)
    return out


def cells_to_vertices_any(mask):
    out = np.zeros((mask.shape[0] + 1, mask.shape[1] + 1), bool)
    for dr in (0, 1):
        for dc in (0, 1):
            out[dr:dr + mask.shape[0], dc:dc + mask.shape[1]] |= mask
    return out


def vertices_to_cells_any(vmask):
    a, b, c, d = corners(vmask)
    return a | b | c | d


def submerged_fraction(a, b, water):
    """Exact portion of a linear edge strictly below both adjacent water levels (audit_water_connections.py:14-17)."""
    low, high = np.minimum(a, b), np.maximum(a, b)
    return np.where(high - low > 1e-12, np.clip((water - low) / np.maximum(high - low, 1e-12), 0, 1), (water > low).astype(float))


def make_field(h, p):
    """Verbatim from derive_connected_visual_field.py:12-44 (Astra, 2026-10-09)."""
    n = h.shape[0]
    pad = np.pad(p, 1, constant_values=np.nan)
    v = np.stack([pad[:-1, :-1], pad[:-1, 1:], pad[1:, :-1], pad[1:, 1:]])
    finite = np.isfinite(v)
    reach = np.zeros((4, 4, n, n), bool)
    for k in range(4):
        reach[k, k] = finite[k]
    for a, b, dh, dw in [(0, 1, -1, 0), (0, 2, 0, -1), (1, 3, 0, 1), (2, 3, 1, 0)]:
        other = np.roll(h, (-dh, -dw), (0, 1))
        contact = finite[a] & finite[b] & (submerged_fraction(h, other, np.minimum(v[a], v[b])) > 1e-8)
        if dh < 0: contact[0] = False
        if dh > 0: contact[-1] = False
        if dw < 0: contact[:, 0] = False
        if dw > 0: contact[:, -1] = False
        reach[a, b] = reach[b, a] = contact
    for k in range(4):
        for a in range(4):
            for b in range(4):
                reach[a, b] |= reach[a, k] & reach[k, b]
    result = np.full(v.shape, np.nan)
    for a in range(4):
        count = reach[a].sum(axis=0)
        total = np.where(reach[a], np.nan_to_num(v), 0).sum(axis=0)
        high = np.max(np.where(reach[a], v, -np.inf), axis=0)
        target = total / np.maximum(count, 1)
        target = np.where(high > h, np.maximum(target, np.minimum(h + .02, high)), target)
        result[a] = np.where(finite[a], target, np.nan)
    return np.stack([result[3, :-1, :-1], result[2, :-1, 1:], result[1, 1:, :-1], result[0, 1:, 1:]], axis=-1)


def field_checks(h, p, field):
    """Seam and dry-divide checks of derive_connected_visual_field.py:55-80."""
    out = []
    for axis in (0, 1):
        if axis == 0:
            a, b = p[:-1], p[1:]; h0, h1 = h[1:-1, :-1], h[1:-1, 1:]
            aa, bb = field[:-1, :, 2:4], field[1:, :, 0:2]
        else:
            a, b = p[:, :-1], p[:, 1:]; h0, h1 = h[:-1, 1:-1], h[1:, 1:-1]
            aa, bb = field[:, :-1, :][:, :, [1, 3]], field[:, 1:, :][:, :, [0, 2]]
        both = np.isfinite(a) & np.isfinite(b)
        before = submerged_fraction(h0, h1, np.minimum(a, b))
        wet = both & (before > 1e-8)
        diff = np.max(np.abs(aa - bb), axis=-1)
        x0 = aa[:, :, 0] - h0; x1 = aa[:, :, 1] - h1; y0 = bb[:, :, 0] - h0; y1 = bb[:, :, 1] - h1
        def interval(d0, d1):
            crossing = np.clip(-d0 / np.where(abs(d1 - d0) > 1e-12, d1 - d0, 1), 0, 1)
            lower = np.where((d0 <= 0) & (d1 > 0), crossing, 0.)
            upper = np.where((d0 > 0) & (d1 <= 0), crossing, 1.)
            upper = np.where((d0 <= 0) & (d1 <= 0), 0., upper)
            return lower, upper
        al, ah = interval(x0, x1); bl, bh = interval(y0, y1)
        after = np.maximum(0, np.minimum(ah, bh) - np.maximum(al, bl))
        extra = both & (before <= 1e-8) & (after > 1e-8)
        dry_div = both & (a != b) & ~wet
        out.append(dict(axis=axis, wet_contacts=int(wet.sum()), max_wet_seam_m=float(np.max(diff[wet], initial=0)),
                        new_contacts_on_dry_divides=int(extra.sum()), dry_divides=int(dry_div.sum())))
    return out


def main():
    terrain, cover_path, out = sys.argv[1:4]
    env_path = sys.argv[4] if len(sys.argv) > 4 else None
    assert not os.path.exists(out), "fresh output required"
    os.makedirs(out)
    z = np.load(terrain)
    H = z["heights"].astype(np.float64)
    frozen = z["reserve"] | z["platform"] | z["narva"]
    cover = np.load(cover_path).astype(np.float64)
    base = np.isfinite(cover)
    cmin = np.minimum.reduce(corners(H))
    cell_frozen = vertices_to_cells_any(frozen)
    # S2 envelope
    _, (ri, ci) = distance_transform_edt(~base, return_indices=True)
    nearP = cover[ri, ci]
    cand = ~base & ~cell_frozen & (cmin >= nearP + ENV_CLEAR)
    env = base.copy()
    for _ in range(ENV_STEPS):
        env |= binary_dilation(env, N8) & cand
    env_plane = np.where(base, cover, np.where(env, nearP, np.nan))
    if env_path:
        env_plane = np.load(env_path).astype(np.float64)
        env = np.isfinite(env_plane)
        assert env[base].all(), "given envelope must contain every base cover cell"
    # S4 footprint
    visible = env & (cmin < env_plane)
    fp = visible.copy()
    rings = []
    for _ in range(CLOSE_RINGS):
        vin = cells_to_vertices_any(fp)
        vout = cells_to_vertices_any(~fp) | np.pad(np.zeros((2046, 2046), bool), 1, constant_values=True)
        vP = cells_to_vertices_max(np.where(fp, env_plane, -np.inf))
        need = vin & vout & (H < vP + CLOSE_CLEAR)
        add = env & ~fp & vertices_to_cells_any(need)
        rings.append(int(add.sum()))
        if not add.any():
            break
        fp |= add
    plane = np.where(fp, env_plane, np.nan)
    vin = cells_to_vertices_any(fp)
    vout = cells_to_vertices_any(~fp) | np.pad(np.zeros((2046, 2046), bool), 1, constant_values=True)
    vP = cells_to_vertices_max(np.where(fp, plane, -np.inf))
    border = vin & vout
    exposed = border & (H < vP + EDGE_MARGIN)
    low_margin = border & (H < vP + CLOSE_CLEAR)
    field = make_field(H, plane)
    assert np.isfinite(field[fp]).all()
    dev = np.abs(field - plane[:, :, None])
    checks = field_checks(H, plane, field)
    # G7 bed and level
    vmax_F = cells_to_vertices_max(np.where(fp[:, :, None], field, -np.inf).max(axis=-1))
    bed_low = vin & (H < BED_MIN) & (H < np.maximum(vmax_F, vP))
    rep = dict(schema="pond-footprint-v31.v1", terrain=terrain, terrain_sha256=sha(terrain), cover=cover_path, cover_sha256=sha(cover_path),
               envelope=env_path, envelope_sha256=sha(env_path) if env_path else None,
               params=dict(ENV_CLEAR=ENV_CLEAR, ENV_STEPS=ENV_STEPS, CLOSE_RINGS=CLOSE_RINGS, CLOSE_CLEAR=CLOSE_CLEAR,
                           EDGE_MARGIN=EDGE_MARGIN, FIELD_MAX_DEV=FIELD_MAX_DEV),
               base_cells=int(base.sum()), envelope_added=int((env & ~base).sum()), envelope_cells=int(env.sum()),
               visible_cells=int(visible.sum()), closure_added_per_ring=rings, footprint_cells=int(fp.sum()),
               footprint_outside_base=int((fp & ~base).sum()), base_cells_dropped=int((base & ~fp).sum()),
               min_plane=float(np.nanmin(plane)), border_vertices=int(border.sum()), exposed_border_lt_0p05=int(exposed.sum()),
               border_lt_0p30=int(low_margin.sum()), field_dev_max=float(np.nanmax(dev)),
               field_corners_over_0p35=int(np.count_nonzero(dev > FIELD_MAX_DEV + 1e-9)),
               field_corners_changed_over_1mm=int(np.count_nonzero(dev > 1e-3)), field_checks=checks,
               bed_below_1m_under_water=int(bed_low.sum()),
               exposed_xz=[[6 * int(c), 6 * (2047 - int(r))] for r, c in np.argwhere(exposed)[:200]],
               over035_xz=[[6 * int(c), 6 * (2047 - int(r))] for r, c, _ in np.argwhere(dev > FIELD_MAX_DEV + 1e-9)[:50]])
    np.savez(os.path.join(out, "footprint.npz"), env_plane=env_plane.astype(np.float32), plane=plane.astype(np.float32),
             field=field.astype(np.float64), visible=visible)
    with open(os.path.join(out, "footprint-report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if not k.endswith("_xz")}, indent=1))


if __name__ == "__main__":
    main()
