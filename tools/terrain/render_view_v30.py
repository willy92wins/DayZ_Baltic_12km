"""Offline oblique views of terrain V30 with surface V30 (voxel-space heightfield renderer). Not the engine.

Colour per 1 m from the surface tiles (s_*_lco.png, tile cores stitched), terrain from the native triangles at 1 m,
water where the terrain is below the local water level (blue-grey, darker with depth, as a flat plane).
Usage: render_view_v30.py <terrain_v30.npz> <surface_dir> <out.png> x z eye_height yaw_deg [distance_m] [pitch]
"""
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v30_common import N, tri_sample, cell_planes  # noqa: E402

W, H = 1280, 720
TILE, STEP, OVER = 512, 384, 64


def region_colour(surface, x0, z0, x1, z1):
    """Stitch satellite tile cores into a 1 m colour array covering [x0, x1] x [z0, z1] (row 0 = north)."""
    x0, z0 = max(int(x0), 0), max(int(z0), 0)
    x1, z1 = min(int(x1), 12287), min(int(z1), 12287)
    out = np.zeros((z1 - z0 + 1, x1 - x0 + 1, 3), np.uint8)
    for a in range(x0 // STEP, x1 // STEP + 1):
        for b in range((12288 - z1) // STEP, (12288 - z0) // STEP + 1):
            if not (0 <= a < 32 and 0 <= b < 32):
                continue
            img = np.asarray(Image.open(os.path.join(surface, "layers", f"s_{a:03d}_{b:03d}_lco.png")).convert("RGB"))
            core = img[OVER:OVER + STEP, OVER:OVER + STEP]          # x in [384a, 384a+384), z top 12288-384b
            cx0, cz_top = STEP * a, 12288 - STEP * b
            xs0, xs1 = max(cx0, x0), min(cx0 + STEP - 1, x1)
            zs1, zs0 = min(cz_top - 1, z1), max(cz_top - STEP, z0)
            if xs0 > xs1 or zs0 > zs1:
                continue
            out[z1 - zs1:z1 - zs0 + 1, xs0 - x0:xs1 - x0 + 1] = \
                core[cz_top - 1 - zs1:cz_top - 1 - zs0 + 1, xs0 - cx0:xs1 - cx0 + 1]
    return out, x0, z1


def main():
    terrain, surface, out = sys.argv[1:4]
    cx, cz, eye, yaw = (float(v) for v in sys.argv[4:8])
    dist = float(sys.argv[8]) if len(sys.argv) > 8 else 900.0
    horizon = float(sys.argv[9]) if len(sys.argv) > 9 else 0.30
    t = np.load(terrain)
    h = t["heights"].astype(np.float64)
    cls, level = t["cls"], t["level"].astype(np.float64)
    # A nearest-water lookup extends a high pond level over unrelated land.
    # Use only the cells actually covered by the authored pond pieces, plus
    # the global sea. Same geometric contract as the surface producer.
    planes = cell_planes(cls, level)
    sea = 0.75
    x0, x1, z0, z1 = cx - dist - 10, cx + dist + 10, cz - dist - 10, cz + dist + 10
    col, ox, oz_top = region_colour(surface, x0, z0, x1, z1)
    ground = tri_sample(h, [cx], [cz])[0]
    cam_h = ground + eye
    fy = math.radians(yaw)
    fwd = np.array([math.sin(fy), math.cos(fy)])
    right = np.array([math.cos(fy), -math.sin(fy)])
    fov = math.radians(70)
    u = (np.arange(W) + 0.5) / W * 2 - 1
    dirs = fwd[None, :] + right[None, :] * (u[:, None] * math.tan(fov / 2))
    img = np.zeros((H, W, 3), np.float64)
    ybuf = np.full(W, H, np.int64)
    focal = (W / 2) / math.tan(fov / 2)
    sky_top, sky_bot = np.array([118, 150, 186.0]), np.array([196, 210, 220.0])
    for r in range(H):
        img[r] = sky_top + (sky_bot - sky_top) * min(r / (H * horizon + 1), 1.0)
    d = 1.0
    while d < dist:
        p = cx + dirs[:, 0] * d, cz + dirs[:, 1] * d
        px, pz = np.clip(p[0], 0, 12282), np.clip(p[1], 0, 12282)
        hz = tri_sample(h, px, pz)
        rr = np.clip(np.floor((12282 - pz) / 6).astype(int), 0, N - 2)
        cc = np.clip(np.floor(px / 6).astype(int), 0, N - 2)
        lv = np.maximum(np.nan_to_num(planes[rr, cc], nan=sea), sea)
        wet = hz < lv
        surf = np.where(wet, lv, hz)
        ci = np.clip((oz_top - pz).astype(int), 0, col.shape[0] - 1)
        cj = np.clip((px - ox).astype(int), 0, col.shape[1] - 1)
        c = col[ci, cj].astype(np.float64) * 1.9
        depth = np.clip(lv - hz, 0, 3) / 3
        wc = np.array([70, 92, 104.0])[None, :] * (1 - 0.35 * depth[:, None]) + c * 0.15
        c = np.where(wet[:, None], wc, c)
        fog = min(d / dist, 1.0) ** 1.6
        c = c * (1 - fog) + sky_bot * fog
        yscr = (H * horizon - (surf - cam_h) / d * focal).astype(np.int64)
        yscr = np.clip(yscr, 0, H)
        for j in np.flatnonzero(yscr < ybuf):
            img[yscr[j]:ybuf[j], j] = c[j]
        ybuf = np.minimum(ybuf, yscr)
        d += 0.25 + d * 0.004
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out)
    print(out, "camera", round(cx), round(cz), round(cam_h, 2), "yaw", yaw)


if __name__ == "__main__":
    main()
