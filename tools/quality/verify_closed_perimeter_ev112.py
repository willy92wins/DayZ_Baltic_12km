# Independent verifier for closed_perimeter_ev112 reports (Q02A).
#
# This module does not import the producer or shape_patterns. It rewalks
# every triple with scalar arithmetic: lengths by math.hypot / math.fsum,
# angles checked through the cosine identity dot/(|a|*|b|) with tolerance
# 2e-14, and the >=45 degree witness rule through the independent exact
# algebraic criterion dot <= 0 or 2*dot**2 <= |a|^2 * |b|^2 evaluated
# with Fractions built from the float64 coordinates before subtraction.
# Per-edge length agreement is 4 ULP; perimeter agreement is 16 ULP.
# Unknown keys are rejected at global, summary, chain, witness and
# closure levels. Duplicate JSON keys are rejected at every level via
# object_pairs_hook, as are NaN/Infinity constants. Any PASS/acceptance
# attempt is rejected: the only accepted global status is DIAGNOSTIC_ONLY
# and chains may only be DIAGNOSTIC_FINDINGS,
# NO_RAW_TURN_FINDING_NOT_ACCEPTANCE, DEGENERATE or NO_EVALUABLE_VERTEX.
# NO_EVALUABLE_VERTEX (reason 'no_evaluable_vertex', open 1/2-point chains
# without a short segment) is counted separately from DEGENERATE; closed
# chains with fewer than 3 distinct core vertices remain DEGENERATE.
# angles_deg must equal absolute_turns_deg exactly, and
# absolute_turns_deg must equal abs(signed_turns_deg) exactly, except
# that a signed turn rounded to the canonical +180 spike is accepted even
# when the recomputed cross is negative (rounding of a near -180 turn).
# An empty chain is schema-invalid and rejects the whole unit.
# Optional --summary file exact keys: {schema_version, status,
# threshold_deg, input_sha256, summary, full_report_sha256}; it is
# validated against the exact report bytes (SHA-256) and every report
# field, without modifying the report bytes.
# Non-finite intermediate calculations are rejected.
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

_SCHEMA = 'closed_perimeter_ev112.v1'
_REQUIRED = ('point_offsets', 'chain_points', 'closed', 'chain_offsets')
_GLOBAL_KEYS = {'schema_version', 'status', 'threshold_deg', 'input_sha256', 'source_npz_keys', 'summary', 'chains'}
_SUMMARY_KEYS = {'chain_count', 'closed_chain_count', 'open_chain_count', 'degenerate_chain_count', 'finding_chain_count', 'no_finding_chain_count', 'no_evaluable_chain_count', 'evaluated_vertices', 'evaluated_edges', 'total_witness_count', 'closed_chains_with_closure_witness', 'closed_chains_where_closure_is_only_witness'}
_SUMMARY_FILE_KEYS = {'schema_version', 'status', 'threshold_deg', 'input_sha256', 'summary', 'full_report_sha256'}
_CHAIN_KEYS = {'chain_index', 'closed', 'status', 'degenerate_reason', 'point_count_stored', 'vertex_count', 'evaluated_vertices', 'evaluated_edges', 'edge_lengths', 'perimeter', 'vertex_indices', 'vertex_xy', 'signed_turns_deg', 'absolute_turns_deg', 'angles_deg', 'witnesses', 'closure_turn', 'coincident_endpoints'}
_WITNESS_KEYS = {'vertex_index', 'vertex_xy', 'signed_turn_deg', 'absolute_turn_deg'}
_CLOSURE_KEYS = {'vertex_index', 'vertex_xy', 'signed_turn_deg', 'absolute_turn_deg', 'is_witness'}
_REASONS = {None, 'closure_mismatch', 'short_segment', 'distinct_vertices_lt3', 'no_evaluable_vertex'}
_HEX = set('0123456789abcdef')


def _fail(message):
    raise ValueError(message)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_num(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)))


