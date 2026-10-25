"""Engine views of one candidate beside another at the same poses (latest capture per pose), one JPEG per pose present
in the second, plus a manifest with the source files and their hashes.
Usage: views_pair.py OUTDIR LABEL_A=VIEWS_DIR_A LABEL_B=VIEWS_DIR_B"""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


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
    (la, da), (lb, db) = (a.split('=', 1) for a in sys.argv[2:4])
    da, db = Path(da), Path(db)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {'waits': '3 min of loading per pose (two 90 s waits) before the capture', 'pairs': []}
    for pose_dir in sorted(p for p in db.iterdir() if p.is_dir()):
        pose = pose_dir.name
        caps = sorted(pose_dir.glob('capture_*.jpg'))
        if not caps:
            continue
        cur = caps[-1]
        prev_caps = sorted((da / pose).glob('capture_*.jpg')) if (da / pose).is_dir() else []
        if prev_caps:
            prev = prev_caps[-1]
            a = label(Image.open(prev).convert('RGB').resize((960, 540)), f'{la} - {pose}')
            b = label(Image.open(cur).convert('RGB').resize((960, 540)), f'{lb} - {pose}')
            im = Image.new('RGB', (1930, 540), (255, 255, 255))
            im.paste(a, (0, 0))
            im.paste(b, (970, 0))
            dst = out / f'{pose.lower()}-{la}-vs-{lb}.jpg'
            im.save(dst, quality=88)
            manifest['pairs'].append({'pose': pose, la: {'file': str(prev), 'sha256': sha(prev)},
                                      lb: {'file': str(cur), 'sha256': sha(cur)}, 'figure': dst.name})
        else:
            dst = out / f'{pose.lower()}-{lb}.jpg'
            label(Image.open(cur).convert('RGB').resize((1280, 720)), f'{lb} - {pose}').save(dst, quality=88)
            manifest['pairs'].append({'pose': pose, lb: {'file': str(cur), 'sha256': sha(cur)}, 'figure': dst.name})
    (out / 'views-manifest.json').write_text(json.dumps(manifest, indent=1) + '\n', encoding='utf-8')
    print(json.dumps([p['figure'] for p in manifest['pairs']]))


if __name__ == '__main__':
    main()
