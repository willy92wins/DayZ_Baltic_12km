"""Hand-calculated cadence controls and falsified-capture rejection."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/performance'))
from read_presentmon_ev112 import analyze


def fixture():
    # Exactly 120 seconds, 20ms cadence, independent of producer output.
    return [dict(Application='DayZDiag_x64.exe',ProcessID='123',SwapChainAddress='0xABC',
                 CPUStartQPCTimeInMs=str(1000000+20*i),MsBetweenPresents='20',
                 MsUntilDisplayed='20',PresentMode='Composed: Flip') for i in range(6001)]


class Evidence(unittest.TestCase):
    def test_documentation_legacy_schema_not_silently_accepted(self):
        rows=fixture()
        for r in rows:
            r['CPUStartQPCTime']=r.pop('CPUStartQPCTimeInMs')
            r['DisplayedTime']=r.pop('MsUntilDisplayed')
        with self.assertRaises(ValueError):analyze(rows,123,'DayZDiag_x64.exe')

    def test_known_cadence(self):
        r=analyze(fixture(),123,'DayZDiag_x64.exe')
        self.assertEqual(r['present_interval_ms'],dict(p50=20,p95=20,p99=20))
        self.assertEqual(r['mean_present_rate_fps'],50)
        self.assertEqual(r['status'],'DESCRIPTIVE_ONLY_CONTEXT_UNVERIFIED')

    def test_real_stall_and_dropped_retained(self):
        rows=fixture();rows[3000]['MsBetweenPresents']='200';rows[3000]['MsUntilDisplayed']='NA'
        r=analyze(rows,123,'DayZDiag_x64.exe')
        self.assertEqual(r['max_present_interval_ms'],200)
        self.assertEqual(r['frames'],6001)
        self.assertEqual(r['undisplayed_frames'],1)
        self.assertEqual(r['stalls_per_minute']['100'],.5)

    def test_invalid_evidence(self):
        variants=[]
        rows=fixture();rows[2]['ProcessID']='999';variants.append(rows)
        rows=fixture();rows[2]['SwapChainAddress']='0xDEF';variants.append(rows)
        rows=fixture();rows[2]['CPUStartQPCTimeInMs']=rows[1]['CPUStartQPCTimeInMs'];variants.append(rows)
        rows=fixture();rows[2]['MsBetweenPresents']='nan';variants.append(rows)
        rows=fixture();rows[2]['Application']='other.exe';variants.append(rows)
        rows=fixture();rows[2]['MsBetweenPresents']='0';variants.append(rows)
        variants.append(fixture()[:1000])
        rows=fixture()
        for r in rows:r['CPUStartQPCTimeInMs']=str(float(r['CPUStartQPCTimeInMs'])/1000)
        variants.append(rows)
        rows=fixture()
        for r in rows:r['MsUntilDisplayed']='NA'
        variants.append(rows)
        for i,rows in enumerate(variants):
            with self.subTest(case=i),self.assertRaises(ValueError):analyze(rows,123,'DayZDiag_x64.exe')


if __name__=='__main__':unittest.main()
