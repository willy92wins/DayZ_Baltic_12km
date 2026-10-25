"""BALTIC-015 (Guillermo, 2026-10-11: vanilla bridges by width): place a vanilla bridge where a road crosses a stream on a
dry embankment, open the channel under its span and seal that channel into the v31 pond envelope.

Per site (JSON list: id, x, z, road bearing deg, model, level, water bearing deg, width m, optional spans = 1 or 2,
optional stack = true):
  model     DZ\\structures\\roads\\bridges\\<model>.p3d, read from its ODOL: length axis (X for wood, Z for metal), roadway
            end heights at +-half length, centre of the roadway in model coordinates. Only models with a verified seat
            (SEATS) are accepted; anything else is refused, as is a model without an exact roadway (3e15) or visual
            (1.0) LOD or whose seat does not pass the checks in seat_*().
  variant   a model in VARIANTS (bridge_wood_50_1: the tall vanilla wood_50, roadway 1.301 m higher in the model) is posed
            and cut exactly as its base model, then moved down its own Y axis by the measured roadway offset, so the
            world roadway stays where the base model's is (015-42: wood_50 legs hung up to 3.3 m over the cut gully).
  pose      length axis along the road bearing, pitched so both roadway ends sit on the road terrain (world = position +
            R . ODOL vertex, the convention of the WRP records; matrix = local X, Y, Z axes as columns, then position).
            Each end height is the road terrain on the axis, or, where the terrain under the deck end strip (full deck
            width at the end, END_IN m inward, less the deck's rise along its pitch) stands higher, that terrain +
            END_CLEAR: a deck wider than the road
            (bridge_metal_25: 14.2 m) sat with one corner a few cm inside a cross-sloped road (Guillermo, 15-10, 015-8).
            With spans = 2 (the 015 plan's 'bridge_metal_25 x2') two copies stand end to end on one straight pitched line
            between the two outer roadway ends; each span's centre height is interpolated on that line.
  stack     stack = true adds a second copy of the same model, same axes, STACK_DY m lower along its Y axis (record role
            'stack-lower'): the upper legs' feet (y -2.603..-2.524) stand on the lower copy's kerbs (2.56/2.60), the
            posts line up, and the lower legs reach the ground where a single trestle hung up to 4.8 m over the cut
            gully (Guillermo, 15-10, 015-16: 'apilar un puente debajo').
  channel   q = distance to the water axis through the site, t = distance along it: H = min(H, bed + BANK (|q| - W/2)) for
            |t| <= CUT_T, bed = max(1.0, level - 0.5); this may lower reserve/platform vertices, but only under the deck
            (|s| <= flat half-span along the road), which is the explicit exception of the plan.
  seals     cells within W/2 + 6 m of the water axis and |t| <= CUT_T take the stream level in the envelope.
  corridor  the road reserve band is often far wider than the deck (015-16: 24 m against 8 m), so the channel is opened
            through the whole band under the deck's length (frozen vertices with |s| <= flat half-span, any lateral offset;
            limiting it to the deck width left the shoulders as dams). The cut reaches, on each side separately,
            max(25 m, the far end of the frozen run met along the water axis + 6 m, the first point where the terrain within
            3 m of the axis is below the stream level + 4 m), capped at 60 m: a fixed 25 m stopped short of the band on
            oblique or wide crossings (015-4) and of the water beyond the EV102 road cones (015-13/16/40: water resumed at
            ~30 m), leaving dams and, against them, sealed pond edges.
  link      the inventory's water bearing is a chord: where no water lies on the straight axis on one side within 60 m,
            the channel is also carved (same width and banks, frozen vertices untouched) and sealed along a straight
            segment from the axis just beyond the frozen run to the nearest wet vertex of an envelope cell at the stream
            level on that side (015-16 north, 015-40 south: the natural channel ran 6-12 m beside the axis).
            Since v6 the corridor/link cut above is the v4 REFERENCE only (openings, *_v4 report values, the frozen
            vertices a cut may lower); the terrain is cut by the curved channel below.
  slopes    a changed triangle steeper than max(35 deg, before) has its highest vertex lowered in 0.1 m steps when that
            vertex is neither channel floor (|q| <= W/2 from the axis or a link) nor frozen and lies within 2 vertices of
            the edit (80 passes): the wall is laid back; the channel floor and the frozen embankment never move. Steep faces where the frozen embankment meets the
            channel under the deck (the abutments) stay: the bridge stands over them, as in Chernarus.
            This pass, run after all sites, gives the v4 terrain (kept internally as the reference of the water checks).
  sea mode  when the water on the axis within CUT_T is engine sea (terrain < 0.75 m outside every envelope cell; EV96 turned
            many low reaches into sea), the bed is SEA_BED below the sea and no seal is written: the engine sea fills the
            channel, so no pond piece ever covers sea water (the two-colour rule of 11-10).
  end fit   (v5) after all cuts and the v4 slope pass, one joint raise-only solve (linear programme over vertex raises,
            every site at once, so overlapping sites cannot undo each other) on the planar NW-SE triangles, with the real
            ODOL faces transformed by each record and cut by the triangle edges (each piece lies in one triangle, where
            terrain and face are both linear, so the piece vertices give the exact extremes):
              abutment  bridge_metal_25: no face of the visual-LOD pier block at an outer end may stand more than
                        FACE_TOL above the terrain (015-13: the oblique cut left a 6 m triangle that bared the block's inner
                        corner by 1.17 m; the prototype's 0.5 m samples missed a 0.049 m residual).
              ramp      wood bridges: under the visual-LOD underside of each outer ramp, from the tip to the first pile bent
                        (4.0-4.5 m), the terrain rises toward underside - RAMP_AIR, never above underside - RAMP_CAP where
                        it was not already higher, with soft 1:WING wings beside it (the ramp rises 0.30 m/m from the
                        road: ~1 m of air at the first bent on all 14 ramps before any cut; Chernarus median 0).
                        Within reach only where the cut lowered the ground: on the 6 m grid a triangle that crosses the
                        tip carries the road vertex beyond it, and the deck rule below keeps it from tilting up 0.30 m/m.
              legs      every foot of a lower stack copy and of a variant model must touch the terrain (LEG_TOL).
              deck      a raise never brings the terrain above any deck (roadway LOD) face - DECK_CLEAR.
            A raise is never more than a row needs (deficit / weight, weights >= 0.05) nor OVER_MAX above that row's bound.
            Never raised: vertices under the stream level, the sea or an envelope cell (the wet set and its connectivity
            stay), frozen vertices outside the support of a bridge footprint (the triangles under the visual LOD's plan
            rectangle) and the map border. Where a raise narrows the opening (narrowest wet width across the water axis
            under the deck, exact on the planar triangles, sections every 0.1 m) below the v4 terrain's, free bank vertices
            (dry, cut-allowed by the v4 rules, not held by a fit row) are lowered toward the bed, best gain first, each
            only as far as the narrowed sections need, until it is back (no overshoot, so the opening is continuous in
            W); if that fails, the raises of that site are reverted and given back one at a time, least harmful first,
            each as far as the opening allows (bisection), the shortfall kept as a cap on that vertex, and the solve
            repeats. No width
            threshold: the prototype's W < 6 m neighbour rule dropped a 015-25 fixture from 4.1 to 1.3 m at W = 6.0.
            The slope pass then runs again; it never lowers a vertex if that would break a satisfied fit row or deepen a
            broken one. Every row is measured again on the final terrain and reported per end and per site (deck end
            strips, every deck face, abutment faces, ramp air, legs; stuck triangles counted by triangle, not by cell).
            Frozen vertices: the fill only raises inside the footprint support; the v4 corridor cut above still lowers
            frozen channel vertices beyond it (|s| <= flat, any lateral offset), unchanged from v4.
  end zone  (v6; Guillermo, 17-10, 015-13: 'subiste un poco la esquina bajada, pero hay que nivelarlo un poco mejor': under the
            deck end the ground still fell toward the channel across the deck and bared the slab) every outer end gets a
            hard fit row family over its deck-end zone: from the end to the abutment face (block seat: the block's inner
            face, 3.380 m on bridge_metal_25) or the first pile bent (ramp seat), across the whole width there (visual LOD
            within END_DEPTH of the underside and every roadway-LOD vertex, kerbs and the metal block pads: +-8.80 m metal,
            -4.33..+4.02 m wood), the terrain >= underside plane - END_AIR (end_zone(): the ramp's fitted slab underside,
            or the metal deck slab, 7.650, the lowest visual face within END_DEPTH under the roadway, refused unless flat
            and planar to 0.02 m). Beyond the zone and beside it soft 1:WING wings fall toward the channel (only over
            points above the level + 0.3). No cap on the zone fill: a cap at the underside (ub = terrain where the ground
            was already higher) blocked every raise of a triangle shared with the 8.0 m road ground (015-13 kept 1.17 m
            of bare block face); the deck rows (roadway - DECK_CLEAR) and the v5 ramp caps on the real slab faces stay.
            Wood ramps stay out of reach as in v5 (the tip's slope break needs a grid line the 6 m triangles do not have).
  curve     (v6; Guillermo, 17-10: 'la parte del rio a ambos lados del puente cerca le falta smoothing': the straight cut met
            the natural river with polygonal kinks on both sides) channel_v6() per site and side:
              straight  the v4 section stays straight under the deck, to the opening sections (+-td) + 3 m and, on a
                        legged (wood) deck, over the whole footprint crossed by the channel strip + 3 m (no leg over a bend;
                        bridge_metal_25 spans clear: straight to 22.7 m left 015-13 a 49 deg hairpin into its pool).
              track     from there (S) track_natural() follows the natural stream (input terrain under the level inside
                        an envelope cell at the level; a look-ahead every TRACK_STEP m, turned up to 60 deg, run nearest
                        the look point, TRACK_GAPS dry steps allowed).
              join      each tracked point beyond S + CURVE_MIN, moved to the centroid of the input water within 5 m
                        (recentre(): a centre on the far edge of a pool put the 015-13 join against the road platform), is
                        a candidate J; its direction is natural_dir(), J to the centroid of the input water 3-18 m ahead
                        (the tracker's local direction missed a wide reach by 54 deg, 015-11 north). fair_curve() builds
                        the cubic Hermite S -> J, tangent at both ends, with the end-tangent scales (HERMITE_K x HERMITE_K)
                        giving the smallest largest turning between TURN_CHORD m chords (6 m lead-in and lead-out included).
              choice    a candidate conflicts where a vertex it may not cut lies inside its waterline or where its 0.5 m
                        path cannot be made wet (WET_MARGIN) even with every vertex it may cut at its lowest permitted
                        height and the straight cut applied (015-19: a curve leaving the axis inside the frozen band met
                        the uncut platform, +6.7 m). The straight part grows in 3 m steps up to the v4 cut's own extent
                        until a conflict-free curve turns <= TURN_TOOL; else the best by (conflict, turning > TURN_GATE,
                        turning > TURN_TOOL, turning, straight length) is kept (015-13 east, a pool beside the road, and
                        015-25 north end near 29 deg).
              section   the v4 bank (bed + BANK (d - wb/2)), bed width blended (smoothstep) from W to the natural width
                        at J (median run width of the 5 tracked points around J, clamped), rising BANK per m past J.
                        A curve lowers only free vertices and frozen ones the v4 cut lowered, never kit, lagoon or a
                        vertex under a hard fit row of any site (015-42: a curve under a wood_50_1 leg left it 0.074 m in
                        the air), and never below hmin: beside a vertex it may not lower, that vertex's height minus
                        0.8 tan(SLOPE_MAX) times 6 m (8.49 m on a diagonal).
              wet path  the planar terrain along the centreline (0.5 m samples) must be WET_MARGIN under the level; a dry
                        neck lowers the allowed vertex with the largest weight to its hmin (narrow oblique sections bead
                        into pools on the 6 m grid, 015-16). Islets: a dry vertex a curve touched with all 6 native-edge
                        neighbours wet goes WET_MARGIN under the level (015-13 east: +0.14 m in the pool mouth).
              guard     no triangle a curve, the wet path or an islet lowered ends steeper than max(SLOPE_MAX, input):
                        those vertices come back in 0.1 m steps, channel floor last, never above their height after the v4
                        section; the v4 section itself is never raised (raising it closed 015-19's opening to 0.2 m).
              seals     cells within the waterline + SEAL_OUT of the straight part or a curve, added to the v4 seals,
                        which are kept: v4-cut frozen vertices a curve leaves at the old axis became footprint border
                        vertices under the plane that bury_edges_v31 could not bury (015-16, 015-40).
            The v4 links are replaced; a side where no natural water is tracked (or sea mode) keeps the v4 straight cut
            and link. The slope pass, then the end fit, run on this terrain, both with the slope cap (a lay-back step that
            would leave a triangle steeper than max(SLOPE_MAX, input) and steeper than before is refused: laying back one
            wall steepened its neighbour against a frozen top, 015-13 pool end); the openings, the *_v4 values and the
            compensation targets stay the v4 terrain's.
  v6r2      (review of 18-10, EV112 review 1)
              input     refused unless heights are a finite (2048, 2048) float array, the frozen masks (2048, 2048) booleans,
                        the envelope (2047, 2047) levels or NaN and the sites a non-empty list of distinct ids; the output
                        heights are checked finite before anything is written (a NaN at heights[34, 1315] went through, exit 0).
              wet path  on the straight part it may also lower the vertices the v4 rule lets the cut lower (frozen ones only
                        under a footprint or where v4 cut them) and vertices under seat rows (abutment faces, deck-end
                        zones, ramps, legs), each only as far as every seat row through it stays satisfied, to a floor taken
                        from its fixed neighbours' heights after the v4 section; the cells around every vertex it takes under
                        the level are sealed (v6 left the axis dry under the deck over 4.1 m at 015-18 and 3.3 m at 015-40,
                        their two mouths in different water bodies: the lower copies' leg rows, which only ask terrain >=
                        foot - LEG_TOL, held the channel vertices beside them, and the v4 section's 1:2 banks on a 6 m grid
                        left 5.5-6.3 m channels above the level between vertex rows).
              path      the end fit gets one upper row per 0.5 m sample of each site's centreline: no raise may lift the
                        planar terrain there above level - PATH_UB (or above its current value where it is higher); only
                        samples already under the level get a row (a dry one has no water to keep, and in the overlap fixture
                        015-13b's dry path under 015-13's abutment block held the block's ground 1.17 m low).
              wings     the 1:WING wings are hard rows (v6: soft, 015-13 end 0 left 0.21-0.58 m under the profile), built on
                        exact polygons (beyond the zone WING_BEYOND m toward the channel across its width; beside it WING_SIDE
                        m out; cut where the profile falls to level + 0.3), and a wing row lets its vertices rise up to the
                        wing's top (zone plane - END_AIR) instead of OVER_MAX over the row; they do not hold the channel
                        (only seat rows make a vertex 'held' for the curves and the wet path), and the shore cap and the
                        opening still win over them. Wood ramps stay out of reach (the same 6 m tip triangles as their zone).
Outputs: terrain (v31_bridge_cut = every vertex this pass changed, lowered or raised, OR earlier cuts; v31_bridge_fill =
vertices left above their input height, OR earlier fills), envelope (v4 seals + the v6 seals), records (upper records exactly
as v4 except a variant's model and position; stack copies after their upper record), report (schema bridges-v31.v6: per
end 'zone' (air over the deck-end zone) and 'wings' (v6r2: deficit under the 1:WING profile), per site 'channel' (straight
part, sides with join, turning, widths, wet path, the centreline at 1 m, v6r2 'final_path': its 0.5 m samples on the final
terrain), opening_m v4 / base (v6 channel terrain) / v5 (= this run's, key kept for the v5 gates); 'revision' v6r2).
Usage: bridges_v31.py <terrain.npz> <envelope.npy> <sites.json> <out_terrain.npz> <out_envelope.npy> <records.json> <report.json>
"""
import json, math, sys
import numpy as np
from scipy.ndimage import binary_dilation
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
from odol_reader import ODOL

