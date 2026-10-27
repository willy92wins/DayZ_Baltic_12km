from pathlib import Path
import hashlib
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/navigation'))
from package_nav8_onload_config_ev112 import rewrite_onload, verify_config_delta, tokens

BEFORE = 'class CfgWorlds {class CAWorld; class BalticTrial:CAWorld {class Navmesh {filterIsolatedIslandsOnLoad="true"; class GenParams {tileWidth=8;filterIsolatedIslands="true";};};};};'
AFTER = 'class CfgWorlds {class CAWorld; class BalticTrial:CAWorld {class Navmesh {filterIsolatedIslandsOnLoad=1; class GenParams {tileWidth=8;filterIsolatedIslands="true";};};};};'


class OnLoadConfig(unittest.TestCase):
    def test_literal_independent_pair(self):
        self.assertEqual(rewrite_onload(BEFORE), AFTER)
        verify_config_delta(BEFORE, AFTER)

    def test_actual_observed_config(self):
        path = Path(__file__).parent/'fixtures/nav8-onload/original.cpp'
        raw = path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), '345b9a4dd2a38af2566b81ee578b5d3bcf7e3b4f4f1f175bb1aeb72499ae6fe8')
        before = raw.decode('utf-8-sig')
        expected = before.replace('filterIsolatedIslandsOnLoad="true";', 'filterIsolatedIslandsOnLoad=1;')
        self.assertNotEqual(expected, before)
        self.assertEqual(rewrite_onload(before), expected)
        verify_config_delta(before, expected)

    def test_non_target_genparams(self):
        with self.assertRaises(ValueError):
            verify_config_delta(BEFORE, AFTER.replace('filterIsolatedIslands="true"', 'filterIsolatedIslands=1'))

    def test_non_target_width(self):
        with self.assertRaises(ValueError): verify_config_delta(BEFORE, AFTER.replace('tileWidth=8', 'tileWidth=12'))

    def test_wrong_world(self):
        with self.assertRaises(ValueError): rewrite_onload(BEFORE.replace('BalticTrial', 'OtherWorld'))

    def test_wrong_class(self):
        with self.assertRaises(ValueError): rewrite_onload(BEFORE.replace('class Navmesh', 'class Other'))

    def test_duplicate_inside_genparams(self):
        duplicate = BEFORE.replace('class GenParams {', 'class GenParams {filterIsolatedIslandsOnLoad="true";')
        with self.assertRaises(ValueError): rewrite_onload(duplicate)

    def test_target_only_inside_genparams(self):
        misplaced = BEFORE.replace('filterIsolatedIslandsOnLoad="true";', '').replace('tileWidth=8;', 'tileWidth=8;filterIsolatedIslandsOnLoad="true";')
        with self.assertRaises(ValueError): rewrite_onload(misplaced)

    def test_float_one_is_not_integer(self):
        with self.assertRaises(ValueError): verify_config_delta(BEFORE, AFTER.replace('OnLoad=1', 'OnLoad=1.0'))

    def test_rejects_no_change(self):
        with self.assertRaises(ValueError): verify_config_delta(BEFORE, BEFORE)

    def test_extra_declaration(self):
        with self.assertRaises(ValueError): verify_config_delta(BEFORE, AFTER+'extra=1;')

    def test_quoted_path_whitespace_preserved(self):
        old = BEFORE.replace('class Navmesh {', 'class Navmesh {path="a b\\c";')
        new = AFTER.replace('class Navmesh {', 'class Navmesh {path="ab\\c";')
        with self.assertRaises(ValueError): verify_config_delta(old, new)
        self.assertIn('"a b\\c"', tokens(old))

    def test_layout_not_semantics(self):
        verify_config_delta(BEFORE, AFTER.replace('=', ' = ').replace(';', ';\n'))

    def test_unbalanced(self):
        with self.assertRaises(ValueError): rewrite_onload(BEFORE[:-2])


if __name__ == '__main__': unittest.main()
