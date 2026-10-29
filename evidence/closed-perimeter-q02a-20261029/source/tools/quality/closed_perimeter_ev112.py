# Closed-perimeter turn census for EV112 (Q02A).
#
# Input arrays (numpy, no pickle at CLI load):
#   point_offsets: int array, shape (n_chains+1,), first 0, monotone,
#     last == len(chain_points). Booleans are not accepted as integers.
#   chain_offsets: int array, shape (n_chains+1,), first 0, monotone, and
#     diff(chain_offsets)[i] == diff(point_offsets)[i] - 1 for every chain.
#     It may index segment data stored under other NPZ keys; those keys are
#     enumerated in source_npz_keys but are not read here.
#   chain_points: float64 array, shape (N, 2), all finite.
#   closed: bool array, shape (n_chains,).
# Extra NPZ keys are enumerated, not rejected. The JSON report schema is
# closed: unknown keys are rejected by the verifier at every level.
# An empty chain is schema-invalid, not DEGENERATE and not
# NO_EVALUABLE_VERTEX: diff 0 is inconsistent with diff-1 segment count,
# so validation rejects the whole unit before any chain is analysed.
#
# Report schema (exact keys):
#   {schema_version, status, threshold_deg, input_sha256, source_npz_keys,
#    summary, chains}
#   schema_version='closed_perimeter_ev112.v1', status='DIAGNOSTIC_ONLY',
#   threshold_deg=45. There is deliberately no PASS/acceptance field.
# summary exact keys:
#   {chain_count, closed_chain_count, open_chain_count,
#    degenerate_chain_count, finding_chain_count, no_finding_chain_count,
#    no_evaluable_chain_count, evaluated_vertices, evaluated_edges,
#    total_witness_count, closed_chains_with_closure_witness,
#    closed_chains_where_closure_is_only_witness}
# chain exact keys:
#   {chain_index, closed, status, degenerate_reason, point_count_stored,
#    vertex_count, evaluated_vertices, evaluated_edges, edge_lengths,
#    perimeter, vertex_indices, vertex_xy, signed_turns_deg,
#    absolute_turns_deg, angles_deg, witnesses, closure_turn,
#    coincident_endpoints}
#   status is DIAGNOSTIC_FINDINGS, NO_RAW_TURN_FINDING_NOT_ACCEPTANCE,
#   DEGENERATE or NO_EVALUABLE_VERTEX. The last status is used only with
#   degenerate_reason='no_evaluable_vertex' (an open chain with 1 or 2
#   stored points and no short segment): it is not a geometric invalidity
#   and is counted separately from DEGENERATE chains. Geometrically
#   invalid chains, including closed chains with fewer than 3 distinct
#   core vertices, remain DEGENERATE. degenerate_reason is None,
#   'closure_mismatch', 'short_segment', 'distinct_vertices_lt3' or
#   'no_evaluable_vertex'.
#   angles_deg is an exact copy of absolute_turns_deg (0 straight, 180
#   spike, spike canonicalised to +180). vertex_indices are original
#   stored indices; for a valid closed chain the removed terminal repeat
#   shares index 0 geometry, so core indices are 0..vertex_count-1.
#   witnesses items have exact keys {vertex_index, vertex_xy,
#    signed_turn_deg, absolute_turn_deg}. closure_turn is None or
#   {vertex_index, vertex_xy, signed_turn_deg, absolute_turn_deg,
#    is_witness} and duplicates the i=0 entry for valid closed chains.
#   perimeter is the cyclic perimeter for closed chains and the polyline
#   length for open chains, summed with math.fsum. evaluated_edges ==
#   len(edge_lengths) (edges measured even on degenerate chains);
#   evaluated_vertices is the number of vertices at which a turn was
#   evaluated (0 on degenerate and on no-evaluable chains).
# Optional summary file (--summary-output) exact keys:
#   {schema_version, status, threshold_deg, input_sha256, summary,
#    full_report_sha256}, where full_report_sha256 is the SHA-256 of the
#   exact report JSON bytes written first.
#
# Witness rule (exact, no atan/sqrt): with incoming a and outgoing b built
# as Fractions of the float64 coordinates (subtracted after conversion),
# a vertex is a witness iff dot <= 0 or abs(cross) >= dot. This is the
# exact >=45 degree test. Edge lengths < 1e-8 make a chain DEGENERATE
# ('short_segment'); a closed chain whose last stored point is not exactly
# its first is DEGENERATE ('closure_mismatch'), never welded. Open chains
# are never closed; coincident open endpoints are only recorded.
# Non-finite intermediate calculations are rejected with ValueError.
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import sys
from fractions import Fraction
from pathlib import Path
import numpy as np

