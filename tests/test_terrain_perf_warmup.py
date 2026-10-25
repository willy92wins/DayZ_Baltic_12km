from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/navigation'))
from verify_terrain_perf import verify


class WarmupBoundary(unittest.TestCase):
    def fixture(self):
        # Unmodified engine capture, pass 5 on 2026-10-25: INIT20.068,
        # first tick51.068 and first window1s. Its warmup is exactly30s.
        return (ROOT / 'tests/fixtures/server-baseline-roundoff.log').read_text(encoding='utf-8-sig')

    def test_real_capture_has_exact_thirty_second_warmup(self):
        result = verify(self.fixture())
        self.assertEqual(result['warmup_seconds'], 30.)
        self.assertEqual(result['samples'], 120)

    def test_one_millisecond_short_is_rejected(self):
        text = self.fixture().replace('INIT;20.068;20069', 'INIT;20.069;20069', 1)
        with self.assertRaisesRegex(ValueError, 'Warmup missing'):
            verify(text)

    def test_long_first_window_cannot_hide_short_warmup(self):
        text = self.fixture().replace('INIT;20.068;20069', 'INIT;20;20000', 1)
        text = text.replace('S;1;51.068;51068;1;', 'S;1;51.068;51068;2;', 1)
        # 51.068 - 20 - 2 = 29.068s, although the first tick is >31s later.
        with self.assertRaisesRegex(ValueError, 'Warmup missing'):
            verify(text)

    def test_accepted_short_window_still_requires_full_warmup(self):
        text = self.fixture().replace('INIT;20.068;20069', 'INIT;20.069;20069', 1)
        text = text.replace('S;1;51.068;51068;1;', 'S;1;51.068;51068;0.999;', 1)
        self.assertEqual(verify(text)['warmup_seconds'], 30.)


if __name__ == '__main__':
    unittest.main()
