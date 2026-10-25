"""Engine views of v9 beside the previous candidate at the same pose (3 min of loading), one JPEG per pose, plus a
manifest with the source files and their hashes. Usage: views_side_by_side.py OUTDIR"""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

B = Path('E:/DayZ-Baltic-Build')
V9 = B / 'v30-redesign/views'
PAIRS = [  # pose, previous label, previous capture
    ('RIVER_80', 'v8', B / 'v30-v8/views/RIVER_80/capture_20261006_013927_801.jpg'),
    ('RIVER_8', 'v8', B / 'v30-v8/views/RIVER_8/capture_20261006_014157_560.jpg'),
    ('NAVFREE_85', 'v8', B / 'v30-v8/views/NAVFREE_85/capture_20261006_013650_049.jpg'),
    ('BORDER_E330', 'v8c (sintesis)', B / 'v30-v8/views-c2/BORDER_E330_3min/capture_20261006_030104_987.jpg'),
    ('L106_330', 'v8c (sintesis)', B / 'v30-v8/views-c2/L106_330_3min/capture_20261006_031234_535.jpg'),
    ('L202_330', 'v7d', B / 'v30-v7/views-d/L202_330/capture_20261006_002607_130.jpg'),
    ('NAV_330', 'v7d', B / 'v30-v7/views-d/NAV_330/capture_20261006_003145_963.jpg'),
]
SINGLE = ['L288_330', 'L288_60']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def label(im, text):
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype('arial.ttf', 28)
    except OSError:
        font = ImageFont.load_default()
    d.rectangle((0, 0, 20 + 15 * len(text), 44), fill=(0, 0, 0))
    d.text((10, 6), text, fill=(255, 255, 255), font=font)
    return im


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    manifest = {'waits': '3 min of loading per pose (two 90 s waits) before the capture',
                'run_v9': '6d421b36', 'mod_v9': '@DayZ_Baltic_V9Candidate world b4f68bf1 + water a1abc83f', 'pairs': []}
    for pose, prev_label, prev in PAIRS:
        cur = sorted((V9 / pose).glob('capture_*.jpg'))[-1]
        a = label(Image.open(prev).convert('RGB').resize((960, 540)), f'{prev_label} - {pose}')
        b = label(Image.open(cur).convert('RGB').resize((960, 540)), f'v9 - {pose}')
        im = Image.new('RGB', (1930, 540), (255, 255, 255))
        im.paste(a, (0, 0))
        im.paste(b, (970, 0))
        dst = out / f'{pose.lower()}-{prev_label.split()[0]}-vs-v9.jpg'
        im.save(dst, quality=88)
        manifest['pairs'].append({'pose': pose, 'previous': {'label': prev_label, 'file': str(prev), 'sha256': sha(prev)},
                                  'v9': {'file': str(cur), 'sha256': sha(cur)}, 'figure': dst.name})
    for pose in SINGLE:
        cur = sorted((V9 / pose).glob('capture_*.jpg'))[-1]
        dst = out / f'{pose.lower()}-v9.jpg'
        label(Image.open(cur).convert('RGB').resize((1280, 720)), f'v9 - {pose}').save(dst, quality=88)
        manifest['pairs'].append({'pose': pose, 'v9': {'file': str(cur), 'sha256': sha(cur)}, 'figure': dst.name})
    (out / 'views-manifest.json').write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf-8')
    print(json.dumps([p['figure'] for p in manifest['pairs']]))


if __name__ == '__main__':
    main()
