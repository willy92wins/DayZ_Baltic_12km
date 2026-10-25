"""Terrain flicker by height: per-pixel brightness change in a burst of captures, binned by the terrain height seen.

Each frame of a pose burst is compared with the burst median; every 2nd pixel is cast onto the terrain (same camera
model as tools/playtest/tide_views_v30.py: look-at pose, vertical FOV --vfov, frame size read from the captures) and the
mean change is reported per terrain-height bin on land. A shading switched by height (a wet band below some level)
concentrates in a few bins; cloud shadows or exposure changes move every bin alike, so each frame also reports the
mean change on land at 2.2 m and above (ref) to subtract. The sea level of each frame comes from the `levels` output
of tide_views_v30.py.
Usage: flicker_by_height_v30.py --terrain T.npz --groups groups.json --shots DIR --levels levels.json [--vfov 68.5]
                                [--out table.json] POSE [POSE ...]
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'terrain'))
from v30_common import N, tri_sample  # noqa: E402

STEP = 2
BINS = [0.8, 1.0, 1.2, 1.35, 1.40, 1.42, 1.45, 1.50, 1.55, 1.60, 1.8, 2.2, 3.0, 6.0]
REF_M = 2.2


def cast(H, cls, cam, look, W, HH, vfov_deg, sea=0.75):
    cam, look = np.array(cam, float), np.array(look, float)
    f = (look - cam) / np.linalg.norm(look - cam)
    right = np.array([f[2], 0.0, -f[0]])
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    if up[1] < 0:
        up = -up
    t2 = math.tan(math.radians(vfov_deg) / 2)
    px, py = np.meshgrid(np.arange(STEP / 2, W, STEP), np.arange(STEP / 2, HH, STEP))
    dv = (f + right * (((px - W / 2) / (W / 2)) * t2 * W / HH)[..., None]
          + up * (((HH / 2 - py) / (HH / 2)) * t2)[..., None]).reshape(-1, 3)
    dv /= np.linalg.norm(dv, axis=1, keepdims=True)
    t = np.full(len(dv), 0.5)
    hit = np.full((len(dv), 3), np.nan)
    alive = np.ones(len(dv), bool)
    for _ in range(4000):
        idx = np.nonzero(alive)[0]
        if idx.size == 0:
            break
        p = cam + t[idx, None] * dv[idx]
        inside = (p[:, 0] > 0) & (p[:, 0] < 12282) & (p[:, 2] > 0) & (p[:, 2] < 12282) & (t[idx] < 3000)
        ter = np.where(inside, tri_sample(H, np.clip(p[:, 0], 0, 12281), np.clip(p[:, 2], 0, 12281)), -1e9)
        h = p[:, 1] <= np.maximum(ter, sea)
        hit[idx[h]] = p[h]
        alive[idx[h | ~inside]] = False
        t[idx] += np.maximum(0.1, t[idx] * 0.002)
    hit = hit.reshape(px.shape + (3,))
    ok = np.isfinite(hit[..., 0])
    x, z = np.where(ok, hit[..., 0], 0), np.where(ok, hit[..., 2], 0)
    ter = np.where(ok, tri_sample(H, x, z), np.nan)
    r = np.clip(((12282 - z) / 6).round().astype(int), 0, N - 1)
    c = np.clip((x / 6).round().astype(int), 0, N - 1)
    return ter, ok & (cls[r, c] == 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--terrain', required=True)
    ap.add_argument('--groups', required=True)
    ap.add_argument('--shots', required=True)
    ap.add_argument('--levels', required=True)
    ap.add_argument('--vfov', type=float, default=68.5)
    ap.add_argument('--out')
    ap.add_argument('poses', nargs='+')
    a = ap.parse_args()
    with np.load(a.terrain) as d:
        H, cls = d['heights'].astype(np.float64), d['cls']
    groups = json.loads(Path(a.groups).read_text(encoding='utf-8'))
    level = {s['file'][-14:-4]: s['level'] for s in json.loads(Path(a.levels).read_text(encoding='utf-8'))['shots']}
    res = {}
    for pose in a.poses:
        g = groups[pose]
        frames = []
        for k in g['frames']:
            hits = sorted(Path(a.shots).glob(f'capture_*_{k}.jpg'))
            assert len(hits) == 1, f'frame {k}: {len(hits)} files'
            frames.append(np.asarray(Image.open(hits[0]).convert('L')).astype(float))
        HH, W = frames[0].shape
        ter, land = cast(H, cls, g['cam'], g['look'], W, HH, a.vfov)
        stack = np.stack([fr[STEP // 2::STEP, STEP // 2::STEP][:ter.shape[0], :ter.shape[1]] for fr in frames])
        med = np.median(stack, axis=0)
        masks = [land & (ter >= lo) & (ter < hi) for lo, hi in zip(BINS[:-1], BINS[1:])]
        high = land & (ter >= REF_M)
        rows = []
        for k, fr in zip(g['frames'], stack):
            dlt = fr - med
            rows.append({'frame': k, 'sea': level.get(k),
                         'mean_change': [round(float(dlt[m].mean()), 2) if m.sum() >= 30 else None for m in masks],
                         'ref_change': round(float(dlt[high].mean()), 2) if high.sum() >= 30 else None})
        res[pose] = {'pixels': [int(m.sum()) for m in masks], 'frames': rows}
        print(f'\n{pose}: land pixels {int(land.sum())}; mean (frame - burst median) by terrain height bin')
        print('frame        sea   ' + ' '.join(f'{lo:>4.2f}-' for lo in BINS[:-1]) + '   ref')
        print('pixels            ' + ' '.join(f'{n:>5d}' for n in res[pose]['pixels']))
        for r in rows:
            print(f"{r['frame']}  {r['sea'] if r['sea'] is not None else float('nan'):.2f}  "
                  + ' '.join(f'{v:+5.1f}' if v is not None else '   . ' for v in r['mean_change'])
                  + (f" {r['ref_change']:+5.1f}" if r['ref_change'] is not None else '     .'))
    if a.out:
        out = {'status': 'DIAGNOSTIC_FLICKER_BY_HEIGHT', 'terrain': a.terrain, 'vfov_deg': a.vfov,
               'bins_m': BINS, 'ref_from_m': REF_M, 'poses': res,
               'limits': ['Mean brightness change per height bin; it names no cause.',
                          'Pixels are binned by the terrain the camera model predicts; FOV error blurs the bins.']}
        Path(a.out).write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
