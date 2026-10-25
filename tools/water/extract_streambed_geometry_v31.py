"""Streambed kit geometry for streambed_kit_v31.py v8, read from the vanilla ODOL files (P:/DZ/water/streambed).

Per model streambed_<family>_<kind>.p3d (stored frame = MLOD minus bounding centre = the frame a world matrix places):
  road      roadway LOD (resolution ~3e15) faces with their texture (water_ext = flat run, concrete_ext = end lips);
  water     LOD0 of the CalmWater proxy (proxy/streambed_<kind>_water.p3d) in the parent stored frame:
            parent = child_stored + proxy position + child bounding centre (convention inferred in
            scratchpad turn-pieces/turn-pieces.json 'conventions.water_proxy_frame'; the proxy orientation must be identity);
            LOD0 covers the whole plate incl. the end lips, 0.25 m (straights, curves) / 0.20 m (slanted) above the roadway;
  centre    roadway strip rung midpoints from the downstream (-Z) to the upstream (+Z) plate end;
  ends      plate-end centre and upstream unit direction (xz) of both end rungs; curves also get the PI (intersection
            of the two end tangents) and the tangent lengths entry->PI, PI->exit;
  sills     geometry-LOD component centroids sorted by z (slanted: the channel runs sill to sill along model Z).
Fail-closed: the source folder must exist and every model of REQUIRED must load with roadway faces (water_ext and
concrete_ext), water-proxy faces and a centreline; otherwise nothing is written and the exit code is 1, so an existing
geometry file is never replaced by an empty or partial one (the first version caught FileNotFoundError, wrote models={} and
exited 0 without P:, review of 15-10). The output is written to <out.json>.tmp and renamed over <out.json> only when complete.
Usage: extract_streambed_geometry_v31.py <out.json> [source_dir]   (default P:/DZ/water/streambed/, i.e. the P: subst; needs
       the dayz-p3d-debinarizer odol_reader)
"""
import collections, json, os, sys
import numpy as np
sys.path.insert(0, r"C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts")
from odol_reader import ODOL

D = "P:/DZ/water/streambed/"
FAMILIES = ("leaf", "moss", "sand")
KINDS = ("long_straight", "long_straight_2", "short_straight", "long_curve_left", "long_curve_right", "short_slanted", "short_slanted_inv")
REQUIRED = [f"{fam}_{kind}" for fam in FAMILIES for kind in KINDS if (fam, kind) != ("sand", "long_straight_2")]   # vanilla has no sand _2


def lodv(l):
    return np.array([(p.x, p.y, p.z) for p in l.vertices]) if l.vertices else np.zeros((0, 3))


def faces_tex(l):
    V = lodv(l); out = []
    for s in l.sections:
        tex = l.textures[s.texture_index].split("\\")[-1] if 0 <= s.texture_index < len(l.textures) else ""
        for f in s.get_face_indices(l.faces):
            out.append((tex, V[list(l.faces[f].vertex_indices)]))
    return out


def key(p):
    return (round(float(p[0]), 3), round(float(p[1]), 3), round(float(p[2]), 3))


def strip_rungs(F):
    """Rungs (shared edges plus the two end edges) of a strip of quads, ordered from the -Z end to the +Z end."""
    edges = collections.defaultdict(list)
    for fi, (_, P) in enumerate(F):
        for i in range(len(P)):
            edges[frozenset((key(P[i]), key(P[(i + 1) % len(P)])))].append(fi)
    adj = collections.defaultdict(list)
    for e, fs in edges.items():
        if len(fs) == 2:
            adj[fs[0]].append((fs[1], e)); adj[fs[1]].append((fs[0], e))
    ends = sorted([fi for fi in range(len(F)) if len(adj[fi]) == 1], key=lambda fi: F[fi][1][:, 2].mean())
    assert len(ends) == 2, ends
    order, rungs, prev, cur = [ends[0]], [], None, ends[0]
    while True:
        nxt = [(f, e) for f, e in adj[cur] if f != prev]
        if not nxt:
            break
        f, e = nxt[0]; rungs.append(e); prev, cur = cur, f; order.append(cur)

    def end_rung(fi, shared):
        P = F[fi][1]
        for i in range(len(P)):
            e = frozenset((key(P[i]), key(P[(i + 1) % len(P)])))
            if e != shared and not (e & shared):
                return e
    allr = [end_rung(order[0], rungs[0])] + rungs + [end_rung(order[-1], rungs[-1])]
    return [np.array(sorted(e)) for e in allr]


def end_dir(r, towards):
    """Unit xz normal of rung r pointing towards the point `towards` (xz)."""
    v = (r[1] - r[0])[[0, 2]]; n = np.array([-v[1], v[0]]); n /= np.linalg.norm(n)
    return n if n @ (towards - r.mean(0)[[0, 2]]) > 0 else -n


