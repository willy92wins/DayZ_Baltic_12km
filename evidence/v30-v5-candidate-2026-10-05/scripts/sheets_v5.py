"""Two contact sheets for Guillermo: the v5 coast close-ups, and the edges (dam, gulf island, lake 269 from the air)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
V = Path('E:/DayZ-Baltic-Build/v30-v5/views')
SP = Path(__file__).parent
try:
    FONT = ImageFont.truetype('arial.ttf', 22)
except OSError:
    FONT = ImageFont.load_default()


def sheet(items, out, cols, w=960):
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


def one(folder):
    files = sorted((V / folder).glob('capture_*.jpg'))
    assert len(files) >= 1, folder
    return files[-1]


sheet([(one('closeups/COAST_FLAT1'), 'v5 costa FLAT1 (5134, 10339), 9 m de altura'),
       (one('closeups/COAST_FLAT2'), 'v5 costa FLAT2 (6850, 11649)'),
       (one('closeups/COAST_FLAT3'), 'v5 costa FLAT3 (4127, 9277)'),
       (one('closeups/COAST_FLAT4'), 'v5 costa FLAT4 (4763, 11938)'),
       (one('closeups/COAST_EDGE1'), 'v5 costa EDGE1 (2138, 7391), 10 m de altura')],
      SP / 'v5-costa-de-cerca.jpg', 2)
E = V / 'edges'
sheet([(SP / 'puntiagudos-2.png', 'tu foto 2'),
       (E / 'capture_20261005_134128_775.jpg', 'v5: dique de Kronstadt, tramo este, a 30 m'),
       (E / 'capture_20261005_132320_946.jpg', 'v5: el mismo tramo hasta la orilla norte, a 80 m'),
       (E / 'capture_20261005_133140_930.jpg', 'v5: isla del golfo (1365, 10554) desde 330 m: suave'),
       (E / 'capture_20261005_133549_897.jpg', 'v5: lago 269 desde 330 m: agua partida en dientes'),
       (E / 'capture_20261005_133657_700.jpg', 'v5: lago 269 desde 40 m: banda de agua con bordes rectos')],
      SP / 'v5-bordes.jpg', 2)