SCHEMA_VERSION = 'closed_perimeter_ev112.v1'
_REQUIRED = ('point_offsets', 'chain_points', 'closed', 'chain_offsets')
_HEX = set('0123456789abcdef')


def _check_sha(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in _HEX for c in value):
        raise ValueError('expected_sha256 must be 64 lowercase hex characters')
    return value


def _validate_arrays(data):
    if not isinstance(data, dict):
        raise ValueError('data must be a dict of numpy arrays')
    if any(not isinstance(k, str) for k in data):
        raise ValueError('array keys must be strings')
    for key in _REQUIRED:
        if key not in data:
            raise ValueError('missing required array: ' + key)
        if not isinstance(data[key], np.ndarray):
            raise ValueError('array must be numpy.ndarray: ' + key)
    point_offsets = data['point_offsets']
    chain_offsets = data['chain_offsets']
    chain_points = data['chain_points']
    closed = data['closed']
    if point_offsets.ndim != 1 or point_offsets.dtype.kind not in 'iu':
        raise ValueError('point_offsets must be a 1-D integer array')
    if chain_offsets.ndim != 1 or chain_offsets.dtype.kind not in 'iu':
        raise ValueError('chain_offsets must be a 1-D integer array')
    if closed.ndim != 1 or closed.dtype.kind != 'b':
        raise ValueError('closed must be a 1-D bool array')
    if chain_points.ndim != 2:
        raise ValueError('chain_points must be a 2-D array')
    if chain_points.shape[1] != 2:
        raise ValueError('chain_points must have shape (N, 2)')
    if chain_points.dtype != np.dtype('float64'):
        raise ValueError('chain_points must be float64')
    if chain_points.size and not bool(np.isfinite(chain_points).all()):
        raise ValueError('chain_points must be finite')
    po = [int(v) for v in point_offsets.tolist()]
    co = [int(v) for v in chain_offsets.tolist()]
    n = int(closed.shape[0])
    if len(po) != n + 1 or len(co) != n + 1:
        raise ValueError('offsets must have length n_chains + 1')
    if po[0] != 0 or co[0] != 0:
        raise ValueError('offsets must start at 0')
    if any(b < a for a, b in zip(po, po[1:])) or any(b < a for a, b in zip(co, co[1:])):
        raise ValueError('offsets must be monotone nondecreasing')
    if po[-1] != int(chain_points.shape[0]):
        raise ValueError('point_offsets terminal must equal len(chain_points)')
    for i in range(n):
        if (po[i + 1] - po[i]) - 1 != co[i + 1] - co[i]:
            raise ValueError('chain_offsets differences must equal point count - 1 per chain')
    return po, co, [bool(v) for v in closed.tolist()], chain_points


def _edge_lengths(core, cyclic):
    if not core:
        return []
    if cyclic and len(core) == 1:
        return [0.0]
    arr = np.asarray(core, dtype=np.float64)
    if cyclic:
        diffs = np.roll(arr, -1, axis=0) - arr
    else:
        if len(core) < 2:
            return []
        diffs = np.diff(arr, axis=0)
    lengths = [float(v) for v in np.hypot(diffs[:, 0], diffs[:, 1])]
    if any(not math.isfinite(v) for v in lengths):
        raise ValueError('non-finite edge length calculation')
    return lengths


