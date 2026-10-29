# Q02B0 offline numeric discovery. Diagnostic only; no map changes.
import argparse
import hashlib
import io
import json
import math
import sys
import zipfile
from decimal import Decimal, localcontext
from pathlib import Path, PurePosixPath
import numpy as np
from numpy.lib import format as npformat
STATUS = 'NUMERIC_DISCOVERY_ONLY'
EXPECTED_H = [6, 12, 24, 48, 96]
EXPECTED_PRECISIONS = [80, 100]
REQUIRED = ['point_offsets', 'chain_offsets', 'chain_points', 'closed']
STATES = {'DEFINED', 'COINCIDENT_SUPPORT', 'INSUFFICIENT_SUPPORT'}
# Diagnostic inherited from Q02A only; not a quality or production threshold.
SHORT_SEGMENT_M = 1e-8
LIMIT_CAPS = {'archive_bytes': 33554432, 'required_uncompressed_bytes': 33554432, 'header_bytes': 10000, 'members': 128, 'seconds': 30, 'rss_bytes': 536870912}
class DiscoveryError(RuntimeError):
    pass
def _fail(msg):
    raise DiscoveryError('INCONCLUSIVE: ' + msg)
def _is_int(v):
    return type(v) is int
def _sha_bytes(data):
    return hashlib.sha256(data).hexdigest()
def _strict_json(data, label):
    def no_dup(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                _fail(label + ' duplicate key')
            out[k] = v
        return out
    def bad_const(v):
        _fail(label + ' nonfinite constant ' + v)
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=no_dup, parse_constant=bad_const)
    except DiscoveryError:
        raise
    except Exception as e:
        _fail(label + ' invalid strict JSON: ' + str(e))
def _closed_keys(obj, keys, label):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        _fail(label + ' closed-key mismatch')
def _hex64(v, label):
    if not isinstance(v, str) or len(v) != 64 or any(c not in '0123456789abcdef' for c in v):
        _fail(label + ' must be lowercase sha256 hex')
def _validate_contract(c):
    _closed_keys(c, ['schema', 'npz_path', 'npz_sha256', 'oracle_path', 'oracle_sha256', 'h_set', 'decimal_precisions', 'limits', 'required_keys', 'result_status', 'calibration_ready', 'natural_positive_count'], 'contract')
    if c['schema'] != 'q02b0-discovery-contract.v1':
        _fail('contract schema')
    if not isinstance(c['npz_path'], str) or not c['npz_path'] or not Path(c['npz_path']).is_absolute():
        _fail('npz_path must be absolute')
    if not isinstance(c['oracle_path'], str) or not c['oracle_path'] or not Path(c['oracle_path']).is_absolute():
        _fail('oracle_path must be absolute')
    _hex64(c['npz_sha256'], 'npz_sha256')
    _hex64(c['oracle_sha256'], 'oracle_sha256')
    if c['h_set'] != EXPECTED_H or any(not _is_int(x) for x in c['h_set']):
        _fail('h_set exact mismatch')
    if c['decimal_precisions'] != EXPECTED_PRECISIONS or any(not _is_int(x) for x in c['decimal_precisions']):
        _fail('decimal_precisions exact mismatch')
    _closed_keys(c['limits'], ['archive_bytes', 'required_uncompressed_bytes', 'header_bytes', 'members', 'seconds', 'rss_bytes'], 'limits')
    for k, v in c['limits'].items():
        if not _is_int(v) or v <= 0 or v > LIMIT_CAPS[k]:
            _fail('limits.' + k + ' must be positive int at or below plan cap')
    if c['required_keys'] != REQUIRED:
        _fail('required_keys exact mismatch')
    if c['result_status'] != STATUS or c['calibration_ready'] is not False or not _is_int(c['natural_positive_count']) or c['natural_positive_count'] != 0:
        _fail('contract status fields')
    return c
