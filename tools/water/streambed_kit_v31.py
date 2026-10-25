"""Thin streams with the vanilla streambed kit laid on the grid lattice like Chernarus (v9, 17-10; v8 = 15-10 lattice;
v7 = 14-10 pilot).

v9 (17-10, Guillermo in game on EV110 and the rollout decision 'Kit en malla' for the polygonal thin streams of the whole map):
  stones    kit-118: 'las piedras bien colocadas pero los monticulos de tierra estan descentrados y en el aire'. v8 put a group
            2.3 m off the corner VERTEX (the PI, metres outside the real curve) with its origin at terrain - 0.08: the mounds
            sat 3.8-5.3 m (p50) from the channel and their base ring floated (max gap p50 0.17-0.30 m, p90 0.84; stone check of
            17-10). v9 places them like Chernarus (572 stones within 30 m of 1,639 streambed pieces, measured against the REAL
            piece centrelines, E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-wip/kit/chern-stones.json): STONES_PER_KM per
            site, model by the Chernarus counts of the family, q (distance to the real centreline: rung midpoints of every piece
            of the site) and yaw relative to the local centreline tangent drawn in the model's Chernarus p25-p75 band
            (STONE_BANDS), on the outer bank at a corner (within 12 m) and on a random bank elsewhere. Vertical: the base ring
            (stones_geometry: the visual-LOD vertices at or below the model's 10th y percentile; with a yaw-only matrix they are
            also the lowest 10 % in world y) goes STONE_SINK below the final terrain at its deepest-standing vertex, i.e.
            max(base y - terrain) = -STONE_SINK. A stone is moved out in 0.25 m steps (up to the band's p75 + STONE_Q_EXTRA,
            then the other bank) while it would block the visible sheet (share of its sampled vertices above visible kit water >
            STONE_BLOCK, below the Chernarus p90 0.245 because the gate counts every LOD vertex) or stand above the water within
            STONE_RIBBON of the centreline (gate: 0.6 m), touch a triangle with a frozen vertex, stand over kept pond water,
            come within STONE_GAP of another stone's origin, or be left with less than STONE_VIS_MIN of its sampled vertices
            above the terrain once its base is buried (a hidden stone). A kind with no position left is replaced by
            STONE_FALLBACK; then the station moves by +-STONE_SHIFT (12 m, three more tries inside the wet span); then the stone
            is dropped. The water is that of every site's pieces (junctions). Measured in a dev run of 17-10: bars and curved
            bars (6 x 10.6 m plates) need their origin 0.8-1.0 m deep to bury the base across the 0.32 m/m V seat and are then
            hidden (visible share p50 0.00); Chernarus leaves them floating (base gap p50 0.43 / 0.34 m), which is what
            Guillermo saw as 'monticulos ... en el aire'. So a bar stands only where the bank is flat enough to show it. v8's
            stone draws are still made (and discarded) so the piece-variant draws of every site stay those of v8.
  reach     site mode 'reach' (kit_worklist_v31.py): the body is the given list of thin vertices (one stem of the census, not
            the whole wet component), the course is the given stem (upstream first) plus straight extensions to an earlier
            site's course at 'kit' ends. Pond cells are removed as in v8 (plane in the body's range, within CUT_Q of the path or
            touching the body dilated twice, which takes the dry envelope rings of the banks) but only when they touch no kept
            wet vertex (wet in the input and in no site's body): wide water, bridge zones and streams left out keep their water
            (the long-pending 'reach-only body' mode). Exception, the seat corridor: a cell with a vertex within RING1 of the
            path is removed even when it touches kept water, so no ring vertex is frozen under the kit; the kept water ends at a
            sill just outside. Mode 'component' (default; kit-118, kit-7) is v8 unchanged.
  junctions kit/pond (bridge zone, wide water, a stream left out, the sea if ever met): a vertex of a kept envelope cell that
            is also a vertex of a removed cell and lies below its kept plane + 0.05 would be a NEW exposed pond edge
            (bury_edges_v31.py raises it afterwards, which G6 refuses); v9 raises it to plane + SILL_UP (bury's own target)
            as a sill, and ends the chain SILL_CLEAR before it. The chain therefore stops short, the pond keeps its water and a
            low sill closes it; the dry strip between the two sheets is measured per junction by the gates. A frozen vertex
            cannot be a sill, nor a vertex next to one (a sill raised against a road embankment steepened a 42 deg face in
            the third rollout): the removed cells around it are given back (the kept water ends one cell further out). kit/kit (a
            branch meeting an earlier site): the branch course runs to the earlier course and the chain is trimmed KK_CLEAR off
            the earlier lattice polyline; an earlier site's channel (its seat rings, sills and the triangles under its axis
            samples) can only be lowered by a later site (a later seat notches the earlier bank, never fills its channel); its
            other changes (outer banks, filled pits) may be raised, so the later sheet stays buried (130.0-1 showed 6 m out
            over 130.0-0's bank in a dev run of 17-10). kit/road: the worklist stops the reach FROZEN_R short of
            reserve/platform/narva (and v31_bridge_cut) vertices, the chain is trimmed END_CLEAR off them as in v8, and the
            old water up to the road is removed with the reach (Chernarus: 26 of 65 channel ends at a road have nothing,
            15 a culvert, 24 a bridge; no culvert is placed here). kit/bridge: the worklist keeps R_BRIDGE (75 m) of pond
            around every bridge site (the bridge pass cuts and seals up to 60 m along the water axis and needs that water).
  frozen    reach mode treats v31_bridge_cut (the 015-15 pilot cut) like reserve/platform/narva for the path and the ends,
            and keeps the path one vertex step off envelope water at another level and off those frozen vertices (a ring-0
            vertex 6 m from a road embankment cut a 35 deg face in a dev run of 17-10).
  strays    after the mound pass, a wet patch of a reach site's sheet cut off from its channel is buried (bury_strays: the
            movable vertices under it are raised to the sheet + BURY, and that becomes their floor).
  sea       the axis rule and the slope guard never lower a vertex below LOW_FLOOR (0.80; a dev run of 17-10 made 9 new
            engine-sea vertices, terrain < 0.75 off the envelope, down to 0.21 m). Reach mode keeps the roadway at least
            REACH_Y_MIN (1.45, v8 1.33): at 1.33 the curve lips of three low reaches needed an outer vertex at 0.78 m.
  mounds    Guillermo, 17-10: 'a los lados hay monticulos poligonales piramidales que suavizar'. On the 6 m NW-SE grid a
            pyramid is a small shape standing above everything around it: a single vertex, an edge pair or a native
            triangle whose lowest vertex is more than MOUND_T above the highest vertex of its native ring (the shapes of the
            despike track's census, ev112-wip/despike; EV107 has 3,563 single vertices > 0.30 m above all six neighbours).
            After all sites, inside MOUND_Q of any site's lattice polyline (the path itself, not its 40 m extensions), every
            such shape whose vertices are all movable (not frozen, not a vertex of an envelope cell left at the end, not set
            by a seat, not a sill) is laid down to its ring's
            highest vertex (lower-only, never below the kit's burial floor yq + 0.25 + BURY within OUTER nor MOUND_FLOOR), up
            to MOUND_PASSES times. Only such shapes move: a first version eroded every convex vertex (mean of the
            neighbours + 0.15 m) and lowered 22,934 band vertices by up to 3.6 m, shaving ridges that are not pyramids.
            A seat-ring vertex the exact V left standing more than MOUND_T above all six neighbours (a ring-1 vertex at a
            chain end or corner in low land: 6 of them in a dev run of 17-10, up to 1.25 m) is lowered to their highest +
            MOUND_RING (the waterline bulges there by a few decimetres). The slope guard runs after it, and the shapes are laid
            once more after the guard. '--no-mounds' skips all of it (used by the regression check against EV110).
v8 (15-10) follows; every rule below still holds for both modes unless the v9 notes above say otherwise.

Decisions of 15-10 (Guillermo, and the orchestrator's defaults he judges in game): the kit is re-laid on the lattice as in
Chernarus; NE-SW reaches are slanted elbow staircases; ring 1 of the V is set exactly (cutting allowed); width as the v8
prototype (HW 1.8 m). v8 replaces v7's free-heading chords and distance-to-chord seat, which drew hexagonal, variable-width
edges (Guillermo, 13-10) because the waterline crossed non-planar triangles.

Measured on Chernarus (E:/DayZ-Baltic-Build/vanilla-tricks-20261013/REPORT.md section 3, scratchpad turn-pieces/turn-pieces.json):
  pieces    dz\\water\\streambed\\streambed_<family>_<kind>.p3d, model +Z upstream. long/short_straight: 14 m plate, 24 / 12 m;
            long_curve_left/right: 45-deg turn (44.36 / -44.53 deg measured), PI at the crossing of the two end tangents;
            short_slanted (model Z always E-W) and short_slanted_inv (always N-S): 6.7 x 11.9 m plates with mitred ends on the
            NW-SE diagonal, paired at every 90-deg elbow with their origins at mid-cell on the two vertex lines.
  lattice   Chernarus' straights lie on vertex lines (N-S, E-W, and the NW-SE triangle diagonal), curves join an axis line to
            the diagonal, elbows join N-S to E-W; NE-SW reaches are elbow staircases.
  geometry  streambed_kit_geometry_v31.json (extract_streambed_geometry_v31.py, from the ODOL files): roadway LOD faces with
            their texture (water_ext flat run, concrete_ext end lips dropping 0.69 m over the last 3 m) and LOD0 of the
            CalmWater proxy (the roadway outline incl. the lips, +0.25 m; +0.20 m slanted). Every height and coverage test below
            uses these faces. Stones: streambed_stones_geometry_v31.json (extract_stones_geometry_v31.py).
  seat      terrain minus roadway across the axis: -0.33 at 0 m (Chernarus), linear V around a vertex line (see terrain).

Per site (JSON list: id, seed [x, z], family; v9 reach sites: id, mode 'reach', family, stem [[r, c] ...] upstream first,
body [[r, c] ...], ends {up, dn}, extend {side: {partner, to [x, z]}}): body, smoothed thalweg (upstream first) and water
profile W as v7 (14-10).
  path      Dijkstra over states (vertex, heading, run since the last corner, last corner type), on vertices <= DMAX from the
            thalweg and not reserve/platform/narva. Headings N, S, E, W (6 m) and NW, SE (8.49 m), never NE/SW. Step cost
            L (LAMBDA + (d / SIGMA)^2), d = distance to the thalweg; TURN_COST per corner, corners closer than MIN_RUN refused.
            Turns: 45 deg between an axis heading and the diagonal (curve); 90 deg only N<->E and S<->W (elbow), as Chernarus.
  curve     PI on the corner vertex, scale CURVE_S (0.80-1.00, adjusted by 0.02 until every run can be filled), flat at the mean
            profile of its two plate ends. The model turns 44.36 / 44.53 deg, not 45: the piece is rotated about the PI by half
            the deficit so both end tangents miss their vertex lines by the same angle; the measured end offsets go to the
            report (v8 prototype aligned the entry only: exit ends 0.10-0.14 m off the line, review of 15-10).
  elbow     slanted on the E-W leg, slanted_inv on the N-S leg, scale SLANT_S, origin at mid-cell (3 m from the corner) on the
            leg line, model +Z upstream along the leg, flat at the profile of its origin; a one-cell tread shared by two
            elbows carries one piece.
  straights centred on the vertex line, long/short mix with one scale per run (0.90-1.06) and one overlap; pitched between the
            profile at their two plate ends; 25 % long_straight_2. Every joint overlaps: plate ends overlap by at least
            max(OV_FLOOR, lip_a + lip_b - DIP_SPAN) (lips = the concrete_ext run of each plate end, scaled), at most OV_MAX;
            a direct corner-to-corner joint needs the same overlap. The prototype accepted gaps up to +0.5 m (six interior
            gaps of 0.05-0.34 m in kit-7, review of 15-10); DIP_SPAN keeps the roadway at a joint within ~0.2 m of the flat run.
  ends      end pieces whose span passes within END_CLEAR of a reserve/platform/narva vertex or of visible water at another
            level, or within RING1 + 0.5 m of a vertex of an envelope cell at another level, are dropped (v7 rule, RING1 + 0.5
            instead of v7's TRENCH + 0.5 because the lattice seat reaches 6 m). v9 reach mode adds the sills (SILL_CLEAR),
            earlier sites' lattice polylines (KK_CLEAR), any native triangle under the piece's span or centreline with a
            vertex of a kept envelope cell (a sill at its target height) higher than the piece's roadway - AXIS_CLEAR (the
            axis rule could not lower it), and any face vertex of the piece in a triangle with a reserve/platform/narva/
            v31_bridge_cut vertex (no kit piece on a road platform; END_CLEAR along the axis let 0.4-0.55 m of 14 m plate
            show over five roads in a dev run of 17-10).
  profile   roadway Y(s) on the lattice polyline (0.5 m samples): v7 rule, W from the nearest thalweg sample, bank land = median
            terrain 5/7.5/10 m to either side, Y = min(W - 0.25, land - NEED6), 20 m moving average, monotone, >= BED_MIN +
            0.33.
  terrain   q = distance of a vertex to the lattice polyline (extended straight beyond both path ends), yq = Y at its station.
            ring 0 (q < 0.01): yq + SEAT0; ring 1 (q <= RING1): yq + SEAT0 + SLOPE q, set exactly (raising or cutting): the
            waterline then crosses only ring0-ring1 triangles, which are planar strips along a vertex line, so the edge is
            straight and of constant width (half width (0.25 - SEAT0) / SLOPE = HW). Outer (RING1 < q <= OUTER): raised only, to
            yq + 0.25 + BURY, capped by the v7 seat table, so no part of the 14 m sheet shows beyond ring 1. Beyond the chain
            ends (station outside the plate span): raised only, to at most yq + END_RISE (v7), burying the end lips.
  axis      every axis sample (the lattice polyline every AXIS_STEP and every piece's rung-midpoint centreline every AXIS_STEP,
            joints included, from the first piece's flat run to the last one's) keeps the planar terrain AXIS_CLEAR below the
            highest roadway face of the kit there (all textures; a sample with no roadway face is a gap and stays
            unresolved; the outer lips of the two chain ends are buried by design and are not samples). An excess is taken
            from the movable triangle vertices with barycentric weight >= AXIS_W, at most AXIS_DROP below the target (v7 kept
            the target as a floor, which leaves a sample unresolved when a low-weight vertex holds it up), ring-0 vertices only
            when no other vertex qualifies (the review of 15-10 found samples on ring-0 edges
            whose off-axis weight is 0, e.g. (8274, 8986.36), margin 0.082). Run before and after the pit fill; ring-0 and
            ring-1 vertices it lowers are counted (ring 1 is no longer exact there, mostly inside curves and elbows).
  ponds     every cover and envelope cell with a plane in the body's range within CUT_Q of the lattice polyline or touching the
            body is removed (v7); cover and envelope removals are counted separately (prototype reported max of both).
            v9 reach mode: see 'reach' above.
  pits      v7: the old bed left without water is filled to its spill level; other vertices only by the growth of their
            closed-depression depth; drains = seat, axis-lowered, frozen, protected vertices and the window border.
  slopes    v7 guard after all sites: a changed triangle steeper than max(35 deg, before) has its highest vertex lowered in 0.1
            m steps when movable (not seat, frozen or protected), up to WALL_STEPS passes. Lowering never reduces an axis
            margin. v9: movable also covers the native neighbours of the touched band, never a kept-envelope vertex or a sill,
            and never below LOW_FLOOR nor the burial floor yq + 0.25 + BURY within OUTER (a lowered bank let the 14 m sheet show
            in three small patches beside 41.0-0 in a dev run of 17-10); a dry rim vertex of a kept envelope cell may be lowered
            too, never below its highest incident kept plane + SILL_UP (it stays a buried pond edge); when the top cannot move
            (a kept pond rim), the lowest vertex of the triangle is raised in 0.1 m steps instead, if movable and under no axis
            sample (7 such triangles, 35-45 deg, in a dev run of 17-10).
  stones    v8 (replaced in v9, see above): a stones group 2.3 m out on the outer bank of each corner at least 18 m after the
            previous group, plus one every 60 m, on the final terrain 0.08 m deep (v7).
  check     the axis margins are recomputed on the final float32 terrain (report: samples, min, below AXIS_MIN = 0.10, no
            roadway face, share of samples whose highest water_ext face alone keeps AXIS_MIN). The server gave kit water only
            with >= 0.10 m (streams/README.md, EV108 probe); AXIS_CLEAR 0.12 leaves 2 cm for the float32 store and the sampling
            step. This margin is GEOMETRIC: the EV108 probe read water on water_ext faces only (it had no point elsewhere),
            and about a quarter of the axis samples, nearly every joint, lie on concrete_ext lips only. Engine water there is
            unverified until the server probe of probe_points_kit.py's kit_lip / kit_joint points (review of 15-10).
Reserve/platform/narva vertices never change; vertices of the envelope cells left at the end are raised only as sills and
lowered only as dry rims staying at or above their highest kept plane + SILL_UP (asserts).
Usage: streambed_kit_v31.py <terrain.npz> <footprint.npz> <cover.npy> <envelope.npy> <sites.json> <out_terrain.npz>
       <out_cover.npy> <out_envelope.npy> <records.json> <report.json> [--no-mounds]
Records: site, piece, model, matrix (columns X, Y, Z scaled, then T: world = T + M . stored), kind, scale, station (plate-end
stations on the lattice polyline), pitch_deg; stones: piece 'stones', model, matrix, kind, q, yaw_rel_deg, side, sink.
Report schema streambed-kit-v31.v9: per site the mode, ends, lattice polyline, wet span, corners, curve end offsets, joints,
axis checks, terrain counters, sills and stones; globally the mound pass and the object counts.
"""
import json, math, sys, heapq, time
from collections import deque
from pathlib import Path
import numpy as np
from scipy.ndimage import label, binary_dilation
from scipy.spatial import cKDTree

ZTOP = 12282.0
GEOM_PATH = Path(__file__).with_name("streambed_kit_geometry_v31.json")
DIRS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1), "NW": (-1, -1), "SE": (1, 1)}
HEAD = {"N": 0, "E": 90, "S": 180, "W": 270, "NW": 315, "SE": 135}
DN = list(DIRS)
LAMBDA, SIGMA, DMAX = 0.3, 2.5, 12.0
TURN_COST = {"curve": 10.0, "elbow": 14.0}
MIN_RUN = {("start", "curve"): 10.0, ("start", "elbow"): 4.0, ("curve", "curve"): 18.0, ("curve", "elbow"): 14.0,
           ("elbow", "curve"): 14.0, ("elbow", "elbow"): 6.0}
CURVE_S, CURVE_S_MIN, CURVE_S_MAX, SLANT_S = 0.88, 0.80, 1.00, 0.82
S_MIN, S_MAX = 0.90, 1.06
OV_FLOOR, DIP_SPAN, OV_MAX, OV_PREF, DIRECT_MAX = 0.3, 3.5, 5.0, 2.5, 7.5
SEAT0, HW = -0.33, 1.8
SLOPE = (0.25 - SEAT0) / HW                                     # 0.322 / m
RING1 = 6.01
OUTER, BURY, END_RISE = 13.0, 0.10, 0.5
SEAT_OQ, SEAT_OH = [3.0, 4.5, 6.0, 9.0, 12.0, 14.0], [0.70, 1.30, 1.81, 2.50, 3.13, 3.40]   # v7 outer cap
NEED6, BED_MIN, CUT_Q, END_CLEAR = 1.06, 1.0, 10.0, 6.0
AXIS_STEP, AXIS_CLEAR, AXIS_MIN, AXIS_W, AXIS_PASSES, AXIS_DROP = 0.25, 0.12, 0.10, 0.15, 40, 1.0
WALL_STEPS = 60
EXTEND = 40.0                                                   # polyline extension beyond both path ends (m)
NATIVE = ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1))
STONES = ["group_1", "group_2", "group_3", "group_3", "bar", "bar_curve"]

# ---------------------------------------------------------------- v9 (17-10)
STONES_GEOM_PATH = Path(__file__).with_name("streambed_stones_geometry_v31.json")
STONES_PER_KM = 17.0                                            # Chernarus: 572 stones within 30 m of 33.6 km of streambed
STONE_SINK, STONE_BLOCK, STONE_RIBBON, STONE_GAP, STONE_Q_EXTRA, STONE_Q_STEP = 0.08, 0.20, 0.8, 3.0, 2.0, 0.25
STONE_VIS_MIN, STONE_FALLBACK, STONE_SHIFT = 0.25, "group_3", 12.0                 # share of the stone's sampled vertices left above the terrain
# Chernarus p25-p75 per kind (scratchpad ev112-kit/chern-stones.json): q to the real centreline (m), yaw of model Z to the
# centreline tangent folded to [0, 90] (deg); counts per family from kit/chernarus-bank-dressing.json stones_models
STONE_BANDS = {"group_1": ((0.598, 2.351), (4.33, 52.72)), "group_2": ((0.801, 2.070), (33.45, 76.35)),
               "group_3": ((0.730, 2.524), (10.56, 53.12)), "bar": ((2.417, 3.432), (75.62, 86.10)),
               "bar_curve": ((2.069, 4.137), (51.55, 67.98))}
STONE_COUNTS = {"leaf": {"group_1": 25, "group_2": 31, "group_3": 72, "bar": 15, "bar_curve": 51},
                "moss": {"group_1": 12, "group_2": 22, "group_3": 40, "bar": 29, "bar_curve": 35},
                "sand": {"group_1": 25, "group_2": 22, "group_3": 106, "bar": 24, "bar_curve": 63}}
