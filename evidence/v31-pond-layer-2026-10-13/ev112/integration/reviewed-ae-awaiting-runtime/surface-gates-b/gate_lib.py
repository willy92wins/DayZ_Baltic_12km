"""Shared helpers for the surface-patch gates. Written apart from patch_surface_v31.py: the domain, the zone, the paint
model, the PBO reader and the PAA decoding are reimplemented here; only road_chains() (the data) and, for the
reference renders, the generator's tile() are shared."""
import hashlib
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, maximum_filter
from scipy.spatial import cKDTree

WT = Path(r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c")
TOOLS = WT / "tools" / "terrain"
sys.path.insert(0, str(TOOLS))
from verify_roads_v30 import road_chains  # noqa: E402

PY = r"C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe"
I2P = r"C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\ImageToPAA\ImageToPAA.exe"
OUT = Path(os.environ.get("SURFACE_GATE_ROOT", "E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev110-wip/surface"))
# the patch and package folders under test (environment overrides for a later run, e.g. on the EV110 terrain)
PATCH = Path(os.environ.get("SURFACE_PATCH_DIR", str(OUT / "patch-ev109")))
PACKAGE = Path(os.environ.get("SURFACE_PACKAGE_DIR", str(OUT / "package-ev109-test")))
# the PBO under test: the packed output of package_surface_patch_v31.py, read back entry by entry by G2, G3, G4 and G5
FINAL_PBO = PACKAGE / "packed" / "narva_trial.pbo"
EV95_TERRAIN = "E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/build-wide-slope/candidate/terrain.npz"
EV95_TERRAIN_SHA = "40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a"
EV95_PLANE = "E:/DayZ-Baltic-Build/v30-narva-dry-bank-relief-20261010/candidate/plane.npy"
EV95_PLANE_SHA = "768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0"
EV95_PBO = "P:/Mods/@DayZ_Baltic_EV95_WideBankPreviewV1/Addons/narva_trial.pbo"
EV109_PBO = "P:/Mods/@DayZ_Baltic_EV109_BridgeRolloutV1/Addons/narva_trial.pbo"
# Trusted target (review 2 of 15-10): the terrain the patch must describe and the compiled WRP that ships with it, given
# by the build chain, never read from the manifest under test. Defaults: the EV109 pair of the trial package.
TARGET_TERRAIN = os.environ.get("SURFACE_TARGET_TERRAIN", "E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev109/terrain-ev109.npz")
TARGET_TERRAIN_SHA = os.environ.get("SURFACE_TARGET_TERRAIN_SHA256", "86c0a85c2b46a65a16e79d450e54473e1593a3db95fe0670c2d5d00561751149")
TARGET_WRP_SHA = os.environ.get("SURFACE_TARGET_WRP_SHA256", "d5f5c8eae280aba6b2ad3b2964f907e79042bbca0632dd4ea8b7ea82a9be789f")
SOURCES = ["E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/build-wide-slope/surface/layers",
           "E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/surface/layers",
           "E:/DayZ-Baltic-Build/v30-complete-dry-surface-20261009/surface/layers",
           "E:/DayZ-Baltic-Build/v30-mixed-bank-constrained-20261010/surface/layers"]
FLAGS = ["--bed-tone", "depth-all", "--bed-surface", "gravel", "--shore-ring", "flowing",
         "--landcover", "smooth", "--landcover-sigma", "1.0"]
SLOTS = np.array([[0, 0, 0], [255, 0, 0], [0, 255, 0], [0, 0, 255]], np.int32)
MIN_DROP = 0.5


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha12(path):
    return sha(path)[:12]


# reports are keyed by the manifest hash AND the packed PBO hash, so neither a new patch nor a repacked PBO reuses an
# old report; renders and decodes are cached by content (terrain/plane hashes, PAA bytes) under gates/cache
GATES = Path(os.environ.get("SURFACE_GATE_OUT") or
             OUT / "gates" / f"{PATCH.name}-{_sha12(PATCH / 'manifest.json')}-{PACKAGE.name}-{_sha12(FINAL_PBO)}")
CACHE = OUT / "gates" / "cache"


def target_terrain():
    """The trusted target terrain, checked by SHA256 before any gate uses it."""
    got = sha(TARGET_TERRAIN)
    assert got == TARGET_TERRAIN_SHA, f"trusted target terrain {TARGET_TERRAIN} has sha {got}, expected {TARGET_TERRAIN_SHA}"
    return TARGET_TERRAIN


def manifest():
    return json.loads((PATCH / "manifest.json").read_text(encoding="utf-8"))


def stems(a, b):
    return {"s": f"s_{a:03d}_{b:03d}_lco", "m": f"m_{a:03d}_{b:03d}_lca"}


class Pbo:
    def __init__(self, path):
        self.path, self.index, self.props = path, {}, {}
        with open(path, "rb") as f:
            def cstr():
                out = bytearray()
                while (c := f.read(1)) not in (b"\0", b""):
                    out += c
                return out.decode("latin1")
            names = []
            while True:
                name = cstr()
                mime, _, _, _, size = struct.unpack("<5I", f.read(20))
                if not name and mime == 0x56657273:
                    while (key := cstr()):
                        self.props[key] = cstr()
                    continue
                if not name:
                    break
                names.append((name.replace("\\", "/"), size))
            pos = f.tell()
        for name, size in names:
            self.index[name] = (pos, size)
            pos += size

    def read(self, name):
        pos, size = self.index[name]
        with open(self.path, "rb") as f:
            f.seek(pos)
            return f.read(size)


EXTRA = None


def source_png(stem, shipped_paa, wide=False):
    """Source PNG of a shipped layer: the one whose sibling PAA has the shipped bytes. wide=True also searches every
    surface build on E: (for unpatched neighbours whose source is older than EV82)."""
    global EXTRA
    dirs = list(SOURCES)
    if wide:
        if EXTRA is None:
            import glob
            EXTRA = sorted(set(glob.glob("E:/DayZ-Baltic-Build/*/surface/layers") + glob.glob("E:/DayZ-Baltic-Build/*/*/surface/layers")
                               + glob.glob("E:/DayZ-Baltic-Build/surface-v30*/layers")))
        dirs += EXTRA
    for d in dirs:
        png, paa = Path(d) / f"{stem}.png", Path(d) / f"{stem}.paa"
        if png.exists() and paa.exists() and paa.read_bytes() == shipped_paa:
            return png
    return None


def load_png(path):
    return np.asarray(Image.open(path)).copy()


def decode_bytes(data):
    """Top mip of a PAA given as bytes, decoded with ImageToPAA; cached by the SHA256 of the bytes."""
    key = hashlib.sha256(data).hexdigest()
    d = CACHE / "decoded"
    d.mkdir(parents=True, exist_ok=True)
    png, paa = d / f"{key}.png", d / f"{key}.paa"
    if not png.exists():
        paa.write_bytes(data)
        tmp = d / f"{key}.tmp.png"
        r = subprocess.run([I2P, str(paa), str(tmp)], capture_output=True, text=True)
        assert r.returncode == 0 and tmp.exists(), (str(paa), r.stdout, r.stderr)
        os.replace(tmp, png)
    return np.asarray(Image.open(png).convert("RGBA")).copy()


def decode_paa(paa, _unused=None):
    """Decode a PAA file (content-keyed cache, never keyed by name)."""
    return decode_bytes(Path(paa).read_bytes())


def slot_of(rgb):
    d = ((rgb[..., None, :3].astype(np.int32) - SLOTS) ** 2).sum(-1)
    return np.argmin(d, axis=-1)


def tile_xz(a, b, pad=0):
    j = np.arange(-pad, 512 + pad) + 0.5
    x = 384 * a - 64 + j
    z = 12288 - 384 * b + 64 - j
    return np.meshgrid(x, z)


def planar(H, X, Z):
    """Height on the native NW-SE triangles: fc >= fr -> NW + fc(NE-NW) + fr(SE-NE); else NW + fr(SW-NW) + fc(SE-SW)."""
    c, r = X / 6.0, (12282.0 - Z) / 6.0
    c0 = np.clip(np.floor(c).astype(int), 0, 2046)
    r0 = np.clip(np.floor(r).astype(int), 0, 2046)
    fc, fr = np.clip(c - c0, 0, 1), np.clip(r - r0, 0, 1)
    nw, ne, sw, se = H[r0, c0], H[r0, c0 + 1], H[r0 + 1, c0], H[r0 + 1, c0 + 1]
    return np.where(fc >= fr, nw + fc * (ne - nw) + fr * (se - ne), nw + fr * (sw - nw) + fc * (se - sw))


def cell_of(X, Z):
    """Cell (row, col) under each pixel centre; -1 outside the map."""
    col = np.floor(X / 6.0).astype(int)
    row = np.floor((12282.0 - Z) / 6.0).astype(int)
    out = (X < 0) | (X >= 12282) | (Z <= 0) | (Z > 12282)
    return np.where(out, -1, row), np.where(out, -1, col)


class World:
    """Lowered cells, road distance and the reference (EV95) water, reimplemented."""
    def __init__(self, target_terrain):
        assert sha(EV95_TERRAIN) == EV95_TERRAIN_SHA and sha(EV95_PLANE) == EV95_PLANE_SHA
        self.H0 = np.load(EV95_TERRAIN)["heights"].astype(np.float64)
        self.H1 = np.load(target_terrain)["heights"].astype(np.float64)
        assert self.H0.shape == self.H1.shape == (2048, 2048), "terrains must be 2048^2"
        assert np.isfinite(self.H0).all() and np.isfinite(self.H1).all(), "non-finite height: lowered cells undefined"
        vdrop = self.H0 - self.H1
        cell_drop = np.max(np.stack([vdrop[:-1, :-1], vdrop[:-1, 1:], vdrop[1:, :-1], vdrop[1:, 1:]]), axis=0)
        self.lowered = cell_drop > MIN_DROP
        self.cell_drop = cell_drop
        self.P0 = np.load(EV95_PLANE)
        samples = []
        for chain in road_chains():
            if len(chain) < 2:
                continue
            seg = np.hypot(*np.diff(chain, axis=0).T)
            s_at = np.concatenate([[0.0], np.cumsum(seg)])
            s = np.arange(0.0, s_at[-1], 0.5)
            samples.append(np.stack([np.interp(s, s_at, chain[:, 0]), np.interp(s, s_at, chain[:, 1])], axis=1))
        self.tree = cKDTree(np.concatenate(samples))

    def fields(self, a, b, pad=0):
        """Per pixel of tile (a, b) with pad: lowered cell, road (<= 3.5 m), painted road in EV95 (road and dry)."""
        X, Z = tile_xz(a, b, pad)
        row, col = cell_of(X, Z)
        inside = row >= 0
        low = np.zeros(X.shape, bool)
        low[inside] = self.lowered[row[inside], col[inside]]
        d, _ = self.tree.query(np.stack([X.ravel(), Z.ravel()], axis=1), distance_upper_bound=6.0)
        road = (d <= 3.5).reshape(X.shape)
        h0 = planar(self.H0, np.clip(X, 0, 12282), np.clip(Z, 0, 12282))
        p0 = np.full(X.shape, np.nan)
        p0[inside] = self.P0[row[inside], col[inside]]
        wet0 = (np.isfinite(p0) & (h0 < np.where(np.isfinite(p0), p0, -1e9))) | (h0 < 0.75)
        return dict(X=X, Z=Z, row=row, col=col, low=low, road=road, painted=road & ~wet0 & inside)


def domain_cells(world):
    """Lowered cells that hold EV95 road paint (any pixel centre painted), computed cell by cell."""
    rows, cols = np.nonzero(world.lowered)
    off = np.arange(6) + 0.5
    ox, oz = np.meshgrid(off, off)
    X = 6.0 * cols[:, None] + ox.ravel()
    Z = 12282.0 - 6.0 * rows[:, None] - oz.ravel()
    d, _ = world.tree.query(np.stack([X.ravel(), Z.ravel()], axis=1), distance_upper_bound=6.0)
    road = (d <= 3.5).reshape(X.shape)
    h0 = planar(world.H0, X, Z)
    p0 = world.P0[rows, cols][:, None]
    wet0 = (np.isfinite(p0) & (h0 < np.where(np.isfinite(p0), p0, -1e9))) | (h0 < 0.75)
    keep = (road & ~wet0).any(axis=1)
    dom = np.zeros(world.lowered.shape, bool)
    dom[rows[keep], cols[keep]] = True
    near_wet_only = int((road.any(axis=1) & ~keep).sum())
    return dom, near_wet_only


def tile_domain(dom, a, b, pad=0):
    X, Z = tile_xz(a, b, pad)
    row, col = cell_of(X, Z)
    out = np.zeros(X.shape, bool)
    inside = row >= 0
    out[inside] = dom[row[inside], col[inside]]
    return out


def tile_zone(dom, a, b):
    """Domain dilated by 2 px (Chebyshev), computed with a pad so that overlapping tiles agree."""
    d = tile_domain(dom, a, b, pad=4)
    return maximum_filter(d, size=5)[4:-4, 4:-4]


def tiles_touched(dom, zone):
    """Every 512 px layer tile (a, b in 0..31) holding a pixel of the domain (zone=False) or of the domain dilated by
    2 px (zone=True), derived from the domain alone: never from the manifest under test."""
    rows, cols = np.nonzero(dom)
    cand = set()
    for r, c in zip(rows, cols):
        a0, b0 = int(6 * c // 384), int((12288 - (12282 - 6 * r)) // 384)
        for a in (a0 - 1, a0, a0 + 1):
            for b in (b0 - 1, b0, b0 + 1):
                if 0 <= a < 32 and 0 <= b < 32:
                    cand.add((a, b))
    test = (lambda a, b: tile_zone(dom, a, b).any()) if zone else (lambda a, b: tile_domain(dom, a, b).any())
    return sorted(t for t in cand if test(*t))


def layer_entry(stem):
    return f"data/layers/{stem}.paa"


def final_layer(rec_layer, stem, shipped):
    """Patched PNG if the tool changed this layer, else the shipped source PNG."""
    if rec_layer.get("changed_px"):
        return load_png(PATCH / "layers" / f"{stem}.png")
    return load_png(source_png(stem, shipped))


def verdict(name, ok, report):
    GATES.mkdir(parents=True, exist_ok=True)
    report = dict(gate=name, result="PASS" if ok else "FAIL", **report)
    (GATES / f"{name}.json").write_text(json.dumps(report, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"{name}: {'PASS' if ok else 'FAIL'}")
    return ok
