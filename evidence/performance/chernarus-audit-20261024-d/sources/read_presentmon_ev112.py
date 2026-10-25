"""PresentMon 2.6 default CSV statistics. Never accepts a benchmark on CSV alone.

Schema/units: actual signed 2.6 binary replay and upstream CsvOutput.cpp.
The README mixes legacy v2 names with default names; accept the verified default.
All presents, including undisplayed frames and real stalls, remain in the sample.
Multiple swap chains require investigation, not automatic fastest/largest choice.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def percentile(values, p):
    a = sorted(values); pos = (len(a)-1)*p
    lo = int(pos); hi = min(lo+1,len(a)-1)
    return a[lo]+(a[hi]-a[lo])*(pos-lo)


def analyze(rows, process_id, application, expected_seconds=120.):
    if len(rows)<3:raise ValueError('too few frame records')
    fields = {'Application','ProcessID','SwapChainAddress','CPUStartQPCTimeInMs',
              'MsBetweenPresents','MsUntilDisplayed','PresentMode'}
    if any(not fields<=set(r) for r in rows):raise ValueError('expected PresentMon 2.6 default schema with --qpc_time_ms')
    if any(int(r['ProcessID'])!=process_id or r['Application'].lower()!=application.lower() for r in rows):
        raise ValueError('process identity mismatch')
    chains = {r['SwapChainAddress'] for r in rows}
    if len(chains)!=1 or not next(iter(chains)):raise ValueError('ambiguous swap chain')
    times = [float(r['CPUStartQPCTimeInMs']) for r in rows]
    intervals = [float(r['MsBetweenPresents']) for r in rows]
    if not all(math.isfinite(t) and t>=0 for t in times):raise ValueError('invalid clock')
    if any(b<=a for a,b in zip(times,times[1:])):raise ValueError('non-monotonic frame clock')
    if not all(math.isfinite(t) and t>0 for t in intervals):raise ValueError('invalid present interval')
    span = (times[-1]-times[0])/1000
    if not expected_seconds-1 <= span <= expected_seconds+1:raise ValueError('incomplete capture or unexpected time units/duration')
    # CPU-start and present clocks are related but not identical. Allow boundary
    # work equal to two largest real frames; do not discard a slow frame.
    if abs(sum(intervals[1:])/1000-span)>1+2*max(intervals)/1000:
        raise ValueError('present-duration/clock coverage mismatch')
    displayed = []
    for r in rows:
        if r['MsUntilDisplayed']=='NA':continue
        d=float(r['MsUntilDisplayed'])
        if not math.isfinite(d) or d<0:raise ValueError('invalid display latency')
        displayed.append(d)
    if not displayed:raise ValueError('no displayed frames')
    return dict(status='DESCRIPTIVE_ONLY_CONTEXT_UNVERIFIED',csv_structure='VALID',
                process_id=process_id,application=application,swap_chain=next(iter(chains)),
                frames=len(rows),span_seconds=span,undisplayed_frames=len(rows)-len(displayed),
                present_interval_ms={k:percentile(intervals,p) for k,p in [('p50',.5),('p95',.95),('p99',.99)]},
                mean_present_rate_fps=1000*len(intervals)/sum(intervals),max_present_interval_ms=max(intervals),
                stalls_per_minute={str(ms):sum(v>ms for v in intervals)*60/span for ms in (50,100)},
                present_modes=sorted({r['PresentMode'] for r in rows}),
                limits=['Present cadence, not CPU execution time or display cadence.',
                        'No runtime collector validation, focus/pause/scene, settings, ETW loss or repetition acceptance from CSV alone.',
                        'No FPS comparison verdict, RAM/VRAM or multiplayer capacity.'])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('csv',type=Path);ap.add_argument('out',type=Path)
    ap.add_argument('--process-id',type=int,required=True);ap.add_argument('--application',required=True)
    a=ap.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    with a.csv.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    result=analyze(rows,a.process_id,a.application)
    result['csv_sha256']=hashlib.sha256(a.csv.read_bytes()).hexdigest()
    result['producer_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
