import copy,json,unittest
from unittest.mock import patch
from pathlib import Path
import contact_pair_b3g1_receipts_ev112 as b


class RecoveryTests(unittest.TestCase):
    def test_json_number_preserves_raw(self):
        for encoded in ('600', '600.0'):
            raw=json.loads('{"request":{"wait_for_box_s":'+encoded+',"mode":"server"}}')
            before=copy.deepcopy(raw); result=b.normalize_launch(raw)
            self.assertEqual(raw,before);self.assertIs(type(result['request']['wait_for_box_s']),float)
            self.assertEqual(result['request']['mode'],'server');self.assertIsNot(result,raw)

    def test_wrong_numeric_rejected(self):
        for value in (True,False,'600','600.0',599,600.0000001,float('nan'),float('inf'),10**500):
            with self.subTest(value=str(value)[:30]),self.assertRaises(ValueError):
                b.normalize_launch({'request':{'wait_for_box_s':value}})

    def window(self):
        return dict(basis='HOST_UTC_FIRST_SERVER_BOUND_VERSION_OK_FRESH',
            ready_utc='2026-10-29T00:00:00Z',capture_started_utc='2026-10-29T00:00:01Z',
            capture_deadline_utc='2026-10-29T00:03:00Z',capture_ended_utc='2026-10-29T00:02:59Z',
            mission_error_before_capture=False,run_id='own',pid=42,
            script_log_checked_utc='2026-10-29T00:00:00Z',script_log_sha256='a'*64)

    def test_window(self):b.capture_window(self.window())
    def test_naive_and_non_utc(self):
        for suffix in ('','+01:00'):
            w=self.window()
            for k in w:
                if k.endswith('_utc'):w[k]=w[k].replace('Z',suffix)
            with self.assertRaisesRegex(ValueError,'clock_not_utc'):b.capture_window(w)

    def test_missing_keys(self):
        for raw in ({},{'request':{}},{'request':None}):
            with self.assertRaises(ValueError):b.normalize_launch(raw)
        for key in self.window():
            row=self.window();del row[key]
            with self.assertRaises(ValueError):b.capture_window(row)

    def test_identity_guards_and_delegation(self):
        args=[{},dict(run_id='own',request=dict(wait_for_box_s=600)),
            dict(pid=42,created_utc='2026-10-28T23:59:58Z'),{},{},
            dict(captured_utc='2026-10-29T00:02:59Z',last_write_utc='2026-10-29T00:02:58Z'),{},'hash',self.window()]
        raw=json.dumps(args[1],sort_keys=True)
        with patch.object(b.previous,'identity') as consumer:
            b.identity(*args);consumer.assert_called_once()
            self.assertIs(type(consumer.call_args.args[1]['request']['wait_for_box_s']),float)
            self.assertEqual(json.dumps(args[1],sort_keys=True),raw)
        for ix,key,value in ((2,'created_utc','2026-10-29T00:00:01Z'),
            (5,'captured_utc','2026-10-29T00:02:57Z'),(5,'last_write_utc','2026-10-29T00:03:01Z'),
            (8,'run_id','other'),(8,'pid',43),(8,'script_log_checked_utc','2026-10-29T00:00:02Z')):
            bad=copy.deepcopy(args);bad[ix][key]=value
            with self.subTest(key=key),patch.object(b.previous,'identity') as consumer,self.assertRaises(ValueError):
                b.identity(*bad)
            consumer.assert_not_called()

    def test_bad_windows(self):
        for key,value in (('basis','inferred'),('capture_deadline_utc','2026-10-29T00:03:01Z'),
            ('capture_ended_utc','2026-10-29T00:03:00.001Z'),('capture_started_utc','2026-10-28T23:59:59Z'),
            ('mission_error_before_capture',True),('mission_error_before_capture',0)):
            row=self.window();row[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):b.capture_window(row)

    def test_field_order_and_delta_only(self):
        root=Path(__file__).resolve().parents[2]
        old=(root/'missions/BalticContactB3G.BalticTrial/init.c').read_text(encoding='utf-8')
        new=(root/'missions/BalticContactB3G1.BalticTrial/init.c').read_text(encoding='utf-8')
        oldlines=old.splitlines(); newlines=new.splitlines()
        index=next(i for i,s in enumerate(oldlines) if 'row = row + ";" + seaA' in s)
        # Independent wire order: each reference contributes sea, pond, surface.
        expected=['seaA','pondA','refA','seaB','pondB','refB','seaC','pondC','refC']
        actual=[]
        for line in newlines[index:index+3]:
            tokens=[t.strip().rstrip(';') for t in line.strip().split(' + ')]
            self.assertEqual(tokens[0],'row = row');self.assertEqual(tokens[1::2],['";"']*3)
            actual+=tokens[2::2]
        self.assertEqual(actual,expected)
        original=[t.strip().rstrip(';') for t in oldlines[index].strip().split(' + ')]
        self.assertEqual(original[2::2],expected)
        self.assertEqual(oldlines[:index],newlines[:index])
        self.assertEqual(oldlines[index+1:],newlines[index+3:])


if __name__=='__main__':unittest.main()
