"""Replay the four EV112 runtime water-margin corrections on exact terrain C.

This changes native heights only. It neither changes gate thresholds nor grants
acceptance. The server's original FAIL and temporal diagnostic stay archived.
Usage: python -I apply_engine_water_margins_v31.py terrain-C.npz fresh-output.npz
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np

SOURCE_SHA256 = '0f3034c7418005f23dffd090714424763f5a96510a134c1e183af45b431184be'
# row, col, exact float32 before, exact float32 after
PATCH = (
    (796, 1721, 1.8700000047683716, 1.7200000286102295),
    (963, 1876, 1.709999918937683, 1.899999976158142),
    (631, 1685, 1.459999918937683, 1.649999976158142),
    (324, 1135, 0.6499999761581421, -0.9271936416625977),
)
PROTECTED = ('reserve', 'platform', 'narva', 'v31_bridge_cut',
             'v31_bridge_fill', 'v31_dam', 'v31_lagoon')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('terrain', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.suffix.lower() != '.npz':
        raise ValueError('output must be a fresh .npz file')
    if args.output.exists():
        raise FileExistsError(args.output)
    if hashlib.sha256(args.terrain.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('expected the exact reviewed EV112 terrain C')
    with np.load(args.terrain, allow_pickle=False) as data:
        arrays = {key: data[key] for key in data.files}
    heights = arrays['heights']
    if heights.shape != (2048, 2048) or heights.dtype != np.dtype('<f4'):
        raise ValueError('expected native 2048 square float32 terrain')
    if not np.isfinite(heights).all():
        raise ValueError('terrain must be finite')
    for row, col, before, after in PATCH:
        if float(heights[row, col]) != before:
            raise ValueError('before-height mismatch')
        if any(arrays[key][row, col] for key in PROTECTED):
            raise ValueError('protected vertex')
        if np.hypot(col * 6 - 10397.4, 12282 - row * 6 - 9421.9) <= 60:
            raise ValueError('protected 015-45 disk')
        heights[row, col] = after
    # Exclusive creation prevents a concurrent writer from being overwritten.
    with args.output.open('xb') as output:
        np.savez_compressed(output, **arrays)
    print(json.dumps(dict(output=str(args.output), changed_vertices=len(PATCH),
                         sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
                         acceptance='NOT_GRANTED')))


if __name__ == '__main__':
    main()
