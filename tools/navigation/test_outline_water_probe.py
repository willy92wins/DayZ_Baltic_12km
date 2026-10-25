"""Protocol controls; synthetic PASS is not an in-game result."""
import unittest
from verify_outline_water_probe import verify


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        kinds=['dry_shore_source']*12+['dry_low_interior']*4+['dry_high_control']*4+['wet_control']*4
        cls.reference={'points':[dict(index=i,xz=[8200+i*6,10430],kind=k,ground_m=1.4 if i<20 else -1.) for i,k in enumerate(kinds)]}
        rows=['BALTIC_OUTLINE_WATER_V1;BalticTrial']
        for epoch in range(681):
            t=20+epoch*.25
            rows.append(f'SEA;{t};{t+20};0.5;1;0.9;0.25;0.1')
            for p in cls.reference['points']:
                i=p['index'];g=p['ground_m'];x,z=p['xz'];wet='true' if i>=20 else 'false'
                rows.append(f'S;{t};{i};<{x:.6f}, {g+10:.6f}, {z:.6f}>;{g};0.9;1.1;-9;{wet};false')
        rows.append('COMPLETE;198.1')
        cls.rows=rows

    def test_complete_positive(self):
        result=verify('\n'.join(self.rows),self.reference)
        self.assertEqual(result['epochs'],681)
        self.assertEqual(result['samples'],16344)

    def test_negative_controls(self):
        def row_change(index,field,value):
            rows=self.rows.copy();parts=rows[index].split(';');parts[field]=value;rows[index]=';'.join(parts);return rows
        controls={
            'no_completion':self.rows[:-1],
            'premature_completion':self.rows[:100]+['COMPLETE;198.1'],
            'wrong_world':['BALTIC_OUTLINE_WATER_V1;chernarusplus']+self.rows[1:],
            'missing_point':self.rows[:2]+self.rows[3:],
            'duplicate_point':self.rows[:3]+[self.rows[2]]+self.rows[3:],
            'moved_sample':row_change(2,3,'<8210.000000, 11.400000, 10430.000000>'),
            'bad_ground':row_change(2,4,'1.5'),
            'nonfinite':row_change(2,6,'nan'),
            'bad_vector':row_change(2,3,'8200 11.4 10430'),
            'false_boolean':row_change(2,8,'0'),
            'flooded_dry':row_change(2,8,'true'),
            'insufficient_freeboard':row_change(2,6,'1.35'),
            'dry_wet_control':row_change(22,8,'false'),
            'shallow_wet_control':row_change(22,5,'-0.9'),
            'no_sea_epoch':self.rows[:1]+self.rows[2:],
            'reversed_tick':row_change(26,2,'39'),
            'data_after_completion':self.rows+[self.rows[-1]],
            'early_terminal':self.rows[:-1]+['COMPLETE;197'],
        }
        for name,rows in controls.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):verify('\n'.join(rows),self.reference)


if __name__=='__main__':unittest.main()
