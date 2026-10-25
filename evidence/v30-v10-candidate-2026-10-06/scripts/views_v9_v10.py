"""Engine views of v10 beside v9 at the same poses (3 min of loading), one JPEG per pose, plus a manifest with the
source files and their hashes. Usage: views_v9_v10.py OUTDIR"""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

B = Path('E:/DayZ-Baltic-Build')
V9, V10 = B / 'v30-redesign/views', B / 'v30-v10/views'


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
    manifest = {'waits': '3 min of loading per pose (two 90 s waits) before the capture', 'pairs': []}
    for pose_dir in sorted(V10.iterdir()):
        pose = pose_dir.name
        cur = sorted(pose_dir.glob('capture_*.jpg'))[-1]
        prev_dir = V9 / pose
        if prev_dir.is_dir() and list(prev_dir.glob('capture_*.jpg')):
            prev = sorted(prev_dir.glob('capture_*.jpg'))[-1]
            a = label(Image.open(prev).convert('RGB').resize((960, 540)), f'v9 - {pose}')
            b = label(Image.open(cur).convert('RGB').resize((960, 540)), f'v10 - {pose}')
            im = Image.new('RGB', (1930, 540), (255, 255, 255))
            im.paste(a, (0, 0))
            im.paste(b, (970, 0))
            dst = out / f'{pose.lower()}-v9-vs-v10.jpg'
            im.save(dst, quality=88)
            manifest['pairs'].append({'pose': pose, 'v9': {'file': str(prev), 'sha256': sha(prev)},
                                      'v10': {'file': str(cur), 'sha256': sha(cur)}, 'figure': dst.name})
        else:
            dst = out / f'{pose.lower()}-v10.jpg'
            label(Image.open(cur).convert('RGB').resize((1280, 720)), f'v10 - {pose}').save(dst, quality=88)
            manifest['pairs'].append({'pose': pose, 'v10': {'file': str(cur), 'sha256': sha(cur)}, 'figure': dst.name})
    (out / 'views-manifest.json').write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf-8')
    print(json.dumps([p['figure'] for p in manifest['pairs']]))


if __name__ == '__main__':
    main()
