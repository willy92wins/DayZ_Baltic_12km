import sys
sys.path.insert(0, r"C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts")
from odol_reader import ODOL
import numpy as np
for m in sys.argv[1:]:
    o = ODOL.from_file(f"P:/DZ/water/streambed/{m}.p3d")
    l = min(o.lods, key=lambda l: abs(l.resolution - 3e15))
    V = np.array([(p.x, p.y, p.z) for p in l.vertices])
    print("==", m, "textures", l.textures)
    for s in l.sections:
        idx = s.get_face_indices(l.faces)
        for f in idx:
            P = V[list(l.faces[f].vertex_indices)]
            tex = l.textures[s.texture_index] if 0 <= s.texture_index < len(l.textures) else ""
            print("  face tex", tex.split("\\")[-1], "x", P[:, 0].round(2).tolist(), "y", P[:, 1].round(2).tolist(), "z", P[:, 2].round(2).tolist())