def model(fam, kind, src=D):
    o = ODOL.from_file(src + f"streambed_{fam}_{kind}.p3d")
    bc = o.model_info.bounding_center
    road = min(o.lods, key=lambda l: abs(l.resolution - 3e15))
    F = faces_tex(road)
    rungs = strip_rungs(F)
    mids = np.array([r.mean(0) for r in rungs])
    d_in = end_dir(rungs[0], mids[1][[0, 2]]); d_out = -end_dir(rungs[-1], mids[-2][[0, 2]])
    flat_y = float(max(p[1] for _, P in F for p in P))
    out = dict(bc=[bc.x, bc.y, bc.z], roadway_flat_y=round(flat_y, 4),
               road=[dict(tex=t, v=np.round(P, 4).tolist()) for t, P in F],
               centre=np.round(mids, 4).tolist(),
               entry=dict(centre=np.round(mids[0], 4).tolist(), dir_up=np.round(d_in, 5).tolist()),
               exit=dict(centre=np.round(mids[-1], 4).tolist(), dir_up=np.round(d_out, 5).tolist()),
               turn_deg_upstream=round(float(np.degrees(np.arctan2(d_out[0], d_out[1]) - np.arctan2(d_in[0], d_in[1]))), 3))
    if "curve" in kind:
        a, b = mids[0][[0, 2]], mids[-1][[0, 2]]
        t = np.linalg.solve(np.c_[d_in, d_out], b - a)            # a + t0 d_in = b - t1 d_out
        pi = a + t[0] * d_in
        out["pi"] = dict(xz=np.round(pi, 4).tolist(), entry_to_pi=round(float(t[0]), 4), pi_to_exit=round(float(t[1]), 4))
    g = min(o.lods, key=lambda l: abs(l.resolution - 1e13)); Vg = lodv(g)
    sills = sorted((Vg[list(ns.selected_vertices)].mean(0) for ns in g.named_selections if len(ns.selected_vertices)), key=lambda p: p[2])
    out["sills"] = [np.round(p, 4).tolist() for p in sills]
    l0 = o.lods[0]; px = l0.proxies[0]; pp = px.transformation.position; O = px.transformation.orientation
    ori = np.array([[O.aside.x, O.aside.y, O.aside.z], [O.up.x, O.up.y, O.up.z], [O.dir.x, O.dir.y, O.dir.z]])
    assert np.allclose(ori, np.eye(3), atol=1e-4), (kind, ori)
    name = px.model.split("\\")[-1]
    w = ODOL.from_file(src + f"proxy/{name}.p3d"); wbc = w.model_info.bounding_center
    shift = np.array([pp.x + wbc.x, pp.y + wbc.y, pp.z + wbc.z])
    WF = faces_tex(w.lods[0])
    out["water"] = [np.round(P + shift, 4).tolist() for _, P in WF]
    out["water_proxy"] = dict(model=px.model, shift=np.round(shift, 4).tolist(), lod0_resolution=w.lods[0].resolution,
                              top_above_roadway=round(float(max(p[1] for P in out["water"] for p in P) - flat_y), 4))
    return out


def complete(m):
    tex = {f["tex"].split(".")[0] for f in m["road"]}
    return bool(m["road"]) and bool(m["water"]) and len(m["centre"]) >= 2 and {"water_ext", "concrete_ext"} <= tex


def main():
    out = sys.argv[1]
    src = sys.argv[2].replace("\\", "/").rstrip("/") + "/" if len(sys.argv) > 2 else D
    if not os.path.isdir(src):
        sys.exit(f"source folder {src} not found (P: subst missing?): nothing written")
    res = dict(schema="streambed-kit-geometry-v31.v1", source=src, odol_reader="dayz-p3d-debinarizer/scripts/odol_reader.py", models={})
    bad = []
    for name in REQUIRED:
        fam, kind = name.split("_", 1)
        try:
            m = model(fam, kind, src)
        except OSError as e:
            bad.append(f"{name}: {e}"); continue
        if not complete(m):
            bad.append(f"{name}: incomplete (road {len(m['road'])}, water {len(m['water'])}, centre {len(m['centre'])})"); continue
        res["models"][name] = m
        print(fam, kind, "flat", m["roadway_flat_y"], "water+", m["water_proxy"]["top_above_roadway"], "road faces", len(m["road"]),
              "water faces", len(m["water"]), "turn", m["turn_deg_upstream"], m.get("pi"))
    if bad or sorted(res["models"]) != sorted(REQUIRED):
        sys.exit("refused, nothing written: " + "; ".join(bad))
    with open(out + ".tmp", "w", newline="\n") as f:
        json.dump(res, f, separators=(",", ":"))
    os.replace(out + ".tmp", out)


if __name__ == "__main__":
    main()
