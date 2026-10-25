"""G1: without --road-off-lowered, the modified generator reproduces the shipped EV95 source PNGs byte for byte.

Regenerates every tile of the manifest and of the independent zone (gate_lib.tiles_touched) with the worktree build_surface_v30.py on the EV95 terrain, the EV95 water plane and the
EV95 flags (build-wide-slope/build_surface.py:63-67), and compares the PNG files (SHA256) and pixels with the source PNG
whose PAA is the shipped EV95 entry. Also: --road-off-lowered with the EV95 terrain as its own reference (nothing
lowered) must give the same files as no option, on two tiles.
PASS iff every tile and layer is byte-identical and the no-op run matches.
"""
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_lib import (target_terrain, EV95_PBO, EV95_PLANE, EV95_PLANE_SHA, EV95_TERRAIN, FLAGS, GATES, PY, TOOLS, Pbo, World,
                      domain_cells, load_png, manifest, sha, source_png, stems, tiles_touched, verdict)


def run(out, tiles, extra=()):
    if (Path(out) / "surface.json").exists():
        return
    cmd = [PY, "-I", "-B", str(TOOLS / "build_surface_v30.py"), EV95_TERRAIN, str(out), "--tiles",
           ";".join(f"{a},{b}" for a, b in tiles), "--workers", "2", *FLAGS,
           "--water-plane", EV95_PLANE, "--water-plane-sha256", EV95_PLANE_SHA, *extra]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]


def main():
    m = manifest()
    dom, _ = domain_cells(World(target_terrain()))
    tiles = sorted({tuple(t) for t in m["tiles"]} | set(tiles_touched(dom, zone=True)))
    gen12 = sha(TOOLS / "build_surface_v30.py")[:12]  # cached runs are keyed by the generator under test
    out = GATES / "g1" / f"regen-ev95-{gen12}"
    run(out, tiles)
    noop = GATES / "g1" / f"noop-ev95-{gen12}"
    run(noop, tiles[:2], ("--road-off-lowered", EV95_TERRAIN))
    pbo = Pbo(EV95_PBO)
    rows, ok = [], True
    for a, b in tiles:
        for p, stem in stems(a, b).items():
            src = source_png(stem, pbo.read(f"data/layers/{stem}.paa"))
            new = out / "layers" / f"{stem}.png"
            same_bytes = sha(src) == sha(new)
            same_px = bool(np.array_equal(load_png(src), load_png(new)))
            rows.append(dict(tile=[a, b], layer=p, source=str(src), bytes_identical=same_bytes, pixels_identical=same_px))
            ok &= same_bytes
    noop_rows = []
    for a, b in tiles[:2]:
        for p, stem in stems(a, b).items():
            same = sha(noop / "layers" / f"{stem}.png") == sha(out / "layers" / f"{stem}.png")
            noop_rows.append(dict(tile=[a, b], layer=p, identical_to_no_option=same))
            ok &= same
    ok &= len(rows) > 0 and len(noop_rows) == 4
    verdict("G1_default_identity", ok, dict(tiles=[list(t) for t in tiles],
        generator_sha256=sha(TOOLS / "build_surface_v30.py"), terrain=EV95_TERRAIN, water_plane_sha256=EV95_PLANE_SHA,
        layers_compared=len(rows), byte_identical=sum(r["bytes_identical"] for r in rows),
        pixel_identical=sum(r["pixels_identical"] for r in rows), rows=rows, noop=noop_rows))


if __name__ == "__main__":
    main()
