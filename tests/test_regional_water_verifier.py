"""Reject incomplete/false-green regional evidence; fixtures are frozen runtime data."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('regional_verify', ROOT/'tools/playtest/verify_regional_water.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RegionalWaterEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads((ROOT/'evidence/regional-water/reference-v1.json').read_text())
        cls.log = (ROOT/'evidence/regional-water/baseline-engine-v1.log').read_text()

    def test_actual_flooding_fails(self):
        result = module.assess(self.reference, self.log)
        self.assertEqual(result['status'], 'FAIL_DRY_LAND_FLOODING')
        self.assertEqual(result['flooded_dry_count'], 20)

    def test_missing_final_marker(self):
        with self.assertRaises(ValueError):
            module.assess(self.reference, self.log.rsplit('END_', 1)[0])

    def test_missing_point(self):
        lines = self.log.splitlines()
        lines.remove(next(line for line in lines if line.startswith('G;')))
        with self.assertRaises(ValueError):
            module.assess(self.reference, '\n'.join(lines))

    def test_wrong_native_registration(self):
        ref = copy.deepcopy(self.reference)
        ref['samples'][0]['native_height'] += .02
        with self.assertRaises(ValueError):
            module.assess(ref, self.log)

    def test_changed_sea_range_rejected(self):
        with self.assertRaises(ValueError):
            module.assess(self.reference, self.log.replace('sea_max=1', 'sea_max=0.1'))

    def test_positive_control_clear_dry_interior(self):
        # Isolated synthetic consumer fixture: dry ground above tide and no water flags.
        ref = {'samples': [dict(x=60, z=60, native_height=2.0, dry_interior=True, region='fixture')]}
        log = 'BALTIC_REGIONAL_WATER_V1\nsea_min=0.5\nsea_max=1\nsea_now=0.8\nG;60;60;2;false;false;0;0\nEND_BALTIC_REGIONAL_WATER_V1\n'
        self.assertEqual(module.assess(ref, log)['status'], 'PASS_SAMPLED_DRY_INTERIOR')
        low_ref = copy.deepcopy(ref)
        low_ref['samples'][0]['native_height'] = .9
        self.assertEqual(module.assess(low_ref, log.replace(';2;', ';0.9;'))['status'], 'FAIL_DRY_LAND_CLEARANCE')


if __name__ == '__main__':
    unittest.main()
