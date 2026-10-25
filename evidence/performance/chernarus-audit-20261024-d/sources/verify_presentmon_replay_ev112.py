"""Compare replay of the pinned official public ETL with its upstream golden CSV.

Offline format/cadence validation, not a live capture or a DayZ benchmark.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from read_presentmon_ev112 import analyze


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('golden',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    d=a.golden
    for r in json.loads((d/'upstream-files.json').read_text(encoding='utf-8-sig')):
        b=(d/Path(r['path']).name).read_bytes()
        assert len(b)==r['size'] and hashlib.sha1(('blob '+str(len(b))+'\0').encode()+b).hexdigest()==r['sha']
    def groups(path):
        out=defaultdict(list)
        with path.open(encoding='utf-8-sig',newline='') as f:
            for r in csv.DictReader(f):out[(r['Application'],r['ProcessID'],r['SwapChainAddress'])].append(r)
        return out
    gold,actual=groups(d/'test_case_0.csv'),groups(d/'replay.csv')
    assert set(gold)==set(actual)
    results=[]
    for k,g in gold.items():
        rows=actual[k];assert len(g)==len(rows)
        x=np.array([float(r['MsBetweenPresents']) for r in g]);y=np.array([float(r['MsBetweenPresents']) for r in rows])
        assert np.array_equal(x,y)
        assert [r['MsUntilDisplayed'] for r in g]==[r['MsUntilDisplayed'] for r in rows]
        span=(float(rows[-1]['CPUStartQPCTimeInMs'])-float(rows[0]['CPUStartQPCTimeInMs']))/1000
        # The small public fixture is not a 120-second benchmark. Its durations
        # only exercise parsing; live coverage remains an independent gate.
        metrics=analyze(rows,int(k[1]),k[0],expected_seconds=span)
        for name,q in [('p50',50),('p95',95),('p99',99)]:assert abs(metrics['present_interval_ms'][name]-np.percentile(x,q))<1e-10
        results.append(dict(application=k[0],process_id=int(k[1]),frames=len(rows),metrics=metrics))
    result=dict(status='OFFICIAL_TRACE_REPLAY_AND_READER_PASS',live_dayz_capture=False,
                frames=sum(r['frames'] for r in results),groups=len(results),results=results,
                inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (d/'test_case_0.etl',d/'test_case_0.csv',d/'replay.csv')})
    a.output.write_text(json.dumps(result,indent=2));print(result['status'],result['frames'],result['groups'])


if __name__=='__main__':main()
