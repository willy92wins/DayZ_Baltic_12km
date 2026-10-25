"""Tide and swell views: date captures in the engine swell, and measure the darkening of flat land per frame.

The engine sea (missions/BalticTideProbeV2) is a swell: SurfaceGetSeaLevel = MaxTide/2 + MaxWave*sin(2*pi*t/12.5 s).
`levels` reads the probe log (SEA rows every 250 ms, RT rows tying the server clock to the wall clock) and gives the
sea level at each capture_YYYYMMDD_HHMMSS_mmm.jpg. `flats` casts every 4th pixel of a pose onto the terrain (frame size
read from the captures; vertical FOV --vfov, 68.5 deg as calibrated on EDGE1 at 1920x1080) and reports, per frame, the
mean luminance on land at the flat floor divided by the mean on land 1.42-1.60 m: 1.00 is no darkening; frames well
below it show the flat land turning dark.

Usage:
  tide_views_v30.py levels --log baltic_tide_probe_v2.log --shots DIR --out levels.json
  tide_views_v30.py flats --terrain T.npz --shots DIR --groups groups.json --out flats.json [--floor 1.40] [--vfov 68.5]
groups.json: {"POSE": {"cam": [x,y,z], "look": [x,y,z], "frames": ["HHMMSS_mmm", ...]}, ...}
"""
import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'terrain'))
from v30_common import tri_sample  # noqa: E402

STEP = 4


def read_log(path):
    rt, sea, cfg = [], [], None
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        f = line.split(';')
        if f[0] == 'RT':
            rt.append((int(f[1]), int(f[2]) * 3600 + int(f[3]) * 60 + int(f[4])))
        elif f[0] == 'SEA':
            sea.append((int(f[2]), float(f[3])))
        elif f[0] == 'CFG':
            cfg = dict(sea_min=float(f[1]), sea_max=float(f[2]), wave_max=float(f[3]))
    assert rt and sea, 'Probe log without RT or SEA rows'
    return np.array(rt, float), np.array(sea, float), cfg


def levels(args):
    rt, sea, cfg = read_log(args.log)
    (k, b), *_ = np.linalg.lstsq(np.column_stack([rt[:, 1], np.ones(len(rt))]), rt[:, 0], rcond=None)
    resid = np.abs(rt[:, 0] - (k * rt[:, 1] + b))
    t = sea[:, 0] / 1000.0
    best = None
    for period in np.arange(5, 30, 0.01):
        w = 2 * np.pi / period
        m = np.column_stack([np.ones_like(t), np.sin(w * t), np.cos(w * t)])
        c, *_ = np.linalg.lstsq(m, sea[:, 1], rcond=None)
        r = float(np.sqrt(np.mean((m @ c - sea[:, 1]) ** 2)))
        if best is None or r < best[0]:
            best = (r, float(period), c)
    shots = []
    for p in sorted(Path(args.shots).glob('capture_*.jpg')):
        g = re.search(r'_(\d{2})(\d{2})(\d{2})_(\d{3})\.jpg$', p.name)
        wall = int(g.group(1)) * 3600 + int(g.group(2)) * 60 + int(g.group(3)) + int(g.group(4)) / 1000.0
        ms = k * wall + b
        shots.append(dict(file=p.name, server_ms=round(ms), level=round(float(np.interp(ms, sea[:, 0], sea[:, 1])), 3)))
    return dict(status='DIAGNOSTIC_SWELL_LEVELS', config=cfg, clock_slope_ms_per_s=round(float(k), 3),
                clock_residual_p95_ms=round(float(np.percentile(resid, 95)), 1), sea_rows=len(sea),
                sea_level=dict(min=float(sea[:, 1].min()), max=float(sea[:, 1].max())),
                swell=dict(period_s=round(best[1], 3), amplitude_m=round(float(np.hypot(best[2][1], best[2][2])), 4),
                           mean_m=round(float(best[2][0]), 4), rms_m=round(best[0], 5)),
                shots=shots, limits=['Server API sea; the client renders its own swell and wave field.'])