def _evaluate(core, indices, cyclic):
    m = len(core)
    frac = [(Fraction(x), Fraction(y)) for x, y in core]
    signed_list = []
    absolute_list = []
    witnesses = []
    for idx in indices:
        prev = core[(idx - 1) % m] if cyclic else core[idx - 1]
        cur = core[idx]
        nxt = core[(idx + 1) % m] if cyclic else core[idx + 1]
        ax = float(cur[0] - prev[0])
        ay = float(cur[1] - prev[1])
        bx = float(nxt[0] - cur[0])
        by = float(nxt[1] - cur[1])
        if not all(math.isfinite(v) for v in (ax, ay, bx, by)):
            raise ValueError('non-finite turn calculation')
        cross = ax * by - ay * bx
        dot = ax * bx + ay * by
        if not math.isfinite(cross) or not math.isfinite(dot):
            raise ValueError('non-finite turn calculation')
        signed = float(np.degrees(np.arctan2(cross, dot)))
        if not math.isfinite(signed):
            raise ValueError('non-finite turn calculation')
        if signed == -180.0:
            signed = 180.0
        absolute = abs(signed)
        signed_list.append(signed)
        absolute_list.append(absolute)
        fprev = frac[(idx - 1) % m] if cyclic else frac[idx - 1]
        fcur = frac[idx]
        fnxt = frac[(idx + 1) % m] if cyclic else frac[idx + 1]
        fax = fcur[0] - fprev[0]
        fay = fcur[1] - fprev[1]
        fbx = fnxt[0] - fcur[0]
        fby = fnxt[1] - fcur[1]
        fdot = fax * fbx + fay * fby
        fcross = fax * fby - fay * fbx
        if fdot <= 0 or abs(fcross) >= fdot:
            witnesses.append({'vertex_index': int(idx), 'vertex_xy': [float(cur[0]), float(cur[1])], 'signed_turn_deg': signed, 'absolute_turn_deg': absolute})
    return signed_list, absolute_list, witnesses


def analyze_arrays(data, input_sha256=None, source_npz_keys=None):
    po, _co, closed_flags, chain_points = _validate_arrays(data)
    if input_sha256 is not None:
        _check_sha(input_sha256)
    if source_npz_keys is None:
        sources = sorted(data.keys())
    else:
        if any(not isinstance(k, str) for k in source_npz_keys):
            raise ValueError('source_npz_keys must be strings')
        sources = sorted(set(source_npz_keys))
        for key in _REQUIRED:
            if key not in sources:
                raise ValueError('source_npz_keys must include required keys')
    all_points = chain_points.tolist()
    chains = []
    for index in range(len(closed_flags)):
        stored = [[float(x), float(y)] for x, y in all_points[po[index]:po[index + 1]]]
        is_closed = closed_flags[index]
        degenerate = None
        indices = []
        if is_closed:
            if not stored:
                # Unreachable: _validate_arrays rejects empty chains.
                core = []
                edges = []
                degenerate = 'no_evaluable_vertex'
            elif stored[0] != stored[-1]:
                core = stored
                edges = _edge_lengths(core, False)
                degenerate = 'closure_mismatch'
            else:
                core = stored[:-1]
                if len({(p[0], p[1]) for p in core}) < 3:
                    edges = _edge_lengths(core, True)
                    degenerate = 'distinct_vertices_lt3'
                else:
                    edges = _edge_lengths(core, True)
                    if any(e < 1e-8 for e in edges):
                        degenerate = 'short_segment'
                    else:
                        indices = list(range(len(core)))
        else:
            core = stored
            edges = _edge_lengths(core, False)
            if any(e < 1e-8 for e in edges):
                degenerate = 'short_segment'
            elif len(core) < 3:
                degenerate = 'no_evaluable_vertex'
            else:
                indices = list(range(1, len(core) - 1))
        signed_list = []
        absolute_list = []
        witnesses = []
        if indices:
            signed_list, absolute_list, witnesses = _evaluate(core, indices, is_closed)
        if degenerate == 'no_evaluable_vertex':
            status = 'NO_EVALUABLE_VERTEX'
        elif degenerate is not None:
            status = 'DEGENERATE'
        elif witnesses:
            status = 'DIAGNOSTIC_FINDINGS'
        else:
            status = 'NO_RAW_TURN_FINDING_NOT_ACCEPTANCE'
        closure_turn = None
        if is_closed and degenerate is None:
            closure_turn = {'vertex_index': 0, 'vertex_xy': [float(core[0][0]), float(core[0][1])], 'signed_turn_deg': signed_list[0], 'absolute_turn_deg': absolute_list[0], 'is_witness': any(w['vertex_index'] == 0 for w in witnesses)}
        try:
            perimeter = float(math.fsum(edges)) if edges else 0.0
        except OverflowError:
            raise ValueError('non-finite perimeter calculation')
        if not math.isfinite(perimeter):
            raise ValueError('non-finite perimeter calculation')
        chains.append({'chain_index': int(index), 'closed': bool(is_closed), 'status': status, 'degenerate_reason': degenerate, 'point_count_stored': int(len(stored)), 'vertex_count': int(len(core)), 'evaluated_vertices': int(len(indices)), 'evaluated_edges': int(len(edges)), 'edge_lengths': [float(e) for e in edges], 'perimeter': perimeter, 'vertex_indices': [int(i) for i in indices], 'vertex_xy': [[float(core[i][0]), float(core[i][1])] for i in indices], 'signed_turns_deg': signed_list, 'absolute_turns_deg': absolute_list, 'angles_deg': list(absolute_list), 'witnesses': witnesses, 'closure_turn': closure_turn, 'coincident_endpoints': bool(len(stored) >= 2 and stored[0] == stored[-1])})
    summary = {'chain_count': int(len(chains)), 'closed_chain_count': int(sum(1 for c in chains if c['closed'])), 'open_chain_count': int(sum(1 for c in chains if not c['closed'])), 'degenerate_chain_count': int(sum(1 for c in chains if c['status'] == 'DEGENERATE')), 'finding_chain_count': int(sum(1 for c in chains if c['status'] == 'DIAGNOSTIC_FINDINGS')), 'no_finding_chain_count': int(sum(1 for c in chains if c['status'] == 'NO_RAW_TURN_FINDING_NOT_ACCEPTANCE')), 'no_evaluable_chain_count': int(sum(1 for c in chains if c['status'] == 'NO_EVALUABLE_VERTEX')), 'evaluated_vertices': int(sum(c['evaluated_vertices'] for c in chains)), 'evaluated_edges': int(sum(c['evaluated_edges'] for c in chains)), 'total_witness_count': int(sum(len(c['witnesses']) for c in chains)), 'closed_chains_with_closure_witness': int(sum(1 for c in chains if c['closure_turn'] is not None and c['closure_turn']['is_witness'])), 'closed_chains_where_closure_is_only_witness': int(sum(1 for c in chains if c['closure_turn'] is not None and c['closure_turn']['is_witness'] and len(c['witnesses']) == 1))}
    return {'schema_version': SCHEMA_VERSION, 'status': 'DIAGNOSTIC_ONLY', 'threshold_deg': 45, 'input_sha256': input_sha256, 'source_npz_keys': sources, 'summary': summary, 'chains': chains}


