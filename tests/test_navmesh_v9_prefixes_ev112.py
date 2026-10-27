from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/navigation'))
from inspect_navmesh_v9_ev112 import inspect


def synthetic_prefix_fixture():
    # Observed serialized header contract, no proprietary polygon payload.
    # The real 94,249-tile Chernarus reference is checked separately on disk.
    header = struct.pack('<5I5f2I', 0x4d534554, 9, 2, 2, 1, 0, 0, 0, 50, 50, 2, 1048576)
    blocks = []
    for x in (0, 1):
        prefix = struct.pack('<QII', 0x1000000000000 + x * 1048576, 104, 0)
        integers = [0x444e4156, 12, x, 0, 0, 0, 1, 4, 12, 0, 0, 0, 2, 0, 1]
        values = [1.5, .3, .45, x * 50, -10, 0, (x + 1) * 50, 20, 50, 4]
        blocks.append(prefix + struct.pack('<15I10f', *integers, *values) + b'\0' * 4)
    return bytearray(header + struct.pack('<2I', 0, len(blocks[0])) + b''.join(blocks))


class NavmeshV9Prefixes(unittest.TestCase):
    def test_observed_prefix_contract(self):
        result = inspect(synthetic_prefix_fixture(), (2, 1))
        self.assertEqual(result['tiles'], 2)
        self.assertEqual(result['declared_polygons'], 2)
        self.assertEqual(result['declared_vertices'], 8)
        self.assertEqual(result['grid'], [2, 1])
        self.assertEqual(result['y_bounds'], [-10, 20])
        self.assertEqual(result['header_parameter_u32_at_44'], 1048576)
        self.assertTrue(result['reference_encoding_matches_installed'])
        self.assertIn('Polygon payload/topology not decoded.', result['limits'][1])

    def test_rejects_corrupt_fields(self):
        for offset, value, pattern in (
            (0, 0, 'serialized version'),
            (4, 6, 'serialized version'),
            (8, 3, 'grid coverage'),
            (40, 3, 'count fields'),
            (52, 0, 'tile offsets'),
            (56 + 8, 100, 'payload length'),
            (56 + 12, 1, 'payload length'),
            (56 + 20, 11, 'tile version'),
            (56 + 24, 2, 'tile coordinate'),
            (56 + 4, 0, 'tile reference'),
            (176, 0, 'tile reference'),
            (176 + 24, 0, 'tile coordinate'),
        ):
            with self.subTest(offset=offset):
                data = synthetic_prefix_fixture()
                struct.pack_into('<I', data, offset, value)
                with self.assertRaisesRegex(ValueError, pattern):
                    inspect(data, (2, 1))

    def test_rejects_bounds_and_truncation(self):
        for offset, value, pattern in ((20, 1., 'origin'), (32, 25., 'dimensions'),
                                       (56 + 76, 0., 'positive tile parameters'),
                                       (56 + 112, 0., 'positive tile parameters'),
                                       (56 + 88, 1., 'bounds disagree'),
                                       (56 + 92, float('nan'), 'Nonfinite'),
                                       (56 + 92, 30., 'vertical bounds')):
            with self.subTest(offset=offset):
                data = synthetic_prefix_fixture()
                struct.pack_into('<f', data, offset, value)
                with self.assertRaisesRegex(ValueError, pattern):
                    inspect(data, (2, 1))
        with self.assertRaisesRegex(ValueError, 'grid coverage'):
            inspect(synthetic_prefix_fixture(), (1, 2))
        for length in (0, 47, 50, 100, 200, 295):
            with self.subTest(length=length), self.assertRaises(ValueError):
                inspect(synthetic_prefix_fixture()[:length], (2, 1))

    def test_explicit_baltic_tile_dimension(self):
        data = synthetic_prefix_fixture()
        struct.pack_into('<2f', data, 32, 12.5, 12.5)
        for start, x in ((56, 0), (176, 1)):
            struct.pack_into('<f', data, start + 88, x * 12.5)
            struct.pack_into('<f', data, start + 100, (x + 1) * 12.5)
            struct.pack_into('<f', data, start + 108, 12.5)
        self.assertEqual(inspect(data, (2, 1), 12.5)['tile_width'], 12.5)
        with self.assertRaisesRegex(ValueError, 'tile dimensions'):
            inspect(data, (2, 1), 50.)
        with self.assertRaisesRegex(ValueError, 'Unsupported explicit'):
            inspect(data, (2, 1), 0.)

    def test_eight_metre_bounds_and_dimension_remain_strict(self):
        data = synthetic_prefix_fixture()
        struct.pack_into('<2f', data, 32, 8., 8.)
        for start, x in ((56, 0), (176, 1)):
            struct.pack_into('<f', data, start + 88, x * 8.)
            struct.pack_into('<f', data, start + 100, (x + 1) * 8.)
            struct.pack_into('<f', data, start + 108, 8.)
        self.assertEqual(inspect(data, (2, 1), 8.)['tile_width'], 8.)
        with self.assertRaisesRegex(ValueError, 'tile dimensions'):
            inspect(data, (2, 1), 12.5)
        struct.pack_into('<f', data, 176 + 100, 16.1)
        with self.assertRaisesRegex(ValueError, 'bounds disagree'):
            inspect(data, (2, 1), 8.)

    def test_twelve_metre_grid_bounds_and_wrong_dimension_rejection(self):
        for width in (12., 8., 12.5):
            data = synthetic_prefix_fixture()
            struct.pack_into('<2f', data, 32, width, width)
            for start, x in ((56, 0), (176, 1)):
                struct.pack_into('<f', data, start + 88, x * width)
                struct.pack_into('<f', data, start + 100, (x + 1) * width)
                struct.pack_into('<f', data, start + 108, width)
            if width != 12.:
                with self.subTest(width=width), self.assertRaisesRegex(ValueError, 'tile dimensions'):
                    inspect(data, (2, 1), 12.)
                continue
            result = inspect(data, (2, 1), 12.)
            self.assertEqual(result['tiles'], 2)
            self.assertEqual(result['grid'], [2, 1])
            self.assertEqual(result['tile_width'], 12.)
            with self.assertRaisesRegex(ValueError, 'grid coverage'):
                inspect(data, (1024, 1024), 12.)
            struct.pack_into('<f', data, 176 + 100, 24.1)
            with self.assertRaisesRegex(ValueError, 'bounds disagree'):
                inspect(data, (2, 1), 12.)


if __name__ == '__main__':
    unittest.main()
