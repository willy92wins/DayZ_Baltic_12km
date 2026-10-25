"""Analytic positive/negative controls of actual EV90 shape predicates."""
from pathlib import Path
import hashlib, json
import numpy as np
from shape_contract import evaluate_shape, positive_prominences

r, c = np.indices((11, 11))
ramp = (r*.25+c*.125).astype(np.float32)
window = (2, 9, 2, 9)
b = ramp.copy(); b[5, 5] += 4.
tests = {}

result = evaluate_shape(b, ramp, window, (5, 5))
assert all(result['gates'].values())
tests['peak_to_inclined_ramp_passes'] = True

pit = ramp.copy(); pit[5, 5] -= 1.
result = evaluate_shape(b, pit, window, (5, 5))
assert not result['gates']['no_new_strict_minima8'] and [5, 5] in result['new_minima8']
tests['peak_to_pit_is_rejected_even_with_zero_positive_prominence'] = True

flat = ramp.copy(); flat[5:7, 5:7] = 2.
result = evaluate_shape(b, flat, window, (5, 5))
assert not result['gates']['no_new_exactly_constant_2x2_windows']
assert [5, 5] in result['new_constant_quads']
tests['new_clipped_plateau_is_rejected'] = True

almost = flat.copy(); almost[6, 6] = np.nextafter(almost[6, 6], np.float32(np.inf))
result = evaluate_shape(b, almost, window, (5, 5))
assert [5, 5] not in result['new_constant_quads']
tests['one_ulp_slope_is_not_exact_plateau'] = True

shift = ramp.copy(); shift[6, 6] += .5
result = evaluate_shape(b, shift, window, (5, 5))
assert all(result['gates'].values())
assert any(x['rc'] == [6, 6] for x in result['axes']['east_west']['new_subdominant_or_dominant_maxima'])
tests['smaller_shifted_peak_is_reported_without_old_row_veto'] = True

larger = ramp.copy(); larger[6, 6] += 5.
result = evaluate_shape(b, larger, window, (5, 5))
assert not result['gates']['fixed_population_max_prominence_nonworse_both_axes']
tests['larger_shifted_peak_is_rejected'] = True

multiple = ramp.copy()
for rc in [(3, 3), (3, 7), (7, 3), (7, 7)]: multiple[rc] += 3.
result = evaluate_shape(b, multiple, window, (5, 5))
assert result['gates']['fixed_population_max_prominence_nonworse_both_axes']
assert not result['gates']['fixed_population_sum_squares_prominence_nonworse_both_axes']
tests['distributed_peaks_fail_energy_even_when_each_peak_is_smaller'] = True

border = ramp.copy(); border[2, 2] += 1.
p = positive_prominences(border, window)
assert p['east_west'].shape == (7, 7) and p['east_west'][0, 0] == .875
assert p['north_south'][0, 0] == .75
tests['population_border_uses_external_context'] = True

for invalid in [ramp.astype(np.float64), np.where(r == 5, np.nan, ramp).astype(np.float32)]:
    try: evaluate_shape(b, invalid, window, (5, 5))
    except ValueError: pass
    else: raise AssertionError('invalid height representation accepted')
tests['non_float32_and_nonfinite_fail_closed'] = True

out = {'status': 'PASS_SHAPE_FIXTURES_ONLY', 'checks': tests,
       'source_sha256': hashlib.sha256(Path(__file__).with_name('shape_contract.py').read_bytes()).hexdigest()}
Path(__file__).with_name('shape-fixtures.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
print(json.dumps(out))
