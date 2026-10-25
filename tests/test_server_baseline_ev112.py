import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/performance'))
from read_server_baseline_ev112 import verify,require_inputs


class EmptyServerBaseline(unittest.TestCase):
    def fixture(self):
        text=(ROOT/'evidence/performance/native-baseline-v1/engine.log').read_text(encoding='utf-8-sig')
        lines=text.splitlines();start=float(lines[1].split(';')[1])
        samples=[line.split(';') for line in lines[3:-1]]
        begin=float(samples[0][2])-float(samples[0][4])-start
        timeline=[(float(i)+.1,lines[2]) for i in range(int(begin)+1)]
        timeline += [(float(s[2])-start+.1,';'.join(s)) for s in samples[:-1]]
        timeline.append((float(samples[-1][2])-start+.1,lines[-1]))
        stamp='2026-10-25T18:00:00.0000000+00:00'
        rows=[dict(sample=i,elapsed_s=t,process_id=5500,start_utc=stamp,cpu_total_s=t*.1,working_set_bytes=512*1048576,private_bytes=600*1048576,engine_last_line=line) for i,(t,line) in enumerate(timeline)]
        return text,rows,stamp

    def test_real_engine_contract_and_known_host_counters(self):
        text,rows,stamp=self.fixture();result=verify('BalticTrial',5500,stamp,text,rows)
        self.assertAlmostEqual(result['cpu_percent_one_logical_core'],10.)
        self.assertEqual(result['working_set_mib']['median'],512)
        self.assertEqual(result['private_mib']['median'],600)
        self.assertEqual(result['engine']['samples'],120)

    def test_explicit_chernarus_world_adapter(self):
        text,rows,stamp=self.fixture();text=text.replace(';BalticTrial;', ';ChernarusPlus;',1)
        self.assertEqual(verify('ChernarusPlus',5500,stamp,text,rows)['world'],'ChernarusPlus')
        with self.assertRaisesRegex(ValueError,'world'):verify('BalticTrial',5500,stamp,text,rows)
        lower=text.replace('ChernarusPlus','chernarusplus')
        self.assertEqual(verify('ChernarusPlus',5500,stamp,lower,rows)['engine_world'],'chernarusplus')

    def test_identity_nan_regression_and_memory_rejected(self):
        text,rows,stamp=self.fixture()
        cases=[('process_id',5501),('start_utc','2026-10-25T19:00:00+00:00'),('cpu_total_s',float('nan')),('cpu_total_s',0.),('private_bytes',0),('working_set_bytes',float('inf')),('sample',999)]
        for key,value in cases:
            with self.subTest(key=key,value=value):
                bad=copy.deepcopy(rows);bad[70][key]=value
                with self.assertRaises(ValueError):verify('BalticTrial',5500,stamp,text,bad)

    def test_host_gap_rejected(self):
        text,rows,stamp=self.fixture();rows[70]['elapsed_s']+=5
        with self.assertRaisesRegex(ValueError,'clock gap'):verify('BalticTrial',5500,stamp,text,rows)

    def test_missing_host_boundaries_rejected(self):
        text,rows,stamp=self.fixture()
        for target in ('S;1;','END;'):
            bad=copy.deepcopy(rows)
            for row in bad:
                if row['engine_last_line'].startswith(target):row['engine_last_line']=''
            with self.subTest(target=target),self.assertRaises(ValueError):verify('BalticTrial',5500,stamp,text,bad)

    def test_unknown_or_regressing_marker_rejected(self):
        text,rows,stamp=self.fixture()
        for marker in ('BOGUS',text.splitlines()[2]):
            bad=copy.deepcopy(rows);bad[75]['engine_last_line']=marker
            with self.subTest(marker=marker),self.assertRaises(ValueError):verify('BalticTrial',5500,stamp,text,bad)

    def test_damaged_engine_log_rejected(self):
        text,rows,stamp=self.fixture();lines=text.splitlines()
        for bad in ('\n'.join(lines[:-1]),'\n'.join(lines[:5]+lines[6:]),text.replace('max_timeslice','min_timeslice',1)):
            with self.assertRaises(ValueError):verify('BalticTrial',5500,stamp,bad,rows)

    def test_duration_mismatch_without_individual_clock_gap(self):
        text,rows,stamp=self.fixture()
        for i,row in enumerate(rows):row['elapsed_s']+=i*.03
        with self.assertRaisesRegex(ValueError,'duration mismatch'):verify('BalticTrial',5500,stamp,text,rows)

    def test_capture_after_end_and_short_capture_rejected(self):
        text,rows,stamp=self.fixture();extra=copy.deepcopy(rows[-1])
        extra.update(sample=len(rows),elapsed_s=extra['elapsed_s']+1,cpu_total_s=extra['cpu_total_s']+.1)
        with self.assertRaisesRegex(ValueError,'after END'):verify('BalticTrial',5500,stamp,text,rows+[extra])
        with self.assertRaisesRegex(ValueError,'Incomplete'):verify('BalticTrial',5500,stamp,text,rows[:100])

    def test_unknown_start_boundary_gap_rejected(self):
        text,rows,stamp=self.fixture();idx=next(i for i,r in enumerate(rows) if r['engine_last_line'].startswith('S;1;'))
        extra=copy.deepcopy(rows[idx-1]);extra.update(engine_last_line='',elapsed_s=(rows[idx-1]['elapsed_s']+rows[idx]['elapsed_s'])/2)
        rows.insert(idx,extra)
        for i,row in enumerate(rows):row['sample']=i
        with self.assertRaisesRegex(ValueError,'start boundary'):verify('BalticTrial',5500,stamp,text,rows)

    def test_zero_cpu_measurement_rejected(self):
        text,rows,stamp=self.fixture()
        for row in rows:row['cpu_total_s']=1.
        with self.assertRaisesRegex(ValueError,'No measured process CPU'):verify('BalticTrial',5500,stamp,text,rows)

    def test_hash_binding_requires_actual_captures_and_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);roles={k:str(root/n) for k,n in [('engine','engine.log'),('host','host.jsonl'),('mission','init.c'),('executable','game.exe'),('server_config','server.cfg')]}
            for key,path in roles.items():Path(path).write_text(key)
            ref=dict(artifacts=roles,inputs={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in roles.values()})
            require_inputs(ref,roles['engine'],roles['host'])
            bad=copy.deepcopy(ref);bad['inputs']={}
            with self.assertRaisesRegex(ValueError,'hash missing'):require_inputs(bad,roles['engine'],roles['host'])
            bad=copy.deepcopy(ref);del bad['artifacts']['mission']
            with self.assertRaisesRegex(ValueError,'artifact identity'):require_inputs(bad,roles['engine'],roles['host'])
            with self.assertRaisesRegex(ValueError,'paths'):require_inputs(ref,root/'other.log',roles['host'])
            Path(roles['engine']).write_text('changed')
            with self.assertRaisesRegex(ValueError,'Bound input changed'):require_inputs(ref,roles['engine'],roles['host'])


if __name__=='__main__':unittest.main()
