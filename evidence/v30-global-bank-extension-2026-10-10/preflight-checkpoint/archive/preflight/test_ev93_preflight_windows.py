import importlib.util
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name('ev93_preflight_windows.py')
spec = importlib.util.spec_from_file_location('ev93_preflight_windows_tested', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class EV93PreflightFixtures(unittest.TestCase):
    def test_frozen_and_index_adapter_fixtures(self):
        result = module.run_fixtures()
        self.assertEqual(set(result.values()), {'PASS'})
        self.assertEqual(len(result), 11)

if __name__ == '__main__':
    unittest.main(verbosity=2)
