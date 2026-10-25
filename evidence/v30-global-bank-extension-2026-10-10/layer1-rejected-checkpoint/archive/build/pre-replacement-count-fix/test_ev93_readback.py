"""Focused fail-closed fixtures for EV93 post-package readback helpers."""
from __future__ import annotations

import unittest

from check_changed_mips import expected_surface_mips, validate_changed_texture_names
from verify_packaged_oprw import changed_entries_between, verify_oprw_identity


class MipScopeFixtures(unittest.TestCase):
    def test_surface_artifact_index_is_exact_for_satellite_and_mask(self):
        surface = {'files': [{
            'tile': [7, 12],
            'files': {
                's': {'paa_sha256': 'a' * 64, 'decoded_sha256': 'b' * 64},
                'm': {'paa_sha256': 'c' * 64, 'decoded_sha256': 'd' * 64},
            },
        }]}
        result = expected_surface_mips(surface)
        self.assertEqual(set(result), {'s_007_012_lco.paa', 'm_007_012_lca.paa'})
        self.assertEqual(result['s_007_012_lco.paa']['decoded_sha256'], 'b' * 64)

    def test_changed_texture_scope_rejects_duplicate_or_non_layer_entries(self):
        self.assertEqual(validate_changed_texture_names([
            'data/layers/s_007_012_lco.paa', 'data/layers/m_007_012_lca.paa']),
            ['data/layers/m_007_012_lca.paa', 'data/layers/s_007_012_lco.paa'])
        for names in ([], ['s_007_012_lco.paa', 's_007_012_lco.paa'], ['data/layers/other.paa']):
            with self.subTest(names=names), self.assertRaises(ValueError):
                validate_changed_texture_names(names)

    def test_surface_artifact_ambiguity_fails_closed(self):
        row = {'tile': [1, 2], 'files': {
            's': {'paa_sha256': 'a', 'decoded_sha256': 'b'},
            'm': {'paa_sha256': 'c', 'decoded_sha256': 'd'},
        }}
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            expected_surface_mips({'files': [row, row]})


class OprwReadbackFixtures(unittest.TestCase):
    def test_compiled_packed_deployed_must_be_exact_oprw_identity(self):
        blob = b'OPRW' + bytes(range(32))
        self.assertEqual(verify_oprw_identity(blob, blob, blob, __import__('hashlib').sha256(blob).hexdigest()),
                         __import__('hashlib').sha256(blob).hexdigest())

    def test_oprw_magic_or_byte_drift_fails_closed(self):
        blob = b'OPRW' + b'x' * 10
        sha = __import__('hashlib').sha256(blob).hexdigest()
        with self.assertRaisesRegex(ValueError, 'magic'):
            verify_oprw_identity(b'NOPE' + b'x' * 10, blob, blob, sha)
        with self.assertRaisesRegex(ValueError, 'differ'):
            verify_oprw_identity(blob, blob, blob + b'changed', sha)

    def test_changed_pbo_inventory_is_exact_and_detects_delta(self):
        baseline = {'world.wrp': b'old', 'tile.paa': b'old-paa', 'same': b'x'}
        packed = {'world.wrp': b'new', 'tile.paa': b'new-paa', 'same': b'x'}
        self.assertEqual(changed_entries_between(baseline, packed), ['tile.paa', 'world.wrp'])
        with self.assertRaisesRegex(ValueError, 'inventory'):
            changed_entries_between(baseline, {'world.wrp': b'new'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