def _validate_expr(expr, label):
    if not isinstance(expr, list) or len(expr) != 2:
        _fail(label + ' expression must have 2 coordinates')
    for coord in expr:
        if not isinstance(coord, list) or not coord:
            _fail(label + ' coordinate terms')
        for term in coord:
            _closed_keys(term, ['num', 'den', 'radicand'], label + ' term')
            if not _is_int(term['num']) or not _is_int(term['den']) or not _is_int(term['radicand']):
                _fail(label + ' term ints (no bool)')
            if term['den'] == 0:
                _fail(label + ' zero denominator')
            if term['radicand'] <= 0:
                _fail(label + ' radicand must be positive')
def _validate_oracles(o, contract):
    _closed_keys(o, ['schema', 'unit', 'plane', 'natural_positive_count', 'calibration_ready', 'fixtures'], 'oracles')
    if o['schema'] != 'q02b0-oracles.v1' or o['unit'] != 'm' or o['plane'] != 'XZ':
        _fail('oracles header')
    if o['calibration_ready'] is not False or not _is_int(o['natural_positive_count']) or o['natural_positive_count'] != 0:
        _fail('oracles calibration fields')
    fixtures = o['fixtures']
    if not isinstance(fixtures, list) or len(fixtures) != 6:
        _fail('oracles requires exactly 6 fixtures')
    ids = set()
    total = coincident = insufficient = 0
    for fx in fixtures:
        _closed_keys(fx, ['id', 'points', 'closed', 'center_index', 'queries'], 'fixture')
        if not isinstance(fx['id'], str) or not fx['id'] or fx['id'] in ids:
            _fail('fixture ids unique')
        ids.add(fx['id'])
        pts = fx['points']
        if not isinstance(pts, list) or len(pts) < 2:
            _fail(fx['id'] + ' points')
        for p in pts:
            if not isinstance(p, list) or len(p) != 2 or not _is_int(p[0]) or not _is_int(p[1]):
                _fail(fx['id'] + ' integer XZ points required')
        if type(fx['closed']) is not bool:
            _fail(fx['id'] + ' closed bool')
        if fx['closed'] and pts[0] == pts[-1]:
            _fail(fx['id'] + ' closed fixture must not repeat endpoint')
        if not _is_int(fx['center_index']) or not (0 <= fx['center_index'] < len(pts)):
            _fail(fx['id'] + ' center_index')
        qs = fx['queries']
        if not isinstance(qs, list) or len(qs) != 5 or [q.get('h') if isinstance(q, dict) else None for q in qs] != contract['h_set']:
            _fail(fx['id'] + ' queries/h_set exact mismatch')
        for q in qs:
            _closed_keys(q, ['h', 'state', 'a_exact', 'c_exact'], fx['id'] + ' query')
            if not _is_int(q['h']):
                _fail(fx['id'] + ' query h must be strict int')
            if q['state'] not in STATES:
                _fail(fx['id'] + ' query state')
            total += 1
            coincident += q['state'] == 'COINCIDENT_SUPPORT'
            insufficient += q['state'] == 'INSUFFICIENT_SUPPORT'
            if q['state'] == 'INSUFFICIENT_SUPPORT':
                if q['a_exact'] is not None or q['c_exact'] is not None:
                    _fail(fx['id'] + ' insufficient query must have null exact')
            else:
                _validate_expr(q['a_exact'], fx['id'] + ' a_exact')
                _validate_expr(q['c_exact'], fx['id'] + ' c_exact')
    if total != 30 or coincident != 5 or insufficient != 1:
        _fail('oracle query census must be 30 with 5 COINCIDENT_SUPPORT and 1 INSUFFICIENT_SUPPORT')
    return o
def _read_bounded_archive(path, limit):
    try:
        size = path.stat().st_size
    except Exception as e:
        _fail('npz stat failed: ' + str(e))
    if size > limit:
        _fail('npz archive over byte limit before read')
    try:
        with path.open('rb') as f:
            data = f.read(limit + 1)
    except DiscoveryError:
        raise
    except Exception as e:
        _fail('npz read failed: ' + str(e))
    if len(data) > limit:
        _fail('npz archive over byte limit')
    return data
