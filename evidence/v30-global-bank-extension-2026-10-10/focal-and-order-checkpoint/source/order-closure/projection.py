"""Exact float32 closure for a bounded directed order graph.

An edge (w, c) means q[c] >= q[w]. All heights and bounds live on the
float32 lattice; no tolerance or post-projection rounding is applied.
"""
from __future__ import annotations

from collections import deque
import math
import numpy as np


def _height_vector(value, name):
    a = np.asarray(value)
    if a.ndim != 1 or a.dtype != np.dtype(np.float32):
        raise ValueError(f'{name} must be a flat float32 vector')
    if not np.isfinite(a).all():
        raise ValueError(f'{name} must be finite')
    return a.copy()


def _edges_array(edges, n):
    e = np.asarray(edges)
    if e.ndim != 2 or e.shape[1] != 2 or not np.issubdtype(e.dtype, np.integer):
        raise ValueError('edges must be an integer (E,2) array of witness,center indices')
    if np.issubdtype(e.dtype, np.bool_):
        raise ValueError('boolean edge indices are invalid')
    e = np.asarray(e, dtype=np.int64)
    if e.size and (int(e.min()) < 0 or int(e.max()) >= n):
        raise ValueError('edge index outside node domain')
    return e


def _check(guard, counter):
    if guard is not None and (counter & 4095) == 0:
        guard()


def evaluate_objective_gates(raw_cost, closed_cost, baseline_cost):
    """Apply the frozen closure budget and strict-improvement comparison."""
    costs = tuple(float(v) for v in (raw_cost, closed_cost, baseline_cost))
    if not all(math.isfinite(v) for v in costs):
        raise ValueError('objective costs must be finite')
    raw_cost, closed_cost, baseline_cost = costs
    allowance = 1e-7 * max(1.0, raw_cost)
    return {'allowance': allowance,
            'closure_budget_pass': bool(closed_cost - raw_cost <= allowance),
            'strict_improvement_vs_baseline': bool(closed_cost < baseline_cost)}


def project_order(raw, lower, upper, edges, *, baseline=None, fixed=None,
                  guard=None):
    """Project raw values by bounded order closure.

    Args:
        raw, lower, upper: exact float32 vectors on one common node domain.
        edges: integer rows ``(witness, center)`` encoding center >= witness.
        baseline: optional exact feasible float32 witness, used to validate
            the input bounds/order and to confirm fixed-node preservation.
        fixed: optional boolean mask. Fixed entries must equal baseline.
        guard: optional no-argument resource/deadline guard called periodically.

    Returns a dict containing the projected q, propagated upper U, clipped r,
    and the pre-closure bound terms b and V. Raises ValueError if infeasible.
    """
    raw = _height_vector(raw, 'raw')
    lower = _height_vector(lower, 'lower')
    upper = _height_vector(upper, 'upper')
    n = raw.size
    if lower.shape != raw.shape or upper.shape != raw.shape:
        raise ValueError('raw/lower/upper shape mismatch')
    if np.any(lower > upper):
        raise ValueError('inverted input bounds')
    edges = _edges_array(edges, n)
    if fixed is not None:
        fixed = np.asarray(fixed)
        if fixed.shape != (n,) or fixed.dtype != np.dtype(bool):
            raise ValueError('fixed must be a boolean mask matching the node domain')
        if baseline is None:
            raise ValueError('baseline is required when fixed nodes are supplied')
    if baseline is not None:
        baseline = _height_vector(baseline, 'baseline')
        if baseline.shape != raw.shape:
            raise ValueError('baseline shape mismatch')
        if np.any(baseline < lower) or np.any(baseline > upper):
            raise ValueError('baseline is not a feasible box witness')
        if edges.size and np.any(baseline[edges[:, 0]] > baseline[edges[:, 1]]):
            raise ValueError('baseline is not a feasible order witness')
        if fixed is not None and np.any(lower[fixed] != upper[fixed]):
            raise ValueError('fixed nodes must have equal lower and upper bounds')
        if fixed is not None and (np.any(lower[fixed] != baseline[fixed])
                                  or np.any(upper[fixed] != baseline[fixed])):
            raise ValueError('fixed bounds differ from baseline')

    # Reverse upper closure: for every witness->center edge, the witness
    # cannot exceed the center's propagated upper limit.
    incoming_witnesses = [[] for _ in range(n)]
    outgoing_centers = [[] for _ in range(n)]
    for w, c in edges:
        incoming_witnesses[int(c)].append(int(w))
        outgoing_centers[int(w)].append(int(c))
    propagated_upper = upper.copy()
    queue = deque(range(n))
    queued = bytearray(b'\x01') * n
    ops = 0
    while queue:
        center = queue.popleft()
        queued[center] = 0
        cap = propagated_upper[center]
        for witness in incoming_witnesses[center]:
            if propagated_upper[witness] > cap:
                propagated_upper[witness] = cap
                if not queued[witness]:
                    queue.append(witness)
                    queued[witness] = 1
            ops += 1
            _check(guard, ops)

    if np.any(lower > propagated_upper):
        raise ValueError('infeasible box/order bounds after reverse propagation')
    if baseline is not None and (np.any(baseline < lower)
                                  or np.any(baseline > propagated_upper)):
        raise ValueError('baseline does not witness propagated upper bounds')

    clipped = np.minimum(np.maximum(raw, lower), propagated_upper).astype(np.float32, copy=False)
    b = float(np.max(np.abs(clipped.astype(np.float64) - raw.astype(np.float64)), initial=0.0))
    violations = np.maximum(
        0.0,
        clipped[edges[:, 0]].astype(np.float64) - clipped[edges[:, 1]].astype(np.float64),
    ) if edges.size else np.empty(0, dtype=np.float64)
    V = math.fsum(float(v) for v in violations)

    # Forward least majorant: any raise to a center is sent to its dependents.
    q = clipped.copy()
    edge_queue = deque(range(len(edges)))
    queued_edges = bytearray(b'\x01') * len(edges)
    by_witness = [[] for _ in range(n)]
    for eid, (w, _c) in enumerate(edges):
        by_witness[int(w)].append(eid)
    ops = 0
    while edge_queue:
        eid = edge_queue.popleft()
        queued_edges[eid] = 0
        w, c = edges[eid]
        w = int(w); c = int(c)
        if q[c] < q[w]:
            q[c] = q[w]
            for next_eid in by_witness[c]:
                if not queued_edges[next_eid]:
                    edge_queue.append(next_eid)
                    queued_edges[next_eid] = 1
        ops += 1
        _check(guard, ops)

    if np.any(q < lower) or np.any(q > propagated_upper):
        raise AssertionError('projected result escaped bounded feasible set')
    if edges.size and np.any(q[edges[:, 0]] > q[edges[:, 1]]):
        raise AssertionError('projected result violates directed order')
    if fixed is not None and np.any(q[fixed] != baseline[fixed]):
        raise AssertionError('projected result changed fixed values')
    correction = float(np.max(np.abs(q.astype(np.float64) - raw.astype(np.float64)), initial=0.0))
    bound = b + V
    if correction > bound:
        raise AssertionError(f'a priori correction bound failed: {correction} > {bound}')
    return {
        'q': q,
        'clipped': clipped,
        'upper_propagated': propagated_upper,
        'clip_max_abs': b,
        'raw_order_violation_sum_after_clip': V,
        'a_priori_correction_bound': bound,
        'max_abs_correction': correction,
        'changed_nodes': int(np.count_nonzero(q != raw)),
        'raised_nodes': int(np.count_nonzero(q > raw)),
        'lowered_nodes': int(np.count_nonzero(q < raw)),
    }
