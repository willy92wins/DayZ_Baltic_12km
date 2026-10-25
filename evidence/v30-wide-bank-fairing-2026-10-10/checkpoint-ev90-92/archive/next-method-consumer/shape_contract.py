"""EV90 shape predicates, independent of authoring; no solver or terrain writes.

Inputs are final float32 heights. `window` fixes the measured node population
in both states; one surrounding row/column is required as reading context.
The caller must also apply the existing angular, objective and physical gates.
"""
from __future__ import annotations
import numpy as np


def _arrays(before, after, window):
    b, h = np.asarray(before), np.asarray(after)
    if b.ndim != 2 or b.shape != h.shape or b.dtype != np.float32 or h.dtype != np.float32:
        raise ValueError('matching two-dimensional float32 height grids required')
    if not np.isfinite(b).all() or not np.isfinite(h).all():
        raise ValueError('height grids must be finite')
    r0, r1, c0, c1 = map(int, window)
    if not (0 < r0 < r1 < b.shape[0] and 0 < c0 < c1 < b.shape[1]):
        raise ValueError('fixed population must have one vertex of external context')
    return b, h, (r0, r1, c0, c1)


def positive_prominences(grid, window):
    """Separate E-W/N-S prominence at every node of the same fixed window."""
    a = np.asarray(grid, dtype=np.float64)
    r0, r1, c0, c1 = window
    center = a[r0:r1, c0:c1]
    return {
        'east_west': np.maximum(0., center - np.maximum(a[r0:r1, c0-1:c1-1], a[r0:r1, c0+1:c1+1])),
        'north_south': np.maximum(0., center - np.maximum(a[r0-1:r1-1, c0:c1], a[r0+1:r1+1, c0:c1])),
    }


def _strict_minimum8(a, r, c):
    center = a[r, c]
    return all(center < a[r+dr, c+dc] for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)


def evaluate_shape(before, after, window, focus):
    b, h, window = _arrays(before, after, window)
    r0, r1, c0, c1 = window
    fr, fc = map(int, focus)
    if not (r0 <= fr < r1 and c0 <= fc < c1):
        raise ValueError('focus outside fixed node population')
    changed = np.argwhere(b != h)
    if any(not (r0 <= r < r1 and c0 <= c < c1) for r, c in changed):
        raise ValueError('change outside measured population')
    pb, ph = positive_prominences(b, window), positive_prominences(h, window)
    axes = {}
    for axis in pb:
        x, y = pb[axis], ph[axis]
        focus_b, focus_h = float(x[fr-r0, fc-c0]), float(y[fr-r0, fc-c0])
        new_peaks = np.argwhere((x == 0.) & (y > 0.))
        axes[axis] = {
            'nodes': int(x.size), 'B_max_m': float(x.max()), 'H_max_m': float(y.max()),
            'B_sum_squares_m2': float(np.sum(x*x)), 'H_sum_squares_m2': float(np.sum(y*y)),
            'max_nonworse': bool(y.max() <= x.max()),
            'sum_squares_nonworse': bool(np.sum(y*y) <= np.sum(x*x)),
            'focus_B_m': focus_b, 'focus_H_m': focus_h,
            'focus_reduced_25pct': focus_b > 0. and focus_h <= .75*focus_b,
            'new_subdominant_or_dominant_maxima': [
                {'rc': [int(r+r0), int(c+c0)], 'prominence_m': float(y[r, c])} for r, c in new_peaks
            ],
        }
    touched_centers = {(int(r+dr), int(c+dc)) for r, c in changed
                       for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
    if any(not (0 < r < b.shape[0]-1 and 0 < c < b.shape[1]-1) for r, c in touched_centers):
        raise ValueError('insufficient context for every minimum possibly affected by a change')
    new_minima = [[r, c] for r, c in sorted(touched_centers)
                  if _strict_minimum8(h, r, c) and not _strict_minimum8(b, r, c)]
    touched_quads = {(int(r+dr), int(c+dc)) for r, c in changed for dr in (-1, 0) for dc in (-1, 0)}
    flats = []
    for r, c in sorted(touched_quads):
        vb, vh = b[r:r+2, c:c+2], h[r:r+2, c:c+2]
        if vb.shape != (2, 2) or vh.shape != (2, 2):
            raise ValueError('incomplete changed 2x2 window')
        if np.all(vh == vh[0, 0]) and not np.all(vb == vb[0, 0]):
            flats.append([r, c])
    gates = {
        'focus_positive_prominence_reduced_25pct_both_axes': all(x['focus_reduced_25pct'] for x in axes.values()),
        'fixed_population_max_prominence_nonworse_both_axes': all(x['max_nonworse'] for x in axes.values()),
        'fixed_population_sum_squares_prominence_nonworse_both_axes': all(x['sum_squares_nonworse'] for x in axes.values()),
        'no_new_strict_minima8': not new_minima,
        'no_new_exactly_constant_2x2_windows': not flats,
    }
    return {'gates': gates, 'window': list(window), 'axes': axes,
            'changed_vertices': int(len(changed)), 'tested_minimum_positions': len(touched_centers),
            'tested_quad_positions': len(touched_quads), 'new_minima8': new_minima,
            'new_constant_quads': flats,
            'limit': 'Shape predicates only. New small maxima are reported, not proof of absence of folds; no physical/runtime acceptance.'}
