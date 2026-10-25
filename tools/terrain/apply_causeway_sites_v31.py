"""Replay an EV112 native-height retouch layer on its exact c0/c1 terrain input.

The committed layer retains the before/after float32 bits of the approved shore
ramps. Acceptance is checked separately by the physical-water consumer. This
tool changes only heights and the union of the causeway mask; it never changes
the underlying GIS sources or grants a PASS.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np

SCHEMA = 'ev112-causeway-height-layer.v1'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('terrain', 'layer', 'manifest', 'out'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    if a.out.suffix.lower() != '.npz':
        raise ValueError('output must have the .npz suffix')
    m = json.loads(a.manifest.read_text(encoding='utf-8-sig'))
    if m.get('schema') != SCHEMA:
        raise ValueError('unknown layer schema')
    for path, expected in ((a.terrain, m['terrain_sha256']), (a.layer, m['layer_sha256'])):
        if sha(path) != expected:
            raise ValueError('frozen input hash mismatch: ' + str(path))
    if a.out.exists():
        raise FileExistsError(a.out)
    with np.load(a.terrain, allow_pickle=False) as z:
        arrays = {k: z[k] for k in z.files}
    h = arrays['heights']
    if h.shape != (2048, 2048) or h.dtype != np.dtype('<f4') or not np.isfinite(h).all():
        raise ValueError('expected finite native 2048 square float32 terrain')
    if arrays['v31_causeway'].shape != h.shape or arrays['v31_causeway'].dtype != np.bool_:
        raise ValueError('invalid causeway mask')
    with np.load(a.layer, allow_pickle=False) as z:
        if set(z.files) != {'index', 'before', 'after'}:
            raise ValueError('unexpected layer fields')
        index, before, after = (z[k] for k in ('index', 'before', 'after'))
    if any(v.dtype != np.dtype('<u4') or v.ndim != 1 for v in (index, before, after)):
        raise ValueError('layer requires uint32 one-dimensional arrays')
    if not (len(index) == len(before) == len(after) == m['changed_vertices'] and len(index) > 0):
        raise ValueError('inconsistent layer lengths')
    if index[-1] >= h.size or not np.all(index[1:] > index[:-1]):
        raise ValueError('indices must be unique, ordered, and inside the native grid')
    if not np.array_equal(h.view('<u4').ravel()[index], before):
        raise ValueError('before-height bits mismatch')
    if not np.isfinite(after.view('<f4')).all() or np.any(before == after):
        raise ValueError('invalid or redundant after-height bits')
    h.view('<u4').ravel()[index] = after
    arrays['v31_causeway'].ravel()[index] = True
    a.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(a.out, **arrays)
    print(json.dumps(dict(output=str(a.out), sha256=sha(a.out), changed_vertices=len(index))))


if __name__ == '__main__':
    main()
