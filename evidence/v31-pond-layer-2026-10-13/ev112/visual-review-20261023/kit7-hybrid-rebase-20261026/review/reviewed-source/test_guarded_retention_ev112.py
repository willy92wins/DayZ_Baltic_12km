import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'tools/terrain'),
                str(Path(__file__).resolve().parents[1] / 'tools/water')]
import repair_guarded_shapes_ev112 as author


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GuardedRetention(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base, self.discovery = self.root / 'base', self.root / 'discovery'
        self.base.mkdir(); self.discovery.mkdir()
        footprint = self.base / 'bury-work/fp0/footprint.npz'
        footprint.parent.mkdir(parents=True)
        h = np.full((13, 13), 2., np.float32); h[6, 6] = 2.6
        self.heights = h
        self.free = np.zeros(h.shape, bool); self.free[3:-3, 3:-3] = True; self.free[6, 6] = False
        np.savez_compressed(self.base / 'terrain-buried.npz', heights=h,
                            water=np.zeros(h.shape, bool), level=np.zeros_like(h))
        np.save(self.base / 'envelope.npy', np.full((12, 12), np.nan))
        np.savez_compressed(footprint, plane=np.full((12, 12), np.nan), field=np.full((12, 12, 4), .75))
        np.savez_compressed(self.discovery / 'domains.npz', free=self.free,
                            road=np.zeros(h.shape, bool), shore=np.zeros(h.shape, bool))
        (self.discovery / 'report.json').write_text(json.dumps(dict(
            terrain_sha256=sha(self.base / 'terrain-buried.npz'), footprint_sha256=sha(footprint),
            groups=[dict(independently_feasible=True, kind='peak', representative=[6, 6], target_vertices=[[6, 6]])])))

    def run_author(self, output, retained=None, fresh_hybrid=False):
        args = ['repair_guarded_shapes_ev112.py', str(self.base), str(self.discovery), str(output),
                '--expected-terrain-sha256', sha(self.base / 'terrain-buried.npz'),
                '--expected-domains-sha256', sha(self.discovery / 'domains.npz')]
        if retained:
            args += ['--retain-candidate', str(retained), '--expected-retained-sha256', sha(retained / 'terrain.npz'),
                     '--expected-retained-domains-sha256', sha(retained / 'domains.npz'), '--hybrid-witnesses']
        if fresh_hybrid:
            args += ['--hybrid-witnesses']
        # Only the native-grid dimension is scaled for this integration fixture;
        # production author, solver, serializers and independent consumers run.
        with patch.object(sys, 'argv', args), patch.object(author.D, 'N', 13), contextlib.redirect_stdout(io.StringIO()):
            try:
                author.main()
            except SystemExit as result:
                self.assertEqual(result.code, 0)
        return json.loads((output / 'report.json').read_text())

    def test_fresh_hybrid_candidate_uses_all_existing_guards(self):
        result=self.run_author(self.root/'fresh-hybrid',fresh_hybrid=True)
        self.assertEqual(result['witness_mode'],'hybrid')
        self.assertIsNone(result['retained_candidate'])
        self.assertEqual(result['groups_applied'],1)
        self.assertTrue(all(result['checks'].values()))

    def test_retains_previous_actual_solution_exactly(self):
        first, second = self.root / 'first', self.root / 'second'
        result = self.run_author(first)
        self.assertEqual(result['groups_applied'], 1)
        self.assertGreater(result['changed_vertices'], 0)
        replay = self.run_author(second, first)
        self.assertTrue(replay['checks']['retained_changes_exact'])
        with np.load(first / 'terrain.npz') as a, np.load(second / 'terrain.npz') as b:
            np.testing.assert_array_equal(a['heights'], b['heights'])
            np.testing.assert_array_equal(b['heights'][~self.free], self.heights[~self.free])
        with np.load(first / 'domains.npz') as a, np.load(second / 'domains.npz') as b:
            np.testing.assert_array_equal(a['accepted'], b['accepted'])

    def test_rejects_incoherent_retained_masks_even_with_matching_file_hash(self):
        first = self.root / 'first'; self.run_author(first)
        mask_path = first / 'domains.npz'
        with np.load(mask_path) as data:
            original = {key: data[key] for key in data.files}
        for kind in ('changed', 'accepted', 'free'):
            with self.subTest(kind=kind):
                altered = {key: value.copy() for key, value in original.items()}
                altered[kind][0, 0] = ~altered[kind][0, 0]
                np.savez_compressed(mask_path, **altered)
                with self.assertRaisesRegex(ValueError, 'mismatch|outside target'):
                    self.run_author(self.root / ('bad-' + kind), first)


if __name__ == '__main__':
    unittest.main()
