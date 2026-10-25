"""Side-by-side engine views: one row per pose, the reference capture on the left and the candidate on the right,
client area only (the 1920 x 1080 frame inside the window capture), each scaled to --width px. Missing references
leave the left cell blank. Usage: engine_pairs.py OUT.png --pair POSE REF.jpg|- CAND.jpg [...] [--labels A B]"""
import argparse

from PIL import Image, ImageDraw, ImageFont


def client(p):
    im = Image.open(p).convert('RGB')
    return im.crop((11, 45, 11 + 1920, 45 + 1080)) if im.size == (1942, 1136) else im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--pair', nargs=3, action='append', metavar=('POSE', 'REF', 'CAND'), required=True)
    ap.add_argument('--labels', nargs=2, default=['v10b', 'v11'])
    ap.add_argument('--width', type=int, default=960)
    a = ap.parse_args()
    w = a.width
    h = w * 1080 // 1920
    pad = 28
    sheet = Image.new('RGB', (2 * w + 3 * 8, len(a.pair) * (h + pad) + 8), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('arial.ttf', 18)
    except OSError:
        font = ImageFont.load_default()
    for i, (pose, ref, cand) in enumerate(a.pair):
        y = 8 + i * (h + pad)
        for j, (path, label) in enumerate(((ref, a.labels[0]), (cand, a.labels[1]))):
            x = 8 + j * (w + 8)
            draw.text((x, y), f'{pose} - {label}', fill=(235, 235, 235), font=font)
            if path != '-':
                sheet.paste(client(path).resize((w, h), Image.LANCZOS), (x, y + pad - 6))
    sheet.save(a.out, optimize=True)
    print(a.out, sheet.size)


if __name__ == '__main__':
    main()
