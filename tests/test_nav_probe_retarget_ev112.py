import sys,unittest,copy
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/navigation'))
from prepare_current_nav_probe_ev112 import retarget


class NavProbeRetarget(unittest.TestCase):
    def test_physical_deck_stays_above_changed_riverbed(self):
        q=[dict(name='bridge_out',start=[60,11.03,60],end=[66,11.03,66],expect='pass'),
           dict(name='dry_route',start=[60,8.,60],end=[66,9.,66],expect='pass')]
        before=copy.deepcopy(q);new,changes=retarget(q,np.full((2048,2048),2.,np.float32))
        self.assertEqual(q,before);self.assertEqual(new[0],q[0])
        self.assertAlmostEqual(new[1]['start'][1],2.1)
        self.assertEqual(new[1]['start'][::2],q[1]['start'][::2])
        self.assertEqual(new[1]['expect'],q[1]['expect'])
        self.assertEqual(changes[0]['basis'],'preserved_physical_deck')


if __name__=='__main__':unittest.main()
