"""Independent wire fixtures for the native config diagnostic consumer."""
import unittest
from verify_nav_config_types_ev112 import evaluate

PROBE = '09e9d4be-5e12-47cf-bfb7-cd3116bdf24f'
FIXTURE = '''BALTIC_NAV_CONFIG_TYPES_V1;BalticTrial;09e9d4be-5e12-47cf-bfb7-cd3116bdf24f;9
C;0;CfgWorlds BalticTrial Navmesh filterIsolatedIslandsOnLoad;true;2;true;true;0;0
C;1;CfgWorlds BalticTrial Navmesh GenParams filterIsolatedIslands;true;2;true;true;0;0
C;2;CfgWorlds ChernarusPlus Navmesh filterIsolatedIslandsOnLoad;true;0;true;1;1;1
C;3;CfgWorlds ChernarusPlus Navmesh GenParams filterIsolatedIslands;true;0;true;1;1;1
C;4;CfgWorlds BalticTrial Navmesh GenParams tileWidth;true;0;true;8;8;8
C;5;CfgWorlds ChernarusPlus Navmesh GenParams tileWidth;true;0;true;50;50;50
C;6;CfgWorlds BalticTrial startTime;true;2;true;12:00;12;12
C;7;CfgWorlds ChernarusPlus description;true;2;true;Chernarus;0;0
C;8;CfgWorlds BalticTrial Navmesh __missing_09e9d4be-5e12-47cf-bfb7-cd3116bdf24f;false;-1;false;;0;0
END;9
'''


class ConfigCaptureTests(unittest.TestCase):
    def test_difference_observed_not_acceptance(self):
        result = evaluate(FIXTURE, PROBE)
        self.assertEqual(result['status'], 'OBSERVED_SCRIPT_NUMERIC_CONVERSION_DIFFERENCE')
        self.assertEqual(len(result['different_baltic_flags']), 2)
        self.assertFalse(result['acceptance_eligible'])

    def test_true_may_convert_to_one(self):
        result = evaluate(FIXTURE.replace(';true;0;0', ';true;1;1'), PROBE)
        self.assertEqual(result['status'], 'NO_SCRIPT_NUMERIC_CONVERSION_DIFFERENCE')

    def test_no_assumed_string_prefix_conversion(self):
        result = evaluate(FIXTURE.replace(';12:00;12;12', ';12:00;0;0'), PROBE)
        self.assertEqual(result['observations'][6]['integer'], 0)

    def reject(self, text, message):
        with self.assertRaisesRegex(ValueError, message): evaluate(text, PROBE)

    def test_wrong_numeric_control(self):
        self.reject(FIXTURE.replace(';50;50;50', ';50;49;50'), 'Invalid numeric')

    def test_absent_positive(self):
        self.reject(FIXTURE.replace(';true;0;true;8;', ';false;0;true;8;'), 'Absent positive')

    def test_existing_negative(self):
        self.reject(FIXTURE.replace(';false;-1;', ';true;-1;'), 'Missing-field')

    def test_wrong_missing_sentinel(self):
        self.reject(FIXTURE.replace(';false;-1;', ';false;0;'), 'Missing-field')

    def test_nonfinite(self):
        self.reject(FIXTURE.replace(';true;0;0', ';true;0;nan'), 'Nonfinite')

    def test_wrong_uuid(self):
        self.reject(FIXTURE.replace(PROBE, 'another-probe'), 'Header')

    def test_wrong_world(self):
        self.reject(FIXTURE.replace(';BalticTrial;', ';ChernarusPlus;'), 'Header')

    def test_duplicate_row(self):
        rows = FIXTURE.splitlines(); rows[2] = rows[1]
        self.reject('\n'.join(rows), 'Row identity')

    def test_incomplete(self):
        self.reject(FIXTURE.replace('END;9', 'END;8'), 'Incomplete')

    def test_wrong_text(self):
        self.reject(FIXTURE.replace(';Chernarus;0;0', ';Livonia;0;0'), 'Invalid text')

    def test_text_getter_failed(self):
        self.reject(FIXTURE.replace(';true;12:00;', ';false;12:00;'), 'Invalid text')

    def test_bad_boolean(self):
        self.reject(FIXTURE.replace(';true;2;', ';yes;2;'), 'Boolean')


if __name__ == '__main__': unittest.main()
