from pathlib import Path
import unittest
import json
import subprocess
import sys
import tempfile
from verify_nav8_load1_config_ev112 import verify

PROBE = '68006643-4412-467a-b437-734168f3f1e0'
BASELINE = (Path(__file__).resolve().parents[2]/'evidence/navigation/kit7-native-config-types-20261027/runtime.log').read_text(encoding='utf-8-sig')
EXPECTED = BASELINE.replace('OnLoad;true;2;true;true;0;0', 'OnLoad;true;0;true;1;1;1')


class Load1Config(unittest.TestCase):
    def test_expected_literal_observations(self):
        self.assertNotEqual(BASELINE, EXPECTED)
        result = verify(EXPECTED, PROBE)
        self.assertEqual(result['status'], 'PASS_NATIVE_LOAD1_CONFIG')
        self.assertFalse(result['acceptance_eligible'])

    def test_original_not_candidate(self):
        with self.assertRaises(ValueError): verify(BASELINE, PROBE)

    def test_float_not_integer_type(self):
        with self.assertRaises(ValueError): verify(EXPECTED.replace('OnLoad;true;0;', 'OnLoad;true;1;'), PROBE)

    def test_numeric_text_not_integer_type(self):
        with self.assertRaises(ValueError): verify(EXPECTED.replace('OnLoad;true;0;', 'OnLoad;true;2;'), PROBE)

    def test_generator_flag_must_not_change(self):
        with self.assertRaises(ValueError): verify(EXPECTED.replace('filterIsolatedIslands;true;2;true;true;0;0', 'filterIsolatedIslands;true;0;true;1;1;1'), PROBE)

    def test_wrong_text(self):
        with self.assertRaises(ValueError): verify(EXPECTED.replace('OnLoad;true;0;true;1;1;1', 'OnLoad;true;0;true;true;1;1'), PROBE)

    def test_negative_control(self):
        with self.assertRaises(ValueError): verify(EXPECTED.replace(';false;-1;', ';true;-1;'), PROBE)

    def test_wrong_probe(self):
        with self.assertRaises(ValueError): verify(EXPECTED, 'wrong-uuid')


class IsolatedCli(unittest.TestCase):
    def test_actual_cli_positive_and_negatives(self):
        script = Path(__file__).with_name('verify_nav8_load1_config_ev112.py')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for label, text, probe, expected in (
                ('expected', EXPECTED, PROBE, 0),
                ('old_flag', BASELINE, PROBE, 1),
                ('wrong_uuid', EXPECTED, 'wrong-uuid', 1),
            ):
                with self.subTest(case=label):
                    log = root/(label+'.log')
                    out = root/(label+'.json')
                    log.write_text(text, encoding='utf-8')
                    proc = subprocess.run([sys.executable, '-I', str(script), '--log', str(log), '--probe-id', probe, '--out', str(out)], capture_output=True, text=True)
                    self.assertEqual(proc.returncode, expected, proc.stderr)
                    result = json.loads(out.read_text(encoding='utf-8'))
                    self.assertEqual(result['status'] == 'PASS_NATIVE_LOAD1_CONFIG', expected == 0)
                    self.assertFalse(result['acceptance_eligible'])


if __name__ == '__main__': unittest.main()
