"""Verifier sensitivity only. Fabricated records do not count as engine evidence."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('load_sites', ROOT/'tools/navigation/verify_foundation_load_sites.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SiteChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref = json.loads((ROOT/'evidence/overnight-2026-10-01/performance-v10-sites.json').read_text())
        records = []
        for index, ((x, z), y) in enumerate(zip(cls.ref['points'], cls.ref['heights'])):
            position = f'<{x:.6f}, {y+0.05:.6f}, {z:.6f}>'
            nav = f'<{x:.6f}, {y:.6f}, {z:.6f}>'
            records.append(f'S;{index};{position};{y:.8f};true;{nav};true;2' if index < 100
                           else f'G;{position};{y:.8f};true;{nav}')
        cls.lines = ['BALTIC_FOUNDATION_LOAD_SITES_V1', records[-1], *records[:-1], 'END;true']

    def result(self, lines):
        try:
            return module.verify('\n'.join(lines), self.ref)['status'].startswith('PASS_')
        except (ValueError, IndexError, KeyError):
            return False

    def test_controls(self):
        self.assertTrue(self.result(self.lines))
        controls = {}
        controls['missing_site'] = self.lines[:5]+self.lines[6:]
        controls['duplicate_site'] = self.lines[:3]+[self.lines[2]]+self.lines[4:]
        controls['no_terminal'] = self.lines[:-1]
        controls['failed_terminal'] = self.lines[:-1]+['END;false']
        for name, old, new in [('wrong_position','2050.000000','2055.000000'),
                               ('failed_sample',';true;',';false;'),
                               ('failed_path',';true;2',';false;2'),
                               ('empty_path',';true;2',';true;0'),
                               ('nonfinite_ground',f";{self.ref['heights'][0]:.8f};",';nan;')]:
            changed = self.lines.copy()
            changed[2] = changed[2].replace(old,new,1)
            self.assertNotEqual(changed, self.lines)
            controls[name] = changed
        for name, changed in controls.items():
            with self.subTest(name=name):
                self.assertFalse(self.result(changed))


if __name__ == '__main__':
    unittest.main()
