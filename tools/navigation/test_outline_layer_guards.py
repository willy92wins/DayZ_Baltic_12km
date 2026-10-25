"""Reject foreign identity/pose changes before deriving any layer write."""
import copy, struct, unittest
from correct_outline_v33_layer_offsets import ROOT, derive, read


class Guards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layer=(ROOT/'evidence/foundation-followup-2026-10-01/outline-v33-native/before-relative-offset-correction.tv4l').read_bytes()
        cls.baseline=read(ROOT/'tb/regional_foundation_v10/02_reopened_v10.wrp')
        cls.observed=read(ROOT/'tb/regional_outline_smoothing_v33/4.wrp')
        cls.first_id=cls.baseline['objects'][0]['id']

    def test_foreign_mutations_rejected(self):
        for kind in ['missing_id','model','rotation','x','z','huge_y','nan_y']:
            with self.subTest(kind=kind):
                new=copy.deepcopy(self.observed)
                obj=next(o for o in new['objects'] if o['id']==self.first_id)
                if kind=='missing_id':new['objects'].remove(obj)
                elif kind=='model':obj['name']='foreign.p3d'
                else:
                    matrix=list(struct.unpack('<12f',bytes.fromhex(obj['matrix'])))
                    index={'rotation':0,'x':9,'z':11,'huge_y':10,'nan_y':10}[kind]
                    matrix[index]=float('nan') if kind=='nan_y' else matrix[index]+10
                    obj['matrix']=struct.pack('<12f',*matrix).hex()
                with self.assertRaises(AssertionError):derive(self.layer,self.baseline,new)


if __name__=='__main__':unittest.main()
