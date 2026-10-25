"""Put surface V30 textures into a staged world (tools/terrain/derive_world_v30.py output).

Converts every layers/s_*_lco.png and m_*_lca.png of a surface build (tools/terrain/build_surface_v30.py) to PAA
with DayZ Tools' ImageToPAA (TexConvert rules: _lco DXT1, _lca DXT5), then replaces the 1,024 + 1,024 textures of
the stage's data/layers, PNG and PAA, under their existing names. 215 of V29's 4,775 tile materials are not the
full four-surface set (130 sea tiles with gravel only, 85 with two or three surfaces), so every P_*.rvmat is
rewritten from one full template with its tile's textures and uvTransform; the renderer must first reproduce all
4,560 full V29 materials byte for byte. Material names and the WRP material grid do not change.
Usage: apply_surface_v30.py <surface_dir> <stage_dir> [--workers 8]
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

FULL = ["cp_gravel", "cp_conifer_common1", "cp_grass", "cp_grass_tall"]
SURF = re.compile(r"terrain\\(cp_[a-z0-9_]+?)_nopx\.paa")
TILE = re.compile(r"^P_(\d{3})-(\d{3})_", re.I)


def render(template, a, b):
    """The template tile 010-010 moved to tile (a, b): its two textures and the uvTransform pos of TexGen3/4."""
    t = template.replace("s_010_010_lco", f"s_{a:03d}_{b:03d}_lco").replace("m_010_010_lca", f"m_{a:03d}_{b:03d}_lca")
    u, v = -(384 * a - 64) / 512, (12288 - 384 * b + 64) / 512
    old = "pos[]={-7.375,16.625,0};"
    assert t.count(old) == 2
    return t.replace(old, f"pos[]={{{u:g},{v:g},0}};")


def normalise_materials(layers):
    names = [f for f in os.listdir(layers) if f.lower().endswith(".rvmat") and TILE.match(f)]
    read = lambda f: open(os.path.join(layers, f), "rb").read().decode("utf-8")
    template = read("P_010-010_L00_L01_L02_L03.rvmat")
    full, partial = [], []
    for f in names:
        (full if SURF.findall(read(f)) == FULL else partial).append(f)
    for f in full:
        a, b = (int(g) for g in TILE.match(f).groups())
        assert render(template, a, b) == read(f), f"template does not reproduce {f}"
    for f in partial:
        a, b = (int(g) for g in TILE.match(f).groups())
        data = render(template, a, b).encode("utf-8")
        with open(os.path.join(layers, f), "wb") as h:
            h.write(data)
        assert open(os.path.join(layers, f), "rb").read() == data
    return {"materials": len(names), "full_reproduced": len(full), "rewritten": len(partial)}


IMAGE_TO_PAA = r"C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\ImageToPAA\ImageToPAA.exe"


def convert(png):
    paa = png[:-4] + ".paa"
    if os.path.exists(paa) and os.path.getmtime(paa) >= os.path.getmtime(png):
        return paa, 0
    r = subprocess.run([IMAGE_TO_PAA, png, paa], capture_output=True, text=True)
    return paa, r.returncode


def main():
    surface, stage = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 8
    src = os.path.join(surface, "layers")
    pngs = sorted(os.path.join(src, f) for f in os.listdir(src) if f.endswith(".png"))
    assert len(pngs) == 2048, len(pngs)
    with ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(convert, pngs))
    bad = [p for p, code in results if code != 0 or not os.path.exists(p)]
    assert not bad, bad[:5]
    dst = os.path.join(stage, "data", "layers")
    names = os.listdir(dst)
    replaced = {"png": 0, "paa": 0}
    for name in names:
        low = name.lower()
        if not (low.startswith(("s_", "m_")) and low.endswith(("_lco.png", "_lca.png", "_lco.paa", "_lca.paa"))):
            continue
        source = os.path.join(src, low)
        assert os.path.exists(source), source
        data = open(source, "rb").read()
        with open(os.path.join(dst, name), "wb") as f:
            f.write(data)
        assert open(os.path.join(dst, name), "rb").read() == data
        replaced[low[-3:]] += 1
    assert replaced == {"png": 2048, "paa": 2048}, replaced
    materials = normalise_materials(dst)
    digest = hashlib.sha256()
    for p, _ in results:
        digest.update(open(p, "rb").read())
    receipt = {"status": "SURFACE_V30_APPLIED", "replaced": replaced, "materials": materials,
               "paa_set_sha256": digest.hexdigest(),
               "surface_dir": os.path.abspath(surface)}
    with open(os.path.join(stage, "..", "surface-receipt.json"), "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=1)
    print(json.dumps(receipt, indent=1))


if __name__ == "__main__":
    main()