def _read_npz(contract):
    path = Path(contract['npz_path'])
    limits = contract['limits']
    data = _read_bounded_archive(path, limits['archive_bytes'])
    before = _sha_bytes(data)
    if before != contract['npz_sha256']:
        _fail('npz pin mismatch before parse')
    arrays = {}
    meta = {}
    other = []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            infos = zf.infolist()
            if len(infos) > limits['members']:
                _fail('zip member count over limit')
            names = [i.filename for i in infos]
            if len(names) != len(set(names)):
                _fail('zip duplicate members')
            for n in names:
                p = PurePosixPath(n)
                if not n or chr(92) in n or ':' in n or n.startswith('/') or p.is_absolute() or len(p.parts) != 1 or p.parts[0] != n or '..' in p.parts:
                    _fail('zip member must be a flat root name: ' + n)
            required_names = {k + '.npy': k for k in REQUIRED}
            for n in names:
                if n not in required_names:
                    other.append(n[:-4] if n.endswith('.npy') else n)
            missing = [k for k in REQUIRED if k + '.npy' not in names]
            if missing:
                _fail('npz missing required members ' + ','.join(missing))
            total_req = sum(zf.getinfo(k + '.npy').file_size for k in REQUIRED)
            if total_req > limits['required_uncompressed_bytes']:
                _fail('required uncompressed bytes over limit')
            declared_total = 0
            for key in REQUIRED:
                info = zf.getinfo(key + '.npy')
                with zf.open(info) as fp:
                    try:
                        version = npformat.read_magic(fp)
                    except Exception as e:
                        _fail(key + ' bad npy magic: ' + str(e))
                    if version not in ((1, 0), (2, 0)):
                        _fail(key + ' npy version must be exactly (1, 0) or (2, 0)')
                    try:
                        if version[0] == 1:
                            shape, fortran, dtype = npformat.read_array_header_1_0(fp, max_header_size=limits['header_bytes'])
                        else:
                            shape, fortran, dtype = npformat.read_array_header_2_0(fp, max_header_size=limits['header_bytes'])
                    except Exception as e:
                        _fail(key + ' bad npy header: ' + str(e))
                    if dtype.hasobject:
                        _fail(key + ' object arrays rejected')
                    if any(int(x) < 0 for x in shape):
                        _fail(key + ' negative shape dimension before payload')
                    header_end = fp.tell()
                    payload = math.prod(shape) * dtype.itemsize
                    if payload != info.file_size - header_end:
                        _fail(key + ' declared payload size mismatch before load')
                    declared_total += payload
                    if declared_total > limits['required_uncompressed_bytes']:
                        _fail('declared payload sum over limit before load')
                    raw = fp.read(payload + 1)
                    if len(raw) != payload:
                        _fail(key + ' truncated payload')
                    arr = np.frombuffer(raw, dtype=dtype)
                    arr = np.array(arr.reshape(shape, order='F' if fortran else 'C'), copy=True)
                    arrays[key] = arr
                    meta[key] = {'shape': [int(x) for x in shape], 'dtype': str(dtype), 'nbytes': int(payload), 'member_bytes': int(info.file_size)}
    except DiscoveryError:
        raise
    except Exception as e:
        _fail('npz parse failed: ' + str(e))
    data_after = _read_bounded_archive(path, limits['archive_bytes'])
    after = _sha_bytes(data_after)
    if after != before:
        _fail('npz changed after parse')
    return arrays, meta, sorted(other), before, after
