"""Contact sheets for the BALTIC-018 bed probe: lake water from the air before and after raising the Peipus bed to
1.0 m (runs c20d6f6b with the v6 surface, 7294adce with the v5 surface; v5 seen again in run 5d3900d6 for control),
and the land that renders dark while its tile textures load (the 'border' of two colours)."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

V6 = Path('E:/DayZ-Baltic-Build/v30-v6/views')
P = Path('E:/DayZ-Baltic-Build/v30-v7probe')
OUT = Path(sys.argv[1])
try:
    FONT = ImageFont.truetype('arial.ttf', 22)
except OSError:
    FONT = ImageFont.load_default()


def last(folder):
    files = sorted(Path(folder).glob('capture_*.jpg'))
    assert files, folder
    return files[-1]


def first(folder):
    files = sorted(Path(folder).glob('capture_*.jpg'))
    assert files, folder
    return files[0]


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


sheet([(last(P / 'views-v5control' / 'L269_330'), 'v5, hoy: lago 269 desde 330 m, fondo a -5,4 m (bandas)'),
       (last(P / 'views-B' / 'L269_330_later'), 'fondo a 1,0 m, mismo encuadre: agua uniforme'),
       (last(V6 / 'L269_40'), 'v6: lago 269 desde 40 m (parches grises)'),
       (last(P / 'views-B' / 'L269_40'), 'fondo a 1,0 m, desde 40 m'),
       (last(P / 'views' / 'L202_330'), 'control sin tocar, mismo run: lago 202 desde 330 m'),
       (last(P / 'views-B' / 'L269_330_SHIFT'), 'fondo a 1,0 m, desde otra posición')],
      OUT / 'fondo-de-lago-a-1m.jpg')
sheet([(last(V6 / 'LHIGH_80'), 'v6: la «frontera», en x = 3456 m (borde de tesela de 384 m)'),
       (last(P / 'views' / 'LHIGH_80'), 'otro run con la superficie del v6: oscuro a los 55 s'),
       (last(P / 'views-v5control' / 'LHIGH_80'), 'v5, hoy: verde a los 10 s'),
       (last(P / 'views-B' / 'LHIGH_80'), 'mismo terreno, superficie del v5: verde a los 10 s'),
       (last(P / 'views-B' / 'L269_330'), 'Peipus a los 40 s: tierra oscura'),
       (last(P / 'views-B' / 'L269_330_later'), 'la misma vista 2,5 min después: va cargando')],
      OUT / 'tierra-oscura-cargando.jpg')
