import argparse
import hashlib
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

MAX_BYTES = 4 * 1024 * 1024
HEX_RE = re.compile(r'[0-9a-f]{64}')
CONTRACT_KEYS = {'schema', 'unit', 'plane', 'natural_positive_count', 'calibration_ready', 'q01', 'fixtures'}
Q01_KEYS = {'ledger_path', 'ledger_sha256', 'sources_root', 'source_pins', 'case_ids', 'control_ids'}
FIXTURE_KEYS = {'id', 'closed', 'role', 'context', 'features', 'limitation', 'expected', 'points_file', 'points_sha256'}
CORPUS_FIXTURE_KEYS = {'id', 'closed', 'role', 'context', 'features', 'limitation', 'expected', 'points'}
EXPECTED_KEYS = {'vertex_count', 'edge_squared_lengths', 'nonzero_turns', 'twice_signed_area', 'circle'}
CIRCLE_KEYS = {'center', 'radius_squared'}
CORPUS_KEYS = {'schema', 'contract_sha256', 'unit', 'plane', 'human_references', 'scope_controls', 'photographic_references', 'fixtures', 'natural_positive_count', 'calibration_ready', 'resolved_count', 'c1_verdict', 'visual_acceptance'}
MANIFEST_KEYS = {'schema', 'contract_sha256', 'corpus_sha256'}
CASE_KEYS = {'id', 'human_verdict', 'source_bindings', 'scope', 'location_status', 'required_layers', 'automatic_evidence'}
ROLES = {'SYNTHETIC_ENGINEERING', 'SYNTHETIC_SMOOTH_REFERENCE'}
CONTEXTS = {'UNCLASSIFIED_SHORE', 'DESIGNED_STRUCTURE'}
BINDING_KEYS = {'path', 'sha256', 'pointer', 'expected_literal'}

def _fail(msg):
    raise ValueError(msg)

def _is_hex(v):
    return isinstance(v, str) and HEX_RE.fullmatch(v) is not None

def _bad_constant(v):
    raise ValueError('invalid JSON constant: ' + v)