def _npz_metadata(arrays, meta, other):
    po, co, pts, closed = (arrays[k] for k in REQUIRED)
    for name, arr in (('point_offsets', po), ('chain_offsets', co)):
        if arr.ndim != 1 or arr.dtype.kind not in 'iu':
            _fail(name + ' must be 1D int (no bool)')
    if closed.ndim != 1 or closed.dtype.kind != 'b':
        _fail('closed must be 1D bool')
    if pts.ndim != 2 or pts.shape[1] != 2 or pts.dtype != np.dtype('float64'):
        _fail('chain_points must be float64 Nx2')
    if not np.isfinite(pts).all():
        _fail('chain_points nonfinite')
    n = int(closed.shape[0])
    if po.shape[0] != n + 1 or co.shape[0] != n + 1:
        _fail('offsets length must be chains+1')
    po_l = [int(x) for x in po.tolist()]
    co_l = [int(x) for x in co.tolist()]
    if po_l[0] != 0 or co_l[0] != 0 or po_l[-1] != int(pts.shape[0]):
        _fail('offset origin/terminal mismatch')
    if any(b < a for a, b in zip(po_l, po_l[1:])) or any(b < a for a, b in zip(co_l, co_l[1:])):
        _fail('offsets must be monotone')
    stored = [b - a for a, b in zip(po_l, po_l[1:])]
    if any(s < 1 for s in stored):
        _fail('stored points per chain must be at least 1')
    # Source NPZ contract: chain_offsets index consecutive raw segments for every chain.
    if co_l[-1] != sum(s - 1 for s in stored):
        _fail('chain_offsets terminal must equal sum(stored-1)')
    core = []
    mismatch = degenerate = zero_segments = short_segments = positive = segment_count = 0
    reason_counts = {'stored_lt2': 0, 'closure_mismatch': 0, 'closed_lt3_distinct': 0, 'short_segment_lt_1e-8': 0, 'zero_segment': 0}
    seg_min = seg_max = None
    perimeters = []
    for i in range(n):
        seg_pts = [(float(pts[j, 0]), float(pts[j, 1])) for j in range(po_l[i], po_l[i + 1])]
        is_closed = bool(closed[i])
        s = len(seg_pts)
        if co_l[i + 1] - co_l[i] != s - 1:
            _fail('chain_offsets diff must equal diff(point_offsets)-1 for every chain')
        exact_closed = is_closed and s >= 2 and seg_pts[0] == seg_pts[-1]
        core_pts = seg_pts[:-1] if exact_closed else seg_pts
        core.append(len(core_pts))
        reasons = set()
        if s < 2:
            reasons.add('stored_lt2')
        mism = bool(is_closed and not exact_closed)
        if mism:
            mismatch += 1
            reasons.add('closure_mismatch')
        if is_closed and len(set(core_pts)) < 3:
            reasons.add('closed_lt3_distinct')
        # Never weld a mismatched closed chain: raw segments only, no invented closing segment.
        pairs = list(zip(seg_pts, seg_pts[1:]))
        segment_count += len(pairs)
        lengths = []
        for (x1, z1), (x2, z2) in pairs:
            try:
                ln = math.hypot(x2 - x1, z2 - z1)
            except OverflowError:
                _fail('segment length overflow')
            if not math.isfinite(ln):
                _fail('nonfinite segment length')
            lengths.append(ln)
            if ln == 0.0:
                zero_segments += 1
                reasons.add('zero_segment')
            if ln < SHORT_SEGMENT_M:
                short_segments += 1
                reasons.add('short_segment_lt_1e-8')
            if ln > 0.0:
                positive += 1
                seg_min = ln if seg_min is None else min(seg_min, ln)
                seg_max = ln if seg_max is None else max(seg_max, ln)
        for r in reasons:
            reason_counts[r] += 1
        if reasons:
            degenerate += 1
        try:
            per = math.fsum(lengths)
        except OverflowError:
            _fail('perimeter overflow')
        if not math.isfinite(per):
            _fail('nonfinite perimeter')
        perimeters.append(per)
    max_abs = float(np.max(np.abs(pts))) if pts.shape[0] else None
    if max_abs is not None and not math.isfinite(max_abs):
        _fail('nonfinite max_abs_coord')
    return {'arrays': meta, 'other_members_enumerated_only': other, 'chain_count': n, 'closed_chain_count': int(np.count_nonzero(closed)), 'open_chain_count': n - int(np.count_nonzero(closed)), 'stored_point_count': int(pts.shape[0]), 'core_vertex_count': int(sum(core)), 'segment_count': int(segment_count), 'stored_points_per_chain_min': min(stored) if stored else None, 'stored_points_per_chain_max': max(stored) if stored else None, 'core_vertices_per_chain_min': min(core) if core else None, 'core_vertices_per_chain_max': max(core) if core else None, 'positive_segment_count': positive, 'zero_segment_count': zero_segments, 'short_segment_count': short_segments, 'short_segment_threshold_m': SHORT_SEGMENT_M, 'short_segment_threshold_note': 'diagnostic inherited from Q02A; not a quality threshold', 'min_segment_m': seg_min, 'max_segment_m': seg_max, 'min_perimeter_m': min(perimeters) if perimeters else None, 'max_perimeter_m': max(perimeters) if perimeters else None, 'max_abs_coord': max_abs, 'degenerate_chain_count': degenerate, 'degenerate_reason_counts': reason_counts, 'closure_mismatch_count': mismatch, 'candidate_window_rows_upper': int(sum(core)) * 5, 'length_method': 'float64 math.hypot per raw segment, math.fsum per chain; observed range only, not an error bound'}
