"""One analytic focal height, isolated and explicitly consumer-pending."""
from pathlib import Path
import hashlib
import json
import numpy as np

HERE = Path(__file__).resolve().parent
G = HERE.parent.parent
BASE = G / 'compound-selection/run-02/candidate-terrain.npz'
B = G.parent / 'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
PLAN = HERE / 'PLAN_FOCUS_1981.md'
BOUND = HERE / 'focus-1981-univariable-bound.json'
LOCAL = HERE / 'focus-1981-local-coverage-diagnostic.json'
OUT = HERE / 'focus-unit/author-run-01'
PINS = {
    BASE: '6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d',
    B: 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    PLAN: '2ec25fb308cc41334db5ee3d529290473498295d8e7657814b208fbc6f55c4b2',
    BOUND: 'feccc8ebdb9b9ddbf0a5151e5aa49841ae980682a3c2fdd80287d48cf2eb444a',
    LOCAL: '050dae41c0ac5eb69c28e73d7a2bd219ae438009c6a489a6aad98b0b20a60051',
}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()

def readset():
    result = {str(p): sha(p) for p in PINS}
    if any(result[str(p)] != expected for p, expected in PINS.items()):
        raise RuntimeError('focal input drift')
    result[str(Path(__file__).resolve())] = sha(Path(__file__).resolve())
    return result

def main():
    before = readset()
    if OUT.exists():
        raise FileExistsError(OUT)
    with np.load(BASE, allow_pickle=False) as z:
        base = {k: z[k] for k in z.files}
    with np.load(B, allow_pickle=False) as z:
        b = z['heights']
    h = base['heights']
    assert h.dtype == np.float32 and h.shape == (2048, 2048)
    assert np.array_equal(h[832:849, 362:379], b[832:849, 362:379])
    r, c = 840, 370
    center = float(h[r, c])
    ew = center - max(float(h[r, c-1]), float(h[r, c+1]))
    ns = center - max(float(h[r-1, c]), float(h[r+1, c]))
    assert min(ew, ns) > 0
    target64 = min(center - .25*ew, center - .25*ns)
    target = np.float32(target64)
    if float(target) > target64:
        target = np.nextafter(target, np.float32(-np.inf))
    bound = json.loads(BOUND.read_text(encoding='utf-8'))
    assert bound['readset_stable'] and bound['index_reverified']
    assert float(target) == bound['float32_focus_target']['chosen_float32_height_m']
    assert 0 < center - float(target) < bound['strict_burial_bound_m_unknown_cells_physical_visible']
    result = {k: value.copy() for k, value in base.items()}
    result['heights'][r, c] = target
    assert np.array_equal(np.argwhere(result['heights'] != h), [[r, c]])
    assert all(result[k].dtype == base[k].dtype and result[k].shape == base[k].shape
               and result[k].tobytes() == base[k].tobytes()
               for k in base if k != 'heights')
    OUT.mkdir(parents=True, exist_ok=False)
    candidate = OUT / 'candidate-terrain.npz'
    with candidate.open('xb') as f:
        np.savez_compressed(f, **result)
    with np.load(candidate, allow_pickle=False) as z:
        assert set(z.files) == set(result)
        assert all(z[k].dtype == result[k].dtype and z[k].shape == result[k].shape
                   and z[k].tobytes() == result[k].tobytes() for k in result)
    after = readset()
    assert before == after
    receipt = {'status': 'SINGLE_POINT_AUTHORED_PENDING_CONSUMER',
               'candidate_path': str(candidate), 'candidate_sha256': sha(candidate),
               'base_path': str(BASE), 'base_sha256': PINS[BASE],
               'changed_rc': [[r, c]], 'height_before_m': center,
               'target64_m': target64, 'height_after_m': float(target),
               'descent_m': center-float(target),
               'source_hashes_start': before, 'source_hashes_end': after,
               'scope': 'One isolated focal change only. No consumer, map, native or visual acceptance.'}
    (OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: receipt[k] for k in ('status', 'candidate_sha256', 'height_after_m', 'descent_m')}))

if __name__ == '__main__':
    main()