def _exact_keys(obj, keys, label):
    if not isinstance(obj, dict):
        _fail(label + ' must be an object')
    if set(obj.keys()) != keys:
        _fail(label + ' has unknown or missing keys')


def _check_xy(value, label):
    if not isinstance(value, list) or len(value) != 2 or not all(_is_num(v) for v in value):
        _fail(label + ' must be [x, y] finite numbers')
    return [float(value[0]), float(value[1])]


def _validate_input(data):
    if not isinstance(data, dict):
        _fail('data must be a dict of numpy arrays')
    for key in _REQUIRED:
        if key not in data:
            _fail('missing required array: ' + key)
        if not isinstance(data[key], np.ndarray):
            _fail('array must be numpy.ndarray: ' + key)
    po_arr = data['point_offsets']
    co_arr = data['chain_offsets']
    pts_arr = data['chain_points']
    closed_arr = data['closed']
    if po_arr.ndim != 1 or po_arr.dtype.kind not in 'iu':
        _fail('point_offsets must be a 1-D integer array')
    if co_arr.ndim != 1 or co_arr.dtype.kind not in 'iu':
        _fail('chain_offsets must be a 1-D integer array')
    if closed_arr.ndim != 1 or closed_arr.dtype.kind != 'b':
        _fail('closed must be a 1-D bool array')
    if pts_arr.ndim != 2 or pts_arr.shape[1] != 2:
        _fail('chain_points must have shape (N, 2)')
    if pts_arr.dtype != np.dtype('float64'):
        _fail('chain_points must be float64')
    if pts_arr.size and not bool(np.isfinite(pts_arr).all()):
        _fail('chain_points must be finite')
    po = [int(v) for v in po_arr.tolist()]
    co = [int(v) for v in co_arr.tolist()]
    n = int(closed_arr.shape[0])
    if len(po) != n + 1 or len(co) != n + 1:
        _fail('offsets must have length n_chains + 1')
    if po[0] != 0 or co[0] != 0:
        _fail('offsets must start at 0')
    if any(b < a for a, b in zip(po, po[1:])) or any(b < a for a, b in zip(co, co[1:])):
        _fail('offsets must be monotone nondecreasing')
    if po[-1] != int(pts_arr.shape[0]):
        _fail('point_offsets terminal must equal len(chain_points)')
    for i in range(n):
        if (po[i + 1] - po[i]) - 1 != co[i + 1] - co[i]:
            _fail('chain_offsets differences must equal point count - 1 per chain')
    points = [[float(x), float(y)] for x, y in pts_arr.tolist()]
    return po, [bool(v) for v in closed_arr.tolist()], points


def _polyline_edges(core):
    return [math.hypot(core[i + 1][0] - core[i][0], core[i + 1][1] - core[i][1]) for i in range(len(core) - 1)] if len(core) >= 2 else []


def _cyclic_edges(core):
    if not core:
        return []
    if len(core) == 1:
        return [0.0]
    m = len(core)
    return [math.hypot(core[(i + 1) % m][0] - core[i][0], core[(i + 1) % m][1] - core[i][1]) for i in range(m)]


def _expected_chain(stored, is_closed):
    if is_closed:
        if not stored:
            # Unreachable: _validate_input rejects empty chains.
            return stored, [], 'no_evaluable_vertex', []
        if stored[0] != stored[-1]:
            return stored, _polyline_edges(stored), 'closure_mismatch', []
        core = stored[:-1]
        edges = _cyclic_edges(core)
        if len({(p[0], p[1]) for p in core}) < 3:
            return core, edges, 'distinct_vertices_lt3', []
        if any(e < 1e-8 for e in edges):
            return core, edges, 'short_segment', []
        return core, edges, None, list(range(len(core)))
    edges = _polyline_edges(stored)
    if any(e < 1e-8 for e in edges):
        return stored, edges, 'short_segment', []
    if len(stored) < 3:
        return stored, edges, 'no_evaluable_vertex', []
    return stored, edges, None, list(range(1, len(stored) - 1))