BANK, CUT_T, BED_MIN, ZTOP = 0.5, 25.0, 1.0, 12282
END_IN, END_CLEAR = 2.0, 0.02
SEA, SEA_BED = 0.75, 0.0
STACK_DY = 5.04                                     # lower copy offset along model Y; contact window 4.993..5.084 (LOD 1)
FACE_TOL, RAMP_CAP, RAMP_AIR, LEG_TOL, DECK_CLEAR, WING = 0.01, 0.05, 0.09, 0.04, 0.015, 1.5
FIT_ROUNDS = 16
OPEN_MARGIN = 1e-5                                  # compensation and caps aim this far above the v4 opening
SLOPE_MAX = 55.0                                    # no fit raise or widening cut leaves a triangle steeper than this
OVER_MAX = 1.0                                      # a raised vertex stands at most this above the bound it serves
END_AIR, END_DEPTH = 0.09, 0.6                      # v6 deck-end zone: air target, slab search depth under the roadway
WING_REACH = (0.5, 1.0, 2.0, 3.0, 4.5, 6.0, 8.0, 10.0, 12.0)   # v6 wing samples beyond the zone (m; report only since v6r2)
WING_BEYOND, WING_SIDE = 12.0, 6.0                  # v6r2 exact wing polygons: reach beyond the zone and beside it (m)
TRACK_STEP, TRACK_SEARCH, TRACK_MAX, TRACK_GAPS = 4.0, 14.0, 95.0, 8   # v6 natural channel tracking (m, m, m, steps)
CURVE_MIN, TURN_CHORD, TURN_TOOL, TURN_GATE = 12.0, 6.0, 20.0, 30.0   # v6 shortest curve, turning chord (m), target, limit (deg)
SEAL_OUT = 5.0                                       # v6 seal reach beyond the waterline (v4: W/2 + 6 from the axis)
WET_MARGIN = 0.15                                    # v6 the centreline path stays this far under the level
HERMITE_K = (0.25, 0.35, 0.5, 0.7, 1.0, 1.4, 2.0)             # v6 end-tangent scales tried for each curve
PATH_UB = 0.05                                       # v6r2 the fit keeps the centreline at least this under the level
WING_SOFT = False                                    # v6r2 wing rows are hard (v6: soft, left 0.21-0.58 m short at 015-13)
KEEP_KINDS = ("face", "ramp", "zone", "leg")         # v6r2 hard rows a wet-path lowering may not break nor deepen
DZ = "P:/DZ/structures/roads/bridges"
SEATS = {"bridge_metal_25": "block", "bridge_wood_25": "ramp", "bridge_wood_50": "ramp", "bridge_wood_50_1": "ramp"}
VARIANTS = {"bridge_wood_50_1": "bridge_wood_50"}
GN = 2048
_MODELS = {}


def refuse(msg):
    raise SystemExit(f"bridges_v31: refused: {msg}")


def lod_exact(od, res, name):
    c = [l for l in od.lods if abs(l.resolution - res) <= 1e-6 * max(1.0, abs(res))]
    if len(c) != 1:
        refuse(f"{name}: no single LOD with resolution {res:g}")
    return c[0]


def welded(l):
    """Vertices, per-vertex welded component label, triangles (n, 3, 3) and their component labels."""
    V = np.array([(p.x, p.y, p.z) for p in l.vertices], float)
    U, inv = np.unique(V.round(4), axis=0, return_inverse=True); inv = inv.ravel()
    a, b, tris, tv = [], [], [], []
    for f in l.faces:
        ids = list(f.vertex_indices)
        for j in ids[1:]:
            a.append(inv[ids[0]]); b.append(inv[j])
        for i in range(1, len(ids) - 1):
            tris.append(V[[ids[0], ids[i], ids[i + 1]]]); tv.append(ids[0])
    _, lab = connected_components(coo_matrix((np.ones(len(a)), (a, b)), shape=(len(U), len(U))), directed=False)
    vl = lab[inv]
    return V, vl, np.array(tris), vl[np.array(tv)]


def top_at(tris, x, z, lowest=False):
    """Highest (or lowest) triangle hit of vertical rays; nan where none."""
    best = np.full(np.shape(x), np.nan)
    for A, B, C in tris:
        m = np.array([[B[0] - A[0], C[0] - A[0]], [B[2] - A[2], C[2] - A[2]]])
        if abs(np.linalg.det(m)) < 1e-12:
            continue
        iv = np.linalg.inv(m); u = iv[0, 0] * (x - A[0]) + iv[0, 1] * (z - A[2]); w = iv[1, 0] * (x - A[0]) + iv[1, 1] * (z - A[2])
        ins = (u >= -1e-9) & (w >= -1e-9) & (u + w <= 1 + 1e-9); y = A[1] + u * (B[1] - A[1]) + w * (C[1] - A[1])
        best = np.where(ins & ~((best <= y) if lowest else (best >= y)), y, best)
    return best


def seat_block(tris, tl, V, vl, ax, lat, e, inw, y_end, c_lat, half_w, name):
    a = (V[:, ax] - e) * inw
    deep = [k for k in np.unique(vl) if V[vl == k, 1].min() < y_end - 5 and a[vl == k].min() <= 0.1 and a[vl == k].max() < 8]
    if len(deep) != 1:
        refuse(f"{name}: {len(deep)} pier blocks flush with the end at {e:g}")
    k = deep[0]; p = V[vl == k]; pa = a[vl == k]
    top, a_in, hw = float(p[:, 1].max()), float(pa.max()), float(np.abs(p[:, lat] - c_lat).max())
    if not (y_end - 2.5 <= top <= y_end - 1.0 and 2.5 <= a_in <= 5.0 and hw <= half_w + 0.1 and p[:, 1].min() < top - 5):
        refuse(f"{name}: unverified pier block at {e:g} (top {top:.3f}, roadway {y_end:.3f}, length {a_in:.2f}, half width {hw:.2f})")
    return dict(kind="block", faces=tris[tl == k], top=top, a_in=a_in, hw=hw)


def seat_ramp(tris, tl, V, vl, ax, lat, e, inw, y_end, c_lat, road_tris, name):
    a = (V[:, ax] - e) * inw
    slabs = [k for k in np.unique(vl) if a[vl == k].min() <= 0.5 and np.ptp(a[vl == k]) > 3 and V[vl == k, 1].min() > y_end - 0.6]
    if not slabs:
        refuse(f"{name}: no ramp slab at {e:g}")
    k = max(slabs, key=lambda q: np.ptp(a[vl == q])); st = tris[tl == k]
    nrm = np.cross(st[:, 1] - st[:, 0], st[:, 2] - st[:, 0]); flat = np.abs(nrm[:, 1]) > 0.7 * np.linalg.norm(nrm, axis=1)
    cen = st.mean(1); above = top_at(st, cen[:, 0], cen[:, 2])
    bottom = st[flat & (above > cen[:, 1] + 0.05)]                                    # a slab face with slab above it
    if len(bottom) < 2:
        refuse(f"{name}: no ramp underside at {e:g}")
    ba = (bottom[..., ax] - e) * inw
    s1, y1 = np.polyfit(ba.ravel(), bottom[..., 1].ravel(), 1)
    others = (vl != k) & (a > 0.5) & (V[:, 1] < y1 + s1 * a - 0.05)                     # first pile bent below the slab
    a_seat = float(a[others].min()) if others.any() else np.inf
    faces = [P for P in (clip_le(T, (T[:, ax] - e) * inw, a_seat) for T in bottom) if len(P) >= 3]
    fv = np.concatenate(faces) if faces else np.zeros((0, 3))
    res = float(np.abs(fv[:, 1] - (y1 + s1 * (fv[:, ax] - e) * inw)).max()) if len(fv) else np.inf
    ra = np.linspace(0.5, min(a_seat, 4.0), 8)
    rx = np.zeros((len(ra), 3)); rx[:, ax] = e + inw * ra; rx[:, lat] = c_lat
    gap = top_at(road_tris, rx[:, 0], rx[:, 2]) - (y1 + s1 * ra)
    if not (3.5 <= a_seat <= 5.0 and res <= 0.02 and 0.27 <= s1 <= 0.34 and np.all((gap >= 0.2) & (gap <= 0.45))):
        refuse(f"{name}: unverified ramp at {e:g} (first bent {a_seat:.2f} m, slope {s1:.4f}, fit residual {res:.3f}, roadway-underside {np.nanmin(gap):.3f}..{np.nanmax(gap):.3f})")
    lv = fv[:, lat] - c_lat
    return dict(kind="ramp", faces=faces, a_seat=a_seat, y0=float(y1), slope=float(s1), fit_residual=res,
                lat_lo=float(lv.min()), lat_hi=float(lv.max()), road_gap=[float(np.nanmin(gap)), float(np.nanmax(gap))])


def end_zone(tris, V, road_v, ax, lat, e, inw, y_end, c_lat, road_half, seat, name):
    """(v6) Deck-end zone of one outer end: from the end to the abutment face (block seat: the block's inner face) or to
    the first pile bent (ramp seat), across the whole visual-LOD width there (deck, kerbs and rails), under an underside
    plane y = y0 + slope * a (a = metres inward from the end). Ramp: the seat's fitted slab underside. Block: the lowest
    visual face within END_DEPTH under the roadway, sampled over the zone (bridge_metal_25: the deck slab, 7.650), refused
    unless flat and planar to 0.02 m."""
    if seat["kind"] == "ramp":
        a_end, y0, s, res = seat["a_seat"], seat["y0"], seat["slope"], seat["fit_residual"]
    else:
        a_end = seat["a_in"]
        hi = tris[tris[..., 1].min(1) >= y_end - END_DEPTH]
        A_, L_ = np.meshgrid(np.linspace(0.3, a_end - 0.3, 9), np.linspace(-0.7 * road_half, 0.7 * road_half, 9), indexing="ij")
        P = np.zeros(A_.shape + (3,)); P[..., ax] = e + inw * A_; P[..., lat] = c_lat + L_
        y = top_at(hi, P[..., 0], P[..., 2], lowest=True); ok = np.isfinite(y)
        if ok.sum() < 0.9 * ok.size:
            refuse(f"{name}: no deck underside over the end zone at {e:g}")
        s, y0 = np.polyfit(A_[ok], y[ok], 1); res = float(np.abs(y[ok] - (y0 + s * A_[ok])).max())
        if res > 0.02 or abs(s) > 0.02:
            refuse(f"{name}: deck underside at {e:g} not planar (residual {res:.3f}, slope {s:.4f})")
    a = (V[:, ax] - e) * inw
    sel = (a >= -1e-6) & (a <= a_end + 1e-6) & (V[:, 1] >= y0 + s * np.clip(a, 0, a_end) - END_DEPTH)
    ar = (road_v[:, ax] - e) * inw
    lv = np.r_[V[sel, lat], road_v[(ar >= -1e-6) & (ar <= a_end + 1e-6), lat]] - c_lat      # visual and roadway LOD (kerbs)
    return dict(a_end=float(a_end), y0=float(y0), slope=float(s), residual=float(res), lat_lo=float(lv.min()), lat_hi=float(lv.max()))


def model_info(name):
    if name in _MODELS:
        return _MODELS[name]
    if name not in SEATS:
        refuse(f"{name}: no verified seat (known: {', '.join(sorted(SEATS))})")
    od = ODOL.from_file(f"{DZ}/{name}.p3d")
    road = min(od.lods, key=lambda l: abs(l.resolution - 3e15))
    lod_exact(od, 3e15, name)
    v = np.array([(p.x, p.y, p.z) for p in road.vertices])
    ax = 0 if np.ptp(v[:, 0]) >= np.ptp(v[:, 2]) else 2
    lat = 2 - ax
    lo, hi = v[:, ax].min(), v[:, ax].max()
    ends = [float(v[np.abs(v[:, ax] - e) < 0.6, 1].max()) for e in (lo, hi)]
    c_lat = (v[:, lat].max() + v[:, lat].min()) / 2
    end_w = max(float(np.abs(v[(np.abs(v[:, ax] - e) < 0.6) & (v[:, 1] >= y - 0.3), lat] - c_lat).max()) for e, y in zip((lo, hi), ends))
    m = dict(axis=ax, half=(hi - lo) / 2, centre_len=(hi + lo) / 2, centre_lat=c_lat,
             end_y=ends, deck_max=float(v[:, 1].max()), width=float(np.ptp(v[:, lat])), end_half_w=end_w)
    # v5: deck faces (roadway faces at or above the lower roadway end), visual LOD 1 seats, legs and plan bbox
    rt = np.array([v[[f.vertex_indices[0], f.vertex_indices[i], f.vertex_indices[i + 1]]] for f in road.faces for i in range(1, len(f.vertex_indices) - 1)])
    m["deck_faces"] = rt[rt[..., 1].min(1) >= min(ends) - 0.01]
    vis = lod_exact(od, 1.0, name)
    V, vl, tris, tl = welded(vis)
    kind = SEATS[name]
    m["seats"] = [seat_block(tris, tl, V, vl, ax, lat, e, inw, y, c_lat, m["width"] / 2, name) if kind == "block" else
                  seat_ramp(tris, tl, V, vl, ax, lat, e, inw, y, c_lat, rt, name)
                  for e, y, inw in ((lo, ends[0], 1.0), (hi, ends[1], -1.0))]
    rs = [float(np.abs(v[(np.abs(v[:, ax] - e) < 0.6) & (np.abs(v[:, 1] - y) < 0.05), lat] - c_lat).max()) for e, y in zip((lo, hi), ends)]
    m["zones"] = [end_zone(tris, V, v, ax, lat, e, inw, y, c_lat, r_, st, name)
                  for (e, y, inw), r_, st in zip(((lo, ends[0], 1.0), (hi, ends[1], -1.0)), rs, m["seats"])]
    ymin = V[:, 1].min(); legs = []
    for k in np.unique(vl):
        p = V[vl == k]
        if p[:, 1].min() < ymin + 0.3 and kind == "ramp":
            legs.append(np.unique(p[p[:, 1] < p[:, 1].min() + 0.05].round(4), axis=0))
    m["legs"] = legs
    m["legs_over_stack"] = [float(F[:, 1].min() - np.nanmax(top_at(tris, F[:, 0], F[:, 2]) - STACK_DY)) if np.isfinite(top_at(tris, F[:, 0], F[:, 2])).any() else np.inf
                            for F in legs]
    m["roadway_lo_hi"] = (float(lo), float(hi))
    m["bbox"] = (V.min(0), V.max(0))
    m["road_vertices"] = v
    _MODELS[name] = m
    return m


