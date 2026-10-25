"""G7: server probe points for the new records, checked independently of the generator. Runs probe_points_kit.py (worktree
tools/water by default, or --tools dir) as in HANDOFF step 7 on the kit run after the bury pass: <run>/bury-work/fpN (last)/
footprint.npz, <run>/terrain-ev108.npz, lagoons-report.json, <run>/kit-records.json, bridges/terrain-ev107.npz,
bridges/fp-ev107/footprint.npz. Then, with gatelib's own face transform, point-in-triangle and terrain interpolation (no code
of the generator), every exported point is recomputed at the coordinates written to points.json AND points.csv:
  csv       same rows, ids and x/z (1e-5 m) as points.json;
  coverage  every non-stones record: 3 kit_axis + 2 lateral controls (kit_side or validated kit_confluence); every joint:
            1 kit_joint + 1 kit_lip per piece; every piece kind of the records has axis, lip and joint points;
  identity  site/piece exist, piece_kind = the record's model, scale = |matrix Y column| (1e-3);
  membership kit_axis inside that piece's water_ext faces and on its centreline (<= 0.02 m); kit_lip inside that piece's
            concrete_ext faces, on its centreline, at the declared end; kit_joint inside the roadway faces of both pieces;
  heights   ground (terrain-ev108 on the native triangle), roadway (highest roadway face of all pieces), water_ext (highest
            water_ext face or None) and expect recomputed and equal (1e-3 m); roadway - ground >= 0.10 for axis/lip/joint;
            kit_axis expect 'wet';
  side      kit_side/kit_confluence 6 m (0.01) from its kit_axis point, perpendicular (|cos| <= 0.01) to its centreline, on the
            declared side of the downstream direction; kit_joint_side at its declared distance (6/8/10) from its kit_joint,
            perpendicular to the lip-to-lip line, one per side at most;
  dry       every dry control, selected by KIND (kit_side, kit_joint_side, old_bed), must carry expect = 'dry' and have no
            kit water-proxy face above the ground there (review 2 of 15-10: relabelling them 'test' or dropping 'expect'
            skipped the check); every comparison with a declared value is fail-closed on non-finite values;
  old_bed   on a grid vertex; plane = the EV107 vertex plane (recomputed), EV107 terrain below it; ground = the new terrain;
            farther than 6 m from every piece's continuous centreline; not under the visible water of the given footprint;
            (EV112) it names a built site and lies in that site's body (reach sites: the sites file's body list; component
            sites: the EV107 wet component at the seed); at least one per site unless the gate itself finds no eligible
            vertex for that site (body vertices wet in EV107, > 6 m from every centreline, under no kit sheet and no pond
            water of the given footprint): a reach whose old bed lies within 6 m of the new centreline has no control by
            construction, and the gate prints those sites.
Pass: exit 0 and every check holds. Usage: gate_g7_probe.py [run_dir] [--tools dir] [--sites sites.json]   (default sites:
the EV112 chain's, gatelib.CHAIN)"""
import glob, json, os, subprocess, sys
from collections import Counter, defaultdict
import numpy as np
sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as G
from probe_confluence_contract import validate as validate_confluences
DRY_KINDS = ("kit_side", "kit_joint_side", "old_bed")
PIECE_SIDE_KINDS = ("kit_side", "kit_confluence")
args = sys.argv[1:]
tools = G.WT + "/tools/water"
if "--tools" in args:
    i = args.index("--tools"); tools = args[i + 1]; args = args[:i] + args[i + 2:]
spath = None
if "--sites" in args:
    i = args.index("--sites"); spath = args[i + 1]; args = args[:i] + args[i + 2:]
if spath is None:
    spath = G.chain()["args"][5]
spath = spath if os.path.isabs(spath) else G.B + "/" + spath
run = args[0] if args else G.OUT
fps = sorted(glob.glob(run + "/bury-work/fp*/footprint.npz"), key=lambda p: int(p.replace("\\", "/").split("/fp")[-1].split("/")[0]))
out_dir = run + "/probe"; os.makedirs(out_dir, exist_ok=True)
cmd = [sys.executable, "-I", tools + "/probe_points_kit.py", fps[-1], run + "/terrain-ev108.npz", G.B + "/lagoons-report.json",
       run + "/kit-records.json", G.B + "/bridges/terrain-ev107.npz", G.B + "/bridges/fp-ev107/footprint.npz",
       out_dir + "/points.csv", out_dir + "/points.json", spath]
pr = subprocess.run(cmd, capture_output=True, text=True)
res = dict(cmd=" ".join(cmd), exit=pr.returncode, stdout=pr.stdout[-600:], stderr=pr.stderr[-800:])
fails = defaultdict(list)