def _expected_witness_indices(core, indices, cyclic):
    m = len(core)
    frac = [(Fraction(x), Fraction(y)) for x, y in core]
    result = []
    for idx in indices:
        fprev = frac[(idx - 1) % m] if cyclic else frac[idx - 1]
        fcur = frac[idx]
        fnxt = frac[(idx + 1) % m] if cyclic else frac[idx + 1]
        ax = fcur[0] - fprev[0]
        ay = fcur[1] - fprev[1]
        bx = fnxt[0] - fcur[0]
        by = fnxt[1] - fcur[1]
        dot = ax * bx + ay * by
        norm2a = ax * ax + ay * ay
        norm2b = bx * bx + by * by
        if dot <= 0 or 2 * dot * dot <= norm2a * norm2b:
            result.append(idx)
    return result


def _close_ulp(reported, expected, ulps, label):
    if not math.isfinite(expected):
        _fail(label + ' non-finite expected value')
    if expected == 0.0:
        if float(reported) != 0.0:
            _fail(label + ' must be 0')
        return
    if abs(float(reported) - expected) > ulps * math.ulp(expected):
        _fail(label + ' disagrees beyond ULP tolerance')


def verify_arrays(data, report, expected_input_sha256=None, source_npz_keys=None):
    po, closed_flags, all_points = _validate_input(data)
    _exact_keys(report, _GLOBAL_KEYS, 'report')
    if report['schema_version'] != _SCHEMA:
        _fail('unsupported schema_version')
    if report['status'] != 'DIAGNOSTIC_ONLY':
        _fail('report status must be DIAGNOSTIC_ONLY; acceptance is rejected')
    if not _is_num(report['threshold_deg']) or float(report['threshold_deg']) != 45.0:
        _fail('threshold_deg must be 45')
    sha = report['input_sha256']
    if expected_input_sha256 is not None:
        if sha != expected_input_sha256:
            _fail('input_sha256 does not match expected SHA-256')
    elif sha is not None:
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in _HEX for c in sha):
            _fail('input_sha256 must be null or 64 lowercase hex characters')
    sources = report['source_npz_keys']
    expected_sources = sorted(source_npz_keys) if source_npz_keys is not None else sorted(data.keys())
    if not isinstance(sources, list) or any(not isinstance(s, str) for s in sources) or sources != expected_sources:
        _fail('source_npz_keys mismatch')
    for key in _REQUIRED:
        if key not in sources:
            _fail('source_npz_keys must include required keys')
    summary = report['summary']
    _exact_keys(summary, _SUMMARY_KEYS, 'summary')
    for key in _SUMMARY_KEYS:
        if not _is_int(summary[key]):
            _fail('summary values must be integers: ' + key)
    chains = report['chains']
    if not isinstance(chains, list) or len(chains) != len(closed_flags):
        _fail('chains must list every chain exactly once')
    totals = {'closed': 0, 'degenerate': 0, 'no_evaluable': 0, 'finding': 0, 'no_finding': 0, 'vertices': 0, 'edges': 0, 'witnesses': 0, 'closure_witness': 0, 'closure_only': 0}
    for index, chain in enumerate(chains):
        _exact_keys(chain, _CHAIN_KEYS, 'chain')
        stored = all_points[po[index]:po[index + 1]]
        is_closed = closed_flags[index]
        core, exp_edges, exp_reason, exp_indices = _expected_chain(stored, is_closed)
        if any(not math.isfinite(e) for e in exp_edges):
            _fail('non-finite expected edge length')
        exp_witness_idx = _expected_witness_indices(core, exp_indices, is_closed) if exp_indices else []
        if not _is_int(chain['chain_index']) or chain['chain_index'] != index:
            _fail('chain_index must be sequential')
        if not isinstance(chain['closed'], bool) or chain['closed'] != is_closed:
            _fail('closed flag mismatch')
        reason = chain['degenerate_reason']
        if reason is not None and not isinstance(reason, str):
            _fail('degenerate_reason must be a string or null')
        if reason not in _REASONS or reason != exp_reason:
            _fail('degenerate_reason mismatch')
        if exp_reason == 'no_evaluable_vertex':
            exp_status = 'NO_EVALUABLE_VERTEX'
        elif exp_reason is not None:
            exp_status = 'DEGENERATE'
        elif exp_witness_idx:
            exp_status = 'DIAGNOSTIC_FINDINGS'
        else:
            exp_status = 'NO_RAW_TURN_FINDING_NOT_ACCEPTANCE'
        if chain['status'] != exp_status:
            _fail('chain status mismatch')
        if not _is_int(chain['point_count_stored']) or chain['point_count_stored'] != len(stored):
            _fail('point_count_stored mismatch')
        if not _is_int(chain['vertex_count']) or chain['vertex_count'] != len(core):
            _fail('vertex_count mismatch')
        if not _is_int(chain['evaluated_vertices']) or chain['evaluated_vertices'] != len(exp_indices):
            _fail('evaluated_vertices mismatch')
        if not _is_int(chain['evaluated_edges']) or chain['evaluated_edges'] != len(exp_edges):
            _fail('evaluated_edges mismatch')
        exp_coincident = bool(len(stored) >= 2 and stored[0] == stored[-1])
        if not isinstance(chain['coincident_endpoints'], bool) or chain['coincident_endpoints'] != exp_coincident:
            _fail('coincident_endpoints mismatch')
        rep_edges = chain['edge_lengths']
        if not isinstance(rep_edges, list) or len(rep_edges) != len(exp_edges) or any(not _is_num(v) for v in rep_edges):
            _fail('edge_lengths mismatch')
        for pos, (rep_e, exp_e) in enumerate(zip(rep_edges, exp_edges)):
            _close_ulp(rep_e, exp_e, 4, 'edge_lengths[' + str(pos) + ']')
        if not _is_num(chain['perimeter']):
            _fail('perimeter must be a finite number')
        try:
            exp_perimeter = math.fsum(exp_edges)
        except OverflowError:
            _fail('non-finite expected perimeter')
        _close_ulp(chain['perimeter'], exp_perimeter, 16, 'perimeter')
        for field in ('vertex_indices', 'vertex_xy', 'signed_turns_deg', 'absolute_turns_deg', 'angles_deg'):
            if not isinstance(chain[field], list) or len(chain[field]) != len(exp_indices):
                _fail(field + ' length mismatch')
        m = len(core)
        for pos, idx in enumerate(exp_indices):
            if not _is_int(chain['vertex_indices'][pos]) or chain['vertex_indices'][pos] != idx:
                _fail('vertex_indices mismatch')
            xy = _check_xy(chain['vertex_xy'][pos], 'vertex_xy')
            if xy != [core[idx][0], core[idx][1]]:
                _fail('vertex_xy mismatch')
            signed = chain['signed_turns_deg'][pos]
            absolute = chain['absolute_turns_deg'][pos]
            alias = chain['angles_deg'][pos]
            if not _is_num(signed) or not _is_num(absolute) or not _is_num(alias):
                _fail('turn angles must be finite numbers')
            if float(alias) != float(absolute):
                _fail('angles_deg must equal absolute_turns_deg exactly')
            if not (0.0 <= float(absolute) <= 180.0) or not (-180.0 < float(signed) <= 180.0):
                _fail('turn angle out of canonical range')
            if float(absolute) != abs(float(signed)):
                _fail('signed and absolute turns disagree')
            prev = core[(idx - 1) % m] if is_closed else core[idx - 1]
            cur = core[idx]
            nxt = core[(idx + 1) % m] if is_closed else core[idx + 1]
            ax = cur[0] - prev[0]
            ay = cur[1] - prev[1]
            bx = nxt[0] - cur[0]
            by = nxt[1] - cur[1]
            dot = ax * bx + ay * by
            cross = ax * by - ay * bx
            denom = math.hypot(ax, ay) * math.hypot(bx, by)
            if not all(math.isfinite(v) for v in (dot, cross, denom)) or denom == 0.0:
                _fail('non-finite turn calculation')
            cos_expected = dot / denom
            if not math.isfinite(cos_expected):
                _fail('non-finite turn calculation')
            if abs(math.cos(math.radians(float(absolute))) - cos_expected) > 2e-14:
                _fail('absolute turn fails cosine identity')
            if cross > 0.0 and float(signed) < 0.0:
                _fail('signed turn sign mismatch')
            if cross < 0.0 and float(signed) > 0.0 and float(signed) != 180.0:
                _fail('signed turn sign mismatch')
            if cross == 0.0:
                want = 0.0 if dot > 0.0 else 180.0
                if abs(float(signed) - want) > 1e-12:
                    _fail('signed turn mismatch on straight/spike vertex')
        witnesses = chain['witnesses']
        if not isinstance(witnesses, list) or len(witnesses) != len(exp_witness_idx):
            _fail('witness list must match expected witnesses exactly')
        for pos, widx in enumerate(exp_witness_idx):
            wit = witnesses[pos]
            _exact_keys(wit, _WITNESS_KEYS, 'witness')
            if not _is_int(wit['vertex_index']) or wit['vertex_index'] != widx:
                _fail('witness vertex_index mismatch')
            if _check_xy(wit['vertex_xy'], 'witness vertex_xy') != [core[widx][0], core[widx][1]]:
                _fail('witness vertex_xy mismatch')
            src = exp_indices.index(widx)
            if not _is_num(wit['signed_turn_deg']) or not _is_num(wit['absolute_turn_deg']):
                _fail('witness angles must be finite numbers')
            if float(wit['signed_turn_deg']) != float(chain['signed_turns_deg'][src]) or float(wit['absolute_turn_deg']) != float(chain['absolute_turns_deg'][src]):
                _fail('witness angles must match evaluated turns')
        closure = chain['closure_turn']
        if is_closed and exp_reason is None:
            _exact_keys(closure, _CLOSURE_KEYS, 'closure_turn')
            if not _is_int(closure['vertex_index']) or closure['vertex_index'] != 0:
                _fail('closure_turn must be vertex 0')
            if _check_xy(closure['vertex_xy'], 'closure vertex_xy') != [core[0][0], core[0][1]]:
                _fail('closure vertex_xy mismatch')
            if not _is_num(closure['signed_turn_deg']) or not _is_num(closure['absolute_turn_deg']):
                _fail('closure angles must be finite numbers')
            if float(closure['signed_turn_deg']) != float(chain['signed_turns_deg'][0]) or float(closure['absolute_turn_deg']) != float(chain['absolute_turns_deg'][0]):
                _fail('closure angles must match vertex 0 turn')
            if not isinstance(closure['is_witness'], bool) or closure['is_witness'] != (0 in exp_witness_idx):
                _fail('closure is_witness mismatch')
        elif closure is not None:
            _fail('closure_turn must be null for open or degenerate chains')
        totals['closed'] += 1 if is_closed else 0
        totals['degenerate'] += 1 if exp_status == 'DEGENERATE' else 0
        totals['no_evaluable'] += 1 if exp_status == 'NO_EVALUABLE_VERTEX' else 0
        totals['finding'] += 1 if exp_status == 'DIAGNOSTIC_FINDINGS' else 0
        totals['no_finding'] += 1 if exp_status == 'NO_RAW_TURN_FINDING_NOT_ACCEPTANCE' else 0
        totals['vertices'] += len(exp_indices)
        totals['edges'] += len(exp_edges)
        totals['witnesses'] += len(exp_witness_idx)
        if is_closed and exp_reason is None and 0 in exp_witness_idx:
            totals['closure_witness'] += 1
            if len(exp_witness_idx) == 1:
                totals['closure_only'] += 1
    expected_summary = {'chain_count': len(closed_flags), 'closed_chain_count': totals['closed'], 'open_chain_count': len(closed_flags) - totals['closed'], 'degenerate_chain_count': totals['degenerate'], 'finding_chain_count': totals['finding'], 'no_finding_chain_count': totals['no_finding'], 'no_evaluable_chain_count': totals['no_evaluable'], 'evaluated_vertices': totals['vertices'], 'evaluated_edges': totals['edges'], 'total_witness_count': totals['witnesses'], 'closed_chains_with_closure_witness': totals['closure_witness'], 'closed_chains_where_closure_is_only_witness': totals['closure_only']}
    for key, want in expected_summary.items():
        if summary[key] != want:
            _fail('summary mismatch: ' + key)
    return True