def _dec_point(p):
    return (Decimal(p[0]), Decimal(p[1]))
def _dist_dec(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2).sqrt()
def walk(points, closed, center, h, direction, precision):
    if direction not in (-1, 1):
        _fail('walk direction')
    with localcontext() as ctx:
        ctx.prec = int(precision)
        pts = [_dec_point(p) for p in points]
        n = len(pts)
        if n < 2:
            return ('DEGENERATE', None)
        if closed and len(set(pts)) < 3:
            return ('DEGENERATE', None)
        edges = [(pts[i], pts[(i + 1) % n]) for i in range(n)] if closed else list(zip(pts, pts[1:]))
        if any(_dist_dec(a, b) < Decimal('1e-8') for a, b in edges):
            return ('DEGENERATE', None)
        hd = Decimal(h)
        if closed:
            per = sum((_dist_dec(pts[i], pts[(i + 1) % n]) for i in range(n)), Decimal(0))
            if Decimal(2) * hd >= per:
                return ('INSUFFICIENT_SUPPORT', None)
        remaining = +hd
        idx = int(center)
        for _ in range(n + 1 if closed else n):
            if remaining == 0:
                return ('DEFINED', pts[idx])
            if closed:
                nxt = (idx + direction) % n
            else:
                nxt = idx + direction
                if nxt < 0 or nxt >= n:
                    return ('INSUFFICIENT_SUPPORT', None)
            start, end = pts[idx], pts[nxt]
            ln = _dist_dec(start, end)
            if remaining < ln:
                t = remaining / ln
                return ('DEFINED', (start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t))
            remaining -= ln
            idx = nxt
        return ('INSUFFICIENT_SUPPORT', None)
def _walk_float(points, closed, center, h, direction):
    pts = [(float(p[0]), float(p[1])) for p in points]
    n = len(pts)
    if n < 2:
        return ('DEGENERATE', None)
    if closed and len(set(pts)) < 3:
        return ('DEGENERATE', None)
    edges = [(pts[i], pts[(i + 1) % n]) for i in range(n)] if closed else list(zip(pts, pts[1:]))
    if any(math.hypot(b[0] - a[0], b[1] - a[1]) < SHORT_SEGMENT_M for a, b in edges):
        return ('DEGENERATE', None)
    if closed:
        per = math.fsum(math.hypot(pts[(i + 1) % n][0] - pts[i][0], pts[(i + 1) % n][1] - pts[i][1]) for i in range(n))
        if 2.0 * float(h) >= per:
            return ('INSUFFICIENT_SUPPORT', None)
    remaining = float(h)
    idx = int(center)
    for _ in range(n + 1 if closed else n):
        if remaining == 0.0:
            return ('DEFINED', pts[idx])
        nxt = (idx + direction) % n if closed else idx + direction
        if not closed and not (0 <= nxt < n):
            return ('INSUFFICIENT_SUPPORT', None)
        (x1, z1), (x2, z2) = pts[idx], pts[nxt]
        ln = math.hypot(x2 - x1, z2 - z1)
        if remaining < ln:
            t = remaining / ln
            return ('DEFINED', (x1 + (x2 - x1) * t, z1 + (z2 - z1) * t))
        remaining -= ln
        idx = nxt
    return ('INSUFFICIENT_SUPPORT', None)
def _reference_point(expr, precision):
    if expr is None:
        return None
    with localcontext() as ctx:
        ctx.prec = int(precision)
        out = []
        for coord in expr:
            v = Decimal(0)
            for t in coord:
                v += (Decimal(t['num']) / Decimal(t['den'])) * Decimal(t['radicand']).sqrt()
            out.append(+v)
        return tuple(out)
