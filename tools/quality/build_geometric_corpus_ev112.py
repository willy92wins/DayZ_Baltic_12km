import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

MAX_BYTES = 4 * 1024 * 1024
HEX_RE = re.compile(r'[0-9a-f]{64}')
CONTRACT_KEYS = {'schema', 'unit', 'plane', 'natural_positive_count', 'calibration_ready', 'q01', 'fixtures'}
Q01_KEYS = {'ledger_path', 'ledger_sha256', 'sources_root', 'source_pins', 'case_ids', 'control_ids'}
FIXTURE_KEYS = {'id', 'closed', 'role', 'context', 'features', 'limitation', 'expected', 'points_file', 'points_sha256'}
EXPECTED_KEYS = {'vertex_count', 'edge_squared_lengths', 'nonzero_turns', 'twice_signed_area', 'circle'}
CORPUS_KEYS = {'schema', 'contract_sha256', 'unit', 'plane', 'human_references', 'scope_controls', 'photographic_references', 'fixtures', 'natural_positive_count', 'calibration_ready', 'resolved_count', 'c1_verdict', 'visual_acceptance'}

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
        if isinstance(e, ValueError) and str(e).startswith(('duplicate JSON key', 'invalid JSON constant')):
            raise
        _fail(label + ': invalid JSON: ' + str(e))

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

def _checked_contract(contract_path, contract_sha):
    if not _is_hex(contract_sha):
        _fail('contract_sha256 malformed')
    raw = _read(contract_path, 'contract')
    if _sha(raw) != contract_sha:
        _fail('contract_sha256 mismatch')
    doc = _loads(raw, 'contract')
    _validate_contract(doc)
    return doc, _sha(raw)

def _validate_contract(c):
    if not isinstance(c, dict) or set(c) != CONTRACT_KEYS:
        _fail('contract: exact schema keys required')
    if c['schema'] != 'q17a-contract.v1':
        _fail('contract: schema mismatch')
    if c['unit'] != 'm' or c['plane'] != 'XZ':
        _fail('contract: unit/plane mismatch')
    if type(c['natural_positive_count']) is not int or c['natural_positive_count'] != 0:
        _fail('contract: natural_positive_count must be 0')
    if c['calibration_ready'] is not False:
        _fail('contract: calibration_ready must be false')
    q = c['q01']
    if not isinstance(q, dict) or set(q) != Q01_KEYS:
        _fail('contract: q01 exact keys required')
    if not isinstance(q['ledger_path'], str) or not q['ledger_path']:
        _fail('contract: ledger_path required')
    if not _is_hex(q['ledger_sha256']):
        _fail('contract: ledger_sha256 malformed')
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
        if not isinstance(f['id'], str) or not f['id']:
            _fail('contract: fixture id required')
        ids.append(f['id'])
        if f['id'] in q['case_ids'] or f['id'] in q['control_ids']:
            _fail('contract: fixture id must not be a human/control id')
        if type(f['closed']) is not bool:
            _fail('contract: fixture closed must be bool')
        if not isinstance(f['role'], str) or not isinstance(f['context'], str):
            _fail('contract: fixture role/context required')
        if not isinstance(f['features'], list) or not all(isinstance(x, str) and x for x in f['features']):
            _fail('contract: fixture features malformed')
        if not isinstance(f['limitation'], str) or not f['limitation']:
            _fail('contract: fixture limitation required')
        if not isinstance(f['expected'], dict) or set(f['expected']) != EXPECTED_KEYS:
            _fail('contract: fixture expected exact keys required')
        if not isinstance(f['points_file'], str) or not _is_hex(f['points_sha256']):
            _fail('contract: fixture points binding malformed')
    if len(set(ids)) != len(ids):
        _fail('contract: fixture ids not unique')
    total_expected = 0
    for f in fx:
        vc = f['expected'].get('vertex_count') if isinstance(f['expected'], dict) else None
        if type(vc) is int:
            total_expected += vc
    if total_expected > 4096:
        _fail('contract: total vertex_count exceeds 4096')

def _root(root):
    r = Path(root)
    if r.is_symlink() or not r.is_dir():
        _fail('root: directory not found')
    return r.resolve()

def _safe_join(root_resolved, rel, label):
    if not isinstance(rel, str) or not rel:
        _fail(label + ': relative path required')
    p = Path(rel)
    if p.is_absolute() or rel.startswith('/') or rel.startswith('\\'):
        _fail(label + ': absolute path not allowed')
    if any(part in ('..', '') for part in p.parts):
        _fail(label + ': path escape not allowed')
    cur = root_resolved
    for part in p.parts:
        cur = cur / part
        if cur.is_symlink():
            _fail(label + ': symlink not allowed')
    try:
        resolved = cur.resolve()
    except Exception:
        _fail(label + ': path cannot be resolved')
    if resolved != root_resolved and root_resolved not in resolved.parents:
        _fail(label + ': path escapes root')
    return cur

def _extract_points(doc, label):
    if isinstance(doc, list):
        return doc
    _fail(label + ': points array not found')

