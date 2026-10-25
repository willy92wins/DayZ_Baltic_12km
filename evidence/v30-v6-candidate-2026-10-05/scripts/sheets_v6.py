"""Contact sheets for the v6 candidate: v5 against v6 at the same poses (dam and FLAT1), and the lake-water checks of
BALTIC-018 (lake 269 from two positions, a lake whose bed stays above the sea, and a vanilla Chernarus pond)."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

V5 = Path('E:/DayZ-Baltic-Build/v30-v5/views')
V6 = Path('E:/DayZ-Baltic-Build/v30-v6/views')
OUT = Path(sys.argv[1])
try:
    FONT = ImageFont.truetype('arial.ttf', 22)
except OSError:
    FONT = ImageFont.load_default()


def last(folder):
    files = sorted(Path(folder).glob('capture_*.jpg'))
    assert files, folder
    return files[-1]


def sheet(items, out, cols=2, w=960):
    tiles = []
    for path, label in items:
        im = Image.open(path).convert('RGB')
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, w, 34], fill=(0, 0, 0))
        d.text((10, 5), label, fill=(255, 255, 255), font=FONT)
        tiles.append(im)
    h = max(t.height for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    canvas = Image.new('RGB', (cols * w + (cols - 1) * 8, rows * h + (rows - 1) * 8), (255, 255, 255))
    for i, t in enumerate(tiles):
        canvas.paste(t, ((i % cols) * (w + 8), (i // cols) * (h + 8)))
    canvas.save(out, quality=88)
    print(out, canvas.size)


E5 = V5 / 'edges'
sheet([(E5 / 'capture_20261005_134128_775.jpg', 'v5: dique, tramo este, a 30 m'),
       (last(V6 / 'DAM_E_30'), 'v6: el mismo encuadre'),
       (E5 / 'capture_20261005_132320_946.jpg', 'v5: tramo este hasta la orilla norte, a 80 m'),
       (last(V6 / 'DAM_E_80'), 'v6: el mismo encuadre'),
       (last(V6 / 'DAM_E_LOW'), 'v6: tramo este a 9 m, como tu foto 3'),
       (last(V6 / 'DAM_S_40'), 'v6: tramo sur desde el oeste, a 40 m'),
       (V5 / 'closeups' / 'COAST_FLAT1' / 'capture_20261005_134144_530.jpg', 'v5: FLAT1, fondo del estanque con hierba'),
       (last(V6 / 'COAST_FLAT1'), 'v6: FLAT1, fondo de grava bajo el agua')],
      OUT / 'v6-dique-y-flat1.jpg')
sheet([(E5 / 'capture_20261005_133549_897.jpg', 'v5: lago 269 desde 330 m'),
       (last(V6 / 'L269_330'), 'v6: lago 269, mismo encuadre'),
       (last(V6 / 'L269_330_SHIFT'), 'v6: lago 269 desde otra posición, mismo blanco'),
       (last(V6 / 'L269_40'), 'v6: lago 269 desde 40 m'),
       (last(V6 / 'LHIGH_330'), 'v6: lago a 4,38 m con fondo sobre el mar, desde 330 m'),
       (last(V6 / 'LHIGH_80'), 'v6: el mismo lago desde 80 m'),
       (last(V6 / 'CH_330'), 'Chernarus: estanque vanilla a 2,78 m desde 330 m'),
       (last(V6 / 'CH_40'), 'Chernarus: el mismo estanque desde 40 m')],
      OUT / 'v6-agua-de-lagos.jpg')