def _dstr(v):
    return None if v is None else str(v)
def _pt_str(p):
    return None if p is None else [str(p[0]), str(p[1])]
def _max_diff(p, q):
    if p is None or q is None:
        return None
    return max(abs(p[0] - q[0]), abs(p[1] - q[1]))
def _metrics(a, b, c, h):
    if a is None or c is None:
        return {'side_ab_m': None, 'side_bc_m': None, 'side_ac_m': None, 'cross': None, 'dot': None, 'cos': None, 'angle_rad_float': None, 'angle_precision': 'float64 math.atan2 when present', 'deviation_m': None, 'curvature_per_m': None, 'chord_deficit': None, 'undefined_reasons': ['INSUFFICIENT_SUPPORT']}
    with localcontext() as ctx:
        ctx.prec = 100
        ab = _dist_dec(a, b); bc = _dist_dec(b, c); ac = _dist_dec(a, c)
        bax, baz = b[0] - a[0], b[1] - a[1]
        cbx, cbz = c[0] - b[0], c[1] - b[1]
        cross = bax * cbz - baz * cbx
        dot = bax * cbx + baz * cbz
        reasons = []
        cos = deviation = curvature = None
        if ab == 0 or bc == 0:
            reasons.append('ZERO_SIDE')
        else:
            cos = dot / (ab * bc)
        if ac == 0:
            reasons.append('AC_ZERO')
        else:
            deviation = ((c[0] - a[0]) * baz - (c[1] - a[1]) * bax) / ac
            if ab != 0 and bc != 0:
                curvature = (Decimal(2) * cross) / (ab * bc * ac)
        angle = None
        if ab != 0 and bc != 0:
            angle = math.atan2(float(cross), float(dot))
        return {'side_ab_m': _dstr(ab), 'side_bc_m': _dstr(bc), 'side_ac_m': _dstr(ac), 'cross': _dstr(cross), 'dot': _dstr(dot), 'cos': _dstr(cos), 'angle_rad_float': angle, 'angle_precision': 'float64 math.atan2 when present', 'deviation_m': _dstr(deviation), 'curvature_per_m': _dstr(curvature), 'chord_deficit': _dstr((Decimal(2 * h) - ac) / Decimal(2 * h)), 'undefined_reasons': reasons}
def _combine(sa, a, sc, c):
    if 'DEGENERATE' in (sa, sc):
        return 'DEGENERATE'
    if 'INSUFFICIENT_SUPPORT' in (sa, sc):
        return 'INSUFFICIENT_SUPPORT'
    return 'COINCIDENT_SUPPORT' if a == c else 'DEFINED'
def _oracle_records(oracles):
    records = []
    for fx in oracles['fixtures']:
        pts, closed, center = fx['points'], fx['closed'], fx['center_index']
        b_dec = _dec_point(pts[center])
        for q in fx['queries']:
            h = q['h']
            walks = {}
            for prec in (80, 100):
                sa, a = walk(pts, closed, center, h, -1, prec)
                sc, c = walk(pts, closed, center, h, 1, prec)
                walks[prec] = (_combine(sa, a, sc, c), a, c)
            st100, a100, c100 = walks[100]
            st80, a80, c80 = walks[80]
            ref_a = _reference_point(q['a_exact'], 100)
            ref_c = _reference_point(q['c_exact'], 100)
            with localcontext() as ctx:
                ctx.prec = 100
                d80 = None
                if a80 is not None and c80 is not None and a100 is not None and c100 is not None:
                    d80 = max(_max_diff(a80, a100), _max_diff(c80, c100))
                dref = None
                if ref_a is not None and ref_c is not None and a100 is not None and c100 is not None:
                    dref = max(_max_diff(ref_a, a100), _max_diff(ref_c, c100))
            fsa, fa = _walk_float(pts, closed, center, h, -1)
            fsc, fc = _walk_float(pts, closed, center, h, 1)
            float_state = _combine(fsa, fa, fsc, fc)
            dfloat = None
            if fa is not None and fc is not None and a100 is not None and c100 is not None:
                with localcontext() as ctx:
                    ctx.prec = 100
                    dfloat = max(_max_diff((Decimal(fa[0]), Decimal(fa[1])), a100), _max_diff((Decimal(fc[0]), Decimal(fc[1])), c100))
            metrics = _metrics(a100, b_dec, c100, h)
            if st100 == 'DEGENERATE':
                metrics['undefined_reasons'] = ['DEGENERATE']
            records.append({'fixture_id': fx['id'], 'h': h, 'expected_state': q['state'], 'state': st100, 'state_matches_expected': st100 == q['state'], 'float_state': float_state, 'a_walk_float64': None if fa is None else [fa[0], fa[1]], 'c_walk_float64': None if fc is None else [fc[0], fc[1]], 'b_decimal100': _pt_str(b_dec), 'a_walk_decimal100': _pt_str(a100), 'c_walk_decimal100': _pt_str(c100), 'a_reference_decimal100': _pt_str(ref_a), 'c_reference_decimal100': _pt_str(ref_c), 'decimal80_to_100_max_abs_diff': _dstr(d80), 'reference_to_walk100_max_abs_diff': _dstr(dref), 'float64_to_walk100_max_abs_diff': _dstr(dfloat), 'metrics_decimal100': metrics})
    return records
