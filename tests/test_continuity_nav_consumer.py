"""Fixed semantic controls; synthetic evidence is never a native runtime PASS."""
from pathlib import Path
import copy
import sys
import unittest

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/navigation'))
from verify_continuity_nav_v30 import verify


class NativeConsumerControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h=np.full((2048,2048),2.,dtype=np.float32)
        cls.ref=dict(header='BALTIC_V30_CONTINUITY_NAV_V1;BalticTrial',
            queries=[dict(name='walk',start=[12,2.2,12],end=[36,2.2,12]),
                     dict(name='negative',start=[12,2.2,12],end=[36,2.2,12]),
                     dict(name='gap',start=[12,2.2,12],end=[36,2.2,36],expect='disconnected')],
            max_waypoint_surface_error_m=.801,limits=['Synthetic reader controls only.'])
        cls.good='\n'.join([
            cls.ref['header'],
            'Q;walk;true;true;true;2;<12,2.2,12>;<36,2.2,12>;<12,2.1,12>;<36,2.1,12>',
            'P;walk;0;<12,2.1,12>;<12,2,12>;<12,2,12>',
            'P;walk;1;<36,2.1,12>;<36,2,12>;<36,2,12>',
            'Q;negative;false;false;false;0;<12,2.2,12>;<36,2.2,12>;<0,0,0>;<0,0,0>',
            'Q;gap;true;true;false;0;<12,2.2,12>;<36,2.2,36>;<12,2.1,12>;<36,2.1,36>',
            'END;3'])

    def reject(self,text):
        try: result=verify(self.ref,text,self.h)
        except (ValueError,IndexError,KeyError): return
        self.assertFalse(result['status'].startswith('PASS'))

    def test_positive_and_short_partial_disconnection(self):
        self.assertTrue(verify(self.ref,self.good,self.h)['status'].startswith('PASS'))
        partial=self.good.replace('Q;gap;true;true;false;0','Q;gap;true;true;true;2').replace(
            'END;3','P;gap;0;<12,2.1,12>;<12,2,12>;<12,2,12>\n'
            'P;gap;1;<18,2.1,12>;<18,2,12>;<18,2,12>\nEND;3')
        self.assertTrue(verify(self.ref,partial,self.h)['status'].startswith('PASS'))

    def test_negative_semantics_and_completeness(self):
        variants={
            'wrong_world':self.good.replace(';BalticTrial',';Other'),
            'missing_terminal':self.good.rsplit('\n',1)[0],
            'truncated_query':self.good.replace('Q;walk;true','Q;walk'),
            'duplicate_query':self.good.replace('END;3',self.good.splitlines()[1]+'\nEND;3'),
            'missing_point':self.good.replace(self.good.splitlines()[2]+'\n',''),
            'reordered_point':self.good.replace('P;walk;0','P;walk;1'),
            'false_find':self.good.replace('Q;walk;true;true;true','Q;walk;true;true;false'),
            'negative_filter_found':self.good.replace('Q;negative;false;false;false','Q;negative;true;true;true'),
            'partial_walk':self.good.replace('P;walk;1;<36,2.1,12>','P;walk;1;<25,2.1,12>'),
            'nan_waypoint':self.good.replace('P;walk;1;<36,2.1,12>','P;walk;1;<36,nan,12>'),
            'ground_changed':self.good.replace('P;walk;1;<36,2.1,12>;<36,2,12>','P;walk;1;<36,2.1,12>;<36,2.2,12>'),
            'floating_nav':self.good.replace('P;walk;1;<36,2.1,12>','P;walk;1;<36,3.1,12>'),
            'surface_xy_changed':self.good.replace('P;walk;1;<36,2.1,12>;<36,2,12>;<36,2,12>',
                'P;walk;1;<36,2.1,12>;<36,2,12>;<37,2,12>'),
            'unrequested_path':self.good.replace('P;walk;1','P;other;1'),
            'unexpected_complete_crossing':self.good.replace('Q;gap;true;true;false;0','Q;gap;true;true;true;2').replace(
                'END;3','P;gap;0;<12,2.1,12>;<12,2,12>;<12,2,12>\n'
                'P;gap;1;<36,2.1,36>;<36,2,36>;<36,2,36>\nEND;3'),
        }
        for label,text in variants.items():
            with self.subTest(label=label):self.reject(text)


if __name__=='__main__':unittest.main(verbosity=2)
