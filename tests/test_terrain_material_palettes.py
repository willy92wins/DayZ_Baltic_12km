"""Reject a wrong surface binding rather than painting it into a generated tile."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'playtest'))
from complete_terrain_materials import PALETTE, complete, tile_palettes


class MaterialPaletteTests(unittest.TestCase):
    def test_compacted_palette_skips_conifer(self):
        palette = tile_palettes([Path('P_004-000_L00_L02.rvmat'),
                                 Path('P_004-000_L00_N.rvmat')])['004-000']
        self.assertEqual(palette[5], r'dz\surfaces\data\terrain\cp_grass_nopx.paa')
        source = ('PixelShaderID="TerrainX";' + ''.join(
            'class Stage%d { texture="%s"; };' % (n, palette[n] if n < 5 else '')
            for n in palette)).encode()
        fixed, count = complete(source, 'compact', palette)
        self.assertEqual(count, 2)
        self.assertIn(b'cp_grass_nopx.paa', fixed)
        self.assertNotIn(b'cp_conifer_common1', fixed)
        self.assertNotIn(b'class Stage7', fixed)
        self.assertEqual(complete(fixed, 'again', palette), (fixed, 0))

    def test_full_palette_preserved(self):
        source = ('PixelShaderID="TerrainX";' + ''.join(
            'class Stage%d { texture="%s"; };' % (n, PALETTE[n]) for n in PALETTE)).encode()
        self.assertEqual(complete(source, 'full'), (source, 0))

    def test_reject_unresolved_slot(self):
        with self.assertRaises(ValueError):
            tile_palettes([Path('P_004-000_L00_N.rvmat')])

    def test_reject_conflicting_siblings(self):
        with self.assertRaises(ValueError):
            tile_palettes([Path('P_004-000_L00_L02.rvmat'), Path('P_004-000_L00_L01.rvmat')])

    def test_reject_reordered_palette(self):
        with self.assertRaises(ValueError):
            tile_palettes([Path('P_004-000_L02_L00.rvmat')])

    def test_reject_wrong_texture(self):
        with self.assertRaises(ValueError):
            complete(b'PixelShaderID="TerrainX"; class Stage3 { texture="wrong.paa"; }; class Stage4 { texture=""; };', 'wrong')

    def test_reject_gap(self):
        with self.assertRaises(ValueError):
            complete(b'PixelShaderID="TerrainX"; class Stage3 { texture=""; }; class Stage5 { texture=""; };', 'gap')

    def test_reject_other_shader(self):
        with self.assertRaises(ValueError):
            complete(b'PixelShaderID="Terrain15";', 'shader')


if __name__ == '__main__':
    unittest.main()