def discover(contract_path, external_sha):
    _hex64(external_sha, 'external contract sha')
    raw = Path(contract_path).read_bytes()
    if _sha_bytes(raw) != external_sha:
        _fail('contract pin mismatch before parse')
    contract = _validate_contract(_strict_json(raw, 'contract'))
    oracle_raw = Path(contract['oracle_path']).read_bytes()
    if _sha_bytes(oracle_raw) != contract['oracle_sha256']:
        _fail('oracle pin mismatch before parse')
    oracles = _validate_oracles(_strict_json(oracle_raw, 'oracles'), contract)
    arrays, meta, other, before, after = _read_npz(contract)
    npz_meta = _npz_metadata(arrays, meta, other)
    records = _oracle_records(oracles)
    mismatches = [r['fixture_id'] + ':' + str(r['h']) for r in records if not r['state_matches_expected']]
    divergences = [r['fixture_id'] + ':' + str(r['h']) for r in records if r['reference_to_walk100_max_abs_diff'] is not None and Decimal(r['reference_to_walk100_max_abs_diff']) != 0]
    return {'status': STATUS, 'calibration_ready': False, 'natural_positive_count': 0, 'physical_hypothesis': 'NOT_EVALUATED', 'no_map_changes': True, 'contract_sha256': external_sha, 'npz_sha256_before': before, 'npz_sha256_after': after, 'oracle_sha256': contract['oracle_sha256'], 'h_set': contract['h_set'], 'decimal_precisions': contract['decimal_precisions'], 'npz': npz_meta, 'oracles': {'fixture_count': 6, 'query_count': len(records), 'coincident_support_count': sum(r['state'] == 'COINCIDENT_SUPPORT' for r in records), 'insufficient_support_count': sum(r['state'] == 'INSUFFICIENT_SUPPORT' for r in records), 'degenerate_count': sum(r['state'] == 'DEGENERATE' for r in records), 'state_mismatches': mismatches, 'reference_divergences_nonzero': divergences, 'records': records}, 'bound_proposals': [], 'bound_status': 'PENDING_REVIEW_NOT_APPROVED', 'conditioning_notes': ['Observed Decimal80->100 and float64 divergences are diagnostics, not approved bounds.', 'No quality threshold is proposed or approved by this discovery.']}
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--contract', required=True)
    ap.add_argument('--contract-sha256', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args(argv)
    out = Path(args.output)
    if out.exists():
        print('INCONCLUSIVE: output already exists; not overwritten', file=sys.stderr)
        return 2
    try:
        report = discover(args.contract, args.contract_sha256)
        text = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + chr(10)
        with open(out, 'x', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        msg = str(e) if str(e).startswith('INCONCLUSIVE') else 'INCONCLUSIVE: ' + str(e)
        print(msg, file=sys.stderr)
        return 2
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
