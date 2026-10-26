import copy
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/terrain'))
import native_height_probe_ev112 as probe


class NativeHeightProbe(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        r, c = np.mgrid[:9, :11]
        self.before = 14 + 2.0 * c + 3.0 * r
        self.after = self.before.copy()
        self.after[4, 5] += .6
        self.points = probe.points_for_changes(self.before, self.after)
        self.survey = str(uuid.uuid4())

    def log(self, points=None):
        points = points or self.points
        lines = ['BALTIC_FOREST_BOUNDARY_V1;BalticTrial', 'SURVEY;' + self.survey, 'BEGIN;' + str(len(points))]
        for p in points:
            # Analytic plane + barycentric weight of the perturbed vertex.
            c, r = p['x'] / 6, 8 - p['z'] / 6
            value = 14 + 2 * c + 3 * r
            if p['kind'] == 'changed_vertex':
                value += .6
            elif (p['row'], p['col'], p['triangle']) in {(3, 4, 0), (3, 4, 1), (3, 5, 1), (4, 4, 0), (4, 5, 0), (4, 5, 1)}:
                value += .2
            lines.append(f"P;{p['id']};{value};false;false;{100+p['id']}")
        return '\n'.join(lines + ['END;' + str(len(points))]) + '\n'

    def document(self):
        mission = self.root / 'mission';mission.mkdir()
        (mission / 'init.c').write_text('fixture')
        (mission / 'points.csv').write_text(probe.csv_text(self.points), encoding='ascii')
        (mission / 'identity.txt').write_text(self.survey + '\n')
        a, b = self.root / 'before.npz', self.root / 'after.npz'
        np.savez(a, heights=self.before);np.savez(b, heights=self.after)
        producer = self.root / 'source-init.c';producer.write_text('fixture')
        packages = {}
        for name in ('narva_trial.pbo', 'baltic_water_v30.pbo', 'baltic_stream_pilot.pbo'):
            p = self.root / name;p.write_bytes(name.encode());packages[str(p)] = probe.sha(p)
        return dict(schema='ev112-native-height-v1', survey_id=self.survey, points=self.points,
                    terrain_before=str(a), terrain_after=str(b), producer=str(producer),
                    inputs={str(a):probe.sha(a), str(b):probe.sha(b), str(producer):probe.sha(producer)}, packages=packages,
                    mission=str(mission), mission_hashes={str(p):probe.sha(p) for p in mission.iterdir()},
                    counts=probe.verify_coverage(self.before, self.after, self.points))

    def test_analytic_positive_has_vertex_and_all_eight_triangles(self):
        self.assertEqual(len(self.points), 9)
        self.assertEqual(probe.verify_coverage(self.before, self.after, self.points)['incident_cells'], 4)
        result = probe.judge(self.points, probe.parse(self.log(), 9, self.survey))
        self.assertEqual(result['status'], 'NATIVE_HEIGHT_SAMPLE_PASS')
        probe.verify_binding(self.document())

    def test_wrong_native_height_fails_consumer(self):
        rows = probe.parse(self.log(), 9, self.survey);rows[3]['ground'] += .02
        self.assertEqual(probe.judge(self.points, rows)['failure_count'], 1)

    def test_log_omission_duplicate_and_stale_uuid_rejected(self):
        log = self.log()
        for bad in [log.replace('END;9', 'END;8'), log.replace('P;1;', 'P;0;'), log.replace(self.survey, str(uuid.uuid4()))]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):probe.parse(bad, 9, self.survey)

    def test_nonfinite_height_with_valid_six_field_schema_rejected(self):
        lines = self.log().splitlines();fields = lines[4].split(';')
        self.assertEqual(len(fields), 6);fields[2] = 'nan';lines[4] = ';'.join(fields)
        with self.assertRaisesRegex(ValueError, 'height'):probe.parse('\n'.join(lines), 9, self.survey)

    def test_changed_mission_producer_even_with_updated_hash_rejected(self):
        doc = self.document();path = Path(doc['mission']) / 'init.c';path.write_text('changed')
        doc['mission_hashes'][str(path)] = probe.sha(path)
        with self.assertRaisesRegex(ValueError, 'producer'):probe.verify_binding(doc)

    def test_empty_terrain_or_point_set_rejected(self):
        with self.assertRaises(ValueError):probe.points_for_changes(self.before, self.before)
        with self.assertRaises(ValueError):probe.judge([], {})

    def test_missing_triangle_even_with_sequential_ids_rejected(self):
        points = copy.deepcopy(self.points[:-1])
        with self.assertRaisesRegex(ValueError, 'missing'):probe.verify_coverage(self.before, self.after, points)

    def test_coordinates_and_expectation_checked_against_native_grid(self):
        for key in ('x', 'ground'):
            points = copy.deepcopy(self.points);points[1][key] += .1
            with self.subTest(key=key), self.assertRaises(ValueError):probe.verify_coverage(self.before, self.after, points)

    def test_csv_or_package_drift_is_rejected(self):
        doc = self.document();path = Path(doc['mission']) / 'points.csv';path.write_text('0;1 0 1\n')
        doc['mission_hashes'][str(path)] = probe.sha(path)
        with self.assertRaisesRegex(ValueError, 'CSV'):probe.verify_binding(doc)
        path.write_text(probe.csv_text(self.points), encoding='ascii');doc['mission_hashes'][str(path)] = probe.sha(path)
        Path(next(iter(doc['packages']))).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'changed input'):probe.verify_binding(doc)

    def test_source_drift_or_unbound_source_rejected(self):
        doc = self.document();unbound = copy.deepcopy(doc);unbound['inputs'].pop(unbound['terrain_before'])
        with self.assertRaisesRegex(ValueError, 'unbound terrain'):probe.verify_binding(unbound)
        Path(doc['terrain_after']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'changed input'):probe.verify_binding(doc)

    def test_edge_vertex_has_only_in_map_incident_triangles(self):
        after = self.before.copy();after[0, 0] += 1
        points = probe.points_for_changes(self.before, after)
        self.assertEqual(len(points), 3)
        self.assertEqual(probe.verify_coverage(self.before, after, points)['incident_cells'], 1)


if __name__ == '__main__':unittest.main()