def build(root, contract_path, contract_sha, output):
    root_r = _root(root)
    out = Path(output)
    if out.exists() or out.is_symlink():
        _fail('output: destination already exists')
    contract_abs = Path(contract_path).resolve()
    out_resolved = out.resolve()
    if contract_abs == out_resolved or out_resolved in contract_abs.parents:
        _fail('contract: must be outside output')
    contract, contract_hash = _checked_contract(contract_path, contract_sha)
    q = contract['q01']
    ledger_path = _safe_join(root_r, q['ledger_path'], 'ledger')
    ledger_raw = _read(ledger_path, 'ledger')
    if _sha(ledger_raw) != q['ledger_sha256']:
        _fail('ledger: sha256 mismatch')
    ledger = _loads(ledger_raw, 'ledger')
    if not isinstance(ledger, dict):
        _fail('ledger: object required')
    for k in ('cases', 'scope_controls', 'references', 'source_pins', 'resolved_count', 'c1_verdict', 'visual_acceptance'):
        if k not in ledger:
            _fail('ledger: missing ' + k)
    if ledger['resolved_count'] != 0 or type(ledger['resolved_count']) is not int:
        _fail('ledger: resolved_count must be 0')
    if ledger['c1_verdict'] != 'NOT_REVIEWED':
        _fail('ledger: c1_verdict mismatch')
    if ledger['visual_acceptance'] != 'NOT_GRANTED':
        _fail('ledger: visual_acceptance mismatch')
    cases = ledger['cases']
    if not isinstance(cases, list) or len(cases) != 9:
        _fail('ledger: cases must have 9 entries')
    human = []
    for i, case in enumerate(cases):
        if not isinstance(case, dict):
            _fail('ledger: case must be object')
        for k in ('id', 'human_verdict', 'scope', 'location_status', 'source_bindings'):
            if k not in case:
                _fail('ledger: case missing ' + k)
        human.append({'id': copy.deepcopy(case['id']), 'human_verdict': copy.deepcopy(case['human_verdict']), 'scope': copy.deepcopy(case['scope']), 'location_status': copy.deepcopy(case['location_status']), 'source_bindings': copy.deepcopy(case['source_bindings']), 'geometry_binding': 'GEOMETRY_UNBOUND', 'ledger_pointer': '/cases/' + str(i)})
    controls = ledger['scope_controls']
    if not isinstance(controls, list) or len(controls) != 4:
        _fail('ledger: scope_controls must have 4 entries')
    refs = ledger['references']
    if not isinstance(refs, list):
        _fail('ledger: references must be list')
    photographic = [copy.deepcopy(r) for r in refs if isinstance(r, dict) and r.get('kind') == 'REFERENCE_ONLY']
    fixtures = []
    for f in contract['fixtures']:
        ppath = _safe_join(root_r, f['points_file'], 'points')
        praw = _read(ppath, 'points')
        if _sha(praw) != f['points_sha256']:
            _fail('points: sha256 mismatch for ' + f['id'])
        pdoc = _loads(praw, 'points')
        points = _extract_points(pdoc, 'points')
        nf = {k: copy.deepcopy(v) for k, v in f.items() if k not in ('points_file', 'points_sha256')}
        nf['points'] = copy.deepcopy(points)
        fixtures.append(nf)
    corpus = {'schema': 'q17a-corpus.v1', 'contract_sha256': contract_hash, 'unit': 'm', 'plane': 'XZ', 'human_references': human, 'scope_controls': copy.deepcopy(controls), 'photographic_references': photographic, 'fixtures': fixtures, 'natural_positive_count': 0, 'calibration_ready': False, 'resolved_count': 0, 'c1_verdict': 'NOT_REVIEWED', 'visual_acceptance': 'NOT_GRANTED'}
    if set(corpus) != CORPUS_KEYS:
        _fail('corpus: internal key error')
    created = False
    try:
        out.mkdir(parents=False, exist_ok=False)
        created = True
        corpus_bytes = (json.dumps(corpus, ensure_ascii=False, indent=2, sort_keys=False) + '\n').encode('utf-8')
        if len(corpus_bytes) > MAX_BYTES:
            _fail('corpus: too large')
        with open(out / 'corpus.json', 'xb') as fh:
            fh.write(corpus_bytes)
        manifest = {'schema': 'q17a-manifest.v1', 'contract_sha256': contract_hash, 'corpus_sha256': _sha(corpus_bytes)}
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False) + '\n').encode('utf-8')
        with open(out / 'manifest.json', 'xb') as fh:
            fh.write(manifest_bytes)
    except Exception:
        if created:
            try:
                for name in ('corpus.json', 'manifest.json'):
                    t = out / name
                    if t.exists():
                        t.unlink()
                out.rmdir()
            except Exception:
                pass
        raise
    return corpus

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--contract', required=True)
    ap.add_argument('--contract-sha256', required=True)
    ap.add_argument('--output', required=True)
    a = ap.parse_args(argv)
    try:
        build(a.root, a.contract, a.contract_sha256, a.output)
    except ValueError as e:
        print('REJECTED_CORPUS: ' + str(e), file=sys.stderr)
        return 1
    except OSError as e:
        print('INCONCLUSIVE_IO: ' + str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print('INTERNAL_ERROR: ' + str(e), file=sys.stderr)
        return 1
    print('CREATED_CORPUS_NOT_MAP_ACCEPTANCE')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
