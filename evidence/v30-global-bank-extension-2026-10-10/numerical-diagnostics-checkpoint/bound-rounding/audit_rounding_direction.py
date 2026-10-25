"""Read-only audit of the frozen run-05 bound rounding; no solver/terrain output."""
from pathlib import Path
import hashlib
import json
import numpy as np

ROOT = Path('E:/DayZ-Baltic-Build')
G = ROOT/'v30-global-bank-extension-20261010'
HERE = G/'global-operator-prototype/global-sizing-ev95'
OUT = HERE/'rounding-direction-audit.json'
INPUTS = {
    'H': (G/'build-wide-slope/candidate/terrain.npz', '40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a'),
    'B': (ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz', 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'),
    'O': (ROOT/'v30-narva-dry-bank-relief-20261010/candidate/terrain.npz', 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'),
    'P': (ROOT/'v30-narva-dry-bank-relief-20261010/candidate/plane.npy', '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'),
    'F': (ROOT/'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy', 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'),
    'masks': (HERE/'run-05/masks.npz', '8f5959308923263538440d29dd93960c5331bc8f13c88b61590380c17d6cdfff'),
    'source': (HERE/'run-05/preflight_global_resources.py', '9b997a3ebf64b78828955476eed4c4c57cfc1ca77d998e407adda17ea5a6bfb7'),
}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def inward(raw, lower):
    raw = np.asarray(raw, np.float64)
    result = raw.astype(np.float32)
    wrong = (result.astype(np.float64) < raw) if lower else (result.astype(np.float64) > raw)
    result[wrong] = np.nextafter(result[wrong], np.float32(np.inf if lower else -np.inf))
    return result

def legacy_outward(raw, lower):
    raw = np.asarray(raw, np.float64)
    result = raw.astype(np.float32)
    wrong = (result.astype(np.float64) > raw) if lower else (result.astype(np.float64) < raw)
    result[wrong] = np.nextafter(result[wrong], np.float32(-np.inf if lower else np.inf))
    return result

def require(ok, message):
    if not ok:
        raise ValueError(message)

def main():
    require(not OUT.exists(), 'Preserve existing audit')
    start = {key: sha(path) for key, (path, _) in INPUTS.items()}
    for key, (_, wanted) in INPUTS.items():
        require(start[key] == wanted, 'Input hash mismatch: '+key)
    f32 = np.array([-12.3, -1.0, 0.0, 1.0, 6.675, 180.5], np.float32)
    toward = np.nextafter(f32, np.float32(np.inf)).astype(np.float64)
    middle = f32.astype(np.float64) + (toward-f32.astype(np.float64))*0.4
    raw = np.concatenate([middle, f32.astype(np.float64)])
    lower, upper = inward(raw, True), inward(raw, False)
    require(np.all(lower.astype(np.float64) >= raw), 'lower must never undercut the real bound')
    require(np.all(upper.astype(np.float64) <= raw), 'upper must never exceed the real bound')
    require(np.all(np.nextafter(lower, np.float32(-np.inf)).astype(np.float64) < raw), 'lower not closest inward')
    require(np.all(np.nextafter(upper, np.float32(np.inf)).astype(np.float64) > raw), 'upper not closest inward')
    require(np.any(legacy_outward(raw, True).astype(np.float64) < raw), 'legacy lower negative fixture did not fail')
    require(np.any(legacy_outward(raw, False).astype(np.float64) > raw), 'legacy upper negative fixture did not fail')
    heights = {}
    for key in ('H', 'B', 'O'):
        with np.load(INPUTS[key][0], allow_pickle=False) as z:
            heights[key] = z['heights'].astype(np.float64)
    H, B, O = (heights[key] for key in ('H', 'B', 'O'))
    P = np.load(INPUTS['P'][0], mmap_mode='r', allow_pickle=False)
    F = np.load(INPUTS['F'][0], mmap_mode='r', allow_pickle=False)
    require(P.dtype == F.dtype == np.dtype('float64'), 'Water levels must preserve binary64')
    levels = np.full(H.shape, .85, np.float64)
    pv = np.nan_to_num(P, nan=.85)
    for i, (dr, dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
        level = np.maximum(.85, np.maximum(pv, np.nan_to_num(F[:,:,i], nan=.85)))
        np.maximum(levels[dr:dr+2047,dc:dc+2047], level, out=levels[dr:dr+2047,dc:dc+2047])
    del pv, level
    lo_real = np.maximum.reduce((H-2., np.minimum(O,levels+1e-4), np.minimum(O,1.8), O-2.))
    hi_real = np.minimum.reduce((H+2., O+2., B+.5))
    old_lo, old_hi = legacy_outward(lo_real, True), legacy_outward(hi_real, False)
    lo, hi = inward(lo_real, True), inward(hi_real, False)
    with np.load(INPUTS['masks'][0], allow_pickle=False) as z:
        variables = z['ev95_variable'].astype(bool)
        reason = z['reason_bits']
    old_bad, new_bad = old_lo>old_hi, lo>hi
    require(np.array_equal((reason & 1024)!=0, old_bad), 'Frozen infeasibility mask does not reproduce')
    report = {
        'status': 'ROUNDING_DIRECTION_AUDITED_NO_SOLVE',
        'source_sha256': sha(Path(__file__)),
        'readset_start': start,
        'fixtures': {'closest_inward_lower': True, 'closest_inward_upper': True,
                     'legacy_lower_violation_detected': True, 'legacy_upper_violation_detected': True},
        'bug': 'run-05 inward32 is outward-rounded; run-05 review inward wording is false',
        'full_grid': {'lower_values_different': int(np.count_nonzero(lo!=old_lo)),
                      'upper_values_different': int(np.count_nonzero(hi!=old_hi)),
                      'old_infeasible': int(old_bad.sum()), 'correct_infeasible': int(new_bad.sum()),
                      'infeasibility_mask_changed': int(np.count_nonzero(old_bad!=new_bad))},
        'frozen_domain': {'variables': int(variables.sum()),
                          'lower_values_different': int(np.count_nonzero(variables & (lo!=old_lo))),
                          'upper_values_different': int(np.count_nonzero(variables & (hi!=old_hi))),
                          'correct_infeasible_variables': int(np.count_nonzero(variables & new_bad)),
                          'domain_counts_still_valid': bool(not np.any(old_bad!=new_bad)),
                          'EV95_outside_correct_bounds': int(np.count_nonzero(variables & ((H<lo)|(H>hi))))},
        'limits': 'No new bounds policy, terrain, global solve or mask written. Benchmark may reuse counts only if domain_counts_still_valid.'
    }
    report['readset_end'] = {key: sha(path) for key,(path,_) in INPUTS.items()}
    require(report['readset_start'] == report['readset_end'], 'Readset changed')
    OUT.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
