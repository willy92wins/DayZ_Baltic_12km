"""Contact sheets for the v7 candidate (run 06e14fcf): lake water and shores against v6 and the bed probe, and the
lake 259 islands from 60 and 10 m with the offline plot of their waterline."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

V6 = Path('E:/DayZ-Baltic-Build/v30-v6/views')
PR = Path('E:/DayZ-Baltic-Build/v30-v7probe')
V7 = Path('E:/DayZ-Baltic-Build/v30-v7/views')
OUT = Path(sys.argv[1])
PLOT = Path(sys.argv[2])
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


sheet([(last(V6 / 'L269_330'), 'v6: Peipus desde 330 m'),
       (last(V7 / 'L269_330'), 'v7: el mismo encuadre (fondo a 1,0 m, orillas perfiladas)'),
       (last(PR / 'views' / 'L202_330'), 'lago 202 sin tocar, desde 330 m (run de la prueba)'),
       (last(V7 / 'L202_330'), 'v7: lago 202, el mismo encuadre'),
       (last(V6 / 'LHIGH_80'), 'v6: lago LHIGH desde 80 m (la «frontera»)'),
       (last(V7 / 'LHIGH_80'), 'v7: el mismo encuadre, tras 90 s')],
      OUT / 'v7-lagos.jpg')
sheet([(last(V7 / 'L259_60'), 'v7: islas del lago 259 desde 60 m'),
       (last(V7 / 'L259_10'), 'v7: la isla grande desde 10 m'),
       (last(V7 / 'L106_330'), 'v7: lago 106 (0,43 m de agua) desde 330 m'),
       (last(V7 / 'L106_40'), 'v7: lago 106 desde 40 m'),
       (PLOT, 'línea de agua del motor: v6 en rojo, v7 en azul')],
      OUT / 'v7-islas.jpg')