def fail(check, *info):
    fails[check].append(info)


def seg_dist(W, q):
    a, b = W[:-1], W[1:]; ab = b - a; t = np.clip(((q - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-12), 0, 1)
    d = np.linalg.norm(q - (a + t[:, None] * ab), axis=1); k = int(np.argmin(d))
    return float(d[k]), ab[k] / np.linalg.norm(ab[k])


def tri_any(tris, q):
    o = np.full(1, -np.inf); G.tri_max(tris, np.asarray(q, float).reshape(1, 2), o); return o[0]


def vplane(path):
    pl = np.load(path)["plane"].astype(float); n = pl.shape[0]
    vp = np.full((n + 1, n + 1), -np.inf); cp = np.where(np.isfinite(pl), pl, -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            vp[dr:dr + n, dc:dc + n] = np.maximum(vp[dr:dr + n, dc:dc + n], cp)
    return vp


if pr.returncode == 0:
    pts = json.load(open(out_dir + "/points.json.full.json"))
    rows = [l.split(";") for l in open(out_dir + "/points.csv.full.csv").read().splitlines() if l]
    runtime = json.load(open(out_dir + "/points.json"))
    rt_rows = [l.split(";") for l in open(out_dir + "/points.csv").read().splitlines() if l]
    full_by_id = {p["id"]:p for p in pts}; rt_ids = {p["id"] for p in runtime}
    if not 0 < len(runtime) <= 3000 or len(rt_ids) != len(runtime):
        fail("runtime_budget_or_unique_ids", len(runtime), len(rt_ids))
    if len(rt_rows) != len(runtime):
        fail("runtime_csv_count", len(rt_rows), len(runtime))
    for p, row in zip(runtime,rt_rows):
        if full_by_id.get(p["id"]) != p:
            fail("runtime_changed_or_unknown_point", p["id"])
        xyz = row[1].split()
        if int(row[0]) != p["id"] or abs(float(xyz[0])-p["x"]) > 1e-5 or abs(float(xyz[2])-p["z"]) > 1e-5:
            fail("runtime_csv",p["id"])
        if any(ref not in rt_ids for ref in p.get("lips",[])) or ("of" in p and p["of"] not in rt_ids):
            fail("runtime_reference_closure",p["id"])
    res["runtime_points"] = len(runtime)
    if len(rows) != len(pts):
        fail("csv_rows", len(rows), len(pts))
    for i, (row, p) in enumerate(zip(rows, pts)):
        xyz = row[1].split()
        if not (int(row[0]) == p["id"] == i and abs(float(xyz[0]) - p["x"]) <= 1e-5 and abs(float(xyz[2]) - p["z"]) <= 1e-5
                and np.isfinite([p["x"], p["z"]]).all()):
            fail("csv_match", i)
    models = json.load(open(G.GEOM))["models"]
    recs = [r for r in json.load(open(run + "/kit-records.json")) if r["piece"] != "stones"]
    pieces = {(r["site"], r["piece"]): G.Piece(r, models) for r in recs}
    allp = list(pieces.values())
    Hn = np.load(run + "/terrain-ev108.npz")["heights"].astype(np.float64)
    for p in pieces.values():
        p.W = p.world(p.centre_model)[:, [0, 2]]
        p.conc = p.road[~p.road_ext]; p.ext = p.road[p.road_ext]
    for error in validate_confluences(pts,pieces,json.load(open(spath)),Hn,runtime):
        fail(*error)
    byid = {p["id"]: p for p in pts}
    kitk = [p for p in pts if p["kind"] in ("kit_axis", "kit_lip", "kit_joint")]
    Q = np.array([[p["x"], p["z"]] for p in kitk]).reshape(-1, 2)
    road = G.surface(allp, Q, "road"); ext = G.surface(allp, Q, "road_ext"); ground = G.terrain_y(Hn, Q[:, 0], Q[:, 1])
    for k, p in enumerate(kitk):
        q = Q[k]
        names = [p["piece"]] if "piece" in p else p["pieces"]
        kinds = [p["piece_kind"]] if "piece_kind" in p else p["piece_kinds"]
        scales = [p["scale"]] if "scale" in p else p["scales"]
        pcs = [pieces.get((p["site"], n)) for n in names]
        if any(pc is None for pc in pcs):
            fail("identity_piece", p["id"]); continue
        for pc, kd, sc in zip(pcs, kinds, scales):
            if pc.kind != kd or abs(pc.scale - sc) > 1e-3:
                fail("identity_kind_scale", p["id"], kd, pc.kind, sc, round(pc.scale, 4))
        if p["kind"] == "kit_axis":
            pc = pcs[0]
            if not np.isfinite(tri_any(pc.ext, q)):
                fail("member_axis_water_ext", p["id"])
            if seg_dist(pc.W, q)[0] > 0.02:
                fail("member_axis_centreline", p["id"], round(seg_dist(pc.W, q)[0], 3))
            if p["expect"] != "wet":
                fail("axis_not_wet", p["id"])
        elif p["kind"] == "kit_lip":
            pc = pcs[0]
            if not np.isfinite(tri_any(pc.conc, q)):
                fail("member_lip_concrete", p["id"])
            if seg_dist(pc.W, q)[0] > 0.02:
                fail("member_lip_centreline", p["id"])
            end = "downstream" if np.linalg.norm(q - pc.W[0]) < np.linalg.norm(q - pc.W[-1]) else "upstream"
            if end != p["end"]:
                fail("member_lip_end", p["id"], p["end"], end)
        else:
            for pc in pcs:
                if not np.isfinite(tri_any(pc.road, q)):
                    fail("member_joint_roadway", p["id"], pc.rec["piece"])
        if not abs(ground[k] - p["ground"]) <= 1e-3:
            fail("ground", p["id"], p["ground"], float(ground[k]))
        if not (np.isfinite(road[k]) and abs(road[k] - p["roadway"]) <= 1e-3):
            fail("roadway", p["id"], p["roadway"], float(road[k]))
        if (p["water_ext"] is None) != (not np.isfinite(ext[k])) or (p["water_ext"] is not None and not abs(ext[k] - p["water_ext"]) <= 1e-3):
            fail("water_ext", p["id"], p["water_ext"], float(ext[k]))
        if p["expect"] != ("wet" if ext[k] - ground[k] >= 0.10 else "test"):
            fail("expect", p["id"], p["expect"])
        if not (road[k] - ground[k] >= 0.10):
            fail("margin", p["id"], float(road[k] - ground[k]))
    # coverage
    ax = Counter((p["site"], p["piece"]) for p in pts if p["kind"] == "kit_axis")
    sd = defaultdict(set)
    for p in pts:
        if p["kind"] in PIECE_SIDE_KINDS:
            sd[(p["site"], p["piece"])].add(p["side"])
    lips = Counter((p["site"], p["piece"], p["joint_with"]) for p in pts if p["kind"] == "kit_lip")
    joints = Counter((p["site"], tuple(p["pieces"])) for p in pts if p["kind"] == "kit_joint")
    n_joints = 0
    for key in pieces:
        if ax[key] != 3:
            fail("coverage_axis", key, ax[key])
        if sd[key] != {-1, 1} or sum(1 for p in pts if p["kind"] in PIECE_SIDE_KINDS and (p["site"], p["piece"]) == key) != 2:
            fail("coverage_side", key)
    for sid in sorted({k[0] for k in pieces}):
        L = sorted([pc for k, pc in pieces.items() if k[0] == sid], key=lambda pc: pc.rec["station"][0])
        for a, b in zip(L[:-1], L[1:]):
            n_joints += 1; na, nb = a.rec["piece"], b.rec["piece"]
            if joints[(sid, (na, nb))] != 1 or lips[(sid, na, nb)] != 1 or lips[(sid, nb, na)] != 1:
                fail("coverage_joint", sid, na, nb)
    rec_kinds = Counter(pc.kind for pc in allp)
    for sid in sorted({k[0] for k in pieces}):
        ordered = sorted([pc for k,pc in pieces.items() if k[0]==sid],key=lambda pc:pc.rec["station"][0])
        sampled = [p for p in runtime if p.get("site")==sid and p["kind"]=="kit_axis"]
        covered = {p["piece"] for p in sampled}
        required = {ordered[i].rec["piece"] for i in {0,len(ordered)//2,len(ordered)-1}}
        if not required <= covered or {pc.kind for pc in ordered} - {p["piece_kind"] for p in sampled}:
            fail("runtime_reach_strata",sid)
        steepest = max(ordered,key=lambda pc:abs(pc.rec["matrix"][7])/max(np.linalg.norm(pc.rec["matrix"][6:9]),1e-12))
        if steepest.rec["piece"] not in covered:
            fail("runtime_max_grade_piece",sid)
        allj = sorted([p for p in pts if p["kind"]=="kit_joint" and p.get("site")==sid],key=lambda p:p["id"])
        if allj and not {allj[i]["id"] for i in {0,len(allj)//2,len(allj)-1}} <= rt_ids:
            fail("runtime_joint_strata",sid)
        if any(p["kind"]=="old_bed" and p.get("site")==sid for p in pts) and not any(p["kind"]=="old_bed" and p.get("site")==sid for p in runtime):
            fail("runtime_old_bed",sid)
    for kd in rec_kinds:
        for kk, have in (("kit_axis", [p["piece_kind"] for p in pts if p["kind"] == "kit_axis"]),
                         ("kit_lip", [p["piece_kind"] for p in pts if p["kind"] == "kit_lip"]),
                         ("kit_joint", [k_ for p in pts if p["kind"] == "kit_joint" for k_ in p["piece_kinds"]])):
            if kd not in have:
                fail("coverage_kind", kd, kk)
    # side points
    seen = defaultdict(set)
    for p in pts:
        if p["kind"] not in (*PIECE_SIDE_KINDS, "kit_joint_side"):
            continue
        o = byid.get(p["of"]); q = np.array([p["x"], p["z"]])
        if p["kind"] in PIECE_SIDE_KINDS:
            if not o or o["kind"] != "kit_axis" or (o["site"], o["piece"]) != (p["site"], p["piece"]):
                fail("side_ref", p["id"]); continue
            c = np.array([o["x"], o["z"]]); pc = pieces[(p["site"], p["piece"])]
            if p.get("piece_kind") != pc.kind or not abs(p.get("scale",float("nan"))-pc.scale)<=1e-3:
                fail("side_identity",p["id"])
            _, up = seg_dist(pc.W, c); down = -up; dist = 6.0
        else:
            if not o or o["kind"] != "kit_joint" or o["pieces"] != p["pieces"]:
                fail("side_ref", p["id"]); continue
            c = np.array([o["x"], o["z"]]); la, lb = byid[o["lips"][0]], byid[o["lips"][1]]
            down = np.array([lb["x"] - la["x"], lb["z"] - la["z"]]); down /= np.linalg.norm(down); dist = p["distance"]
            if dist not in (6.0, 8.0, 10.0):
                fail("side_distance", p["id"], dist)
        v = q - c
        if abs(np.linalg.norm(v) - dist) > 0.01:
            fail("side_distance", p["id"], round(float(np.linalg.norm(v)), 3))
        if abs(v @ down) / max(np.linalg.norm(v), 1e-9) > 0.01:
            fail("side_perpendicular", p["id"])
        left = np.array([-down[1], down[0]])
        if (v @ left > 0) != (p["side"] == -1):
            fail("side_sign", p["id"], p["side"])
        if p["side"] in seen[p["of"]]:
            fail("side_duplicate", p["id"])
        seen[p["of"]].add(p["side"])
    # dry controls and old bed
    dry = [p for p in pts if p["kind"] in DRY_KINDS]
    for p in dry:
        if p.get("expect") != "dry":
            fail("dry_label", p["id"], p["kind"], p.get("expect"))
    for p in pts:
        if p["kind"].startswith("kit_") and p["kind"] not in DRY_KINDS and p.get("expect") not in ("wet", "test"):
            fail("kit_label", p["id"], p["kind"], p.get("expect"))
    D = np.array([[p["x"], p["z"]] for p in dry]).reshape(-1, 2)
    wat = G.surface(allp, D, "water"); gD = G.terrain_y(Hn, D[:, 0], D[:, 1])
    for k, p in enumerate(dry):
        if wat[k] > gD[k] or not np.isfinite(gD[k]):
            fail("dry_in_kit_sheet", p["id"], p["kind"], round(float(wat[k] - gD[k]), 3))
        if not abs(gD[k] - p.get("ground", float("nan"))) <= 1e-3:
            fail("dry_ground", p["id"], p["ground"], float(gD[k]))
    H7 = np.load(G.B + "/bridges/terrain-ev107.npz")["heights"].astype(float); vp7 = vplane(G.B + "/bridges/fp-ev107/footprint.npz")
    vpn = vplane(fps[-1])
    segs = np.vstack([np.c_[pc.W[:-1], pc.W[1:]] for pc in allp])
    old = [p for p in pts if p["kind"] == "old_bed"]
    for p in old:
        c, r = p["x"] / 6.0, (G.ZTOP - p["z"]) / 6.0
        if abs(c - round(c)) > 1e-9 or abs(r - round(r)) > 1e-9:
            fail("old_vertex", p["id"]); continue
        r, c = int(round(r)), int(round(c)); q = np.array([p["x"], p["z"]])
        if not (np.isfinite(vp7[r, c]) and abs(vp7[r, c] - p["plane"]) <= 1e-4 and H7[r, c] < vp7[r, c]):
            fail("old_ev107_plane", p["id"])
        if np.isfinite(vpn[r, c]) and Hn[r, c] < vpn[r, c]:
            fail("old_in_new_pond", p["id"])
        a, b = segs[:, :2], segs[:, 2:]; ab = b - a
        t = np.clip(((q - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-12), 0, 1)
        dmin = float(np.linalg.norm(q - (a + t[:, None] * ab), axis=1).min())
        if dmin <= 6.0:
            fail("old_near_axis", p["id"], round(dmin, 3))
    # EV112: membership in the named site's body and at least one per site where an eligible vertex exists
    from scipy.ndimage import label as _label
    sites_ = {x["id"]: x for x in json.load(open(spath))}
    wet7 = np.isfinite(vp7) & (H7 < vp7)
    lab7, _ = _label(wet7, np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]]))
    built = sorted({k[0] for k in pieces})
    members = {}
    for sid in built:
        st = sites_.get(sid)
        if st is None:
            fail("old_site_unknown", sid); continue
        if "body" in st:
            b = np.array(st["body"], int).reshape(-1, 2); members[sid] = b[wet7[b[:, 0], b[:, 1]]]
        else:
            sx, sz = st["seed"]; r0_, c0_ = int(round((G.ZTOP - sz) / 6)), int(round(sx / 6))
            w = np.argwhere(wet7[r0_ - 3:r0_ + 4, c0_ - 3:c0_ + 4])[0] + (r0_ - 3, c0_ - 3)
            members[sid] = np.argwhere(lab7 == lab7[w[0], w[1]])
    mset = {sid: {(int(a), int(b)) for a, b in m} for sid, m in members.items()}
    old_sites = Counter()
    for p in old:
        r_, c_ = int(round((G.ZTOP - p["z"]) / 6)), int(round(p["x"] / 6))
        if p.get("site") not in mset or (r_, c_) not in mset[p["site"]]:
            fail("old_site_membership", p["id"], p.get("site")); continue
        old_sites[p["site"]] += 1
    no_eligible = []
    A_, B_ = segs[:, :2], segs[:, 2:]; AB_ = B_ - A_; L2_ = np.maximum((AB_ * AB_).sum(1), 1e-12)
    for sid in built:
        if old_sites[sid] > 0 or sid not in members:
            continue
        m = members[sid]; Qm = np.c_[6.0 * m[:, 1], G.ZTOP - 6.0 * m[:, 0]]
        dmin = np.full(len(Qm), np.inf)
        for k0 in range(0, len(Qm), 128):
            qq = Qm[k0:k0 + 128, None, :]
            t_ = np.clip(((qq - A_) * AB_).sum(2) / L2_, 0, 1)
            dmin[k0:k0 + 128] = np.linalg.norm(qq - (A_ + t_[..., None] * AB_), axis=2).min(1)
        wt = G.surface(allp, Qm, "water"); gm = Hn[m[:, 0], m[:, 1]]
        newpond = np.isfinite(vpn[m[:, 0], m[:, 1]]) & (gm < vpn[m[:, 0], m[:, 1]])
        elig = int(((dmin > 6.0) & ~(wt > gm) & ~newpond).sum())
        if elig:
            fail("old_per_site", sid, elig)
        else:
            no_eligible.append(sid)
    res["old_bed_sites_without_eligible_vertex"] = no_eligible
    res.update(points=len(pts), by_kind=dict(Counter(p["kind"] for p in pts)), expect=dict(Counter(p.get("expect") for p in pts if "expect" in p)),
               record_kinds=dict(rec_kinds), joints=n_joints, joint_sides=sum(1 for p in pts if p["kind"] == "kit_joint_side"),
               joints_with_two_sides=sum(1 for k_, s in seen.items() if byid[k_]["kind"] == "kit_joint" and len(s) == 2),
               lip_test_by_kind=dict(Counter(p["piece_kind"] for p in pts if p["kind"] == "kit_lip" and p["expect"] == "test")),
               margin_min={k: round(min(p["roadway"] - p["ground"] for p in pts if p["kind"] == k), 4) for k in ("kit_axis", "kit_lip", "kit_joint")},
               old_bed_per_site=dict(old_sites), checked_kit_points=len(kitk), checked_dry_points=len(dry),
               failures={k: dict(n=len(v), first=[list(map(str, x)) for x in v[:5]]) for k, v in fails.items()})
    res["passed"] = not fails
else:
    res["passed"] = False
print(json.dumps(res))
json.dump(res, open(run + "/gate-g7.json", "w"), indent=1)
print("G7", "PASS" if res["passed"] else "FAIL")
sys.exit(0 if res["passed"] else 1)
