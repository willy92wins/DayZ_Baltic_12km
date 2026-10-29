import hashlib
import io
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock
import zipfile
import numpy as np
from numpy.lib import format as npformat
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'quality'))
import shore_numeric_discovery_ev112 as m
ORACLE_PATH = ROOT / 'tests' / 'fixtures' / 'q02b0' / 'oracles.json'
# Fixture metrology only, justified for these oracles: |coord| <= 240, h <= 96,
# <= 7 edges per chain, shortest edge 30 m, and at most about 100 Decimal sqrt/divide
# operations per walk, so prec-80 rounding is around 1e-76 and 1e-60 is conservative.
# TOL100 follows the same argument at prec 100. Neither tolerance is a final bound,
# a map threshold, or a float-map threshold. Historical R0 failure mode: comparing
# formatted strings such as -6.00 versus -6 and calling a nonexistent write_magic API;
# these tests compare Decimal values and use only the verified header API below.
TOL80 = Decimal('1e-60')
TOL100 = Decimal('1e-80')
def sha(data):
    return hashlib.sha256(data).hexdigest()
def sha_file(p):
    return sha(Path(p).read_bytes())
def dec_pt(v):
    return None if v is None else [Decimal(x) for x in v]
def synth_arrays(closed_mismatch=False):
    pts = np.array([[-10, 0], [0, 0], [10, 0], [0, 0], [10, 0], [10, 10], [0, 10], [0, 9 if closed_mismatch else 0], [5, 5], [5, 5]], dtype=np.float64)
    # Correct source contract for both variants: diff(chain_offsets) == diff(point_offsets)-1.
    return {'point_offsets': np.array([0, 3, 8, 10], dtype=np.int64), 'chain_offsets': np.array([0, 2, 6, 7], dtype=np.int64), 'chain_points': pts, 'closed': np.array([False, True, False])}
def write_npz(path, arrays):
    np.savez(path, **arrays)
def make_contract(tmp, npz_path, oracle_path=ORACLE_PATH, oracle_bytes=None, limits_override=None):
    if oracle_bytes is None:
        oracle_bytes = Path(oracle_path).read_bytes()
        oracle_file = Path(oracle_path)
    else:
        oracle_file = Path(tmp) / 'oracles.json'
        oracle_file.write_bytes(oracle_bytes)
    limits = {'archive_bytes': 33554432, 'required_uncompressed_bytes': 33554432, 'header_bytes': 10000, 'members': 128, 'seconds': 30, 'rss_bytes': 536870912}
    if limits_override:
        limits.update(limits_override)
    contract = {'schema': 'q02b0-discovery-contract.v1', 'npz_path': str(npz_path), 'npz_sha256': sha_file(npz_path), 'oracle_path': str(oracle_file), 'oracle_sha256': sha(oracle_bytes), 'h_set': [6, 12, 24, 48, 96], 'decimal_precisions': [80, 100], 'limits': limits, 'required_keys': ['point_offsets', 'chain_offsets', 'chain_points', 'closed'], 'result_status': 'NUMERIC_DISCOVERY_ONLY', 'calibration_ready': False, 'natural_positive_count': 0}
    cpath = Path(tmp) / 'contract.json'
    data = json.dumps(contract).encode()
    cpath.write_bytes(data)
    return cpath, sha(data)
def npy_bytes(arr):
    bio = io.BytesIO()
    npformat.write_array(bio, np.asarray(arr))
    return bio.getvalue()
def write_custom_npz(path, arrays, overrides=None, extra=None):
    overrides = overrides or {}
    with zipfile.ZipFile(path, 'w') as z:
        for k, v in arrays.items():
            z.writestr(k + '.npy', overrides.get(k, npy_bytes(v)))
        for name, data in (extra or {}).items():
            z.writestr(name, data)
def bad_version_bytes():
    d = b"{'descr': '<f8', 'fortran_order': False, 'shape': (2, 2), }"
    pad = (64 - ((10 + len(d) + 1) % 64)) % 64
    header = d + b' ' * pad + bytes([10])
    return bytes([147]) + b'NUMPY' + bytes([1, 99]) + len(header).to_bytes(2, 'little') + header + b'1234'