def variant_offset(base, var, name):
    """Model-Y offset of a variant's roadway over its base's; refused unless the roadways are congruent to 3 mm."""
    a, b = base["road_vertices"], var["road_vertices"]
    if len(a) != len(b):
        refuse(f"{name}: roadway vertex count differs from its base")
    sa, sb = a[np.lexsort((a[:, 2], a[:, 0]))], b[np.lexsort((b[:, 2], b[:, 0]))]
    dy = float(np.mean(sb[:, 1] - sa[:, 1]))
    if np.abs(sb[:, [0, 2]] - sa[:, [0, 2]]).max() > 0.003 or np.abs(sb[:, 1] - sa[:, 1] - dy).max() > 0.003:
        refuse(f"{name}: roadway is not its base's moved along Y")
    return dy


def tri_h(H, x, z):
    c, r = x / 6, (ZTOP - z) / 6
    c0, r0 = int(c), int(r); fc, fr = c - c0, r - r0
    nw, ne, sw, se = H[r0, c0], H[r0, c0 + 1], H[r0 + 1, c0], H[r0 + 1, c0 + 1]
    return nw + fc * (ne - nw) + fr * (se - ne) if fc >= fr else nw + fr * (sw - nw) + fc * (se - sw)


def tri_w(x, z):
    """Flat vertex indices (n, 3) and planar weights (n, 3) of world points, NW-SE split as in tri_h."""
    c, r = np.asarray(x, float) / 6, (ZTOP - np.asarray(z, float)) / 6
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int); fc, fr = c - c0, r - r0
    up = fc >= fr
    rows = np.stack([r0, np.where(up, r0, r0 + 1), r0 + 1], -1); cols = np.stack([c0, np.where(up, c0 + 1, c0), c0 + 1], -1)
    w = np.stack([np.where(up, 1 - fc, 1 - fr), np.where(up, fc - fr, fr - fc), np.where(up, fr, fc)], -1)
    return rows * GN + cols, w


def terrain_at(Hf, x, z):
    i, w = tri_w(x, z)
    return (Hf[i] * w).sum(-1)


def to_world(matrix, P):
    m = np.asarray(matrix, float)
    return np.asarray(P, float) @ m[:9].reshape(3, 3) + m[9:12]


FAMS = (lambda P: P[:, 0] / 6, lambda P: (ZTOP - P[:, 2]) / 6, lambda P: P[:, 0] / 6 - (ZTOP - P[:, 2]) / 6)


def split(P, v, k):
    lo, hi = [], []
    n = len(P)
    for i in range(n):
        A, B, va, vb = P[i], P[(i + 1) % n], v[i], v[(i + 1) % n]
        if va <= k:
            lo.append(A)
        if va >= k:
            hi.append(A)
        if (va - k) * (vb - k) < 0:
            X = A + (k - va) / (vb - va) * (B - A); lo.append(X); hi.append(X)
    return np.array(lo), np.array(hi)


def pieces(P):
    """Convex 3D polygon cut by the vertical planes of the terrain triangle edges: each piece lies in one triangle."""
    out = [np.asarray(P, float)]
    for f in FAMS:
        nxt = []
        for Q in out:
            v = f(Q)
            for k in range(int(np.floor(v.min())) + 1, int(np.ceil(v.max()))):
                lo, Q = split(Q, f(Q), k)
                if len(lo) >= 3:
                    nxt.append(lo)
                if len(Q) < 3:
                    break
            if len(Q) >= 3:
                nxt.append(Q)
        out = nxt
    return out


def clip_le(P, v, k):
    return split(P, v, k)[0]


def face_points(polys, Hf=None, cap=None):
    """Piece vertices of world polygons (each piece inside one terrain triangle). With cap (per polygon: callable giving
    the face height minus a margin at points) the pieces are also split where cap - terrain changes sign, so a constraint
    max(0, cap - terrain) is linear on every piece. Returns points (n, 3) and the sign flag of cap - terrain."""
    pts, pos = [], []
    for j, P in enumerate(polys):
        for Q in pieces(P):
            if cap is None:
                pts.append(Q); continue
            g = cap[j](Q) - terrain_at(Hf, Q[:, 0], Q[:, 2])
            if g.min() < 0 < g.max():
                a, b = split(Q, g, 0.0)
                for R_, sg in ((a, False), (b, True)):
                    if len(R_) >= 3:
                        pts.append(R_); pos.append(np.full(len(R_), sg))
            else:
                pts.append(Q); pos.append(np.full(len(Q), bool(g.max() > 0) or bool(g.min() >= 0)))
    if not pts:
        return np.zeros((0, 3)), np.zeros(0, bool)
    P = np.concatenate(pts)
    return P, (np.concatenate(pos) if cap is not None else np.ones(len(P), bool))


def tri_slopes(A_):
    nw, ne, sw, se = A_[:-1, :-1], A_[:-1, 1:], A_[1:, :-1], A_[1:, 1:]
    return (np.degrees(np.arctan(np.hypot((ne - nw) / 6.0, (ne - se) / 6.0))),
            np.degrees(np.arctan(np.hypot((se - sw) / 6.0, (nw - sw) / 6.0))))


CORNERS = (((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 1), (1, 0)))


def slope_pass(H, H0, core, frz_all, rows=None, passes=80, cap=False):
    """v4 wall lay-back; with rows (sparse A, lower bound b) a lowering is refused where it would break a satisfied row or
    deepen a broken one. cap (v6): a lowering is also refused where it would leave a triangle steeper than max(SLOPE_MAX,
    input) and steeper than before (laying back one wall steepened its neighbour against a frozen top, 015-13 pool end)."""
    s0 = tri_slopes(H0); guard = 0
    lim = [np.maximum(SLOPE_MAX, a) + 1e-4 for a in s0]
    near = binary_dilation(H != H0, np.ones((3, 3), bool), iterations=2)
    for it in range(passes):
        s1 = tri_slopes(H); ch = H != H0; low = np.zeros(H.shape, bool)
        for (a0, a1), cor in zip(zip(s0, s1), CORNERS):
            chc = np.zeros(a0.shape, bool)
            for dr, dc in cor:
                chc |= ch[dr:dr + GN - 1, dc:dc + GN - 1]
            for r, c in np.argwhere(chc & (a1 > np.maximum(35.0, a0) + 1e-4)):
                top_v = max(((r + dr, c + dc) for dr, dc in cor), key=lambda v: H[v])
                if not core[top_v] and not frz_all[top_v] and near[top_v]:
                    low[top_v] = True
        if rows is not None and low.any():
            A, b = rows
            cur = A @ H.ravel()
            while low.any():
                new = A @ (H - 0.1 * low).ravel()
                bad = (new < b - 1e-9) & (new < cur - 1e-12)
                if not bad.any():
                    break
                hit = np.unique(A[np.flatnonzero(bad)].indices)
                hit = hit[low.ravel()[hit]]
                if not len(hit):
                    break
                low.ravel()[hit] = False
        while cap and low.any():
            sn = tri_slopes(H - 0.1 * low); stop = np.zeros(H.shape, bool)
            for an, a1, lm, cor in zip(sn, s1, lim, CORNERS):
                v = (an > lm) & (an > a1 + 1e-9)
                for dr, dc in cor:
                    stop[dr:dr + GN - 1, dc:dc + GN - 1] |= v
            stop &= low
            if not stop.any():
                break
            low &= ~stop
        if not low.any():
            break
        H = np.where(low, H - 0.1, H); guard += int(low.sum())
    return H, guard


def steep_changed(H, H0):
    """Changed triangles still steeper than max(35 deg, before), by triangle (row, col, half)."""
    s0, s1 = tri_slopes(H0), tri_slopes(H); ch = H != H0; out = []
    for half, ((a0, a1), cor) in enumerate(zip(zip(s0, s1), CORNERS)):
        chc = np.zeros(a0.shape, bool)
        for dr, dc in cor:
            chc |= ch[dr:dr + GN - 1, dc:dc + GN - 1]
        out += [(int(r), int(c), half) for r, c in np.argwhere(chc & (a1 > np.maximum(35.0, a0) + 1e-4))]
    return out


def section_widths(Hf, x0, z0, wd, wn, ts, qmax, level):
    """Exact wet width (planar terrain < level - 0.02) of the run at or nearest the axis, per section at t in ts (lines
    across the water axis; the terrain is linear between the crossings of the triangle edges)."""
    out = []
    for t in ts:
        P0 = np.array([x0 + t * wd[0], 0.0, z0 + t * wd[1]]); D = np.array([wn[0], 0.0, wn[1]])
        qs = [-qmax, qmax]
        for f in FAMS:
            fa, fb = f((P0 - qmax * D)[None])[0], f((P0 + qmax * D)[None])[0]
            if abs(fb - fa) > 1e-12:
                ks = np.arange(np.ceil(min(fa, fb)), np.floor(max(fa, fb)) + 1)
                qs += list(-qmax + (ks - fa) / (fb - fa) * 2 * qmax)
        qs = np.unique(np.clip(qs, -qmax, qmax))
        g = terrain_at(Hf, P0[0] + qs * D[0], P0[2] + qs * D[2]) - (level - 0.02)
        runs, start = [], (qs[0] if g[0] < 0 else None)
        for i in range(len(qs) - 1):
            if (g[i] < 0) != (g[i + 1] < 0):
                xq = qs[i] + g[i] / (g[i] - g[i + 1]) * (qs[i + 1] - qs[i])
                if g[i + 1] < 0:
                    start = xq
                else:
                    runs.append((start, xq)); start = None
        if start is not None:
            runs.append((start, qs[-1]))
        out.append(0.0 if not runs else max(0.0, (lambda r: r[1] - r[0])(min(runs, key=lambda r: 0 if r[0] <= 0 <= r[1] else min(abs(r[0]), abs(r[1]))))))
    return np.array(out)


def _unit(v):
    v = np.asarray(v, float)
    return v / max(float(np.hypot(*v)), 1e-12)


def _rot(u, deg):
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([c * u[0] - s_ * u[1], s_ * u[0] + c * u[1]])


def wet_runs(Hf, envc, P, n, qmax, L, step=0.25):
    """Wet runs (input terrain under L - 0.01 inside an envelope cell at L) along the line P + q n, |q| <= qmax:
    list of (centre q, width)."""
    q = np.arange(-qmax, qmax + 1e-9, step)
    X, Z = P[0] + q * n[0], P[1] + q * n[1]
    r, c = np.floor((ZTOP - Z) / 6).astype(int), np.floor(X / 6).astype(int)
    ok = (r >= 0) & (r < GN - 1) & (c >= 0) & (c < GN - 1)
    wet = np.zeros(len(q), bool)
    wet[ok] = (terrain_at(Hf, X[ok], Z[ok]) < L - 0.01) & envc[r[ok], c[ok]]
    out, start = [], None
    for i, w_ in enumerate(wet):
        if w_ and start is None:
            start = q[i]
        if not w_ and start is not None:
            out.append(((start + q[i - 1]) / 2, q[i - 1] - start + step)); start = None
    if start is not None:
        out.append(((start + q[-1]) / 2, q[-1] - start + step))
    return out


def track_natural(Hf, envc, start, u0, L, site):
    """(v6) Follow the natural stream from start: every TRACK_STEP m look ahead (straight, then turned +-15..60 deg) for a
    wet run across the look direction within TRACK_SEARCH m and step to the centre of the run nearest the look point.
    Returns [(centre xz, run width, direction)], gaps (no water) step straight, up to TRACK_GAPS in a row."""
    P, u, out, gaps = np.asarray(start, float), _unit(u0), [], 0
    for _ in range(80):
        hit = None
        for ang in (0, 15, -15, 30, -30, 45, -45, 60, -60):
            ud = _rot(u, ang); Pa = P + TRACK_STEP * ud; n = np.array([-ud[1], ud[0]])
            runs = wet_runs(Hf, envc, Pa, n, TRACK_SEARCH, L)
            if runs:
                mid, wid = min(runs, key=lambda r_: abs(r_[0]))
                hit = (Pa + mid * n, wid); break
        if hit is None:
            P = P + TRACK_STEP * u; gaps += 1
            if gaps > TRACK_GAPS:
                break
        else:
            C, wid = hit; dv = C - P
            if np.hypot(*dv) > 1e-6:
                u = _unit(0.5 * _unit(dv) + 0.5 * u)
            P = C; gaps = 0; out.append((C.copy(), float(wid), u.copy()))
        if np.hypot(*(P - site)) > TRACK_MAX:
            break
    return out


def natural_dir(Hf, envc, J, u, L):
    """Direction of the natural stream at J: from J to the centroid of the input water (planar terrain under L - 0.01 inside
    an envelope cell at L) sampled every 0.5 m in the cone +-75 deg around u, 3-18 m from J; the tracker's u where fewer
    than 8 samples are wet (the stream ends there). The tracker's local direction alone missed the stream's course by up to
    54 deg where it entered a wide reach (015-11 north)."""
    rr, aa = np.meshgrid(np.arange(3.0, 18.0 + 1e-9, 0.5), np.radians(np.arange(-75, 75.1, 2.5)), indexing="ij")
    base = math.atan2(u[1], u[0])
    X, Z = J[0] + rr * np.cos(base + aa), J[1] + rr * np.sin(base + aa)
    r, c = np.floor((ZTOP - Z) / 6).astype(int), np.floor(X / 6).astype(int)
    ok = (r >= 0) & (r < GN - 1) & (c >= 0) & (c < GN - 1)
    wet = np.zeros(X.shape, bool)
    wet[ok] = (terrain_at(Hf, X[ok], Z[ok]) < L - 0.01) & envc[r[ok], c[ok]]
    if wet.sum() < 8:
        return _unit(u), int(wet.sum())
    return _unit(np.array([X[wet].mean() - J[0], Z[wet].mean() - J[1]])), int(wet.sum())


def recentre(Hf, envc, C, L, rad=5.0):
    """Centroid of the input water (as in natural_dir) within rad m of C, 0.5 m samples; C itself where none is wet. A
    tracked centre on the far edge of a pool put the 015-13 join against the road platform, where the slope guard had to
    give the cut back and left the path dry."""
    gx, gz = np.meshgrid(np.arange(-rad, rad + 1e-9, 0.5), np.arange(-rad, rad + 1e-9, 0.5))
    k = np.hypot(gx, gz) <= rad; X, Z = C[0] + gx[k], C[1] + gz[k]
    r, c = np.floor((ZTOP - Z) / 6).astype(int), np.floor(X / 6).astype(int)
    ok = (r >= 0) & (r < GN - 1) & (c >= 0) & (c < GN - 1)
    wet = np.zeros(X.shape, bool)
    wet[ok] = (terrain_at(Hf, X[ok], Z[ok]) < L - 0.01) & envc[r[ok], c[ok]]
    return np.array([X[wet].mean(), Z[wet].mean()]) if wet.any() else np.asarray(C, float)


