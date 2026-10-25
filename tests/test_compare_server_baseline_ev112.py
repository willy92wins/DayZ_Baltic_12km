import copy
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/performance'))
from compare_server_baseline_ev112 import compare,require_equivalent,ORDER


class Comparison(unittest.TestCase):
    def fixture(self,a=105,b=100):
        return [dict(status='PASS_COMPLETE_EMPTY_SERVER_MEASUREMENT',world=world,process_id=i+100,
                     start_utc='2026-10-25T18:00:00Z',working_set_mib=dict(median=a if world=='BalticTrial' else b),
                     private_mib=dict(median=a if world=='BalticTrial' else b),cpu_percent_one_logical_core=10.)
                for i,world in enumerate(ORDER)]

    def test_known_budget_pass_and_repeatable_fail(self):
        self.assertEqual(compare(self.fixture())['status'],'PASS_EMPTY_SERVER_RAM_BUDGET')
        self.assertEqual(compare(self.fixture(120))['status'],'FAIL_EMPTY_SERVER_RAM_BUDGET')
        result=compare(self.fixture(120))['metrics']['working_set_mib']
        self.assertAlmostEqual(result['ratio'],1.2)
        self.assertEqual(result['paired_ratios'],[1.2]*3)

    def test_noisy_triple_is_inconclusive(self):
        rows=self.fixture(120);rows[0]['working_set_mib']['median']=130
        rows[0]['private_mib']['median']=130
        self.assertEqual(compare(rows)['status'],'INCONCLUSIVE')

    def test_missing_wrong_order_reused_process_and_incomplete_rejected(self):
        rows=self.fixture()
        cases=[rows[:-1],list(reversed(rows))]
        bad=copy.deepcopy(rows);bad[1]['process_id']=bad[0]['process_id'];cases.append(bad)
        bad=copy.deepcopy(rows);bad[0]['status']='FAIL_MEASUREMENT';cases.append(bad)
        for bad in cases:
            with self.assertRaises(ValueError):compare(bad)

    def test_invalid_counter_and_cpu_has_no_invented_budget(self):
        rows=self.fixture();rows[0]['cpu_percent_one_logical_core']=999.
        self.assertEqual(compare(rows)['metrics']['cpu_percent_one_logical_core']['status'],'DESCRIPTIVE_ONLY')
        for value in (float('nan'),float('inf'),0.,-1.,True):
            bad=copy.deepcopy(rows);bad[0]['private_mib']['median']=value
            with self.assertRaises(ValueError):compare(bad)

    def test_paired_excess_not_reproduced_is_inconclusive(self):
        rows=self.fixture(110.1)
        for i,value in zip((0,3,4),(109.9,110.3,110.4)):
            rows[i]['working_set_mib']['median']=value
            rows[i]['private_mib']['median']=value
        for i,value in zip((1,2,5),(100.,100.3,100.1)):
            rows[i]['working_set_mib']['median']=value
            rows[i]['private_mib']['median']=value
        # Deliberately permute close values so ratio of medians exceeds1.1,
        # but only one paired pass exceeds; independent arithmetic oracle.
        self.assertEqual(compare(rows)['status'],'INCONCLUSIVE')
        self.assertEqual(compare(rows)['metrics']['private_mib']['status'],'INCONCLUSIVE_PAIRED_EXCESS')

    def test_bound_condition_drift_rejected(self):
        loaded=[(r,dict(engine_name=str(i),executable='exe',server_config='cfg',canonical_mission='mission',packages=r['world'])) for i,r in enumerate(self.fixture())]
        require_equivalent(loaded)
        for key in ('executable','server_config','canonical_mission','packages','engine_name'):
            bad=copy.deepcopy(loaded);bad[0][1][key]='changed' if key!='engine_name' else '1'
            with self.subTest(key=key),self.assertRaises(ValueError):require_equivalent(bad)


if __name__=='__main__':unittest.main()
