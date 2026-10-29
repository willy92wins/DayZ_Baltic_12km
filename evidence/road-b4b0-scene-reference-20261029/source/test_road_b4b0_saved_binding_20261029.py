import copy, importlib.util, unittest
from pathlib import Path

MODULE = Path(__file__).with_name('consume_road_b4b0_saved_20261029.py')
sp = importlib.util.spec_from_file_location('saved_binding', MODULE)
m = importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)

class BindingTests(unittest.TestCase):
    def setUp(self):
        self.path = Path('X:/fixture/script.py')
        self.report = {'tool': {'pid': 22, 'path': str(self.path), 'sha256': 'a'*64}}
        self.running = {'pid': 11, 'birth': 100.2, 'started': 100.0}
        self.completion = {'identities': {'11': 100.2, '22': 100.5}, 'started': 100.0, 'finished': 101.0, 'reason': None}
    def check(self):
        return m.process_binding(self.report, self.running, self.completion, self.path, 'a'*64)
    def test_observed_descendant(self):
        self.assertEqual(self.check()['pid'], 22)
        self.assertFalse(self.check()['child_executable_independently_recorded'])
    def test_foreign_pid(self):
        self.report['tool']['pid'] = 23
        with self.assertRaisesRegex(ValueError, 'not observed'): self.check()
    def test_birth_outside(self):
        self.completion['identities']['22'] = 99.0
        with self.assertRaisesRegex(ValueError, 'outside'): self.check()
    def test_launcher_reused(self):
        self.completion['identities']['11'] = 100.4
        with self.assertRaisesRegex(ValueError, 'launcher birth'): self.check()
    def test_script_pin(self):
        self.report['tool']['sha256'] = 'b'*64
        with self.assertRaisesRegex(ValueError, 'script identity'): self.check()
    def test_timeout(self):
        self.completion['reason'] = 'TIMEOUT'
        with self.assertRaisesRegex(ValueError, 'incomplete'): self.check()
    def test_boolean_pid(self):
        self.report['tool']['pid'] = True
        with self.assertRaisesRegex(ValueError, 'invalid report pid'): self.check()

if __name__ == '__main__': unittest.main()
