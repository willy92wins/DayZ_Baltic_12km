"""BALTIC-019 evidence of 07-10-2026: the untextured-terrain share of every capture of the v11 time series (run
9b486b9a) and of the vanilla Chernarus control (run 4272a090) against the seconds since the pose's teleport, written as
JSONL, plus the time-series chart and a 2 x 2 panel of the same symptom on both maps.
Teleport times are the bridge's server clock minus 136 s (wall clock of the captures, +-3 s); NAVFREE_85 was the first
pose after launch and its start is approximate.
Usage: baltic019_figures.py REPO_ROOT OUT_DIR"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

BUILD = Path('E:/DayZ-Baltic-Build/v30-v11')
SERVER_TO_WALL = -136.0
# pose folder -> list of (teleport server time or wall 'HH:MM:SS', first capture name prefix or None)
VISITS = {
    'v11': {
        'NAVFREE_85': [('10:59:22', None)],
        'LAKE10_150': [(39877.75, None)],
        'PONDS_120': [(40144.14, None)],
        'L202_330': [(40217.63, None)],
        'BORDER_E330': [(40283.04, None)],
        'RIVER_80': [(40347.86, None)],
        'END_GRIB_40': [(40733.05, None)],
        'END_VOLKHOV_60': [(40778.94, None), (41039.05, '112145')],
        'RIVER_8': [(40973.07, None)],
    },
    'chernarus': {
        'CH_BEREZINO_80': [(41493.11, None)],
    },
}
FOLDERS = {'v11': BUILD / 'views-timeseries', 'chernarus': BUILD / 'views-timeseries-chernarus'}


def wall_seconds(t):
    if isinstance(t, str):
        h, m, s = (int(x) for x in t.split(':'))
        return h * 3600 + m * 60 + s
    return t + SERVER_TO_WALL


def capture_seconds(name):
    hh, mm, ss, ms = re.search(r'_(\d{2})(\d{2})(\d{2})_(\d{3})\.jpg$', name).groups()
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000


def main():
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    sys.path.insert(0, str(root / 'tools' / 'playtest'))
    from dark_tiles_v30 import measure
    (out / 'reports').mkdir(parents=True, exist_ok=True)
    (out / 'figures').mkdir(parents=True, exist_ok=True)
    series = {}
    for game, poses in VISITS.items():
        rows = []
        for pose, visits in poses.items():
            files = sorted((FOLDERS[game] / pose).glob('capture_*.jpg'))
            starts = [(wall_seconds(t), pref) for t, pref in visits]
            for f in files:
                tc = capture_seconds(f.name)
                visit = max(i for i, (t0, pref) in enumerate(starts)
                            if tc >= t0 and (pref is None or f.name.split('_', 2)[2] >= pref))
                m = measure(f, 0.55, 0.8, 140.0)
                row = {'game': game, 'pose': pose, 'visit': visit + 1, 'capture': f.name,
                       'seconds_since_teleport': round(tc - starts[visit][0]), 'flat_dark_share': m['flat_dark_share'],
                       'lower_mean_lum': m['lower_mean_lum']}
                rows.append(row)
                series.setdefault((game, pose, visit + 1), []).append(row)
        with open(out / 'reports' / f'dark-tiles-{game}.jsonl', 'w', encoding='utf-8', newline='\n') as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + '\n')
        print(game, len(rows), 'captures')

    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=110)
    for (game, pose, visit), rows in sorted(series.items()):
        xs = [r['seconds_since_teleport'] / 60 for r in rows]
        ys = [r['flat_dark_share'] for r in rows]
        label = f'{pose}' + (f' (visita {visit})' if visit > 1 else '')
        ax.plot(xs, ys, marker='o', ms=4, lw=1.6 if game == 'v11' else 2.6,
                ls='-' if game == 'v11' else '--', color='black' if game == 'chernarus' else None,
                label=('Chernarus ' if game == 'chernarus' else 'v11 ') + label)
    ax.axhline(0.2, color='grey', lw=0.8, ls=':')
    ax.text(0.05, 0.21, 'umbral de vista válida (0,2)', fontsize=8, color='grey')
    ax.set_xlabel('minutos desde el teletransporte')
    ax.set_ylabel('cuota de bloques planos y oscuros (mitad inferior)')
    ax.set_title('BALTIC-019: la textura tarda minutos tras cada teletransporte, también en Chernarus vanilla')
    ax.set_ylim(0, 0.7)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, ncol=2, loc='upper right')
    fig.tight_layout()
    fig.savefig(out / 'figures' / 'timeseries.png')

    panels = [
        (BUILD / 'views-timeseries/END_VOLKHOV_60/capture_20261007_112440_838.jpg',
         'Baltic v11, final del Volkhov a 60 m: tierra sin textura (2.ª visita, +3 min; 6 min en total)'),
        (BUILD / 'views-timeseries/END_VOLKHOV_4/capture_20261007_112436_362.jpg',
         'Baltic v11, mismo sitio a 4 m: detalle cercano cargado, banda media oscura'),
        (BUILD / 'views-timeseries-chernarus/CH_BEREZINO_80/capture_20261007_113615_621.jpg',
         'Chernarus vanilla, Berezino a 80 m: tierra negra, edificios y árboles sin textura (+7 min)'),
        (BUILD / 'views-timeseries-chernarus/CH_BEREZINO_4/capture_20261007_113243_563.jpg',
         'Chernarus vanilla, Berezino a 4 m del suelo: todo sin textura (+3,5 min)'),
    ]
    w, h, pad = 960, 540, 30
    sheet = Image.new('RGB', (2 * w + 24, 2 * (h + pad) + 16), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('arial.ttf', 17)
    except OSError:
        font = ImageFont.load_default()
    for i, (path, caption) in enumerate(panels):
        x, y = 8 + (i % 2) * (w + 8), 8 + (i // 2) * (h + pad)
        im = Image.open(path).convert('RGB').crop((11, 45, 1931, 1125)).resize((w, h), Image.LANCZOS)
        draw.text((x, y), caption, fill=(235, 235, 235), font=font)
        sheet.paste(im, (x, y + pad - 6))
    sheet.save(out / 'figures' / 'panels.jpg', quality=88, optimize=True)
    print('figures written', datetime.now().strftime('%H:%M:%S'))


if __name__ == '__main__':
    main()