SILL_UP, SILL_EXPOSED, SILL_CLEAR, KK_CLEAR = 0.06, 0.05, 2.0, 2.5
MOUND_Q, MOUND_T, MOUND_RING, MOUND_FLOOR, MOUND_PASSES = 24.0, 0.30, 0.25, 0.80, 10
SHAPES = (((0, 0),), ((0, 0), (0, 1)), ((0, 0), (1, 0)), ((0, 0), (1, 1)), ((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 1), (1, 0)))
PROJ_RMAX, PIT_Q, END_SLIDE = 40.0, 36.0, 8.0
LOW_FLOOR = 0.80                                                # no lowering below it: terrain < 0.75 off the envelope is engine sea
REACH_Y_MIN = 1.45                                              # reach mode roadway floor (v8: BED_MIN - SEAT0 = 1.33)
# v10 (18-10): junctions
POND_R, JUNC_R_MIN, JUNC_R_MAX, JUNC_CONE = 12.0, 15.0, 30.0, 35.0     # target vertex J of a pond/bridge junction
JUNC_EX, JUNC_WIN, JUNC_SLIDE, JUNC_G, JUNC_L0 = 25.0, (0.3, 4.0), 12.0, 0.04, 26.0
JUNC_KIT_REACH, JUNC_W, JUNC_SLACK, JUNC_AW, JUNC_AW_R = 2.0, 0.05, 0.10, 0.02, 30.0
# v10 mounds: the zone the despike pass leaves to the kit (despike_v31.py free_domain: v31_kit dilated by 2 vertices, 15 m
# around every kit/stones record origin) plus margins; kept dry rims are laid down to their plane + RIM_CLEAR (despike's
# ENV_CLEAR, which keeps every footprint predicate unchanged)
ZONE_DIL, ZONE_REC_R, RIM_CLEAR, ZONE_ROUNDS = 4, 21.0, 0.35, 6



# ---------------------------------------------------------------- v7 helpers (unchanged)
def xz(r, c):
    return np.array([6.0 * c, ZTOP - 6.0 * r])


def geodesic(body, start):
    par = {start: None}; q = deque([start]); last = start
    while q:
        a = q.popleft(); last = a
        for dr, dc in NATIVE:
            b = (a[0] + dr, a[1] + dc)
            if b not in par and body[b]:
                par[b] = a; q.append(b)
    return last, par


def path_between(body, a):
    b, par = geodesic(body, a)
    p = [b]
    while par[p[-1]] is not None:
        p.append(par[p[-1]])
    return p


def smooth(P, win=7, passes=4):
    P = P.copy()
    for _ in range(passes):
        Q = P.copy()
        for i in range(1, len(P) - 1):
            k = min(win // 2, i, len(P) - 1 - i)
            Q[i] = P[i - k:i + k + 1].mean(0)
        P = Q
    return P


def resample(P, step=0.5):
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
    t = np.arange(0, s[-1] + 1e-9, step)
    return np.c_[np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])], t


def tri_h(H, x, z):
    """Planar height of the native triangle (NW-SE diagonal) under world (x, z); vectorised."""
    x = np.asarray(x, float); z = np.asarray(z, float)
    c_, r_ = x / 6.0, (ZTOP - z) / 6.0
    c0 = np.clip(np.floor(c_).astype(int), 0, H.shape[1] - 2); r0 = np.clip(np.floor(r_).astype(int), 0, H.shape[0] - 2)
    fc, fr = c_ - c0, r_ - r0
    nw, ne, sw, se = H[r0, c0], H[r0, c0 + 1], H[r0 + 1, c0], H[r0 + 1, c0 + 1]
    return np.where(fc >= fr, nw + fc * (ne - nw) + fr * (se - ne), nw + fr * (sw - nw) + fc * (se - sw))


def seg_dist(p, a, b):
    ab = b - a; t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + np.outer(t, ab)) if p.ndim > 1 else p - (a + t * ab), axis=-1), t


def fill_pits(h, fillable, drain):
    """Raise every fillable vertex of h to its spill level: priority flood over the native triangle edges from the
    drain vertices (which keep their height). Returns the filled copy."""
    out = h.copy(); done = drain.copy()
    # v9: only drains with a non-drain native neighbour seed the flood (a drain surrounded by drains pushes nothing; the
    # result is identical and the heap no longer holds every drain of a large window)
    edge = np.zeros(h.shape, bool)
    for dr, dc in NATIVE:
        sh = np.zeros(h.shape, bool)
        sh[max(-dr, 0):h.shape[0] - max(dr, 0), max(-dc, 0):h.shape[1] - max(dc, 0)] = ~drain[max(dr, 0):h.shape[0] - max(-dr, 0), max(dc, 0):h.shape[1] - max(-dc, 0)]
        edge |= sh
    heap = [(out[r, c], r, c) for r, c in map(tuple, np.argwhere(drain & edge))]
    heapq.heapify(heap)
    nr, nc = h.shape
    while heap:
        z0, r, c = heapq.heappop(heap)
        for dr, dc in NATIVE:
            a, b = r + dr, c + dc
            if 0 <= a < nr and 0 <= b < nc and not done[a, b]:
                done[a, b] = True
                if fillable[a, b] and out[a, b] < z0:
                    out[a, b] = z0
                heapq.heappush(heap, (out[a, b], a, b))
    return out


def spill_depth(h, drain):
    full = np.ones(h.shape, bool)
    return fill_pits(h, full & ~drain, drain) - h


def tri_slopes(A_):
    nw, ne, sw, se = A_[:-1, :-1], A_[:-1, 1:], A_[1:, :-1], A_[1:, 1:]
    return (np.degrees(np.arctan(np.hypot((ne - nw) / 6.0, (ne - se) / 6.0))),
            np.degrees(np.arctan(np.hypot((se - sw) / 6.0, (nw - sw) / 6.0))))


# ---------------------------------------------------------------- kit geometry
def load_models(path=GEOM_PATH):
    return json.load(open(path))["models"]


def model_key(model):
    return model.replace("/", "\\").split("\\")[-1][:-4].replace("streambed_", "", 1)      # e.g. leaf_long_straight


def kind_of(model):
    return model_key(model).split("_", 1)[1]


def rec_frame(rec):
    m = rec["matrix"]
    return np.array([m[0:3], m[3:6], m[6:9]], float).T, np.array(m[9:12], float)      # columns X, Y, Z; T


def fan(faces):
    out = []
    for f in faces:
        f = np.asarray(f, float)
        for j in range(1, len(f) - 1):
            out.append(f[[0, j, j + 1]])
    return out


class KitSurface:
    """World triangles of the roadway LOD (with a water_ext flag) and of the water proxy LOD0 of a set of records, and the
    highest face over arbitrary xz points (point-in-triangle in plan, planar height inside the face)."""
    CELL = 4.0

    def __init__(self, records, models):
        road, ext, water, rp, wp = [], [], [], [], []
        for i, rec in enumerate(records):
            if rec.get("piece") == "stones":
                continue
            g = models[model_key(rec["model"])]; R, T = rec_frame(rec)
            for f in g["road"]:
                for t in fan([f["v"]]):
                    road.append(t @ R.T + T); ext.append(f["tex"].startswith("water_ext")); rp.append(i)
            for t in fan(g["water"]):
                water.append(t @ R.T + T); wp.append(i)
        self.sets = {"road": self._prep(np.array(road), np.array(rp)), "water": self._prep(np.array(water), np.array(wp))}
        self.sets["road_ext"] = self._prep(np.array(road)[np.array(ext, bool)], np.array(rp)[np.array(ext, bool)])

    def _prep(self, tri, owner):
        A = tri[:, 0, [0, 2]]; B = tri[:, 1, [0, 2]]; C = tri[:, 2, [0, 2]]
        M = np.stack([B - A, C - A], axis=2)                        # 2x2 per triangle
        det = M[:, 0, 0] * M[:, 1, 1] - M[:, 0, 1] * M[:, 1, 0]
        ok = np.abs(det) > 1e-10
        tri, owner, A, M, det = tri[ok], owner[ok], A[ok], M[ok], det[ok]
        inv = np.stack([np.stack([M[:, 1, 1], -M[:, 0, 1]], 1), np.stack([-M[:, 1, 0], M[:, 0, 0]], 1)], 1) / det[:, None, None]
        lo = tri[:, :, [0, 2]].min(1); hi = tri[:, :, [0, 2]].max(1)
        grid = {}
        for k in range(len(tri)):
            for gx in range(int(math.floor(lo[k, 0] / self.CELL)), int(math.floor(hi[k, 0] / self.CELL)) + 1):
                for gz in range(int(math.floor(lo[k, 1] / self.CELL)), int(math.floor(hi[k, 1] / self.CELL)) + 1):
                    grid.setdefault((gx, gz), []).append(k)
        return dict(tri=tri, owner=owner, A=A, inv=inv, grid=grid)

    def max_height(self, P, which="water", owner=False):
        """Highest face of the set over each xz point (-inf where none); with owner=True also the record index."""
        S = self.sets[which]; P = np.asarray(P, float).reshape(-1, 2)
        out = np.full(len(P), -np.inf); who = np.full(len(P), -1)
        if not len(S["tri"]):
            return (out, who) if owner else out
        keys = np.floor(P / self.CELL).astype(np.int64)
        order = np.lexsort((keys[:, 1], keys[:, 0])); ks = keys[order]
        brk = np.r_[0, np.nonzero(np.any(np.diff(ks, axis=0) != 0, axis=1))[0] + 1, len(ks)]
        for a, b in zip(brk[:-1], brk[1:]):
            tl = S["grid"].get((int(ks[a, 0]), int(ks[a, 1])))
            if not tl:
                continue
            idx = order[a:b]; Q = P[idx]
            tl = np.array(tl)
            d = Q[None, :, :] - S["A"][tl][:, None, :]                     # (T, N, 2)
            uv = np.einsum("tij,tnj->tni", S["inv"][tl], d)
            u, v = uv[..., 0], uv[..., 1]
            inside = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
            tri = S["tri"][tl]
            y = tri[:, 0, 1][:, None] + u * (tri[:, 1, 1] - tri[:, 0, 1])[:, None] + v * (tri[:, 2, 1] - tri[:, 0, 1])[:, None]
            y = np.where(inside, y, -np.inf)
            best = y.max(0); arg = y.argmax(0)
            better = best > out[idx]
            out[idx] = np.where(better, best, out[idx]); who[idx] = np.where(better, S["owner"][tl][arg], who[idx])
        return (out, who) if owner else out


def centreline_world(rec, models, step):
    """Rung-midpoint centreline of a record in world xz, resampled every `step` m (both plate ends included)."""
    g = models[model_key(rec["model"])]; R, T = rec_frame(rec)
    C = np.array(g["centre"]) @ R.T + T
    P, _ = resample(C[:, [0, 2]], step)
    return np.vstack([P, C[-1, [0, 2]]])


# ---------------------------------------------------------------- lattice
def vxz(r, c):
    return np.array([6.0 * c, ZTOP - 6.0 * r])


def turn_type(h1, h2):
    d = (h2 - h1 + 540) % 360 - 180
    if d == 0:
        return None, 0
    if abs(d) == 45:
        return "curve", d
    if abs(d) == 90 and {h1, h2} in ({0, 90}, {180, 270}):
        return "elbow", d
    return "bad", d


def lattice_path(P, frozen, end_run=(0.0, 6.0), end_targets=(None, None), receiving_water=None):
    """Dijkstra from the upstream end of the thalweg P to its downstream end over lattice states."""
    tree = cKDTree(P)
    lo, hi = P.min(0) - DMAX - 12, P.max(0) + DMAX + 12
    r0, r1 = int((ZTOP - hi[1]) / 6), int((ZTOP - lo[1]) / 6) + 1
    c0, c1 = int(lo[0] / 6), int(hi[0] / 6) + 1
    R_, C_ = np.mgrid[r0:r1 + 1, c0:c1 + 1]
    D = tree.query(np.c_[6.0 * C_.ravel(), ZTOP - 6.0 * R_.ravel()])[0].reshape(R_.shape)
    ok = (D <= DMAX) & ~frozen[r0:r1 + 1, c0:c1 + 1]

    def inside(r, c):
        return r0 <= r <= r1 and c0 <= c <= c1 and ok[r - r0, c - c0]
    starts = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1) if inside(r, c) and np.linalg.norm(vxz(r, c) - P[0]) <= 6.0+1e-6]
    goals = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1) if inside(r, c) and np.linalg.norm(vxz(r, c) - P[-1]) <= 6.0+1e-6}
    def through_target(r, c, direction, distance, target):
        if target is None:
            return True
        if receiving_water is not None:
            # A lateral connection is legal too. Screen the shortest connector
            # to the real retained surface, not just its representative vertex;
            # G11 later checks the complete built junction on native triangles.
            start=vxz(r,c);target=np.asarray(target)
            close=start+np.clip((target-start)@direction,0,distance)*direction
            length=float(np.linalg.norm(target-close))
            Q=close+np.linspace(0,1,max(2,int(math.ceil(length/.1))+1))[:,None]*(target-close)
            hit=np.flatnonzero(receiving_water(Q))
            return bool(len(hit) and length*hit[0]/(len(Q)-1)<=6.0)
        delta = np.asarray(target)-vxz(r,c)
        along = float(delta@direction)
        return -1e-6 <= along <= distance+1e-6 and np.linalg.norm(delta-along*direction) <= 1e-6
    RCAP = 40.0
    best, par, heap = {}, {}, []
    for (r, c) in starts:
        for d in DN:
            if not through_target(r,c,unit(d),end_run[0],end_targets[0]):
                continue
            st = (r, c, d, 0.0 if end_run[0] else RCAP, "start"); g = np.linalg.norm(vxz(r, c) - P[0]) * 2
            best[st] = g; par[st] = None; heapq.heappush(heap, (g, st))
    end = None
    while heap:
        g, st = heapq.heappop(heap)
        if g > best.get(st, 1e18):
            continue
        r, c, d, run, last = st
        if ((r, c) in goals and run >= end_run[1] and par[st] is not None
                and through_target(r,c,-unit(d),run,end_targets[1])):
            end = st; break
        for d2 in DN:
            tt, _ = turn_type(HEAD[d], HEAD[d2])
            if tt == "bad":
                continue
            add, run2, last2 = 0.0, run, last
            if tt:
                if run < (end_run[0] if last == "start" and end_run[0] else MIN_RUN.get((last, tt), 18.0)):
                    continue
                add, run2, last2 = TURN_COST[tt], 0.0, tt
            dr, dc = DIRS[d2]; rn, cn = r + dr, c + dc
            if not inside(rn, cn):
                continue
            L = 6.0 * math.hypot(dr, dc)
            dm = 0.5 * (D[r - r0, c - c0] + D[rn - r0, cn - c0])
            g2 = g + add + L * (LAMBDA + (dm / SIGMA) ** 2)
            st2 = (rn, cn, d2, min(run2 + L, RCAP), last2)
            if g2 < best.get(st2, 1e18):
                best[st2] = g2; par[st2] = st; heapq.heappush(heap, (g2, st2))
    assert end is not None, "no lattice path"
    seq = []
    st = end
    while st is not None:
        seq.append(st); st = par[st]
    seq = seq[::-1]
    return [(s_[0], s_[1]) for s_ in seq], [s_[2] for s_ in seq[1:]]


def segments(dirs):
    segs, i0 = [], 0
    for i in range(1, len(dirs)):
        if dirs[i] != dirs[i - 1]:
            segs.append((dirs[i - 1], i0, i)); i0 = i
    segs.append((dirs[-1], i0, len(dirs)))
    return segs


def unit(d):
    dr, dc = DIRS[d]; v = np.array([dc, -dr], float)
    return v / np.linalg.norm(v)


def heading_of(v):
    return math.degrees(math.atan2(v[0], v[1]))


def yaw_frame(theta_deg, s, phi=0.0):
    """Rotation-scale matrix (columns X, Y, Z world xyz): model +Z at compass heading theta, pitched up by phi."""
    t = math.radians(theta_deg); u = np.array([math.sin(t), math.cos(t)])
    Z = np.array([u[0] * math.cos(phi), math.sin(phi), u[1] * math.cos(phi)])
    Yax = np.array([-u[0] * math.sin(phi), math.cos(phi), -u[1] * math.sin(phi)])
    X = np.cross(Yax, Z)
    return np.stack([X, Yax, Z], axis=1) * s


class Polyline:
    """Lattice polyline with stations; projections use the first and last segments extended by EXTEND m."""
    def __init__(self, V):
        u0 = (V[1] - V[0]) / np.linalg.norm(V[1] - V[0]); u1 = (V[-1] - V[-2]) / np.linalg.norm(V[-1] - V[-2])
        self.V = V; self.cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(V, axis=0), axis=1))]
        self.X = np.vstack([V[0] - EXTEND * u0, V, V[-1] + EXTEND * u1])
        self.xcum = np.r_[-EXTEND, self.cum, self.cum[-1] + EXTEND]

    def at(self, st):
        st = np.asarray(st, float)
        return np.c_[np.interp(st, self.xcum, self.X[:, 0]), np.interp(st, self.xcum, self.X[:, 1])]

    def project(self, P):
        P = np.asarray(P, float).reshape(-1, 2)
        q = np.full(len(P), np.inf); stq = np.zeros(len(P))
        for i in range(len(self.X) - 1):
            dd, t = seg_dist(P, self.X[i], self.X[i + 1])
            better = dd < q - 1e-9
            q = np.where(better, dd, q); stq = np.where(better, self.xcum[i] + t * (self.xcum[i + 1] - self.xcum[i]), stq)
        return q, stq

    def project_grid(self, r0, r1, c0, c1, rmax):
        """project() of the grid vertices r0..r1 x c0..c1 (shape (r1-r0+1, c1-c0+1)), exact for every vertex within rmax of
        the extended polyline (same segment order and tie rule as project()); farther vertices get q = inf, station 0.
        v9: a 10 km reach has a window of millions of vertices; every q-dependent rule of the tool acts within OUTER,
        MOUND_Q or PIT_Q (< rmax), so the far vertices never matter."""
        nr, nc = r1 - r0 + 1, c1 - c0 + 1
        q = np.full((nr, nc), np.inf); stq = np.zeros((nr, nc))
        for i in range(len(self.X) - 1):
            a, b = self.X[i], self.X[i + 1]
            lo, hi = np.minimum(a, b) - rmax, np.maximum(a, b) + rmax
            ra, rb = max(int(math.floor((ZTOP - hi[1]) / 6.0)), r0), min(int(math.ceil((ZTOP - lo[1]) / 6.0)), r1)
            ca, cb = max(int(math.floor(lo[0] / 6.0)), c0), min(int(math.ceil(hi[0] / 6.0)), c1)
            if ra > rb or ca > cb:
                continue
            RR, CC = np.mgrid[ra:rb + 1, ca:cb + 1]
            dd, t = seg_dist(np.c_[6.0 * CC.ravel(), ZTOP - 6.0 * RR.ravel()], a, b)
            dd = dd.reshape(RR.shape); t = t.reshape(RR.shape)
            qb = q[ra - r0:rb - r0 + 1, ca - c0:cb - c0 + 1]; sb = stq[ra - r0:rb - r0 + 1, ca - c0:cb - c0 + 1]
            better = dd < qb - 1e-9
            q[ra - r0:rb - r0 + 1, ca - c0:cb - c0 + 1] = np.where(better, dd, qb)
            stq[ra - r0:rb - r0 + 1, ca - c0:cb - c0 + 1] = np.where(better, self.xcum[i] + t * (self.xcum[i + 1] - self.xcum[i]), sb)
        far = q > rmax
        q[far] = np.inf; stq[far] = 0.0
        return q, stq


def fill_run(G, ov_lo_lo, ov_lo_hi, end_lo, end_hi, lip_s):
    """Straights for a free length G (m) between the plate ends of the two corner pieces of a run (chain end: no piece).
    ov_lo_lo / ov_lo_hi: the corner piece's own scaled lip (overlap floor = max(OV_FLOOR, lip_corner + lip_straight - DIP_SPAN)).
    Returns (penalty, n_long, n_short, scale, overlap) or None."""
    best = None
    # The old eleven-long-piece cap cannot fill a terminal straight above
    # 305 m even with two short pieces at maximum scale. Bound the search by
    # the requested length and the minimum net length per long piece.
    max_long = max(11, int(math.ceil((G + 2*OV_MAX)/(24*S_MIN-OV_MAX))) + 1)
    for nl in range(max_long + 1):
        if nl == 12 and best is not None:
            break  # preserve the original layout whenever that search fits
        for ns in range(0, 3):
            k = nl + ns
            if k == 0:
                continue
            nj = k - 1 + (0 if end_lo else 1) + (0 if end_hi else 1)
            for s in np.arange(S_MIN, S_MAX + 1e-4, 0.01):
                lip = lip_s * s
                lo = max([OV_FLOOR, 2 * lip - DIP_SPAN] + ([] if end_lo else [ov_lo_lo + lip - DIP_SPAN])
                         + ([] if end_hi else [ov_lo_hi + lip - DIP_SPAN]))
                Ls = 24.0 * nl + 12.0 * ns
                if nj:
                    ov = (Ls * s - G) / nj
                    if not (lo <= ov <= OV_MAX):
                        continue
                else:
                    ov = None
                    if not (0 <= Ls * s - G <= 4.0):
                        continue
                pen = ((s - 1) / 0.05) ** 2 + (((ov if ov is not None else OV_PREF) - max(OV_PREF, lo + 0.3)) / 0.7) ** 2 + 0.5 * k + 0.8 * ns
                if best is None or pen < best[0]:
                    best = (pen, nl, ns, round(float(s), 3), float(ov) if ov is not None else 0.0)
    return best