def _validate_summary_file(summary_obj, report, report_raw):
    _exact_keys(summary_obj, _SUMMARY_FILE_KEYS, 'summary file')
    if summary_obj['schema_version'] != _SCHEMA:
        _fail('summary file schema_version mismatch')
    if summary_obj['status'] != 'DIAGNOSTIC_ONLY':
        _fail('summary file status must be DIAGNOSTIC_ONLY')
    if not _is_num(summary_obj['threshold_deg']) or float(summary_obj['threshold_deg']) != 45.0 or float(summary_obj['threshold_deg']) != float(report['threshold_deg']):
        _fail('summary file threshold_deg mismatch')
    if summary_obj['input_sha256'] != report['input_sha256']:
        _fail('summary file input_sha256 mismatch')
    link = summary_obj['full_report_sha256']
    if not isinstance(link, str) or len(link) != 64 or any(c not in _HEX for c in link):
        _fail('summary file full_report_sha256 must be 64 lowercase hex characters')
    if link != hashlib.sha256(report_raw).hexdigest():
        _fail('summary file full_report_sha256 does not match report bytes')
    inner = summary_obj['summary']
    _exact_keys(inner, _SUMMARY_KEYS, 'summary file summary')
    for key in _SUMMARY_KEYS:
        if not _is_int(inner[key]):
            _fail('summary file summary values must be integers: ' + key)
    if inner != report['summary']:
        _fail('summary file summary does not match report summary')
    return True


