"""Before/after of the Kronstadt dam: v5 heights and 0.75 m waterline (red) against v6 (blue), with the crest mask."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

v5 = np.load('E:/DayZ-Baltic-Build/v30-v5/coast/terrain_coast.npz')
v6 = np.load('E:/DayZ-Baltic-Build/v30-v6/causeway/terrain_causeway.npz')
m = np.load('E:/DayZ-Baltic-Build/v30-v6/causeway/masks.npz')
wins = [(6600, 10120, 7000, 10600), (6950, 10580, 7650, 10800)]
fig, axes = plt.subplots(2, 2, figsize=(18, 14), dpi=90)
for row, (x0, z0, x1, z1) in enumerate(wins):
    c0, c1 = int(x0 / 6), int(x1 / 6) + 1
    r0, r1 = int((12282 - z1) / 6), int((12282 - z0) / 6) + 1
    X = np.arange(c0, c1) * 6.0
    Z = 12282.0 - np.arange(r0, r1) * 6.0
    for col, (t, name) in enumerate(((v5, 'v5'), (v6, 'v6'))):
        ax = axes[row, col]
        h = t['heights'][r0:r1, c0:c1].astype(float)
        ax.imshow(h, extent=(X[0], X[-1], Z[-1], Z[0]), cmap='terrain', vmin=-3, vmax=4, origin='upper',
                  interpolation='nearest')
        ax.contour(X, Z, v5['heights'][r0:r1, c0:c1], levels=[0.75], colors='red', linewidths=0.9)
        if name == 'v6':
            ax.contour(X, Z, h, levels=[0.75], colors='blue', linewidths=1.2)
            ax.contour(X, Z, m['crest'][r0:r1, c0:c1].astype(float), levels=[0.5], colors='k', linewidths=0.6,
                       linestyles='dotted')
        ax.set_title(f'{name}: rojo línea de agua v5 (0,75 m), azul v6; punteado negro cresta del v6', fontsize=9)
        ax.set_xlim(x0, x1)
        ax.set_ylim(z0, z1)
        ax.set_aspect('equal')
fig.tight_layout()
fig.savefig('C:/Users/guill/AppData/Local/Temp/claude/C--Users-guill-OneDrive-Documentos-DayZ-Projects-DayZ-Baltic-12km-dev--claude-worktrees-codex-handoff-review-74f290/14ffcdc3-48af-41ae-8838-30ace879bcdd/scratchpad/causeway-before-after.png')
print('ok')