def site_axis(site, vp, wet, lab):
    """v7 main() 172-199: body, smoothed thalweg (upstream first) and the monotone plane profile W."""
    sr, sc = int(round((ZTOP - site["seed"][1]) / 6)), int(round(site["seed"][0] / 6))
    w = np.argwhere(wet[sr - 3:sr + 4, sc - 3:sc + 4])
    assert len(w), site
    rr, cc = w[np.argmin(np.hypot(w[:, 0] - 3, w[:, 1] - 3))] + (sr - 3, sc - 3)
    body = lab == lab[rr, cc]
    planes = vp[body]
    p0 = path_between(body, (int(rr), int(cc)))[0]
    path = path_between(body, p0)
    if len(path) < 2:
        return None
    if vp[path[0]] < vp[path[-1]]:
        path = path[::-1]
    Praw = np.array([xz(*v) for v in path]); Wraw = np.array([vp[v] for v in path])
    P, s = resample(smooth(Praw))
    sraw = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Praw, axis=0), axis=1))]
    W = np.minimum.accumulate(np.interp(np.linspace(0, sraw[-1], len(s)), sraw, Wraw))
    k = 40
    Wp = np.r_[np.full(k, W[0]), W, np.full(k, W[-1])]
    W = np.minimum.accumulate(np.convolve(Wp, np.ones(2 * k + 1) / (2 * k + 1), mode="valid"))
    return body, planes, P, s, W


def profile_on(PL, P, W, H0, ymin=BED_MIN - SEAT0):
    idx = cKDTree(P).query(PL)[1]
    Wl = np.minimum.accumulate(W[idx])
    k = 40
    Wp = np.r_[np.full(k, Wl[0]), Wl, np.full(k, Wl[-1])]
    Wl = np.minimum.accumulate(np.convolve(Wp, np.ones(2 * k + 1) / (2 * k + 1), mode="valid"))
    nrm = np.gradient(PL, axis=0); nrm = np.c_[-nrm[:, 1], nrm[:, 0]] / np.linalg.norm(nrm, axis=1)[:, None]
    land = np.median(np.stack([tri_h(H0, *(PL + sg * d * nrm).T) for sg in (-1, 1) for d in (5.0, 7.5, 10.0)]), axis=0)
    Y = np.minimum(Wl - 0.25, land - NEED6)
    Yp = np.r_[np.full(k, Y[0]), Y, np.full(k, Y[-1])]
    Y = np.minimum.accumulate(np.convolve(Yp, np.ones(2 * k + 1) / (2 * k + 1), mode="valid"))
    return np.maximum(Y, ymin)


def kit_dims(models, fam):
    """Per kind: plate-end z of the centreline (downstream, upstream) and the scaled-1 lip lengths along model z."""
    out = {}
    for kind in ("long_straight", "short_straight", "long_curve_left", "long_curve_right", "short_slanted", "short_slanted_inv"):
        g = models[f"{fam}_{kind}"]; C = np.array(g["centre"]); fy = g["roadway_flat_y"]
        flat = np.nonzero(np.abs(C[:, 1] - fy) < 0.005)[0]
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C[:, [0, 2]], axis=0), axis=1))]
        if "slanted" in kind:
            lip_dn, lip_up = C[flat[0], 2] - C[0, 2], C[-1, 2] - C[flat[-1], 2]
        else:
            lip_dn, lip_up = s[flat[0]], s[-1] - s[flat[-1]]
        out[kind] = dict(z_dn=float(C[0, 2]), z_up=float(C[-1, 2]), lip_dn=float(lip_dn), lip_up=float(lip_up), flat_y=fy)
    return out


def joint_points(recs, models):
    """v9: for consecutive pieces (by station) the midpoint of their two nearest plate-end centres (the probe's kit_joint)."""
    out = []
    L = sorted([r for r in recs if r.get("piece") != "stones"], key=lambda r: r["station"][0])
    for a, b in zip(L[:-1], L[1:]):
        Ea, Eb = [], []
        for r, E in ((a, Ea), (b, Eb)):
            g = models[model_key(r["model"])]; R, T = rec_frame(r); C = np.array(g["centre"]) @ R.T + T
            E += [C[0, [0, 2]], C[-1, [0, 2]]]
        d = [[np.linalg.norm(x - y) for y in Eb] for x in Ea]
        i, j = np.unravel_index(int(np.argmin(d)), (2, 2))
        out.append(0.5 * (Ea[i] + Eb[j]))
    return np.array(out).reshape(-1, 2)


def axis_samples(recs, PLn, span, models, joints=False):
    """Axis samples: the lattice polyline and every piece centreline, every AXIS_STEP, inside the wet span; with joints=True
    (v9 reach mode) also the probe's kit_joint points and the actual model rungs/lip breaks. A regular resampling can miss a
    local minimum next to a lip break even when its spacing is finer than the consumer's."""
    st = np.arange(span[0], span[1] + 1e-9, AXIS_STEP)
    pts = [PLn.at(np.r_[st, span[1]])]
    if joints:
        pts.append(joint_points(recs, models))
    for rec in recs:
        pts.append(centreline_world(rec, models, AXIS_STEP))
        if joints:
            R, T = rec_frame(rec)
            C = np.array(models[model_key(rec["model"])]["centre"]) @ R.T + T
            pts.append(C[:, [0, 2]])
    P = np.vstack(pts)
    _, stq = PLn.project(P)
    return P[(stq >= span[0] - 1e-6) & (stq <= span[1] + 1e-6)]


def tri_weights(P):
    """Native triangle vertices (r, c) and barycentric weights for world points (v7 lines 333-336)."""
    c_, r_ = P[:, 0] / 6.0, (ZTOP - P[:, 1]) / 6.0
    ci, ri = np.floor(c_).astype(int), np.floor(r_).astype(int); fc, fr = c_ - ci, r_ - ri
    up = fc >= fr
    rr = np.stack([ri, np.where(up, ri, ri + 1), ri + 1], 1)
    cc = np.stack([ci, np.where(up, ci + 1, ci), ci + 1], 1)
    ww = np.stack([np.where(up, 1 - fc, 1 - fr), np.where(up, fc - fr, fr - fc), np.where(up, fr, fc)], 1)
    return rr, cc, ww


def axis_rule(h, r0, c0, fz, ring0, P, top, vfloor=None, axis_w=None):
    """Lower movable vertices until sum(w h) <= top at every sample. Returns moved mask, unresolved count, outside count."""
    rr, cc, ww = tri_weights(P)
    rr = rr - r0; cc = cc - c0
    inside = (rr.min(1) >= 0) & (cc.min(1) >= 0) & (rr.max(1) < h.shape[0]) & (cc.max(1) < h.shape[1])
    moved = np.zeros(h.shape, bool)
    idx = np.nonzero(inside)[0]
    R3, C3, W3, TP = rr[idx], cc[idx], ww[idx], top[idx]
    AW = np.full(len(idx), AXIS_W) if axis_w is None else np.asarray(axis_w, float)[idx]     # v10: lower near a junction

    def excess():
        return (W3 * h[R3, C3]).sum(1) - TP
    for _ in range(AXIS_PASSES):
        e_all = excess()
        bad = np.nonzero(e_all > 1e-4)[0]
        if not len(bad):
            break
        for i in bad:
            e = float((W3[i] * h[R3[i], C3[i]]).sum() - TP[i])
            if e <= 1e-4:
                continue
            cand = [j for j in range(3) if not fz[R3[i, j], C3[i, j]] and W3[i, j] >= AW[i] and h[R3[i, j], C3[i, j]] > TP[i] - AXIS_DROP]
            mv = [j for j in cand if not ring0[R3[i, j], C3[i, j]]] or cand
            sw = sum(W3[i, j] for j in mv)
            for j in (mv if sw > 0 else []):
                v = (R3[i, j], C3[i, j])
                h[v] = max(TP[i] - AXIS_DROP, h[v] - e / sw, min(h[v], LOW_FLOOR), -np.inf if vfloor is None else min(h[v], vfloor[v])); moved[v] = True
    unresolved = int((excess() > 1e-3).sum())
    return moved, unresolved, int((~inside).sum())


# ---------------------------------------------------------------- v9: reach mode, junction sills, mounds, stones
def load_stones(path=STONES_GEOM_PATH):
    return json.load(open(path))["models"]


def v2c(v):
    """Vertex mask -> cells with any corner in it."""
    return v[:-1, :-1] | v[:-1, 1:] | v[1:, :-1] | v[1:, 1:]


def c2v(c):
    """Cell mask -> vertices with any incident cell in it."""
    out = np.zeros((c.shape[0] + 1, c.shape[1] + 1), bool)
    for dr in (0, 1):
        for dc in (0, 1):
            out[dr:dr + c.shape[0], dc:dc + c.shape[1]] |= c
    return out


def c2v_max(val):
    out = np.full((val.shape[0] + 1, val.shape[1] + 1), -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            out[dr:dr + val.shape[0], dc:dc + val.shape[1]] = np.maximum(out[dr:dr + val.shape[0], dc:dc + val.shape[1]], val)
    return out


def reach_axis(site, vp, ext_to=None):
    """Reach mode: thalweg from the given stem (upstream first) plus the straight extensions to an earlier course (v10: or to
    the junction target, ext_to {side: xz}, which replaces the sites file's 'to'); W as v7."""
    S = np.array(site["stem"], int)
    Praw = np.array([xz(*v) for v in S]); Wraw = vp[S[:, 0], S[:, 1]].astype(float)
    ext = {k: np.array(v["to"], float) for k, v in (site.get("extend") or {}).items()}
    ext.update(ext_to or {})
    for side in ("up", "dn"):
        if side not in ext:
            continue
        to = np.asarray(ext[side], float); a = Praw[0] if side == "up" else Praw[-1]
        n = max(1, int(math.ceil(np.linalg.norm(to - a) / 6.0)))
        seg = a + (to - a) * (np.arange(1, n + 1) / n)[:, None]
        if side == "up":
            Praw = np.vstack([seg[::-1], Praw]); Wraw = np.r_[np.full(n, Wraw[0]), Wraw]
        else:
            Praw = np.vstack([Praw, seg]); Wraw = np.r_[Wraw, np.full(n, Wraw[-1])]
    P, s = resample(smooth(Praw))
    sraw = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Praw, axis=0), axis=1))]
    W = np.minimum.accumulate(np.interp(np.linspace(0, sraw[-1], len(s)), sraw, Wraw))
    k = 40
    Wp = np.r_[np.full(k, W[0]), W, np.full(k, W[-1])]
    W = np.minimum.accumulate(np.convolve(Wp, np.ones(2 * k + 1) / (2 * k + 1), mode="valid"))
    return P, s, W


def reach_cut(body, kept, cover, env, planes, H, frozen, V, junctions):
    """Reach mode: remove the cover and envelope cells (plane in the body's range) that lie within CUT_Q of the lattice
    polyline V or touch the body dilated twice (v8's rule, which also takes the dry envelope rings of the channel's banks)
    and touch no kept wet vertex; then find the sills: vertices of kept envelope cells that are also vertices of a removed
    cell and stand below their highest kept plane + SILL_EXPOSED (a new exposed pond edge for bury_edges_v31.py)."""
    br, bc = np.nonzero(body)
    vr = ((ZTOP - V[:, 1]) / 6.0); vc = V[:, 0] / 6.0
    m = int(math.ceil(CUT_Q / 6.0)) + 3
    r0 = max(int(min(br.min(), vr.min())) - m, 0); r1 = min(int(max(br.max(), vr.max())) + m, 2047)
    c0 = max(int(min(bc.min(), vc.min())) - m, 0); c1 = min(int(max(bc.max(), vc.max())) + m, 2047)
    bd = binary_dilation(body[r0:r1 + 1, c0:c1 + 1], np.ones((3, 3), bool), iterations=2)
    bcell, kcell = v2c(bd), v2c(kept[r0:r1 + 1, c0:c1 + 1])
    PLc = Polyline(V) if len(V) > 1 else None
    cq, _ = PLc.project_grid(r0, r1 - 1, c0, c1 - 1, CUT_Q + 6.0)          # cell (r, c) ~ vertex (r, c) + half a cell
    cr, cc_ = np.mgrid[r0:r1, c0:c1]
    Cc = np.c_[6.0 * cc_.ravel() + 3, ZTOP - 6.0 * cr.ravel() - 3]
    near = np.nonzero(np.isfinite(cq.ravel()) & (cq.ravel() <= CUT_Q + 6.0))[0]
    cqx = np.full(Cc.shape[0], np.inf)
    for i in range(len(V) - 1):
        if len(near):
            cqx[near] = np.minimum(cqx[near], seg_dist(Cc[near], V[i], V[i + 1])[0])
    bcell = bcell | (cqx.reshape(cr.shape) <= CUT_Q)
    # the seat corridor: a cell with a vertex within RING1 of the path is removed even when it touches kept water (a kept
    # tributary or pond reaching the channel would otherwise freeze ring vertices under the kit: margins down to -2.4 m in
    # the second rollout); the kept water then ends at a sill just outside the corridor
    corridor = v2c(dist_grid(V, r0, r1, c0, c1, RING1) <= RING1)
    keep_core = np.zeros((r1-r0+1,c1-c0+1),bool)
    rgrid,cgrid = np.mgrid[r0:r1+1,c0:c1+1]
    for ji in junctions.values():
        if "J" not in ji or ji["type"]=="kit": continue
        xj,zj=ji["J"]
        keep_core |= (np.hypot(6*cgrid-xj,ZTOP-6*rgrid-zj)<=12) & kept[r0:r1+1,c0:c1+1]
    core_cells=v2c(keep_core)
    # Never remove original water cells incident to a frozen vertex. A newly
    # exposed frozen edge cannot be repaired by the downstream bury pass.
    core_cells |= v2c(frozen[r0:r1+1,c0:c1+1])
    lo, hi = float(planes.min()) - 0.05, float(planes.max()) + 0.05
    counts, cut_any = {}, np.zeros(bcell.shape, bool)
    backup = (cover[r0:r1, c0:c1].copy(), env[r0:r1, c0:c1].copy())
    for name, arr in (("cover", cover), ("envelope", env)):
        blk = arr[r0:r1, c0:c1]
        cut = bcell & (~kcell | corridor) & ~core_cells & np.isfinite(blk) & (blk >= lo) & (blk <= hi)
        counts[name] = int(cut.sum()); cut_any |= cut
        arr[r0:r1, c0:c1] = np.where(cut, np.nan, blk)
    h = H[r0:r1 + 1, c0:c1 + 1]
    fz = frozen[r0:r1 + 1, c0:c1 + 1]
    fz_near = fz.copy()
    for dr, dc in NATIVE:
        fz_near |= shifted(fz, dr, dc, False)
    restored = 0
    for _ in range(8):
        # a frozen vertex cannot be raised into a sill (bury_edges_v31 would then restore its neighbours): the cut cells
        # around it are given back, so the kept water ends one cell further out (the first rollout left 2 such edges)
        eb = env[r0:r1, c0:c1]; rem = np.isfinite(eb)
        vP = c2v_max(np.where(rem, eb, -np.inf))
        sill = c2v(rem) & c2v(cut_any) & (h < vP + SILL_EXPOSED)
        bad = sill & fz_near                                       # frozen, or next to a frozen vertex (a road embankment)
        if not bad.any():
            break
        back = cut_any & v2c(bad)
        cover[r0:r1, c0:c1] = np.where(back, backup[0], cover[r0:r1, c0:c1])
        env[r0:r1, c0:c1] = np.where(back, backup[1], env[r0:r1, c0:c1])
        cut_any &= ~back; restored += int(back.sum())
    eb = env[r0:r1, c0:c1]; rem = np.isfinite(eb)
    vP = c2v_max(np.where(rem, eb, -np.inf))
    sill = c2v(rem) & c2v(cut_any) & (h < vP + SILL_EXPOSED)
    counts["restored_for_frozen_sills"] = restored
    counts["kept_cells_in_corridor"] = int((corridor & kcell & np.isfinite(backup[1])).sum())
    return dict(win=(r0, r1, c0, c1), counts=counts, cut_cells=int(cut_any.sum()), cut_any=cut_any, backup=backup,
                sill=sill & ~fz, target=vP + SILL_UP, sill_frozen=int((sill & fz).sum()), kept_cells_touching_body=int((bcell & kcell).sum()))


def vertex_height_bounds(H, reference, r, c, limit=35.0):
    """Allowed height interval satisfying all six incident native triangles."""
    ring=((0,1),(1,1),(1,0),(0,-1),(-1,-1),(-1,0))
    lower,upper=-math.inf,math.inf
    if r<1 or c<1 or r>=H.shape[0]-1 or c>=H.shape[1]-1:
        return float(H[r,c]),float(H[r,c])
    for (dr1,dc1),(dr2,dc2) in zip(ring,ring[1:]+ring[:1]):
        matrix=np.array([[6.*dc1,6.*dr1],[6.*dc2,6.*dr2]])
        coefficient=np.linalg.solve(matrix,np.ones(2))
        constant=np.linalg.solve(matrix,np.array([H[r+dr1,c+dc1],H[r+dr2,c+dc2]]))
        original=np.linalg.solve(matrix,np.array([reference[r+dr1,c+dc1]-reference[r,c],reference[r+dr2,c+dc2]-reference[r,c]]))
        cap=max(math.tan(math.radians(limit)),float(np.linalg.norm(original)))
        aa=float(coefficient@coefficient); bb=float(coefficient@constant)
        discriminant=bb*bb-aa*(float(constant@constant)-cap*cap)
        if discriminant < -1e-9:return math.inf,-math.inf
        delta=math.sqrt(max(0,discriminant))
        lower=max(lower,(bb-delta)/aa); upper=min(upper,(bb+delta)/aa)
    return lower,upper




def junction_target(v_end, kept, vp, H0, nearest=False):
    """v10: the kept wet vertex J a pond/bridge junction runs to. k1 = the kept wet vertex nearest to the stem end (must be
    within POND_R); J = among the kept wet vertices JUNC_R_MIN-JUNC_R_MAX m from the stem end, at least 0.05 m deep and within
    JUNC_CONE deg of the direction to k1, the best aligned (then the nearest to JUNC_R_MIN m); else the farthest kept wet
    vertex inside that cone. Returns (xz, None) or (None, reason)."""
    r0, c0 = int(v_end[0]), int(v_end[1]); m = int(JUNC_R_MAX / 6.0) + 1
    ra, rb, ca, cb = max(r0 - m, 0), min(r0 + m, 2047), max(c0 - m, 0), min(c0 + m, 2047)
    w = np.argwhere(kept[ra:rb + 1, ca:cb + 1]) + (ra, ca)
    if not len(w):
        return None, "no kept wet vertex within %.0f m" % JUNC_R_MAX
    p0 = xz(r0, c0); Pw = np.c_[6.0 * w[:, 1], ZTOP - 6.0 * w[:, 0]]; d = np.hypot(Pw[:, 0] - p0[0], Pw[:, 1] - p0[1])
    k1 = int(np.argmin(d))
    if d[k1] > POND_R:
        return None, "nearest kept wet vertex %.1f m from the stem end" % d[k1]
    if nearest:
        return Pw[k1], None
    u = (Pw[k1] - p0) / d[k1]
    cos = ((Pw - p0) @ u) / np.maximum(d, 1e-9)
    depth = vp[w[:, 0], w[:, 1]] - H0[w[:, 0], w[:, 1]]
    cone = cos >= math.cos(math.radians(JUNC_CONE)) - 1e-9
    ok = cone & (d >= JUNC_R_MIN) & (d <= JUNC_R_MAX) & (depth >= 0.05)
    if ok.any():
        i = np.nonzero(ok)[0]
        j = i[np.lexsort((np.abs(d[i] - JUNC_R_MIN), -np.round(cos[i], 3)))][0]
    else:
        i = np.nonzero(cone)[0]
        j = i[np.argmax(d[i])]
    return Pw[j], None


def junction_B(side, PLn, s_stem, prot_v):
    """v10: station of the first lattice vertex beyond the stem end (outwards) that is a vertex of an envelope cell left after
    the cut (the sill line of a pond/bridge junction), or None."""
    cum, V = PLn.cum, PLn.V
    if side == "dn":
        idx = [i for i in range(len(V)) if cum[i] >= s_stem[1] - 1e-6]
    else:
        idx = [i for i in range(len(V) - 1, -1, -1) if cum[i] <= s_stem[0] + 1e-6]
    for i in idx:
        r, c = int(round((ZTOP - V[i][1]) / 6.0)), int(round(V[i][0] / 6.0))
        if prot_v[r, c]:
            return float(cum[i])
    return None


