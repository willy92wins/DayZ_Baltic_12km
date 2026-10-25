"""Overlay on the FLAT1 close-up: what each pixel hits in the v5 terrain (sea, pond and its depth, land and its
height), to check whether the 'overflowing' water sheet is the sea or a pond."""
from pathlib import Path

import numpy as np
from PIL import Image

SP = Path(__file__).parent
hit = np.load(SP / 'flat1-hit.npy')
lvl = float(np.load(SP / 'flat1-level.npy')[0])
t = np.load('E:/DayZ-Baltic-Build/v30-v5/coast/terrain_coast.npz')
h, cls, lev = t['heights'].astype(float), t['cls'], t['level'].astype(float)
ok = np.isfinite(hit[..., 0])
cx = np.clip(np.round(np.nan_to_num(hit[..., 0]) / 6).astype(int), 0, 2047)
rz = np.clip(np.round((12282 - np.nan_to_num(hit[..., 2])) / 6).astype(int), 0, 2047)
hv, cv, lv = h[rz, cx], cls[rz, cx], lev[rz, cx]
rgb = np.zeros(hit.shape[:2] + (3,), np.uint8)
sea = ok & (np.isin(cv, (1, 4)) | (hv < lvl))
pond = ok & ~sea & (cv > 0)
depth = np.where(pond, lv - hv, 0)
land = ok & ~sea & ~pond
rgb[sea] = (20, 40, 160)
rgb[pond & (depth >= 0.6)] = (0, 150, 255)
rgb[pond & (depth >= 0.25) & (depth < 0.6)] = (0, 230, 230)
rgb[pond & (depth < 0.25)] = (255, 255, 0)
rgb[land & (hv < 1.6)] = (255, 120, 0)
rgb[land & (hv >= 1.6) & (hv < 2.2)] = (90, 160, 60)
rgb[land & (hv >= 2.2)] = (40, 90, 30)
ov = Image.fromarray(rgb).resize((1273, 701), Image.NEAREST)
cap = Image.open(SP / 'flat1-client.png').convert('RGB')
blend = Image.blend(cap, ov, 0.45)
out = Image.new('RGB', (1273, 701 * 2 + 6), (255, 255, 255))
out.paste(cap, (0, 0))
out.paste(blend, (0, 707))
out.save(SP / 'flat1-overlay.jpg', quality=88)
print('pond depth under the oval area: share <0.25 m', round(float((pond & (depth < 0.25)).sum() / max(pond.sum(), 1)), 3),
      'pond px', int(pond.sum()), 'pond levels', np.unique(lv[pond]).round(2))
print('legend: dark blue sea; blue pond >=0.6 m deep; cyan 0.25-0.6; yellow <0.25; orange land <1.6; green land')
