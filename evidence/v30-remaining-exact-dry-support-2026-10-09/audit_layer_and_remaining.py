"""Replay the saved edit and account for every original EV59 dry target."""
from pathlib import Path
import csv, hashlib, json
import numpy as np

B = Path(__file__).parent
R = B.parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source = R / 'v30-exact-dry-support-20261009/candidate/terrain.npz'
candidate = B / 'candidate/terrain.npz'
original = R / 'v30-strict-dry-composition-20261009/candidate/terrain.npz'
a = dict(np.load(source))
v = dict(np.load(candidate))
layer = dict(np.load(B / 'terrain-delta.npz'))
rr, cc = layer['row'], layer['col']
assert len(set(zip(rr.tolist(), cc.tolist()))) == len(rr)
assert np.array_equal(a['heights'][rr, cc], layer['before'])
a['heights'][rr, cc] = layer['after']
assert set(a) == set(v)
assert all(np.array_equal(a[k], v[k], equal_nan=True) for k in a)
replay = B / 'layer-replay'
replay.mkdir(exist_ok=False)
np.savez_compressed(replay / 'terrain.npz', **a)
assert sha(replay / 'terrain.npz') == sha(candidate)
scope = dict(np.load(R / 'v30-low-dry-domain-classification-20261009/domain.npz'))
constraints = dict(np.load(B / 'constraints.npz'))
remaining = scope['editable'] & (v['heights'] < 1.79999)
expected = np.zeros(v['heights'].shape, dtype=bool)
with (B / 'protected-remaining.csv').open(newline='') as f:
    rows = list(csv.DictReader(f))
for row in rows:
    r, c = int(row['row']), int(row['col'])
    assert not expected[r, c]
    expected[r, c] = True
assert np.array_equal(remaining, expected)
assert remaining.sum() == len(rows) == 145
assert not (remaining & ~constraints['fixed']).any()
large = constraints['large_lake_banks']
border = np.zeros(remaining.shape, dtype=bool)
border[:11] = border[-11:] = True
border[:, :11] = border[:, -11:] = True
assert not (remaining & ~(large | border)).any()
old = np.load(original)['heights']
delta = v['heights'].astype(float) - old.astype(float)
assert delta.min() >= -1e-6 and delta.max() <= .400001
assert not (remaining & (delta != 0)).any()
report = dict(
    status='PASS_EXACT_LAYER_AND_DRY_TARGET_ACCOUNTING',
    source_sha256=sha(source), candidate_sha256=sha(candidate),
    layer_sha256=sha(B / 'terrain-delta.npz'), replay_byte_exact=True,
    changed_in_ev71=len(rr), changed_since_ev61=int((delta != 0).sum()),
    max_cumulative_uplift_m=float(delta.max()),
    original_ev59_targets=int(scope['editable'].sum()),
    targets_at_floor=int((scope['editable'] & ~remaining).sum()),
    remaining_protected=int(remaining.sum()), remaining_editable=0,
    remaining_large_lake=int((remaining & large).sum()),
    remaining_border=int((remaining & border).sum()),
    remaining_both=int((remaining & border & large).sum()),
    limits=[
        'Accounts for the EV59 dry-target set, not every shoreline vertex or every graphical defect.',
        'Protected large-lake banks and map border stay unchanged; no policy exception is inferred.',
        'No native execution or artistic acceptance is claimed.'
    ])
(B / 'layer-replay.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
