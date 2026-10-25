"""BALTIC-018 evidence of 07-10-2026 (navigable water): the engine view that reproduces Guillermo's capture south of
the v11 spawn, and the cross-section of the river there from the final v11 terrain (inland/terrain_inland.npz): bed,
water level and the band where the engine sea sits. Usage: baltic018_navigable_figure.py INLAND_DIR VIEW.jpg OUT.png"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

inland, view, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
t = np.load(inland / 'terrain_inland.npz')
H, C, L = t['heights'], t['cls'], t['level']
n = H.shape[0]
z = 5250
r = n - 1 - int(round(z / 6.0))
xs = np.arange(1100, 1461, 6)
cols = np.round(xs / 6.0).astype(int)
bed = H[r, cols]
cls = C[r, cols]
lvl = np.where(cls == 3, L[r, cols], np.nan)

fig = plt.figure(figsize=(12, 10.5), dpi=100)
ax0 = fig.add_axes([0.03, 0.42, 0.94, 0.50])
im = Image.open(view).convert('RGB')
if im.size[0] > 2000:
    im = im.crop((11, 45, im.size[0] - 11, im.size[1] - 11))
ax0.imshow(im)
ax0.set_axis_off()
ax0.set_title('v11 en motor, 12 m sobre el punto de aparición (1185, 5392) mirando al SSE: agua del mar del motor '
              'con oleaje y espuma\ndentro del río navegable; franja clara de agua somera junto a la orilla',
              fontsize=10)
ax1 = fig.add_axes([0.08, 0.06, 0.88, 0.30])
river = ~np.isnan(lvl) & (bed < np.nan_to_num(lvl))
sea = river & (bed < 0.75)
ax1.fill_between(xs, -8, bed, color='#8b7355', alpha=0.85, label='terreno (fondo y orillas)')
ax1.fill_between(xs, bed, np.nan_to_num(lvl), where=river, color='#9ecae1', alpha=0.7,
                 label='agua del río navegable (clase 3), a 2,58 m')
ax1.fill_between(xs, bed, 0.75, where=sea, color='#08519c', alpha=0.75,
                 label='bajo el nivel del mar del motor (~0,75 m): ahí el motor dibuja el mar')
ax1.plot(xs[river], np.full(river.sum(), 1.0), color='grey', lw=1.0, ls='--',
         label='fondo de 1,0 m del resto del agua (lagos, ríos, arroyos)')
ax1.set_xlim(1100, 1460)
ax1.set_ylim(-5, 14)
ax1.set_xlabel('x (m), sección oeste-este a z = 5250, 140 m al sur del punto de aparición')
ax1.set_ylabel('altura (m)')
ax1.grid(alpha=0.3)
ax1.legend(fontsize=8, loc='upper right')
fig.savefig(out)
print(out)
