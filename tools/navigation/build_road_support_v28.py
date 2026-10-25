"""V28: preserve accepted shoreline faces, without an extra dry-land buffer."""
from pathlib import Path
import inspect, json
import numpy as np
from affine import Affine
from rasterio.features import rasterize
from shapely.geometry import shape
import build_road_support_v27 as previous

ROOT = previous.ROOT
OUT = ROOT/'tests/regional_road_network_v28_constraints'
sha = previous.sha


def water_exclusion(root, digest):
    pins = {'water-surfaces-contour-v2.geojson': 'df860f693a1bf0115cb4af65a13cea5f8006a5a21bc9bca1d88276b83802ccdc',
            'ocean-game.json': 'c72aaafd6ee35abfcdec180135571e34b9c5eaefb42d3bca1bfbabad6493f757'}
    geos = []
    for name, expected in pins.items():
        p = root/'evidence/regional-foundation-v1'/name
        assert digest(p) == expected
        for feature in json.loads(p.read_text())['features']:
            g = shape(feature['geometry'])
            if feature['properties'].get('body', '').startswith('lake_'):
                g = g.buffer(6)
            geos.append(g)
    cells = rasterize([(g, 1) for g in geos], out_shape=(2047, 2047),
                      transform=Affine(6, 0, 0, 0, -6, 12282),
                      all_touched=True, dtype='uint8').astype(bool)
    protected = np.zeros((2048, 2048), dtype=bool)
    for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1)):
        protected[dy:2047+dy, dx:2047+dx] |= cells
    # The isolated V27 contradiction was entirely on dry land 27-29m from
    # river_contour_0029; neither vertex belongs to a protected water face.
    assert not protected.ravel()[886205] and not protected.ravel()[888253]
    return protected


def main():
    assert sha(Path(previous.__file__)) == 'e43fb95726a7d4afe47fef4feee65ad477be237adfb85da8de97e9ff55c73430'
    assert sha(ROOT/'tools/navigation/road_continuous_coverage.py') == 'a419b431d36fc1b3d047ba6affb22706732b30c2562cd25cb71e0c2618593047'
    code = inspect.getsource(previous.main)
    assert code.count('true_water30m_and_native_faces=True') == 1
    code = code.replace('true_water30m_and_native_faces=True',
                        "legacy_wet30m_and_exact_shore_faces=True")
    code = code.replace('[V27 continuous coverage]', '[V28 exact shoreline faces]')
    scope = dict(vars(previous), OUT=OUT, water_exclusion=water_exclusion)
    exec(compile(code, __file__+' [pinned V27 builder]', 'exec'), scope)
    scope['main']()


if __name__ == '__main__':
    main()
