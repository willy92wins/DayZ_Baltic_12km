"""Native-resolution crops of the same region of two engine views of a pose (latest capture of each), stacked.
Usage: crop_pair.py POSE l,t,r,b OUT.jpg [LABEL_A=VIEWS_DIR_A LABEL_B=VIEWS_DIR_B]  (box in client pixels, 1920x1080;
default pair: v9 and v10)"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

B = Path('E:/DayZ-Baltic-Build')
DEFAULT = [('v9', B / 'v30-redesign/views'), ('v10', B / 'v30-v10/views')]


def client(p):
    im = Image.open(p).convert('RGB')
    return im.crop((11, 45, 11 + 1920, 45 + 1080)) if im.size == (1942, 1136) else im


def main():
    pose, box, out = sys.argv[1], tuple(int(v) for v in sys.argv[2].split(',')), Path(sys.argv[3])
    pair = [(a.split('=', 1)[0], Path(a.split('=', 1)[1])) for a in sys.argv[4:6]] if len(sys.argv) > 5 else DEFAULT
    ims = []
    for tag, d in pair:
        im = client(sorted((d / pose).glob('capture_*.jpg'))[-1]).crop(box)
        dr = ImageDraw.Draw(im)
        dr.rectangle((0, 0, 20 + 14 * len(tag), 30), fill=(0, 0, 0))
        dr.text((8, 4), tag, fill=(255, 255, 255), font=ImageFont.truetype('arial.ttf', 22))
        ims.append(im)
    w, h = ims[0].size
    o = Image.new('RGB', (w, 2 * h + 8), (255, 255, 255))
    o.paste(ims[0], (0, 0))
    o.paste(ims[1], (0, h + 8))
    o.save(out, quality=90)


if __name__ == '__main__':
    main()
