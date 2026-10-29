import copy
import hashlib
import json
import math
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest import mock
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'quality'))
import closed_perimeter_ev112 as producer
import verify_closed_perimeter_ev112 as consumer


def make_data(specs, extra=None):
    po = [0]
    co = [0]
    points = []
    closed = []
    for pts, flag in specs:
        points.extend(pts)
        po.append(len(points))
        co.append(co[-1] + len(pts) - 1)
        closed.append(flag)
    data = {'point_offsets': np.array(po, dtype=np.int64), 'chain_points': np.array(points, dtype=np.float64).reshape(-1, 2), 'closed': np.array(closed, dtype=bool), 'chain_offsets': np.array(co, dtype=np.int64)}
    if extra:
        data.update(extra)
    return data


def one(points, closed):
    return producer.analyze_arrays(make_data([(points, closed)]))['chains'][0]


SQUARE = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
# Asymmetric closed polygon defined locally in the test (not via any
# producer transform): absolute turns are all distinct and include
# 45 deg, 90 deg and other angles, so permuting angles or XY is visible.
ASYMM = [(0.0, 0.0), (10.0, 0.0), (12.0, 2.0), (6.0, 12.0), (0.0, 8.0), (0.0, 0.0)]


def xy_angle_map(chain):
    return {tuple(xy): (s, a) for xy, s, a in zip(chain['vertex_xy'], chain['signed_turns_deg'], chain['absolute_turns_deg'])}


def rounded_rectangle():
    pts = [(0.0, 0.0), (6.0, 0.0)]
    for deg in (-75, -60, -45, -30, -15, 0):
        r = math.radians(deg)
        pts.append((6.0 + 2.0 * math.cos(r), 2.0 + 2.0 * math.sin(r)))
    pts.append((8.0, 8.0))
    for deg in (15, 30, 45, 60, 75, 90):
        r = math.radians(deg)
        pts.append((6.0 + 2.0 * math.cos(r), 8.0 + 2.0 * math.sin(r)))
    pts.append((2.0, 10.0))
    for deg in (105, 120, 135, 150, 165, 180):
        r = math.radians(deg)
        pts.append((2.0 + 2.0 * math.cos(r), 8.0 + 2.0 * math.sin(r)))
    pts.append((0.0, 0.0))
    return pts