def _no_dup(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError('duplicate JSON key: ' + str(k))
        out[k] = v
    return out

def _loads(raw, label):
    try:
        text = raw.decode('utf-8')
    except Exception:
        _fail(label + ': invalid utf-8')
    try:
        return json.loads(text, object_pairs_hook=_no_dup, parse_constant=_bad_constant)
    except ValueError as e:
        s = str(e)
        if s.startswith(('duplicate JSON key', 'invalid JSON constant')):
            raise
        _fail(label + ': invalid JSON: ' + s)

def _read(path, label):
    p = Path(path)
    if p.is_symlink():
        _fail(label + ': symlink not allowed')
    if not p.is_file():
        _fail(label + ': file not found')
    if p.stat().st_size > MAX_BYTES:
        _fail(label + ': file too large')
    data = p.read_bytes()
    if len(data) > MAX_BYTES:
        _fail(label + ': file too large')
    return data

def _sha(data):
    return hashlib.sha256(data).hexdigest()

def _eq(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        if set(a) != set(b):
            return False
        return all(_eq(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    return a == b

def _frac(v, label):
    if isinstance(v, bool):
        _fail(label + ': bool coordinate not allowed')
    if isinstance(v, int):
        return Fraction(v)
    if isinstance(v, Fraction):
        return v
    if isinstance(v, str):
        try:
            f = Fraction(v)
        except Exception:
            _fail(label + ': invalid rational string')
        if str(f) != v:
            _fail(label + ': non-canonical rational string')
        return f
    _fail(label + ': coordinate must be int or canonical rational string')

def _is_canonical_rational(v):
    if not isinstance(v, str):
        return False
    try:
        return str(Fraction(v)) == v
    except Exception:
        return False

def measure(points, closed):
    if type(closed) is not bool:
        _fail('closed must be bool')
    if not isinstance(points, (list, tuple)):
        _fail('points must be a list')
    pts = []
    for pt in points:
        if not isinstance(pt, (list, tuple)) or len(pt) != 2:
            _fail('point must have exactly 2 coordinates')
        pts.append((_frac(pt[0], 'point'), _frac(pt[1], 'point')))
    n = len(pts)
    if closed and n < 3:
        _fail('closed fixture requires at least 3 vertices')
    if not closed and n < 2:
        _fail('open fixture requires at least 2 vertices')
    if n > 4096:
        _fail('fixture exceeds 4096 vertices')
    if n >= 2 and pts[0] == pts[-1]:
        _fail('duplicate endpoints not allowed')
    m = n if closed else n - 1
    edges = []
    lengths = []
    for i in range(m):
        a = pts[i]
        b = pts[(i + 1) % n]
        dx = b[0] - a[0]
        dz = b[1] - a[1]
        if dx == 0 and dz == 0:
            _fail('zero-length edge not allowed')
        edges.append((dx, dz))
        lengths.append(str(dx * dx + dz * dz))
    turns = []
    if closed:
        idxs = list(range(n))
    else:
        idxs = list(range(1, n - 1))
    for i in idxs:
        if closed and i == 0:
            vin = (pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])
        else:
            vin = (pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        nxt = pts[(i + 1) % n] if closed else pts[i + 1]
        vout = (nxt[0] - pts[i][0], nxt[1] - pts[i][1])
        det = vin[0] * vout[1] - vin[1] * vout[0]
        dot = vin[0] * vout[0] + vin[1] * vout[1]
        if det == 0 and dot < 0:
            _fail('reversal not allowed')
        if det > 0:
            turns.append([i, 1])
        elif det < 0:
            turns.append([i, -1])
    area = None
    if closed:
        s = Fraction(0)
        for i in range(n):
            a = pts[i]
            b = pts[(i + 1) % n]
            s += a[0] * b[1] - b[0] * a[1]
        area = str(s)
    return {'vertex_count': n, 'edge_squared_lengths': lengths, 'nonzero_turns': turns, 'twice_signed_area': area}

def _validate_expected(exp):
    if not isinstance(exp, dict) or set(exp) != EXPECTED_KEYS:
        _fail('expected: exact keys required')
    if type(exp['vertex_count']) is not int or exp['vertex_count'] < 1:
        _fail('expected: vertex_count malformed')
    if not isinstance(exp['edge_squared_lengths'], list) or not all(_is_canonical_rational(x) for x in exp['edge_squared_lengths']):
        _fail('expected: edge_squared_lengths must be canonical rational strings')
    if not isinstance(exp['nonzero_turns'], list):
        _fail('expected: nonzero_turns malformed')
    for t in exp['nonzero_turns']:
        if not isinstance(t, list) or len(t) != 2 or type(t[0]) is not int or type(t[1]) is not int or t[1] not in (1, -1):
            _fail('expected: nonzero_turns entries malformed')
    if exp['twice_signed_area'] is not None and not _is_canonical_rational(exp['twice_signed_area']):
        _fail('expected: twice_signed_area malformed')
    c = exp['circle']
    if c is not None:
        if not isinstance(c, dict) or set(c) != CIRCLE_KEYS:
            _fail('expected: circle exact keys required')
        if not isinstance(c['center'], list) or len(c['center']) != 2:
            _fail('expected: circle center malformed')
        _frac(c['center'][0], 'circle center')
        _frac(c['center'][1], 'circle center')
        if not _is_canonical_rational(c['radius_squared']):
            _fail('expected: radius_squared malformed')
        if Fraction(c['radius_squared']) <= 0:
            _fail('expected: radius_squared must be positive')

def validate_fixture(f):
    if not isinstance(f, dict) or set(f) != CORPUS_FIXTURE_KEYS:
        _fail('fixture: exact corpus keys required')
    if not isinstance(f['id'], str) or not f['id']:
        _fail('fixture: id required')
    if f['id'] in ['NARVA-VIS-01', 'NARVA-VIS-02', 'NARVA-VIS-03', 'KIT118-VIS-01', 'KIT118-VIS-02', 'CONT65-VIS-01', 'ROAD49-RIVER-VIS-01', 'CROSSING-VIS-01', 'RELIEF-EAST-VIS-01', 'forest-dense', 'causeway-c0', 'road-49', 'causeway-c1']:
        _fail('fixture: id must not be a human/control id')
    if type(f['closed']) is not bool:
        _fail('fixture: closed must be bool')
    if f['role'] not in ROLES:
        _fail('fixture: role not in closed enum')
    if f['context'] not in CONTEXTS:
        _fail('fixture: context not in closed enum')
    if not isinstance(f['features'], list) or not all(isinstance(x, str) and x for x in f['features']):
        _fail('fixture: features malformed')
    if not isinstance(f['limitation'], str) or not f['limitation']:
        _fail('fixture: limitation required')
    _validate_expected(f['expected'])
    got = measure(f['points'], f['closed'])
    exp = f['expected']
    if got['vertex_count'] != exp['vertex_count']:
        _fail('fixture: vertex_count mismatch')
    if not _eq(got['edge_squared_lengths'], exp['edge_squared_lengths']):
        _fail('fixture: edge_squared_lengths mismatch')
    if not _eq(got['nonzero_turns'], exp['nonzero_turns']):
        _fail('fixture: nonzero_turns mismatch')
    if not _eq(got['twice_signed_area'], exp['twice_signed_area']):
        _fail('fixture: twice_signed_area mismatch')
    circ = exp['circle']
    if circ is not None:
        cx = _frac(circ['center'][0], 'circle center')
        cz = _frac(circ['center'][1], 'circle center')
        r2 = Fraction(circ['radius_squared'])
        for pt in f['points']:
            x = _frac(pt[0], 'point')
            z = _frac(pt[1], 'point')
            if (x - cx) * (x - cx) + (z - cz) * (z - cz) != r2:
                _fail('fixture: point not on expected circle')
    return True

def _validate_contract(c):
    if not isinstance(c, dict) or set(c) != CONTRACT_KEYS:
        _fail('contract: exact schema keys required')
    if c['schema'] != 'q17a-contract.v1' or c['unit'] != 'm' or c['plane'] != 'XZ':
        _fail('contract: schema/unit/plane mismatch')
    if type(c['natural_positive_count']) is not int or c['natural_positive_count'] != 0:
        _fail('contract: natural_positive_count must be 0')
    if c['calibration_ready'] is not False:
        _fail('contract: calibration_ready must be false')
    q = c['q01']
    if not isinstance(q, dict) or set(q) != Q01_KEYS:
        _fail('contract: q01 exact keys required')
    if not isinstance(q['ledger_path'], str) or not q['ledger_path'] or not _is_hex(q['ledger_sha256']):
        _fail('contract: ledger binding malformed')
    if not isinstance(q['sources_root'], str) or not q['sources_root']:
        _fail('contract: sources_root required')
    if not isinstance(q['source_pins'], dict) or len(q['source_pins']) != 12:
        _fail('contract: source_pins must have 12 entries')
    for k, v in q['source_pins'].items():
        if not isinstance(k, str) or not _is_hex(v):
            _fail('contract: source_pins malformed')
    if q['case_ids'] != ['NARVA-VIS-01', 'NARVA-VIS-02', 'NARVA-VIS-03', 'KIT118-VIS-01', 'KIT118-VIS-02', 'CONT65-VIS-01', 'ROAD49-RIVER-VIS-01', 'CROSSING-VIS-01', 'RELIEF-EAST-VIS-01']:
        _fail('contract: case_ids mismatch')
    if q['control_ids'] != ['forest-dense', 'causeway-c0', 'road-49', 'causeway-c1']:
        _fail('contract: control_ids mismatch')
    fx = c['fixtures']
    if not isinstance(fx, list) or not (1 <= len(fx) <= 20):
        _fail('contract: fixtures length out of range')
    ids = []
    for f in fx:
        if not isinstance(f, dict) or set(f) != FIXTURE_KEYS:
            _fail('contract: fixture exact keys required')
        ids.append(f['id'])
        if f['id'] in q['case_ids'] or f['id'] in q['control_ids']:
            _fail('contract: fixture id must not be a human/control id')
        if not isinstance(f['id'], str) or not f['id'] or type(f['closed']) is not bool:
            _fail('contract: fixture id/closed malformed')
        if f['role'] not in ROLES:
            _fail('contract: fixture role not in closed enum')
        if f['context'] not in CONTEXTS:
            _fail('contract: fixture context not in closed enum')
        if not isinstance(f['features'], list) or not all(isinstance(x, str) and x for x in f['features']):
            _fail('contract: fixture features malformed')
        if not isinstance(f['limitation'], str) or not f['limitation']:
            _fail('contract: fixture limitation required')
        _validate_expected(f['expected'])
        if not isinstance(f['points_file'], str) or not _is_hex(f['points_sha256']):
            _fail('contract: fixture points binding malformed')
    if len(set(ids)) != len(ids):
        _fail('contract: fixture ids not unique')
    if sum(f['expected']['vertex_count'] for f in fx) > 4096:
        _fail('contract: total vertex_count exceeds 4096')

def _root(root):
    r = Path(root)
    if r.is_symlink() or not r.is_dir():
        _fail('root: directory not found')
    return r.resolve()

def _safe_join(root_r, rel, label):
    if not isinstance(rel, str) or not rel:
        _fail(label + ': relative path required')
    p = Path(rel)
    if p.is_absolute():
        _fail(label + ': absolute path not allowed')
    if any(part in ('..', '') for part in p.parts):
        _fail(label + ': path escape not allowed')
    cur = root_r
    for part in p.parts:
        cur = cur / part
        if cur.is_symlink():
            _fail(label + ': symlink not allowed')
    resolved = cur.resolve()
    if resolved != root_r and root_r not in resolved.parents:
        _fail(label + ': path escapes root')
    return cur

def _extract_points(doc, label):
    if isinstance(doc, list):
        return doc
    _fail(label + ': points array not found')

def _resolve_pointer(doc, pointer, label):
    if not isinstance(pointer, str):
        _fail(label + ': pointer must be string')
    if pointer == '':
        return doc
    if not pointer.startswith('/'):
        _fail(label + ': pointer must start with /')
    cur = doc
    for raw in pointer[1:].split('/'):
        tok = raw.replace('~1', '/').replace('~0', '~')
        if isinstance(cur, dict):
            if tok not in cur:
                _fail(label + ': pointer token not found')
            cur = cur[tok]
        elif isinstance(cur, list):
            if not tok.isdigit() or (len(tok) > 1 and tok.startswith('0')):
                _fail(label + ': pointer index malformed')
            i = int(tok)
            if i >= len(cur):
                _fail(label + ': pointer index out of range')
            cur = cur[i]
        else:
            _fail(label + ': pointer traverses scalar')
    return cur

def verify(root, contract_path, contract_sha, corpus_dir):
    root_r = _root(root)
    cdir_resolved = Path(corpus_dir).resolve()
    contract_resolved = Path(contract_path).resolve()
    if contract_resolved == cdir_resolved or cdir_resolved in contract_resolved.parents:
        _fail('contract: must be outside corpus')
    if not _is_hex(contract_sha):
        _fail('contract_sha256 malformed')
    craw = _read(contract_path, 'contract')
    if _sha(craw) != contract_sha:
        _fail('contract_sha256 mismatch')
    contract = _loads(craw, 'contract')
    _validate_contract(contract)
    contract_hash = _sha(craw)
    q = contract['q01']
    ledger_path = _safe_join(root_r, q['ledger_path'], 'ledger')
    lraw = _read(ledger_path, 'ledger')
    if _sha(lraw) != q['ledger_sha256']:
        _fail('ledger: sha256 mismatch')
    ledger = _loads(lraw, 'ledger')
    if not isinstance(ledger, dict):
        _fail('ledger: object required')
    for k in ('cases', 'scope_controls', 'references', 'source_pins', 'resolved_count', 'c1_verdict', 'visual_acceptance'):
        if k not in ledger:
            _fail('ledger: missing ' + k)
    if type(ledger['resolved_count']) is not int or ledger['resolved_count'] != 0:
        _fail('ledger: resolved_count must be 0')
    if ledger['c1_verdict'] != 'NOT_REVIEWED':
        _fail('ledger: c1_verdict mismatch')
    if ledger['visual_acceptance'] != 'NOT_GRANTED':
        _fail('ledger: visual_acceptance mismatch')
    if not _eq(ledger['source_pins'], contract['q01']['source_pins']):
        _fail('ledger: source_pins differ from contract')
    cases = ledger['cases']
    if not isinstance(cases, list) or len(cases) != 9:
        _fail('ledger: cases must have 9 entries')
    case_ids = []
    for case in cases:
        if not isinstance(case, dict) or not CASE_KEYS.issubset(set(case)):
            _fail('ledger: case missing required fields')
        if 'status' in case or 'verdict' in case:
            _fail('ledger: fictitious case status/verdict not allowed')
        if case['human_verdict'] != 'OPEN_REJECTED':
            _fail('ledger: human_verdict mismatch')
        if case['location_status'] != 'UNCONFIRMED_CONTEXT_ONLY':
            _fail('ledger: location_status mismatch')
        if not isinstance(case['source_bindings'], list) or not isinstance(case['required_layers'], list):
            _fail('ledger: case bindings/layers malformed')
        case_ids.append(case['id'])
    if not _eq(case_ids, q['case_ids']):
        _fail('ledger: case ids differ from contract')
    controls = ledger['scope_controls']
    if not isinstance(controls, list) or len(controls) != 4:
        _fail('ledger: scope_controls must have 4 entries')
    control_ids = []
    for ctl in controls:
        if not isinstance(ctl, dict) or 'id' not in ctl:
            _fail('ledger: control id required')
        control_ids.append(ctl['id'])
    if not _eq(control_ids, q['control_ids']):
        _fail('ledger: control ids differ from contract')
    refs = ledger['references']
    if not isinstance(refs, list) or not all(isinstance(r, dict) for r in refs):
        _fail('ledger: references malformed')
    sources_root_r = _safe_join(root_r, q['sources_root'], 'sources_root')
    parsed_sources = {}
    for pin_key, pin_sha in q['source_pins'].items():
        chosen = _safe_join(root_r, q['sources_root'] + '/' + pin_key, 'source')
        sraw = _read(chosen, 'source')
        if _sha(sraw) != pin_sha:
            _fail('source: sha256 mismatch for ' + pin_key)
        parsed_sources[pin_key] = _loads(sraw, 'source')
    def source_for(path):
        if path in parsed_sources:
            return parsed_sources[path]
        _fail('binding: source path not pinned')
    def check_bindings(bindings, owner):
        if not isinstance(bindings, list):
            _fail(owner + ': source_bindings must be list')
        for b in bindings:
            if not isinstance(b, dict) or set(b) != BINDING_KEYS:
                _fail(owner + ': binding exact keys required')
            if not isinstance(b['path'], str) or not _is_hex(b['sha256']):
                _fail(owner + ': binding path/sha malformed')
            pin = q['source_pins'].get(b['path']) if isinstance(b['path'], str) else None
            if pin is None or pin != b['sha256']:
                _fail(owner + ': binding sha differs from pin')
            doc = source_for(b['path'])
            val = _resolve_pointer(doc, b['pointer'], owner)
            if not _eq(val, b['expected_literal']):
                _fail(owner + ': pointer literal mismatch')
    for case in cases:
        check_bindings(case['source_bindings'], 'case ' + str(case.get('id')))
    for ctl in controls:
        if 'source_bindings' in ctl:
            check_bindings(ctl['source_bindings'], 'control ' + str(ctl.get('id')))
        elif 'bindings' in ctl:
            check_bindings(ctl['bindings'], 'control ' + str(ctl.get('id')))
    for r in refs:
        if 'source_bindings' in r:
            check_bindings(r['source_bindings'], 'reference')
        elif 'bindings' in r:
            check_bindings(r['bindings'], 'reference')
    cdir = Path(corpus_dir)
    if cdir.is_symlink() or not cdir.is_dir():
        _fail('corpus: directory not found')
    corpus_raw = _read(cdir / 'corpus.json', 'corpus')
    manifest_raw = _read(cdir / 'manifest.json', 'manifest')
    corpus = _loads(corpus_raw, 'corpus')
    manifest = _loads(manifest_raw, 'manifest')
    corpus_hash = _sha(corpus_raw)
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS:
        _fail('manifest: exact keys required')
    if manifest['schema'] != 'q17a-manifest.v1' or manifest['contract_sha256'] != contract_hash or manifest['corpus_sha256'] != corpus_hash:
        _fail('manifest: hash/schema mismatch')
    if not isinstance(corpus, dict) or set(corpus) != CORPUS_KEYS:
        _fail('corpus: exact keys required, unknown fields not allowed')
    if corpus['schema'] != 'q17a-corpus.v1' or corpus['contract_sha256'] != contract_hash:
        _fail('corpus: schema/contract hash mismatch')
    if corpus['unit'] != 'm' or corpus['plane'] != 'XZ':
        _fail('corpus: unit/plane mismatch')
    if type(corpus['natural_positive_count']) is not int or corpus['natural_positive_count'] != 0:
        _fail('corpus: natural_positive_count must be 0')
    if corpus['calibration_ready'] is not False:
        _fail('corpus: calibration_ready must be false')
    if type(corpus['resolved_count']) is not int or corpus['resolved_count'] != 0:
        _fail('corpus: resolved_count must be 0')
    if corpus['c1_verdict'] != 'NOT_REVIEWED' or corpus['visual_acceptance'] != 'NOT_GRANTED':
        _fail('corpus: verdict/acceptance mismatch')
    expected_human = []
    for i, case in enumerate(cases):
        expected_human.append({'id': case['id'], 'human_verdict': case['human_verdict'], 'scope': case['scope'], 'location_status': case['location_status'], 'source_bindings': case['source_bindings'], 'geometry_binding': 'GEOMETRY_UNBOUND', 'ledger_pointer': '/cases/' + str(i)})
    if not _eq(corpus['human_references'], expected_human):
        _fail('corpus: human_references differ from ledger projection')
    if not _eq(corpus['scope_controls'], controls):
        _fail('corpus: scope_controls differ from ledger')
    expected_photo = [r for r in refs if r.get('kind') == 'REFERENCE_ONLY']
    if not _eq(corpus['photographic_references'], expected_photo):
        _fail('corpus: photographic_references differ from ledger')
    expected_fixtures = []
    for f in contract['fixtures']:
        ppath = _safe_join(root_r, f['points_file'], 'points')
        praw = _read(ppath, 'points')
        if _sha(praw) != f['points_sha256']:
            _fail('points: sha256 mismatch for ' + f['id'])
        points = _extract_points(_loads(praw, 'points'), 'points')
        nf = {k: v for k, v in f.items() if k not in ('points_file', 'points_sha256')}
        nf['points'] = points
        expected_fixtures.append(nf)
    if not isinstance(corpus['fixtures'], list) or len(corpus['fixtures']) > 20:
        _fail('corpus: fixtures length out of range')
    if not _eq(corpus['fixtures'], expected_fixtures):
        _fail('corpus: fixtures differ from contract')
    expected_total = 0
    expected_total_known = True
    for f in corpus['fixtures']:
        vc = f.get('expected', {}).get('vertex_count') if isinstance(f, dict) and isinstance(f.get('expected'), dict) else None
        if type(vc) is not int:
            expected_total_known = False
            break
        expected_total += vc
    if expected_total_known and expected_total > 4096:
        _fail('corpus: total vertex_count exceeds 4096')
    total = 0
    for f in corpus['fixtures']:
        validate_fixture(f)
        total += f['expected']['vertex_count']
    if total > 4096:
        _fail('corpus: total vertex_count exceeds 4096')
    return {'status': 'VERIFIED_CORPUS_INCOMPLETE_CALIBRATION', 'fixture_count': len(corpus['fixtures']), 'vertex_count': total, 'human_case_count': 9, 'resolved_count': 0, 'natural_positive_count': 0, 'calibration_ready': False, 'c1_verdict': 'NOT_REVIEWED', 'map_acceptance': 'NOT_EVALUATED', 'contract_sha256': contract_hash, 'corpus_sha256': corpus_hash}

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--contract', required=True)
    ap.add_argument('--contract-sha256', required=True)
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--report', required=True)
    a = ap.parse_args(argv)
    report_path = Path(a.report)
    try:
        if report_path.exists() or report_path.is_symlink():
            _fail('report: destination already exists')
        report = verify(a.root, a.contract, a.contract_sha256, a.corpus)
        data = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        with open(report_path, 'xb') as fh:
            fh.write(data)
    except ValueError as e:
        print('REJECTED_CORPUS: ' + str(e), file=sys.stderr)
        return 1
    except OSError as e:
        print('INCONCLUSIVE_IO: ' + str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print('INTERNAL_ERROR: ' + str(e), file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
