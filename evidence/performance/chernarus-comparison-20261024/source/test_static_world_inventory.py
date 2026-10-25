"""Controls for false completeness and density units in the OPRW inventory."""
import importlib.util
from pathlib import Path
import struct
import unittest

SPEC = importlib.util.spec_from_file_location('census', Path(__file__).parents[1] / 'tools/performance/compare_static_worlds_ev112.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def fixture(version=32, ids=(10, 11, 12)):
    names = [b'dz\\plants\\tree\\t_example.p3d', b'dz\\rocks\\r_example.p3d']
    header = b'OPRW' + struct.pack('<I', version) + b'\xff' * 64
    model_table = struct.pack('<I', 2) + b'\0'.join(names) + b'\0'
    data = b''
    for i, ident in enumerate(ids):
        matrix = [1, 0, 0, 0, 1, 0, 0, 0, 1, 10 + i * 10, 2, 10]
        data += struct.pack('<2I12fI', ident, 0 if i < 2 else 1, *matrix, 2)
        if version == 32:
            data += struct.pack('<I', 0)
    return header + model_table + b'\xff' * 64 + data + struct.pack('<2I', 0, 10)


def read(b):
    return M.locate(b, rb'dz\\[^\x00]+\.p3d\x00',
                    dict(name='dz\\plants\\tree\\t_example.p3d', xyz=[10, 2, 10]))


class InventoryControls(unittest.TestCase):
    def test_two_versions_and_hand_counted_density(self):
        for version in (29, 32):
            rows, names, meta = read(fixture(version))
            self.assertEqual(rows['id'].tolist(), [10, 11, 12])
            self.assertEqual(meta['version'], version)
            inv = M.inventory(rows, names, 512)
            self.assertEqual(inv['groups']['vegetation']['instances'], 2)
            self.assertEqual(inv['hotspots']['all_128m']['max'], 3)
            self.assertEqual(inv['hotspots']['vegetation_128m']['max'], 2)
            self.assertAlmostEqual(inv['objects_per_square_km_including_sea'], 3 / .262144)

    def test_duplicate_record_rejected(self):
        with self.assertRaises(AssertionError):
            read(fixture(ids=(10, 11, 11)))

    def test_missing_or_wrong_map_info_rejected(self):
        b = fixture()
        for bad in (b[:-8], b[:-4] + struct.pack('<I', 999)):
            with self.assertRaises((AssertionError, struct.error)):
                read(bad)


if __name__ == '__main__':
    unittest.main()