class TestProducer(unittest.TestCase):
    def test_01_closed_square(self):
        chain = one(SQUARE, True)
        self.assertEqual(chain['status'], 'DIAGNOSTIC_FINDINGS')
        self.assertEqual(chain['absolute_turns_deg'], [90.0, 90.0, 90.0, 90.0])
        self.assertEqual(chain['perimeter'], 40.0)
        self.assertEqual([w['vertex_index'] for w in chain['witnesses']], [0, 1, 2, 3])
        self.assertTrue(chain['closure_turn']['is_witness'])
        self.assertEqual(chain['evaluated_vertices'], 4)
        self.assertEqual(chain['evaluated_edges'], 4)

    def test_02_closed_triangle_120(self):
        pts = [(0.0, 0.0), (10.0, 0.0), (5.0, 8.660254037840387), (0.0, 0.0)]
        chain = one(pts, True)
        self.assertEqual(len(chain['absolute_turns_deg']), 3)
        for angle in chain['absolute_turns_deg']:
            self.assertAlmostEqual(angle, 120.0, places=9)
        self.assertAlmostEqual(chain['perimeter'], 30.0, places=9)

    def test_03_open_l(self):
        chain = one([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)], False)
        self.assertEqual(chain['absolute_turns_deg'], [90.0])
        self.assertEqual(chain['vertex_indices'], [1])
        self.assertEqual(chain['perimeter'], 20.0)
        self.assertIsNone(chain['closure_turn'])

    def test_04_fine_polygon_no_witness(self):
        pts = [(10.0 * math.cos(2.0 * math.pi * i / 36.0), 10.0 * math.sin(2.0 * math.pi * i / 36.0)) for i in range(36)]
        pts.append(pts[0])
        chain = one(pts, True)
        self.assertEqual(chain['witnesses'], [])
        self.assertEqual(chain['status'], 'NO_RAW_TURN_FINDING_NOT_ACCEPTANCE')
        self.assertTrue(all(a < 45.0 for a in chain['absolute_turns_deg']))

    def test_05_open_straight_no_finding(self):
        report = producer.analyze_arrays(make_data([([(0.0, 0.0), (5.0, 0.0), (10.0, 0.0)], False)]))
        self.assertEqual(report['status'], 'DIAGNOSTIC_ONLY')
        self.assertEqual(report['chains'][0]['status'], 'NO_RAW_TURN_FINDING_NOT_ACCEPTANCE')
        self.assertNotIn('pass', json.dumps(report).lower().replace('NO_RAW_TURN_FINDING_NOT_ACCEPTANCE', ''))
        self.assertEqual(report['threshold_deg'], 45)

    def test_06_closure_is_only_witness(self):
        chain = one(rounded_rectangle(), True)
        self.assertEqual([w['vertex_index'] for w in chain['witnesses']], [0])
        self.assertAlmostEqual(chain['absolute_turns_deg'][0], 90.0, places=9)
        self.assertTrue(chain['closure_turn']['is_witness'])

    def test_07_closure_mismatch_degenerate_consumer_ok(self):
        data = make_data([(SQUARE[:-1], True)])
        report = producer.analyze_arrays(data)
        chain = report['chains'][0]
        self.assertEqual(chain['status'], 'DEGENERATE')
        self.assertEqual(chain['degenerate_reason'], 'closure_mismatch')
        self.assertEqual(chain['evaluated_vertices'], 0)
        self.assertTrue(consumer.verify_arrays(data, report))

    def test_08_short_segment_closed(self):
        pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
        chain = one(pts, True)
        self.assertEqual(chain['status'], 'DEGENERATE')
        self.assertEqual(chain['degenerate_reason'], 'short_segment')

    def test_09_short_segment_open(self):
        chain = one([(0.0, 0.0), (10.0, 0.0), (10.0, 0.0)], False)
        self.assertEqual(chain['degenerate_reason'], 'short_segment')
        self.assertEqual(chain['status'], 'DEGENERATE')

    def test_10_distinct_lt3_closed(self):
        chain = one([(0.0, 0.0), (10.0, 0.0), (0.0, 0.0)], True)
        self.assertEqual(chain['status'], 'DEGENERATE')
        self.assertEqual(chain['degenerate_reason'], 'distinct_vertices_lt3')

    def test_11_no_evaluable_vertex_open(self):
        for pts in ([(1.0, 1.0)], [(0.0, 0.0), (10.0, 0.0)]):
            chain = one(pts, False)
            self.assertEqual(chain['status'], 'NO_EVALUABLE_VERTEX')
            self.assertEqual(chain['degenerate_reason'], 'no_evaluable_vertex')
            self.assertNotEqual(chain['status'], 'DEGENERATE')
            self.assertNotEqual(chain['status'], 'NO_RAW_TURN_FINDING_NOT_ACCEPTANCE')
            self.assertEqual(chain['evaluated_vertices'], 0)

    def test_11b_no_evaluable_summary_totals_separate(self):
        data = make_data([([(0.0, 0.0), (10.0, 0.0)], False), ([(0.0, 0.0), (10.0, 0.0), (0.0, 0.0)], True), (SQUARE, True)])
        report = producer.analyze_arrays(data)
        self.assertEqual(report['summary']['no_evaluable_chain_count'], 1)
        self.assertEqual(report['summary']['degenerate_chain_count'], 1)
        self.assertEqual(report['summary']['finding_chain_count'], 1)
        self.assertEqual(report['summary']['chain_count'], 3)
        self.assertTrue(consumer.verify_arrays(data, report))
        mutant = copy.deepcopy(report)
        mutant['chains'][0]['status'] = 'DEGENERATE'
        with self.assertRaises(ValueError):
            consumer.verify_arrays(data, mutant)
        mutant2 = copy.deepcopy(report)
        mutant2['summary']['no_evaluable_chain_count'] = 0
        mutant2['summary']['degenerate_chain_count'] = 2
        with self.assertRaises(ValueError):
            consumer.verify_arrays(data, mutant2)

    def test_11c_empty_chain_is_schema_invalid(self):
        data = {'point_offsets': np.array([0, 0], dtype=np.int64), 'chain_points': np.empty((0, 2), dtype=np.float64), 'closed': np.array([True], dtype=bool), 'chain_offsets': np.array([0, 0], dtype=np.int64)}
        with self.assertRaises(ValueError):
            producer.analyze_arrays(data)
        report = producer.analyze_arrays(make_data([(SQUARE, True)]))
        with self.assertRaises(ValueError):
            consumer.verify_arrays(data, report)

    def test_12_nan_rejected(self):
        data = make_data([(SQUARE, True)])
        data['chain_points'] = data['chain_points'].copy()
        data['chain_points'][0, 0] = np.nan
        with self.assertRaises(ValueError):
            producer.analyze_arrays(data)

    def test_13_noninteger_offsets_rejected(self):
        for dtype in (np.float64, bool):
            data = make_data([(SQUARE, True)])
            data['point_offsets'] = data['point_offsets'].astype(dtype)
            with self.assertRaises(ValueError):
                producer.analyze_arrays(data)

    def test_14_malformed_offsets_rejected(self):
        data = make_data([(SQUARE, True)])
        bad = dict(data)
        bad['point_offsets'] = np.array([0, 3, 5], dtype=np.int64)
        bad['closed'] = np.array([True], dtype=bool)
        with self.assertRaises(ValueError):
            producer.analyze_arrays(bad)
        data2 = make_data([(SQUARE, True)])
        data2['chain_offsets'] = np.array([0, 99], dtype=np.int64)
        with self.assertRaises(ValueError):
            producer.analyze_arrays(data2)
        data3 = make_data([(SQUARE, True)])
        data3['point_offsets'] = np.array([0, 4], dtype=np.int64)
        with self.assertRaises(ValueError):
            producer.analyze_arrays(data3)

    def test_15_wrong_dtypes_or_missing_key(self):
        data = make_data([(SQUARE, True)])
        bad = dict(data)
        bad['chain_points'] = data['chain_points'].astype(np.float32)
        with self.assertRaises(ValueError):
            producer.analyze_arrays(bad)
        bad2 = dict(data)
        bad2['closed'] = np.array([1], dtype=np.int64)
        with self.assertRaises(ValueError):
            producer.analyze_arrays(bad2)
        bad3 = dict(data)
        del bad3['chain_offsets']
        with self.assertRaises(ValueError):
            producer.analyze_arrays(bad3)

    def test_16_extra_npz_key_enumerated(self):
        data = make_data([(SQUARE, True)], extra={'segment_extra': np.array([1, 2, 3], dtype=np.int64)})
        report = producer.analyze_arrays(data)
        self.assertIn('segment_extra', report['source_npz_keys'])
        self.assertTrue(consumer.verify_arrays(data, report))

    def test_17_open_coincident_endpoints_not_closed(self):
        chain = one([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 0.0)], False)
        self.assertFalse(chain['closed'])
        self.assertTrue(chain['coincident_endpoints'])
        self.assertIsNone(chain['closure_turn'])
        self.assertEqual(chain['vertex_indices'], [1, 2])

    def test_18_spike_canonical_180(self):
        chain = one([(0.0, 0.0), (10.0, 0.0), (0.0, 0.0)], False)
        self.assertEqual(chain['signed_turns_deg'], [180.0])
        self.assertEqual(chain['absolute_turns_deg'], [180.0])
        self.assertEqual(len(chain['witnesses']), 1)

    def test_18b_almost_minus_180_rounds_to_canonical_plus_180(self):
        data = make_data([([(0.0, 0.0), (10.0, 0.0), (0.0, -1e-16)], False)])
        report = producer.analyze_arrays(data)
        chain = report['chains'][0]
        self.assertEqual(chain['signed_turns_deg'], [180.0])
        self.assertEqual(chain['absolute_turns_deg'], [180.0])
        self.assertTrue(consumer.verify_arrays(data, report))

    def test_18c_nonfinite_calculation_rejected(self):
        with self.assertRaises(ValueError):
            one([(-1e308, 0.0), (1e308, 0.0), (0.0, 0.0)], False)

    def test_19_exact_45_and_nextafter(self):
        cases = [(math.nextafter(1.0, 0.0), False), (1.0, True), (math.nextafter(1.0, 2.0), True)]
        for y, is_witness in cases:
            data = make_data([([(0.0, 0.0), (1.0, 0.0), (2.0, y)], False)])
            report = producer.analyze_arrays(data)
            chain = report['chains'][0]
            self.assertEqual(bool(chain['witnesses']), is_witness)
            self.assertTrue(consumer.verify_arrays(data, report))

    def test_19b_closed_closure_boundary_nextafter_analytic(self):
        # Vertex 0 is (1,0): incoming (1,0), outgoing (1,y), so the
        # analytic test-local reference is simply Fraction(y) >= 1.
        # This formula is neither the producer nor the verifier formula.
        cases = [(math.nextafter(1.0, 0.0), False), (1.0, True), (math.nextafter(1.0, 2.0), True)]
        for y, expected in cases:
            pts = [(1.0, 0.0), (2.0, y), (3.0, 4.0), (0.0, 4.0), (0.0, 0.0), (1.0, 0.0)]
            data = make_data([(pts, True)])
            report = producer.analyze_arrays(data)
            chain = report['chains'][0]
            analytic = Fraction(y) >= 1
            self.assertEqual(analytic, expected)
            self.assertEqual(chain['closure_turn']['is_witness'], analytic)
            self.assertEqual(0 in [w['vertex_index'] for w in chain['witnesses']], analytic)
            self.assertTrue(consumer.verify_arrays(data, report))

    def test_20_rotate_origin_closed_asymmetric(self):
        core = ASYMM[:-1]
        rotated = core[1:] + core[:1]
        rotated.append(rotated[0])
        base = one(ASYMM, True)
        moved = one(rotated, True)
        angles = base['absolute_turns_deg']
        self.assertEqual(len(set(angles)), 5)
        self.assertTrue(any(abs(a - 45.0) < 1e-9 for a in angles))
        self.assertTrue(any(abs(a - 90.0) < 1e-9 for a in angles))
        self.assertTrue(any(abs(a - 45.0) > 1e-9 and abs(a - 90.0) > 1e-9 for a in angles))
        self.assertEqual(moved['perimeter'], base['perimeter'])
        self.assertEqual(xy_angle_map(moved), xy_angle_map(base))

    def test_21_reverse_order_closed_asymmetric(self):
        core = ASYMM[:-1]
        rev = [core[0], core[4], core[3], core[2], core[1], core[0]]
        base = one(ASYMM, True)
        moved = one(rev, True)
        self.assertEqual(moved['perimeter'], base['perimeter'])
        base_map = xy_angle_map(base)
        moved_map = xy_angle_map(moved)
        self.assertEqual(set(moved_map), set(base_map))
        for xy, (sig, ab) in base_map.items():
            self.assertAlmostEqual(moved_map[xy][1], ab, places=9)
            self.assertAlmostEqual(moved_map[xy][0], -sig, places=9)

    def test_22_rigid_90_translation_asymmetric(self):
        moved_pts = [(-y + 10.0, x + 3.0) for x, y in ASYMM]
        base = one(ASYMM, True)
        moved = one(moved_pts, True)
        self.assertEqual(moved['perimeter'], base['perimeter'])
        expected = {(-xy[1] + 10.0, xy[0] + 3.0): val for xy, val in xy_angle_map(base).items()}
        moved_map = xy_angle_map(moved)
        self.assertEqual(set(moved_map), set(expected))
        for xy, (sig, ab) in expected.items():
            self.assertAlmostEqual(moved_map[xy][0], sig, places=9)
            self.assertAlmostEqual(moved_map[xy][1], ab, places=9)

    def test_23_collinear_subdivision_open(self):
        chain = one([(0.0, 0.0), (5.0, 0.0), (10.0, 0.0), (10.0, 5.0), (10.0, 10.0)], False)
        self.assertEqual(chain['perimeter'], 20.0)
        self.assertEqual([a for a in chain['absolute_turns_deg'] if a != 0.0], [90.0])
        self.assertEqual(chain['absolute_turns_deg'][0], 0.0)

    def test_23b_collinear_subdivision_both_closure_edges(self):
        closing = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 5.0), (0.0, 0.0)]
        data = make_data([(closing, True)])
        report = producer.analyze_arrays(data)
        chain = report['chains'][0]
        self.assertEqual(chain['evaluated_vertices'], 5)
        cmap = xy_angle_map(chain)
        self.assertEqual(cmap[(0.0, 5.0)], (0.0, 0.0))
        self.assertEqual(cmap[(0.0, 0.0)], (90.0, 90.0))
        self.assertTrue(chain['closure_turn']['is_witness'])
        self.assertTrue(consumer.verify_arrays(data, report))
        first = [(0.0, 0.0), (5.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
        data2 = make_data([(first, True)])
        report2 = producer.analyze_arrays(data2)
        chain2 = report2['chains'][0]
        self.assertEqual(chain2['evaluated_vertices'], 5)
        cmap2 = xy_angle_map(chain2)
        self.assertEqual(cmap2[(5.0, 0.0)], (0.0, 0.0))
        self.assertEqual(cmap2[(0.0, 0.0)], (90.0, 90.0))
        self.assertTrue(chain2['closure_turn']['is_witness'])
        self.assertTrue(consumer.verify_arrays(data2, report2))

    def test_24_reflection_preserves_absolute_asymmetric(self):
        moved_pts = [(-x, y) for x, y in ASYMM]
        base = one(ASYMM, True)
        moved = one(moved_pts, True)
        self.assertEqual(moved['perimeter'], base['perimeter'])
        expected = {(-xy[0], xy[1]): (-val[0], val[1]) for xy, val in xy_angle_map(base).items()}
        moved_map = xy_angle_map(moved)
        self.assertEqual(set(moved_map), set(expected))
        for xy, (sig, ab) in expected.items():
            self.assertAlmostEqual(moved_map[xy][0], sig, places=9)
            self.assertAlmostEqual(moved_map[xy][1], ab, places=9)


class TestConsumer(unittest.TestCase):
    def setUp(self):
        self.data = make_data([(SQUARE, True), ([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)], False)])
        self.report = producer.analyze_arrays(self.data)

    def test_25_consumer_accepts_valid(self):
        self.assertTrue(consumer.verify_arrays(self.data, self.report))

    def test_26_omitted_closure_witness_fails(self):
        data = make_data([(rounded_rectangle(), True)])
        report = producer.analyze_arrays(data)
        mutant = copy.deepcopy(report)
        mutant['chains'][0]['witnesses'] = []
        mutant['chains'][0]['status'] = 'NO_RAW_TURN_FINDING_NOT_ACCEPTANCE'
        mutant['summary']['total_witness_count'] = 0
        with self.assertRaises(ValueError):
            consumer.verify_arrays(data, mutant)
        mutant2 = copy.deepcopy(self.report)
        mutant2['chains'][0]['witnesses'] = [w for w in mutant2['chains'][0]['witnesses'] if w['vertex_index'] != 0]
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant2)

    def test_27_displaced_witness_fails(self):
        mutant = copy.deepcopy(self.report)
        mutant['chains'][0]['witnesses'][0]['vertex_index'] = 1
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant)

    def test_27b_permuted_angles_or_xy_fail(self):
        data = make_data([(ASYMM, True)])
        report = producer.analyze_arrays(data)
        mutant = copy.deepcopy(report)
        mutant['chains'][0]['absolute_turns_deg'][0], mutant['chains'][0]['absolute_turns_deg'][1] = mutant['chains'][0]['absolute_turns_deg'][1], mutant['chains'][0]['absolute_turns_deg'][0]
        mutant['chains'][0]['angles_deg'] = list(mutant['chains'][0]['absolute_turns_deg'])
        with self.assertRaises(ValueError):
            consumer.verify_arrays(data, mutant)
        mutant2 = copy.deepcopy(report)
        mutant2['chains'][0]['vertex_xy'][0], mutant2['chains'][0]['vertex_xy'][1] = mutant2['chains'][0]['vertex_xy'][1], mutant2['chains'][0]['vertex_xy'][0]
        with self.assertRaises(ValueError):
            consumer.verify_arrays(data, mutant2)

    def test_28_altered_length_or_angle_fails(self):
        mutant = copy.deepcopy(self.report)
        mutant['chains'][0]['edge_lengths'][0] += 1.0
        mutant['chains'][0]['perimeter'] += 1.0
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant)
        mutant2 = copy.deepcopy(self.report)
        for field in ('absolute_turns_deg', 'angles_deg'):
            mutant2['chains'][0][field][0] = 80.0
        mutant2['chains'][0]['signed_turns_deg'][0] = 80.0
        mutant2['chains'][0]['witnesses'][0]['absolute_turn_deg'] = 80.0
        mutant2['chains'][0]['witnesses'][0]['signed_turn_deg'] = 80.0
        mutant2['chains'][0]['closure_turn']['absolute_turn_deg'] = 80.0
        mutant2['chains'][0]['closure_turn']['signed_turn_deg'] = 80.0
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant2)

    def test_28b_alias_and_signed_absolute_exact(self):
        mutant = copy.deepcopy(self.report)
        mutant['chains'][0]['angles_deg'][0] = math.nextafter(90.0, 91.0)
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant)
        mutant2 = copy.deepcopy(self.report)
        mutant2['chains'][0]['absolute_turns_deg'][0] = math.nextafter(90.0, 91.0)
        mutant2['chains'][0]['angles_deg'][0] = math.nextafter(90.0, 91.0)
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant2)

    def test_28c_reason_list_raises_valueerror(self):
        mutant = copy.deepcopy(self.report)
        mutant['chains'][0]['degenerate_reason'] = ['short_segment']
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant)

    def test_29_false_pass_or_unknown_fields_fail(self):
        mutant = copy.deepcopy(self.report)
        mutant['pass'] = True
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant)
        mutant2 = copy.deepcopy(self.report)
        mutant2['status'] = 'PASS'
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant2)
        mutant3 = copy.deepcopy(self.report)
        mutant3['chains'][0]['extra'] = 1
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant3)
        mutant4 = copy.deepcopy(self.report)
        mutant4['chains'][0]['witnesses'][0]['extra'] = 1
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant4)

    def test_30_missing_or_duplicate_chain_fails(self):
        mutant = copy.deepcopy(self.report)
        mutant['chains'] = mutant['chains'][:1]
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant)
        mutant2 = copy.deepcopy(self.report)
        mutant2['chains'].append(copy.deepcopy(mutant2['chains'][0]))
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant2)

    def test_31_extra_witness_fails(self):
        mutant = copy.deepcopy(self.report)
        mutant['chains'][1]['witnesses'].append({'vertex_index': 1, 'vertex_xy': [10.0, 0.0], 'signed_turn_deg': 90.0, 'absolute_turn_deg': 90.0})
        with self.assertRaises(ValueError):
            consumer.verify_arrays(self.data, mutant)

    def test_32_degenerate_status_mutant_fails(self):
        data = make_data([(SQUARE[:-1], True)])
        report = producer.analyze_arrays(data)
        mutant = copy.deepcopy(report)
        mutant['chains'][0]['status'] = 'NO_RAW_TURN_FINDING_NOT_ACCEPTANCE'
        mutant['chains'][0]['degenerate_reason'] = None
        with self.assertRaises(ValueError):
            consumer.verify_arrays(data, mutant)


