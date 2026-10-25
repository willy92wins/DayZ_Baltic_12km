"""Streambed kit models: LODs, bounding centre, proxies, memory points, roadway faces (ODOL stored frame)."""
import sys, json, glob, os
import numpy as np
sys.path.insert(0, r"C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts")
from odol_reader import ODOL
out = {}
for path in sorted(glob.glob("P:/DZ/water/streambed/streambed_leaf_*.p3d")) + ["P:/DZ/water/streambed/misc/stones_leaf_group_3.p3d", "P:/DZ/water/streambed/misc/stones_leaf_bar.p3d"]:
    o = ODOL.from_file(path); bc = o.model_info.bounding_center
    r = dict(bc=[round(bc.x, 3), round(bc.y, 3), round(bc.z, 3)], lods={})
    for l in o.lods:
        V = np.array([(p.x, p.y, p.z) for p in l.vertices]) if l.vertices else np.zeros((0, 3))
        e = dict(nv=len(V), nf=len(l.faces))
        if len(V):
            e["min"] = V.min(0).round(2).tolist(); e["max"] = V.max(0).round(2).tolist()
        if l.proxies:
            e["proxies"] = [(p.model, [round(v, 3) for v in (p.transformation.position.x, p.transformation.position.y, p.transformation.position.z)]) for p in l.proxies]
        if l.named_selections and l.resolution > 1e14:
            e["sel"] = {ns.name: [V[i].round(2).tolist() for i in list(ns.selected_vertices)[:4]] for ns in l.named_selections}
        if abs(l.resolution - 3e15) / 3e15 < 0.01 or abs(l.resolution - 1e15) / 1e15 < 0.01:   # roadway / geometry
            e["faces"] = [[V[i].round(2).tolist() for i in f.vertex_indices] for f in l.faces][:12]
            e["tex"] = l.textures
        r["lods"]["%.3g" % l.resolution] = e
    out[os.path.basename(path)] = r
json.dump(out, open("kit_models.json", "w", newline="\n"), indent=1)
for k, r in out.items():
    print("==", k, "bc", r["bc"])
    for res, e in r["lods"].items():
        s = {kk: e[kk] for kk in ("nv", "nf", "min", "max") if kk in e}
        print("   lod", res, s, ("proxies %s" % e["proxies"]) if "proxies" in e else "", ("sel %s" % list(e["sel"])) if "sel" in e else "")