def project(H, cls, cam, look, floor, W, HH, vfov_deg, sea=0.75):
    cam, look = np.array(cam, float), np.array(look, float)
    f = (look - cam) / np.linalg.norm(look - cam)
    right = np.array([f[2], 0.0, -f[0]])
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    if up[1] < 0:
        up = -up
    t2 = math.tan(math.radians(vfov_deg) / 2)
    px, py = np.meshgrid(np.arange(STEP / 2, W, STEP), np.arange(STEP / 2, HH, STEP))
    d = (f + right * (((px - W / 2) / (W / 2)) * t2 * W / HH)[..., None]
         + up * (((HH / 2 - py) / (HH / 2)) * t2)[..., None]).reshape(-1, 3)
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    t = np.full(len(d), 0.5)
    hit = np.full((len(d), 3), np.nan)
    alive = np.ones(len(d), bool)
    for _ in range(4000):
        idx = np.nonzero(alive)[0]
        if idx.size == 0:
            break
        p = cam + t[idx, None] * d[idx]
        inside = (p[:, 0] > 0) & (p[:, 0] < 12282) & (p[:, 2] > 0) & (p[:, 2] < 12282) & (t[idx] < 6000)
        ter = np.where(inside, tri_sample(H, np.clip(p[:, 0], 0, 12281), np.clip(p[:, 2], 0, 12281)), -1e9)
        h = p[:, 1] <= np.maximum(ter, sea)
        hit[idx[h]] = p[h]
        alive[idx[h | ~inside]] = False
        t[idx] += np.maximum(0.25, t[idx] * 0.004)
    hit = hit.reshape(px.shape + (3,))
    ok = np.isfinite(hit[..., 0])
    x, z = np.where(ok, hit[..., 0], 0), np.where(ok, hit[..., 2], 0)
    ter = np.where(ok, tri_sample(H, x, z), np.nan)
    r = np.clip(((12282 - z) / 6).round().astype(int), 0, H.shape[0] - 1)
    c = np.clip((x / 6).round().astype(int), 0, H.shape[1] - 1)
    land = ok & (cls[r, c] == 0)
    return land & (np.abs(ter - floor) < 0.01), land & (ter >= floor + 0.02) & (ter < floor + 0.20)


def flats(args):
    with np.load(args.terrain) as d:
        H, cls = d['heights'].astype(np.float64), d['cls']
    groups = json.loads(Path(args.groups).read_text(encoding='utf-8'))
    first = next(iter(groups.values()))['frames'][0]
    W, HH = Image.open(next(Path(args.shots).glob(f'capture_*_{first}.jpg'))).size
    out = {}
    for pose, g in groups.items():
        flat, ring = project(H, cls, g['cam'], g['look'], args.floor, W, HH, args.vfov)
        ratios = []
        for k in g['frames']:
            hits = sorted(Path(args.shots).glob(f'capture_*_{k}.jpg'))
            assert len(hits) == 1, f'frame {k}: {len(hits)} files'
            a = np.asarray(Image.open(hits[0]).convert('L')).astype(np.float64)
            a = a[STEP // 2::STEP, STEP // 2::STEP][:flat.shape[0], :flat.shape[1]]
            ratios.append(round(float(a[flat].mean() / a[ring].mean()), 4) if flat.any() and ring.any() else None)
        valid = [v for v in ratios if v is not None]
        out[pose] = dict(flat_pixels=int(flat.sum()), ring_pixels=int(ring.sum()), ratios=ratios,
                         min=min(valid) if valid else None, max=max(valid) if valid else None,
                         spread=round(max(valid) - min(valid), 4) if valid else None)
    return dict(status='DIAGNOSTIC_FLAT_DARKENING', floor_m=args.floor, vfov_deg=args.vfov, frame_size=[W, HH],
                poses=out,
                limits=['Ratio of luminances; it names no cause.', 'Camera FOV calibrated on one pose (EDGE1).'])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('levels')
    a.add_argument('--log', required=True)
    a.add_argument('--shots', required=True)
    a.add_argument('--out', required=True)
    b = sub.add_parser('flats')
    b.add_argument('--terrain', required=True)
    b.add_argument('--shots', required=True)
    b.add_argument('--groups', required=True)
    b.add_argument('--out', required=True)
    b.add_argument('--floor', type=float, default=1.40)
    b.add_argument('--vfov', type=float, default=68.5)
    args = ap.parse_args()
    out = Path(args.out)
    assert not out.exists(), 'Preserve prior evidence'
    res = levels(args) if args.cmd == 'levels' else flats(args)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in res.items() if k not in ('shots', 'poses')}, indent=1))
    if 'poses' in res:
        for pose, v in res['poses'].items():
            print(pose, 'min', v['min'], 'max', v['max'], 'spread', v['spread'])


if __name__ == '__main__':
    main()