class TestCli(unittest.TestCase):
    def _write_npz(self, directory):
        data = make_data([(SQUARE, True)])
        path = Path(directory) / 'census.npz'
        np.savez(path, **data)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return path, digest

    def test_33_producer_wrong_sha_no_output_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, digest = self._write_npz(tmp)
            out = Path(tmp) / 'report.json'
            self.assertNotEqual(producer.main(['--input', str(path), '--expected-sha256', '0' * 64, '--output', str(out)]), 0)
            self.assertFalse(out.exists())
            self.assertEqual(producer.main(['--input', str(path), '--expected-sha256', digest, '--output', str(out)]), 0)
            before = out.read_bytes()
            self.assertNotEqual(producer.main(['--input', str(path), '--expected-sha256', digest, '--output', str(out)]), 0)
            self.assertEqual(out.read_bytes(), before)

    def test_34_cli_roundtrip_summary_and_finite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, digest = self._write_npz(tmp)
            out = Path(tmp) / 'report.json'
            self.assertEqual(producer.main(['--input', str(path), '--expected-sha256', digest, '--output', str(out)]), 0)
            text = out.read_text(encoding='utf-8')
            self.assertNotIn('NaN', text)
            self.assertNotIn('Infinity', text)
            report = json.loads(text)
            self.assertEqual(report['input_sha256'], digest)
            self.assertEqual(report['summary']['closed_chain_count'], 1)
            self.assertEqual(report['summary']['closed_chains_with_closure_witness'], 1)
            self.assertEqual(report['summary']['closed_chains_where_closure_is_only_witness'], 0)
            self.assertEqual(consumer.main(['--input', str(path), '--expected-sha256', digest, '--report', str(out)]), 0)
            self.assertNotEqual(consumer.main(['--input', str(path), '--expected-sha256', '0' * 64, '--report', str(out)]), 0)

    def test_35_snapshot_bytes_after_path_mutation_producer(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, digest = self._write_npz(tmp)
            out = Path(tmp) / 'report.json'
            orig_read = Path.read_bytes
            def read_then_mutate(self_path, *a, **k):
                raw = orig_read(self_path, *a, **k)
                if Path(self_path) == path:
                    np.savez(path, **make_data([([(0.0, 0.0), (20.0, 0.0), (20.0, 20.0)], False)]))
                return raw
            with mock.patch.object(Path, 'read_bytes', read_then_mutate):
                self.assertEqual(producer.main(['--input', str(path), '--expected-sha256', digest, '--output', str(out)]), 0)
            report = json.loads(out.read_text(encoding='utf-8'))
            self.assertEqual(report['chains'][0]['perimeter'], 40.0)
            self.assertNotEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_35b_snapshot_bytes_after_path_mutation_consumer(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, digest = self._write_npz(tmp)
            out = Path(tmp) / 'report.json'
            self.assertEqual(producer.main(['--input', str(path), '--expected-sha256', digest, '--output', str(out)]), 0)
            orig_read = Path.read_bytes
            def read_then_mutate(self_path, *a, **k):
                raw = orig_read(self_path, *a, **k)
                if Path(self_path) == path:
                    np.savez(path, **make_data([([(0.0, 0.0), (20.0, 0.0), (20.0, 20.0)], False)]))
                return raw
            with mock.patch.object(Path, 'read_bytes', read_then_mutate):
                self.assertEqual(consumer.main(['--input', str(path), '--expected-sha256', digest, '--report', str(out)]), 0)
            self.assertNotEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_36_cli_duplicate_known_key_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, digest = self._write_npz(tmp)
            out = Path(tmp) / 'report.json'
            self.assertEqual(producer.main(['--input', str(path), '--expected-sha256', digest, '--output', str(out)]), 0)
            text = out.read_text(encoding='utf-8')
            dup = Path(tmp) / 'dup.json'
            dup.write_text(text.replace('"status": "DIAGNOSTIC_ONLY"', '"status": "DIAGNOSTIC_ONLY", "status": "PASS"', 1), encoding='utf-8')
            self.assertNotEqual(consumer.main(['--input', str(path), '--expected-sha256', digest, '--report', str(dup)]), 0)
            dup2 = Path(tmp) / 'dup2.json'
            dup2.write_text(text.replace('"chain_count": 1', '"chain_count": 1, "chain_count": 99', 1), encoding='utf-8')
            self.assertNotEqual(consumer.main(['--input', str(path), '--expected-sha256', digest, '--report', str(dup2)]), 0)

    def test_37_summary_output_roundtrip_and_mutants(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, digest = self._write_npz(tmp)
            out = Path(tmp) / 'report.json'
            summ = Path(tmp) / 'summary.json'
            self.assertEqual(producer.main(['--input', str(path), '--expected-sha256', digest, '--output', str(out), '--summary-output', str(summ)]), 0)
            report_raw = out.read_bytes()
            report = json.loads(report_raw.decode('utf-8'))
            sobj = json.loads(summ.read_text(encoding='utf-8'))
            self.assertEqual(set(sobj), {'schema_version', 'status', 'threshold_deg', 'input_sha256', 'summary', 'full_report_sha256'})
            self.assertEqual(sobj['full_report_sha256'], hashlib.sha256(report_raw).hexdigest())
            self.assertEqual(sobj['input_sha256'], digest)
            self.assertEqual(sobj['summary'], report['summary'])
            self.assertEqual(sobj['schema_version'], report['schema_version'])
            self.assertEqual(consumer.main(['--input', str(path), '--expected-sha256', digest, '--report', str(out), '--summary', str(summ)]), 0)
            bad = copy.deepcopy(sobj)
            bad['summary']['chain_count'] = 99
            bad_path = Path(tmp) / 'summary_bad.json'
            bad_path.write_text(json.dumps(bad), encoding='utf-8')
            self.assertNotEqual(consumer.main(['--input', str(path), '--expected-sha256', digest, '--report', str(out), '--summary', str(bad_path)]), 0)
            bad2 = copy.deepcopy(sobj)
            bad2['full_report_sha256'] = '0' * 64
            bad2_path = Path(tmp) / 'summary_bad2.json'
            bad2_path.write_text(json.dumps(bad2), encoding='utf-8')
            self.assertNotEqual(consumer.main(['--input', str(path), '--expected-sha256', digest, '--report', str(out), '--summary', str(bad2_path)]), 0)
            bad3 = copy.deepcopy(sobj)
            bad3['extra'] = 1
            bad3_path = Path(tmp) / 'summary_bad3.json'
            bad3_path.write_text(json.dumps(bad3), encoding='utf-8')
            self.assertNotEqual(consumer.main(['--input', str(path), '--expected-sha256', digest, '--report', str(out), '--summary', str(bad3_path)]), 0)
            self.assertEqual(out.read_bytes(), report_raw)

    def test_38_summary_preflight_both_destinations(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, digest = self._write_npz(tmp)
            out = Path(tmp) / 'report.json'
            summ = Path(tmp) / 'summary.json'
            summ.write_text('existing', encoding='utf-8')
            self.assertNotEqual(producer.main(['--input', str(path), '--expected-sha256', digest, '--output', str(out), '--summary-output', str(summ)]), 0)
            self.assertFalse(out.exists())
            self.assertEqual(summ.read_text(encoding='utf-8'), 'existing')
            same = Path(tmp) / 'same.json'
            self.assertNotEqual(producer.main(['--input', str(path), '--expected-sha256', digest, '--output', str(same), '--summary-output', str(same)]), 0)
            self.assertFalse(same.exists())
            out2 = Path(tmp) / 'report2.json'
            summ2 = Path(tmp) / 'summary2.json'
            self.assertEqual(producer.main(['--input', str(path), '--expected-sha256', digest, '--output', str(out2), '--summary-output', str(summ2)]), 0)
            out3 = Path(tmp) / 'report3.json'
            self.assertNotEqual(producer.main(['--input', str(path), '--expected-sha256', digest, '--output', str(out3), '--summary-output', str(summ2)]), 0)
            self.assertFalse(out3.exists())


if __name__ == '__main__':
    unittest.main()
