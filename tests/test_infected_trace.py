"""Independent crossing fixture plus missing/teleported/under-deck negatives."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('judge', Path(__file__).parents[1]/'tools/playtest/verify_infected_trace.py')
judge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge)


def fixture():
    lines = ['BALTIC_INFECTED_V1', 'world=BalticTrial', 'event;t;stage;x;y;z;d;cross;health;mind;target_entity']
    t = 0
    for stage, distances in enumerate((range(-30, -44, -1), range(-30, 27), range(30, -27, -1))):
        for i, d in enumerate(distances):
            t += .2
            x, z = 2417.143+.988364361*d, 6889.885-.152104866*d
            marker = 'SAMPLE'
            if i == 0:
                marker = 'SPAWN'
            if i == len(distances)-1:
                marker = 'REACHED'
            # Deliberately bogus d/cross: verifier must use XYZ.
            lines.append(f'{marker};{t};{stage};{x};2;{z};123456;123456;100;2;not_read')
    lines.append(f'COMPLETE_ALL_STAGES;{t};3;0;0;0;0;0;0;-1;not_read')
    return '\n'.join(lines)


class TraceTests(unittest.TestCase):
    def test_known_continuous_crossing(self):
        self.assertEqual(judge.assess(fixture())['status'], 'PASS_NATIVE_AI_BOTH_DIRECTIONS')

    def test_completion_required(self):
        self.assertNotEqual(judge.assess(fixture().rsplit('\n', 1)[0])['status'], 'PASS_NATIVE_AI_BOTH_DIRECTIONS')

    def test_below_bridge(self):
        rows = fixture().splitlines()
        for i in range(3, len(rows)-1):
            p = rows[i].split(';')
            p[4] = '0.2'
            rows[i] = ';'.join(p)
        self.assertFalse(judge.assess('\n'.join(rows))['stages']['1']['checks']['on_deck'])

    def test_teleport_rejected(self):
        rows = fixture().splitlines()
        p = rows[30].split(';')
        p[3] = str(float(p[3])+50)
        rows[30] = ';'.join(p)
        self.assertFalse(judge.assess('\n'.join(rows))['stages']['1']['checks']['max_step_2_5m'])

    def test_nonfinite_and_truncation(self):
        self.assertEqual(judge.assess(fixture().replace(';100;', ';nan;', 1))['status'], 'FAIL')
        self.assertEqual(judge.assess(fixture()+'\nSAMPLE;5;1')['status'], 'INCONCLUSIVE')


if __name__ == '__main__':
    unittest.main()
