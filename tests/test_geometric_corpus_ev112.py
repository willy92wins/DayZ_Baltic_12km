import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'quality'))
from build_geometric_corpus_ev112 import build, _extract_points as _build_extract_points
from verify_geometric_corpus_ev112 import measure, validate_fixture, verify, _validate_contract, _extract_points

CONTRACT = ROOT / 'tests' / 'fixtures' / 'q17a' / 'contract.json'
CONTRACT_SHA256 = '5416dbef4547a5dad0fa40c0da90337ec003ebdd73dc61f149a9c8174ed5394a'

def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()

def contract_sha():
    return sha_bytes(CONTRACT.read_bytes())

def load_json(p):
    return json.loads(Path(p).read_bytes().decode('utf-8'))

def write_json(p, obj):
    Path(p).write_bytes((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def fixture(points, expected, fid='manual', closed=False, role='SYNTHETIC_ENGINEERING', context='UNCLASSIFIED_SHORE'):
    return {'id': fid, 'closed': closed, 'role': role, 'context': context, 'features': ['open_polyline'], 'limitation': 'Synthetic fixture only; no source or human coverage claimed.', 'expected': expected, 'points': points}

L_POINTS = [[0, 0], [6, 0], [6, 2], [2, 2], [2, 6], [0, 6]]
L_EXPECTED = {'vertex_count': 6, 'edge_squared_lengths': ['36', '4', '16', '16', '4', '36'], 'nonzero_turns': [[0, 1], [1, 1], [2, 1], [3, -1], [4, 1], [5, 1]], 'twice_signed_area': '40', 'circle': None}

class CorpusCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.out = self.base / 'out'
        build(ROOT, CONTRACT, contract_sha(), self.out)
        self.corpus_path = self.out / 'corpus.json'
        self.corpus = load_json(self.corpus_path)
    def tearDown(self):
        self.tmp.cleanup()
    def rewrite_corpus(self, obj, fix_manifest=True):
        data = (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        self.corpus_path.write_bytes(data)
        if fix_manifest:
            m = load_json(self.out / 'manifest.json')
            m['corpus_sha256'] = sha_bytes(data)
            write_json(self.out / 'manifest.json', m)
    def assert_verify_rejected(self, obj):
        self.rewrite_corpus(obj)
        with self.assertRaises(ValueError):
            verify(ROOT, CONTRACT, contract_sha(), self.out)
    def sandbox(self):
        sb = self.base / 'sandbox'
        contract = load_json(CONTRACT)
        cpath = sb / 'tests' / 'fixtures' / 'q17a' / 'contract.json'
        cpath.parent.mkdir(parents=True)
        write_json(cpath, contract)
        ledger_rel = contract['q01']['ledger_path']
        (sb / ledger_rel).parent.mkdir(parents=True, exist_ok=True)
        (sb / ledger_rel).write_bytes((ROOT / ledger_rel).read_bytes())
        for pin in contract['q01']['source_pins']:
            src = ROOT / contract['q01']['sources_root'] / pin
            dest = sb / contract['q01']['sources_root'] / pin
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src.read_bytes())
        for f in contract['fixtures']:
            dest = sb / f['points_file']
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((ROOT / f['points_file']).read_bytes())
        out2 = self.base / 'sandbox_out'
        build(sb, cpath, sha_bytes(cpath.read_bytes()), out2)
        return sb, cpath, out2

class TestPositive(CorpusCase):
    def test_build_and_verify_report(self):
        r = verify(ROOT, CONTRACT, contract_sha(), self.out)
        self.assertEqual(r['status'], 'VERIFIED_CORPUS_INCOMPLETE_CALIBRATION')
        self.assertEqual(r['fixture_count'], 11)
        self.assertEqual(r['vertex_count'], 66)
        self.assertEqual(r['human_case_count'], 9)
        self.assertEqual(r['resolved_count'], 0)
        self.assertEqual(r['natural_positive_count'], 0)
        self.assertEqual(r['calibration_ready'], False)
        self.assertEqual(r['c1_verdict'], 'NOT_REVIEWED')
        self.assertEqual(r['map_acceptance'], 'NOT_EVALUATED')
        self.assertEqual(contract_sha(), CONTRACT_SHA256)
        self.assertEqual(r['contract_sha256'], CONTRACT_SHA256)
        self.assertEqual(set(self.corpus), {'schema', 'contract_sha256', 'unit', 'plane', 'human_references', 'scope_controls', 'photographic_references', 'fixtures', 'natural_positive_count', 'calibration_ready', 'resolved_count', 'c1_verdict', 'visual_acceptance'})
        self.assertEqual(len(self.corpus['human_references']), 9)
        self.assertEqual(len(self.corpus['scope_controls']), 4)
        self.assertEqual(sum(f['expected']['vertex_count'] for f in self.corpus['fixtures']), 66)
        for h in self.corpus['human_references']:
            self.assertEqual(h['geometry_binding'], 'GEOMETRY_UNBOUND')
            self.assertEqual('coordinates' in h, False)
            self.assertEqual('automatic_evidence' in h, False)
    def test_manual_measure_and_fixture(self):
        pts = [[0, 0], [4, 0], [4, 3]]
        exp = {'vertex_count': 3, 'edge_squared_lengths': ['16', '9'], 'nonzero_turns': [[1, 1]], 'twice_signed_area': None, 'circle': None}
        self.assertEqual(measure(pts, False), {'vertex_count': 3, 'edge_squared_lengths': ['16', '9'], 'nonzero_turns': [[1, 1]], 'twice_signed_area': None})
        self.assertEqual(validate_fixture(fixture(pts, exp)), True)
        self.assertEqual(measure(L_POINTS, True), {'vertex_count': 6, 'edge_squared_lengths': L_EXPECTED['edge_squared_lengths'], 'nonzero_turns': L_EXPECTED['nonzero_turns'], 'twice_signed_area': '40'})
    def test_rational_and_circle(self):
        pts = [[5, 0], [3, 4], [0, 5], [-3, 4], [-5, 0]]
        got = measure(pts, False)
        self.assertEqual(got['edge_squared_lengths'], ['20', '10', '10', '20'])
        exp = {'vertex_count': 5, 'edge_squared_lengths': ['20', '10', '10', '20'], 'nonzero_turns': [[1, 1], [2, 1], [3, 1]], 'twice_signed_area': None, 'circle': {'center': [0, 0], 'radius_squared': '25'}}
        self.assertEqual(validate_fixture(fixture(pts, exp, fid='arc')), True)
        pts2 = [['1/2', 0], [2, 0]]
        self.assertEqual(measure(pts2, False)['edge_squared_lengths'], ['9/4'])

class TestMetamorphic(unittest.TestCase):
    def test_rotation(self):
        pts = [[-z, x] for x, z in L_POINTS]
        self.assertEqual(measure(pts, True), measure(L_POINTS, True))
        self.assertEqual(validate_fixture(fixture(pts, copy.deepcopy(L_EXPECTED), fid='meta_l', closed=True)), True)
    def test_translation(self):
        pts = [[x + 17, z - 23] for x, z in L_POINTS]
        self.assertEqual(measure(pts, True), {'vertex_count': 6, 'edge_squared_lengths': ['36', '4', '16', '16', '4', '36'], 'nonzero_turns': L_EXPECTED['nonzero_turns'], 'twice_signed_area': '40'})
        self.assertEqual(validate_fixture(fixture(pts, copy.deepcopy(L_EXPECTED), fid='meta_l', closed=True)), True)
    def test_closed_cyclic_shift2(self):
        pts = L_POINTS[2:] + L_POINTS[:2]
        exp = {'vertex_count': 6, 'edge_squared_lengths': ['16', '16', '4', '36', '36', '4'], 'nonzero_turns': [[0, 1], [1, -1], [2, 1], [3, 1], [4, 1], [5, 1]], 'twice_signed_area': '40', 'circle': None}
        self.assertEqual(measure(pts, True), {'vertex_count': 6, 'edge_squared_lengths': exp['edge_squared_lengths'], 'nonzero_turns': exp['nonzero_turns'], 'twice_signed_area': '40'})
        self.assertEqual(validate_fixture(fixture(pts, exp, fid='meta_l', closed=True)), True)
    def test_reverse_full_order(self):
        # q_j = p_{n-1-j}; turn at q_j is sign-flipped turn of p_{n-1-j}
        pts = list(reversed(L_POINTS))
        exp = {'vertex_count': 6, 'edge_squared_lengths': ['4', '16', '16', '4', '36', '36'], 'nonzero_turns': [[0, -1], [1, -1], [2, 1], [3, -1], [4, -1], [5, -1]], 'twice_signed_area': '-40', 'circle': None}
        self.assertEqual(measure(pts, True), {'vertex_count': 6, 'edge_squared_lengths': exp['edge_squared_lengths'], 'nonzero_turns': exp['nonzero_turns'], 'twice_signed_area': '-40'})
        self.assertEqual(validate_fixture(fixture(pts, exp, fid='meta_l', closed=True)), True)
    def test_midpoint_subdivision_closed(self):
        # Insert midpoint of each closed edge; original vertex p_i lands at index 2i, lengths squared /4, area unchanged. Midpoints lie on chords, so circle is None, not the curved circle.
        pts = []
        for i, p in enumerate(L_POINTS):
            q = L_POINTS[(i + 1) % len(L_POINTS)]
            pts.append(p)
            pts.append([(p[0] + q[0]) // 2, (p[1] + q[1]) // 2])
        exp = {'vertex_count': 12, 'edge_squared_lengths': ['9', '9', '1', '1', '4', '4', '4', '4', '1', '1', '9', '9'], 'nonzero_turns': [[0, 1], [2, 1], [4, 1], [6, -1], [8, 1], [10, 1]], 'twice_signed_area': '40', 'circle': None}
        self.assertEqual(measure(pts, True), {'vertex_count': 12, 'edge_squared_lengths': exp['edge_squared_lengths'], 'nonzero_turns': exp['nonzero_turns'], 'twice_signed_area': '40'})
        self.assertEqual(validate_fixture(fixture(pts, exp, fid='meta_l', closed=True)), True)
    def test_midpoint_subdivision_open(self):
        pts0 = [[0, 0], [4, 0], [4, 3]]
        pts = [pts0[0], [2, 0], pts0[1], [4, '3/2'], pts0[2]]
        exp = {'vertex_count': 5, 'edge_squared_lengths': ['4', '4', '9/4', '9/4'], 'nonzero_turns': [[2, 1]], 'twice_signed_area': None, 'circle': None}
        self.assertEqual(measure(pts, False), {'vertex_count': 5, 'edge_squared_lengths': ['4', '4', '9/4', '9/4'], 'nonzero_turns': [[2, 1]], 'twice_signed_area': None})
        self.assertEqual(validate_fixture(fixture(pts, exp, fid='open_l')), True)

class TestNegatives(CorpusCase):
    def test_omit_and_duplicate_human(self):
        c = copy.deepcopy(self.corpus); c['human_references'].pop(); self.assert_verify_rejected(c)
        c = copy.deepcopy(self.corpus); c['human_references'].append(copy.deepcopy(c['human_references'][0])); self.assert_verify_rejected(c)
    def test_fake_coords_and_avatar_binding(self):
        c = copy.deepcopy(self.corpus); c['human_references'][0]['coordinates'] = [0, 0]; self.assert_verify_rejected(c)
        c = copy.deepcopy(self.corpus); c['human_references'][0]['geometry_binding'] = 'AVATAR'; self.assert_verify_rejected(c)
    def test_scope_borrow_promote_fake_flags(self):
        c = copy.deepcopy(self.corpus); c['human_references'][6]['scope'] = 'road-49'; self.assert_verify_rejected(c)
        c = copy.deepcopy(self.corpus); c['c1_verdict'] = 'ACCEPTED'; self.assert_verify_rejected(c)
        c = copy.deepcopy(self.corpus); c['natural_positive_count'] = 1; self.assert_verify_rejected(c)
        c = copy.deepcopy(self.corpus); c['calibration_ready'] = True; self.assert_verify_rejected(c)
        c = copy.deepcopy(self.corpus); c['resolved_count'] = 1; self.assert_verify_rejected(c)
    def test_synthetic_covers_resolves_and_unknown(self):
        c = copy.deepcopy(self.corpus); c['fixtures'][0]['covers'] = ['NARVA-VIS-01']; self.assert_verify_rejected(c)
        c = copy.deepcopy(self.corpus); c['fixtures'][0]['resolves'] = ['NARVA-VIS-01']; self.assert_verify_rejected(c)
        c = copy.deepcopy(self.corpus); c['extra'] = 1; self.assert_verify_rejected(c)
        c = copy.deepcopy(self.corpus); c['fixtures'][0]['unknown'] = 1; self.assert_verify_rejected(c)
    def test_fixture_semantic_mutations_verify_and_direct(self):
        c = copy.deepcopy(self.corpus); c['fixtures'][1]['expected']['nonzero_turns'] = [t for t in c['fixtures'][1]['expected']['nonzero_turns'] if t[0] != 0]; self.assert_verify_rejected(c)
        with self.assertRaises(ValueError):
            validate_fixture(c['fixtures'][1])
        c = copy.deepcopy(self.corpus); c['fixtures'][0]['points'][0][0] = 999; self.assert_verify_rejected(c)
        with self.assertRaises(ValueError):
            validate_fixture(c['fixtures'][0])
        c = copy.deepcopy(self.corpus); c['fixtures'][1]['closed'] = False; self.assert_verify_rejected(c)
        with self.assertRaises(ValueError):
            validate_fixture(c['fixtures'][1])
    def test_swapped_and_context_change(self):
        c = copy.deepcopy(self.corpus); c['fixtures'][0], c['fixtures'][1] = c['fixtures'][1], c['fixtures'][0]; self.assert_verify_rejected(c)
        c = copy.deepcopy(self.corpus); c['fixtures'][7]['context'] = 'DESIGNED_STRUCTURE'; self.assert_verify_rejected(c)
        bad = fixture([[0, 0], [1, 0]], {'vertex_count': 2, 'edge_squared_lengths': ['1'], 'nonzero_turns': [], 'twice_signed_area': None, 'circle': None}, context='RIVER')
        with self.assertRaises(ValueError):
            validate_fixture(bad)
    def test_manifest_corrupt_and_comutated(self):
        m = load_json(self.out / 'manifest.json'); m['corpus_sha256'] = '0' * 64; write_json(self.out / 'manifest.json', m)
        with self.assertRaises(ValueError):
            verify(ROOT, CONTRACT, contract_sha(), self.out)
        c = copy.deepcopy(self.corpus); c['c1_verdict'] = 'ACCEPTED'; self.assert_verify_rejected(c)
    def test_malformed_contract_sha(self):
        with self.assertRaises(ValueError):
            verify(ROOT, CONTRACT, 'XYZ', self.out)
        with self.assertRaises(ValueError):
            build(ROOT, CONTRACT, 'not-a-hash', self.base / 'nope')
        with self.assertRaises(ValueError):
            verify(ROOT, CONTRACT, '0' * 64, self.out)
    def test_direct_measure_rejections(self):
        with self.assertRaises(ValueError):
            measure([[0, 0], [0, 0]], False)
        with self.assertRaisesRegex(ValueError, 'reversal'):
            measure([[0, 0], [4, 0], [2, 0]], False)
        with self.assertRaises(ValueError):
            measure([[0, 0], [4, 0], [0, 0]], False)
        with self.assertRaises(ValueError):
            measure([[0, 0], [1, 0]], 1)
        with self.assertRaises(ValueError):
            measure([[0, 0], [float('nan'), 1]], False)
        with self.assertRaises(ValueError):
            measure([[0, 0], [None, 1]], False)
        with self.assertRaises(ValueError):
            measure([[0, 0]], False)
        bad = fixture([[0, 0], [1, 0]], {'vertex_count': 2, 'edge_squared_lengths': ['1'], 'nonzero_turns': [], 'twice_signed_area': None, 'circle': None}); bad['closed'] = 1
        with self.assertRaises(ValueError):
            validate_fixture(bad)
        bad2 = fixture([[0, 0], [True, 0]], {'vertex_count': 2, 'edge_squared_lengths': ['1'], 'nonzero_turns': [], 'twice_signed_area': None, 'circle': None})
        with self.assertRaises(ValueError):
            validate_fixture(bad2)
    def test_source_hash_drift_sandbox(self):
        sb, cpath, out2 = self.sandbox()
        contract = load_json(cpath)
        pin = next(iter(contract['q01']['source_pins']))
        target = sb / contract['q01']['sources_root'] / pin
        target.write_bytes(target.read_bytes() + b' ')
        with self.assertRaises(ValueError):
            verify(sb, cpath, sha_bytes(cpath.read_bytes()), out2)
    def test_source_pointer_wrong_sandbox(self):
        sb, cpath, out2 = self.sandbox()
        contract = load_json(cpath)
        ledger_path = sb / contract['q01']['ledger_path']
        ledger = load_json(ledger_path)
        binding = ledger['cases'][0]['source_bindings'][0]
        pin = binding['path']
        self.assertIn(pin, contract['q01']['source_pins'])
        src_path = sb / contract['q01']['sources_root'] / pin
        doc = load_json(src_path)
        toks = binding['pointer'][1:].split('/')
        cur = doc
        for raw in toks[:-1]:
            tok = raw.replace('~1', '/').replace('~0', '~')
            cur = cur[int(tok)] if isinstance(cur, list) else cur[tok]
        last = toks[-1].replace('~1', '/').replace('~0', '~')
        if isinstance(cur, list):
            cur[int(last)] = '__MUTATED__'
        else:
            cur[last] = '__MUTATED__'
        write_json(src_path, doc)
        new_sha = sha_bytes(src_path.read_bytes())
        contract['q01']['source_pins'][pin] = new_sha
        ledger['source_pins'][pin] = new_sha
        for case in ledger['cases']:
            for b in case['source_bindings']:
                if b['path'] == binding['path']:
                    b['sha256'] = new_sha
        for coll in ('scope_controls', 'references'):
            for item in ledger.get(coll, []):
                for key in ('source_bindings', 'bindings'):
                    for b in item.get(key, []):
                        if b['path'] == binding['path']:
                            b['sha256'] = new_sha
        write_json(ledger_path, ledger)
        contract['q01']['ledger_sha256'] = sha_bytes(ledger_path.read_bytes())
        write_json(cpath, contract)
        out3 = self.base / 'sandbox_out3'
        build(sb, cpath, sha_bytes(cpath.read_bytes()), out3)
        with self.assertRaisesRegex(ValueError, 'pointer literal mismatch'):
            verify(sb, cpath, sha_bytes(cpath.read_bytes()), out3)

    def test_comutated_contract_corpus_manifest_old_sha_rejected(self):
        sb, cpath, out2 = self.sandbox()
        old_sha = sha_bytes(cpath.read_bytes())
        contract = load_json(cpath)
        new_context = 'DESIGNED_STRUCTURE' if contract['fixtures'][0]['context'] != 'DESIGNED_STRUCTURE' else 'UNCLASSIFIED_SHORE'
        contract['fixtures'][0]['context'] = new_context
        write_json(cpath, contract)
        corpus = load_json(out2 / 'corpus.json')
        corpus['fixtures'][0]['context'] = new_context
        new_sha = sha_bytes(cpath.read_bytes())
        corpus['contract_sha256'] = new_sha
        data = (json.dumps(corpus, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        (out2 / 'corpus.json').write_bytes(data)
        manifest = load_json(out2 / 'manifest.json')
        manifest['corpus_sha256'] = sha_bytes(data)
        manifest['contract_sha256'] = new_sha
        write_json(out2 / 'manifest.json', manifest)
        with self.assertRaisesRegex(ValueError, 'contract_sha256 mismatch'):
            verify(sb, cpath, old_sha, out2)
        self.assertEqual(verify(sb, cpath, new_sha, out2)['status'], 'VERIFIED_CORPUS_INCOMPLETE_CALIBRATION')
    def test_contract_total_vertex_limit_strict(self):
        contract = load_json(CONTRACT)
        contract['fixtures'] = copy.deepcopy(contract['fixtures'][:2])
        for f in contract['fixtures']:
            f['expected']['vertex_count'] = 3000
        with self.assertRaisesRegex(ValueError, 'total vertex_count exceeds 4096'):
            _validate_contract(contract)
    def test_points_object_wrapper_rejected(self):
        with self.assertRaises(ValueError):
            _extract_points({'points': [[0, 0], [1, 0]]}, 'points')
        with self.assertRaises(ValueError):
            _build_extract_points({'points': [[0, 0], [1, 0]]}, 'points')
    def test_synthetic_fixture_human_id_rejected(self):
        bad = fixture([[0, 0], [1, 0]], {'vertex_count': 2, 'edge_squared_lengths': ['1'], 'nonzero_turns': [], 'twice_signed_area': None, 'circle': None}, fid='NARVA-VIS-01')
        with self.assertRaisesRegex(ValueError, 'human/control id'):
            validate_fixture(bad)
    def test_source_live_divergent_ignored_and_snapshot_required(self):
        sb, cpath, out2 = self.sandbox()
        contract = load_json(cpath)
        pin = next(iter(contract['q01']['source_pins']))
        live = sb / pin
        live.parent.mkdir(parents=True, exist_ok=True)
        live.write_bytes(b'not-the-frozen-source')
        r = verify(sb, cpath, sha_bytes(cpath.read_bytes()), out2)
        self.assertEqual(r['status'], 'VERIFIED_CORPUS_INCOMPLETE_CALIBRATION')
        live.write_bytes((sb / contract['q01']['sources_root'] / pin).read_bytes())
        (sb / contract['q01']['sources_root'] / pin).unlink()
        with self.assertRaises(ValueError):
            verify(sb, cpath, sha_bytes(cpath.read_bytes()), out2)
    def test_contract_inside_corpus_rejected_before_parse(self):
        inside = self.out / 'contract.json'
        inside.write_bytes(CONTRACT.read_bytes())
        with self.assertRaisesRegex(ValueError, 'must be outside corpus'):
            verify(ROOT, inside, sha_bytes(inside.read_bytes()), self.out)

if __name__ == '__main__':
    unittest.main()