def hermite(S, tS, J, tJ, k0=1.0, k1=1.0, step=0.25):
    """Cubic Hermite from S (unit tangent tS) to J (unit tangent tJ), end tangents k0 and k1 times the chord, resampled
    at 1 m."""
    ln = float(np.hypot(*(J - S)))
    tau = np.linspace(0, 1, max(int(ln / step * 2), 8))[:, None]
    h00, h10, h01, h11 = 2 * tau ** 3 - 3 * tau ** 2 + 1, tau ** 3 - 2 * tau ** 2 + tau, -2 * tau ** 3 + 3 * tau ** 2, tau ** 3 - tau ** 2
    return resample(h00 * S + h10 * k0 * ln * tS + h01 * J + h11 * k1 * ln * tJ, 1.0)


def fair_curve(S, tS, J, tJ):
    """The Hermite S -> J with the smallest largest turning (TURN_CHORD chords, a 6 m lead-in along tS and lead-out along
    tJ included) over end-tangent scales HERMITE_K x HERMITE_K: the curvature spreads over the whole curve instead of
    bunching at one end (015-13: 37 deg with unit scales)."""
    lead = np.array([S - tS * (6 - i_) for i_ in range(6)]); tail = np.array([J + tJ * (i_ + 1) for i_ in range(6)])
    best = None
    for k0 in HERMITE_K:
        for k1 in HERMITE_K:
            cur = hermite(S, tS, J, tJ, k0, k1)
            t_ = max_turn(np.vstack([lead, cur, tail]))
            if best is None or t_ < best[0] - 1e-9:
                best = (t_, cur, k0, k1)
    return best


def resample(P, step):
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    t = np.r_[np.arange(0, s[-1], step), s[-1]]
    if len(t) > 1 and t[-1] - t[-2] < 1e-6:
        t = t[:-1]
    return np.column_stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])])


def max_turn(P, chord=TURN_CHORD):
    """Largest angle (deg) between the chords P(s - chord) -> P(s) and P(s) -> P(s + chord), P resampled at 1 m."""
    k = int(round(chord))
    if len(P) < 2 * k + 1:
        return 0.0
    a, b = P[k:-k] - P[:-2 * k], P[2 * k:] - P[k:-k]
    cs = (a * b).sum(1) / np.maximum(np.hypot(*a.T) * np.hypot(*b.T), 1e-12)
    return float(np.degrees(np.arccos(np.clip(cs, -1, 1))).max())


def seg_project(X, Z, P):
    """Nearest point of polyline P (n, 2) for points (X, Z): distance, arc length along P, overshoot beyond the last vertex
    (along the last segment's direction) and perpendicular distance to that end's tangent line."""
    A, B = P[:-1], P[1:]; AB = B - A; ln = np.hypot(*AB.T); cum = np.r_[0, np.cumsum(ln)]
    best = np.full(X.shape, np.inf); sarc = np.zeros(X.shape)
    for i in range(len(A)):
        t = np.clip(((X - A[i, 0]) * AB[i, 0] + (Z - A[i, 1]) * AB[i, 1]) / max(ln[i] ** 2, 1e-12), 0, 1)
        dd = np.hypot(X - A[i, 0] - t * AB[i, 0], Z - A[i, 1] - t * AB[i, 1])
        b = dd < best; best = np.where(b, dd, best); sarc = np.where(b, cum[i] + t * ln[i], sarc)
    te = _unit(AB[-1]); dx, dz = X - P[-1, 0], Z - P[-1, 1]
    over = dx * te[0] + dz * te[1]; perp = np.abs(-dx * te[1] + dz * te[0])
    return best, sarc, over, perp


def floor_beside(Hs, fixed, bed):
    """Lowest height a vertex may take beside the fixed vertices of the window Hs: their height minus 0.8 x tan SLOPE_MAX
    x 6 m along edges (x 8.485 m on diagonals), and never under bed."""
    hmin = np.full(Hs.shape, -np.inf)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == dc == 0:
                continue
            sh = np.full(Hs.shape, -np.inf); src_ = np.where(fixed, Hs, -np.inf)
            rs, cs_ = slice(max(dr, 0), Hs.shape[0] + min(dr, 0)), slice(max(dc, 0), Hs.shape[1] + min(dc, 0))
            rd, cd = slice(max(-dr, 0), Hs.shape[0] + min(-dr, 0)), slice(max(-dc, 0), Hs.shape[1] + min(-dc, 0))
            sh[rd, cd] = src_[rs, cs_]
            hmin = np.maximum(hmin, sh - 0.8 * math.tan(math.radians(SLOPE_MAX)) * (6.0 if dr == 0 or dc == 0 else 8.485))
    return np.maximum(hmin, bed)


