"""Joint road-bank bounds using the frozen V33 continuous shoreline contract."""
import csv, json, math
import numpy as np
from affine import Affine
from rasterio.features import rasterize
from shapely import STRtree, polygons, intersection, get_coordinates
from shapely.geometry import shape, box
from shapely.ops import unary_union

TX = Affine(6, 0, 0, 0, -6, 12282)
PINS = {'water-surfaces-contour-v2.geojson': 'df860f693a1bf0115cb4af65a13cea5f8006a5a21bc9bca1d88276b83802ccdc',
        'ocean-game.json': 'c72aaafd6ee35abfcdec180135571e34b9c5eaefb42d3bca1bfbabad6493f757'}


def sources(root, sha):
    ev = root/'evidence/regional-foundation-v1'
    for name, digest in PINS.items():
        assert sha(ev/name) == digest
    features = json.loads((ev/'water-surfaces-contour-v2.geojson').read_text())['features']
    geos = [shape(f['geometry']) for f in features]
    ocean = shape(json.loads((ev/'ocean-game.json').read_text())['features'][0]['geometry'])
    return features, geos, ocean


def water_exclusion(root, sha):
    _, geos, ocean = sources(root, sha)
    return rasterize([(g, 1) for g in geos+[ocean]], out_shape=(2048, 2048),
                     transform=Affine(6, 0, -3, 0, -6, 12285),
                     all_touched=False, dtype='uint8').astype(bool)


def append_shore(root, sha, h, mapping, support, bound):
    design = root/'tests/regional_outline_smoothing_v33'
    assert sha(design/'shore-transition.json') == '15652b897b68e5ab3dc7927db964cae3d732ec42ae7249cbd4204eba61f5c488'
    assert sha(design/'independent-consumer.json') == '0cf85d0dd9c87c0175d10e51579bc28e6016657fe1f773317a3d5c5af8cfbfa6'
    proof = json.loads((design/'independent-consumer.json').read_text())
    assert proof['status'] == 'PASS_OFFLINE_OUTLINE_GEOMETRY' and all(proof['checks'].values())
    fs, geos, ocean = sources(root, sha)
    small = [i for i, f in enumerate(fs) if f['properties']['body'].startswith('lake_') and geos[i].buffer(-6*math.sqrt(2)).is_empty]
    assert len(small) == 23
    shores = [g.buffer(6) if f['properties']['body'].startswith('lake_') else g for f, g in zip(fs, geos)]+[ocean]
    levels = np.array([f['properties']['level_m'] for f in fs]+[1.05])
    union = unary_union(shores); original_union = unary_union(geos+[ocean])
    land = box(0, 0, 12282, 12282).difference(union)
    original_land = box(0, 0, 12282, 12282).difference(original_union)
    tree = STRtree(shores)
    affected = support[:-1, :-1] | support[:-1, 1:] | support[1:, :-1] | support[1:, 1:]
    cells = rasterize([(union.boundary, 1), (original_union.boundary, 1)],
                      out_shape=(2047, 2047), transform=TX,
                      all_touched=True, dtype='uint8').astype(bool) & affected
    cells[:2] = cells[-2:] = False; cells[:, :2] = cells[:, -2:] = False
    counts = dict(dry_plane=0, dry_sea_floor=0, lake_core=0, frozen_points=0)
    unchanged = 0

    def add(coords, limit, category, upper=False):
        nonlocal unchanged
        for x, z in coords:
            c = min(2046, max(0, int(x//6))); r = min(2046, max(0, int((12282-z)//6)))
            a = x/6-c; b = (12282-z)/6-r
            if b <= a:
                ix = np.array([r*2048+c, r*2048+c+1, (r+1)*2048+c+1]); w = np.array([1-a, a-b, b])
            else:
                ix = np.array([r*2048+c, (r+1)*2048+c+1, (r+1)*2048+c]); w = np.array([1-b, a, b-a])
            if not upper:
                w = -w
            ceiling = (limit if upper else -limit)
            if not np.any((mapping[ix] >= 0) & (abs(w) > 1e-14)):
                assert float(w@h.ravel()[ix]) <= ceiling+1e-5, (category, x, z)
                unchanged += 1
                continue
            bound(ix, w, ceiling+1e-6)
            counts[category] += 1

    rr, cc = np.where(cells); tile_ids = (rr//32)*64+cc//32
    for tile in np.unique(tile_ids):
        chosen = tile_ids == tile; r, c = rr[chosen], cc[chosen]; x, z = c*6, 12282-r*6
        extent = box(float(x.min()), float(z.min()-6), float(x.max()+6), float(z.max()))
        local, marine = land.intersection(extent), original_land.intersection(extent)
        aa, bb, dd, ee = np.c_[x, z], np.c_[x+6, z], np.c_[x+6, z-6], np.c_[x, z-6]
        for verts in (np.stack([aa, bb, dd], axis=1), np.stack([aa, dd, ee], axis=1)):
            tris = polygons(verts); pairs = tree.query(tris, predicate='intersects')
            ceiling = np.full(len(tris), 1.4)
            np.maximum.at(ceiling, pairs[0], levels[pairs[1]]+.35)
            for i, clip in enumerate(intersection(tris, local)):
                if clip.area > 1e-8:
                    add(get_coordinates(clip), float(ceiling[i]), 'dry_plane')
            for clip in intersection(tris, marine):
                if clip.area > 1e-8:
                    add(get_coordinates(clip), 1.4, 'dry_sea_floor')
    for i, f in enumerate(fs):
        if not f['properties']['body'].startswith('lake_'):
            continue
        core = geos[i].buffer(-4.5 if i in small else -6*math.sqrt(2))
        if core.is_empty:
            p = geos[i].representative_point()
            add([[p.x, p.y]], float(levels[i]-.15), 'lake_core', upper=True)
            continue
        hit = rasterize([(core, 1)], out_shape=(2047, 2047), transform=TX,
                        all_touched=True, dtype='uint8').astype(bool) & affected
        r, c = np.where(hit)
        if not len(r):
            continue
        x, z = c*6, 12282-r*6
        aa, bb, dd, ee = np.c_[x, z], np.c_[x+6, z], np.c_[x+6, z-6], np.c_[x, z-6]
        for verts in (np.stack([aa, bb, dd], axis=1), np.stack([aa, dd, ee], axis=1)):
            add(get_coordinates(intersection(polygons(verts), core)), float(levels[i]-.15), 'lake_core', upper=True)
    manifest = root/'evidence/regional-foundation-v1/consumer-reference-v5.json'
    assert sha(manifest) == '78fd406f340efcc8b3de2218ee8b8ae14b25b36ef8bf13eb9d3c206078d21b0c'
    points = root/'missions/BalticFoundationConsumerV5.BalticTrial/water-points.csv'
    assert sha(points) == json.loads(manifest.read_text())['water_file_sha256']
    rows = list(csv.reader(points.read_text().splitlines(), delimiter=';')); assert len(rows) == 81212
    for kind, index, position, old_ground, water, depth, group in rows:
        x, y, z = np.asarray(list(map(float, position.split())), dtype='float32').astype(float)
        add([[x, z]], float(water)-float(depth) if kind == 'W' else 1.25,
            'frozen_points', upper=kind == 'W')
    return dict(affected_shore_cells=int(cells.sum()), rows=counts,
                unchanged_points_checked=unchanged, numerical_slack_m=1e-6)