class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(ORACLE_PATH.is_file(), 'repo fixture tests/fixtures/q02b0/oracles.json is mandatory')
    def run_synth(self, arrays=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        npz = Path(tmp.name) / 'synth.npz'
        write_npz(npz, arrays if arrays is not None else synth_arrays())
        cpath, csha = make_contract(tmp.name, npz)
        return m.discover(str(cpath), csha), npz
    def expect_error(self, fn):
        try:
            fn()
        except m.DiscoveryError as e:
            self.assertIn('INCONCLUSIVE', str(e))
            return
        self.fail('expected DiscoveryError')
    def test_oracle_anchors_and_census(self):
        report, _ = self.run_synth()
        self.assertEqual(report['status'], 'NUMERIC_DISCOVERY_ONLY')
        self.assertFalse(report['calibration_ready'])
        self.assertEqual(report['natural_positive_count'], 0)
        self.assertEqual(report['physical_hypothesis'], 'NOT_EVALUATED')
        self.assertTrue(report['no_map_changes'])
        self.assertEqual(report['oracles']['query_count'], 30)
        self.assertEqual(report['oracles']['coincident_support_count'], 5)
        self.assertEqual(report['oracles']['insufficient_support_count'], 1)
        self.assertEqual(report['oracles']['degenerate_count'], 0)
        self.assertEqual(report['bound_status'], 'PENDING_REVIEW_NOT_APPROVED')
        rec = {(r['fixture_id'], r['h']): r for r in report['oracles']['records']}
        for key, r in rec.items():
            self.assertTrue(r['state_matches_expected'], key)
            self.assertNotEqual(r['state'], 'DEGENERATE', key)
            self.assertNotEqual(r['float_state'], 'DEGENERATE', key)
            if r['reference_to_walk100_max_abs_diff'] is not None:
                self.assertLess(Decimal(r['reference_to_walk100_max_abs_diff']), TOL100, key)
            if r['decimal80_to_100_max_abs_diff'] is not None:
                self.assertLess(Decimal(r['decimal80_to_100_max_abs_diff']), TOL80, key)
            self.assertIsInstance(r['metrics_decimal100']['angle_rad_float'], (float, type(None)))
        straight = rec[('straight', 6)]['metrics_decimal100']
        self.assertEqual(Decimal(straight['cross']), 0)
        self.assertEqual(Decimal(straight['chord_deficit']), 0)
        left = rec[('right_l', 6)]
        self.assertEqual(dec_pt(left['a_walk_decimal100']), [Decimal(-6), Decimal(0)])
        self.assertEqual(dec_pt(left['c_walk_decimal100']), [Decimal(0), Decimal(6)])
        seam = rec[('square_seam', 6)]
        self.assertEqual(dec_pt(seam['a_walk_decimal100']), [Decimal(0), Decimal(6)])
        self.assertEqual(dec_pt(seam['c_walk_decimal100']), [Decimal(6), Decimal(0)])
        spike = rec[('spike', 6)]
        self.assertEqual(spike['state'], 'COINCIDENT_SUPPORT')
        self.assertEqual(Decimal(spike['metrics_decimal100']['side_ac_m']), 0)
        self.assertIsNone(spike['metrics_decimal100']['deviation_m'])
        self.assertIsNone(spike['metrics_decimal100']['curvature_per_m'])
        self.assertIn('AC_ZERO', spike['metrics_decimal100']['undefined_reasons'])
        arc = rec[('rational_arc', 48)]
        self.assertLess(Decimal(arc['reference_to_walk100_max_abs_diff']), TOL100)
        stair = rec[('oblique_stair', 96)]
        self.assertEqual(stair['state'], 'DEFINED')
        self.assertLess(Decimal(stair['reference_to_walk100_max_abs_diff']), TOL100)
        self.assertEqual(rec[('rational_arc', 96)]['state'], 'INSUFFICIENT_SUPPORT')
        self.assertIsNone(rec[('rational_arc', 96)]['float64_to_walk100_max_abs_diff'])
    def test_npz_metadata_and_sources_intact(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        npz = Path(tmp.name) / 's.npz'; write_npz(npz, synth_arrays())
        cpath, csha = make_contract(tmp.name, npz)
        before = (sha_file(npz), sha_file(ORACLE_PATH))
        report = m.discover(str(cpath), csha)
        self.assertEqual((sha_file(npz), sha_file(ORACLE_PATH)), before)
        self.assertEqual(report['npz_sha256_before'], report['npz_sha256_after'])
        meta = report['npz']
        self.assertEqual(meta['chain_count'], 3)
        self.assertEqual(meta['core_vertex_count'], 9)
        self.assertEqual(meta['segment_count'], 7)
        self.assertEqual(meta['positive_segment_count'], 6)
        self.assertEqual(meta['zero_segment_count'], 1)
        self.assertEqual(meta['candidate_window_rows_upper'], 45)
        self.assertEqual(meta['closure_mismatch_count'], 0)
        self.assertEqual(meta['degenerate_chain_count'], 1)
        self.assertEqual(meta['degenerate_reason_counts']['zero_segment'], 1)
        self.assertEqual(set(meta['arrays']), {'point_offsets', 'chain_offsets', 'chain_points', 'closed'})
    def test_closed_mismatch_is_retained_diagnostic(self):
        # chain_offsets are the immutable correct [0, 2, 6, 7] here too; mismatch is diagnosed, not welded.
        report, _ = self.run_synth(synth_arrays(closed_mismatch=True))
        self.assertEqual(report['npz']['closure_mismatch_count'], 1)
        self.assertEqual(report['npz']['degenerate_reason_counts']['closure_mismatch'], 1)
        self.assertEqual(report['npz']['segment_count'], 7)
        self.assertEqual(report['npz']['core_vertex_count'], 10)
    def test_old_corecount_offsets_rejected(self):
        a = synth_arrays(); a['chain_offsets'] = np.array([0, 3, 7, 9], dtype=np.int64)
        with tempfile.TemporaryDirectory() as td:
            npz = Path(td) / 's.npz'; write_npz(npz, a)
            cpath, csha = make_contract(td, npz)
            self.expect_error(lambda: m.discover(str(cpath), csha))
    def test_pin_before_parse_and_strict_json(self):
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / 'c.json'; bad.write_bytes(b'{not json')
            self.expect_error(lambda: m.discover(str(bad), '0' * 64))
            dup = Path(td) / 'd.json'; data = b'{"a":1,"a":2}'
            dup.write_bytes(data)
            self.expect_error(lambda: m.discover(str(dup), sha(data)))
            nan = Path(td) / 'n.json'; data = b'{"a":NaN}'
            nan.write_bytes(data)
            self.expect_error(lambda: m.discover(str(nan), sha(data)))
    def test_zip_duplicate_and_declared_oversize(self):
        with tempfile.TemporaryDirectory() as td:
            arrays = synth_arrays()
            dup = Path(td) / 'dup.npz'
            with zipfile.ZipFile(dup, 'w') as z:
                for k, v in arrays.items():
                    z.writestr(k + '.npy', npy_bytes(v))
                z.writestr('closed.npy', npy_bytes(arrays['closed']))
            cpath, csha = make_contract(td, dup)
            self.expect_error(lambda: m.discover(str(cpath), csha))
            big = Path(td) / 'big.npz'
            bio = io.BytesIO()
            # Verified runtime API: this header call writes the complete magic internally; do not add magic.
            npformat.write_array_header_1_0(bio, {'descr': '<f8', 'fortran_order': False, 'shape': (3000000, 2)})
            bio.write(b'1234')
            write_custom_npz(big, arrays, overrides={'chain_points': bio.getvalue()})
            cpath, csha = make_contract(td, big)
            self.expect_error(lambda: m.discover(str(cpath), csha))
    def test_corrupt_arrays_and_nonfinite(self):
        cases = []
        a = synth_arrays(); a['chain_points'] = a['chain_points'].astype(np.float32); cases.append(a)
        a = synth_arrays(); a['chain_points'] = np.zeros((10, 3)); cases.append(a)
        a = synth_arrays(); a['point_offsets'] = np.array([1, 3, 8, 10]); cases.append(a)
        a = synth_arrays(); a['closed'] = np.array([0, 1, 0]); cases.append(a)
        a = synth_arrays(); a['chain_points'] = a['chain_points'].copy(); a['chain_points'][0, 0] = np.inf; cases.append(a)
        for arr in cases:
            with tempfile.TemporaryDirectory() as td:
                npz = Path(td) / 's.npz'; write_npz(npz, arr)
                cpath, csha = make_contract(td, npz)
                self.expect_error(lambda: m.discover(str(cpath), csha))
    def test_zip_backslash_version_and_structured_object_rejected(self):
        arrays = synth_arrays()
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'a.npz'; write_custom_npz(p, arrays, extra={'bad' + chr(92) + 'closed.npy': npy_bytes(arrays['closed'])})
            cpath, csha = make_contract(td, p); self.expect_error(lambda: m.discover(str(cpath), csha))
            p = Path(td) / 'b.npz'; write_custom_npz(p, arrays, overrides={'chain_points': bad_version_bytes()})
            cpath, csha = make_contract(td, p); self.expect_error(lambda: m.discover(str(cpath), csha))
            structured = np.zeros((2,), dtype=[('x', '<f8'), ('y', object)])
            p = Path(td) / 'c.npz'; write_custom_npz(p, arrays, overrides={'closed': npy_bytes(structured)})
            cpath, csha = make_contract(td, p); self.expect_error(lambda: m.discover(str(cpath), csha))
            p = Path(td) / 'd.npz'; write_custom_npz(p, arrays, extra={'sub/extra.npy': npy_bytes(arrays['closed'])})
            cpath, csha = make_contract(td, p); self.expect_error(lambda: m.discover(str(cpath), csha))
    def test_archive_budget_before_read_with_spy_and_caps(self):
        with tempfile.TemporaryDirectory() as td:
            npz = Path(td) / 's.npz'; write_npz(npz, synth_arrays())
            cpath, csha = make_contract(td, npz, limits_override={'archive_bytes': 8})
            opened = []
            orig_open = Path.open
            def spy(self, *args, **kwargs):
                opened.append(str(self))
                return orig_open(self, *args, **kwargs)
            with mock.patch.object(Path, 'open', spy):
                self.expect_error(lambda: m.discover(str(cpath), csha))
            self.assertNotIn(str(npz), opened)
            cpath, csha = make_contract(td, npz, limits_override={'archive_bytes': 33554433})
            self.expect_error(lambda: m.discover(str(cpath), csha))
            cpath, csha = make_contract(td, npz)
            c = json.loads(cpath.read_bytes()); c['npz_path'] = 'relative.npz'; data = json.dumps(c).encode(); cpath.write_bytes(data)
            self.expect_error(lambda: m.discover(str(cpath), sha(data)))
            cpath, csha = make_contract(td, npz)
            c = json.loads(cpath.read_bytes()); c['natural_positive_count'] = False; data = json.dumps(c).encode(); cpath.write_bytes(data)
            self.expect_error(lambda: m.discover(str(cpath), sha(data)))
    def test_oracle_loss_expression_and_schema_changes(self):
        oracle = json.loads(ORACLE_PATH.read_bytes())
        mutators = [lambda o: o['fixtures'].pop(), lambda o: o['fixtures'][0]['queries'].pop(), lambda o: o['fixtures'][0]['queries'][0]['a_exact'][0][0].update(den=0), lambda o: o.update(natural_positive_count=False), lambda o: o['fixtures'][0]['queries'][0].update(h=6.0)]
        for mutate in mutators:
            with tempfile.TemporaryDirectory() as td:
                npz = Path(td) / 's.npz'; write_npz(npz, synth_arrays())
                o = json.loads(json.dumps(oracle)); mutate(o)
                cpath, csha = make_contract(td, npz, oracle_bytes=json.dumps(o).encode())
                self.expect_error(lambda: m.discover(str(cpath), csha))
        with tempfile.TemporaryDirectory() as td:
            npz = Path(td) / 's.npz'; write_npz(npz, synth_arrays())
            o = json.loads(json.dumps(oracle))
            o['fixtures'][0]['queries'][0]['c_exact'][0][0]['num'] = 7
            cpath, csha = make_contract(td, npz, oracle_bytes=json.dumps(o).encode())
            report = m.discover(str(cpath), csha)
            self.assertEqual(report['status'], 'NUMERIC_DISCOVERY_ONLY')
            r = [x for x in report['oracles']['records'] if x['fixture_id'] == 'straight' and x['h'] == 6][0]
            self.assertGreater(Decimal(r['reference_to_walk100_max_abs_diff']), Decimal('0.5'))
            self.assertIn('straight:6', report['oracles']['reference_divergences_nonzero'])
    def test_degenerate_walks_boundary_and_no_extrapolation(self):
        self.assertEqual(m.walk([[0, 0], [0, 0], [10, 0]], False, 1, 6, 1, 100), ('DEGENERATE', None))
        self.assertEqual(m._walk_float([[0, 0], [0, 0], [10, 0]], False, 1, 6, 1), ('DEGENERATE', None))
        self.assertEqual(m.walk([[0, 0], [10, 0]], True, 0, 6, 1, 100), ('DEGENERATE', None))
        self.assertEqual(m._walk_float([[0, 0], [10, 0]], True, 0, 6, 1), ('DEGENERATE', None))
        square = [[0, 0], [10, 0], [10, 10], [0, 10]]
        self.assertEqual(m.walk(square, True, 0, 20, 1, 100), ('INSUFFICIENT_SUPPORT', None))
        self.assertEqual(m.walk([[0, 0], [10, 0]], False, 0, 12, 1, 100), ('INSUFFICIENT_SUPPORT', None))
        state, pt = m.walk([[10, 0], [0, 0], [10, 0]], False, 1, 6, 1, 100)
        self.assertEqual(state, 'DEFINED')
        self.assertEqual(pt, (Decimal(6), Decimal(0)))
    def test_positive_subthreshold_segments_are_measured_but_not_windowed(self):
        arr = {'point_offsets': np.array([0, 3]), 'chain_offsets': np.array([0, 2]),
               'chain_points': np.array([[0, 0], [1e-10, 0], [1, 0]], dtype=np.float64),
               'closed': np.array([False])}
        report, _ = self.run_synth(arr)
        meta = report['npz']
        self.assertEqual(meta['positive_segment_count'], 2)
        self.assertEqual(meta['short_segment_count'], 1)
        self.assertEqual(meta['min_segment_m'], 1e-10)
        self.assertEqual(meta['degenerate_chain_count'], 1)
        pts = [[0, 0], [Decimal('1e-10'), 0], [1, 0]]
        self.assertEqual(m.walk(pts, False, 1, 6, 1, 100), ('DEGENERATE', None))
        self.assertEqual(m._walk_float(pts, False, 1, 6, 1), ('DEGENERATE', None))
    def test_float_partial_support_is_not_hidden(self):
        fx = {'id': 'partial', 'points': [[0, 0], [10, 0]], 'closed': False, 'center_index': 0, 'queries': [{'h': 6, 'state': 'INSUFFICIENT_SUPPORT', 'a_exact': None, 'c_exact': None}]}
        rec = m._oracle_records({'fixtures': [fx]})[0]
        self.assertEqual(rec['state'], 'INSUFFICIENT_SUPPORT')
        self.assertEqual(rec['float_state'], 'INSUFFICIENT_SUPPORT')
        self.assertIsNone(rec['a_walk_float64'])
        self.assertIsNotNone(rec['c_walk_float64'])
        self.assertIsNone(rec['float64_to_walk100_max_abs_diff'])
    def test_mutant_interpolation_shows_discrepancy(self):
        oracle = json.loads(ORACLE_PATH.read_bytes())
        q = [f for f in oracle['fixtures'] if f['id'] == 'right_l'][0]['queries'][0]
        ref_c = m._reference_point(q['c_exact'], 100)
        mutant_c = (Decimal(-3), Decimal(3))
        diff = max(abs(mutant_c[0] - ref_c[0]), abs(mutant_c[1] - ref_c[1]))
        self.assertGreater(diff, Decimal('1'))
        state, walked = m.walk([[-120, 0], [0, 0], [0, 120]], False, 1, 6, 1, 100)
        self.assertEqual(state, 'DEFINED')
        self.assertLess(max(abs(walked[0] - ref_c[0]), abs(walked[1] - ref_c[1])), TOL100)
    def test_cli_exclusive_output(self):
        with tempfile.TemporaryDirectory() as td:
            npz = Path(td) / 's.npz'; write_npz(npz, synth_arrays())
            cpath, csha = make_contract(td, npz)
            out = Path(td) / 'out.json'
            self.assertEqual(m.main(['--contract', str(cpath), '--contract-sha256', csha, '--output', str(out)]), 0)
            self.assertEqual(json.loads(out.read_bytes())['status'], 'NUMERIC_DISCOVERY_ONLY')
            first = out.read_bytes()
            self.assertEqual(m.main(['--contract', str(cpath), '--contract-sha256', csha, '--output', str(out)]), 2)
            self.assertEqual(out.read_bytes(), first)
if __name__ == '__main__':
    unittest.main()
