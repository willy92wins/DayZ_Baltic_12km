"""Cross-sections of the terrain on the native triangles across water, for several terrains, with the water level:
what the steeper shore profile does to depth and banks. Usage: sections.py OUT.png label=terrain.npz ... --
name:x0,z0,x1,z1 [...]"""
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees'
                   r'\codex-handoff-review-74f290\tools\terrain')
from v30_common import tri_sample  # noqa: E402

out = sys.argv[1]
k = sys.argv.index('--')
terrains = [a.split('=', 1) for a in sys.argv[2:k]]
lines = [(s.split(':')[0], [float(v) for v in s.split(':')[1].split(',')]) for s in sys.argv[k + 1:]]
loaded = [(lab, np.load(p)) for lab, p in terrains]
fig, axes = plt.subplots(len(lines), 1, figsize=(10, 3.2 * len(lines)), squeeze=False)
colours = ['#7f7f7f', '#1f77b4', '#d62728', '#2ca02c']
for ax, (name, (x0, z0, x1, z1)) in zip(axes[:, 0], lines):
    n = int(np.hypot(x1 - x0, z1 - z0) / 0.25) + 1
    xs, zs = np.linspace(x0, x1, n), np.linspace(z0, z1, n)
    s = np.hypot(xs - x0, zs - z0)
    for (lab, t), col in zip(loaded, colours):
        ax.plot(s, tri_sample(t['heights'].astype(np.float64), xs, zs), color=col, lw=1.4, label=lab)
    t = loaded[-1][1]
    lv = t['level'].astype(np.float64)
    r = np.clip(np.rint((12282 - zs) / 6).astype(int), 0, t['level'].shape[0] - 1)
    c = np.clip(np.rint(xs / 6).astype(int), 0, t['level'].shape[1] - 1)
    wl = lv[r, c]
    ax.plot(s, wl, color='#17becf', lw=1.0, ls='--', label='water level')
    ax.set_title(f'{name}: ({x0:.0f}, {z0:.0f}) -> ({x1:.0f}, {z1:.0f})', fontsize=9)
    ax.set_xlabel('m along the section')
    ax.set_ylabel('height (m)')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc='upper right')
fig.tight_layout()
fig.savefig(out, dpi=110)
print(out)
