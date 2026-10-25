"""Where the FLAT1 close-up shows water over land: cast every 2nd pixel of the capture onto the v5 terrain (camera
model of tools/playtest/flicker_by_height_v30.py, vertical FOV 67.4 deg at 1273x701), report the sea level at the
capture time from the probe log, and save the hit points for plotting."""
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees'
            r'\codex-handoff-review-74f290')
sys.path.insert(0, str(REPO / 'tools' / 'terrain'))
from v30_common import tri_sample  # noqa: E402

SP = Path(__file__).parent
CAP = Path('E:/DayZ-Baltic-Build/v30-v5/views/closeups/COAST_FLAT1/capture_20261005_134144_530.jpg')
LOG = Path('E:/DayZ-Baltic-Build/v30-v5/views/baltic_tide_probe_v2.log')
CAM, LOOK = [5134.1, 9.37, 10339.3], [5171.0, 0.75, 10318.5]
t = np.load('E:/DayZ-Baltic-Build/v30-v5/coast/terrain_coast.npz')
H = t['heights'].astype(np.float64)
img = Image.open(CAP)
print('capture size', img.size)
client = img.crop((11, 45, 11 + 1273, 45 + 701)) if img.size == (1295, 757) else img
client.save(SP / 'flat1-client.png')
W, HH = client.size

rt, sea = [], []
for line in LOG.read_text(encoding='utf-8-sig').splitlines():
    f = line.split(';')
    if f[0] == 'RT':
        rt.append((int(f[1]), int(f[2]) * 3600 + int(f[3]) * 60 + int(f[4])))
    elif f[0] == 'SEA':
        sea.append((int(f[2]), float(f[3])))
rt, sea = np.array(rt, float), np.array(sea, float)
k, b = np.polyfit(rt[:, 1], rt[:, 0], 1)
g = re.search(r'_(\d{2})(\d{2})(\d{2})_(\d{3})\.jpg$', CAP.name)
wall = int(g.group(1)) * 3600 + int(g.group(2)) * 60 + int(g.group(3)) + int(g.group(4)) / 1000
ms = k * wall + b
lvl = float(np.interp(ms, sea[:, 0], sea[:, 1]))
print('sea level at capture', round(lvl, 3), 'inside log', bool(sea[0, 0] <= ms <= sea[-1, 0]))

cam, look = np.array(CAM), np.array(LOOK)
f = (look - cam) / np.linalg.norm(look - cam)
right = np.array([f[2], 0.0, -f[0]])
right /= np.linalg.norm(right)
up = np.cross(right, f)
up = up if up[1] > 0 else -up
t2 = math.tan(math.radians(67.4) / 2)
px, py = np.meshgrid(np.arange(1, W, 2), np.arange(1, HH, 2))
dv = (f + right * (((px - W / 2) / (W / 2)) * t2 * W / HH)[..., None]
      + up * (((HH / 2 - py) / (HH / 2)) * t2)[..., None]).reshape(-1, 3)
dv /= np.linalg.norm(dv, axis=1, keepdims=True)
tt = np.full(len(dv), 0.5)
hit = np.full((len(dv), 3), np.nan)
alive = np.ones(len(dv), bool)
for _ in range(6000):
    idx = np.nonzero(alive)[0]
    if idx.size == 0:
        break
    p = cam + tt[idx, None] * dv[idx]
    inside = (p[:, 0] > 0) & (p[:, 0] < 12282) & (p[:, 2] > 0) & (p[:, 2] < 12282) & (tt[idx] < 3000)
    ter = np.where(inside, tri_sample(H, np.clip(p[:, 0], 0, 12281), np.clip(p[:, 2], 0, 12281)), -1e9)
    h = p[:, 1] <= np.maximum(ter, lvl)
    hit[idx[h]] = p[h]
    alive[idx[h | ~inside]] = False
    tt[idx] += np.maximum(0.05, tt[idx] * 0.002)
hit = hit.reshape(px.shape + (3,))
np.save(SP / 'flat1-hit.npy', hit)
np.save(SP / 'flat1-level.npy', np.array([lvl]))
ok = np.isfinite(hit[..., 0])
print('grid', hit.shape[:2], 'hits', int(ok.sum()), 'x', round(float(np.nanmin(hit[..., 0]))),
      round(float(np.nanmax(hit[..., 0]))), 'z', round(float(np.nanmin(hit[..., 2]))), round(float(np.nanmax(hit[..., 2]))))
