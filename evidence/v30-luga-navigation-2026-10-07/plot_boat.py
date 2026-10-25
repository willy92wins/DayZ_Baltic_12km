"""Plot verified runtime trajectories against the routes frozen before launch."""
from pathlib import Path
import json
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    out = Path(__file__).resolve().parent
    reference = json.loads((out/'boat-reference.json').read_text())
    report = json.loads((out/'boat-verification.json').read_text())
    rows = {}
    for line in (out/'boat-runtime.log').read_text().splitlines():
        f = line.split(';')
        if f[0] != 'B':
            continue
        xyz = list(map(float, re.fullmatch(r'<(-?\d+\.\d{6}),\s*(-?\d+\.\d{6}),\s*(-?\d+\.\d{6})>', f[22]).groups()))
        rows.setdefault(int(f[1]), []).append([xyz[0], xyz[2], float(f[2]), float(f[8]), float(f[20])])
    fig, axes = plt.subplots(1, 3, figsize=(13, 5.4), constrained_layout=True)
    labels = ['Oeste · Narva', 'Luga alto', 'Luga bajo']
    metrics = []
    for sector, ax in enumerate(axes):
        forward, reverse = 2*sector, 2*sector+1
        case = reference['cases'][forward]
        route = np.asarray(case['waypoints_xz'])
        origin = route[0]
        ax.plot(*(route-origin).T, color='#555555', linestyle='--', linewidth=2, label='Ruta fijada')
        for ident, label, color in [(forward, 'Ida', '#14827c'), (reverse, 'Vuelta', '#9543a0')]:
            a = np.array(rows[ident])
            ax.plot(*(a[:, :2]-origin).T, color=color, linewidth=1, label=label)
            r = report['cases'][ident]
            metrics.append(dict(case=ident, status=r['status'], health_min=float(a[:, 3].min()),
                                propeller_water_depth_range_m=[float(a[:, 4].min()), float(a[:, 4].max())],
                                sampled_seconds=float(a[-1, 2]-a[0, 2])))
        pair = report['cases'][forward:reverse+1]
        status = 'PASS' if all(v['status']=='PASS' for v in pair) else 'FAIL'
        ax.set(title=f'{labels[sector]} — {status}\nCalado nominal mínimo: {case["dense_nominal_depth_min_m"]:.2f} m',
               xlabel=f'X relativo a {origin[0]:.1f} m', ylabel=f'Z relativo a {origin[1]:.1f} m', aspect='equal')
        relative = route-origin
        centre = (relative.min(axis=0)+relative.max(axis=0))/2
        half = np.ptp(relative, axis=0).max()*.62
        ax.set_xlim(centre[0]-half, centre[0]+half)
        ax.set_ylim(centre[1]-half, centre[1]+half)
        ax.grid(alpha=.2)
        if sector == 0:
            ax.legend(fontsize=8)
        max_error = max(v['max_corridor_distance_m'] for v in pair)
        ax.text(.02, .02, f'Desvío máximo: {max_error:.2f} m', transform=ax.transAxes, fontsize=9,
                bbox=dict(facecolor='white', alpha=.85, edgecolor='none'))
    fig.suptitle('V12 · recorridos reales de lancha vacía, sin imponer posición durante el movimiento', fontsize=13)
    fig.savefig(out/'boat-trajectories.png', dpi=150)
    (out/'boat-motion-summary.json').write_text(json.dumps(dict(cases=metrics,
        note='Propeller water depth is the logged point query, not total channel draught.'), indent=2)+'\n', encoding='utf-8')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