def _reject_constant(value):
    raise ValueError('non-finite JSON constant rejected: ' + value)


def _object_no_duplicates(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate JSON key rejected: ' + str(key))
        obj[key] = value
    return obj


def _load_json_bytes(raw, label):
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError(label + ' must be UTF-8 JSON') from exc
    return json.loads(text, object_pairs_hook=_object_no_duplicates, parse_constant=_reject_constant)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Verify a closed-perimeter report (diagnostic only)')
    parser.add_argument('--input', required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--summary', required=False, default=None)
    args = parser.parse_args(argv)
    try:
        expected = args.expected_sha256.strip().lower()
        if len(expected) != 64 or any(c not in _HEX for c in expected):
            _fail('expected_sha256 must be 64 lowercase hex characters')
        input_path = Path(args.input)
        report_path = Path(args.report)
        summary_path = Path(args.summary) if args.summary else None
        if not input_path.is_file() or not report_path.is_file():
            _fail('input and report files must exist')
        if summary_path is not None and not summary_path.is_file():
            _fail('summary file must exist')
        raw = input_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected:
            _fail('input SHA-256 mismatch')
        report_raw = report_path.read_bytes()
        report = _load_json_bytes(report_raw, 'report')
        summary_obj = None
        if summary_path is not None:
            summary_obj = _load_json_bytes(summary_path.read_bytes(), 'summary file')
        with np.load(io.BytesIO(raw), allow_pickle=False) as npz:
            files = list(npz.files)
            for key in _REQUIRED:
                if key not in files:
                    _fail('missing NPZ key: ' + key)
            data = {key: npz[key] for key in _REQUIRED}
        verify_arrays(data, report, expected_input_sha256=digest, source_npz_keys=files)
        if summary_obj is not None:
            _validate_summary_file(summary_obj, report, report_raw)
    except Exception as exc:
        print('error: ' + str(exc), file=sys.stderr)
        return 2
    print('OK DIAGNOSTIC_ONLY')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
