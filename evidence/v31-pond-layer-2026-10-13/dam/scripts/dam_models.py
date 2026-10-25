"""Dump the vanilla dam ODOLs: every LOD with resolution, bbox, faces, selections, properties, textures; roadway faces."""
import json, sys
import numpy as np
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
from odol_reader import ODOL

D = "P:/DZ/structures/industrial/dams/"
out = {}
for name in ("dam_stone_40", "dam_concrete_20", "dam_concrete_20_floodgate"):
    od = ODOL.from_file(D + name + ".p3d")
    lods = []
    for l in od.lods:
        V = np.array([(p.x, p.y, p.z) for p in l.vertices], float) if l.vertices else np.zeros((0, 3))
        e = dict(res=float(l.resolution), nv=int(len(V)), nf=len(l.faces))
        if len(V):
            e["bbox"] = [V.min(0).round(4).tolist(), V.max(0).round(4).tolist()]
        for attr in ("named_selections", "properties", "textures", "materials", "proxies"):
            v = getattr(l, attr, None)
            if v is None:
                continue
            if attr == "named_selections":
                e[attr] = [s.name for s in v][:40]
            elif attr == "properties":
                e[attr] = [list(p) if isinstance(p, (tuple, list)) else str(p) for p in v]
            elif attr == "materials":
                e[attr] = [getattr(m, "name", str(m)) for m in v][:10]
            elif attr == "textures":
                e[attr] = [str(t) for t in v][:10]
            else:
                e[attr] = [str(p) for p in v][:10]
        if abs(l.resolution - 3e15) < 1e10 or abs(l.resolution - 1e13) < 1e9 or abs(l.resolution - 4e15) < 1e10:
            tris = []
            for f in l.faces:
                ids = list(f.vertex_indices)
                for i in range(1, len(ids) - 1):
                    tris.append(V[[ids[0], ids[i], ids[i + 1]]].round(4).tolist())
            e["tris"] = tris
        if abs(l.resolution - 1e15) < 1e10:
            e["memory_points"] = V.round(4).tolist()
        lods.append(e)
    out[name] = lods
    print(name)
    for e in lods:
        print("  res %.3g nv %d nf %d bbox %s sel %s prop %s" % (e["res"], e["nv"], e["nf"], e.get("bbox"), e.get("named_selections", [])[:12], e.get("properties")))
json.dump(out, open(sys.argv[1], "w"), indent=0)
