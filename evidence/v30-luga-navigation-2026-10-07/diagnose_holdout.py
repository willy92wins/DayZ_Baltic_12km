"""Explain rejected holdout stations on unchanged native faces; no terrain edits."""
from pathlib import Path
import json
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/terrain'))
from v30_common import tri_sample, cell_planes

OUT = Path(__file__).resolve().parent
B = Path('E:/DayZ-Baltic-Build/v30-luga-navigation-20261007')
PILOT = Path('E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007')


def main():
    base = np.load('E:/DayZ-Baltic-Build/v30-v12/inland/terrain_inland.npz')
    new = np.load(B/'luga-scoped/terrain_inland.npz')
    s = np.load(B/'stations-interleaved_1m.npz')
    masks = np.load(PILOT/'luga-frozen-masks.npz')
    failed = np.flatnonzero(s['keep'] & np.isfinite(s['before']) & ~np.isfinite(s['after']))
    assert failed.tolist() == [5375, 6730]
    plane = cell_planes(base['cls'], base['level'])
    q = np.arange(-24, 24.001, .125)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    reports = []
    for row, idx in enumerate(failed):
        p, n = s['points'][idx], s['normal'][idx]
        x, z = (p[:, None] + n[:, None]*q)
        rr = np.floor((12282-z)/6).astype(int)
        cc = np.floor(x/6).astype(int)
        pl = plane[rr, cc]
        traces = {}
        for label, terrain, color in [('V12', base, '#375a7f'), ('Candidato rechazado', new, '#cb5717')]:
            h = tri_sample(terrain['heights'], x, z)
            wet = ((np.isfinite(pl)) & (h < pl)) | (h < .75)
            crosses = (q[:-1]+q[1:])[wet[:-1] != wet[1:]]/2
            traces[label] = {'ground_m': h.tolist(), 'crossings_m': crosses.tolist()}
            axes[row, 0].plot(q, h, label=label, color=color)
        axes[row, 0].plot(q, pl, color='#168d9c', linestyle='--', label='Plano de agua')
        axes[row, 0].axvspan(-8, 8, alpha=.10, color='#168d9c', label='Puerta fija ±8 m')
        axes[row, 0].set(xlabel='Distancia normal al contorno de diseño (m)', ylabel='Altura (m)',
                         title=f'Estación intercalada {idx}: perfil nativo')
        axes[row, 0].grid(alpha=.2)
        if row == 0:
            axes[row, 0].legend(fontsize=8)
        edge = p + n*s['before'][idx]
        r, c = int(np.floor((12282-edge[1])/6)), int(np.floor(edge[0]/6))
        vertices = []
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            a, b = r+dr, c+dc
            vertices.append(dict(row=a, col=b, cls=int(base['cls'][a, b]),
                                 before=float(base['heights'][a, b]), after=float(new['heights'][a, b]),
                                 allowed=bool(masks['allowed'][a, b]), corridor=bool(masks['corridor'][a, b]),
                                 frozen=bool(masks['frozen'][a, b])))
        xx, zz = np.meshgrid(np.arange(p[0]-24, p[0]+24.01, .25), np.arange(p[1]-24, p[1]+24.01, .25))
        rmap = np.floor((12282-zz)/6).astype(int)
        cmap = np.floor(xx/6).astype(int)
        water = plane[rmap, cmap]
        for label, terrain, color in [('V12', base, '#375a7f'), ('Candidato', new, '#cb5717')]:
            h = tri_sample(terrain['heights'], xx, zz)
            wet = ((np.isfinite(water)) & (h < water)) | (h < .75)
            axes[row, 1].contour(xx, zz, wet.astype(float), levels=[.5], colors=[color], linewidths=1.4)
        axes[row, 1].plot(x, z, color='#777777', linewidth=.7)
        inside = abs(q) <= 8
        axes[row, 1].plot(x[inside], z[inside], color='#111111', linewidth=3)
        axes[row, 1].plot(*p, 'ko', markersize=4)
        axes[row, 1].set(xlabel='X (m)', ylabel='Z (m)', title='Líneas de agua: V12 azul / candidato naranja', aspect='equal')
        axes[row, 1].ticklabel_format(useOffset=False)
        reports.append(dict(station=int(idx), point_xz=p.tolist(), normal=n.tolist(),
                            original_crossing_m=float(s['before'][idx]), candidate_crossing_in_8m=None,
                            q_m=q.tolist(), traces=traces, native_cell_vertices=vertices))
    fig.suptitle('Luga: mejora global, pero dos orillas salen del límite local — NO integrado', fontsize=14)
    fig.savefig(OUT/'luga-holdout-fail.png', dpi=150)
    (OUT/'holdout-diagnosis.json').write_text(json.dumps(reports, indent=2)+'\n', encoding='utf-8')
    print(json.dumps([dict(station=r['station'], old_cross=r['original_crossing_m'],
                           expanded_crossings={k:v['crossings_m'] for k,v in r['traces'].items()},
                           vertices=r['native_cell_vertices']) for r in reports], indent=2))


if __name__ == '__main__':
    main()