def _load_npz_bytes(raw):
    with np.load(io.BytesIO(raw), allow_pickle=False) as npz:
        files = list(npz.files)
        for key in _REQUIRED:
            if key not in files:
                raise ValueError('missing NPZ key: ' + key)
        data = {key: npz[key] for key in _REQUIRED}
    return data, files


def main(argv=None):
    parser = argparse.ArgumentParser(description='Closed-perimeter turn census (diagnostic only)')
    parser.add_argument('--input', required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--summary-output', required=False, default=None)
    args = parser.parse_args(argv)
    try:
        expected = _check_sha(args.expected_sha256.strip().lower())
        input_path = Path(args.input)
        output_path = Path(args.output)
        summary_path = Path(args.summary_output) if args.summary_output else None
        if not input_path.is_file():
            raise ValueError('input file not found')
        if output_path.exists():
            raise ValueError('output already exists; refusing to overwrite')
        if summary_path is not None:
            if summary_path.resolve() == output_path.resolve():
                raise ValueError('output and summary-output must be distinct')
            if summary_path.exists():
                raise ValueError('summary output already exists; refusing to overwrite')
        raw = input_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected:
            raise ValueError('input SHA-256 mismatch')
        data, files = _load_npz_bytes(raw)
        report = analyze_arrays(data, input_sha256=digest, source_npz_keys=files)
        text = json.dumps(report, allow_nan=False, indent=2) + chr(10)
        # Bind the actual UTF-8 bytes: text mode changes LF to CRLF on Windows.
        with output_path.open('xb') as handle:
            handle.write(text.encode('utf-8'))
        if summary_path is not None:
            summary_obj = {'schema_version': report['schema_version'], 'status': report['status'], 'threshold_deg': report['threshold_deg'], 'input_sha256': report['input_sha256'], 'summary': report['summary'], 'full_report_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
            summary_text = json.dumps(summary_obj, allow_nan=False, indent=2) + chr(10)
            with summary_path.open('xb') as handle:
                handle.write(summary_text.encode('utf-8'))
    except Exception as exc:
        print('error: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