def channel_v6(H0, Hc, env_in, envc_out, core, arrays, c, v4cut, held0, support, rows_keep):
    """(v6) Curved channel entries and exits of one site (see the header). Hc, envc_out and core are updated in place;
    returns the channel report. v4cut: frozen vertices the v4 cut lowered (the only frozen ones a curve may lower);
    held0: vertices under a hard seat row of any site (abutment faces, deck-end zones, ramps, legs), never lowered by a
    curve. v6r2: on the straight part the wet path may also lower vertices the v4 rule lets the cut lower (frozen ones
    only under a footprint (support) or where v4 cut them) and held ones, each only as far as every seat row it is in
    (rows_keep: sparse A (csc), lower bounds b) stays satisfied (review of 18-10: 015-18 and 015-40 had the axis dry
    over 4.1 and 3.3 m under the deck, both mouths in different water bodies; the lower copies' leg rows, which only
    ask terrain >= foot - LEG_TOL, held the channel vertices beside them)."""
    s, L, bed, W, wd, wn, d = c["s"], c["L"], c["bed"], c["W"], c["wd"], c["wn"], c["d"]
    sx, sz = s["x"], s["z"]; site = np.array([sx, sz]); Hf0 = H0.ravel()
    wl0 = W + 2 * (L - bed) / BANK                                                    # waterline width of the v4 section
    frz = arrays["reserve"] | arrays["platform"] | arrays["narva"]
    keep = arrays.get("v31_kit", np.zeros(H0.shape, bool)) | arrays.get("v31_lagoon", np.zeros(H0.shape, bool))
    envc = np.isfinite(env_in) & (np.abs(env_in - L) < 0.05)
    k = int((TRACK_MAX + 40) / 6)
    rc, cc = int((ZTOP - sz) / 6), int(sx / 6)
    sub = (slice(max(rc - k, 0), rc + k + 1), slice(max(cc - k, 0), cc + k + 1))
    R_, C_ = np.mgrid[sub]
    X, Z = 6.0 * C_, ZTOP - 6.0 * R_
    t, q = (X - sx) * wd[0] + (Z - sz) * wd[1], (X - sx) * wn[0] + (Z - sz) * wn[1]
    sroad = (X - sx) * d[0] + (Z - sz) * d[2]
    allowed = ~frz[sub] | (np.abs(sroad) <= c["flat"])                               # the v4 rule (straight part)
    allowed_c = (~frz[sub] | v4cut[sub]) & ~keep[sub] & ~held0[sub]                  # curves: frozen only where v4 cut it
    # straight part: the opening sections (+-td along the water axis) + 3 m; on a legged (wood) deck also its whole
    # footprint crossed by the channel strip + 3 m, so no leg stands over a bend (bridge_metal_25 spans clear: 015-13 left
    # a 49 deg hairpin into its pool when it stayed straight to 22.7 m)
    ga, gl = np.meshgrid(np.arange(-c["half_all"], c["half_all"] + 1e-9, 0.5), np.arange(-c["deck_half_w"], c["deck_half_w"] + 1e-9, 0.5))
    fx, fz = sx + ga * d[0] + gl * d[2], sz + ga * d[2] - gl * d[0]
    ft, fq = (fx - sx) * wd[0] + (fz - sz) * wd[1], (fx - sx) * wn[0] + (fz - sz) * wn[1]
    strip = (np.abs(fq) <= wl0 / 2 + 2) & bool(c["m"]["legs"])                      # legged decks: straight under all of it
    td = sections(c)[-1]                                                              # the opening sections reach this far
    Ts = {sg: min(max(float((sg * ft[strip]).max()) + 3.0 if strip.any() else 0.0, td + 3.0, 6.0), 60.0) for sg in (-1, 1)}
    side_rep, curves = [], {}
    okg = np.zeros(H0.shape, bool); okg[sub] = allowed_c                              # vertices a curve may lower
    # lowest height an allowed vertex may take beside a vertex it may not lower (that one's height - 0.8 x 6 m x
    # tan SLOPE_MAX along edges, x 8.49 m on diagonals): cutting deeper only feeds the slope guard below
    hmin = floor_beside(Hc[sub], ~allowed_c, bed); hming = np.full(H0.shape, bed); hming[sub] = hmin
    r0s, c0s = sub[0].start, sub[1].start
    q4 = np.abs(q) <= wl0 / 2 + 2                                                   # v4-cut frozen vertices on the axis
    for sg in (-1, 1):
        reach = float((sg * t[v4cut[sub] & q4 & (sg * t > 0)]).max()) + 3.0 if (v4cut[sub] & q4 & (sg * t > 0)).any() else Ts[sg]
        reach = max(reach, c["cut_side"][sg])                                       # up to the v4 cut's own extent
        tries = list(np.arange(Ts[sg], max(Ts[sg], min(reach, 60.0)) + 1e-9, 3.0)) or [Ts[sg]]
        best = None
        for Ts_ in tries:                                                             # straight part as short as it can be
            S = site + sg * Ts_ * wd
            zs_ = (sg * t >= 0) & (sg * t <= Ts_) | (-sg * t >= 0) & (-sg * t <= Ts[-sg])
            Hs = np.where(zs_ & allowed, np.minimum(Hc[sub], bed + BANK * np.maximum(np.abs(q) - W / 2, 0)), Hc[sub])
            tr = [] if c["sea"] else track_natural(Hf0, envc, S, sg * wd, L, site)
            for j, (Cj, wj, uj) in enumerate(tr):
                if np.hypot(*(Cj - site)) < Ts_ + CURVE_MIN:
                    continue
                Cj = recentre(Hf0, envc, Cj, L)                                       # mid-water in a wide reach or pool
                tj, nwet = natural_dir(Hf0, envc, Cj, _unit(tr[j + 1][0] - tr[j - 1][0]) if 0 < j < len(tr) - 1 else uj, L)
                if (tj * (Cj - S)).sum() <= 0:
                    continue
                turn, cur, k0, k1 = fair_curve(S, sg * wd, Cj, tj)
                ws = [w_ for _, w_, _ in tr[max(j - 2, 0):j + 3]]
                wlj = float(np.clip(np.median(ws), max(2.5, 0.6 * wl0), wl0 + 8.0))
                dist, _, _, _ = seg_project(X, Z, cur)
                conflict = int(((dist <= max(wlj, wl0) / 2) & ~allowed_c).sum())
                pth = resample(cur, 0.5); ii_, ww_ = tri_w(pth[:, 0], pth[:, 1])      # wet path feasible: allowed at the bed,
                rl, cl_ = np.divmod(ii_, GN); rl, cl_ = rl - r0s, cl_ - c0s                # the rest after the straight cut
                inw_ = (rl >= 0) & (rl < Hs.shape[0]) & (cl_ >= 0) & (cl_ < Hs.shape[1])
                hcur = np.where(inw_, Hs[np.clip(rl, 0, Hs.shape[0] - 1), np.clip(cl_, 0, Hs.shape[1] - 1)], Hc.ravel()[ii_])
                hv = np.where(okg.ravel()[ii_], np.minimum(hcur, hming.ravel()[ii_]), hcur)
                conflict += int(((hv * ww_).sum(1) >= L - WET_MARGIN).sum())
                score = (conflict > 0, turn > TURN_GATE, turn > TURN_TOOL, turn if turn > TURN_TOOL else 0.0, Ts_, j)
                if best is None or score < best[0]:
                    best = (score, dict(j=j, J=Cj, tJ=tj, curve=cur, turn=turn, wl_join=wlj, conflict=conflict, k=(k0, k1), Ts=Ts_,
                                        S=S, tracked=len(tr), natural_samples=nwet))
                if conflict == 0 and turn <= TURN_TOOL:
                    break
            if best is not None and best[0][0] is False and best[0][2] is False:
                break
        if best is None:                                                              # no natural water reached: v4 straight
            side_rep.append(dict(side=sg, straight_to_m=round(Ts[sg], 2), fallback="no natural water tracked", tracked=len(tr)))
            continue
        b = best[1]; curves[sg] = b; Ts[sg] = b["Ts"]; S = b["S"]
        side_rep.append(dict(side=sg, straight_to_m=round(Ts[sg], 2), straight_tries_m=[round(float(x), 2) for x in tries],
                             start=S.round(2).tolist(), join=b["J"].round(2).tolist(),
                             join_dist_m=round(float(np.hypot(*(b["J"] - site))), 2), join_tangent=b["tJ"].round(4).tolist(),
                             join_natural_samples=b["natural_samples"],
                             curve_len_m=round(float(np.hypot(*np.diff(b["curve"], axis=0).T).sum()), 2), max_turn_deg=round(b["turn"], 2),
                             waterline_width_start_m=round(wl0, 3), waterline_width_join_m=round(b["wl_join"], 3),
                             conflicts=b["conflict"], tracked=b["tracked"], join_index=b["j"], tangent_scales=list(b["k"])))
    # carve: the v4 section on the straight part (and on a side without a curve, out to the v4 cut and its link), the
    # curve's section (bed width blended from W to the natural width at the join) beyond
    new = Hc[sub].copy(); floor = np.zeros(new.shape, bool); seal = np.zeros((new.shape[0] - 1, new.shape[1] - 1), bool)
    cx_, cz_ = X[:-1, :-1] + 3.0, Z[:-1, :-1] - 3.0
    ct, cq = (cx_ - sx) * wd[0] + (cz_ - sz) * wd[1], (cx_ - sx) * wn[0] + (cz_ - sz) * wn[1]
    lo_t = -(Ts[-1] if -1 in curves else c["cut_side"][-1]); hi_t = Ts[1] if 1 in curves else c["cut_side"][1]
    zs = (t >= lo_t) & (t <= hi_t)
    tgt = bed + BANK * np.maximum(np.abs(q) - W / 2, 0)
    new = np.where(zs & allowed, np.minimum(new, tgt), new); floor |= zs & allowed & (np.abs(q) <= W / 2)
    seal |= (np.abs(cq) <= W / 2 + 6) & (ct >= lo_t) & (ct <= hi_t)
    for lk in c["links"]:                                                            # v4 links only on sides without a curve
        if lk["side"] in curves:
            continue
        st_, tg_ = np.array(lk["start"]), np.array(lk["target"]); ab = tg_ - st_
        tt = np.clip(((X - st_[0]) * ab[0] + (Z - st_[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
        dl = np.hypot(X - st_[0] - tt * ab[0], Z - st_[1] - tt * ab[1])
        new = np.where(~frz[sub] & ~keep[sub] & (dl <= W / 2 + 8.0), np.minimum(new, bed + BANK * np.maximum(dl - W / 2, 0)), new)
        floor |= (dl <= W / 2) & ~frz[sub] & ~keep[sub]
        tt = np.clip(((cx_ - st_[0]) * ab[0] + (cz_ - st_[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
        seal |= np.hypot(cx_ - st_[0] - tt * ab[0], cz_ - st_[1] - tt * ab[1]) <= W / 2 + 6
    Hst = new.copy()                                                                  # after the v4 section (and links)
    for sg, b in curves.items():
        cur = b["curve"]; ln = float(np.hypot(*np.diff(cur, axis=0).T).sum())
        dist, sa, over, perp = seg_project(X, Z, cur)
        f = np.clip(sa / max(ln, 1e-9), 0, 1); f = f * f * (3 - 2 * f)
        wl = wl0 + (b["wl_join"] - wl0) * f; wb = np.maximum(wl - 2 * (L - bed) / BANK, 0.5)
        dd = np.where(over > 0, perp, dist)
        tgt = bed + BANK * np.maximum(dd - wb / 2, 0) + BANK * np.maximum(over, 0)
        zone = (over <= 8.0) & (dist <= wl / 2 + 20.0)
        new = np.where(zone & allowed_c, np.minimum(new, np.maximum(tgt, hmin)), new)
        floor |= zone & allowed_c & (over <= 0) & (dist <= wb / 2)
        cd, csa, cov, _ = seg_project(cx_, cz_, cur)
        cf = np.clip(csa / max(ln, 1e-9), 0, 1); cf = cf * cf * (3 - 2 * cf)
        seal |= (cov <= 0) & (cd <= (wl0 + (b["wl_join"] - wl0) * cf) / 2 + SEAL_OUT)
    lowered = new < Hc[sub]
    cmask = new < Hst - 1e-12; wpm = np.zeros(H0.shape, bool)                          # lowered by a curve / the wet path
    Hc_in = Hst
    Hc[sub] = new; core[sub] |= floor
    # wet path: the planar terrain along the centreline (0.5 m samples, up to each join) at least WET_MARGIN under the
    # level; where a narrow oblique section left a dry neck (015-16: the curve beaded into pools on the 6 m grid), the
    # allowed vertex of the triangle with the largest weight goes down to the bed, until the path is wet or none is left
    pp = ([curves[-1]["curve"][::-1]] if -1 in curves else []) + [resample(np.array([site - Ts[-1] * wd, site + Ts[1] * wd]), 1.0)]
    path = resample(np.vstack(pp + ([curves[1]["curve"]] if 1 in curves else [])), 0.5)
    okv = okg.ravel()
    oks = np.zeros(H0.shape, bool)                                                    # v6r2 straight part (see the docstring)
    oks[sub] = zs & allowed & ~keep[sub] & (~frz[sub] | v4cut[sub] | support[sub])
    oks = oks.ravel()
    A_r, A_k, b_k = rows_keep
    # v6r2: the wet path's floor beside a vertex it may not lower uses that vertex's height after the v4 section (the
    # curves' hmin uses the heights before it, so a held vertex the section had cut from 9.25 to 1.81 m kept 015-40's
    # neighbours 0.3 m too high and the axis dry)
    hming = np.full(H0.shape, bed); hming[sub] = floor_beside(Hc[sub], ~(okv | oks).reshape(H0.shape)[sub], bed)
    Hflat = Hc.ravel(); necks = 0; straight_lowered = 0
    for _ in range(400):
        ii, ww = tri_w(path[:, 0], path[:, 1])
        val = (Hflat[ii] * ww).sum(1); bad = np.flatnonzero(val > L - WET_MARGIN)
        if not len(bad):
            break
        moved = False
        for b_ in bad:
            for j_ in np.argsort(-ww[b_]):
                v_ = ii[b_, j_]; tgt_ = hming.ravel()[v_]
                if Hflat[v_] <= tgt_ + 1e-6 or not (okv[v_] or oks[v_]):
                    continue
                lo_, hi_ = A_k.indptr[v_], A_k.indptr[v_ + 1]
                rr_, wv_ = A_k.indices[lo_:hi_], A_k.data[lo_:hi_]
                if len(rr_):                                                         # seat rows through v_: keep them
                    k_ = wv_ > 1e-12; rr_, wv_ = rr_[k_], wv_[k_]
                    if len(rr_):
                        cur_ = A_r[rr_] @ Hflat
                        if (cur_ < b_k[rr_] - 1e-9).any():
                            continue
                        tgt_ = max(tgt_, Hflat[v_] - float(np.min((cur_ - b_k[rr_]) / wv_)))
                        if Hflat[v_] <= tgt_ + 1e-6:
                            continue
                straight_lowered += int(not okv[v_])
                Hflat[v_] = tgt_; core.ravel()[v_] = True; wpm.ravel()[v_] = True; necks += 1; moved = True; break
            if moved:
                break
        if not moved:
            break
    # islets: an allowed vertex of the carved zone left dry with its 6 native-edge neighbours wet (015-13 east: +0.14 m in
    # the pool mouth, a dry triangle fan in the water) goes to WET_MARGIN under the level (never under its hmin)
    islets = 0
    for _ in range(4):
        Hw = Hc[sub]; wet_ = Hw < L
        nb = np.ones(Hw.shape, bool)
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1)):
            sh = np.zeros(Hw.shape, bool)
            sh[max(-dr, 0):Hw.shape[0] + min(-dr, 0), max(-dc, 0):Hw.shape[1] + min(-dc, 0)] = wet_[max(dr, 0):Hw.shape[0] + min(dr, 0), max(dc, 0):Hw.shape[1] + min(dc, 0)]
            nb &= sh
        isl = nb & ~wet_ & allowed_c & cmask & (hmin < L - WET_MARGIN)
        if not isl.any():
            break
        Hc[sub] = np.where(isl, np.maximum(hmin, L - WET_MARGIN), Hw); cmask |= isl; islets += int(isl.sum())
    # slope guard: no triangle a curve or the wet path lowered may end steeper than max(SLOPE_MAX, its input slope); a
    # frozen or held wall beside such a cut (015-13 pool end: platform 9.06 m beside a bank cut to 2.68 m; 015-40: a held
    # deck-end vertex beside a v4-cut one) gets those vertices back in 0.1 m steps, channel floor last, never above their
    # height after the v4 section; the v4 section itself is never raised (raising it closed 015-19's opening to 0.2 m)
    Hw0 = Hc_in; guard_steps = 0
    s0 = np.maximum(np.stack(tri_slopes(H0[sub])), SLOPE_MAX)
    for _ in range(400):
        Hw = Hc[sub]; low = (Hw < Hw0 - 1e-9) & (cmask | wpm[sub])                    # never the v4 section
        s1 = np.stack(tri_slopes(Hw)); bad = s1 > s0 + 1e-4
        lowc = np.stack([low[:-1, :-1] | low[:-1, 1:] | low[1:, 1:], low[:-1, :-1] | low[1:, 1:] | low[1:, :-1]])
        bad &= lowc
        if not bad.any():
            break
        up = np.zeros(Hw.shape, bool)
        for half, r_, c_ in np.argwhere(bad):
            vs = [(r_ + dr, c_ + dc) for dr, dc in CORNERS[half]]
            cand = [v for v in vs if low[v] and not core[sub][v]] or [v for v in vs if low[v]]
            for v in cand:
                up[v] = True
        Hn = np.where(up, np.minimum(Hw + 0.1, Hw0), Hw); guard_steps += int(up.sum())
        Hc[sub] = Hn
    ii, ww = tri_w(path[:, 0], path[:, 1]); dry_ = (Hflat[ii] * ww).sum(1) > L - WET_MARGIN
    pt, pq = (path - site) @ wd, (path - site) @ wn
    st_ = (np.abs(pq) <= 0.05) & (pt >= -Ts[-1] - 0.05) & (pt <= Ts[1] + 0.05)          # the v4 section under the deck
    sealed = 0
    # v6r2: the four cells around every vertex the wet path took under the level are sealed too (015-40: two v4-cut
    # vertices lowered beside unsealed cells became exposed footprint border vertices that bury_edges_v31 could not bury)
    wl_ = wpm[sub] & (Hc[sub] < L); wpc = np.zeros(seal.shape, bool)
    for dr in (0, 1):
        for dc in (0, 1):
            wpc |= wl_[dr:dr + seal.shape[0], dc:dc + seal.shape[1]]
    seal |= wpc
    if not c["sea"]:
        es = envc_out[sub[0].start:sub[0].stop - 1, sub[1].start:sub[1].stop - 1]
        block = np.isfinite(es) & (np.abs(es - L) > 0.05)
        add = seal & ~block & ~(np.isfinite(es) & (np.abs(es - L) <= 0.05))
        envc_out[sub[0].start:sub[0].stop - 1, sub[1].start:sub[1].stop - 1] = np.where(seal & ~block, L, es); sealed = int(add.sum())
    # centreline: side -1 curve reversed, the straight part, side +1 curve (1 m steps)
    parts = []
    if -1 in curves:
        parts.append(curves[-1]["curve"][::-1])
    a0 = site - (Ts[-1] if -1 in curves else c["cut_side"][-1]) * wd; a1 = site + (Ts[1] if 1 in curves else c["cut_side"][1]) * wd
    parts.append(resample(np.array([a0, a1]), 1.0))
    if 1 in curves:
        parts.append(curves[1]["curve"])
    cl = resample(np.vstack(parts), 1.0)
    return dict(straight_m=[round(Ts[-1], 2), round(Ts[1], 2)], waterline_width_m=round(wl0, 3), sides=side_rep,
                wet_path=dict(vertices_lowered=necks, straight_rule_vertices=straight_lowered, dry_samples_left_curves=int((dry_ & ~st_).sum()),
                              dry_samples_left_straight=int((dry_ & st_).sum()), margin_m=WET_MARGIN), slope_guard_raise_steps=guard_steps,
                islets_lowered=islets,
                max_turn_deg=round(max_turn(cl), 2), lowered_vertices=int(lowered.sum()), seal_cells_added=sealed,
                centreline=cl.round(2).tolist())


def check_inputs(arrays, env, sites):
    """(v6r2) Refuse what no rule here can handle: heights not a finite (GN, GN) array (review of 18-10: a NaN at
    heights[34, 1315] went through, exit 0, and only the WRP stage stopped it), masks not (GN, GN) booleans, an
    envelope not (GN-1, GN-1) or holding an infinite value (NaN = no cell), an empty site list or repeated ids."""
    h = arrays.get("heights")
    if h is None or h.shape != (GN, GN) or h.dtype.kind != "f":
        refuse(f"heights missing or not a ({GN}, {GN}) float array")
    bad = np.argwhere(~np.isfinite(h))
    if len(bad):
        refuse(f"{len(bad)} non-finite heights (first {bad[:5].tolist()})")
    for k in ("reserve", "platform", "narva"):
        if k not in arrays or arrays[k].shape != (GN, GN) or arrays[k].dtype != bool:
            refuse(f"mask {k} missing or not a ({GN}, {GN}) boolean array")
    if env.shape != (GN - 1, GN - 1) or np.isinf(env).any():
        refuse(f"envelope not a ({GN - 1}, {GN - 1}) array of levels and NaN")
    if not isinstance(sites, list) or any(not isinstance(s, dict) for s in sites):
        refuse("sites must be a list of objects")
    ids = [s.get("id") for s in sites]
    if not ids or len(set(ids)) != len(ids):
        refuse("the site list is empty or repeats an id")
    for s in sites:
        for k in ("x", "z", "bearing", "level", "water_bearing", "width"):
            v = s.get(k)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
                refuse(f"{s.get('id')}: {k} must be finite")
        if not 0 < s["x"] < ZTOP or not 0 < s["z"] < ZTOP or s["width"] <= 0:
            refuse(f"{s.get('id')}: coordinates outside the map or non-positive width")
        n = s.get("spans", 1)
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            refuse(f"{s.get('id')}: spans must be a positive integer")


def main():
    tpath, epath, spath, out_t, out_e, rec_path, rep_path = sys.argv[1:8]
    z = np.load(tpath); arrays = {k: z[k].copy() for k in z.files}
    env = np.load(epath).astype(np.float64)
    sites_in = json.load(open(spath))
    check_inputs(arrays, env, sites_in)
    H0 = arrays["heights"].astype(np.float64); H = H0.copy()
    env_new = env.copy()
    records, rep, ctx = [], [], []
    core = np.zeros(H.shape, bool)                                                     # channel floor: never raised
    v4cut = np.zeros(H.shape, bool)                                                    # frozen vertices the v4 cut lowers
    for s in sites_in:
        base = VARIANTS.get(s["model"])
        m = model_info(base or s["model"])
        mv = model_info(s["model"]) if base else m
        dy_var = variant_offset(m, mv, s["model"]) if base else 0.0
        b = math.radians(s["bearing"]); d = np.array([math.sin(b), 0.0, math.cos(b)])
        C = np.array([s["x"], 0.0, s["z"]])
        n_sp = int(s.get("spans", 1)); half_all = n_sp * m["half"]
        e1, e2 = C - half_all * d, C + half_all * d
        nl = np.array([d[2], 0.0, -d[0]])                                                  # horizontal, across the road
        a1, a2 = tri_h(H0, e1[0], e1[2]), tri_h(H0, e2[0], e2[2])
        k_pitch = (a2 - a1) / (2 * half_all)                                                # deck rise per metre from e1
        def end_h(e, inward, rise):
            strip = max(tri_h(H0, *(e + a * inward + l * nl)[[0, 2]]) - a * rise for a in np.linspace(0.0, END_IN, 5)
                        for l in np.linspace(-m["end_half_w"], m["end_half_w"], 9))
            return strip + END_CLEAR
        h1, h2 = max(a1, end_h(e1, d, k_pitch)), max(a2, end_h(e2, -d, -k_pitch))
        phi = math.atan2(h2 - h1, 2 * half_all)
        f = np.array([d[0] * math.cos(phi), math.sin(phi), d[2] * math.cos(phi)])          # model length axis
        u = np.array([-d[0] * math.sin(phi), math.cos(phi), -d[2] * math.sin(phi)])         # model up
        if m["axis"] == 0:
            X, Y = f, u; Z = np.cross(X, Y)
        else:
            Z, Y = f, u; X = np.cross(Y, Z)
        Rm = np.stack([X, Y, Z], axis=1)                                                     # columns = local axes
        y_end = (m["end_y"][0] + m["end_y"][1]) / 2
        local_c = np.zeros(3); local_c[m["axis"]] = m["centre_len"]; local_c[2 - m["axis"]] = m["centre_lat"]
        span_pos, upper, lower = [], [], []
        for k in range(n_sp):
            frac = (2 * k + 1) / (2 * n_sp)                                                   # 0..1 along e1 -> e2
            Ck = C + (-half_all + (2 * k + 1) * m["half"]) * d
            pos = Ck - Rm @ np.array([local_c[0], 0.0, local_c[2]])
            pos[1] = h1 + frac * (h2 - h1) - y_end * math.cos(phi)
            pos = pos - dy_var * Y                                                           # variant: same world roadway
            span_pos.append(pos.copy())
            matrix = [*X.tolist(), *Y.tolist(), *Z.tolist(), *pos.tolist()]
            records.append(dict(site=s["id"], span=k, model=f"dz\\structures\\roads\\bridges\\{s['model']}.p3d", matrix=matrix))
            upper.append(matrix)
            if s.get("stack"):
                lm = [*X.tolist(), *Y.tolist(), *Z.tolist(), *(pos - STACK_DY * Y).tolist()]
                records.append(dict(site=s["id"], span=k, role="stack-lower", model=f"dz\\structures\\roads\\bridges\\{s['model']}.p3d", matrix=lm))
                lower.append(lm)
        pos = np.mean(span_pos, axis=0)
        # channel and seals
        wb = math.radians(s["water_bearing"]); wd = np.array([math.sin(wb), math.cos(wb)])
        wn = np.array([-wd[1], wd[0]])
        W = float(s["width"])
        flat = half_all - 6.5
        deck_half_w = m["width"] / 2 + 1.0
        frz = arrays["reserve"] | arrays["platform"] | arrays["narva"]
        run_end, cut_side, run_side, wet_side = 0.0, {}, {}, {}
        for sgn in (-1, 1):                                                            # per side: frozen run, first water
            last, gap = 0.0, 0.0
            for tt in np.arange(0.0, 60.0, 1.0):
                xx, zz = s["x"] + sgn * tt * wd[0], s["z"] + sgn * tt * wd[1]
                if frz[int(round((ZTOP - zz) / 6)), int(round(xx / 6))]:
                    last, gap = tt, 0.0
                else:
                    gap += 1.0
                    if gap > 3.0 and tt > 3.0:
                        break
            first_wet = 0.0
            for tt in np.arange(4.0, 60.0, 1.0):
                xx, zz = s["x"] + sgn * tt * wd[0], s["z"] + sgn * tt * wd[1]
                if min(tri_h(H0, xx + u * wd[1], zz - u * wd[0]) for u in (-3.0, -1.5, 0.0, 1.5, 3.0)) < float(s["level"]) - 0.01:
                    first_wet = tt; break
            run_end = max(run_end, last); run_side[sgn] = last; wet_side[sgn] = first_wet
            cut_side[sgn] = max(CUT_T, min(max(last + 6.0, first_wet + 4.0), 60.0))
        cut_t = max(cut_side.values())
        k = int((cut_t + 30) / 6) + 2
        rc, cc = int((ZTOP - s["z"]) / 6), int(s["x"] / 6)
        R_, C_ = np.mgrid[rc - k:rc + k + 1, cc - k:cc + k + 1]
        X_, Z_ = 6.0 * C_ - s["x"], (ZTOP - 6.0 * R_) - s["z"]
        t = X_ * wd[0] + Z_ * wd[1]; q = X_ * wn[0] + Z_ * wn[1]
        envv = np.full(H.shape, False)
        fin = np.isfinite(env)
        for dr in (0, 1):
            for dc in (0, 1):
                envv[dr:dr + 2047, dc:dc + 2047] |= fin
        in_t = (t >= -cut_side[-1]) & (t <= cut_side[1])
        axis = (np.abs(q) <= W / 2) & in_t
        sub0 = (slice(rc - k, rc + k + 1), slice(cc - k, cc + k + 1))
        sea_mode = bool((axis & ~envv[sub0] & (H0[sub0] < SEA)).any()) and not bool((axis & envv[sub0]).any())
        L = SEA if sea_mode else float(s["level"])
        bed = SEA_BED if sea_mode else max(BED_MIN, L - 0.5)
        sroad = X_ * d[0] + Z_ * d[2]
        target = bed + BANK * np.maximum(np.abs(q) - W / 2, 0)
        zone = in_t
        sub = (slice(rc - k, rc + k + 1), slice(cc - k, cc + k + 1))
        frozen = (arrays["reserve"] | arrays["platform"] | arrays["narva"])[sub]
        slat = X_ * d[2] - Z_ * d[0]                                                       # lateral offset from the road axis
        deck = (np.abs(sroad) <= flat) & (np.abs(slat) <= deck_half_w)
        allowed = zone & (~frozen | (np.abs(sroad) <= flat))
        hs = H[sub].copy()
        new = np.where(allowed, np.minimum(hs, target), hs)
        envl = np.zeros(H.shape, bool)                                                  # vertices of envelope cells at L
        fl = np.isfinite(env) & (np.abs(env - L) < 0.05)
        for dr in (0, 1):
            for dc in (0, 1):
                envl[dr:dr + 2047, dc:dc + 2047] |= fl
        links = []
        for sgn in (-1, 1):
            if wet_side[sgn] or sea_mode:
                continue
            cand = envl[sub] & (H0[sub] < L - 0.01) & (sgn * t > max(run_side[sgn], 6.0)) & ~frozen & (np.hypot(X_, Z_) <= 60.0)
            if not cand.any():
                continue
            i = int(np.argmin(np.where(cand, np.hypot(X_, Z_), np.inf)))
            tgt = np.array([X_.flat[i], Z_.flat[i]]); st = np.array(wd) * sgn * (run_side[sgn] + 3.0)
            ab = tgt - st; tt_ = np.clip(((X_ - st[0]) * ab[0] + (Z_ - st[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
            dl = np.hypot(X_ - (st[0] + tt_ * ab[0]), Z_ - (st[1] + tt_ * ab[1]))
            new = np.where(~frozen & (dl <= W / 2 + 8.0), np.minimum(new, bed + BANK * np.maximum(dl - W / 2, 0)), new)
            links.append(dict(side=sgn, start=(st + [s["x"], s["z"]]).round(1).tolist(), target=(tgt + [s["x"], s["z"]]).round(1).tolist()))
            core[sub] |= (dl <= W / 2) & ~frozen
        core[sub] |= (np.abs(q) <= W / 2) & zone & allowed
        v4cut[sub] |= frozen & (new < hs)
        H[sub] = new
        cR, cC = np.mgrid[rc - k:rc + k, cc - k:cc + k]
        cx, cz = 6.0 * cC + 3 - s["x"], (ZTOP - 6.0 * cR - 3) - s["z"]
        ct, cq = cx * wd[0] + cz * wd[1], cx * wn[0] + cz * wn[1]
        seal = (np.abs(cq) <= W / 2 + 6) & (ct >= -cut_side[-1]) & (ct <= cut_side[1])
        for lk in links:
            st = np.array(lk["start"]) - [s["x"], s["z"]]; tg = np.array(lk["target"]) - [s["x"], s["z"]]; ab = tg - st
            tt_ = np.clip(((cx - st[0]) * ab[0] + (cz - st[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
            seal |= np.hypot(cx - (st[0] + tt_ * ab[0]), cz - (st[1] + tt_ * ab[1])) <= W / 2 + 6
        es = env_new[rc - k:rc + k, cc - k:cc + k]
        block = np.isfinite(es) & (np.abs(es - L) > 0.05)
        if not sea_mode:
            env_new[rc - k:rc + k, cc - k:cc + k] = np.where(seal & ~block, L, es)
        under = deck & (np.abs(q) <= W / 2)                                                  # channel inside the deck footprint
        rep.append(dict(site=s["id"], model=s["model"], spans=n_sp, cut_t=round(cut_t, 1), cut_up_down=[round(cut_side[1], 1), round(cut_side[-1], 1)], frozen_run_m=run_end, links=links, water="sea" if sea_mode else "pond", pitch_deg=round(math.degrees(phi), 3), ends_road_y=[round(h1, 3), round(h2, 3)], ends_lift=[round(h1 - a1, 3), round(h2 - a2, 3)],
                        position=[round(v, 3) for v in pos], deck_road_mid=round(pos[1] + (mv["deck_max"] if mv["axis"] == 0 else (mv["end_y"][0] + mv["end_y"][1]) / 2), 2), level=L, bed=bed,
                        cut_vertices=int((new < hs).sum()), cut_frozen_vertices=int(((new < hs) & frozen).sum()),
                        max_cut_m=round(float((hs - new).max()), 2), channel_ground_max_under_deck=round(float(new[under].max()), 2) if under.any() else None,
                        seal_cells=0 if sea_mode else int((seal & ~block).sum())))
        ctx.append(dict(s=s, m=mv, upper=upper, lower=lower, L=L, bed=bed, sea=sea_mode, W=W, wd=wd, wn=wn, d=d, n_sp=n_sp,
                        sub=sub, cut_allowed=allowed, variant=bool(base), dy_var=dy_var, cut_side=dict(cut_side), run_side=dict(run_side),
                        flat=flat, deck_half_w=deck_half_w, half_all=half_all, links=links))
    frz_all = arrays["reserve"] | arrays["platform"] | arrays["narva"]
    H_v4, guard_v4 = slope_pass(H, H0, core, frz_all)                                  # the v4 terrain (reference only)
    stuck_v4 = steep_changed(H_v4, H0)
    H6, env6, core6, chan = H0.copy(), env_new.copy(), np.zeros(H.shape, bool), []      # v6: curved channel entries/exits
    geo0 = [end_geometry(c) for c in ctx]
    rows0 = build_rows(geo0, ctx, H0.ravel())
    keep_k = np.isin(rows0["kind"], KEEP_KINDS) & rows0["hard_lb"]                       # seat rows (not the wings: water first)
    held0 = np.zeros(GN * GN, bool); held0[np.unique(rows0["A"][np.flatnonzero(keep_k)].indices)] = True
    support = footprint_support(geo0)
    Ak_ = rows0["A"][np.flatnonzero(keep_k)].tocsr(); rows_keep = (Ak_, Ak_.tocsc(), rows0["b"][keep_k])
    for c in ctx:                                                                      # natural water: the INPUT envelope;
        chan.append(channel_v6(H0, H6, env, env6, core6, arrays, c, v4cut, held0.reshape(GN, GN), support.reshape(GN, GN), rows_keep))
    H6s, guard6 = slope_pass(H6, H0, core6, frz_all, cap=True)
    stuck6 = steep_changed(H6s, H0)
    H, fit = end_fit(H6s, H_v4, H0, env6, ctx, core6, frz_all, paths=[(np.array(ch["centreline"]), c["L"]) for ch, c in zip(chan, ctx)])
    env_new = env6
    if not np.isfinite(H).all() or not np.isfinite(H.astype(np.float32)).all():
        refuse("non-finite output heights")
    arrays["heights"] = H.astype(np.float32)
    arrays["v31_bridge_cut"] = (arrays["heights"] != H0.astype(np.float32)) | arrays.get("v31_bridge_cut", np.zeros(H.shape, bool))
    arrays["v31_bridge_fill"] = (arrays["heights"] > H0.astype(np.float32)) | arrays.get("v31_bridge_fill", np.zeros(H.shape, bool))
    np.savez(out_t, **arrays); np.save(out_e, env_new.astype(np.float32))
    json.dump(records, open(rec_path, "w"), indent=1)
    Hst = arrays["heights"].astype(np.float64).ravel()
    for r, f_, ch, c in zip(rep, fit["sites"], chan, ctx):
        Qp = resample(np.array(ch["centreline"]), 0.5); ip, wp = tri_w(Qp[:, 0], Qp[:, 1]); hv = (Hst[ip] * wp).sum(1)
        ch["final_path"] = dict(samples=int(len(Qp)), dry=int((hv >= c["L"]).sum()), max_terrain_minus_level_m=round(float((hv - c["L"]).max()), 4))
        r.update(f_); r["channel"] = ch
    json.dump(dict(schema="bridges-v31.v6", revision="v6r2", params=dict(PATH_UB=PATH_UB, WING_SOFT=WING_SOFT, KEEP_KINDS=list(KEEP_KINDS), BANK=BANK, CUT_T=CUT_T, BED_MIN=BED_MIN, END_IN=END_IN, END_CLEAR=END_CLEAR, STACK_DY=STACK_DY,
                                                         FACE_TOL=FACE_TOL, RAMP_CAP=RAMP_CAP, RAMP_AIR=RAMP_AIR, LEG_TOL=LEG_TOL, DECK_CLEAR=DECK_CLEAR, WING=WING,
                                                         END_AIR=END_AIR, END_DEPTH=END_DEPTH, WING_BEYOND=WING_BEYOND, WING_SIDE=WING_SIDE,
                                                         TRACK_STEP=TRACK_STEP, TRACK_SEARCH=TRACK_SEARCH, TRACK_MAX=TRACK_MAX, TRACK_GAPS=TRACK_GAPS, WET_MARGIN=WET_MARGIN, HERMITE_K=list(HERMITE_K),
                                                         CURVE_MIN=CURVE_MIN, TURN_CHORD=TURN_CHORD, TURN_TOOL=TURN_TOOL, TURN_GATE=TURN_GATE, SEAL_OUT=SEAL_OUT),
                   sites=rep, slope_guard_steps=guard_v4, slope_stuck_triangles=len(stuck_v4),
                   channel_slope_guard_steps=guard6, channel_slope_stuck_triangles=len(stuck6),
                   end_fit=fit["summary"]), open(rep_path, "w", newline="\n"), indent=1)
    print(json.dumps(dict(sites=[{k_: v for k_, v in r.items() if k_ in ("site", "fit_ends", "legs", "opening_m", "fill_vertices")} | dict(channel={k_: v for k_, v in r["channel"].items() if k_ != "centreline"}) for r in rep], end_fit=fit["summary"]), indent=1))


def end_geometry(c):
    """World polygons of one site: abutment faces and ramp undersides (per outer end), deck faces, end strips, legs and
    footprint rectangles."""
    m = c["m"]; ax, lat = m["axis"], 2 - m["axis"]; lo, hi = m["roadway_lo_hi"]
    out = dict(ends=[], deck=[], strips=[], legs=[], foot=[], zones=[])
    for k, M in enumerate(c["upper"]):
        out["deck"] += [to_world(M, T) for T in m["deck_faces"]]
        for ei, (e, inw) in enumerate(((lo, 1.0), (hi, -1.0))):
            if (ei == 0 and k == 0) or (ei == 1 and k == len(c["upper"]) - 1):
                for T in m["deck_faces"]:
                    P = clip_le(T, (T[:, ax] - e) * inw, END_IN)
                    if len(P) >= 3:
                        out["strips"].append((ei, to_world(M, P)))
                st = m["seats"][ei]
                out["ends"].append(dict(end=ei, kind=st["kind"], faces=[to_world(M, T) for T in st["faces"]], seat=st, matrix=M, e=e, inw=inw))
                zn = m["zones"][ei]; rect = np.zeros((4, 3))                     # v6 deck-end zone on its underside plane
                for j, (a_, l_) in enumerate(((0.0, zn["lat_lo"]), (zn["a_end"], zn["lat_lo"]), (zn["a_end"], zn["lat_hi"]), (0.0, zn["lat_hi"]))):
                    rect[j, ax] = e + inw * a_; rect[j, lat] = m["centre_lat"] + l_; rect[j, 1] = zn["y0"] + zn["slope"] * a_
                out["zones"].append(dict(end=ei, poly=to_world(M, rect), zone=zn, matrix=M, e=e, inw=inw))
        bmin, bmax = m["bbox"]
        rect = np.array([[bmin[0], 0, bmin[2]], [bmax[0], 0, bmin[2]], [bmax[0], 0, bmax[2]], [bmin[0], 0, bmax[2]]])
        out["foot"].append(to_world(M, rect) * [1, 0, 1])
        if c["variant"]:
            out["legs"] += [("upper", k, to_world(M, f)) for f in m["legs"]]
        elif c["lower"]:                                                              # upper feet not resting on the copy
            out["legs"] += [("upper", k, to_world(M, f)) for f, g in zip(m["legs"], m["legs_over_stack"]) if g > LEG_TOL]
    for k, M in enumerate(c["lower"]):
        out["legs"] += [("lower", k, to_world(M, f)) for f in m["legs"]]
    return out


def footprint_support(geo):
    """Flat mask of the vertices of the terrain triangles under an upper record's visual-LOD plan rectangle."""
    support = np.zeros(GN * GN, bool)
    for g in geo:
        for F in g["foot"]:
            for Q in pieces(F):
                cq = Q.mean(0)
                support[tri_w(cq[0], cq[2])[0].ravel()] = True
    return support


def end_fit(H_base, H_ref, H0, env, ctx, core, frz_all, paths=None):
    """Joint raise-only fit on the v6 channel terrain H_base; openings and the reported *_v4 values against the v4
    terrain H_ref (both as stored, float32). paths (v6r2): per site (centreline (n, 2), level): no raise may lift the
    planar terrain at a wet 0.5 m sample of it above level - PATH_UB (or above its current value where it is already
    higher), so the fit never dams the channel it is given."""
    H_v4 = H_base.astype(np.float32).astype(np.float64)                               # the base the fit raises
    Hf0 = H_v4.ravel()
    Href = H_ref.astype(np.float32).astype(np.float64).ravel()
    geo = [end_geometry(c) for c in ctx]
    support = footprint_support(geo)                                                    # vertices under a footprint
    # wet: below the site level, the sea or any adjacent envelope cell's level
    envmax = np.full((GN, GN), -np.inf)
    e_ = np.where(np.isfinite(env), env, -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            envmax[dr:dr + GN - 1, dc:dc + GN - 1] = np.maximum(envmax[dr:dr + GN - 1, dc:dc + GN - 1], e_)
    wet = (H_v4 < envmax) | (H_v4 < SEA)
    for c in ctx:
        wet[c["sub"]] |= H_v4[c["sub"]] < c["L"]
    sec = [sections(c) for c in ctx]
    w_v4 = [section_widths(Href, c["s"]["x"], c["s"]["z"], c["wd"], c["wn"], ts, c["W"] / 2 + 12, c["L"]) for c, ts in zip(ctx, sec)]
    open_v4 = [float(w.min()) for w in w_v4]
    open_base = [float(section_widths(Hf0, c["s"]["x"], c["s"]["z"], c["wd"], c["wn"], ts, c["W"] / 2 + 12, c["L"]).min()) for c, ts in zip(ctx, sec)]
    cap = np.full(GN * GN, np.inf)                                                     # per-vertex raise caps (shore)
    rows = build_rows(geo, ctx, Hf0, paths=paths)
    held = np.zeros(GN * GN, bool); held[np.unique(rows["A"][np.flatnonzero(rows["hard_lb"])].indices)] = True
    blocked = wet.ravel() | (frz_all.ravel() & ~support) | edge_mask()
    log, caps_log = [], []
    for rnd in range(FIT_ROUNDS):
        x, info = solve(rows, Hf0, blocked, cap)
        Hfit = (Hf0 + x).reshape(GN, GN)
        comp = []
        for i, c in enumerate(ctx):                                                   # widen what the raise narrowed
            Hfit, low = compensate(Hfit, c, sec[i], open_v4[i], held | (x > 0), frz_all, support)
            comp += low
        lb_rows = (rows["A"][rows["hard_lb"]], rows["b"][rows["hard_lb"]])
        Hfin, guard = slope_pass(Hfit, H0, core, frz_all, rows=lb_rows, cap=True)
        Hfin = Hfin.astype(np.float32).astype(np.float64)
        op = [float(section_widths(Hfin.ravel(), c["s"]["x"], c["s"]["z"], c["wd"], c["wn"], ts, c["W"] / 2 + 12, c["L"]).min()) for c, ts in zip(ctx, sec)]
        narrowed = [i for i, (a, b) in enumerate(zip(open_v4, op)) if b < a - 1e-6]
        log.append(dict(round=rnd + 1, lp=info, compensation_vertices=len(comp), narrowed=[ctx[i]["s"]["id"] for i in narrowed]))
        if not narrowed:
            break
        new = []
        for i in narrowed:                                                           # cap the raises that narrow, one by one
            new += cap_shore(Hfit, x, cap, ctx[i], sec[i], open_v4[i])
        caps_log += new
        if not new:
            break
    protect = np.isfinite(cap)                                                         # capped: water-limited
    # final measurement of every constraint on the final terrain
    rows_f = build_rows(geo, ctx, Hfin.ravel())
    v = rows_f["A"] @ Hfin.ravel(); v4v = rows_f["A"] @ Href
    Ab = rows_f["A"].copy(); Ab.data = (Ab.data > 1e-9).astype(float)
    rowblk = (Ab @ (wet.ravel() | protect).astype(float)) > 0                         # row touches a wet or capped vertex
    sites = []
    for i, (c, g) in enumerate(zip(ctx, geo)):
        sel = rows_f["site"] == i; fe = []
        for ei in sorted({e["end"] for e in g["ends"]}):
            kind = [e["kind"] for e in g["ends"] if e["end"] == ei][0]
            r = sel & (rows_f["end"] == ei) & (rows_f["kind"] == ("face" if kind == "block" else "ramp"))
            if kind == "block":
                expo = rows_f["y"][r] - v[r]
                fe.append(dict(end=ei, kind=kind, max_exposure_m=round(float(expo.max()), 4), max_exposure_v4_m=round(float((rows_f["y"][r] - v4v[r]).max()), 4)))
            else:
                air = rows_f["y"][r] - v[r]; wat = rowblk[r]; bad = air > 0.10
                fe.append(dict(end=ei, kind=kind, max_air_m=round(float(air.max()), 4), max_air_v4_m=round(float((rows_f["y"][r] - v4v[r]).max()), 4),
                               max_air_dry_m=round(float(air[~wat].max()), 4) if (~wat).any() else None,
                               points=int(r.sum()), points_over_0_10=int(bad.sum()), water_exceptions=int((bad & wat).sum()),
                               fill_over_cap_m=round(float(np.maximum(v[r] - np.maximum(v4v[r], rows_f["y"][r] - RAMP_CAP), 0).max()), 4)))
            zr = sel & (rows_f["end"] == ei) & (rows_f["kind"] == "zone")              # v6 deck-end zone, full width
            if zr.any():
                air = rows_f["y"][zr] - v[zr]; wat = rowblk[zr]; bad = air > 0.10
                fe[-1]["zone"] = dict(points=int(zr.sum()), max_air_m=round(float(air.max()), 4), max_air_v4_m=round(float((rows_f["y"][zr] - v4v[zr]).max()), 4),
                                      max_air_dry_m=round(float(air[~wat].max()), 4) if (~wat).any() else None,
                                      points_over_0_10=int(bad.sum()), water_exceptions=int((bad & wat).sum()))
            wr = sel & (rows_f["end"] == ei) & np.isin(rows_f["kind"], ("wing", "zwing"))   # v6r2 wings, hard rows
            if wr.any():
                dfc = rows_f["lb"][wr] - v[wr]; wat = rowblk[wr]; bad = dfc > 0.10
                fe[-1]["wings"] = dict(points=int(wr.sum()), max_deficit_m=round(float(dfc.max()), 4),
                                       max_deficit_dry_m=round(float(dfc[~wat].max()), 4) if (~wat).any() else None,
                                       points_over_0_10=int(bad.sum()), water_blocked=int((bad & wat).sum()))
        rs = sel & (rows_f["kind"] == "strip")
        rd = sel & (rows_f["kind"] == "deck")
        legs = {}
        for role in ("upper", "lower"):
            rl = sel & (rows_f["kind"] == "leg") & (rows_f["role"] == role)
            if rl.any():
                gaps = []
                for lid in np.unique(rows_f["leg"][rl]):
                    j = rl & (rows_f["leg"] == lid)
                    gaps.append(float(rows_f["y"][j].min() - v[j].max()))
                legs[role] = dict(n=len(gaps), hanging=int(sum(gp > 0.05 for gp in gaps)), max_gap_m=round(max(gaps), 3))
        msk = np.zeros((GN, GN), bool); msk[c["sub"]] = True
        sites.append(dict(fit_ends=fe, deck_strip_min_clear_m=round(float((rows_f["y"][rs] - v[rs]).min()), 4) if rs.any() else None,
                          deck_min_clear_m=round(float((rows_f["y"][rd] - v[rd]).min()), 4) if rd.any() else None,
                          legs=legs, opening_m=dict(v4=round(open_v4[i], 3), base=round(open_base[i], 3), v5=round(op[i], 3)),
                          fill_vertices=int(((Hfin > H_v4) & msk).sum()), fill_max_m=round(float((Hfin - H_v4)[msk].max()), 3),
                          lowered_vs_v4=int(((Hfin < H_v4) & msk).sum()),
                          stack=bool(c["lower"]), record_model=c["s"]["model"], variant_offset_m=round(c["dy_var"], 4)))
    stuck = steep_changed(Hfin, H0)
    summary = dict(rounds=log, capped_vertices=caps_log, capped_at_zero=int((protect & (cap <= 0)).sum()), slope_guard_steps_v5=guard,
                   slope_stuck_triangles=len(stuck), raised_vertices=int((Hfin > H_v4).sum()),
                   lowered_vertices_vs_v4=int((Hfin < H_v4).sum()))
    return Hfin, dict(sites=sites, summary=summary)


def sections(c):
    sn = abs(c["wd"][0] * c["d"][2] - c["wd"][1] * c["d"][0])                         # |sin| water axis vs road
    td = min(c["m"]["width"] / 2 / max(sn, 1e-3), 30.0)
    return np.arange(-td, td + 1e-9, 0.1)


def cap_shore(Hfit, x, cap, c, ts, target):
    """A site still narrowed after compensation: revert every raise of its window; if the opening is then back, give
    each raise back, least harmful first (narrowing it causes alone), as far as the opening allows (bisection), and cap
    it there; so a raise is cut only as far as the water needs (015-42: blocking the whole raised shore left two feet
    hanging 0.075 / 0.196 m) and raises that only narrow together are handled. Caps only shrink."""
    s = c["s"]; qmax = c["W"] / 2 + 12
    width = lambda H: float(section_widths(H.ravel(), s["x"], s["z"], c["wd"], c["wn"], ts, qmax, c["L"]).min())
    msk = np.zeros((GN, GN), bool); msk[c["sub"]] = True
    cand = np.flatnonzero((x > 1e-9) & msk.ravel())
    H = Hfit.copy(); Hr = H.ravel(); Hr[cand] -= x[cand]
    free = width(H)
    if free < target - 1e-9:                                                           # not the raises: nothing to cap
        return []
    goal = min(free, target + OPEN_MARGIN)
    harm = []
    for v in cand:
        Hr[v] += x[v]; harm.append(free - width(H)); Hr[v] -= x[v]
    out = []
    for v, _ in sorted(zip(cand, harm), key=lambda t: t[1]):
        Hr[v] += x[v]
        if width(H) >= goal:
            give = float(x[v])
        else:
            Hr[v] -= x[v]; lo, hi = 0.0, float(x[v])                                       # lo keeps the opening
            for _ in range(30):
                mid = (lo + hi) / 2; Hr[v] += mid
                if width(H) >= goal:
                    lo = mid
                else:
                    hi = mid
                Hr[v] -= mid
            give = max(lo - 1e-5, 0.0); Hr[v] += give
        if give < x[v] - 1e-9:
            cap[v] = min(cap[v], give)
            out.append(dict(site=s["id"], vertex=list(divmod(int(v), GN)), raise_m=round(float(x[v]), 4), cap_m=round(float(cap[v]), 4)))
    return out


def compensate(Hc, c, ts, target, held, frz_all, support, step=0.25):
    """Where the raise narrowed a wet section below the v4 opening, lower free bank vertices (dry, cut-allowed by the
    v4 rules, not held by any fit constraint, frozen ones only under a footprint) toward the bed, best gain first; the
    chosen vertex goes down only as far as the narrowed sections need (bisection within one step), so the opening comes
    back to the v4 width instead of jumping past it (a fixed 0.25 m step took a 015-25 fixture from 4.00 to 4.77 m
    between W = 5.9006 and 5.9004)."""
    s = c["s"]; qmax = c["W"] / 2 + 12
    w = section_widths(Hc.ravel(), s["x"], s["z"], c["wd"], c["wn"], ts, qmax, c["L"])
    if w.min() >= target:
        return Hc, []
    Hc = Hc.copy(); lowered = []
    r0, c0 = c["sub"][0].start, c["sub"][1].start
    cand = np.argwhere(c["cut_allowed"]) + [r0, c0]
    for _ in range(200):
        bad = w < target
        if not bad.any():
            break
        tb = ts[bad]; base = (target - w[bad]).sum(); best = (0.0, None)
        wetm = Hc < c["L"]
        for r, cc in cand:
            fl = r * GN + cc
            if held[fl] or Hc[r, cc] <= c["bed"] + 1e-6 or (frz_all[r, cc] and not support[fl]) or wetm[r, cc]:
                continue
            if not (wetm[max(r - 1, 0):r + 2, max(cc - 1, 0):cc + 2].any()):
                continue
            h = Hc[r, cc]; Hc[r, cc] = max(c["bed"], h - step)
            if any(math.degrees(math.atan(math.hypot(*tri_grad([Hc[a] for a in tri_ids(r0_, c0_, hf)], hf)))) > SLOPE_MAX + 1e-9 and
                   math.degrees(math.atan(math.hypot(*tri_grad([Hc[a] if a != (r, cc) else h for a in tri_ids(r0_, c0_, hf)], hf)))) <= SLOPE_MAX
                   for r0_, c0_, hf in ((r - 1, cc - 1, 0), (r - 1, cc - 1, 1), (r - 1, cc, 1), (r, cc - 1, 0), (r, cc, 0), (r, cc, 1))):
                Hc[r, cc] = h; continue
            gain = base - np.maximum(target - section_widths(Hc.ravel(), s["x"], s["z"], c["wd"], c["wn"], tb, qmax, c["L"]), 0).sum()
            Hc[r, cc] = h
            if gain > best[0] + 1e-9:
                best = (gain, (r, cc))
        if best[1] is None:
            break
        r, cc = best[1]; h = Hc[r, cc]; full = h - max(c["bed"], h - step)

        def enough(dl):
            Hc[r, cc] = h - dl
            return bool(section_widths(Hc.ravel(), s["x"], s["z"], c["wd"], c["wn"], tb, qmax, c["L"]).min() >= target + OPEN_MARGIN)
        if enough(full):                                                                # smallest lowering that suffices
            lo, hi = 0.0, full
            for _ in range(30):
                mid = (lo + hi) / 2
                if enough(mid):
                    hi = mid
                else:
                    lo = mid
            Hc[r, cc] = h - hi
        else:
            Hc[r, cc] = h - full
        lowered.append((int(r), int(cc)))
        w = section_widths(Hc.ravel(), s["x"], s["z"], c["wd"], c["wn"], ts, qmax, c["L"])
    return Hc, sorted(set(lowered))


_EDGE = None


def edge_mask():
    global _EDGE
    if _EDGE is None:
        e = np.zeros((GN, GN), bool); e[0, :] = e[-1, :] = e[:, 0] = e[:, -1] = True; _EDGE = e.ravel()
    return _EDGE


def build_rows(geo, ctx, Hf, paths=None):
    """Constraint rows on vertex heights: value = A @ H. kinds: face (>= y - FACE_TOL), ramp (>= y - RAMP_AIR; cap rows <=),
    leg (>= foot - LEG_TOL), zone (>= underside - END_AIR), wing and zwing (>= the 1:WING profile; hard since v6r2),
    deck and strip (<=), path (<= level - PATH_UB at 0.5 m samples of each site's centreline, when paths are given)."""
    R = dict(idx=[], w=[], y=[], lb=[], ub=[], kind=[], site=[], end=[], role=[], leg=[], soft=[], top=[])
    def add(P, lb, ub, kind, i, end=-1, role="", leg=-1, soft=False, top=np.nan):
        if not len(P):
            return
        P, iu = np.unique(P.round(6), axis=0, return_index=True)
        ix, w = tri_w(P[:, 0], P[:, 2])
        n = len(P)
        R["idx"].append(ix); R["w"].append(w); R["y"].append(P[:, 1])
        bnd = lambda v: v(P) if callable(v) else (np.asarray(v, float)[iu] if np.ndim(v) else np.full(n, v))
        R["lb"].append(bnd(lb)); R["ub"].append(bnd(ub))
        R["kind"] += [kind] * n; R["site"] += [i] * n; R["end"] += [end] * n; R["role"] += [role] * n; R["leg"] += [leg] * n; R["soft"] += [soft] * n
        R["top"] += [top] * n
    leg_id = 0
    for i, g in enumerate(geo):
        for e in g["ends"]:
            if e["kind"] == "block":
                P, _ = face_points(e["faces"])
                add(P, lambda P: P[:, 1] - FACE_TOL, np.inf, "face", i, e["end"])
            else:
                st = e["seat"]
                P, _ = face_points(e["faces"])
                add(P, lambda P: P[:, 1] - RAMP_AIR, np.inf, "ramp", i, e["end"])
                caps = [lambda Q: Q[:, 1] - RAMP_CAP] * len(e["faces"])
                P, pos = face_points(e["faces"], Hf, caps)
                if len(P):
                    T = terrain_at(Hf, P[:, 0], P[:, 2])
                    ub = np.where(pos, np.maximum(P[:, 1] - RAMP_CAP, T), T)
                    add_ub = P.copy()
                    ix, w = tri_w(add_ub[:, 0], add_ub[:, 2]); n = len(add_ub)
                    R["idx"].append(ix); R["w"].append(w); R["y"].append(add_ub[:, 1]); R["lb"].append(np.full(n, -np.inf)); R["ub"].append(ub)
                    R["kind"] += ["cap"] * n; R["site"] += [i] * n; R["end"] += [e["end"]] * n; R["role"] += [""] * n; R["leg"] += [-1] * n; R["soft"] += [False] * n
                    R["top"] += [np.nan] * n
                # wings: 1:WING beside the ramp (soft)
                M = e["matrix"]; ax = ctx[i]["m"]["axis"]; lat = 2 - ax; cl = ctx[i]["m"]["centre_lat"]
                aa = np.linspace(0.5, st["a_seat"] - 0.1, 5); pts, yy = [], []
                for side, l0 in ((-1, st["lat_lo"]), (1, st["lat_hi"])):
                    for r in (0.5, 1.0, 2.0, 3.0, 4.5):
                        p = np.zeros((len(aa), 3)); p[:, ax] = e["e"] + e["inw"] * aa; p[:, lat] = cl + l0 + side * r
                        p[:, 1] = st["y0"] + st["slope"] * aa - RAMP_CAP - r / WING
                        pts.append(to_world(M, p))
                P = np.concatenate(pts)
                add(P, lambda P: P[:, 1], np.inf, "wing", i, e["end"], soft=WING_SOFT, top=st["y0"] + st["slope"] * st["a_seat"] - RAMP_CAP)
        for zn in g["zones"]:                                                          # v6 deck-end zone, full width
            P, _ = face_points([zn["poly"]])
            add(P, lambda P: P[:, 1] - END_AIR, np.inf, "zone", i, zn["end"])
            z_, M = zn["zone"], zn["matrix"]; ax = ctx[i]["m"]["axis"]; lat = 2 - ax; cl = ctx[i]["m"]["centre_lat"]
            ya = z_["y0"] + z_["slope"] * z_["a_end"] - END_AIR
            # v6r2: the wings as exact planar polygons (v6: 9 reaches x 7 lateral samples, which missed the 015-13 end-0
            # triangle 0.74 m under the profile): beyond the zone, WING_BEYOND m toward the channel across the zone width,
            # y = ya - r / WING; beside it, WING_SIDE m out from each side, y = plane(a) - END_AIR - r / WING; each cut
            # where it falls to the level + 0.3 (the wing ends at the water), then split by the terrain triangles
            quads = [[(z_["a_end"], z_["lat_lo"], ya), (z_["a_end"] + WING_BEYOND, z_["lat_lo"], ya - WING_BEYOND / WING),
                      (z_["a_end"] + WING_BEYOND, z_["lat_hi"], ya - WING_BEYOND / WING), (z_["a_end"], z_["lat_hi"], ya)]]
            for side, l0 in ((-1, z_["lat_lo"]), (1, z_["lat_hi"])):
                y_a = lambda a_, r_: z_["y0"] + z_["slope"] * a_ - END_AIR - r_ / WING
                quads.append([(0.0, l0, y_a(0.0, 0.0)), (z_["a_end"], l0, y_a(z_["a_end"], 0.0)),
                              (z_["a_end"], l0 + side * WING_SIDE, y_a(z_["a_end"], WING_SIDE)), (0.0, l0 + side * WING_SIDE, y_a(0.0, WING_SIDE))])
            polys = []
            for qd in quads:
                p = np.zeros((4, 3))
                for j, (a_, l_, y_) in enumerate(qd):
                    p[j, ax] = zn["e"] + zn["inw"] * a_; p[j, lat] = cl + l_; p[j, 1] = y_
                Wq = to_world(M, p); hi_ = split(Wq, Wq[:, 1], ctx[i]["L"] + 0.3)[1]
                if len(hi_) >= 3:
                    polys.append(hi_)
            P, _ = face_points(polys)
            P = P[P[:, 1] > ctx[i]["L"] + 0.3 - 1e-9]
            add(P, lambda P: P[:, 1], np.inf, "zwing", i, zn["end"], soft=WING_SOFT, top=ya)
        for ei, P3 in g["strips"]:
            P, _ = face_points([P3])
            add(P, -np.inf, lambda P: P[:, 1] - DECK_CLEAR, "strip", i, ei)
        P, _ = face_points(g["deck"])
        add(P, -np.inf, lambda P: P[:, 1] - DECK_CLEAR, "deck", i)
        for role, k, F in g["legs"]:
            add(F, lambda P: np.full(len(P), P[:, 1].min()) - LEG_TOL, np.inf, "leg", i, role=role, leg=leg_id)
            leg_id += 1
    for i, (cl, L) in enumerate(paths or []):                                           # v6r2 the channel stays wet
        if len(cl) < 2:
            continue
        Q = resample(np.asarray(cl, float), 0.5)
        Q = Q[terrain_at(Hf, Q[:, 0], Q[:, 1]) < L]                                    # only where there is water to keep (the
        P = np.column_stack([Q[:, 0], np.full(len(Q), L), Q[:, 1]])                    # overlap fixture: 015-13b's dry path under
        add(P, -np.inf, L - PATH_UB, "path", i)                                         # 015-13's block bared it 1.17 m)
    idx = np.concatenate(R["idx"]); w = np.concatenate(R["w"]); n = len(idx)
    A = csr_matrix((w.ravel(), idx.ravel(), np.arange(0, 3 * n + 1, 3)), shape=(n, GN * GN))
    A.eliminate_zeros()
    out = dict(A=A, y=np.concatenate(R["y"]), lb=np.concatenate(R["lb"]), ub=np.concatenate(R["ub"]),
               kind=np.array(R["kind"]), site=np.array(R["site"]), end=np.array(R["end"]), role=np.array(R["role"]),
               leg=np.array(R["leg"]), soft=np.array(R["soft"]), top=np.array(R["top"], float))
    out["b"] = out["lb"]
    out["hard_lb"] = np.isfinite(out["lb"]) & ~out["soft"]
    return out


def tri_ids(r0, c0, half):
    return ((r0, c0), (r0, c0 + 1), (r0 + 1, c0 + 1)) if half == 0 else ((r0, c0), (r0 + 1, c0 + 1), (r0 + 1, c0))


def tri_grad(Hv, half):
    """Gradient (per metre) of a triangle from its three heights, as tri_slopes."""
    a, b, c = Hv
    return ((b - a) / 6.0, (b - c) / 6.0) if half == 0 else ((b - c) / 6.0, (a - c) / 6.0)


def slope_rows(cols, Hf):
    """Linear rows (raises of cols) keeping every triangle around them under SLOPE_MAX (inscribed octagon of the slope
    circle) unless it was already steeper; right-hand side never below what the current terrain uses."""
    pos = {int(v): i for i, v in enumerate(cols)}; rows, rhs = [], []
    lim = math.tan(math.radians(SLOPE_MAX)) * math.cos(math.radians(22.5))
    seen = set()
    for v in cols:
        r, c = divmod(int(v), GN)
        for r0, c0, half in ((r - 1, c - 1, 0), (r - 1, c - 1, 1), (r - 1, c, 1), (r, c - 1, 0), (r, c, 0), (r, c, 1)):
            if (r0, c0, half) in seen or not (0 <= r0 < GN - 1 and 0 <= c0 < GN - 1):
                continue
            seen.add((r0, c0, half))
            ids = [a * GN + b for a, b in tri_ids(r0, c0, half)]
            gx, gz = tri_grad([Hf[i] for i in ids], half)
            if math.degrees(math.atan(math.hypot(gx, gz))) > SLOPE_MAX:
                continue
            ex = tri_grad(np.eye(3), half)                                             # coefficients per vertex
            for th in (0.0, 45.0, 90.0, 135.0):
                co = np.cos(np.radians(th)) * np.array(ex[0]) + np.sin(np.radians(th)) * np.array(ex[1])
                cur = float(co @ [Hf[i] for i in ids])
                for sg in (1.0, -1.0):
                    row = {pos[i]: sg * co[j] for j, i in enumerate(ids) if i in pos and abs(co[j]) > 0}
                    if row:
                        rows.append(row); rhs.append(max(lim - sg * cur, 0.0))
    data, ri, ci = [], [], []
    for k, row in enumerate(rows):
        for j, val in row.items():
            ri.append(k); ci.append(j); data.append(val)
    return csr_matrix((data, (ri, ci)), shape=(len(rows), len(cols))), np.array(rhs)


def solve(rows, Hf, blocked, cap=None):
    """min sum(raise) + 1000 sum(hard deficit) + 2 sum(soft deficit); raise >= 0 only on free vertices, never more than a
    row it serves needs (deficit / weight, for weights >= 0.05) nor more than OVER_MAX above that row's bound (no spikes
    on far vertices; v6r2: a wing row lets its vertices reach the wing's top, the zone plane, as G13's raises may: v6
    left 015-13 end 0 0.74 m under the 1:1.5 profile where one bank vertex could close it) nor more than its shore cap;
    upper rows never pushed above max(current, bound)."""
    from scipy.sparse import hstack, vstack, identity
    A, lb, ub = rows["A"], rows["lb"], rows["ub"]
    cur = A @ Hf
    has_lb = np.isfinite(lb) & (lb > cur + 1e-9)
    x = np.zeros(GN * GN)
    if not has_lb.any():
        return x, "nothing to raise"
    li = np.flatnonzero(has_lb)
    Al = A[li].tocoo()
    dfc, lbe = (lb[li] - cur[li])[Al.row], lb[li][Al.row] - Hf[Al.col]                 # row deficit, row bound over vertex
    tr_ = rows["top"][li][Al.row]                                                       # v6r2 wings: up to the wing top
    reach = np.where(np.isfinite(tr_), np.maximum(tr_ - Hf[Al.col], lbe + OVER_MAX), lbe + OVER_MAX)
    need = np.where(Al.data >= 0.05, np.minimum(dfc / np.maximum(Al.data, 1e-9), reach), lbe)
    top = np.full(GN * GN, -np.inf); np.maximum.at(top, Al.col, need)                    # largest useful raise per vertex
    if cap is not None:
        top = np.minimum(top, cap)
    cols = np.unique(Al.col); cols = cols[~blocked[cols] & (top[cols] > 1e-9)]
    if not len(cols):
        return x, "nothing free to raise"
    Ac = A[:, cols]
    ui = np.flatnonzero(np.isfinite(ub) & (Ac.getnnz(axis=1) > 0))
    Sa, sb = slope_rows(cols, Hf)
    nv, ns = len(cols), len(li)
    G1 = hstack([-Ac[li], -identity(ns, format="csr")])
    h1 = -(lb[li] - cur[li])
    G2 = vstack([hstack([Ac[ui], csr_matrix((len(ui), ns))]), hstack([Sa, csr_matrix((Sa.shape[0], ns))])])
    h2 = np.concatenate([np.maximum(ub[ui] - cur[ui], 0.0), sb])
    pen = np.where(rows["soft"][li], 2.0, 1000.0)
    res = linprog(np.concatenate([np.ones(nv), pen]), A_ub=vstack([G1, G2]).tocsr(), b_ub=np.concatenate([h1, h2]),
                  bounds=list(zip(np.zeros(nv), top[cols])) + [(0, None)] * ns, method="highs")
    if res.status != 0:
        refuse(f"end fit LP failed: {res.message}")
    x[cols] = np.where(res.x[:nv] > 1e-7, res.x[:nv], 0.0)
    return x, f"{res.message} ({nv} vertices, {ns} lower rows, {len(ui)} upper rows)"


if __name__ == "__main__":
    main()
