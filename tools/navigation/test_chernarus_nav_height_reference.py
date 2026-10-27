"""Independent planar fixture and corrupted captures for the reference diagnostic."""
import copy
import unittest
from verify_chernarus_nav_height_reference import evaluate


def fixture():
    anchors = [dict(id=f'ref_{i:02}', shape='test.p3d', family='leaf', historical_position=[100, 10, 100]) for i in range(24)]
    rows = ['CHERNARUS_NAV_HEIGHT_REFERENCE_V1;ChernarusPlus;test-id;24;49']
    for i in range(49):
        ident = f'ref_{i//2:02}' if i < 48 else 'ref_00'
        name = ident + ('_left' if i%2 == 0 else '_right') if i < 48 else 'negative'
        x = 106 if i < 48 and i%2 else 94
        rows.append(f'A;{name};{ident};1;test.p3d;100 10 100;100 10 100;100 10 100;1 0 0;0 1 0;0 0 1;{x} 10 94;{x} 10 106;10;10;10;10;gravel;gravel')
        if i == 48:
            rows.append(f'Q;negative;0;0;0;0;94 10.2 94;94 10.2 106;0 0 0;0 0 0')
        else:
            rows.append(f'Q;{name};1;1;1;2;{x} 10.2 94;{x} 10.2 106;{x} 10 94;{x} 10 106')
            for j,z in enumerate((94, 106)):
                rows.append(f'P;{name};{j};{x} 10 {z};{x} 10 {z};{x} 10 {z};gravel')
    rows.append('END;49')
    return '\n'.join(rows), anchors


class Controls(unittest.TestCase):
    def setUp(self): self.text, self.anchors = fixture()
    def result(self, text=None, anchors=None): return evaluate(text or self.text, anchors or self.anchors, 'test-id')
    def bad(self, old, new):
        with self.assertRaises(ValueError): self.result(self.text.replace(old, new, 1))
    def test_planar(self):
        r=self.result(); self.assertEqual((r['comparable_routes'], r['height_exceedances'], r['acceptance_eligible']), (48,0,False))
    def test_height_equal_ground_road_still_fails(self):
        r=self.result(self.text.replace('P;ref_00_left;0;94 10 94', 'P;ref_00_left;0;94 9 94',1))
        self.assertEqual((r['height_exceedances'],r['raised_waypoints']), (1,0))
    def test_boundary(self):
        self.assertEqual(self.result(self.text.replace('P;ref_00_left;0;94 10 94','P;ref_00_left;0;94 9.2 94',1))['height_exceedances'],0)
    def test_uuid(self): self.bad(';test-id;', ';other-id;')
    def test_world(self): self.bad(';ChernarusPlus;', ';BalticTrial;')
    def test_duplicate(self): self.bad('END;49','END;49\nEND;49')
    def test_missing(self): self.bad('P;ref_00_left;1;', 'X;ref_00_left;1;')
    def test_nonfinite(self): self.bad('94 10 94;', '94 nan 94;')
    def test_end(self): self.bad('END;49','END;48')
    def test_anchor_duplicate(self): self.bad(';ref_00;1;test.p3d',';ref_00;2;test.p3d')
    def test_anchor_missing(self): self.bad('A;ref_00_left;', 'FAIL;ref_00_left;')
    def test_abort_reason(self):
        with self.assertRaisesRegex(ValueError, 'ANCHOR_NOT_UNIQUE_OR_DRIFT'):
            self.result(self.text.split('\n')[0]+'\nFAIL;ref_00_left;ANCHOR_NOT_UNIQUE_OR_DRIFT\nEND;0')
    def test_anchor_drift(self): self.bad('100 10 100;100 10 100;100 10 100','100 10 100;101 10 100;100 10 100')
    def test_input_drift(self):
        anchors=copy.deepcopy(self.anchors);anchors[0]['historical_position'][0]+=1
        with self.assertRaises(ValueError): self.result(anchors=anchors)
    def test_negative(self): self.bad('Q;negative;0;0;0;0;', 'Q;negative;1;1;1;0;')
    def test_noncomparable_preserved(self):
        r=self.result(self.text.replace('Q;ref_00_left;1;1;1;2;', 'Q;ref_00_left;1;1;0;2;',1))
        self.assertEqual((r['noncomparable_routes'],len(r['routes'][0]['points'])),(1,2))
    def test_endpoint_binding(self): self.bad('94 10.2 94;', '95 10.2 94;')
    def test_transform_binding(self): self.bad(';1 0 0;0 1 0;', ';2 0 0;0 1 0;')


if __name__ == '__main__': unittest.main()
