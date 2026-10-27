from pathlib import Path
import unittest
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


if __name__ == '__main__': unittest.main()
