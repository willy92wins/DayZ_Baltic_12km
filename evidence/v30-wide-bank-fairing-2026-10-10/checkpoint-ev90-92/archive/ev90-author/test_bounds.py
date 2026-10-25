"""Bounds are verified independently against exact real inequalities."""
from pathlib import Path
import hashlib, json
import numpy as np
from author_ev90 import inward_bounds

one = np.float32(1.)
nxt = np.nextafter(one, np.float32(np.inf))
mid = (float(one)+float(nxt))/2
l, u = inward_bounds([1., mid, 1.], [2., 2., mid])
assert np.array_equal(l, [1., float(nxt), 1.])
assert np.array_equal(u, [2., 2., 1.])
for bad in [(mid, mid), (np.nan, 2.), (1., np.inf), (1e39, 2e39)]:
    try: inward_bounds([bad[0]], [bad[1]])
    except ValueError: pass
    else: raise AssertionError('invalid/unrepresentable interval accepted')
for endpoint in (l, u):
    h = endpoint.astype(np.float32).astype(np.float64)
    assert np.all(h >= l) and np.all(h <= u)
out = {'status': 'PASS_BOUNDS_FIXTURES_ONLY',
       'cases': ['exact_bounds', 'lower_rounds_inward', 'upper_rounds_inward',
                 'empty_after_rounding', 'nan_rejected', 'infinity_rejected',
                 'unrepresentable_rejected', 'both_exact_endpoints_retained'],
       'author_sha256': hashlib.sha256(Path(__file__).with_name('author_ev90.py').read_bytes()).hexdigest()}
Path(__file__).with_name('bounds-fixtures.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
print(json.dumps(out))
