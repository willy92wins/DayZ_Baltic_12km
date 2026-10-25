"""Review figures for the v10 engine views: the four PONDS_120 captures in a grid (does the dark area clear with
time?) and the RIVER_8 frame difference between two captures 6 s apart (is the change on the open water or on the
shore line?). Usage: review_v10_views.py OUTDIR"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

V10 = Path('E:/DayZ-Baltic-Build/v30-v10')


def font(size):
    try:
        return ImageFont.truetype('arial.ttf', size)
    except OSError:
        return ImageFont.load_default()


def label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 20 + 14 * len(text), 40), fill=(0, 0, 0))
    d.text((10, 6), text, fill=(255, 255, 255), font=font(26))
    return im


def client(p):
    # the saved frame is the whole window (1942x1136); the client area is at (11, 45) 1920x1080
    im = Image.open(p).convert('RGB')
    if im.size == (1942, 1136):
        im = im.crop((11, 45, 11 + 1920, 45 + 1080))
    return im


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    report = {}

    caps = sorted((V10 / 'views/PONDS_120').glob('capture_*.jpg'))
    grid = Image.new('RGB', (1930, 1090), (255, 255, 255))
    for i, p in enumerate(caps[-4:]):
        t = p.stem.split('_')[2]
        im = label(client(p).resize((960, 540)), f'PONDS_120 {t[:2]}:{t[2:4]}:{t[4:6]}')
        grid.paste(im, ((i % 2) * 970, (i // 2) * 550))
        a = np.asarray(client(p).convert('L'), dtype=np.float32)
        report.setdefault('ponds_120', []).append({'file': p.name, 'dark_share_lt60': round(float((a < 60).mean()), 4),
                                                   'mean': round(float(a.mean()), 2)})
    grid.save(out / 'ponds120-four-captures.jpg', quality=88)

    a = np.asarray(client(V10 / 'views/RIVER_8/capture_20261006_153815_855.jpg'), dtype=np.float32)
    b = np.asarray(client(V10 / 'views-flicker/RIVER_8_12frames/capture_20261006_153821_876.jpg'), dtype=np.float32)
    d = np.abs(a - b).mean(axis=2)
    h = d.shape[0]
    rows = {'sky_top_third': d[: h // 3], 'land_middle_band': d[int(h * 0.38): int(h * 0.55)],
            'water_bottom_40pct': d[int(h * 0.6):]}
    report['river_8_diff'] = {k: {'mean': round(float(v.mean()), 3), 'p99': round(float(np.percentile(v, 99)), 2),
                                  'share_gt20': round(float((v > 20).mean()), 5)} for k, v in rows.items()}
    heat = np.clip(d * 6, 0, 255).astype(np.uint8)
    hm = Image.fromarray(np.stack([heat, heat // 3, 255 - heat], axis=2))
    pair = Image.new('RGB', (1930, 540), (255, 255, 255))
    pair.paste(label(Image.fromarray(a.astype(np.uint8)).resize((960, 540)), 'RIVER_8 v10 15:38:15'), (0, 0))
    pair.paste(label(hm.resize((960, 540)), '|diff| x6 vs 15:38:21'), (970, 0))
    pair.save(out / 'river8-frame-difference.jpg', quality=88)
    (out / 'review-v10-views.json').write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