def run_layout(sol, G, a, ends, d_lo, d_hi, cum_i0, dims):
    """Straights of a filled run: list of (kind, st0, st1, flat, pos) (v9 placement; v10 free-end slides d_lo / d_hi)."""
    _, nl, ns, sc, ov = sol
    kinds = ["long_straight"] * nl + ["short_straight"] * ns
    if ns and nl:
        kinds = ["long_straight"] * (nl // 2) + ["short_straight"] * ns + ["long_straight"] * (nl - nl // 2)
    Gf = G + d_lo + d_hi
    Ltot = sum(24.0 if k_ == "long_straight" else 12.0 for k_ in kinds) * sc - ov * (len(kinds) - 1)
    pos = -ov if not ends[0] else (-d_lo if not ends[1] else -d_lo - 0.5 * max(Ltot - Gf, 0.0))
    out = []
    for k_ in kinds:
        Lk = (24.0 if k_ == "long_straight" else 12.0) * sc
        st0 = cum_i0 + a + pos; st1 = st0 + Lk
        lp = dims["long_straight" if "long" in k_ else "short_straight"]["lip_up"] * sc
        out.append((k_, st0, st1, (st0 + lp, st1 - lp), pos))
        pos += Lk - ov
    return out


def stone_frame(heading_deg):
    t = math.radians(heading_deg)
    X = np.array([math.cos(t), 0.0, -math.sin(t)]); Y = np.array([0.0, 1.0, 0.0]); Z = np.array([math.sin(t), 0.0, math.cos(t)])
    return np.stack([X, Y, Z], axis=1)


def stone_try(c, t, nrm, side, kind, q0, yrel, fam, Hc, ks, sgeo, tree, TK, frozen_tri, pond_wet):
    """First acceptable position of one stone of `kind` near the centreline point c (tangent t, left normal nrm): from q0
    outwards in STONE_Q_STEP up to the band's p75 + STONE_Q_EXTRA on `side`, then on the other bank. A position is screened on
    the stored sample of the visual LOD and (v10) accepted only when every test holds on ALL its vertices too. Returns
    (pos, ty, q, side, blocking share, M, visible share) or None."""
    g = sgeo[f"{fam}_{kind}"]; base = np.array(g["base"]); samp = np.array(g["sample"]); allv = np.array(g["all"])
    qb = STONE_BANDS[kind][0][1]
    M = stone_frame(math.degrees(math.atan2(t[0], t[1])) + yrel)

    def tests(V_, pos, ty, Bw):
        Sw = V_ @ M.T + np.array([pos[0], ty, pos[1]])
        gs = tri_h(Hc, Sw[:, 0], Sw[:, 2]); wy = ks.max_height(Sw[:, [0, 2]], "water")
        over = wy > gs; above = over & (Sw[:, 1] > wy)
        dq = tree.query(Sw[:, [0, 2]])[0]
        allxz = np.vstack([Sw[:, [0, 2]], Bw[:, [0, 2]]])
        vis = float((Sw[:, 1] > gs).mean())
        ok = (above.mean() <= STONE_BLOCK and not (above & (dq < STONE_RIBBON)).any() and not frozen_tri(allxz).any()
              and not pond_wet(allxz).any() and vis >= STONE_VIS_MIN)
        return ok, float(above.mean()), vis
    for sd in (side, -side):
        q = q0
        while q <= qb + STONE_Q_EXTRA + 1e-9:
            pos = c + sd * q * nrm
            if np.min(np.hypot(TK[:, 0] - pos[0], TK[:, 1] - pos[1])) >= STONE_GAP:
                Bw = base @ M.T + np.array([pos[0], 0.0, pos[1]])
                gb = tri_h(Hc, Bw[:, 0], Bw[:, 2])
                ty = -float(np.max(Bw[:, 1] - gb)) - STONE_SINK
                if tests(samp, pos, ty, Bw)[0]:
                    ok, blk, vis = tests(allv, pos, ty, Bw)
                    if ok:
                        return pos, ty, q, sd, blk, M, vis
            q += STONE_Q_STEP
    return None


def place_stones(site_id, fam, recs, PLn, span, corner_xz, Hc, ks, sgeo, rng, frozen_tri, pond_wet, taken, models, ribbon_tree):
    """v9 stones of one site on the final terrain Hc. Returns (records, log)."""
    C, Tg = [], []
    for r in recs:
        P_ = centreline_world(r, models, 0.25)
        d = np.gradient(P_, axis=0); d /= np.linalg.norm(d, axis=1)[:, None] + 1e-12
        C.append(P_); Tg.append(d)
    C = np.vstack(C); Tg = np.vstack(Tg); tree = cKDTree(C)
    L = float(span[1] - span[0]); n = int(round(L * STONES_PER_KM / 1000.0))
    kinds = list(STONE_COUNTS[fam]); w = np.array([STONE_COUNTS[fam][k] for k in kinds], float); w /= w.sum()
    out, log = [], dict(target=n, placed=0, dropped=0, moved_out=0, other_bank=0, fallback=0, station_moved=0)
    for k in range(n):
        st = span[0] + (k + 0.5 + rng.uniform(-0.3, 0.3)) * L / max(n, 1)
        kind = kinds[int(rng.choice(len(kinds), p=w))]
        (qa, qb), (ya, yb) = STONE_BANDS[kind]
        q0 = float(rng.uniform(qa, qb)); yrel = float(rng.uniform(ya, yb)) * (1 if rng.random() < 0.5 else -1)
        side0 = 1 if rng.random() < 0.5 else -1
        q0_fb = float(rng.uniform(*STONE_BANDS[STONE_FALLBACK][0]))
        TK = np.array(taken) if taken else np.full((1, 2), 1e9)
        done = None
        for n_st, st_try in enumerate((st, st + STONE_SHIFT, st - STONE_SHIFT, st + 2 * STONE_SHIFT)):
            if not (span[0] <= st_try <= span[1]):
                continue
            p = PLn.at([st_try])[0]; _, i = tree.query(p); c, t = C[i], Tg[i]; nrm = np.array([-t[1], t[0]])
            side = side0
            if len(corner_xz):
                dc = np.hypot(corner_xz[:, 0] - c[0], corner_xz[:, 1] - c[1]); j = int(np.argmin(dc))
                if dc[j] <= 12.0:
                    side = 1 if (corner_xz[j] - c) @ nrm > 0 else -1          # towards the PI (corner vertex): the outer bank
            for kind_try, q_start in [(kind, q0)] + ([(STONE_FALLBACK, q0_fb)] if kind != STONE_FALLBACK else []):
                res = stone_try(c, t, nrm, side, kind_try, q_start, yrel, fam, Hc, ks, sgeo, ribbon_tree, TK, frozen_tri, pond_wet)
                if res is not None:
                    done = res + (kind_try, q_start)
                    log["fallback"] += int(kind_try != kind); log["station_moved"] += int(n_st > 0)
                    break
            if done:
                break
        if done is None:
            log["dropped"] += 1
            continue
        pos, ty, q, sd, blk, M, vis, kind_used, q_start = done
        log["placed"] += 1; log["moved_out"] += int(q > q_start + 1e-9); log["other_bank"] += int(sd != side)
        taken.append(pos)
        out.append(dict(site=site_id, piece="stones", model=f"dz\\water\\streambed\\misc\\stones_{fam}_{kind_used}.p3d",
                        matrix=[*M[:, 0].tolist(), *M[:, 1].tolist(), *M[:, 2].tolist(), float(pos[0]), ty, float(pos[1])],
                        kind=kind_used, q=round(float(tree.query(pos)[0]), 3), yaw_rel_deg=round(abs(yrel), 2), side=sd,
                        sink=round(ty - float(tri_h(Hc, pos[0], pos[1])), 3), blocking_share=round(blk, 3),
                        visible_share=round(vis, 3)))
    return out, log


def shifted(A, dr, dc, fill):
    """B[r, c] = A[r + dr, c + dc] (fill outside)."""
    B = np.full(A.shape, fill, A.dtype)
    n0, n1 = A.shape
    B[max(-dr, 0):n0 - max(dr, 0), max(-dc, 0):n1 - max(dc, 0)] = A[max(dr, 0):n0 - max(-dr, 0), max(dc, 0):n1 - max(-dc, 0)]
    return B


def small_shapes(H, T):
    """Per shape of SHAPES: (anchor mask, ring max) where the shape anchored at a vertex stands > T above its native ring."""
    out = []
    for S in SHAPES:
        ring = sorted({(a + dr, b + dc) for a, b in S for dr, dc in NATIVE} - set(S))
        rmax = np.full(H.shape, -np.inf)
        for dr, dc in ring:
            rmax = np.maximum(rmax, shifted(H, dr, dc, np.inf))           # off-map ring vertex: never a shape there
        smin = np.full(H.shape, np.inf)
        for dr, dc in S:
            smin = np.minimum(smin, shifted(H, dr, dc, -np.inf))
        out.append((S, smin - rmax > T, rmax))
    return out


def bury_strays(H, recs, models, ks, movable_v, floor_v, px=0.25):
    """v9: wet patches of a site's sheet cut off from its channel (the slivers of 1-2.5 m2 in the inner corners of a NE
    elbow staircase, 41.0-0 in a dev run of 17-10): in windows of three consecutive pieces, a wet region (sheet above the
    terrain) that holds no centreline sample of the middle piece and does not reach the window border is buried by raising
    the movable vertices of the native triangles under it to the sheet + BURY. Returns (vertices raised, pixels left)."""
    L = sorted([r for r in recs if r.get("piece") != "stones"], key=lambda r: r["station"][0])
    ext = []
    for r in L:
        g = models[model_key(r["model"])]; R, T = rec_frame(r)
        W = np.vstack([np.array(f, float) for f in g["water"]]) @ R.T + T
        ext.append((W[:, [0, 2]].min(0), W[:, [0, 2]].max(0)))
    raised, left = 0, 0
    for i in range(len(L)):
        a, b = max(i - 1, 0), min(i + 2, len(L))
        lo = np.min([e[0] for e in ext[a:b]], 0) - 1.0; hi = np.max([e[1] for e in ext[a:b]], 0) + 1.0
        nx, nz = int(math.ceil((hi[0] - lo[0]) / px)), int(math.ceil((hi[1] - lo[1]) / px))
        X, Z = np.meshgrid(lo[0] + (np.arange(nx) + 0.5) * px, lo[1] + (np.arange(nz) + 0.5) * px)
        Q = np.c_[X.ravel(), Z.ravel()]
        wy = ks.max_height(Q, "water"); ty = tri_h(H, Q[:, 0], Q[:, 1])
        wet = (wy > ty).reshape(X.shape)
        lab, n = label(wet)
        if n < 2:
            continue
        C = centreline_world(L[i], models, 0.5)
        ci = np.clip(((C[:, 0] - lo[0]) / px).astype(int), 0, nx - 1); cj = np.clip(((C[:, 1] - lo[1]) / px).astype(int), 0, nz - 1)
        keep = set(lab[cj, ci].tolist()) | set(lab[0, :].tolist()) | set(lab[-1, :].tolist()) | set(lab[:, 0].tolist()) | set(lab[:, -1].tolist())
        stray = np.isin(lab, [k for k in range(1, n + 1) if k not in keep])
        if not stray.any():
            continue
        sq = np.nonzero(stray.ravel())[0]
        rr, cc, _ = tri_weights(Q[sq])
        tgt = wy[sq] + BURY
        for k in range(3):
            v_r, v_c = np.clip(rr[:, k], 0, 2047), np.clip(cc[:, k], 0, 2047)
            ok = movable_v[v_r, v_c]
            for r_, c_, t_ in zip(v_r[ok], v_c[ok], tgt[ok]):
                if H[r_, c_] < t_:
                    H[r_, c_] = t_; floor_v[r_, c_] = max(floor_v[r_, c_], t_); raised += 1
        anyok = movable_v[np.clip(rr, 0, 2047), np.clip(cc, 0, 2047)].any(1)
        left += int((~anyok).sum())
    return raised, left


def grade_junction_banks(H, H0, checks, models, frozen, pond_planes, banks, env):
    """Close broad mouths using only already modified dry terrain.

    Burial outside HW+0.3 m is an objective, never a permission to violate a
    roadway, native face, frozen/wet vertex or 1/2/3-vertex mound constraint.
    One bounded solve per receiving-water end; residuals remain explicit and
    independent width/continuity/probe gates decide acceptance.
    """
    from scipy.optimize import linprog
    result_log = []
    by_site = {ck['site']:ck for ck in checks}
    surfaces = {sid:KitSurface(ck['recs'],models) for sid,ck in by_site.items()}
    linked = {sid:set() for sid in by_site}
    axes = {}
    controls = []
    for sid,ck in by_site.items():
        axes[sid] = []
        for ji in ck['junctions'].values():
            other = ji.get('partner')
            if ji.get('type')=='kit' and other in by_site:
                linked[sid].add(other);linked[other].add(sid)
        for rec in ck['recs']:
            g=models[model_key(rec['model'])];R,T=rec_frame(rec)
            C=np.array(g['centre']);W=C@R.T+T
            axes[sid].extend(zip(W[:-1,[0,2]],W[1:,[0,2]]))
            flat=np.flatnonzero(np.abs(C[:,1]-g['roadway_flat_y'])<.005)
            F=C[flat[0]:flat[-1]+1]
            arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(F[:,[0,2]],axis=0),axis=1))]
            half=arc[-1]/2;i=min(np.searchsorted(arc,half,side='right')-1,len(F)-2)
            pm=F[i]+(half-arc[i])/max(arc[i+1]-arc[i],1e-9)*(F[i+1]-F[i])
            p=(R@pm+T)[[0,2]];d=(R@(F[i+1]-F[i]))[[0,2]];d/=np.linalg.norm(d)
            normal=np.array([-d[1],d[0]])
            controls.extend((sid,p+sgn*6*normal) for sgn in (-1,1))
    # Ordinary six-metre laterals are hard dry constraints. A raster objective
    # alone can miss a control just outside the continuous confluence boundary.
    # Only a declared linked branch's actual wet 1.8 m core is exempt.
    dry_points=[];dry_heights=[]
    all_surface=KitSurface([r for ck in checks for r in ck['recs']],models)
    cq=np.array([q for _,q in controls]);cw=all_surface.max_height(cq,'water');ch=tri_h(H,cq[:,0],cq[:,1])
    for (sid,q),water,ground in zip(controls,cw,ch):
        if water<=ground:continue
        confluent=False
        for other in linked[sid]:
            distance=min(float(seg_dist(q.reshape(1,2),a,b)[0][0]) for a,b in axes[other])
            if distance<=HW and surfaces[other].max_height(q.reshape(1,2),'water')[0]>ground:
                confluent=True;break
        if not confluent:
            dry_points.append(q);dry_heights.append(water+.01)
    dry_points=np.array(dry_points).reshape(-1,2);dry_heights=np.array(dry_heights)
    connectors = []
    for ck in checks:
        surface = KitSurface(ck['recs'],models)
        for side,ji in ck['junctions'].items():
            if 'J' not in ji or 'B_xz' not in ji:continue
            start = ck['PLn'].at([ck['span'][0 if side=='up' else 1]])[0]
            target = np.asarray(ji['J'],float)
            Q = start + np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(target-start)/.1))+1))[:,None]*(target-start)
            water = surface.max_height(Q,'water')
            if ji.get('partner') in by_site:
                water=np.maximum(water,KitSurface(by_site[ji['partner']]['recs'],models).max_height(Q,'water'))
            r=np.clip(((ZTOP-Q[:,1])/6).astype(int),0,2046);c=np.clip((Q[:,0]/6).astype(int),0,2046)
            water=np.maximum(water,np.where(np.isfinite(env[r,c]),env[r,c],-np.inf))
            ground=tri_h(H,Q[:,0],Q[:,1]);wet=water>ground
            connectors.append((Q[wet],np.maximum(ground[wet],water[wet]-.01)))
    for ck in checks:
        if ck['mode'] != 'reach':
            continue
        surface = KitSurface(ck['recs'], models)
        for side, ji in ck['junctions'].items():
            if 'B_xz' not in ji:
                continue
            x, z = ji['B_xz']; rc, cc0 = int((ZTOP-z)//6), int(x//6)
            radius = JUNC_L0+12
            halo = int(math.ceil(radius/6))+1
            verts = [(r,c) for r in range(max(2,rc-halo),min(2046,rc+halo+2))
                     for c in range(max(2,cc0-halo),min(2046,cc0+halo+2))
                     if not frozen[r,c] and H[r,c] >= pond_planes[r,c]+.05 and abs(H[r,c]-H0[r,c]) > 1e-6]
            n = len(verts); index = {v:i for i,v in enumerate(verts)}; rows=[]; limits=[]
            entry = dict(site=ck['site'],side=side,variables=n,solved=False)
            if not n:
                entry['reason']='no modified dry vertices';result_log.append(entry);continue
            def add(coeff, limit):
                row=np.zeros(n); rhs=float(limit)
                for v,w in coeff.items():
                    if v in index:row[index[v]]+=w
                    else:rhs-=w*H[v]
                if np.any(row) or rhs < -1e-8:
                    rows.append(row);limits.append(rhs)
            def point_bounds(points, bounds, sign):
                rr,cc,ww=tri_weights(points)
                for ar,ac,aw,bound in zip(rr,cc,ww,bounds):
                    add({(int(r),int(c)):sign*float(w) for r,c,w in zip(ar,ac,aw)},sign*bound)
            X,Z=np.meshgrid(np.arange(x-radius,x+radius,.25),np.arange(z-radius,z+radius,.25));Q=np.c_[X.ravel(),Z.ravel()]
            water=surface.max_height(Q,'water')
            if ji.get('partner') in by_site:
                water=np.maximum(water,KitSurface(by_site[ji['partner']]['recs'],models).max_height(Q,'water'))
            ground=tri_h(H,Q[:,0],Q[:,1]);distance,station=ck['PLn'].project(Q)
            target=(water>ground)&(distance>HW+.3)&(station>=ck['span'][0])&(station<=ck['span'][1])
            if ji.get('partner') in by_site:
                # The approved confluence core is 1.8 m from the actual
                # continuous branch axis, not the lattice or an enlarged band.
                partner_distance=np.full(len(Q),np.inf)
                qlo,qhi=Q.min(0)-HW,Q.max(0)+HW
                for record in by_site[ji['partner']]['recs']:
                    R,T=rec_frame(record)
                    C=(np.array(models[model_key(record['model'])]['centre'])@R.T+T)[:,[0,2]]
                    if np.any(C.max(0)<qlo) or np.any(C.min(0)>qhi):continue
                    for a,b in zip(C[:-1],C[1:]):
                        partner_distance=np.minimum(partner_distance,seg_dist(Q,a,b)[0])
                target &= partner_distance > HW
            entry['burial_points']=int(target.sum())
            point_bounds(Q[target],water[target]+.01,-1)
            burial_rows=len(rows)
            if not burial_rows:
                entry.update(solved=True,vertices_changed=0,burial_residual_max_m=0.0);result_log.append(entry);continue
            lo=np.array([6*(cc0-halo-1),ZTOP-6*(rc+halo+2)]);hi=np.array([6*(cc0+halo+2),ZTOP-6*(rc-halo-1)])
            near=np.all(dry_points>=lo,axis=1)&np.all(dry_points<=hi,axis=1)
            point_bounds(dry_points[near],dry_heights[near],-1)
            entry['ordinary_lateral_constraints']=int(near.sum())
            for points,bounds in connectors:
                near=np.all(points>=lo,axis=1)&np.all(points<=hi,axis=1)
                point_bounds(points[near],bounds[near],1)
            for other in checks:
                A=other['axis_points'];near=np.all(A>=lo,axis=1)&np.all(A<=hi,axis=1)&np.isfinite(other['axis_road'])
                P=A[near];road=other['axis_road'][near]
                point_bounds(P,np.maximum(road-(AXIS_MIN+.01),tri_h(H,P[:,0],P[:,1])),1)
            faces=set()
            for r,c in verts:
                for dr,dc in ((-1,-1),(-1,0),(0,-1),(0,0)):
                    a,b=r+dr,c+dc
                    for face in (((a,b),(a,b+1),(a+1,b+1)),((a,b),(a+1,b),(a+1,b+1))):
                        if (r,c) in face:faces.add(face)
            for face in sorted(faces):
                xy=np.array([[6*(v[1]-face[0][1]),6*(v[0]-face[0][0])] for v in face[1:]],float)
                inv=np.linalg.inv(xy);grad=inv@np.array([H0[v]-H0[face[0]] for v in face[1:]])
                cap=max(math.tan(math.radians(35)),float(np.linalg.norm(grad)))
                for angle in np.arange(32)*2*math.pi/32:
                    a=np.array([math.cos(angle),math.sin(angle)])@inv
                    add({face[0]:-a.sum(),face[1]:a[0],face[2]:a[1]},cap*math.cos(math.pi/32))
            # A fixed minimum member below a fixed maximum ring neighbour is a
            # sufficient bound for each native shape. Anchors are chosen from
            # the current terrain, then included as variables when movable.
            # This permits a broad bank but prevents a new isolated peak.
            for shape in SHAPES:
                anchors=sorted({(r-dr,c-dc) for r,c in verts for dr,dc in shape})
                for r,c in anchors:
                    members=[(r+dr,c+dc) for dr,dc in shape]
                    ring=sorted({(a+dr,b+dc) for a,b in members for dr,dc in NATIVE}-set(members))
                    low=min(members,key=lambda v:(H[v],v));high=max(ring,key=lambda v:(H[v],v))
                    if low in index:add({low:1,high:-1},max(.499,float(H[low]-H[high])))
            matrix=np.pad(np.array(rows),((0,0),(0,burial_rows)))
            matrix[np.arange(burial_rows),n+np.arange(burial_rows)]=-1
            opt=linprog(np.r_[np.full(n,.001),np.ones(burial_rows)],A_ub=matrix,b_ub=np.array(limits),
                        bounds=[(float(H[v]),float(H[v]+4)) for v in verts]+[(0,None)]*burial_rows,method='highs')
            if not opt.success:
                entry['reason']='native constraints infeasible';result_log.append(entry);continue
            old=np.array([H[v] for v in verts]);changes=opt.x[:n]-old
            for v,h,delta in zip(verts,opt.x[:n],changes):
                H[v]=h
                if delta>1e-6:banks[v]=True
            entry.update(solved=True,vertices_changed=int((changes>1e-6).sum()),max_raise_m=round(float(changes.max()),5),
                         burial_residual_max_m=round(float(opt.x[n:].max()),5))
            result_log.append(entry)
    return result_log


def close_bank_caps(H, H0, checks, models, banks, frozen, pond_planes):
    """Bury detached water over an already dry junction bank, with native constraints.

    Raising a vertex merely to the water height is insufficient when the other
    two corners of its triangle belong to a lower, retained pond. Solve the
    barycentric burial inequalities instead. Only existing dry bank vertices
    may rise; all channel samples, slopes and native 1/2/3-vertex shapes remain
    constrained. One bounded pass over connected bank groups; no retry loop.
    """
    from scipy.optimize import linprog
    eligible = banks & ~frozen & (H >= pond_planes + SILL_UP - 1e-6)
    remaining = set(map(tuple, np.argwhere(eligible)))
    groups = []
    while remaining:
        seed = min(remaining); remaining.remove(seed); group = [seed]; stack = [seed]
        while stack:
            r, c = stack.pop()
            for dr, dc in NATIVE:
                v = (r + dr, c + dc)
                if v in remaining:
                    remaining.remove(v); group.append(v); stack.append(v)
        groups.append(group)
    log = []
    for group in groups:
        vv = np.array(group); r0, c0 = np.maximum(vv.min(0)-2, 1); r1, c1 = np.minimum(vv.max(0)+2, 2046)
        lo = np.array([6*c0, ZTOP-6*r1]); hi = np.array([6*c1, ZTOP-6*r0])
        local = (slice(r0,r1+1),slice(c0,c1+1))
        movable = (~frozen[local] & (H[local]>=pond_planes[local]+SILL_UP-1e-6)
                   & ((np.abs(H[local]-H0[local])>1e-6) | banks[local]))
        candidates = np.argwhere(movable) + (r0,c0)
        for ck in checks:
            if ck['mode'] != 'reach':
                continue
            A = ck['axis_points']; local = np.all(A >= lo, axis=1) & np.all(A <= hi, axis=1)
            if not local.any():
                continue
            px = .1
            X, Z = np.meshgrid(np.arange(lo[0]+px/2,hi[0],px),np.arange(lo[1]+px/2,hi[1],px))
            Q = np.c_[X.ravel(),Z.ravel()]; ks = KitSurface(ck['recs'],models)
            wy = ks.max_height(Q,'water'); wet = (wy > tri_h(H,Q[:,0],Q[:,1])).reshape(X.shape)
            labels, count = label(wet)
            if count < 2:
                continue
            ia = np.clip(((A[local,0]-lo[0])/px).astype(int),0,X.shape[1]-1)
            ja = np.clip(((A[local,1]-lo[1])/px).astype(int),0,X.shape[0]-1)
            keep = set(labels[ja,ia]) | set(labels[0,:]) | set(labels[-1,:]) | set(labels[:,0]) | set(labels[:,-1])
            for region in sorted(set(range(1,count+1))-keep):
                ix = np.flatnonzero(labels.ravel()==region); points = Q[ix]
                # Use bank vertices incident to this region only. No shore,
                # retained wet vertex or previously untouched terrain can move.
                rr, cc, ww = tri_weights(points)
                incident = set(zip(rr.ravel(),cc.ravel()))
                support = incident | {(r+dr,c+dc) for r,c in incident for dr,dc in NATIVE}
                verts = sorted(v for v in map(tuple,candidates) if v in support)
                entry = dict(site=ck['site'],area_m2=round(len(ix)*px*px,3),solved=False)
                if not verts:
                    entry['reason']='no dry bank vertex';log.append(entry);continue
                index = {v:i for i,v in enumerate(verts)}; n = len(verts); rows=[]; limits=[]
                def add(coeff,limit):
                    row=np.zeros(n); rhs=float(limit)
                    for v,w in coeff.items():
                        if v in index: row[index[v]] += w
                        else: rhs -= w*H[v]
                    rows.append(row); limits.append(rhs)
                for rows_,cols_,weights_,water in zip(rr,cc,ww,wy[ix]):
                    add({(int(r),int(c)):-float(w) for r,c,w in zip(rows_,cols_,weights_)},-water-.01)
                for other in checks:
                    A=other['axis_points']; near=np.all(A>=lo-6,axis=1)&np.all(A<=hi+6,axis=1)
                    ar,ac,aw=tri_weights(A[near])
                    for rows_,cols_,weights_,road in zip(ar,ac,aw,other['axis_road'][near]):
                        if np.isfinite(road):
                            current=float(np.sum(weights_*H[rows_,cols_]))
                            add({(int(r),int(c)):float(w) for r,c,w in zip(rows_,cols_,weights_)},max(road-AXIS_CLEAR,current)+1e-7)
                faces=set()
                for r,c in verts:
                    for dr,dc in ((-1,-1),(-1,0),(0,-1),(0,0)):
                        a,b=r+dr,c+dc
                        for face in (((a,b),(a,b+1),(a+1,b+1)),((a,b),(a+1,b),(a+1,b+1))):
                            if (r,c) in face: faces.add(face)
                for face in sorted(faces):
                    xy=np.array([[6*(v[1]-face[0][1]),6*(v[0]-face[0][0])] for v in face[1:]],float)
                    inv=np.linalg.inv(xy); grad=inv@np.array([H0[v]-H0[face[0]] for v in face[1:]])
                    cap=max(math.tan(math.radians(35.0)),float(np.linalg.norm(grad)))
                    for angle in np.arange(32)*2*math.pi/32:
                        a=np.array([math.cos(angle),math.sin(angle)])@inv
                        add({face[0]:-a.sum(),face[1]:a[0],face[2]:a[1]},cap*math.cos(math.pi/32))
                result=linprog(np.ones(n),A_ub=np.array(rows),b_ub=np.array(limits),bounds=[(float(H[v]),float(H[v]+4)) for v in verts],method='highs')
                if not result.success:
                    entry['reason']='native constraints infeasible';log.append(entry);continue
                old=np.array([H[v] for v in verts]); window=(slice(max(0,r0-3),min(2048,r1+4)),slice(max(0,c0-3),min(2048,c1+4)))
                before=[m for _,m,_ in small_shapes(H[window],.50)]
                for v,h in zip(verts,result.x):H[v]=h
                after=[m for _,m,_ in small_shapes(H[window],.50)]
                if any((a & ~b).any() for a,b in zip(after,before)):
                    for v,h in zip(verts,old):H[v]=h
                    entry['reason']='would create native mound';log.append(entry);continue
                for v,h0 in zip(verts,old):
                    if H[v]>h0+1e-6:banks[v]=True
                entry.update(solved=True,vertices_changed=int((result.x-old>1e-6).sum()),max_raise_m=round(float((result.x-old).max()),4))
                log.append(entry)
    return log


def mound_pass(H, band, movable, floor_v):
    """Lower-only: lay every small shape (SHAPES) of movable band vertices standing > MOUND_T above its ring down to the ring's
    highest vertex (not below floor_v / MOUND_FLOOR), MOUND_PASSES times. Returns (H, lowered mask, passes, shapes laid,
    shapes left because a vertex is not movable)."""
    H = H.copy(); lowered = np.zeros(H.shape, bool); fl = np.maximum(floor_v, MOUND_FLOOR)
    act = band & movable
    laid, blocked, passes = 0, 0, 0
    for passes in range(1, MOUND_PASSES + 1):
        any_ = False
        for S, anc, rmax in small_shapes(H, MOUND_T):
            inb = anc.copy()
            for dr, dc in S:
                inb &= shifted(band, dr, dc, False)
            if not inb.any():
                continue
            okm = inb.copy()
            for dr, dc in S:
                okm &= shifted(act, dr, dc, False)
            if passes == 1:
                blocked += int((inb & ~okm).sum())
            for r, c in np.argwhere(okm):
                for dr, dc in S:
                    v = (r + dr, c + dc)
                    t = max(float(rmax[r, c]), float(fl[v]))
                    if H[v] > t + 1e-6:
                        H[v] = t; lowered[v] = True; any_ = True
                laid += 1
        if not any_:
            break
    return H, lowered, passes, laid, blocked


def ring_pyramids(H, seat, floor_v):
    """Seat vertices standing more than MOUND_T above all six native neighbours: lowered to that highest + MOUND_RING."""
    nmax = np.full(H.shape, -np.inf)
    for dr, dc in NATIVE:
        nmax = np.maximum(nmax, shifted(H, dr, dc, np.inf))
    m = seat & (H - nmax > MOUND_T)
    H = H.copy(); H[m] = np.maximum(nmax[m] + MOUND_RING, np.maximum(floor_v[m], MOUND_FLOOR))
    return H, m


def seat_shapes(H, zone, seat, movable, floor_v):
    """v10: the six shapes (SHAPES) of zone vertices that hold a seat vertex, every vertex seat or movable, standing > MOUND_T
    above their native ring (a ring-1 vertex left above low land at a chain end or corner: 12 new pairs up to 1.25 m in the
    first rollout, review of 18-10) are lowered to the ring's highest vertex + MOUND_RING, never below floor_v (the burial floor
    yq + 0.25 + BURY: the vertex stays above the sheet, the waterline bulges there) nor MOUND_FLOOR. Lower-only, up to
    MOUND_PASSES times. Returns (H, lowered mask, shapes laid, shapes left above the floor)."""
    H = H.copy(); lowered = np.zeros(H.shape, bool); fl = np.maximum(floor_v, MOUND_FLOOR)
    ok_v = zone & (seat | movable)
    laid = 0
    for _ in range(MOUND_PASSES):
        any_ = False
        for S, anc, rmax in small_shapes(H, MOUND_T):
            m = anc.copy(); hs = np.zeros(H.shape, bool)
            for dr, dc in S:
                m &= shifted(ok_v, dr, dc, False); hs |= shifted(seat, dr, dc, False)
            m &= hs
            for r, c in np.argwhere(m):
                for dr, dc in S:
                    v = (r + dr, c + dc)
                    t = max(float(rmax[r, c]) + MOUND_RING, float(fl[v]))
                    if H[v] > t + 1e-6:
                        H[v] = t; lowered[v] = True; any_ = True
                laid += 1
        if not any_:
            break
    left = 0
    for S, anc, _ in small_shapes(H, MOUND_T):
        m = anc.copy(); hs = np.zeros(H.shape, bool)
        for dr, dc in S:
            m &= shifted(ok_v, dr, dc, False); hs |= shifted(seat, dr, dc, False)
        left += int((m & hs).sum())
    return H, lowered, laid, left


def dist_grid(V, r0, r1, c0, c1, rmax):
    """Distance of the grid vertices r0..r1 x c0..c1 to the polyline V (no extension); inf beyond rmax."""
    d = np.full((r1 - r0 + 1, c1 - c0 + 1), np.inf)
    for a, b in zip(V[:-1], V[1:]):
        lo, hi = np.minimum(a, b) - rmax, np.maximum(a, b) + rmax
        ra, rb = max(int(math.floor((ZTOP - hi[1]) / 6.0)), r0), min(int(math.ceil((ZTOP - lo[1]) / 6.0)), r1)
        ca, cb = max(int(math.floor(lo[0] / 6.0)), c0), min(int(math.ceil(hi[0] / 6.0)), c1)
        if ra > rb or ca > cb:
            continue
        RR, CC = np.mgrid[ra:rb + 1, ca:cb + 1]
        dd = seg_dist(np.c_[6.0 * CC.ravel(), ZTOP - 6.0 * RR.ravel()], a, b)[0].reshape(RR.shape)
        blk = d[ra - r0:rb - r0 + 1, ca - c0:cb - c0 + 1]
        d[ra - r0:rb - r0 + 1, ca - c0:cb - c0 + 1] = np.minimum(blk, dd)
    d[d > rmax] = np.inf
    return d


def prominence(H):
    n = np.full(H.shape, -np.inf)
    for dr, dc in NATIVE:
        sh = np.full(H.shape, -np.inf)
        rs = slice(max(dr, 0), H.shape[0] + min(dr, 0)); rd = slice(max(-dr, 0), H.shape[0] + min(-dr, 0))
        cs = slice(max(dc, 0), H.shape[1] + min(dc, 0)); cd = slice(max(-dc, 0), H.shape[1] + min(-dc, 0))
        sh[rd, cd] = H[rs, cs]
        n = np.maximum(n, sh)
    return H - n


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    assert len(argv) == 10 and flags <= {"--no-mounds"}, __doc__.split("Usage:")[1][:400]
    tpath, fpath, cpath, epath, spath, out_t, out_c, out_e, rec_path, rep_path = argv
    mounds_on = "--no-mounds" not in flags
    models = load_models(); sgeo = load_stones()
    z = np.load(tpath); arrays = {k: z[k].copy() for k in z.files}
    H0 = arrays["heights"].astype(np.float64); H = H0.copy()
    frozen = arrays["reserve"] | arrays["platform"] | arrays["narva"]
    frozen_r = frozen | arrays["v31_bridge_cut"] if "v31_bridge_cut" in arrays else frozen
    near_frozen = frozen_r.copy()
    for dr, dc in NATIVE:
        near_frozen |= shifted(frozen_r, dr, dc, False)
    fpz = np.load(fpath); pl = fpz["plane"].astype(np.float64); visible = fpz["visible"]
    cover = np.load(cpath).astype(np.float64); env = np.load(epath).astype(np.float64)
    vp = np.full(H.shape, -np.inf); cp = np.where(np.isfinite(pl), pl, -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            vp[dr:dr + 2047, dc:dc + 2047] = np.maximum(vp[dr:dr + 2047, dc:dc + 2047], cp)
    wet = np.isfinite(vp) & (H0 < vp)
    lab, _ = label(wet, np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]]))
    sites = json.load(open(spath))
    # kept wet vertices: wet in the input and in no site's body (component sites: their whole wet component)
    claimed = np.zeros(H.shape, bool)
    for site in sites:
        if site.get("mode", "component") == "reach":
            b = np.array(site["body"], int).reshape(-1, 2)
            claimed[b[:, 0], b[:, 1]] = True
        else:
            sr, sc = int(round((ZTOP - site["seed"][1]) / 6)), int(round(site["seed"][0] / 6))
            w = np.argwhere(wet[sr - 3:sr + 4, sc - 3:sc + 4])
            if len(w):
                rr, cc = w[np.argmin(np.hypot(w[:, 0] - 3, w[:, 1] - 3))] + (sr - 3, sc - 3)
                claimed |= lab == lab[rr, cc]
    kept = wet & ~claimed
    kept_cells=kept[:-1,:-1]|kept[:-1,1:]|kept[1:,:-1]|kept[1:,1:]
    def receiving_water(Q):
        rp=(ZTOP-Q[:,1])/6;cp=Q[:,0]/6;rr=np.floor(rp).astype(int);cc=np.floor(cp).astype(int)
        plane=np.full(len(Q),-np.inf)
        for dr in (0,-1):
            for dc in (0,-1):
                r,c=rr+dr,cc+dc
                valid=(r>=0)&(r<2047)&(c>=0)&(c<2047)
                if dr:valid &= np.abs(rp-rr)<1e-8
                if dc:valid &= np.abs(cp-cc)<1e-8
                ix=np.flatnonzero(valid)
                eligible=kept_cells[r[ix],c[ix]]&np.isfinite(env[r[ix],c[ix]])
                ix=ix[eligible];plane[ix]=np.maximum(plane[ix],env[r[ix],c[ix]])
        return tri_h(H0,Q[:,0],Q[:,1])<plane-.001
    rng = np.random.default_rng(20261015); rng_st = np.random.default_rng(20261017)
    records, report, checks = [], [], []
    touched = np.zeros(H.shape, bool); seat_all = np.zeros(H.shape, bool); protect_all = np.zeros(H.shape, bool)
    band_all = np.zeros(H.shape, bool); floor_all = np.full(H.shape, -np.inf); sill_all = np.zeros(H.shape, bool)
    axis_v = np.zeros(H.shape, bool)                                # vertices of triangles under an axis sample
    prior_pts = []
    built = {}                                                      # v10: site id -> lattice polyline and profile (kit junctions)
    jrim_all = np.zeros(H.shape, bool)                              # v10: kept dry rims lowered under a junction
    jbank_all = np.zeros(H.shape, bool)                             # v10: kept dry vertices raised as junction banks
    t_start = time.time()
    for k_site, site in enumerate(sites):
        print(f"[{time.time() - t_start:7.1f} s] site {k_site + 1}/{len(sites)} {site['id']}", file=sys.stderr, flush=True)
        fam = site["family"]; dims = kit_dims(models, fam); mode = site.get("mode", "component")
        if mode == "component":
            ax = site_axis(site, vp, wet, lab)
            if ax is None:
                report.append(dict(site=site["id"], mode=mode, skipped="body of one vertex")); continue
            body, planes, P, s, W = ax
            fz_path = frozen
        else:
            body = np.zeros(H.shape, bool); b = np.array(site["body"], int).reshape(-1, 2)
            if not len(b):
                report.append(dict(site=site["id"], mode=mode, skipped="empty body")); continue
            body[b[:, 0], b[:, 1]] = True; planes = vp[body]
            # v10 junctions: a pond/bridge end runs on to the kept water (target J), a kit end to the partner's lattice
            stem = np.array(site["stem"], int); juncs, ext_to = {}, {}
            for side in ("up", "dn"):
                typ = (site.get("ends") or {}).get(side)
                if typ in ("pond", "bridge", "sea"):
                    J, why = junction_target(stem[0] if side == "up" else stem[-1], kept, vp, H0, True)
                    juncs[side] = dict(type=typ, failed=why) if J is None else dict(type=typ, J=[float(J[0]), float(J[1])])
                    if J is not None:
                        e_ = stem[0] if side == "up" else stem[-1]; u_ = J - xz(*e_)
                        ext_to[side] = J + 6.0 * u_ / max(np.linalg.norm(u_), 1e-6)
                elif typ == "kit":
                    pid = ((site.get("extend") or {}).get(side) or {}).get("partner")
                    if pid in built:
                        Pp = built[pid]["PLn"]; to = np.array(site["extend"][side]["to"], float)
                        sq = float(np.clip(Pp.project(to)[1][0], 0.0, Pp.cum[-1])); Tp = Pp.at([sq])[0]
                        e_ = stem[0] if side == "up" else stem[-1]; u_ = Tp - xz(*e_)
                        Tx = Tp + 6.0 * u_ / max(np.linalg.norm(u_), 1e-6)
                        juncs[side] = dict(type="kit", partner=pid, J=[float(Tp[0]), float(Tp[1])]); ext_to[side] = Tx
                    else:
                        juncs[side] = dict(type="kit", partner=pid, failed="partner not built")
            P, s, W = reach_axis(site, vp, ext_to)
            # the path keeps one vertex step off envelope water at another level (its seat would otherwise cut a 5 m
            # wall under a perched pond rim: 4 triangles at 36-45 deg in a dev run of 17-10)
            oth = np.isfinite(env) & ((env < planes.min() - 0.05) | (env > planes.max() + 0.05))
            jex_c = np.zeros(oth.shape, bool)                          # v10: the target water of a pond/bridge junction
            for j_ in juncs.values():
                if "J" in j_ and j_["type"] != "kit":
                    cx, cz = j_["J"]; c_, r_ = int(cx / 6.0), int((ZTOP - cz) / 6.0); k_ = int(JUNC_EX / 6.0) + 2
                    RR, CC = np.mgrid[max(r_ - k_, 0):min(r_ + k_, 2046) + 1, max(c_ - k_, 0):min(c_ + k_, 2046) + 1]
                    nr_ = np.hypot(6.0 * CC + 3 - cx, ZTOP - 6.0 * RR - 3 - cz) <= JUNC_EX
                    jex_c[RR[nr_], CC[nr_]] = True
            oth &= ~jex_c
            othv = c2v(oth) | frozen_r                                 # and one step off reserve/platform/narva/bridge cut
            near_oth = othv.copy()
            for dr, dc in NATIVE:
                near_oth |= shifted(othv, dr, dc, False)
            fz_path = frozen_r | near_oth
        try:
            # Reserve a corner and its end extension. At a receiving pond the
            # terminal straight must reach the actual retained wet surface:
            # an endpoint merely within 6 m can run beside the pond instead.
            end_run = tuple(18.0 if juncs.get(sd, {}).get("type") in ("pond", "bridge", "sea", "kit") else
                            (0.0 if sd == "up" else 6.0) for sd in ("up", "dn")) if mode == "reach" else (0.0, 6.0)
            targets = tuple(juncs.get(sd, {}).get("J") if juncs.get(sd, {}).get("type") in ("pond", "bridge", "sea") else None
                            for sd in ("up", "dn")) if mode == "reach" else (None,None)
            verts = dirs = None
            # Preserve a completely straight reach when it already has a legal
            # lateral connection. Forcing that reach through a representative
            # pond vertex can create a broad dogleg. Curved routes must instead
            # carry their terminal straight through the retained wet target.
            if mode=='reach' and any(t is not None for t in targets):
                try:
                    candidate_v,candidate_d=lattice_path(P,fz_path,end_run,targets,receiving_water)
                    if len(set(candidate_d))==1:
                        verts,dirs=candidate_v,candidate_d
                except AssertionError:
                    pass
            if verts is None:
                verts,dirs=lattice_path(P,fz_path,end_run,targets)
        except AssertionError:
            report.append(dict(site=site["id"], mode=mode, skipped="no lattice path")); continue
        segs = segments(dirs)
        V = np.array([vxz(*v) for v in verts]); PLn = Polyline(V); cum = PLn.cum
        # ---- reach mode: cut the thin channel first (fixed by the body; v10: before the pieces, so the junctions are known
        # when the profile and the chain ends are set). At a pond/bridge junction the cut follows the path only up to the stem
        # end: the target water beyond keeps its cells and ends at a sill, which the chain crosses (see 'junctions').
        rcut = None; jinfo = {}; jrim_site = np.zeros(H.shape, bool)
        if mode == "reach":
            s_stem = [float(PLn.project(xz(*stem[0]))[1][0]), float(PLn.project(xz(*stem[-1]))[1][0])]
            pj = {sd: ("J" in juncs.get(sd, {}) and juncs[sd]["type"] != "kit") for sd in ("up", "dn")}
            a_ = max(s_stem[0], 0.0) if pj["up"] else 0.0
            b_ = min(s_stem[1], float(cum[-1])) if pj["dn"] else float(cum[-1])
            inner = cum[(cum > a_ + 1e-6) & (cum < b_ - 1e-6)]
            V_cut = PLn.at(np.r_[a_, inner, b_]) if b_ - a_ > 1.0 else V
            rcut = reach_cut(body, kept, cover, env, planes, H, frozen, V_cut, juncs)
            rs0, rs1, cs0, cs1 = rcut["win"]
            sv = np.argwhere(rcut["sill"]) + (rs0, cs0)
            sill_pts = np.c_[6.0 * sv[:, 1], ZTOP - 6.0 * sv[:, 0]] if len(sv) else np.zeros((0, 2))
            prior = np.vstack(prior_pts) if prior_pts else np.zeros((0, 2))
            prot_v = c2v(np.isfinite(env))                              # vertices of the envelope cells left after the cut
            prot_h = H.copy()
            ph = prot_h[rs0:rs1 + 1, cs0:cs1 + 1]
            prot_h[rs0:rs1 + 1, cs0:cs1 + 1] = np.where(rcut["sill"], np.maximum(ph, rcut["target"]), ph)
            keptP_v = c2v_max(np.where(np.isfinite(env), env, -np.inf))
            # v10: at a pond/bridge junction the path ends one step beyond its first vertex of the kept water (the sill line),
            # straight on through it: no corner piece in the target water
            for side in ("dn", "up"):
                j_ = juncs.get(side, {})
                if "J" not in j_ or j_["type"] == "kit":
                    continue
                vidx = [i for i in range(len(verts)) if cum[i] >= s_stem[1] - 1e-6] if side == "dn" else \
                    [i for i in range(len(verts) - 1, -1, -1) if cum[i] <= s_stem[0] + 1e-6]
                kB = next((i for i in vidx if prot_v[verts[i]]), None)
                if kB is not None:
                    # the receiving water itself: the first kept wet vertex from the sill line on (dry kept rims may lie
                    # between, a dev run of 18-10 ended 4 junctions over them, 0.15-0.8 m short of the water)
                    kB = next((i for i in vidx[vidx.index(kB):] if kept[verts[i]] and prot_v[verts[i]] and prot_h[verts[i]] < keptP_v[verts[i]]), kB)
                if kB is None or (side == "dn" and kB == 0) or (side == "up" and kB >= len(verts) - 1):
                    continue
                if side == "dn":
                    d_in = dirs[kB - 1]
                    verts = list(verts[:kB + 1]) + [(verts[kB][0] + DIRS[d_in][0], verts[kB][1] + DIRS[d_in][1])]
                    dirs = list(dirs[:kB]) + [d_in]
                else:
                    d_out = dirs[kB]
                    verts = [(verts[kB][0] - DIRS[d_out][0], verts[kB][1] - DIRS[d_out][1])] + list(verts[kB:])
                    dirs = [d_out] + list(dirs[kB:])
                segs = segments(dirs)
                V = np.array([vxz(*v) for v in verts]); PLn = Polyline(V); cum = PLn.cum
                s_stem = [float(PLn.project(xz(*stem[0]))[1][0]), float(PLn.project(xz(*stem[-1]))[1][0])]
                j_["path_cut_at_sill"] = True
            for side, j_ in juncs.items():
                ji = dict(j_)
                jinfo[side] = ji
                if "J" not in j_:
                    continue
                if j_["type"] != "kit":
                    sB = junction_B(side, PLn, s_stem, prot_v)
                    if sB is None:
                        ji["failed"] = "the path reaches no vertex of the kept water"; continue
                    out_i = [i for i in range(len(V)) if cum[i] >= sB - 1e-6] if side == "dn" else \
                        [i for i in range(len(V) - 1, -1, -1) if cum[i] <= sB + 1e-6]
                    vv_ = lambda i: (int(round((ZTOP - V[i][1]) / 6.0)), int(round(V[i][0] / 6.0)))
                    kw_ = next((i for i in out_i if kept[vv_(i)] and prot_v[vv_(i)] and prot_h[vv_(i)] < keptP_v[vv_(i)]), None)
                    dW = abs(float(cum[kw_]) - sB) if kw_ is not None else 0.0
                    ji.update(sW=round(float(cum[kw_]) if kw_ is not None else sB, 3), win=[round(dW - 6.0, 3), round(dW, 3)],
                              wet_on_axis=kw_ is not None)
                    # the kept dry vertices of the triangles under the path from JUNC_L0 before the sill line to 8 m beyond
                    # it (the end piece's flat end and lip) are lowered to their plane + SILL_UP (still buried pond edges,
                    # as the slope guard's dry rims): a rim 2 m above the pond would otherwise lift the junction by 2 m
                    zr = (sB - JUNC_L0, sB + dW + 8.0) if side == "dn" else (sB - dW - 8.0, sB + JUNC_L0)
                    stz = np.arange(zr[0], zr[1] + 1e-9, 0.25); Pz0 = PLn.at(stz)
                    tz = np.gradient(Pz0, axis=0); tz /= np.linalg.norm(tz, axis=1)[:, None] + 1e-12; nz_ = np.c_[-tz[:, 1], tz[:, 0]]
                    Pz_ = np.vstack([Pz0 + o_ * nz_ for o_ in np.arange(-1.5, 1.51, 0.5)])   # piece centrelines leave the lattice by < 1.5 m
                    rz, cz, wz = tri_weights(Pz_)
                    rz, cz = np.clip(rz, 0, 2047), np.clip(cz, 0, 2047)
                    mz = prot_v[rz, cz] & ~near_frozen[rz, cz] & (wz >= JUNC_W) & (prot_h[rz, cz] > keptP_v[rz, cz] + SILL_UP)
                    jr_v = np.unique(np.c_[rz[mz], cz[mz]], axis=0).reshape(-1, 2)
                    for rj,cj in jr_v:
                        lower,upper=vertex_height_bounds(prot_h,H0,int(rj),int(cj))
                        goal=max(float(keptP_v[rj,cj])+SILL_UP,lower)
                        if goal <= min(float(prot_h[rj,cj]),upper): prot_h[rj,cj]=goal
                    jrim_site[jr_v[:, 0], jr_v[:, 1]] = True
                    mk = prot_v[rz, cz] & (wz >= JUNC_W)                 # the whole zone (several planes along a thin
                    # Terrain is interpolated on native triangles. A tall rim
                    # with a small barycentric weight must not lift the whole
                    # junction to that vertex's height. Free vertices can be
                    # lowered to LOW_FLOOR; retained vertices stay fixed here.
                    hk = float((wz*np.where(prot_v[rz,cz],prot_h[rz,cz],LOW_FLOOR)).sum(axis=1).max())
                    ji["rims_lowered"] = int(len(jr_v))
                    vb = (int(round((ZTOP - PLn.at([sB])[0][1]) / 6.0)), int(round(PLn.at([sB])[0][0] / 6.0)))
                    ji.update(sB=round(sB, 3), B_xz=PLn.at([sB])[0].round(2).tolist(), plane_B=round(float(keptP_v[vb]), 3),
                              kept_high_m=round(hk, 3), Yj=round(hk + AXIS_CLEAR + JUNC_SLACK, 3))
                else:
                    Pp = built[j_["partner"]]["PLn"]
                    st_ = np.arange(s_stem[1], cum[-1] + 1e-9, 0.25) if side == "dn" else np.arange(s_stem[0], -1e-9, -0.25)
                    Q_ = PLn.at(st_); dq_ = np.full(len(Q_), np.inf)
                    for i_ in range(len(Pp.V) - 1):
                        dq_ = np.minimum(dq_, seg_dist(Q_, Pp.V[i_], Pp.V[i_ + 1])[0])
                    hit = np.nonzero(dq_ <= JUNC_KIT_REACH)[0]
                    if not len(hit):
                        ji["failed"] = "the path does not come within %.1f m of the partner's lattice" % JUNC_KIT_REACH; continue
                    sB = float(st_[hit[0]])
                    sq = float(np.clip(Pp.project(PLn.at([sB]))[1][0], 0.0, Pp.cum[-1]))
                    Yp = float(np.interp(sq, built[j_["partner"]]["sL"], built[j_["partner"]]["Y"]))
                    # Match the receiving roadway. The former extra 5 cm
                    # raised the tributary sheet beyond the dry-bank height
                    # permitted by the receiving branch's axis clearance.
                    ji.update(sB=round(sB, 3), B_xz=PLn.at([sB])[0].round(2).tolist(), partner_roadway=round(Yp, 3), Yj=round(Yp, 3),
                              win=list(JUNC_WIN))
        # ---- corners
        corners = []
        for a, b in zip(segs[:-1], segs[1:]):
            tt, dturn = turn_type(HEAD[a[0]], HEAD[b[0]])
            cn = dict(at=b[1], type=tt, d_in=a[0], d_out=b[0], turn=dturn)
            if tt == "curve":
                up_turn = (HEAD[a[0]] - HEAD[b[0]] + 540) % 360 - 180      # heading change travelling upstream
                kind = "long_curve_left" if up_turn > 0 else "long_curve_right"
                g = models[f"{fam}_{kind}"]
                cn.update(kind=kind, s=CURVE_S, t_up=g["pi"]["pi_to_exit"], t_dn=g["pi"]["entry_to_pi"],
                          lip_up=dims[kind]["lip_up"], lip_dn=dims[kind]["lip_dn"])
            else:
                # leg pieces: occupancy = 3 m to the origin + the far plate end of the centreline (scaled)
                k_up = "short_slanted_inv" if a[0] in ("N", "S") else "short_slanted"      # upstream leg (d_in), far end = +Z
                k_dn = "short_slanted_inv" if b[0] in ("N", "S") else "short_slanted"      # downstream leg (d_out), far end = -Z
                cn.update(kind="elbow", s=SLANT_S, t_up=3.0 / SLANT_S + dims[k_up]["z_up"], t_dn=3.0 / SLANT_S - dims[k_dn]["z_dn"],
                          lip_up=dims[k_up]["lip_up"], lip_dn=dims[k_dn]["lip_dn"])
            corners.append(cn)
        runs = []
        for si, (d, i0, i1) in enumerate(segs):
            runs.append(dict(d=d, i0=i0, i1=i1, L=float(cum[i1] - cum[i0]), lo=corners[si - 1] if si > 0 else None,
                             hi=corners[si] if si < len(corners) else None))
        lip_s = dims["long_straight"]["lip_up"]

        def gap(rn):
            a = rn["lo"]["s"] * rn["lo"]["t_dn"] if rn["lo"] else 0.0
            b = rn["hi"]["s"] * rn["hi"]["t_up"] if rn["hi"] else 0.0
            return rn["L"] - a - b, a, b

        def lips(rn):
            return (rn["lo"]["s"] * rn["lo"]["lip_dn"] if rn["lo"] else 0.0, rn["hi"]["s"] * rn["hi"]["lip_up"] if rn["hi"] else 0.0)

        def direct_ok(rn, G):
            if rn["lo"] is None or rn["hi"] is None:
                return G <= 6.0 and (rn["lo"] is not None or rn["hi"] is not None)
            la, lb = lips(rn)
            return -DIRECT_MAX <= G <= -max(OV_FLOOR, la + lb - DIP_SPAN)

        def feasible(rn):
            G, _, _ = gap(rn); la, lb = lips(rn)
            return direct_ok(rn, G) or fill_run(G, la, lb, rn["lo"] is None, rn["hi"] is None, lip_s) is not None
        for it in range(60):
            changed = False
            for rn in runs:
                if feasible(rn):
                    continue
                G, _, _ = gap(rn)
                # move curve scales: towards a direct joint when the gap is small or negative, else towards a longer gap
                la, lb = lips(rn)
                tgt_dir = -max(OV_FLOOR, la + lb - DIP_SPAN) if (rn["lo"] and rn["hi"]) else None
                grow = tgt_dir is not None and G > tgt_dir and G - tgt_dir < 2.0
                for cn in (rn["lo"], rn["hi"]):
                    if cn and cn["type"] == "curve":
                        if grow and cn["s"] < CURVE_S_MAX - 1e-9:
                            cn["s"] = round(cn["s"] + 0.02, 3); changed = True
                        elif not grow and cn["s"] > CURVE_S_MIN + 1e-9:
                            cn["s"] = round(cn["s"] - 0.02, 3); changed = True
            if not changed:
                break
        PL, sL = resample(V, 0.5)
        Y = profile_on(PL, P, W, H0, BED_MIN - SEAT0 if mode == "component" else REACH_Y_MIN)
        for side, ji in jinfo.items():
            # v10: the roadway reaches Yj (kept heights under the axis at the sill + AXIS_CLEAR + 0.02; kit ends: the partner's
            # roadway) JUNC_L0 m before the sill line and over it, and leaves it at JUNC_G m/m
            if "sB" not in ji:
                continue
            if side == "dn":
                F = ji["Yj"] - JUNC_G * np.maximum(0.0, (ji["sB"] - JUNC_L0) - sL)
            else:
                F = ji["Yj"] - JUNC_G * np.maximum(0.0, sL - (ji["sB"] + JUNC_L0))
            ji["lift_max_m"] = round(float(np.max(np.maximum(F - Y, 0.0))), 3)
            ji["lift_length_m"] = round(float(0.5 * np.sum(F > Y + 1e-6)), 1)
            Y = np.maximum(Y, F)

        def Yat(st):
            return float(np.interp(st, sL, Y))
        pieces, notes, seen_slant = [], [], set()
        curve_ends = []
        for cn in corners:
            iv = cn["at"]; Cw = V[iv]; st = cum[iv]
            if cn["type"] == "curve":
                g = models[f"{fam}_{cn['kind']}"]; s_ = cn["s"]
                u_dn_leg, u_up_leg = unit(cn["d_out"]), unit(cn["d_in"])
                # entry (downstream end) points upstream along -d_out, exit along -d_in; balanced yaw
                th1 = heading_of(-u_dn_leg) - heading_of(g["entry"]["dir_up"])
                th2 = heading_of(-u_up_leg) - heading_of(g["exit"]["dir_up"])
                dth = (th2 - th1 + 540) % 360 - 180
                theta = th1 + dth / 2
                st_up, st_dn = st - s_ * cn["t_up"], st + s_ * cn["t_dn"]
                y = 0.5 * (Yat(st_up) + Yat(st_dn))
                R = yaw_frame(theta, s_)
                pim = np.array([g["pi"]["xz"][0], g["roadway_flat_y"], g["pi"]["xz"][1]])
                T = np.array([Cw[0], y, Cw[1]]) - R @ pim
                ends = []
                for e_, line_pt, u_ in ((g["entry"]["centre"], Cw, u_dn_leg), (g["exit"]["centre"], Cw, u_up_leg)):
                    w_ = R @ np.array(e_) + T; d_ = w_[[0, 2]] - line_pt
                    ends.append(round(float(abs(d_[0] * u_[1] - d_[1] * u_[0])), 4))
                curve_ends.append(dict(at=Cw.tolist(), kind=cn["kind"], scale=s_, yaw_split_deg=round(dth / 2, 3), end_offset_m=ends))
                pieces.append(dict(kind=cn["kind"], R=R, T=T, s=s_, st=(st_up, st_dn), flat=(st_up + s_ * cn["lip_up"], st_dn - s_ * cn["lip_dn"]), pitch=0.0))
            else:
                s_ = SLANT_S
                for leg, sign in ((cn["d_in"], -1), (cn["d_out"], +1)):
                    kind = "short_slanted_inv" if leg in ("N", "S") else "short_slanted"
                    u_leg = unit(leg); o = Cw + sign * 3.0 * u_leg
                    key = (round(float(o[0]), 1), round(float(o[1]), 1))
                    if key in seen_slant:
                        continue
                    seen_slant.add(key)
                    R = yaw_frame(heading_of(-u_leg), s_)
                    stp = st + sign * 3.0; y = Yat(stp)
                    T = np.array([o[0], y, o[1]]) - R @ np.array([0.0, models[f"{fam}_{kind}"]["roadway_flat_y"], 0.0])
                    a_, b_ = stp - s_ * dims[kind]["z_up"], stp - s_ * dims[kind]["z_dn"]
                    pieces.append(dict(kind=kind, R=R, T=T, s=s_, st=(a_, b_), flat=(a_ + s_ * dims[kind]["lip_up"], b_ - s_ * dims[kind]["lip_dn"]), pitch=0.0))
        nfill = dict(direct=0, filled=0, failed=0)
        run_log = []
        for rn in runs:
            G, a, b = gap(rn); la, lb = lips(rn)
            ends = (rn["lo"] is None, rn["hi"] is None)
            sol = fill_run(G, la, lb, *ends, lip_s)
            slide = 0.0; d_lo = d_hi = 0.0
            jt = {k_: jinfo[sd_] for k_, sd_, e_ in (("lo", "up", ends[0]), ("hi", "dn", ends[1])) if e_ and "sB" in jinfo.get(sd_, {})}
            if jt:
                # The end lies within six metres before the first retained wet vertex.
                # Avoid an elevated water sheet spanning the receiving pond.
                grid = sorted(np.arange(-JUNC_SLIDE, JUNC_SLIDE + 1e-9, 0.05), key=lambda x: (abs(x), x))
                if len(jt) == 2:
                    g2 = sorted(np.arange(-JUNC_SLIDE, JUNC_SLIDE + 1e-9, 0.25), key=lambda x: (abs(x), x))
                    combos = [(x, y) for x in g2 for y in g2]
                else:
                    combos = [(x, 0.0) for x in grid] if "lo" in jt else [(0.0, y) for y in grid]
                found = None; best_end = None
                for dl, dh in combos:
                    sol_ = fill_run(G + dl + dh, la, lb, *ends, lip_s)
                    if sol_ is None:
                        continue
                    lay = run_layout(sol_, G, a, ends, dl, dh, cum[rn["i0"]], dims)
                    ok_ = True
                    if "lo" in jt:
                        ok_ &= jt["lo"]["sB"] - jt["lo"]["win"][1] <= lay[0][3][0] <= jt["lo"]["sB"] - jt["lo"]["win"][0]
                    if "hi" in jt:
                        ok_ &= jt["hi"]["sB"] + jt["hi"]["win"][0] <= lay[-1][3][1] <= jt["hi"]["sB"] + jt["hi"]["win"][1]
                    if ok_:
                        # Leave lip room inside [W-6,W]. At an immediately wet
                        # sill or a diagonal wet step, use its dry boundary.
                        # Off-axis receivers need the nearest boundary because
                        # their transverse gap already uses the six-metre budget.
                        # Kit links retain their first feasible placement.
                        error = 0.0
                        for key_, sign_, flat_ in (("lo", -1, lay[0][3][0]), ("hi", 1, lay[-1][3][1])):
                            if key_ not in jt or jt[key_]["type"] == "kit":
                                continue
                            j_ = jt[key_]
                            offset_ = ((j_["win"][0] if abs(j_["sW"]-j_["sB"])<.01 or abs(j_["sW"]-j_["sB"])>6.01 else sum(j_["win"])/2)
                                       if j_.get("wet_on_axis") else j_["win"][1])
                            error += abs(flat_ - (j_["sB"] + sign_*offset_))
                        score = (round(error, 8), abs(dl)+abs(dh), dl, dh)
                        if best_end is None or score < best_end:
                            best_end = score; found = (float(dl), float(dh), sol_)
                        if error < .02:
                            break
                for k_, ji in jt.items():
                    ji["window_slide_m"] = (round(found[0 if k_ == "lo" else 1], 2) if found else None)
                    ji["run"] = [round(float(cum[rn["i0"]]), 2), round(float(cum[rn["i1"]]), 2), round(float(G), 2), rn["lo"]["kind"] if rn["lo"] else None, rn["hi"]["kind"] if rn["hi"] else None]
                if found:
                    d_lo, d_hi, sol = found
            if sol is None and ends[0] != ends[1]:
                # v9: a chain-end run with one free end has no slack in v8 (18 m end runs after an elbow, gap ~11.35 m, could
                # not be filled: 30 gaps in a dev run of 17-10); the free end may slide by up to END_SLIDE m
                for d in sorted(np.arange(-END_SLIDE, END_SLIDE + 1e-9, 0.25), key=lambda x: (abs(x), x)):
                    sol = fill_run(G + d, la, lb, *ends, lip_s)
                    if sol is not None:
                        slide = float(d); break
                if sol is not None:
                    d_lo, d_hi = (slide, 0.0) if ends[0] else (0.0, slide)
            if sol is None:
                okd = direct_ok(rn, G)
                nfill["direct" if okd else "failed"] += 1
                run_log.append(dict(at=[V[rn["i0"]].tolist(), V[rn["i1"]].tolist()], gap=round(G, 3), fill="direct" if okd else "FAILED"))
                continue
            nfill["filled"] += 1
            _, nl, ns, sc, ov = sol
            u = unit(rn["d"]); A0 = V[rn["i0"]] + a * u
            lay = run_layout(sol, G, a, ends, d_lo, d_hi, cum[rn["i0"]], dims)
            run_log.append(dict(at=[V[rn["i0"]].tolist(), V[rn["i1"]].tolist()], gap=round(G, 3), fill=[x[0] for x in lay], scale=sc, overlap=round(ov, 3),
                                **(dict(end_slide_m=slide) if slide else {}), **(dict(junction_slide_m=[d_lo, d_hi]) if jt else {})))
            for k_, st0, st1, _fl, pos in lay:
                Lk = (24.0 if k_ == "long_straight" else 12.0) * sc
                ya, yb = Yat(st0), Yat(st1)
                phi = math.atan2(ya - yb, Lk)
                c_ = A0 + (pos + Lk / 2) * u
                kk = k_ if k_ != "long_straight" or rng.random() >= 0.25 or f"{fam}_long_straight_2" not in models else "long_straight_2"
                R = yaw_frame(heading_of(-u), sc, phi)
                T = np.array([c_[0], 0.5 * (ya + yb), c_[1]]) - R @ np.array([0.0, models[f"{fam}_{kk}"]["roadway_flat_y"], 0.0])
                lp = dims["long_straight" if "long" in k_ else "short_straight"]["lip_up"] * sc
                pieces.append(dict(kind=kk, R=R, T=T, s=sc, st=(st0, st1), flat=(st0 + lp, st1 - lp), pitch=math.degrees(phi)))
        # ---- drop end pieces over roads, platforms or other water
        pieces.sort(key=lambda p: p["st"][0])
        # Earlier kit sites already removed their pond cells. The original
        # footprint must not block a branch with water that no longer exists.
        envv = np.zeros(H.shape, bool); fin = visible & np.isfinite(pl) & np.isfinite(env) & ((pl < planes.min() - 0.05) | (pl > planes.max() + 0.05))
        envo = np.zeros(H.shape, bool); fino = np.isfinite(env) & ((env < planes.min() - 0.05) | (env > planes.max() + 0.05))
        for dr in (0, 1):
            for dc in (0, 1):
                envv[dr:dr + 2047, dc:dc + 2047] |= fin; envo[dr:dr + 2047, dc:dc + 2047] |= fino
        # The route mask already dilates other water by one native ring. Piece
        # clearance must measure from the actual obstacle, not dilate that
        # routing margin a second time (which severed a valid pond junction).
        # The separate envo check below also covers non-visible envelope cells.
        blocked = (frozen_r if mode == "reach" else fz_path) | envv
        trim_why = dict(frozen_or_other_water=0, other_envelope=0, sill=0, earlier_kit=0, kept_water_triangle=0, face_over_road=0)
        trim_log = []
        jsB = []
        if mode == "reach":
            # v10: around a junction target (JUNC_EX of J) the target water, its sills and the partner's lattice do not trim
            # the chain (it is meant to reach them); roads still do, and the kept-height rule keeps the axis margin
            Jc = np.array([j_["J"] for j_ in jinfo.values() if "sB" in j_]).reshape(-1, 2)
            jsB = [j_["sB"] for j_ in jinfo.values() if "sB" in j_]
            if len(Jc):
                jex = np.zeros(H.shape, bool)
                for cx, cz in Jc:
                    c_, r_ = int(round(cx / 6.0)), int(round((ZTOP - cz) / 6.0)); k_ = int(JUNC_EX / 6.0) + 2
                    RR, CC = np.mgrid[max(r_ - k_, 0):min(r_ + k_, 2047) + 1, max(c_ - k_, 0):min(c_ + k_, 2047) + 1]
                    nr_ = np.hypot(6.0 * CC - cx, ZTOP - 6.0 * RR - cz) <= JUNC_EX
                    jex[RR[nr_], CC[nr_]] = True
                blocked = frozen_r | (envv & ~jex)
                envo &= ~jex
                far = lambda Q_: np.min(np.hypot(Q_[:, None, 0] - Jc[None, :, 0], Q_[:, None, 1] - Jc[None, :, 1]), 1) > JUNC_EX
                sill_pts = sill_pts[far(sill_pts)] if len(sill_pts) else sill_pts
                prior = prior[far(prior)] if len(prior) else prior

        road_cache, road_cache_count = None, -1
        def piece_blocked(pc, count=False):
            nonlocal road_cache, road_cache_count
            pts = PLn.at(np.arange(pc["st"][0], pc["st"][1] + 1e-9, 1.0))
            lo_, hi_ = pts.min(0) - 14, pts.max(0) + 14
            ra, rb = max(int((ZTOP - hi_[1]) / 6), 0), int((ZTOP - lo_[1]) / 6) + 1; ca, cb = max(int(lo_[0] / 6), 0), int(hi_[0] / 6) + 1
            tr = cKDTree(pts)
            for name, mask, dist_ in (("frozen_or_other_water", blocked, END_CLEAR), ("other_envelope", envo, RING1 + 0.5)):
                vv = np.argwhere(mask[ra:rb + 1, ca:cb + 1]) + (ra, ca)
                if len(vv) and (tr.query(np.c_[6.0 * vv[:, 1], ZTOP - 6.0 * vv[:, 0]])[0] <= dist_).any():
                    if count:
                        trim_why[name] += 1; trim_log.append([name, round(float(pc["st"][0]), 1), round(float(pc["st"][1]), 1)])
                    return True
            if mode == "reach":
                prec = dict(model=f"dz\\water\\streambed\\streambed_{fam}_{pc['kind']}.p3d",
                            matrix=[*pc["R"][:, 0], *pc["R"][:, 1], *pc["R"][:, 2], *pc["T"]])
                cl = np.vstack([pts, centreline_world(prec, models, 1.0)])
                # The two outer concrete lips are deliberately buried. The
                # consumer checks clearance only inside the wet span; include
                # internal lips/overlaps, but do not reject an end for its cap.
                trial_span = (min(pieces,key=lambda p_:p_["st"][0])["flat"][0],
                              max(pieces,key=lambda p_:p_["st"][1])["flat"][1])
                station = PLn.project(cl)[1]
                cl = cl[(station>=trial_span[0]-1e-6)&(station<=trial_span[1]+1e-6)]
                rr3, cc3, ww3 = tri_weights(cl)
                rr3, cc3 = np.clip(rr3, 0, 2047), np.clip(cc3, 0, 2047)
                # A protected corner contributes only its barycentric weight.
                # Compare the resulting native lower bound with the real highest
                # roadway, including overlaps. Rebuild after every end trim so
                # a removed neighbour cannot supply fictitious clearance.
                if road_cache_count != len(pieces):
                    draft = [dict(model=f"dz\\water\\streambed\\streambed_{fam}_{p_['kind']}.p3d",
                                  matrix=[*p_["R"][:,0],*p_["R"][:,1],*p_["R"][:,2],*p_["T"]]) for p_ in pieces]
                    road_cache = KitSurface(draft, models)
                    road_cache_count = len(pieces)
                fixed_floor = (ww3*np.where(prot_v[rr3,cc3],prot_h[rr3,cc3],LOW_FLOOR)).sum(axis=1)
                road = road_cache.max_height(cl, "road")
                impossible = (np.isfinite(road) & (fixed_floor > road-AXIS_CLEAR)).any()
                # Outside a declared receiving junction retain the original
                # kept-bank exclusion. Clearance of the centre alone does not
                # permit a lateral water sheet over the sealed road-end bank.
                near_join=any(pc['st'][0]-(JUNC_L0+12) <= sb <= pc['st'][1]+(JUNC_L0+12) for sb in jsB)
                if not near_join:
                    bank_limit=min(Yat(pc['st'][0]),Yat(pc['st'][1]))-AXIS_CLEAR
                    impossible |= (prot_v[rr3,cc3] & (prot_h[rr3,cc3]>bank_limit)).any()
                if impossible:
                    if count:
                        trim_why["kept_water_triangle"] += 1; trim_log.append(["kept_water_triangle", round(float(pc["st"][0]), 1), round(float(pc["st"][1]), 1)])
                    return True
                # no face of the piece over a triangle with a reserve/platform/narva/bridge-cut vertex (G11 a)
                g_ = models[f"{fam}_{pc['kind']}"]
                fv = np.vstack([np.array(f["v"], float) for f in g_["road"]] + [np.array(w_, float) for w_ in g_["water"]]) @ pc["R"].T + pc["T"]
                fr_, fc_, _ = tri_weights(fv[:, [0, 2]])
                if frozen_r[np.clip(fr_, 0, 2047), np.clip(fc_, 0, 2047)].any():
                    if count:
                        trim_why["face_over_road"] += 1; trim_log.append(["face_over_road", round(float(pc["st"][0]), 1), round(float(pc["st"][1]), 1)])
                    return True
                for name, Q, dist_ in (("sill", sill_pts, SILL_CLEAR), ("earlier_kit", prior, KK_CLEAR)):
                    if len(Q) and (tr.query(Q)[0] <= dist_).any():
                        if count:
                            trim_why[name] += 1; trim_log.append([name, round(float(pc["st"][0]), 1), round(float(pc["st"][1]), 1)])
                        return True
            return False
        dropped = 0
        while pieces and piece_blocked(pieces[0], True):
            pieces.pop(0); dropped += 1
        while pieces and piece_blocked(pieces[-1], True):
            pieces.pop(); dropped += 1
        if mode == "reach":
            # v9: a blocked piece left in the middle (a road or kept water beside the chain near an end: 6 pieces over road
            # triangles in a dev run of 17-10) is removed with every piece between it and the nearer chain end
            for _ in range(len(pieces)):
                bl = [i for i, pc in enumerate(pieces) if piece_blocked(pc, True)]
                if not bl:
                    break
                i = bl[0]
                if i + 1 <= len(pieces) - i:
                    dropped += i + 1; pieces = pieces[i + 1:]
                else:
                    dropped += len(pieces) - i; pieces = pieces[:i]
        for side, ji in jinfo.items():
            if "sB" not in ji:
                continue
            # v10: the end piece crosses the sill line by at most JUNC_WIN[1]; a corner piece (or straight) overshooting it is
            # dropped when the piece before it still crosses the line by at least JUNC_WIN[0]
            while len(pieces) > 1:
                if side == "dn":
                    lastp = max(pieces, key=lambda p_: p_["st"][1]); rest = [p_ for p_ in pieces if p_ is not lastp]
                    over, nxt = lastp["flat"][1] - ji["sB"], max(p_["flat"][1] for p_ in rest) - ji["sB"]
                else:
                    lastp = min(pieces, key=lambda p_: p_["st"][0]); rest = [p_ for p_ in pieces if p_ is not lastp]
                    over, nxt = ji["sB"] - lastp["flat"][0], ji["sB"] - min(p_["flat"][0] for p_ in rest)
                if over > ji["win"][1] + 1e-6 and nxt >= ji["win"][0] - 1e-6:
                    pieces = rest; ji["overshoot_dropped"] = ji.get("overshoot_dropped", 0) + 1
                else:
                    break
        mid_blocked = sum(piece_blocked(pc) for pc in pieces)
        if not pieces:
            if rcut is not None:
                # no kit: the channel keeps its pond water (the cut is undone)
                rs0, rs1, cs0, cs1 = rcut["win"]
                cover[rs0:rs1, cs0:cs1], env[rs0:rs1, cs0:cs1] = rcut["backup"]
                kept |= body & wet
                report.append(dict(site=site["id"], mode=mode, skipped="no piece left after trimming; channel kept as pond",
                                   end_pieces_dropped=dropped, trimmed_by=trim_why))
            else:
                report.append(dict(site=site["id"], mode=mode, skipped="no piece left after trimming", end_pieces_dropped=dropped))
            continue
        recs = []
        for n_, pc in enumerate(pieces):
            R, T = pc["R"], pc["T"]
            recs.append(dict(site=site["id"], piece=n_, model=f"dz\\water\\streambed\\streambed_{fam}_{pc['kind']}.p3d",
                             matrix=[*R[:, 0].tolist(), *R[:, 1].tolist(), *R[:, 2].tolist(), *T.tolist()], kind=pc["kind"],
                             scale=round(pc["s"], 3), station=[round(pc["st"][0], 3), round(pc["st"][1], 3)], pitch_deg=round(pc["pitch"], 2)))
        first = min(pieces, key=lambda p: p["st"][0]); last = max(pieces, key=lambda p: p["st"][1])
        span = (float(first["flat"][0]), float(last["flat"][1]))
        for side, ji in jinfo.items():
            if "sB" not in ji:
                continue
            fe = span[1] if side == "dn" else span[0]
            ji["flat_end"] = round(fe, 3)
            ji["window_ok"] = bool(ji["sB"] + ji["win"][0] - 1e-6 <= fe <= ji["sB"] + ji["win"][1] + 1e-6) if side == "dn" else \
                bool(ji["sB"] - ji["win"][1] - 1e-6 <= fe <= ji["sB"] - ji["win"][0] + 1e-6)
        # The fitting window is a placement heuristic, not an exclusion rule.
        # Keep every eligible reach; G2-G7/G11 reject any invalid final geometry.
        smin, smax = float(first["st"][0]), float(last["st"][1])
        # joints between consecutive pieces along the stations
        joints = []
        for a_, b_ in zip(pieces[:-1], pieces[1:]):
            joints.append(dict(kinds=[a_["kind"], b_["kind"]], overlap_m=round(a_["st"][1] - b_["st"][0], 3), at=PLn.at([0.5 * (a_["st"][1] + b_["st"][0])])[0].round(2).tolist()))
        # ---------------- terrain
        lo, hi = PLn.at([smin, smax]).min(0), PLn.at([smin, smax]).max(0)
        lo, hi = np.minimum(lo, V.min(0)) - OUTER - 12, np.maximum(hi, V.max(0)) + OUTER + 12
        r0, r1 = int((ZTOP - hi[1]) / 6), int((ZTOP - lo[1]) / 6) + 1; c0, c1 = int(lo[0] / 6), int(hi[0] / 6) + 1
        br, bc_ = np.nonzero(body)
        r0, r1 = max(min(r0, br.min() - 4), 1), min(max(r1, br.max() + 4), 2046)
        c0, c1 = max(min(c0, bc_.min() - 4), 1), min(max(c1, bc_.max() + 4), 2046)
        q, stq = PLn.project_grid(r0, r1, c0, c1, PROJ_RMAX)
        at_end = (stq < smin - 1e-6) | (stq > smax + 1e-6)
        yq = np.interp(np.clip(stq, smin, smax), sL, Y)
        sub = (slice(r0, r1 + 1), slice(c0, c1 + 1))
        prev = (H != H0)[sub]                                     # changed by an earlier site: lower-only from here
        dry_bed = np.zeros(H.shape, bool)
        if mode == "component":
            # ponds out (v7 rule against the lattice polyline), cover and envelope counted separately
            cr, cc2 = np.mgrid[r0:r1, c0:c1]
            Cc = np.c_[6.0 * cc2.ravel() + 3, ZTOP - 6.0 * cr.ravel() - 3]
            cq = np.full(len(Cc), np.inf)
            for i in range(len(V) - 1):
                cq = np.minimum(cq, seg_dist(Cc, V[i], V[i + 1])[0])
            cq = cq.reshape(cr.shape)
            bd = binary_dilation(body, np.ones((3, 3), bool), iterations=2)[r0:r1 + 1, c0:c1 + 1]
            bcell = bd[:-1, :-1] | bd[:-1, 1:] | bd[1:, :-1] | bd[1:, 1:]
            cut_counts = {}; cut_any = np.zeros(cq.shape, bool)
            for name, arr in (("cover", cover), ("envelope", env)):
                blk = arr[r0:r1, c0:c1]
                cut = ((cq <= CUT_Q) | bcell) & np.isfinite(blk) & (blk >= planes.min() - 0.05) & (blk <= planes.max() + 0.05)
                cut_counts[name] = int(cut.sum()); cut_any |= cut
                arr[r0:r1, c0:c1] = np.where(cut, np.nan, blk)
            for dr in (0, 1):
                for dc in (0, 1):
                    dry_bed[r0 + dr:r1 + dr, c0 + dc:c1 + dc] |= cut_any
        else:
            cut_counts = rcut["counts"]
            rs0, rs1, cs0, cs1 = rcut["win"]
            dry_bed[rs0:rs1 + 1, cs0:cs1 + 1] |= c2v(rcut["cut_any"])
        dry_bed &= wet
        sillw = np.zeros(H.shape, bool); sill_tgt = np.full(H.shape, -np.inf)
        if mode == "reach":
            rs0, rs1, cs0, cs1 = rcut["win"]
            sillw[rs0:rs1 + 1, cs0:cs1 + 1] = rcut["sill"]; sill_tgt[rs0:rs1 + 1, cs0:cs1 + 1] = rcut["target"]
        ev = np.isfinite(env[r0 - 1:r1 + 1, c0 - 1:c1 + 1])
        protect = ev[:-1, :-1] | ev[:-1, 1:] | ev[1:, :-1] | ev[1:, 1:]
        h0 = H0[sub]; h = H[sub].copy(); fz = frozen[sub] | protect
        if mode == "reach":
            jr_ = jrim_site[sub] & ~frozen[sub]
            kP_ = c2v_max(np.where(np.isfinite(env), env, -np.inf))[sub]
            h = np.where(jr_ & (h > prot_h[sub]), prot_h[sub], h)
            # v10: the sills take their height before the axis rule (a junction's end piece runs over its sill line; v9 kept the
            # chain SILL_CLEAR off every sill, so raising them afterwards could not reduce a margin)
            h = np.where(sillw[sub] & ~prev, np.maximum(h, sill_tgt[sub]), h)
        ring0 = (q < 0.01) & ~at_end
        seat_in = yq + SEAT0 + SLOPE * np.where(q < 0.01, 0.0, q)
        seat_set = (q <= RING1) & ~at_end & ~fz
        conflicts = int(((q <= RING1) & ~at_end & fz).sum())
        h = np.where(seat_set, seat_in, h)
        outer = (q > RING1) & (q <= OUTER) & ~fz & ~at_end
        cap = yq + np.interp(q, SEAT_OQ, SEAT_OH)
        raise_to = np.minimum(np.maximum(yq + 0.25 + BURY, h), np.maximum(cap, yq + 0.25 + BURY))
        h = np.where(outer & (h < raise_to), raise_to, h)
        endcap = at_end & ~fz & (q <= OUTER)
        h = np.where(endcap & (h < yq + 0.25 + BURY), np.minimum(yq + END_RISE, np.maximum(h, yq + 0.25 + BURY)), h)
        jbank = np.zeros(h.shape, bool)
        if mode == "reach":
            # v10 junction banks: from JUNC_L0 before a pond/bridge sill line to the receiving water (its first kept wet vertex
            # on the path), 2-13 m off the path, the dry vertices of the kept envelope cells (sills and rims; not wet, not
            # frozen) are raised (never lowered) to the burial height yq + 0.25 + BURY (not the seat V: its ring-1 height
            # beside an elbow broke 15 axis margins in a dev run of 18-10), as the cut
            # vertices around them: the lifted sheet (Yj + 0.25) would otherwise show over them across the whole 14 m proxy
            # (12.6 m wide sections at 16.0-0 in a dev run of 18-10). They stay dry buried pond edges (raised, above their
            # plane + SILL_UP); the receiving water is untouched
            for side, ji in jinfo.items():
                if "sB" not in ji or ji["type"] == "kit":
                    continue
                dW = abs(ji["sW"] - ji["sB"])
                zone_j = ((stq >= ji["sB"] - JUNC_L0) & (stq <= ji["sB"] + dW + 1e-6)) if side == "dn" else \
                    ((stq <= ji["sB"] + JUNC_L0) & (stq >= ji["sB"] - dW - 1e-6))
                zone_j &= (q >= 2.0) & (q <= OUTER) & ~at_end
                dry_k = protect & ~near_frozen[sub] & (h >= kP_ + SILL_EXPOSED)
                tgt_j = np.maximum(yq + 0.25 + BURY, np.minimum(raise_to, yq + 0.25 + BURY))   # the burial height, no V (low weight near elbows)
                mj = zone_j & dry_k & (h < tgt_j)
                h = np.where(mj, tgt_j, h); jbank |= mj
            jbank_all[sub] |= jbank
        # axis rule, pits, axis rule
        h_pre = h.copy()
        surf = KitSurface(recs, models)
        AP = axis_samples(recs, PLn, span, models, joints=mode == "reach")
        aw = np.full(len(AP), AXIS_W)
        if jsB:
            # v10: within JUNC_AW_R of a sill line the kept sills and rims cannot move and stand only AXIS_CLEAR + JUNC_SLACK
            # under the roadway, so vertices of any weight >= JUNC_AW may be lowered (3 samples at 0.065 m in a dev run of 18-10)
            stA = PLn.project(AP)[1]
            aw = np.where(np.min(np.abs(stA[:, None] - np.array(jsB)[None, :]), axis=1) <= JUNC_AW_R, JUNC_AW, AXIS_W)
        road = surf.max_height(AP, "road")
        no_road = int(np.isinf(road).sum())
        top = np.where(np.isfinite(road), road - AXIS_CLEAR, np.inf)
        fz_ax = fz & ~jbank; vfl = np.where(jbank, kP_ + SILL_UP, -np.inf) if mode == "reach" else None   # v10: banks may be lowered back
        moved_a, _, _ = axis_rule(h, r0, c0, fz_ax, ring0, AP, top, vfl, aw)
        drain = seat_set | moved_a | fz | seat_all[sub]
        drain[0, :] = drain[-1, :] = True; drain[:, 0] = drain[:, -1] = True
        if mode == "reach":
            drain |= q > PIT_Q                                     # v9 reach mode: pits within PIT_Q of the kit only
        hf = fill_pits(h, dry_bed[sub] & ~drain, drain)
        grow = np.maximum(spill_depth(hf, drain) - spill_depth(h0, drain), 0.0)
        hf = np.where(~drain, hf + grow, hf)
        pits_filled = int((hf > h + 1e-6).sum()); h = hf
        moved_b, unresolved, outside = axis_rule(h, r0, c0, fz_ax, ring0, AP, top, vfl, aw)
        ar_, ac_, _ = tri_weights(AP)
        axis_v[np.clip(ar_, 0, 2047), np.clip(ac_, 0, 2047)] = True
        moved = moved_a | moved_b
        lowered = (h_pre - h)[moved]
        # v9: an earlier site's vertices are only lowered; sills raised to bury's target
        prev_ch = prev & (seat_all[sub] | sill_all[sub] | axis_v[sub])   # an earlier site's channel: lower-only
        prev_raised = int((prev_ch & (h > H[sub] + 1e-9)).sum())
        h = np.where(prev_ch, np.minimum(H[sub], h), h)
        sill_here = sillw[sub] & ~prev
        sill_prev_conflict = int((sillw[sub] & prev).sum())
        h = np.where(sill_here, np.maximum(h, sill_tgt[sub]), h)
        if mode == "reach":
            outside_sills = sillw & ~np.pad(np.ones((r1 - r0 + 1, c1 - c0 + 1), bool), ((r0, 2047 - r1), (c0, 2047 - c1)))
            ok_out = outside_sills & (H == H0)
            H[ok_out] = np.maximum(H[ok_out], sill_tgt[ok_out]); sill_all |= ok_out
        jrim_all |= jrim_site
        H[sub] = h; touched[sub] |= (q <= OUTER) | dry_bed[sub]
        seat_all[sub] |= (seat_set & ~moved & ~prev) | jbank; protect_all[sub] |= protect & ~sill_here; sill_all[sub] |= sill_here
        band_all[sub] |= dist_grid(V, r0, r1, c0, c1, MOUND_Q) <= MOUND_Q
        fl = np.where((q <= OUTER) & (~fz | jbank), yq + 0.25 + BURY, -np.inf)
        floor_all[sub] = np.maximum(floor_all[sub], fl)
        prior_pts.append(PLn.at(np.arange(smin, smax + 1e-9, 0.5)))
        checks.append(dict(site=site["id"], recs=recs, PLn=PLn, span=span, fam=fam, mode=mode, axis_points=AP, axis_road=road, junctions=jinfo,
                           corners=np.array([V[c["at"]] for c in corners]).reshape(-1, 2)))
        built[site["id"]] = dict(PLn=PLn, sL=sL, Y=Y)
        # v8 stone draws, discarded (keep the rng stream of the piece variants identical to v8)
        n8, last_st = 0, -1e9
        marks = sorted([(float(cum[c["at"]]), c) for c in corners], key=lambda t: t[0])
        for st_, cn in marks:
            if st_ < span[0] or st_ > span[1] or st_ - last_st < 18.0:
                continue
            n8 += 1; last_st = st_
        st_ = span[0] + 30.0
        while st_ < span[1] - 10.0:
            if min([abs(st_ - m_) for m_, _ in marks] + [1e9]) > 20.0:
                n8 += 1
            st_ += 60.0
        for _ in range(n8):
            rng.uniform(0, 2 * math.pi); rng.choice(STONES)
        records.extend(recs)
        kinds = {}
        for pc in pieces:
            kinds[pc["kind"]] = kinds.get(pc["kind"], 0) + 1
        dev = cKDTree(P).query(PL)[0]
        report.append(dict(
            site=site["id"], mode=mode, ends=site.get("ends"), extend=site.get("extend"), bridge=site.get("bridge"),
            body_vertices=int(body.sum()), planes=[round(float(planes.min()), 3), round(float(planes.max()), 3)],
            thalweg_m=round(float(s[-1]), 1), lattice_m=round(float(cum[-1]), 1), lattice=V.tolist(),
            plate_span=[round(smin, 3), round(smax, 3)], wet_span=[round(span[0], 3), round(span[1], 3)],
            corners=[dict(at=V[c["at"]].tolist(), type=c["type"], kind=c.get("kind"), scale=c["s"], d_in=c["d_in"], d_out=c["d_out"]) for c in corners],
            curve_ends=curve_ends, curve_end_offset_max_m=max([max(c_["end_offset_m"]) for c_ in curve_ends] or [0.0]),
            heading_m={d: round(sum(float(cum[b] - cum[a]) for dd, a, b in segs if dd == d), 1) for d in DN},
            pieces=len(pieces), kinds=kinds, runs=nfill, run_log=run_log, joints=joints,
            joint_overlap_min_m=round(min([j["overlap_m"] for j in joints] or [0.0]), 3),
            dev_lattice_to_thalweg_p50_p90_max=[round(float(x), 2) for x in np.percentile(dev, [50, 90, 100])],
            roadway=[round(float(Y[0]), 2), round(float(Y[-1]), 2)], ring_vertices_set=int(seat_set.sum()),
            frozen_or_protected_in_ring=conflicts, cover_cells_removed=cut_counts["cover"], envelope_cells_removed=cut_counts["envelope"],
            dry_bed_vertices=int(dry_bed.sum()), pits_filled=pits_filled, end_pieces_dropped=dropped, trimmed_by=trim_why,
            middle_pieces_near_blocked=mid_blocked, trim_log=trim_log[:12],
            axis_samples=len(AP), axis_no_roadway=no_road, axis_outside_window=outside, axis_unresolved_in_window=unresolved,
            axis_moved_vertices=int(moved.sum()), axis_moved_ring0=int((moved & ring0).sum()),
            axis_lowered_p50_p90_max_m=np.percentile(lowered, [50, 90, 100]).round(3).tolist() if len(lowered) else [0, 0, 0],
            axis_moved_ring1=int((moved & (q <= RING1) & (q >= 0.01) & ~at_end).sum()),
            sills=int(sill_here.sum()) + (int(ok_out.sum()) if mode == "reach" else 0), sill_frozen=rcut["sill_frozen"] if rcut else 0,
            sill_conflict_earlier_site=sill_prev_conflict, earlier_site_raise_refused=prev_raised,
            kept_cells_touching_body=rcut["kept_cells_touching_body"] if rcut else None,
            junctions=jinfo if mode == "reach" else None, stem_stations=[round(x, 3) for x in s_stem] if mode == "reach" else None))
    # v9 mound pass inside the bands, before the slope guard
    print(f"[{time.time() - t_start:7.1f} s] mounds", file=sys.stderr, flush=True)
    pr0 = prominence(H0)
    kept_v = c2v(np.isfinite(env))                                  # vertices of the envelope cells left at the end
    keptP_all = c2v_max(np.where(np.isfinite(env), env, -np.inf))
    movable_m = ~frozen & ~kept_v & ~seat_all & ~sill_all
    # v10: kept dry rims (>= their plane + RIM_CLEAR) may be laid too, never below plane + RIM_CLEAR; seat shapes apart
    rim_m = kept_v & ~frozen & ~seat_all & ~sill_all & (H >= keptP_all + RIM_CLEAR)
    movable_m = movable_m | rim_m
    floor_m = np.maximum(floor_all, np.where(rim_m, keptP_all + RIM_CLEAR, -np.inf))
    seat_m = seat_all & ~frozen & ~kept_v & ~sill_all
    rec_zone = np.zeros(H.shape, bool)
    RR_, CC_ = np.mgrid[0:H.shape[0], 0:H.shape[1]]
    for rec in records:
        x_, z_ = rec["matrix"][9], rec["matrix"][11]; c_, r_ = int(x_ // 6), int((ZTOP - z_) // 6); k_ = int(ZONE_REC_R // 6) + 2
        sl_ = (slice(max(r_ - k_, 0), r_ + k_ + 1), slice(max(c_ - k_, 0), c_ + k_ + 1))
        rec_zone[sl_] |= np.hypot(6.0 * CC_[sl_] - x_, ZTOP - 6.0 * RR_[sl_] - z_) < ZONE_REC_R
    del RR_, CC_

    def zone_of(Hc):
        return band_all | rec_zone | binary_dilation(Hc != H0, np.ones((3, 3), bool), iterations=ZONE_DIL)

    def lay_all(Hc, zone):
        """mound_pass then seat_shapes until the zone stops growing (lowering widens v31_kit, hence despike's exclusion)."""
        tot = dict(rounds=0, shapes_laid=0, shapes_with_unmovable_vertex=0, seat_shapes_laid=0, seat_shapes_left=0, lowered=np.zeros(H.shape, bool))
        for _ in range(ZONE_ROUNDS):
            Hm_, low_, _, laid_, blk_ = mound_pass(Hc, zone, movable_m, floor_m)
            Hs_, slow_, slaid_, sleft_ = seat_shapes(Hm_, zone, seat_m, movable_m, floor_m)
            tot["rounds"] += 1; tot["shapes_laid"] += laid_; tot["shapes_with_unmovable_vertex"] = blk_
            tot["seat_shapes_laid"] += slaid_; tot["seat_shapes_left"] = sleft_; tot["lowered"] |= low_ | slow_
            Hc = Hs_
            z2 = zone_of(Hc)
            if not (z2 & ~zone).any():
                break
            zone = z2
        return Hc, zone, tot
    mound = dict(enabled=mounds_on, band_vertices=int(band_all.sum()),
                 band_prominent_gt_0p30_before=int((band_all & (pr0 > 0.30)).sum()))
    zone_m = band_all
    if mounds_on:
        Hm, zone_m, tot = lay_all(H, zone_of(H))
        lowered_m = tot.pop("lowered")
        mound.update(tot, zone_vertices=int(zone_m.sum()), lowered_vertices=int(lowered_m.sum()),
                     lowered_p50_p90_max_m=np.percentile((H - Hm)[lowered_m], [50, 90, 100]).round(3).tolist() if lowered_m.any() else [0, 0, 0])
        H = Hm; touched |= lowered_m
    # v9: stray patches of the sheets (reach sites), before the slope guard
    kept_vm = c2v(np.isfinite(env))
    mov_s = ~frozen & ~kept_vm & ~seat_all & ~sill_all & ~axis_v
    stray_raised, stray_left = 0, 0
    for ck in checks:
        if ck["mode"] != "reach":
            continue
        ks_ = KitSurface(ck["recs"], models)
        for _ in range(2):
            r_, l_ = bury_strays(H, ck["recs"], models, ks_, mov_s, floor_all)
            stray_raised += r_
            if not r_:
                break
        stray_left += l_
    touched |= (H != H0) & mov_s
    # slope guard
    print(f"[{time.time() - t_start:7.1f} s] slope guard", file=sys.stderr, flush=True)
    # v9: the guard may also lower the native neighbours of the touched vertices (a lowered outer vertex steepened the
    # triangle to an untouched vertex at q 13.4 m: 20 stuck triangles up to 55 deg in a dev run of 17-10)
    reach_ = touched.copy()
    for dr, dc in NATIVE:
        reach_ |= shifted(touched, dr, dc, False)
    keptP = c2v_max(np.where(np.isfinite(env), env, -np.inf))     # highest kept plane at each vertex
    rim = kept_v & (H >= keptP + SILL_UP + 0.1) & reach_ & ~seat_all & ~frozen & ~sill_all
    floor_all = np.where(rim, np.maximum(floor_all, keptP + SILL_UP), floor_all)
    s0 = tri_slopes(H0); movable = reach_ & ~seat_all & ~frozen & (~kept_v | rim) & ~sill_all
    wall_lowered = 0; wall_lifted = 0; wall_stuck = set(); why_stuck = {}
    for _ in range(WALL_STEPS):
        s1 = tri_slopes(H); ch = H != H0; worst = np.zeros(H.shape, bool); lift = np.zeros(H.shape, bool)
        for (a0, a1), cor in zip(zip(s0, s1), (((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 1), (1, 0)))):
            chc = np.zeros(a0.shape, bool)
            for dr, dc in cor:
                chc |= ch[dr:dr + 2047, dc:dc + 2047]
            bad = chc & (a1 > np.maximum(35.0, a0) + 1e-4)
            for r, c in np.argwhere(bad):
                top_v = max(((r + dr, c + dc) for dr, dc in cor), key=lambda v: H[v])
                low_v = min(((r + dr, c + dc) for dr, dc in cor), key=lambda v: H[v])
                if movable[top_v] and H[top_v] - 0.1 >= max(LOW_FLOOR, floor_all[top_v]):
                    worst[top_v] = True
                elif movable[low_v] and not axis_v[low_v] and (not kept_v[low_v] or sill_all[low_v] or jbank_all[low_v]):
                    lift[low_v] = True                                  # v9: the top cannot move (kept rim): fill the foot
                else:
                    wall_stuck.add((int(r), int(c)))
                    why_stuck[(int(r), int(c))] = ("frozen" if frozen[top_v] else "kept" if kept_v[top_v] else "seat" if seat_all[top_v]
                                                   else "sill" if sill_all[top_v] else "untouched" if not touched[top_v] else "floor")
        lift &= ~worst
        if not worst.any() and not lift.any():
            break
        H = np.where(worst, H - 0.1, np.where(lift, H + 0.1, H)); wall_lowered += int(worst.sum()); wall_lifted += int(lift.sum())
    if mounds_on:
        # the guard lowers banks and can leave a vertex standing above them (dev run of 17-10: one new 0.42 m pyramid beside
        # 41.1-0): the shapes are laid once more (lower-only, so no triangle gets steeper)
        rim_m &= H >= keptP_all + RIM_CLEAR
        movable_m = (~frozen & ~kept_v & ~seat_all & ~sill_all) | rim_m
        # bury_strays updates floor_all after the first mound pass. Rebuild this
        # derived floor here so the second pass cannot uncover those water faces.
        floor_m = np.maximum(floor_all, np.where(rim_m, keptP_all + RIM_CLEAR, -np.inf))
        Hm, zone_m, tot2 = lay_all(H, zone_of(H))
        lowered2 = tot2.pop("lowered")
        mound.update(after_slope_guard=dict(tot2, lowered_vertices=int(lowered2.sum()), zone_vertices=int(zone_m.sum())))
        H = Hm
    bank_caps = close_bank_caps(H,H0,checks,models,jbank_all,frozen_r,keptP_all)
    bank_grade = grade_junction_banks(H,H0,checks,models,frozen_r,keptP_all,jbank_all,env)
    bank_caps += close_bank_caps(H,H0,checks,models,jbank_all,frozen_r,keptP_all)
    H32 = H.astype(np.float32)
    pr1 = prominence(H32.astype(np.float64))
    mound.update(band_prominent_gt_0p30_after=int((band_all & (pr1 > 0.30)).sum()),
                 band_prominent_gt_0p30_after_movable=int((band_all & movable_m & (pr1 > 0.30)).sum()),
                 map_prominent_gt_0p30_before_after=[int((pr0[1:-1, 1:-1] > 0.30).sum()), int((pr1[1:-1, 1:-1] > 0.30).sum())])
    # final axis check on the stored (float32) terrain, then the v9 stones on it
    Hc = H32.astype(np.float64)
    tri_frozen = v2c(frozen)
    remw = np.isfinite(env)

    def frozen_tri(P_):
        c_ = np.clip((P_[:, 0] / 6.0).astype(int), 0, 2046); r_ = np.clip(((ZTOP - P_[:, 1]) / 6.0).astype(int), 0, 2046)
        return tri_frozen[r_, c_]

    def pond_wet(P_):
        c_ = np.clip((P_[:, 0] / 6.0).astype(int), 0, 2046); r_ = np.clip(((ZTOP - P_[:, 1]) / 6.0).astype(int), 0, 2046)
        plv = np.where(remw[r_, c_], env[r_, c_], -np.inf)
        return plv > tri_h(Hc, P_[:, 0], P_[:, 1])
    taken, stone_log = [], {}
    stone_recs = []
    ks_all = KitSurface([r_ for r_ in records if r_["piece"] != "stones"], models)
    ribbon_tree = cKDTree(np.vstack([centreline_world(r_,models,.25) for r_ in records if r_["piece"] != "stones"]))
    print(f"[{time.time() - t_start:7.1f} s] final checks and stones", file=sys.stderr, flush=True)
    for ck, rep in zip(checks, [r for r in report if "skipped" not in r]):
        AP = axis_samples(ck["recs"], ck["PLn"], ck["span"], models, joints=ck["mode"] == "reach")
        ks = KitSurface(ck["recs"], models)
        road = ks.max_height(AP, "road")
        mg = road - tri_h(Hc, AP[:, 0], AP[:, 1])
        mg_ext = ks.max_height(AP, "road_ext") - tri_h(Hc, AP[:, 0], AP[:, 1])
        rep.update(final_axis_below_xz=AP[mg < AXIS_MIN][:6].round(2).tolist(), final_axis_margin_min=round(float(mg.min()), 4),
                   final_axis_samples=len(AP),
                   final_axis_below_min=int((mg < AXIS_MIN).sum()), final_axis_no_roadway=int(np.isinf(road).sum()),
                   final_axis_water_ext_share=round(float((mg_ext >= AXIS_MIN).mean()), 4))
        st_recs, lg = place_stones(ck["site"], ck["fam"], ck["recs"], ck["PLn"], ck["span"], ck["corners"], Hc, ks_all, sgeo, rng_st,
                                   frozen_tri, pond_wet, taken, models, ribbon_tree)
        rep["stones"] = lg; stone_recs.extend(st_recs)
        if st_recs:
            rep["stones"].update(q_p50=round(float(np.median([r_["q"] for r_ in st_recs])), 3))
    records.extend(stone_recs)
    assert not ((H32 != arrays["heights"]) & frozen).any()
    remv = c2v(np.isfinite(env))
    kch = (H32 != arrays["heights"]) & remv
    assert not (kch & ~(H32 >= c2v_max(np.where(np.isfinite(env), env, -np.inf)).astype(np.float32) + np.float32(SILL_UP - 1e-3))).any(), \
        "a kept envelope vertex changed below its plane + SILL_UP"
    assert not (kch & ~sill_all & ~jbank_all & (H32 > arrays["heights"])).any(), \
        "a kept envelope vertex was raised outside the sills and junction banks"
    arrays["heights"] = H32; arrays["v31_kit"] = H32 != z["heights"]
    np.savez(out_t, **arrays); np.save(out_c, cover.astype(np.float32)); np.save(out_e, env.astype(np.float32))
    with open(rec_path, "w", newline="\n") as f:
        json.dump(records, f, indent=1)
    done_sites = [r for r in report if "skipped" not in r]
    counts = dict(sites=len(sites), sites_built=len(done_sites), sites_skipped=len(report) - len(done_sites),
                  pieces=sum(1 for r_ in records if r_["piece"] != "stones"), stones=len(stone_recs),
                  objects=len(records), lattice_km=round(sum(r_["lattice_m"] for r_ in done_sites) / 1000, 2),
                  wet_span_km=round(sum(r_["wet_span"][1] - r_["wet_span"][0] for r_ in done_sites) / 1000, 2))
    rep = dict(schema="streambed-kit-v31.v9", geometry=str(GEOM_PATH.name), stones_geometry=str(STONES_GEOM_PATH.name),
               params=dict(LAMBDA=LAMBDA, SIGMA=SIGMA, DMAX=DMAX, TURN_COST=TURN_COST, MIN_RUN={f"{a}->{b}": v for (a, b), v in MIN_RUN.items()},
                           CURVE_S=CURVE_S, SLANT_S=SLANT_S, S_RANGE=[S_MIN, S_MAX], OV_FLOOR=OV_FLOOR, DIP_SPAN=DIP_SPAN, OV_MAX=OV_MAX,
                           DIRECT_MAX=DIRECT_MAX, SEAT0=SEAT0, HW=HW, SLOPE=SLOPE, RING1=RING1, OUTER=OUTER, BURY=BURY, END_RISE=END_RISE,
                           SEAT_OQ=SEAT_OQ, SEAT_OH=SEAT_OH, NEED6=NEED6, BED_MIN=BED_MIN, CUT_Q=CUT_Q, END_CLEAR=END_CLEAR,
                           AXIS_STEP=AXIS_STEP, AXIS_CLEAR=AXIS_CLEAR, AXIS_MIN=AXIS_MIN, AXIS_W=AXIS_W,
                           STONES_PER_KM=STONES_PER_KM, STONE_SINK=STONE_SINK, STONE_BLOCK=STONE_BLOCK, STONE_RIBBON=STONE_RIBBON,
                           STONE_GAP=STONE_GAP, STONE_Q_EXTRA=STONE_Q_EXTRA, STONE_BANDS=STONE_BANDS, STONE_VIS_MIN=STONE_VIS_MIN, SILL_UP=SILL_UP,
                           SILL_EXPOSED=SILL_EXPOSED, SILL_CLEAR=SILL_CLEAR, KK_CLEAR=KK_CLEAR, MOUND_Q=MOUND_Q, MOUND_T=MOUND_T, MOUND_RING=MOUND_RING,
                           MOUND_FLOOR=MOUND_FLOOR, MOUND_PASSES=MOUND_PASSES),
               counts=counts, mounds=mound, bank_caps=bank_caps, bank_grade=bank_grade, stray_patches=dict(vertices_raised=stray_raised, pixels_without_movable_vertex=stray_left), sites=report, changed_vertices=int(arrays["v31_kit"].sum()), sill_vertices=int(sill_all.sum()), junction_bank_vertices=int(jbank_all.sum()), junction_rims_lowered=int(jrim_all.sum()),
               wall_lowering_steps=wall_lowered, wall_lifting_steps=wall_lifted, wall_stuck_triangles=len(wall_stuck),
               wall_stuck_why={k: sum(1 for v in why_stuck.values() if v == k) for k in sorted(set(why_stuck.values()))},
               wall_stuck_xz=[[6 * c + 3, round(ZTOP - 6 * r - 3, 1), why_stuck.get((r, c))] for r, c in sorted(wall_stuck)[:30]])
    with open(rep_path, "w", newline="\n") as f:
        json.dump(rep, f, indent=1, default=float)
    print(json.dumps(dict(counts=counts, mounds=mound, sites=[{k: v for k, v in r.items() if k in (
        "site", "mode", "skipped", "pieces", "ends", "final_axis_below_min", "final_axis_no_roadway", "sills", "stones", "trimmed_by",
        "frozen_or_protected_in_ring", "middle_pieces_near_blocked")} for r in report]), indent=1, default=float))


if __name__ == "__main__":
    main()
