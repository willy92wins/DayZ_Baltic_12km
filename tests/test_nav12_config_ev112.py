from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/navigation'))
from package_nav12_config_ev112 import rewrite_tile_width, verify_config_delta


class Nav12Config(unittest.TestCase):
    source = 'class GenParams {tileWidth=12.5; cellSize1=0.25; seedPosition[]={6144,0,6144}; note="a b";};'

    def test_only_the_observed_declaration_changes(self):
        result = rewrite_tile_width(self.source)
        self.assertEqual(result, self.source.replace('tileWidth=12.5;', 'tileWidth=12;'))
        verify_config_delta(self.source, result.replace('tileWidth=12;', 'tileWidth = 12 ;'))

    def test_wrong_or_ambiguous_baselines_are_rejected(self):
        for value in (self.source.replace('12.5', '25'), self.source + 'tileWidth=12.5;', self.source.replace('tileWidth','tileOther')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                rewrite_tile_width(value)

    def test_roundtrip_rejects_extra_parameter_or_quoted_value_changes(self):
        target = rewrite_tile_width(self.source)
        for value in (target.replace('0.25', '0.1'), target.replace('a b', 'ab'), target.replace('6144', '6000'), self.source):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'beyond tileWidth'):
                verify_config_delta(self.source, value)


if __name__ == '__main__':
    unittest.main()
